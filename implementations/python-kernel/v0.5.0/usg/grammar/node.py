"""Expression grammar v1.0 (spec Part 3): a uniform, immutable AST.

Every construct is a ``Node(op, args, params, ann)``. Five *sorts* (TERM, SIT,
PROP, VAL, TIME) classify nodes; operators accept only the sorts in their
signature (SG-CON-006). A situation (SIT) becomes a truth-evaluable proposition
(PROP) only through ``HOLDS``: describing a situation never asserts that it
happened, and a negated situation is never stored as an occurred event
(SG-CON-009). Annotations (spans, rules, basis, language features) live in a
separate channel that is EXCLUDED from structural equality and hashing
(SG-CAN-004).

Params are restricted to strings, ints, bools, None and tuples of those, so
every node serialises canonically (no binary floats).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from typing import Any, Iterable, Iterator, Mapping, Sequence

from ..core.ids import Ref
from ..core.kinds import Sort
from ..errors import InvariantViolation

ANY = "ANY"
TERM, SIT, PROP, VAL, TIME = Sort.TERM, Sort.SIT, Sort.PROP, Sort.VAL, Sort.TIME

# ---------------------------------------------------------------------------
# Enumerated parameter values
# ---------------------------------------------------------------------------
QUANTIFIERS = frozenset({"EXISTS", "FORALL", "NO", "EXACTLY", "AT_LEAST", "AT_MOST", "MOST", "MANY", "FEW", "GEN"})
COUNT_QUANTIFIERS = frozenset({"EXACTLY", "AT_LEAST", "AT_MOST"})
FORCES = frozenset({"POSSIBILITY", "NECESSITY"})
FLAVORS = frozenset({"EPISTEMIC", "DEONTIC", "DYNAMIC", "CIRCUMSTANTIAL"})
TENSES = frozenset({"PAST", "PRESENT", "FUTURE"})
ASPECTS = frozenset({"PERFECTIVE", "IMPERFECTIVE", "PROGRESSIVE", "PERFECT", "HABITUAL", "PROSPECTIVE"})
ALLEN = frozenset({"BEFORE", "AFTER", "MEETS", "MET_BY", "OVERLAPS", "OVERLAPPED_BY", "STARTS", "STARTED_BY",
                   "DURING", "CONTAINS", "FINISHES", "FINISHED_BY", "EQUALS"})
ATTRIBUTE_MODES = frozenset({"BELIEF", "REPORT", "PERCEPTION", "INFERENCE", "HEARSAY", "EVIDENTIAL_MARKER"})
COMP_KINDS = frozenset({"SEQUENCE", "PARALLEL", "CONDITION", "LOOP", "DEPENDENCY", "ALTERNATIVE", "SUBPROCESS"})
HOLE_STATES = frozenset({"UNSPECIFIED", "UNKNOWN", "NOT_APPLICABLE", "WITHHELD"})
IDENTITY_SCOPES = frozenset({"DISCOURSE", "RESOLVED_WORLD", "WITHIN"})
TIME_FORMS = frozenset({"INSTANT", "INTERVAL", "DURATION", "PARTIAL"})

_SCALARS = (str, int, bool, type(None))


# ---------------------------------------------------------------------------
# Signatures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Sig:
    result: Any  # a Sort, or ANY (polymorphic)
    fixed: tuple = ()  # required leading argument sorts (a Sort or a tuple of Sorts)
    optional: tuple = ()  # optional trailing argument sorts
    variadic: Any = None  # sort of unlimited extra args (after ``fixed``)
    min_var: int = 0
    any_args: bool = False  # APPLY: fillers of any sort; arity is tied to the 'roles' param
    required: tuple[str, ...] = ()
    allowed: tuple[str, ...] = ()


_SIGS: dict[str, Sig] = {
    "REF": Sig(TERM, required=("ref",)),
    "KIND": Sig(TERM, required=("concept",)),
    "VAR": Sig(TERM, required=("name",), allowed=("binderId",)),
    "REIFY": Sig(TERM, fixed=((SIT, PROP),)),
    "LIT": Sig(VAL, required=("value", "vtype"), allowed=("unit",)),
    "VALUE": Sig(VAL, required=("concept",)),
    "HOLE": Sig(ANY, required=("state",)),
    "TIME_LIT": Sig(TIME, required=("form", "value")),
    "TIME_REL": Sig(TIME, required=("expr",), allowed=("resolved_start", "resolved_end")),
    "SPEECH_TIME": Sig(TIME),
    "UNRESOLVED_TIME": Sig(TIME, required=("text",), allowed=("span",)),
    "EXTENT": Sig(TIME, fixed=(SIT,)),
    "APPLY": Sig(SIT, any_args=True, required=("frame", "version", "roles")),
    "PREDICATE_APP": Sig(SIT, any_args=True, required=("predicate", "roles"),
        allowed=("argumentRequirements", "argumentBindings", "eventFrame", "grammaticalTense",
                 "aspect", "temporalFrame", "attribution", "provenance", "completeness",
                 "evidenceRefs", "nativeSourceClaimId")),
    "CONNECTIVE": Sig(PROP, variadic=PROP, min_var=2, required=("connective", "operandRoles"),
        allowed=("marker", "logicalStatus", "antecedentInterpretation", "conditionMetadata",
                 "disjunctionSemantics", "attribution", "evidenceRefs")),
    "QUANTIFIER": Sig(PROP, fixed=(PROP,), required=("operatorType", "operator", "binderId", "variable", "scopeKind"),
        allowed=("restrictor", "variableBinding", "count", "surfaceText", "evidenceRefs", "attribution")),
    "ASPECT": Sig(SIT, fixed=(SIT,), required=("aspect",)),
    "COMPOSE": Sig(SIT, variadic=SIT, min_var=2, required=("kind",)),
    "HOLDS": Sig(PROP, fixed=(SIT,)),
    "RELATE": Sig(PROP, fixed=(TERM, TERM), required=("relation",)),
    "PROPERTY": Sig(PROP, fixed=(TERM, VAL), optional=(VAL,), required=("property",)),
    "NOT": Sig(PROP, fixed=(PROP,)),
    "AND": Sig(PROP, variadic=PROP, min_var=2),
    "OR": Sig(PROP, variadic=PROP, min_var=2),
    "IMPLIES": Sig(PROP, fixed=(PROP, PROP)),
    "COND": Sig(PROP, fixed=(PROP, PROP)),
    "COUNTERFACTUAL": Sig(PROP, fixed=(PROP, PROP)),
    "Q": Sig(PROP, fixed=(PROP, PROP), optional=(TERM,), required=("quant", "var"), allowed=("n",)),
    "MODAL": Sig(PROP, fixed=(PROP,), required=("force", "flavor")),
    "TENSE": Sig(PROP, fixed=(TIME, PROP), required=("tense",)),
    "TEMPORAL": Sig(PROP, fixed=(TIME, TIME), required=("allen",)),
    "ATTRIBUTE": Sig(PROP, fixed=(TERM, PROP), required=("mode",)),
    "SAME_AS": Sig(PROP, fixed=(TERM, TERM), required=("scope",)),
    "DIFFERENT_FROM": Sig(PROP, fixed=(TERM, TERM), allowed=("scope",)),
    "DIRECT": Sig(PROP, fixed=(TERM, SIT)),
    "FIG": Sig(PROP, fixed=(ANY, ANY), required=("mapping",)),
    "ALT": Sig(ANY, variadic=ANY, min_var=2, required=("group", "ranks")),
    "ASSERT": Sig(PROP, fixed=(PROP,), allowed=("origin", "commitment", "context", "definition", "alt_group")),
    "ERROR": Sig(ANY, required=("code",), allowed=("span", "detail")),
}

OPS = frozenset(_SIGS)


def signature(op: str) -> Sig:
    return _SIGS[op]


# ---------------------------------------------------------------------------
# Annotations and nodes
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Ann:
    """How a node was derived. Never changes what it means; excluded from equality."""

    spans: tuple[tuple[int, int], ...] = ()
    rules: tuple[str, ...] = ()
    basis: str | None = None  # EXPLICIT | GRAMMATICAL | BACKGROUND
    features: tuple[tuple[str, str], ...] = ()


def _norm_value(v: Any) -> Any:
    if isinstance(v, bool) or v is None or isinstance(v, (str, int)):
        return v
    if isinstance(v, float):
        raise InvariantViolation("expression params use ints/strings, not binary floats", "SG-CON-006")
    if isinstance(v, (list, tuple)):
        return tuple(_norm_value(x) for x in v)
    if isinstance(v, Ref):
        return str(v)
    raise InvariantViolation(f"unsupported param value {v!r}", "SG-CON-006")


def _arg_ok(actual: Any, expected: Any) -> bool:
    if actual == ANY or expected == ANY:
        return True
    if isinstance(expected, tuple):
        return actual in expected
    return actual == expected


def _fmt_sort(s: Any) -> str:
    if isinstance(s, tuple):
        return "|".join(x.value for x in s)
    return s.value if isinstance(s, Sort) else str(s)


@dataclass(frozen=True)
class Node:
    op: str
    args: tuple["Node", ...] = ()
    params: tuple[tuple[str, Any], ...] = ()
    ann: Ann | None = field(default=None, compare=False)

    def __post_init__(self):
        if self.op not in _SIGS:
            raise InvariantViolation(f"unknown operator {self.op!r}", "SG-CON-006")
        raw = dict(self.params) if not isinstance(self.params, dict) else self.params
        norm = tuple(sorted((k, _norm_value(v)) for k, v in dict(raw).items()))
        object.__setattr__(self, "params", norm)
        object.__setattr__(self, "args", tuple(self.args))
        sig = _SIGS[self.op]
        keys = {k for k, _ in norm}
        missing = [k for k in sig.required if k not in keys]
        if missing:
            raise InvariantViolation(f"{self.op}: missing params {missing}", "SG-CON-006")
        extra = keys - set(sig.required) - set(sig.allowed)
        if extra:
            raise InvariantViolation(f"{self.op}: unexpected params {sorted(extra)}", "SG-CON-006")
        self._check_args(sig)

    def _check_args(self, sig: Sig) -> None:
        n = len(self.args)
        sorts = [sort_of(a) for a in self.args]
        if sig.any_args:
            roles = self.get("roles")
            if not isinstance(roles, tuple) or len(roles) != n:
                raise InvariantViolation(f"{self.op}: {n} fillers but roles={roles!r}", "SG-CON-006")
            if any(not isinstance(role, str) or not role.strip() for role in roles):
                raise InvariantViolation(f"{self.op}: every role must be a non-empty string", "SG-CON-006")
            return
        lo = len(sig.fixed)
        hi = lo + len(sig.optional) if sig.variadic is None else None
        if sig.variadic is not None:
            lo += sig.min_var
        if n < lo or (hi is not None and n > hi):
            raise InvariantViolation(f"{self.op}: expects {lo}{'+' if hi is None else '..' + str(hi)} args, got {n}", "SG-CON-006")
        expected = list(sig.fixed) + list(sig.optional)
        for i, a in enumerate(sorts):
            exp = expected[i] if i < len(expected) else sig.variadic
            if not _arg_ok(a, exp):
                hint = ""
                if exp == PROP and a == SIT:
                    hint = " (wrap the situation in HOLDS: negation/modality apply to propositions, SG-CON-009)"
                raise InvariantViolation(
                    f"{self.op} arg {i}: expected {_fmt_sort(exp)}, got {_fmt_sort(a)}{hint}", "SG-CON-006")
        if self.op == "ALT":
            known = {s for s in sorts if s != ANY}
            if len(known) > 1:
                raise InvariantViolation("ALT members must all have the same sort", "SG-CON-007")
            ranks = self.get("ranks")
            if not isinstance(ranks, tuple) or len(ranks) != n:
                raise InvariantViolation("ALT needs one ordinal rank per alternative", "SG-CON-007")
        if self.op == "FIG":
            a, b = sorts
            if a != ANY and b != ANY and a != b:
                raise InvariantViolation("FIG relates two expressions of the same sort", "SG-TYP-002")
        if self.op == "CONNECTIVE":
            roles = self.get("operandRoles")
            if not isinstance(roles, tuple) or len(roles) != n:
                raise InvariantViolation("CONNECTIVE requires exactly one operand role per proposition", "SG-CON-006")
            if any(not isinstance(role, str) or not role.strip() for role in roles):
                raise InvariantViolation("CONNECTIVE operand roles must be non-empty strings", "SG-CON-006")
            if len(set(roles)) != len(roles):
                raise InvariantViolation("CONNECTIVE operand roles must be unique", "SG-CON-006")
            if self.get("connective") == "CONDITIONAL" and roles != ("antecedent", "consequent"):
                raise InvariantViolation("CONDITIONAL requires ordered antecedent and consequent roles", "SG-CON-006")
        if self.op == "QUANTIFIER":
            if not all(isinstance(self.get(k), str) and self.get(k).strip()
                       for k in ("operatorType", "operator", "binderId", "variable", "scopeKind")):
                raise InvariantViolation("QUANTIFIER binder and operator identifiers must be non-empty strings", "SG-CON-006")
            count = self.get("count")
            if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count < 0):
                raise InvariantViolation("QUANTIFIER count must be a non-negative integer", "SG-CON-006")

    # -- accessors ---------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        for k, v in self.params:
            if k == key:
                return v
        return default

    def params_dict(self) -> dict[str, Any]:
        return dict(self.params)

    @property
    def sort(self) -> Any:
        return sort_of(self)

    def with_ann(self, ann: Ann | None) -> "Node":
        return replace(self, ann=ann)

    def with_args(self, args: Iterable["Node"]) -> "Node":
        return Node(self.op, tuple(args), self.params, self.ann)

    def __str__(self) -> str:
        return pretty(self)


def sort_of(node: Node) -> Any:
    sig = _SIGS[node.op]
    if sig.result != ANY:
        return sig.result
    if node.op == "ALT":
        for a in node.args:
            s = sort_of(a)
            if s != ANY:
                return s
    return ANY


def walk(node: Node, path: tuple[int, ...] = ()) -> Iterator[tuple[tuple[int, ...], Node]]:
    """Pre-order traversal yielding (path, node)."""
    yield path, node
    for i, a in enumerate(node.args):
        yield from walk(a, path + (i,))


def depth(node: Node) -> int:
    return 1 + max((depth(a) for a in node.args), default=0)


def size(node: Node) -> int:
    return 1 + sum(size(a) for a in node.args)


def role_entries(node: Node) -> list[tuple[str, int, Node]]:
    """(role, ord, filler) triples of an APPLY node."""
    out = []
    for spec, filler in zip(node.get("roles"), node.args):
        role, _, o = str(spec).partition("#")
        out.append((role, int(o or 0), filler))
    return out


# ---------------------------------------------------------------------------
# Builders (authoring DSL). Shorthand: a SIT passed where a PROP is expected is
# wrapped in HOLDS (normalization N1); canonical form is always explicit.
# ---------------------------------------------------------------------------
def _p(x: Node) -> Node:
    return holds(x) if sort_of(x) == SIT else x


def _s(v: Any) -> str:
    return str(v)


def ref(r: Any) -> Node:
    return Node("REF", (), {"ref": _s(r)})


def kind(concept: Any) -> Node:
    return Node("KIND", (), {"concept": _s(concept)})


def var(name: str, binder_id: str | None = None) -> Node:
    params = {"name": name}
    if binder_id is not None:
        params["binderId"] = binder_id
    return Node("VAR", (), params)


def _metadata_json(value: Any) -> str:
    """Canonical JSON envelope for structured source metadata."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def metadata_value(node: Node, key: str, default: Any = None) -> Any:
    value = node.get(key, default)
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def predicate_app(predicate: str, roles: Sequence[str], arguments: Sequence[Node], **metadata: Any) -> Node:
    if not isinstance(predicate, str) or not predicate.strip():
        raise InvariantViolation("PREDICATE_APP predicate must be a non-empty string", "SG-CON-006")
    params: dict[str, Any] = {"predicate": predicate, "roles": tuple(roles)}
    for key, value in metadata.items():
        if key not in _SIGS["PREDICATE_APP"].allowed:
            raise InvariantViolation(f"PREDICATE_APP: unsupported metadata field {key!r}", "SG-CON-006")
        params[key] = _metadata_json(value)
    return Node("PREDICATE_APP", tuple(arguments), params)


