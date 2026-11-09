"""Bounded semantic learning with counterexamples and explicit shadow status.

Anti-unification preserves operators, roles, frame versions and co-reference.
No structural resemblance proves a new concept, event identity or world fact.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

from ..concepts.lexicon import VETTED_VERB_ALIASES
from ..core.ids import IdSpace, Ref
from ..core.values import Component
from ..grammar.node import Node, role_entries, var, walk
from ..grammar.serialize import canonical_string, node_from_json, node_to_json
from ..storage.schema import WriterRole as W
from ..util import canonical_json, sha256_hex
from .dsl import RuleProposal
from .engine import LearningEngine, bounded_match


def anti_unify(left,right,*,max_nodes=200,max_depth=12):
    pairs={};steps=0
    def unify(a,b,depth):
        nonlocal steps
        steps+=1
        if steps>max_nodes or depth>max_depth:
            raise ValueError('anti-unification budget')
        if a.op==b.op=='REF':
            key=(a.get('ref'),b.get('ref'))
            pairs.setdefault(key,f'g{len(pairs)}')
            return var(pairs[key])
        if a.op!=b.op or a.params!=b.params or len(a.args)!=len(b.args):
            return None
        args=[unify(x,y,depth+1) for x,y in zip(a.args,b.args)]
        if any(x is None for x in args):
            return None
        return Node(a.op,tuple(args),a.params)
    return unify(left,right,0)


def test_generalization(pattern,positives,negatives):
    positives,negatives=tuple(positives),tuple(negatives)
    if not positives or not negatives:
        return {'passed':False,'reason':'positive and contrastive evidence required'}
    def matches(n):
        return bounded_match(pattern,n,max_depth=12) is not None
    missed=[i for i,n in enumerate(positives) if not matches(n)]
    counterexamples=[i for i,n in enumerate(negatives) if matches(n)]
    return {'passed':not missed and not counterexamples,'missed_positives':missed,'counterexamples':counterexamples}


class SemanticLearner:
    def __init__(self,service):
        self.service=service

    def mine(self):
        s=self.service
        s.assert_integrity()
        groups=defaultdict(list)
        with s.db.read() as r:
            rows=r.query("SELECT c.*,s.uri FROM candidate c JOIN source s USING(source_id) WHERE c.lifecycle='VALIDATED_FORMALLY' ORDER BY candidate_id DESC LIMIT ?",(s.config['gen_max_candidates']*10,))
            for row in rows:
                source=s.store.get_source(r,Ref(IdSpace.SOURCE,row['source_id']))
                expression=node_from_json(json.loads(row['payload'])['expression'])
                # Preserve the frame/role signature; no cross-context pooling.
                signature=tuple((n.op,n.get('frame'),n.get('version'),n.get('roles')) for _,n in walk(expression) if n.op in {'APPLY','NOT','MODAL','Q','ATTRIBUTE','COND'})
                groups[signature].append((expression,s._origin(source),row['candidate_id']))
        created=0
        with s.db.write(W.CANDIDATE_STORE) as t:
            for signature,examples in groups.items():
                if created>=s.config['gen_max_candidates']:
                    break
                origins=sorted({e[1] for e in examples})
                if len(origins)<s.config['pattern_min_independent_origins']:
                    continue
                pattern=examples[0][0]
                for expr,_,_ in examples[1:20]:
                    # Re-use of an existing generalization is deliberately
                    # bounded; incompatible structures end this candidate.
                    if pattern.op=='ASSERT' and any(n.op=='VAR' for _,n in walk(pattern)):
                        break
                    pattern=anti_unify(pattern,expr)
                    if pattern is None:
                        break
                if pattern is None:
                    continue
                negatives=[e[0] for sig,others in groups.items() if sig!=signature for e in others[:2]][:20]
                checks=test_generalization(pattern,[e[0] for e in examples[:20]],negatives)
                body={'classification':'TYPED_STRUCTURAL_GENERALIZATION','pattern':node_to_json(pattern),
                      'premises':[e[2] for e in examples[:20]],'tests':checks,'epistemic_status':'INFERRED',
                      'licenses_concept_identity':False,'licenses_world_truth':False}
                hid=sha256_hex(canonical_json(body['pattern']))
                old=t.one('SELECT origins FROM semantic_hypothesis WHERE hypothesis_id=?',(hid,))
                if old:
                    origins=sorted(set(origins)|set(json.loads(old[0])))
                    t.execute('UPDATE semantic_hypothesis SET origins=? WHERE hypothesis_id=?',(canonical_json(origins),hid))
                else:
                    t.execute('INSERT INTO semantic_hypothesis VALUES(?,?,?,?,?,?,?)',
                              (hid,'CONCEPT_GENERALIZATION',canonical_json(body),canonical_json(origins),
                               canonical_json(checks.get('counterexamples',[])),'REJECTED' if checks.get('counterexamples') else 'SHADOW',s.db.clock.now()))
                    t.audit(Component.GENERALIZATION_ENGINE,'SEMANTIC_HYPOTHESIS',hid,'SHADOW')
                    created+=1
        return {'new_hypotheses':created,'scanned':len(rows),'trusted_promotions':0}

    def discover_aliases(self):
        """Generate executable rule tests only for package-vetted alignments."""
        s=self.service
        with s.db.read() as r:
            forms={row[0].casefold() for row in r.query("SELECT DISTINCT form FROM provisional WHERE status='ACTIVE'")}
            for row in r.query("SELECT c.unit_start,c.unit_end,c.source_id FROM candidate c WHERE c.outcome='UNRESOLVED' ORDER BY c.candidate_id DESC LIMIT 100"):
                source=s.store.get_source(r,Ref(IdSpace.SOURCE,row['source_id']))
                forms.update(re.findall(r'\b[a-z]+\b',source.text[row['unit_start']:row['unit_end']].casefold()))
        engine=LearningEngine(s.db,s.config);proposed=[]
        for form in sorted(forms & VETTED_VERB_ALIASES.keys()):
            verb=VETTED_VERB_ALIASES[form]
            proposal=RuleProposal('AUTO_ALIAS_'+form.upper(),form,verb,
                    (f'John {form} an apple.',f'Mary {form} food.'),
                    (f'John {form} a flibbertigibbet.',f'John {form} an apple beside a telescope.'),
                    ((f'John {form} an apple.',f'John did not {form} an apple.'),))
            proposed.append(engine.propose(proposal))
        return proposed

    def counterexample(self,hypothesis_id,expression,reason):
        if not isinstance(reason,str) or not 1<=len(reason)<=2000:
            raise ValueError('counterexample reason required')
        with self.service.db.write(W.CANDIDATE_STORE) as t:
            row=t.one('SELECT counterexamples FROM semantic_hypothesis WHERE hypothesis_id=?',(hypothesis_id,))
            if row is None:
                raise ValueError('unknown hypothesis')
            items=json.loads(row[0])
            example={'expression':node_to_json(expression),'reason':reason}
            if example not in items:
                items.append(example)
            t.execute("UPDATE semantic_hypothesis SET state='REJECTED',counterexamples=? WHERE hypothesis_id=?",(canonical_json(items[:100]),hypothesis_id))
            t.audit(Component.VALIDATOR,'SEMANTIC_COUNTEREXAMPLE',hypothesis_id,sha256_hex(reason))
