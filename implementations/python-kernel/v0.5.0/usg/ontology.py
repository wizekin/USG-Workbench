"""In-memory ontology view: concepts, IS_A closure, declared disjointness.

It is the semantic backbone for the three-valued type check (spec Part 3
§3.3.2):

  COMPATIBLE    a class of the value is a subclass of the expected class
  INCOMPATIBLE  every class of the value is provably disjoint from it
  UNDETERMINED  neither is derivable  -> accepted with a warning (open world,
                SG-KNW-001): missing class information is never treated as
                incompatibility.

Concepts are keyed by canonical *name* inside this view. Persisted ids live in
the registry; ``refs`` maps names to ids when the ontology was loaded from the
database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .core.ids import Ref
from .core.kinds import SemKind
from .errors import InvariantViolation


class Compat(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNDETERMINED = "UNDETERMINED"


@dataclass(frozen=True)
class ConceptSeed:
    name: str
    kind: SemKind
    parents: tuple[str, ...] = ()
    domains: tuple[str, ...] = ("UNIVERSAL_CORE",)
    disjoint_with: tuple[str, ...] = ()
    complete: bool = True
    value_domain: str | None = None  # PROPERTY concepts: the VALUE class their values must belong to
    doc: str = ""

    def to_json(self) -> dict:
        return {
            "name": self.name, "kind": self.kind.value, "parents": sorted(self.parents),
            "domains": ([self.domains[0]] + sorted(self.domains[1:])) if self.domains else [],  # primary first
            "disjoint_with": sorted(self.disjoint_with), "complete": self.complete, "value_domain": self.value_domain,
            "doc": self.doc,
        }


class Ontology:
    def __init__(self) -> None:
        self._seeds: dict[str, ConceptSeed] = {}
        self._parents: dict[str, tuple[str, ...]] = {}
        self._disjoint: set[frozenset[str]] = set()
        self._anc_cache: dict[str, frozenset[str]] = {}
        self.refs: dict[str, Ref] = {}
        self.names: dict[Ref, str] = {}

    # -- building ------------------------------------------------------------
    def add(self, seed: ConceptSeed) -> None:
        if seed.name in self._seeds:
            raise InvariantViolation(f"duplicate concept {seed.name!r}", "I-01")
        self._seeds[seed.name] = seed
        self._parents[seed.name] = seed.parents
        for d in seed.disjoint_with:
            self._disjoint.add(frozenset((seed.name, d)))
        self._anc_cache.clear()

    def add_all(self, seeds: Iterable[ConceptSeed]) -> "Ontology":
        for s in seeds:
            self.add(s)
        return self

    def add_disjoint(self, a: str, b: str) -> None:
        self._disjoint.add(frozenset((a, b)))

    def bind_ref(self, name: str, ref: Ref) -> None:
        self.refs[name] = ref
        self.names[ref] = name

    # -- queries ---------------------------------------------------------------
    def has(self, name: str) -> bool:
        return name in self._seeds

    def seed(self, name: str) -> ConceptSeed:
        try:
            return self._seeds[name]
        except KeyError as e:
            raise KeyError(f"unknown concept {name!r}") from e

    def kind_of(self, name: str) -> SemKind:
        return self.seed(name).kind

    def concepts(self) -> list[str]:
        return list(self._seeds)

    def parents_of(self, name: str) -> tuple[str, ...]:
        return self._parents[name]

    def children_of(self, name: str) -> list[str]:
        return [c for c, ps in self._parents.items() if name in ps]

    def ancestors(self, name: str, include_self: bool = False) -> frozenset[str]:
        if name not in self._seeds:
            raise KeyError(f"unknown concept {name!r}")
        cached = self._anc_cache.get(name)
        if cached is None:
            seen: set[str] = set()
            stack = list(self._parents[name])
            while stack:
                n = stack.pop()
                if n in seen:
                    continue
                seen.add(n)
                stack.extend(self._parents.get(n, ()))
            cached = frozenset(seen)
            self._anc_cache[name] = cached
        return cached | {name} if include_self else cached

    def descendants(self, name: str) -> frozenset[str]:
        return frozenset(c for c in self._seeds if name in self.ancestors(c))

    def is_subclass(self, a: str, b: str) -> bool:
        """Reflexive subclass test (a ⊑ b)."""
        return a == b or b in self.ancestors(a)

    def disjoint(self, a: str, b: str) -> bool:
        """Provably disjoint: some ancestor-or-self of a is declared disjoint from some ancestor-or-self of b."""
        if not self._disjoint:
            return False
        xs, ys = self.ancestors(a, True), self.ancestors(b, True)
        return any(frozenset((x, y)) in self._disjoint for x in xs for y in ys)

    def declared_disjoint_pairs(self) -> set[frozenset[str]]:
        return set(self._disjoint)

    # -- three-valued compatibility ---------------------------------------------
    def classes_compatible(self, value_classes: Iterable[str], expected: str) -> Compat:
        classes = [c for c in value_classes if c in self._seeds]
        if not classes:
            return Compat.UNDETERMINED
        if any(self.is_subclass(c, expected) for c in classes):
            return Compat.COMPATIBLE
        if all(self.disjoint(c, expected) for c in classes):
            return Compat.INCOMPATIBLE
        return Compat.UNDETERMINED

    def value_in_domain(self, prop: str, value: str) -> bool:
        """VC-T03: a VALUE must belong to its PROPERTY's value domain."""
        dom = self.seed(prop).value_domain
        return dom is None or self.is_subclass(value, dom)

    # -- validation --------------------------------------------------------------
    def validate(self) -> list[tuple[str, str]]:
        """Return [(code, message)] for every structural problem."""
        issues: list[tuple[str, str]] = []
        for name, seed in self._seeds.items():
            for p in seed.parents:
                if p not in self._seeds:
                    issues.append(("I-02", f"{name}: unknown parent {p!r}"))
                elif self._seeds[p].kind is not seed.kind:
                    issues.append(("SG-KNW-005", f"{name} ({seed.kind.value}) has parent {p} of kind {self._seeds[p].kind.value}"))
            for d in seed.disjoint_with:
                if d not in self._seeds:
                    issues.append(("I-02", f"{name}: unknown disjoint concept {d!r}"))
            if seed.value_domain is not None and seed.value_domain not in self._seeds:
                issues.append(("I-02", f"{name}: unknown value domain {seed.value_domain!r}"))
        # cycles (PROPER subclass structure must be acyclic in the seed ontology)
        for name in self._seeds:
            if any(p in self._seeds and name in self.ancestors(p, True) for p in self._parents[name]):
                issues.append(("VC-G01", f"cycle through {name}"))
        # unsatisfiable concepts: two of its ancestors are declared disjoint (SG-KNW-005 'genuine contradiction')
        for name in self._seeds:
            anc = sorted(self.ancestors(name, True))
            for i, x in enumerate(anc):
                for y in anc[i + 1:]:
                    if frozenset((x, y)) in self._disjoint:
                        issues.append(("SG-KNW-005", f"{name} inherits from disjoint concepts {x} and {y}"))
        return issues

    def assert_valid(self) -> None:
        issues = self.validate()
        if issues:
            code, msg = issues[0]
            raise InvariantViolation(f"{msg} (+{len(issues) - 1} more)" if len(issues) > 1 else msg, code)