def connective(connective_id: str, operands: Sequence[Node], operand_roles: Sequence[str], **metadata: Any) -> Node:
    if not isinstance(connective_id, str) or not connective_id.strip():
        raise InvariantViolation("CONNECTIVE identity must be a non-empty string", "SG-CON-006")
    params: dict[str, Any] = {"connective": connective_id, "operandRoles": tuple(operand_roles)}
    for key, value in metadata.items():
        if key not in _SIGS["CONNECTIVE"].allowed:
            raise InvariantViolation(f"CONNECTIVE: unsupported metadata field {key!r}", "SG-CON-006")
        params[key] = _metadata_json(value)
    return Node("CONNECTIVE", tuple(operands), params)


def quantifier(operator_type: str, operator: str, binder_id: str, variable: str, body: Node,
               scope_kind: str, *, restrictor: Any = None, variable_binding: Any = None,
               count: int | None = None, **metadata: Any) -> Node:
    params: dict[str, Any] = {"operatorType": operator_type, "operator": operator,
        "binderId": binder_id, "variable": variable, "scopeKind": scope_kind}
    if restrictor is not None:
        params["restrictor"] = _metadata_json(restrictor)
    if variable_binding is not None:
        params["variableBinding"] = _metadata_json(variable_binding)
    if count is not None:
        params["count"] = count
    for key, value in metadata.items():
        if key not in ("surfaceText", "evidenceRefs", "attribution"):
            raise InvariantViolation(f"QUANTIFIER: unsupported metadata field {key!r}", "SG-CON-006")
        params[key] = _metadata_json(value)
    return Node("QUANTIFIER", (body,), params)


