"""Time (spec Part 3 §3.9): Allen's thirteen interval relations, an exact
consistency check, and deterministic resolution of relative expressions.

Resolution is plain Python, never a model call. A relative expression resolves
only against a source anchor (E-14); without one it stays unresolved, and vague
expressions ("recently") are never turned into dates. A resolved value is stored
ALONGSIDE the original expression (normalization N6), never instead of it.

Intervals are half-open ``[start, end)``. A date-only INSTANT is the one-day
interval ``[d, d+1)``; a date-time INSTANT has no extent and takes no part in
interval reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Sequence

from ..core.records import Anchor
from .node import ALLEN, Node, walk
from .serialize import canonical_string

# ---------------------------------------------------------------------------
# Allen's thirteen relations
# ---------------------------------------------------------------------------
CONVERSE: dict[str, str] = {
    "BEFORE": "AFTER", "AFTER": "BEFORE", "MEETS": "MET_BY", "MET_BY": "MEETS",
    "OVERLAPS": "OVERLAPPED_BY", "OVERLAPPED_BY": "OVERLAPS", "STARTS": "STARTED_BY", "STARTED_BY": "STARTS",
    "DURING": "CONTAINS", "CONTAINS": "DURING", "FINISHES": "FINISHED_BY", "FINISHED_BY": "FINISHES",
    "EQUALS": "EQUALS",
}
assert set(CONVERSE) == set(ALLEN) and len(ALLEN) == 13

# Each relation as endpoint constraints between interval a=[a-,a+] and b=[b-,b+].
_EP: dict[str, list[tuple[str, str, str]]] = {
    "BEFORE": [("a+", "<", "b-")],
    "AFTER": [("b+", "<", "a-")],
    "MEETS": [("a+", "=", "b-")],
    "MET_BY": [("b+", "=", "a-")],
    "OVERLAPS": [("a-", "<", "b-"), ("b-", "<", "a+"), ("a+", "<", "b+")],
    "OVERLAPPED_BY": [("b-", "<", "a-"), ("a-", "<", "b+"), ("b+", "<", "a+")],
    "STARTS": [("a-", "=", "b-"), ("a+", "<", "b+")],
    "STARTED_BY": [("a-", "=", "b-"), ("b+", "<", "a+")],
    "DURING": [("b-", "<", "a-"), ("a+", "<", "b+")],
    "CONTAINS": [("a-", "<", "b-"), ("b+", "<", "a+")],
    "FINISHES": [("b-", "<", "a-"), ("a+", "=", "b+")],
    "FINISHED_BY": [("a-", "<", "b-"), ("a+", "=", "b+")],
    "EQUALS": [("a-", "=", "b-"), ("a+", "=", "b+")],
}


def converse(rel: str) -> str:
    return CONVERSE[rel]


def allen_relation(a_start: Any, a_end: Any, b_start: Any, b_end: Any) -> str:
    """The unique Allen relation between two proper intervals (start < end)."""
    if not (a_start < a_end and b_start < b_end):
        raise ValueError("intervals must have start < end")
    val = {"a-": a_start, "a+": a_end, "b-": b_start, "b+": b_end}
    hits = [r for r, cs in _EP.items() if all((val[x] < val[y]) if op == "<" else (val[x] == val[y]) for x, op, y in cs)]
    if len(hits) != 1:  # pragma: no cover - the thirteen relations are exhaustive and exclusive
        raise AssertionError(f"expected exactly one Allen relation, got {hits}")
    return hits[0]


def check_consistency(constraints: Sequence[tuple[str, str, str]]) -> tuple[bool, str]:
    """Are the basic Allen constraints ``(relation, name_a, name_b)`` jointly satisfiable?

    Every basic relation is a conjunction of point constraints (< or =), so the set is
    consistent iff, after merging equal endpoints, the strict-order graph has no cycle.
    This is exact for single basic relations per pair (no disjunctions)."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    points: list[tuple[str, str, str]] = []
    names: set[str] = set()
    for rel, a, b in constraints:
        if rel not in _EP:
            return False, f"unknown Allen relation {rel!r}"
        names.update((a, b))
        for x, op, y in _EP[rel]:
            points.append(((a if x[0] == "a" else b) + x[1], op, (a if y[0] == "a" else b) + y[1]))
    for n in names:
        points.append((n + "-", "<", n + "+"))  # every interval has positive extent
    for lhs, op, rhs in points:
        if op == "=":
            parent[find(lhs)] = find(rhs)
    edges: dict[str, set[str]] = {}
    for lhs, op, rhs in points:
        if op == "<":
            u, v = find(lhs), find(rhs)
            if u == v:
                return False, f"{lhs} < {rhs} contradicts an equality"
            edges.setdefault(u, set()).add(v)
    state: dict[str, int] = {}

    def dfs(u: str) -> bool:
        state[u] = 1
        for v in edges.get(u, ()):
            if state.get(v) == 1 or (v not in state and dfs(v)):
                return True
        state[u] = 2
        return False

    for u in list(edges):
        if u not in state and dfs(u):
            return False, "the temporal constraints require a strict-order cycle"
    return True, "ok"


