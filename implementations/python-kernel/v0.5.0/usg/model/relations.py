"""Relation definitions and edge-level constraints (spec Part 2 §2.8).

Three categories: LOGICAL (formal, may support inference), ASSOCIATIVE (retrieval
aid only, the only category that may carry weights) and EPISTEMIC (needs
evidence/uncertainty, no weights). Cycles are allowed or forbidden *per
relation*, never globally.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

from ..core.kinds import SemKind
from ..errors import InvariantViolation


class RelationCategory(str, Enum):
    LOGICAL = "LOGICAL"
    ASSOCIATIVE = "ASSOCIATIVE"
    EPISTEMIC = "EPISTEMIC"


@dataclass(frozen=True)
class RelationDef:
    name: str
    category: RelationCategory
    domain_kind: SemKind | None = None
    range_kind: SemKind | None = None
    reflexive: bool = False
    irreflexive: bool = False
    symmetric: bool = False
    asymmetric: bool = False
    transitive: bool = False
    functional: bool = False
    inverse_of: str | None = None
    sub_relation_of: str | None = None
    cycles_allowed: bool = False
    defeasible: bool = False
    reasoning_policy: str = "OPEN_WORLD"
    description: str = ""
    version: int = 1

    def __post_init__(self):
        def bad(msg: str):
            raise InvariantViolation(f"relation {self.name}: {msg}", "SG-KNW-012")

        if self.symmetric and self.asymmetric:
            bad("cannot be both symmetric and asymmetric")
        if self.reflexive and self.irreflexive:
            bad("cannot be both reflexive and irreflexive")
        if self.asymmetric and self.reflexive:
            bad("asymmetric relations cannot be reflexive")
        if (self.asymmetric or (self.transitive and self.irreflexive)) and self.cycles_allowed:
            bad("asymmetric / strict-transitive relations are acyclic; cycles_allowed must be False")
        if self.defeasible and self.category is RelationCategory.LOGICAL:
            bad("defeasible relations are not LOGICAL")
        if self.reasoning_policy not in ("OPEN_WORLD", "CLOSED_WORLD"):
            bad("reasoning_policy must be OPEN_WORLD or CLOSED_WORLD")

    @property
    def weights_allowed(self) -> bool:
        """SG-KNW-002: only ASSOCIATIVE edges may carry a weight."""
        return self.category is RelationCategory.ASSOCIATIVE

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name, "category": self.category.value,
            "domain_kind": self.domain_kind.value if self.domain_kind else None,
            "range_kind": self.range_kind.value if self.range_kind else None,
            "reflexive": self.reflexive, "irreflexive": self.irreflexive, "symmetric": self.symmetric,
            "asymmetric": self.asymmetric, "transitive": self.transitive, "functional": self.functional,
            "inverse_of": self.inverse_of, "sub_relation_of": self.sub_relation_of,
            "cycles_allowed": self.cycles_allowed, "defeasible": self.defeasible,
            "reasoning_policy": self.reasoning_policy, "description": self.description, "version": self.version,
        }

    @staticmethod
    def from_json(d: Mapping[str, Any]) -> "RelationDef":
        return RelationDef(
            name=d["name"], category=RelationCategory(d["category"]),
            domain_kind=SemKind(d["domain_kind"]) if d.get("domain_kind") else None,
            range_kind=SemKind(d["range_kind"]) if d.get("range_kind") else None,
            reflexive=d.get("reflexive", False), irreflexive=d.get("irreflexive", False),
            symmetric=d.get("symmetric", False), asymmetric=d.get("asymmetric", False),
            transitive=d.get("transitive", False), functional=d.get("functional", False),
            inverse_of=d.get("inverse_of"), sub_relation_of=d.get("sub_relation_of"),
            cycles_allowed=d.get("cycles_allowed", False), defeasible=d.get("defeasible", False),
            reasoning_policy=d.get("reasoning_policy", "OPEN_WORLD"), description=d.get("description", ""),
            version=d.get("version", 1),
        )


def reaches(adj: Mapping[Any, Iterable[Any]], start: Any, goal: Any) -> bool:
    """Is ``goal`` reachable from ``start`` following ``adj``? (iterative DFS)"""
    seen = {start}
    stack = [start]
    while stack:
        n = stack.pop()
        if n == goal:
            return True
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return False


def check_edge(rel: RelationDef, src: Any, tgt: Any, adj: Mapping[Any, Iterable[Any]],
               weight: float | None = None) -> tuple[str, str] | None:
    """Validate adding edge ``src -rel-> tgt`` against the relation's logical
    properties given the existing adjacency ``adj`` of that relation.
    Returns ``(code, message)`` for the first violation, else None.

    VC-G01  acyclicity   VC-G02  declared properties   SG-KNW-002  weights
    """
    if weight is not None and not rel.weights_allowed:
        return ("SG-KNW-002", f"{rel.name} is {rel.category.value}: weights are only allowed on ASSOCIATIVE relations")
    if src == tgt and rel.irreflexive:
        return ("VC-G02", f"{rel.name} is irreflexive; self-edge {src} rejected")
    if src == tgt and rel.asymmetric:
        return ("VC-G02", f"{rel.name} is asymmetric; self-edge {src} rejected")
    if rel.asymmetric and src in set(adj.get(tgt, ())):
        return ("VC-G02", f"{rel.name} is asymmetric; reverse edge {tgt}->{src} already exists")
    if not rel.cycles_allowed and src != tgt and reaches(adj, tgt, src):
        return ("VC-G01", f"{rel.name} is acyclic; edge {src}->{tgt} would close a cycle")
    return None