def reify(x: Node) -> Node:
    return Node("REIFY", (x,))


def lit(value: Any, vtype: str = "Text", unit: str | None = None) -> Node:
    p: dict[str, Any] = {"value": value, "vtype": vtype}
    if unit is not None:
        p["unit"] = unit
    return Node("LIT", (), p)


def value(concept: Any) -> Node:
    return Node("VALUE", (), {"concept": _s(concept)})


def hole(state: str = "UNSPECIFIED") -> Node:
    return Node("HOLE", (), {"state": getattr(state, "value", state)})


def time_lit(form: str, val: str) -> Node:
    return Node("TIME_LIT", (), {"form": form, "value": val})


def time_rel(expr: str, resolved_start: str | None = None, resolved_end: str | None = None) -> Node:
    p: dict[str, Any] = {"expr": expr}
    if resolved_start is not None:
        p["resolved_start"] = resolved_start
        p["resolved_end"] = resolved_end
    return Node("TIME_REL", (), p)


def speech_time() -> Node:
    return Node("SPEECH_TIME")


def unresolved_time(text: str, span: tuple[int, int] | None = None) -> Node:
    p: dict[str, Any] = {"text": text}
    if span is not None:
        p["span"] = tuple(span)
    return Node("UNRESOLVED_TIME", (), p)