# ---------------------------------------------------------------------------
# Dates and intervals
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DateInterval:
    start: date
    end: date  # exclusive

    def __post_init__(self):
        if not self.start < self.end:
            raise ValueError("interval needs start < end")

    def iso(self) -> tuple[str, str]:
        return self.start.isoformat(), self.end.isoformat()


def _parse_date(s: Any) -> date | None:
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def parse_interval(form: str, value: str) -> DateInterval | None:
    """TIME_LIT -> DateInterval where it has a calendar extent, else None."""
    if form == "INSTANT":
        d = _parse_date(value)
        return DateInterval(d, d + timedelta(days=1)) if d else None
    if form == "INTERVAL":
        a, _, b = value.partition("/")
        da, db = _parse_date(a), _parse_date(b)
        return DateInterval(da, db) if da and db and da < db else None
    return None


# ---------------------------------------------------------------------------
# Resolution of relative expressions
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Resolved:
    start: str
    end: str  # exclusive
    rule: str


@dataclass(frozen=True)
class Unresolved:
    reason: str


VAGUE = frozenset({"RECENTLY", "EARLIER", "LATER", "SOON", "LONG_AGO", "LATELY", "NOWADAYS", "FORMERLY", "SOMETIME"})
WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


def anchor_date(anchor: Anchor | None) -> date | None:
    if anchor is None:
        return None
    if anchor.document_date:
        return _parse_date(anchor.document_date)
    if anchor.speech_time:
        return _parse_date(anchor.speech_time[:10])
    return None


