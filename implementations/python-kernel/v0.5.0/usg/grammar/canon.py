"""Canonicalization (spec Part 3 §3.17).

PERMITTED normalizations (each preserves meaning within its declared scope):
  SG-CAN-020  flatten and sort AND/OR children - associativity and commutativity ONLY
  SG-CAN-021  alpha-rename bound variables (v0, v1, ... in order of binder occurrence)
  SG-CAN-022  time normalization: resolved bounds are added NEXT TO the relative expression
  SG-CAN-023  inverse-relation normalization (canonical direction = alphabetically first name)
  SG-CAN-024  symmetric argument ordering (symmetric relations, SAME_AS, DIFFERENT_FROM)
  (N1 - implicit HOLDS - is done by the builders; N4 voice mapping belongs to the interpreter.)

FORBIDDEN (SG-CAN-002) - this module deliberately does none of them:
  * double negation is NOT eliminated ("not uncommon" != "common")
  * quantifiers are not moved across negation
  * duplicate conjuncts are NOT removed (A and A -> A is a logical simplification)
  * an offer is never normalised into a completed transfer; modality/tense are never dropped

``canonicalize`` is idempotent, preserves validity, and records every rule it
applied in an audit trace (SG-CAN-003). Annotations are carried along unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ..core.records import Anchor
from ..model.relations import RelationDef
from .node import Node
from .scope import alpha_rename, to_debruijn
from .serialize import canonical_string
from .timeval import resolve_node

CANON_RULES: dict[str, str] = {
    "SG-CAN-020": "flatten and sort AND/OR children (associativity and commutativity only)",
    "SG-CAN-021": "alpha-rename bound variables",
    "SG-CAN-022": "time normalization: resolved bounds alongside the relative expression",
    "SG-CAN-023": "inverse-relation normalization",
    "SG-CAN-024": "symmetric argument ordering",
}

_SYMMETRIC_OPS = frozenset({"SAME_AS", "DIFFERENT_FROM"})


@dataclass
class CanonTrace:
    """Audit trail of applied rules (SG-CAN-003)."""

    entries: list[tuple[str, str]] = field(default_factory=list)

    def add(self, rule: str, op: str) -> None:
        self.entries.append((rule, op))

    def rules(self) -> set[str]:
        return {r for r, _ in self.entries}


def _key(n: Node, env: tuple[str, ...]) -> str:
    """Order-independent sort key: variables become binding distances (see scope.to_debruijn)."""
    return canonical_string(to_debruijn(n, env))


def canonicalize(node: Node, *, anchor: Anchor | None = None, relations: Mapping[str, RelationDef] | None = None,
                 trace: CanonTrace | None = None, week_start: int = 0) -> Node:
    t = trace if trace is not None else CanonTrace()
    out = _canon(node, anchor, relations or {}, t, week_start, ())
    renamed = alpha_rename(out)
    if canonical_string(renamed) != canonical_string(out):
        t.add("SG-CAN-021", "Q")
    return renamed


def _canon(node: Node, anchor, relations, t: CanonTrace, week_start: int, env: tuple[str, ...]) -> Node:
    if node.op == "Q":
        inner = env + (node.get("var"),)
        args = tuple(_canon(a, anchor, relations, t, week_start, inner if i < 2 else env) for i, a in enumerate(node.args))
    elif node.op == "QUANTIFIER":
        # Identity-bound variables are never alpha-renamed or reordered by legacy Q rules.
        args = tuple(_canon(a, anchor, relations, t, week_start, env) for a in node.args)
    else:
        args = tuple(_canon(a, anchor, relations, t, week_start, env) for a in node.args)
    n = Node(node.op, args, node.params, node.ann)
    op = n.op

    if op in ("AND", "OR"):
        flat: list[Node] = []
        for a in n.args:
            if a.op == op:
                flat.extend(a.args)
            else:
                flat.append(a)
        ordered = sorted(flat, key=lambda x: _key(x, env))
        if tuple(ordered) != n.args:
            t.add("SG-CAN-020", op)
        return Node(op, tuple(ordered), n.params, n.ann)

    if op == "RELATE":
        rel = n.get("relation")
        rd = relations.get(rel)
        a, b = n.args
        if rd is not None:
            inv = rd.inverse_of
            if inv and inv in relations and inv < rel:  # canonical direction: alphabetically first of the pair
                t.add("SG-CAN-023", op)
                return Node("RELATE", (b, a), {"relation": inv}, n.ann)
            if rd.symmetric and _key(b, env) < _key(a, env):
                t.add("SG-CAN-024", op)
                return Node("RELATE", (b, a), n.params, n.ann)
        return n

    if op in _SYMMETRIC_OPS:
        a, b = n.args
        if _key(b, env) < _key(a, env):
            t.add("SG-CAN-024", op)
            return Node(op, (b, a), n.params, n.ann)
        return n

    if op == "TIME_REL":
        r = resolve_node(n, anchor, week_start=week_start)
        if r is not n:
            t.add("SG-CAN-022", op)
        return r

    return n