def extent(sit: Node) -> Node:
    return Node("EXTENT", (sit,))


def apply(frame: str, version: int, bindings: Mapping[str, Node | Sequence[Node]]) -> Node:
    """``APPLY(frame@version, {role: filler})``. Roles are stored sorted by (role, ord) so equal
    bindings in any dict order give structurally equal nodes."""
    items: list[tuple[str, int, Node]] = []
    for role, fill in bindings.items():
        fills = [fill] if isinstance(fill, Node) else list(fill)
        for i, f in enumerate(fills):
            items.append((role, i, f))
    items.sort(key=lambda t: (t[0], t[1]))
    return Node("APPLY", tuple(f for _, _, f in items),
                {"frame": frame, "version": version, "roles": tuple(f"{r}#{o}" for r, o, _ in items)})


def aspect(a: str, sit: Node) -> Node:
    return Node("ASPECT", (sit,), {"aspect": a})


def compose(kind_: str, *sits: Node) -> Node:
    return Node("COMPOSE", tuple(sits), {"kind": kind_})


def holds(sit: Node) -> Node:
    return Node("HOLDS", (sit,))


def relate(relation: str, a: Node, b: Node) -> Node:
    return Node("RELATE", (a, b), {"relation": relation})


def prop(bearer: Node, property_: Any, val: Node, degree: Node | None = None) -> Node:
    args = (bearer, val) + ((degree,) if degree is not None else ())
    return Node("PROPERTY", args, {"property": _s(property_)})