def _month_start(d: date, delta: int) -> date:
    m = d.month - 1 + delta
    return date(d.year + m // 12, m % 12 + 1, 1)


def resolve_relative(expr: str, anchor: Anchor | None, *, week_start: int = 0) -> Resolved | Unresolved:
    """Resolve a relative time expression against the source anchor.

    Supported: TODAY, YESTERDAY, TOMORROW, DAYS_AGO:n, IN_DAYS:n, LAST/THIS/NEXT_WEEK|MONTH|YEAR,
    LAST_<WEEKDAY>, NEXT_<WEEKDAY>. Everything else (vague, ambiguous "THIS_<WEEKDAY>") is UNRESOLVED."""
    if expr in VAGUE:
        return Unresolved("vague expressions are never turned into dates")
    if anchor is not None and anchor.calendar != "gregorian":
        return Unresolved(f"unsupported calendar {anchor.calendar!r}")
    d = anchor_date(anchor)
    if d is None:
        return Unresolved("no anchor date: a relative expression cannot be resolved")

    def day(off: int, rule: str) -> Resolved:
        s = d + timedelta(days=off)
        return Resolved(s.isoformat(), (s + timedelta(days=1)).isoformat(), rule)

    fixed = {"TODAY": 0, "YESTERDAY": -1, "TOMORROW": 1, "DAY_BEFORE_YESTERDAY": -2, "DAY_AFTER_TOMORROW": 2}
    if expr in fixed:
        return day(fixed[expr], expr)
    name, _, arg = expr.partition(":")
    if name in ("DAYS_AGO", "IN_DAYS"):
        if not arg.isdigit():
            return Unresolved(f"{name} needs a count")
        n = int(arg)
        return day(-n if name == "DAYS_AGO" else n, name)
    if name in ("LAST_WEEK", "THIS_WEEK", "NEXT_WEEK"):
        start = d - timedelta(days=(d.weekday() - week_start) % 7)
        s = start + timedelta(days={"LAST_WEEK": -7, "THIS_WEEK": 0, "NEXT_WEEK": 7}[name])
        return Resolved(s.isoformat(), (s + timedelta(days=7)).isoformat(), name)
    if name in ("LAST_MONTH", "THIS_MONTH", "NEXT_MONTH"):
        off = {"LAST_MONTH": -1, "THIS_MONTH": 0, "NEXT_MONTH": 1}[name]
        return Resolved(_month_start(d, off).isoformat(), _month_start(d, off + 1).isoformat(), name)
    if name in ("LAST_YEAR", "THIS_YEAR", "NEXT_YEAR"):
        y = d.year + {"LAST_YEAR": -1, "THIS_YEAR": 0, "NEXT_YEAR": 1}[name]
        return Resolved(date(y, 1, 1).isoformat(), date(y + 1, 1, 1).isoformat(), name)
    for prefix in ("LAST_", "NEXT_"):
        if name.startswith(prefix) and name[len(prefix):] in WEEKDAYS:
            target = WEEKDAYS.index(name[len(prefix):])
            delta = (d.weekday() - target) % 7 if prefix == "LAST_" else (target - d.weekday()) % 7
            delta = delta or 7  # strictly before / after the anchor date
            return day(-delta if prefix == "LAST_" else delta, name)
    if name.startswith("THIS_") and name[5:] in WEEKDAYS:
        return Unresolved("'this <weekday>' is ambiguous without discourse context")
    return Unresolved(f"unknown relative expression {expr!r}")


def resolve_node(node: Node, anchor: Anchor | None, *, week_start: int = 0) -> Node:
    """Add resolved bounds NEXT TO the relative expression of a TIME_REL node (N6)."""
    if node.op != "TIME_REL" or node.get("resolved_start") is not None:
        return node
    r = resolve_relative(node.get("expr"), anchor, week_start=week_start)
    if isinstance(r, Unresolved):
        return node
    return Node("TIME_REL", (), {"expr": node.get("expr"), "resolved_start": r.start, "resolved_end": r.end}, node.ann)


def interval_of(node: Node) -> DateInterval | None:
    if node.op == "TIME_LIT":
        return parse_interval(node.get("form"), node.get("value"))
    if node.op == "TIME_REL" and node.get("resolved_start") is not None:
        a, b = _parse_date(node.get("resolved_start")), _parse_date(node.get("resolved_end"))
        return DateInterval(a, b) if a and b and a < b else None
    return None


def check_temporal(root: Node) -> list[tuple[str, str]]:
    """VC-G06: TEMPORAL constraints in an expression must be jointly satisfiable, and any relation between
    two CONCRETE intervals must actually hold."""
    issues: list[tuple[str, str]] = []
    names: dict[str, str] = {}
    cons: list[tuple[str, str, str]] = []
    for _, n in walk(root):
        if n.op != "TEMPORAL":
            continue
        t1, t2 = n.args
        rel = n.get("allen")
        for t in (t1, t2):
            names.setdefault(canonical_string(t), f"t{len(names)}")
        cons.append((rel, names[canonical_string(t1)], names[canonical_string(t2)]))
        i1, i2 = interval_of(t1), interval_of(t2)
        if i1 and i2:
            actual = allen_relation(i1.start, i1.end, i2.start, i2.end)
            if actual != rel:
                issues.append(("VC-G06", f"TEMPORAL claims {rel} but the intervals are in relation {actual}"))
    ok, why = check_consistency(cons)
    if not ok:
        issues.append(("VC-G06", f"temporal constraints are unsatisfiable: {why}"))
    return issues
