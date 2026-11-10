"""Versioned scoped definitions. A definition stipulates meaning, never world truth.

Only closed, typed grammar expressions are stored; no evaluator runs resource code.
Updates use a compare-and-swap version and preserve every historical constraint.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..core.ids import IdSpace
from ..core.values import Component
from ..errors import InvariantViolation, PolicyDenied
from ..grammar.node import Node, kind, q, relate, var, walk
from ..grammar.serialize import canonical_string, node_from_json, node_to_json
from ..grammar.typecheck import Typechecker
from ..storage.registry import IdRegistry
from ..storage.schema import WriterRole as W
from ..util import canonical_json, sha256_hex
from .identity import Definition


@dataclass(frozen=True)
class Constraint:
    expression: Node
    strength: str = 'ESSENTIAL'
    provenance: str = 'DEFINITIONAL'
    evidence_id: int | None = None

    def __post_init__(self):
        if self.strength not in {'ESSENTIAL','TYPICAL','CONTINGENT','CONTEXTUAL'}:
            raise ValueError('constraint strength')
        if self.provenance not in {'DEFINITIONAL','EMPIRICAL','ASSUMED'}:
            raise ValueError('constraint provenance')
        if self.strength == 'ESSENTIAL' and self.provenance != 'DEFINITIONAL':
            raise PolicyDenied('empirical regularity cannot become a defining condition')


class DefinitionStore:
    def __init__(self, service):
        self.service, self.db = service, service.db

    def publish(self, concept, scope, constraints, *, expected_version=0, complete=False):
        self.service.assert_integrity()
        if not isinstance(scope,str) or not 1 <= len(scope) <= 200 or type(complete) is not bool:
            raise ValueError('definition scope/completeness')
        if type(expected_version) is not int or expected_version < 0:
            raise ValueError('expected version')
        constraints = tuple(constraints)
        if not 1 <= len(constraints) <= 100 or not all(isinstance(c,Constraint) for c in constraints):
            raise ValueError('bounded nonempty constraint list required')
        onto = self.service.foundation.ontology
        if not onto.has(concept):
            raise ValueError('concept must be installed')
        checker = Typechecker(self.service.foundation.frames)
        items=[]
        for c in constraints:
            if any(n.op in {'ERROR','REF','ASSERT'} or n.op=='VAR' and n.get('name')!='self'
                   for _,n in walk(c.expression)):
                raise PolicyDenied('definitions use only bound self, never instance identities')
            closed=q('FORALL','self',relate('INSTANCE_OF',var('self'),kind(concept)),c.expression)
            if not checker.check(closed).ok:
                raise InvariantViolation('ill-typed definition constraint','SG-CON-006')
            if c.evidence_id is not None:
                with self.db.read() as r:
                    if not r.one('SELECT 1 FROM evidence WHERE evidence_id=?',(c.evidence_id,)):
                        raise ValueError('unknown constraint evidence')
            items.append({'class':c.strength,'provenance':c.provenance,
                          'expr':node_to_json(c.expression),'evidence':c.evidence_id})
        items.sort(key=canonical_json)
        if len({canonical_json(x) for x in items}) != len(items):
            raise ValueError('duplicate constraints')
        digest=sha256_hex(canonical_json({'concept':concept,'scope':scope,'complete':complete,'constraints':items}))
        with self.db.write(W.PROMOTION,W.REGISTRY) as t:
            cid=t.scalar('SELECT concept_id FROM concept WHERE canonical_label=?',(concept,))
            old=t.one('SELECT * FROM concept_definition WHERE concept_id=? AND scope=? ORDER BY def_version DESC LIMIT 1',(cid,scope))
            version=old['def_version'] if old else 0
            if old and old['content_hash']==digest:
                return old['definition_id']
            if version != expected_version:
                raise InvariantViolation('stale definition version','SG-GOV-007')
            definition=IdRegistry().allocate(t,IdSpace.DEFINITION,record_kind='ScopedDefinition')
            t.execute('INSERT INTO concept_definition VALUES(?,?,?,?,?,NULL,?)',
                      (definition.n,cid,version+1,scope,str(self.db.clock.now()),digest))
            t.execute('INSERT INTO definition_metadata VALUES(?,?,?)',(definition.n,int(complete),digest))
            for item in items:
                constraint=IdRegistry().allocate(t,IdSpace.NODE,record_kind='DefinitionConstraint')
                t.execute('INSERT INTO definition_constraint VALUES(?,?,?,?,?,?)',
                          (constraint.n,definition.n,item['class'],item['provenance'],canonical_json(item['expr']),item['evidence']))
            if old:
                t.execute('UPDATE concept_definition SET superseded_by=? WHERE definition_id=? AND superseded_by IS NULL',
                          (definition.n,old['definition_id']))
                # Existing equivalences were proved using the prior definition.
                t.execute("UPDATE identity_mapping SET status='REVOKED',version=version+1 WHERE scope=? AND status='ACTIVE' AND (left_id=? OR right_id=?)",(scope,cid,cid))
            t.audit(Component.PROMOTION_CONTROLLER,'DEFINITION_PUBLISHED',str(definition),canonical_json({'hash':digest,'scope':scope,'version':version+1}))
            return definition.n

    def get(self, concept, scope, version=None):
        with self.db.read() as r:
            row=r.one('SELECT d.*,c.sem_kind,m.complete FROM concept_definition d JOIN concept c USING(concept_id) '
                      'JOIN definition_metadata m USING(definition_id) WHERE c.canonical_label=? AND d.scope=? '+
                      ('AND d.def_version=? ' if version is not None else '')+'ORDER BY d.def_version DESC LIMIT 1',
                      (concept,scope,version) if version is not None else (concept,scope))
            if not row:
                return None
            constraints=[dict(x) for x in r.query('SELECT * FROM definition_constraint WHERE definition_id=? ORDER BY expr',(row['definition_id'],))]
        return {**dict(row),'constraints':constraints}

    def identity_definition(self, concept, scope):
        row=self.get(concept,scope)
        if row is None:
            raise ValueError('no scoped definition')
        essential=frozenset(x['expr'] for x in row['constraints'] if x['class']=='ESSENTIAL' and x['provenance']=='DEFINITIONAL')
        return Definition(row['concept_id'],row['sem_kind'],scope,essential,bool(row['complete']),'DEFINITIONAL')

    def inherit(self, concept, scope):
        """Only defining ESSENTIAL conditions inherit down SUBCLASS_OF."""
        onto=self.service.foundation.ontology
        inherited=[]
        for parent in sorted(onto.ancestors(concept,include_self=True)):
            row=self.get(parent,scope)
            if row:
                for c in row['constraints']:
                    if c['class']=='ESSENTIAL' and c['provenance']=='DEFINITIONAL':
                        inherited.append({'definition':row['definition_id'],'concept':parent,
                                          'expression':json.loads(c['expr']),'scope':scope})
        return inherited

    def audit(self):
        errors=[]
        with self.db.read() as r:
            rows=r.query('SELECT d.*,m.complete,m.content_hash AS metadata_hash,c.canonical_label FROM concept_definition d JOIN definition_metadata m USING(definition_id) JOIN concept c USING(concept_id) ORDER BY definition_id')
            for row in rows:
                constraints=r.query('SELECT * FROM definition_constraint WHERE definition_id=?',(row['definition_id'],))
                items=[{'class':x['class'],'provenance':x['provenance'],'expr':json.loads(x['expr']),'evidence':x['evidence_id']} for x in constraints]
                items.sort(key=canonical_json)
                digest=sha256_hex(canonical_json({'concept':row['canonical_label'],'scope':row['scope'],'complete':bool(row['complete']),'constraints':items}))
                if digest!=row['content_hash'] or digest!=row['metadata_hash']:errors.append(row['definition_id'])
                if row['superseded_by'] is not None:
                    successor=r.one('SELECT concept_id,scope,def_version FROM concept_definition WHERE definition_id=?',(row['superseded_by'],))
                    if successor is None or tuple(successor)!=(row['concept_id'],row['scope'],row['def_version']+1):errors.append(row['definition_id'])
        return {'ok':not errors,'checked_definitions':len(rows),'errors':errors}