def not_(p: Node) -> Node:
    return Node("NOT", (_p(p),))


def and_(*ps: Node) -> Node:
    return Node("AND", tuple(_p(p) for p in ps))


def or_(*ps: Node) -> Node:
    return Node("OR", tuple(_p(p) for p in ps))


def implies(a: Node, b: Node) -> Node:
    return Node("IMPLIES", (_p(a), _p(b)))


def cond(a: Node, b: Node) -> Node:
    return Node("COND", (_p(a), _p(b)))


def counterfactual(a: Node, b: Node) -> Node:
    return Node("COUNTERFACTUAL", (_p(a), _p(b)))


def q(quant: str, var_name: str, restrictor: Node, scope: Node, domain: Node | None = None, n: int | None = None) -> Node:
    p: dict[str, Any] = {"quant": quant, "var": var_name}
    if n is not None:
        p["n"] = n
    args = (_p(restrictor), _p(scope)) + ((domain,) if domain is not None else ())
    return Node("Q", args, p)


def modal(force: str, flavor: str, p: Node) -> Node:
    return Node("MODAL", (_p(p),), {"force": force, "flavor": flavor})


def tense(t: str, time: Node, p: Node) -> Node:
    return Node("TENSE", (time, _p(p)), {"tense": t})


def temporal(allen: str, t1: Node, t2: Node) -> Node:
    return Node("TEMPORAL", (t1, t2), {"allen": allen})


