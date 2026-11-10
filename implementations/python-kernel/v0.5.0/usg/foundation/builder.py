"""Assemble and validate the Foundation Package in memory (pure, no database).

The result is deterministic: ``Foundation.content_hash()`` identifies exactly
this package, and installation (usg.foundation.install) refuses to overwrite a
different one (the package is sealed)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..errors import InvariantViolation
from ..model.frames import FrameLibrary
from ..model.relations import RelationDef
from ..ontology import Ontology
from ..util import canonical_json, sha256_hex
from .concepts import DOMAINS, SEED_CONCEPTS
from .frames import FRAMES
from .functions import FN_DERIVED, FN_PRIMITIVES, FUNCTIONS, SEED_FUNCTION_EDGES
from .relations import RELATIONS


@dataclass(frozen=True)
class SeedEdge:
    src: str
    relation: str
    tgt: str
    domain: str = "UNIVERSAL_CORE"
    qualifiers: tuple[tuple[str, str], ...] = ()


@dataclass
class Foundation:
    ontology: Ontology
    relations: dict[str, RelationDef]
    frames: FrameLibrary
    domains: tuple[str, ...]
    edges: tuple[SeedEdge, ...]

    def content_hash(self) -> str:
        payload: dict[str, Any] = {
            "concepts": [{k: v for k, v in self.ontology.seed(n).to_json().items() if k != "disjoint_with"}
                         for n in sorted(self.ontology.concepts())],
            # disjointness is symmetric: hash the set of pairs, not who declared it
            "disjoint": sorted(sorted(p) for p in self.ontology.declared_disjoint_pairs()),
            "relations": [self.relations[n].to_json() for n in sorted(self.relations)],
            "frames": [self.frames.get(n).to_json() for n in sorted(self.frames.names())],
            "edges": sorted([e.src, e.relation, e.tgt, e.domain, [list(q) for q in e.qualifiers]] for e in self.edges),
            "domains": sorted(self.domains),
        }
        return sha256_hex(canonical_json(payload))


def _is_a_edges(onto: Ontology) -> list[SeedEdge]:
    out = []
    for name in onto.concepts():
        seed = onto.seed(name)
        for p in seed.parents:
            out.append(SeedEdge(name, "SUBCLASS_OF", p, seed.domains[0]))
    return out


def _disjoint_edges(onto: Ontology) -> list[SeedEdge]:
    out = []
    for pair in sorted(tuple(sorted(p)) for p in onto.declared_disjoint_pairs()):
        a, b = pair
        out.append(SeedEdge(a, "DISJOINT_WITH", b, onto.seed(a).domains[0]))
    return out


def build_foundation() -> Foundation:
    onto = Ontology().add_all(SEED_CONCEPTS).add_all(f.to_concept() for f in FUNCTIONS)
    onto.assert_valid()

    relations = {r.name: r for r in RELATIONS}
    if len(relations) != len(RELATIONS):
        raise InvariantViolation("duplicate relation names in the catalogue", "I-01")
    for r in relations.values():
        for ref in (r.inverse_of, r.sub_relation_of):
            if ref is not None and ref not in relations:
                raise InvariantViolation(f"relation {r.name} references unknown relation {ref}", "I-02")

    # FN invariants (sealed): exactly six primitives, derived composites defined from primitives
    prim = [f.name for f in FUNCTIONS if not f.derived and f.name in FN_PRIMITIVES]
    if sorted(prim) != sorted(FN_PRIMITIVES):
        raise InvariantViolation("the six FN primitives must all be defined", "SG-FRM-009")
    for f in FUNCTIONS:
        if f.derived and f.name in FN_DERIVED:
            if not f.composed_of or any(c not in FN_PRIMITIVES for c in f.composed_of):
                raise InvariantViolation(f"{f.name} must be composed of primitives only", "SG-FRM-009")

    lib = FrameLibrary(onto, relations).add_all(FRAMES).finalize()

    edges = _is_a_edges(onto) + _disjoint_edges(onto)
    for performer, fn, mode in SEED_FUNCTION_EDGES:
        if not onto.has(performer) or not onto.has(fn):
            raise InvariantViolation(f"unknown concept in function edge {performer}->{fn}", "I-02")
        edges.append(SeedEdge(performer, "HAS_FUNCTION", fn, onto.seed(performer).domains[0], (("mode", mode),)))
    for e in edges:
        if e.relation not in relations:
            raise InvariantViolation(f"seed edge uses unknown relation {e.relation}", "I-02")
    return Foundation(onto, relations, lib, DOMAINS, tuple(edges))
