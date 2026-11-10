"""Scoped, reversible concept equivalence. Similarity never proves identity."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from ..autonomy.policy import ActionClass
from ..core.ids import IdSpace
from ..core.values import Component
from ..errors import InvariantViolation, PolicyDenied
from ..storage.registry import IdRegistry
from ..storage.schema import WriterRole
from ..util import canonical_json


@dataclass(frozen=True)
class Definition:
    concept_id: int
    kind: str
    scope: str
    essential: frozenset[str]
    complete: bool = False
    provenance: str = "ASSUMED"


@dataclass(frozen=True)
class Comparison:
    relation: str
    grade: str
    shared: tuple[str, ...]
    differences: tuple[str, ...]


def compare(left: Definition, right: Definition):
    shared = tuple(sorted(left.essential & right.essential))
    diff = tuple(sorted(left.essential ^ right.essential))
    if left.kind != right.kind:
        return Comparison("DISTINCT", "ESTABLISHED", shared, diff)
    if left.scope != right.scope or not left.complete or not right.complete:
        return Comparison("UNDETERMINED", "CANDIDATE", shared, diff)
    if left.essential == right.essential and left.essential and left.provenance == right.provenance == "DEFINITIONAL":
        return Comparison("EQUIVALENT", "ESTABLISHED", shared, diff)
    if left.essential > right.essential:
        return Comparison("SPECIALIZES", "SUPPORTED", shared, diff)
    if right.essential > left.essential:
        return Comparison("GENERALIZES", "SUPPORTED", shared, diff)
    return Comparison("RELATED" if shared else "UNDETERMINED", "CANDIDATE", shared, diff)


class IdentityResolver:
    def __init__(self, db, panel):
        self.db, self.panel = db, panel

    def establish(self, left, right, *, canary_complete=False):
        comparison = compare(left, right)
        if comparison.relation != "EQUIVALENT" or comparison.grade != "ESTABLISHED" or left.concept_id == right.concept_id:
            raise PolicyDenied("equivalence is not established", "SG-IDN-002")
        proof = {"left": {**asdict(left), "essential": sorted(left.essential)},
                 "right": {**asdict(right), "essential": sorted(right.essential)}, "comparison": asdict(comparison)}
        panel = self.panel.evaluate(ActionClass.EQUIVALENCE_ESTABLISHED, proof, rollback_plan=True, canary_complete=canary_complete)
        if not panel.approved:
            raise PolicyDenied(panel.reason, "SG-IDN-002")
        with self.db.write(WriterRole.REGISTRY) as t:
            for d in (left, right):
                row = t.one("SELECT sem_kind,definition_complete FROM concept WHERE concept_id=?", (d.concept_id,))
                if row is None or row["sem_kind"] != d.kind or not row["definition_complete"]:
                    raise InvariantViolation("definition does not match registry", "SG-IDN-002")
                metadata=t.one('SELECT m.complete FROM concept_definition d JOIN definition_metadata m USING(definition_id) WHERE d.concept_id=? AND d.scope=? AND d.superseded_by IS NULL',(d.concept_id,d.scope))
                if metadata is None or not metadata['complete']:
                    raise PolicyDenied('scoped definition completeness is not established','SG-IDN-002')
                stored = t.query("SELECT c.expr FROM definition_constraint c JOIN concept_definition d USING(definition_id) WHERE d.concept_id=? AND d.scope=? AND d.superseded_by IS NULL AND c.class='ESSENTIAL' AND c.provenance='DEFINITIONAL'", (d.concept_id, d.scope))
                if frozenset(x[0] for x in stored) != d.essential:
                    raise PolicyDenied("proof is not bound to stored definitions", "SG-IDN-002")
            mapping = IdRegistry().allocate(t, IdSpace.MAPPING, record_kind="EquivalenceMapping")
            t.execute("INSERT INTO identity_mapping VALUES(?,?,?,?,?,'ACTIVE',?,1)",
                      (mapping.n, left.concept_id, right.concept_id, left.scope, comparison.grade, canonical_json({**proof, "panel": panel.to_json()})))
            t.audit(Component.REGISTRY, "EQUIVALENCE_ESTABLISHED", str(mapping), left.scope)
            return mapping.n

    def canonical_id(self, concept_id, scope):
        with self.db.read() as r:
            rows = r.query("SELECT left_id,right_id FROM identity_mapping WHERE scope=? AND status='ACTIVE' AND grade='ESTABLISHED'", (scope,))
        group, todo = {concept_id}, [concept_id]
        while todo:
            x = todo.pop()
            for row in rows:
                if x in (row[0], row[1]):
                    for y in row:
                        if y not in group:
                            group.add(y)
                            todo.append(y)
        return min(group)

    def revoke(self, mapping_id, reason):
        with self.db.write(WriterRole.REGISTRY) as t:
            t.execute("UPDATE identity_mapping SET status='REVOKED',version=version+1 WHERE mapping_id=? AND status='ACTIVE'", (mapping_id,))
            t.audit(Component.REGISTRY, "EQUIVALENCE_REVOKED", f"MAPPING:{mapping_id}", reason)