def attribute(holder: Node, mode: str, p: Node) -> Node:
    return Node("ATTRIBUTE", (holder, _p(p)), {"mode": mode})


def same_as(a: Node, b: Node, scope: str = "DISCOURSE") -> Node:
    return Node("SAME_AS", (a, b), {"scope": scope})


def different_from(a: Node, b: Node, scope: str | None = None) -> Node:
    return Node("DIFFERENT_FROM", (a, b), {"scope": scope} if scope else {})


def direct(addressee: Node, sit: Node) -> Node:
    return Node("DIRECT", (addressee, sit))


def fig(mapping: str, literal: Node, intended: Node) -> Node:
    return Node("FIG", (literal, intended), {"mapping": mapping})


def alt(group: str, alternatives: Sequence[Node], ranks: Sequence[int] | None = None) -> Node:
    """Mutually exclusive readings. Support is an ORDINAL rank (1 = best), never a probability."""
    r = tuple(ranks) if ranks is not None else tuple(range(1, len(alternatives) + 1))
    return Node("ALT", tuple(alternatives), {"group": group, "ranks": r})


def assert_(p: Node, **meta: Any) -> Node:
    return Node("ASSERT", (_p(p),), meta)


def error(code: str, detail: str | None = None, span: tuple[int, int] | None = None) -> Node:
    p: dict[str, Any] = {"code": code}
    if detail is not None:
        p["detail"] = detail
    if span is not None:
        p["span"] = tuple(span)
    return Node("ERROR", (), p)


# ---------------------------------------------------------------------------
# Readable form
# ---------------------------------------------------------------------------
def pretty(node: Node) -> str:
    op, a, p = node.op, node.args, node.params_dict()
    if op == "REF":
        return str(p["ref"])
    if op == "KIND":
        return f"KIND({p['concept']})"
    if op == "VAR":
        return f"?{p['name']}"
    if op == "LIT":
        u = f" {p['unit']}" if "unit" in p else ""
        return f"{p['value']!r}{u}"
    if op == "VALUE":
        return f"VALUE({p['concept']})"
    if op == "HOLE":
        return p["state"]
    if op == "TIME_LIT":
        return f"{p['form']}({p['value']})"
    if op == "TIME_REL":
        r = f"={p['resolved_start']}..{p['resolved_end']}" if "resolved_start" in p else ""
        return f"{p['expr']}{r}"
    if op == "SPEECH_TIME":
        return "SPEECH_TIME"
    if op == "UNRESOLVED_TIME":
        return f"UNRESOLVED({p['text']!r})"
    if op == "APPLY":
        body = ", ".join(f"{r}: {pretty(f)}" for r, f in zip(p["roles"], a))
        return f"APPLY({p['frame']}@{p['version']}, {{{body}}})"
    if op == "PREDICATE_APP":
        body = ", ".join(f"{r}: {pretty(f)}" for r, f in zip(p["roles"], a))
        return f"PREDICATE_APP({p['predicate']}, {{{body}}})"
    if op == "CONNECTIVE":
        body = ", ".join(f"{r}: {pretty(f)}" for r, f in zip(p["operandRoles"], a))
        return f"CONNECTIVE[{p['connective']}]({body})"
    if op == "QUANTIFIER":
        return f"QUANTIFIER[{p['operator']} {p['variable']}@{p['binderId']}]({pretty(a[0])})"
    inner = ", ".join(pretty(x) for x in a)
    extras = [f"{k}={v}" for k, v in node.params if k not in ("ranks",)]
    if op == "ALT":
        inner = ", ".join(f"#{r}:{pretty(x)}" for r, x in zip(p["ranks"], a))
    tag = f"[{' '.join(extras)}]" if extras else ""
    return f"{op}{tag}({inner})"
