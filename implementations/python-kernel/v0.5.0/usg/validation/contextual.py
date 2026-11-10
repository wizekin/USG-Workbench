"""Explicit L5 results and exact-context contradiction indexing.

No name-based entity merge, opaque-content flattening, or closed-world negation.
An absent verifier produces NOT_CHECKED, never a fabricated PASS.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..core.values import CheckResult as CR, Component
from ..grammar.node import walk
from ..grammar.serialize import canonical_string, node_from_json
from ..storage.schema import WriterRole as W
from ..storage.views import CURRENT_ASSERTION
from ..util import canonical_json, sha256_hex
from .checks import CheckOutcome


@dataclass
class ContextualValidator:
    mentions: tuple = ()
    lexical_resolver: object = None
    paraphrase_verifier: object = None
    trusted_verifier: object = None
    panel_verifier: object = None

    def __call__(self, candidate):
        results={f'VC-C{i:02}':CheckOutcome(f'VC-C{i:02}',CR.NOT_CHECKED) for i in range(1,8)}
        def result(i, value, detail):
            code=f'VC-C{i:02}'
            results[code]=CheckOutcome(code,value,detail)
        nodes=[n for _,n in walk(candidate.expression)]
        if self.lexical_resolver:
            senses=[self.lexical_resolver(m.label,candidate.source.language).concepts for m in self.mentions]
            bad=any(m.concept not in senses[i] for i,m in enumerate(self.mentions))
            ambiguous=any(len(x)!=1 for x in senses)
            result(1,CR.FAIL if bad else CR.UNCERTAIN if ambiguous else CR.PASS,'installed lexical sense alignment')
        known={m.handle for m in self.mentions}
        references={n.get('ref') for n in nodes if n.op=='REF'}
        if known:
            result(2,CR.PASS if references<=known else CR.UNCERTAIN,'referent candidates are explicit; unresolved links remain uncertain')
        scoped=any(n.op in {'Q','MODAL','ATTRIBUTE','COUNTERFACTUAL','FIG'} for n in nodes)
        result(3,CR.UNCERTAIN if scoped else CR.PASS,'scope plausibility requires retained alternatives for nontrivial operators')
        alternatives=[n for n in nodes if n.op=='ALT']
        duplicate=any(len({canonical_string(a) for a in n.args})!=len(n.args) for n in alternatives)
        result(4,CR.FAIL if duplicate else CR.UNCERTAIN if alternatives else CR.NOT_CHECKED,
               'duplicate alternatives' if duplicate else 'exhaustiveness is not inferred from parser agreement')
        for number,callback in ((5,self.paraphrase_verifier),(6,self.trusted_verifier),(7,self.panel_verifier)):
            if callback:
                try:
                    verdict=callback(candidate)
                    if type(verdict) is not bool:
                        raise ValueError('verifier must return bool')
                    result(number,CR.PASS if verdict else CR.UNCERTAIN,'installed contextual verifier')
                except Exception:
                    result(number,CR.UNCERTAIN,'contextual verifier unavailable')
        return tuple(results.values())


def world_atoms(expression):
    """Retain tense in the conflict key; never extract embedded attitudes."""
    def visit(n,scope=()):
        if n.op=='ASSERT':
            if n.get('commitment','AUTHOR')!='AUTHOR' or n.get('context','WORLD') not in {'WORLD','DOMAIN_MODEL'}:
                return
            yield from visit(n.args[0],scope)
        elif n.op=='AND':
            for a in n.args:
                yield from visit(a,scope)
        elif n.op=='TENSE':
            # Relative past/future intervals do not establish co-temporality.
            # Only an explicit present instant supports a cross-claim key.
            if n.get('tense')=='PRESENT' and n.args[0].op=='TIME_LIT' and n.args[0].get('form')=='INSTANT':
                yield from visit(n.args[1],scope+(canonical_string(n.args[0])+':'+n.get('tense'),))
        else:
            polarity=0 if n.op=='NOT' else 1
            atom=n.args[0] if n.op=='NOT' else n
            if atom.op not in {'RELATE','PROPERTY','HOLDS','SAME_AS','DIFFERENT_FROM'}:
                return
            if any(x.op in {'Q','ALT','MODAL','ATTRIBUTE','COND','COUNTERFACTUAL','FIG','VAR','ERROR'} for _,x in walk(atom)):
                return
            yield sha256_hex(canonical_json([scope,canonical_string(atom)])),polarity
    yield from visit(expression)


def index_claim(txn, assertion_id, expression, context='WORLD', context_name=None, definition_ref=None):
    for key, polarity in world_atoms(expression):
        key=sha256_hex(key+canonical_json([context,context_name,definition_ref]))
        txn.execute('INSERT OR IGNORE INTO conflict_cluster VALUES(?,?,?,?)',(key,assertion_id,polarity,context))
        others=txn.query("SELECT a.assertion_id FROM assertion a JOIN conflict_cluster c USING(assertion_id) WHERE c.cluster_hash=? AND c.polarity<>? AND a.epistemic_status='VERIFIED' AND "+CURRENT_ASSERTION,(key,polarity))
        for other in others:
            txn.execute("UPDATE assertion SET epistemic_status='DISPUTED' WHERE assertion_id=?",(other[0],))
            txn.audit(Component.EVALUATION_PROCESS,'TRUSTED_CONFLICT',str(other[0]),str(assertion_id))


class ConflictIndex:
    def __init__(self,service):
        self.service=service

    def rebuild(self):
        s=self.service
        s.assert_integrity()
        # Snapshot and publication share a write transaction; an evaluator cannot
        # promote a contradictory exact claim between the scan and invalidation.
        with s.db.write(W.EVALUATION) as t:
            rows=t.query("SELECT a.*,e.body FROM assertion a JOIN expression e ON a.content_space='NODE' AND a.content_id=e.node_id WHERE a.commitment='AUTHOR' AND a.eval_context IN ('WORLD','DOMAIN_MODEL') AND "+CURRENT_ASSERTION+" ORDER BY assertion_id")
            t.execute('DELETE FROM conflict_cluster')
            for row in rows:
                for key,polarity in world_atoms(node_from_json(json.loads(row['body']))):
                    key=sha256_hex(key+canonical_json([row['eval_context'],row['eval_context_name'],row['definition_ref']]))
                    t.execute('INSERT OR IGNORE INTO conflict_cluster VALUES(?,?,?,?)',(key,row['assertion_id'],polarity,row['eval_context']))
            conflicts=t.query('SELECT cluster_hash FROM conflict_cluster GROUP BY cluster_hash HAVING MIN(polarity)<>MAX(polarity)')
            disputed=[]
            for conflict in conflicts:
                claims=t.query('SELECT a.assertion_id,a.epistemic_status FROM assertion a JOIN conflict_cluster c USING(assertion_id) WHERE c.cluster_hash=?',(conflict[0],))
                # Source disagreement is retained, not treated as a truth oracle.
                # Promotion is blocked for all conflicting members. Previously
                # verified members lose trusted eligibility immediately.
                for claim in claims:
                    if claim['epistemic_status']=='VERIFIED':
                        t.execute("UPDATE assertion SET epistemic_status='DISPUTED' WHERE assertion_id=?",(claim[0],))
                        disputed.append(claim[0])
            if disputed:
                t.audit(Component.EVALUATION_PROCESS,'TRUSTED_CONFLICT',','.join(map(str,disputed)))
        return {'clusters':len(conflicts),'disputed_assertions':disputed}

    def conflicts(self,assertion_id,txn=None):
        sql=('SELECT DISTINCT other.assertion_id FROM conflict_cluster own JOIN conflict_cluster other '
             'ON own.cluster_hash=other.cluster_hash AND own.polarity<>other.polarity JOIN assertion a ON a.assertion_id=other.assertion_id WHERE own.assertion_id=? AND '+CURRENT_ASSERTION)
        if txn is not None:
            return [x[0] for x in txn.query(sql,(assertion_id,))]
        with self.service.db.read() as r:
            return [x[0] for x in r.query(sql,(assertion_id,))]
