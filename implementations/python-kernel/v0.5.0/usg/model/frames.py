"""Frame model (spec Part 4): definitions, resolution, inheritance rules and
structural validation of role bindings.

Implemented rules
  SG-FRM-001/E-45  closed role list per frame (tier-1 names cannot bypass tier-2 roles)
  SG-FRM-002       SPECIALIZES preserves parent commitments (also pins)
  SG-FRM-003       narrowing only: no role removal, no kind change, no widened
                   class, REQUIRED never weakened, cardinality never widened
  SG-FRM-004       multi-parent conjunction, no linearization; provably empty
                   or unrelated class conjunctions are rejected
  SG-FRM-006       role order is append-only (inherited roles first)
  SG-FRM-008       every frame ships valid / incomplete / invalid / contrastive tests
  SG-FRM-010       layer discipline (child layer >= parent layer; authority by layer)
  E-41             two link kinds: SPECIALIZES vs STRUCTURAL_INSTANCE_OF
  E-42             parameters pinned by specializations; instances never set them
  E-43             perspective variants declared by the frame
  VC-S05..S08, VC-T06  binding validation (frame exists/instantiable, roles defined,
                   REQUIRED roles bound or in a hole state, cardinality, disjoint roles)
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from ..core.kinds import SemKind
from ..core.records import RoleBinding
from ..core.roles import TIER1_ROLES, Requiredness, RoleSpec
from ..core.values import ValueState
from ..errors import InvariantViolation
from ..ontology import Ontology
from ..util import canonical_json, sha256_hex
from .relations import RelationDef


class LinkKind(str, Enum):
    SPECIALIZES = "SPECIALIZES"
    STRUCTURAL_INSTANCE_OF = "STRUCTURAL_INSTANCE_OF"


class SituationKind(str, Enum):
    EVENT = "EVENT"
    STATE = "STATE"
    PROCESS = "PROCESS"
    SYSTEM = "SYSTEM"


class Authority(str, Enum):
    GRAMMAR = "GRAMMAR"
    DOMAIN = "DOMAIN"


class Strength(str, Enum):
    ESSENTIAL = "ESSENTIAL"
    TYPICAL = "TYPICAL"


class ConsequenceKind(str, Enum):
    PRECONDITION = "PRECONDITION"
    EFFECT = "EFFECT"
    TYPICAL_OUTCOME = "TYPICAL_OUTCOME"


class CompKind(str, Enum):
    SEQUENCE = "SEQUENCE"
    PARALLEL = "PARALLEL"
    CONDITION = "CONDITION"
    LOOP = "LOOP"
    DEPENDENCY = "DEPENDENCY"
    ALTERNATIVE = "ALTERNATIVE"
    SUBPROCESS = "SUBPROCESS"


class ControlKind(str, Enum):
    SUBJECT_CONTROL = "SUBJECT_CONTROL"
    OBJECT_CONTROL = "OBJECT_CONTROL"
    NONE = "NONE"


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RoleDecl:
    name: str
    tier: int
    parent: str | None = None
    kind: SemKind = SemKind.ENTITY
    cls: str | None = None  # class constraint by concept name (soft, extensible)
    required: bool = False
    card_max: int = 1
    card_min: int = 0

    def __post_init__(self):
        self.spec()  # reuse RoleSpec validation (I-04, I-05)

    def spec(self) -> RoleSpec:
        return RoleSpec(self.name, self.tier, self.parent, self.kind, None,
                        Requiredness.REQUIRED if self.required else Requiredness.OPTIONAL,
                        max(self.card_min, 1 if self.required else 0), self.card_max)


@dataclass(frozen=True)
class ParamDecl:
    name: str
    allowed: tuple[str, ...] | None = None  # enumeration, or None
    concept_kind: SemKind | None = None  # or: pin must name a concept of this kind


@dataclass(frozen=True)
class ParentLink:
    parent: str
    kind: LinkKind = LinkKind.SPECIALIZES
    role_map: tuple[tuple[str, str], ...] = ()  # (child_role, parent_role)


@dataclass(frozen=True)
class StatePattern:
    """predicate(args): args are role names, 'value:CONCEPT' or 'param:NAME'."""

    predicate: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class Consequence:
    kind: ConsequenceKind
    strength: Strength
    pattern: StatePattern


@dataclass(frozen=True)
class Perspective:
    name: str
    focus_role: str
    hints: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentSpec:
    frame: str
    role_map: tuple[tuple[str, str], ...]  # (composite_role, component_role)
    ordering: CompKind = CompKind.DEPENDENCY


@dataclass(frozen=True)
class Presupposition:
    role: str  # the role whose content is presupposed inside the same context (SG-EVD-004)


@dataclass(frozen=True)
class ControlHint:
    kind: ControlKind
    controller_role: str
    content_role: str
    controlled_tier1: tuple[str, ...] = ("AGENT", "THEME", "EXPERIENCER")


@dataclass(frozen=True)
class FrameTests:
    valid: tuple[str, ...] = ()
    incomplete: tuple[str, ...] = ()
    invalid: tuple[str, ...] = ()
    contrastive: tuple[tuple[str, str], ...] = ()

    def complete(self) -> bool:
        return bool(self.valid and self.incomplete and self.invalid and self.contrastive)


@dataclass(frozen=True)
class FrameDef:
    name: str
    layer: int
    authority: Authority
    situation_kind: SituationKind = SituationKind.EVENT
    abstract: bool = False
    kernel: bool = False
    parents: tuple[ParentLink, ...] = ()
    roles: tuple[RoleDecl, ...] = ()
    params: tuple[ParamDecl, ...] = ()
    pins: tuple[tuple[str, str], ...] = ()
    disjoint_roles: tuple[tuple[str, str], ...] = ()
    initial: tuple[StatePattern, ...] = ()
    final: tuple[StatePattern, ...] = ()
    process: str | None = None
    applies_when: str = "COMPLETED_VIEW"
    consequences: tuple[Consequence, ...] = ()
    presuppositions: tuple[Presupposition, ...] = ()
    components: tuple[ComponentSpec, ...] = ()
    perspectives: tuple[Perspective, ...] = ()
    control: ControlHint | None = None
    role_functions: tuple[tuple[str, str], ...] = ()
    tests: FrameTests = field(default_factory=FrameTests)
    doc: str = ""
    version: int = 1

    def to_json(self) -> dict[str, Any]:
        return _jsonable(self)

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.to_json()))

    @staticmethod
    def from_json(d: Mapping[str, Any]) -> "FrameDef":
        def sp(x):
            return StatePattern(x["predicate"], tuple(x["args"]))

        ctl = d.get("control")
        return FrameDef(
            name=d["name"], layer=d["layer"], authority=Authority(d["authority"]),
            situation_kind=SituationKind(d["situation_kind"]), abstract=d["abstract"], kernel=d["kernel"],
            parents=tuple(ParentLink(p["parent"], LinkKind(p["kind"]), tuple(tuple(x) for x in p["role_map"]))
                          for p in d["parents"]),
            roles=tuple(RoleDecl(r["name"], r["tier"], r["parent"], SemKind(r["kind"]), r["cls"], r["required"],
                                 r["card_max"], r.get("card_min", 0)) for r in d["roles"]),
            params=tuple(ParamDecl(p["name"], tuple(p["allowed"]) if p["allowed"] is not None else None,
                                   SemKind(p["concept_kind"]) if p["concept_kind"] else None) for p in d["params"]),
            pins=tuple(tuple(x) for x in d["pins"]),
            disjoint_roles=tuple(tuple(x) for x in d["disjoint_roles"]),
            initial=tuple(sp(x) for x in d["initial"]), final=tuple(sp(x) for x in d["final"]),
            process=d["process"], applies_when=d["applies_when"],
            consequences=tuple(Consequence(ConsequenceKind(c["kind"]), Strength(c["strength"]), sp(c["pattern"]))
                               for c in d["consequences"]),
            presuppositions=tuple(Presupposition(p["role"]) for p in d["presuppositions"]),
            components=tuple(ComponentSpec(c["frame"], tuple(tuple(x) for x in c["role_map"]), CompKind(c["ordering"]))
                             for c in d["components"]),
            perspectives=tuple(Perspective(p["name"], p["focus_role"], tuple(p["hints"])) for p in d["perspectives"]),
            control=ControlHint(ControlKind(ctl["kind"]), ctl["controller_role"], ctl["content_role"],
                                tuple(ctl["controlled_tier1"])) if ctl else None,
            role_functions=tuple(tuple(x) for x in d["role_functions"]),
            tests=FrameTests(tuple(d["tests"]["valid"]), tuple(d["tests"]["incomplete"]), tuple(d["tests"]["invalid"]),
                             tuple(tuple(x) for x in d["tests"]["contrastive"])),
            doc=d["doc"], version=d["version"],
        )


def _jsonable(o: Any) -> Any:
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        return {f.name: _jsonable(getattr(o, f.name)) for f in dataclasses.fields(o)}
    if isinstance(o, Enum):
        return o.value
    if isinstance(o, (tuple, list)):
        return [_jsonable(x) for x in o]
    return o


# ---------------------------------------------------------------------------
# Resolution results
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ResolvedRole:
    name: str
    spec: RoleSpec
    cls: str | None
    origin: str  # frame where the role was first declared
    index: int

    @property
    def required(self) -> bool:
        return self.spec.requiredness is Requiredness.REQUIRED


@dataclass(frozen=True)
class ResolvedFrame:
    frame: FrameDef
    roles: tuple[ResolvedRole, ...]
    index: Mapping[str, int]
    params: Mapping[str, ParamDecl]
    pins: Mapping[str, str]
    specializes: tuple[str, ...]  # direct SPECIALIZES parents
    structural: tuple[str, ...]  # direct STRUCTURAL_INSTANCE_OF parents

    @property
    def name(self) -> str:
        return self.frame.name

    def role(self, name: str) -> ResolvedRole | None:
        i = self.index.get(name)
        return self.roles[i] if i is not None else None

    def role_names(self) -> tuple[str, ...]:
        return tuple(r.name for r in self.roles)


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    role: str | None = None
    frame: str | None = None

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# ---------------------------------------------------------------------------
# The library
# ---------------------------------------------------------------------------
class FrameLibrary:
    def __init__(self, ontology: Ontology, relations: Mapping[str, RelationDef] | None = None,
                 require_tests: bool = True):
        self.ontology = ontology
        self.relations = dict(relations or {})
        self.require_tests = require_tests
        self._frames: dict[str, FrameDef] = {}
        self._resolved: dict[str, ResolvedFrame] = {}
        self.issues: list[Issue] = []
        self._finalized = False

    # -- registration ---------------------------------------------------------
    def add(self, f: FrameDef) -> None:
        if f.name in self._frames:
            raise InvariantViolation(f"duplicate frame {f.name!r}", "I-01")
        self._frames[f.name] = f
        self._finalized = False

    def add_all(self, frames: Iterable[FrameDef]) -> "FrameLibrary":
        for f in frames:
            self.add(f)
        return self

    def names(self) -> list[str]:
        return list(self._frames)

    def get(self, name: str) -> FrameDef:
        try:
            return self._frames[name]
        except KeyError as e:
            raise KeyError(f"unknown frame {name!r}") from e

    def has(self, name: str) -> bool:
        return name in self._frames

    def resolved(self, name: str) -> ResolvedFrame:
        if not self._finalized:
            raise InvariantViolation("frame library not finalized", "SG-FRM-008")
        return self._resolved[name]

    def kernel_frames(self) -> list[str]:
        return [n for n, f in self._frames.items() if f.kernel]

    # -- finalize -------------------------------------------------------------
    def build(self) -> list[Issue]:
        self.issues = []
        self._resolved = {}
        for name in self._frames:
            self._resolve(name, [])
        for name, rf in self._resolved.items():
            self._validate_frame(rf)
        self._check_component_cycles()
        self._finalized = not self.issues
        return list(self.issues)

    def finalize(self) -> "FrameLibrary":
        issues = self.build()
        if issues:
            first = issues[0]
            more = f" (+{len(issues) - 1} more)" if len(issues) > 1 else ""
            raise InvariantViolation(f"{first.frame}: {first.message}{more}", first.code)
        return self

    def _issue(self, frame: str, code: str, msg: str, role: str | None = None) -> None:
        self.issues.append(Issue(code, msg, role, frame))

    # -- resolution --------------------------------------------------------------
    def _resolve(self, name: str, stack: list[str]) -> ResolvedFrame | None:
        if name in self._resolved:
            return self._resolved[name]
        f = self._frames[name]
        if name in stack:
            self._issue(name, "VC-G01", f"frame inheritance cycle: {' -> '.join(stack + [name])}")
            return None
        for link in f.parents:
            if link.parent not in self._frames:
                self._issue(name, "I-02", f"unknown parent frame {link.parent!r}")
            else:
                self._resolve(link.parent, stack + [name])

        roles: list[ResolvedRole] = []
        idx: dict[str, int] = {}
        params: dict[str, ParamDecl] = {}
        pins: dict[str, str] = {}
        specs: list[str] = []
        structural: list[str] = []

        def put(r: ResolvedRole) -> None:
            idx[r.name] = len(roles)
            roles.append(dataclasses.replace(r, index=len(roles)))

        for link in f.parents:
            p = self._resolved.get(link.parent)
            if p is None:
                continue
            pf = p.frame
            if pf.layer > f.layer:  # SG-FRM-010
                self._issue(name, "SG-FRM-010", f"layer {f.layer} frame cannot build on layer {pf.layer} frame {pf.name}")
            if link.kind is LinkKind.STRUCTURAL_INSTANCE_OF:
                structural.append(link.parent)
                continue
            specs.append(link.parent)
            rename = {pr: cr for cr, pr in link.role_map}
            for pr in p.roles:
                cname = rename.get(pr.name, pr.name)
                inherited = ResolvedRole(cname, _renamed(pr.spec, cname), pr.cls, pr.origin, 0)
                if cname in idx:
                    merged = self._conjoin(name, roles[idx[cname]], inherited)
                    if merged is not None:
                        roles[idx[cname]] = dataclasses.replace(merged, index=idx[cname])
                else:
                    put(inherited)
            for pn, pd in p.params.items():
                if pn in params and params[pn] != pd:
                    self._issue(name, "SG-FRM-004", f"conflicting definitions of parameter {pn} from parents")
                params.setdefault(pn, pd)
            for k, v in p.pins.items():
                if k in pins and pins[k] != v:
                    self._issue(name, "SG-FRM-004", f"parents pin {k} to different values ({pins[k]} vs {v})")
                pins.setdefault(k, v)

        for rd in f.roles:
            if rd.cls is not None and not self.ontology.has(rd.cls):
                self._issue(name, "I-02", f"role {rd.name}: unknown class {rd.cls!r}", rd.name)
            if rd.name in idx:
                old = roles[idx[rd.name]]
                self._check_narrowing(name, old, rd)
                new_cls = rd.cls if rd.cls is not None else old.cls
                roles[idx[rd.name]] = ResolvedRole(rd.name, rd.spec(), new_cls, old.origin, idx[rd.name])
            else:
                put(ResolvedRole(rd.name, rd.spec(), rd.cls, name, 0))

        for pd in f.params:
            if pd.name in params:
                self._issue(name, "SG-FRM-002", f"parameter {pd.name} is already declared by a parent")
            params[pd.name] = pd
        for k, v in f.pins:
            pd = params.get(k)
            if pd is None:
                self._issue(name, "SG-FRM-002", f"pin of undeclared parameter {k}")
                continue
            if k in pins and pins[k] != v:
                self._issue(name, "SG-FRM-002", f"cannot re-pin inherited parameter {k} ({pins[k]} -> {v})")
            if pd.allowed is not None and v not in pd.allowed:
                self._issue(name, "SG-FRM-002", f"pin {k}={v} not in allowed values {pd.allowed}")
            if pd.concept_kind is not None:
                if not self.ontology.has(v) or self.ontology.kind_of(v) is not pd.concept_kind:
                    self._issue(name, "SG-FRM-002", f"pin {k}={v} must name a {pd.concept_kind.value} concept")
            pins[k] = v

        rf = ResolvedFrame(f, tuple(roles), dict(idx), params, pins, tuple(specs), tuple(structural))
        # structural correspondence (no role inheritance)
        for link in f.parents:
            if link.kind is LinkKind.STRUCTURAL_INSTANCE_OF and link.parent in self._resolved:
                pr = self._resolved[link.parent]
                for cr, prn in link.role_map:
                    c, p_ = rf.role(cr), pr.role(prn)
                    if c is None or p_ is None:
                        self._issue(name, "SG-FRM-003", f"structural role_map {cr}->{prn} names a missing role")
                    elif c.spec.expected_kind is not p_.spec.expected_kind:
                        self._issue(name, "SG-FRM-003", f"structural role_map {cr}->{prn}: kinds differ")
        self._resolved[name] = rf
        return rf

    def _check_narrowing(self, frame: str, old: ResolvedRole, rd: RoleDecl) -> None:
        new = rd.spec()
        o = old.spec
        if new.expected_kind is not o.expected_kind:
            self._issue(frame, "SG-FRM-003", f"role {rd.name}: kind change {o.expected_kind.value}->{new.expected_kind.value}", rd.name)
        if (o.tier, o.parent_role) != (new.tier, new.parent_role):
            self._issue(frame, "SG-FRM-003", f"role {rd.name}: tier/parent changed", rd.name)
        if o.requiredness is Requiredness.REQUIRED and new.requiredness is Requiredness.OPTIONAL:
            self._issue(frame, "SG-FRM-003", f"role {rd.name}: REQUIRED cannot become OPTIONAL", rd.name)
        if new.card_max > o.card_max or new.card_min < o.card_min:
            self._issue(frame, "SG-FRM-003", f"role {rd.name}: cardinality widened", rd.name)
        if rd.cls is not None and old.cls is not None and self.ontology.has(rd.cls) and self.ontology.has(old.cls):
            if not self.ontology.is_subclass(rd.cls, old.cls):
                self._issue(frame, "SG-FRM-003", f"role {rd.name}: class {rd.cls} widens inherited {old.cls}", rd.name)

    def _conjoin(self, frame: str, a: ResolvedRole, b: ResolvedRole) -> ResolvedRole | None:
        """Multi-parent merge: conjunction of constraints; no linearization (SG-FRM-004)."""
        sa, sb = a.spec, b.spec
        if sa.expected_kind is not sb.expected_kind or (sa.tier, sa.parent_role) != (sb.tier, sb.parent_role):
            self._issue(frame, "SG-FRM-004", f"role {a.name}: parents disagree on kind/tier", a.name)
            return None
        cls = a.cls
        if a.cls and b.cls and a.cls != b.cls and self.ontology.has(a.cls) and self.ontology.has(b.cls):
            if self.ontology.is_subclass(a.cls, b.cls):
                cls = a.cls
            elif self.ontology.is_subclass(b.cls, a.cls):
                cls = b.cls
            elif self.ontology.disjoint(a.cls, b.cls):
                self._issue(frame, "SG-FRM-004", f"role {a.name}: parent classes {a.cls} and {b.cls} are disjoint (empty conjunction)", a.name)
                return None
            else:
                self._issue(frame, "SG-FRM-004",
                            f"role {a.name}: unrelated parent classes {a.cls}/{b.cls}; the child must narrow explicitly", a.name)
                return None
        elif b.cls and not a.cls:
            cls = b.cls
        req = sa.requiredness is Requiredness.REQUIRED or sb.requiredness is Requiredness.REQUIRED
        spec = RoleSpec(sa.name, sa.tier, sa.parent_role, sa.expected_kind, None,
                        Requiredness.REQUIRED if req else Requiredness.OPTIONAL,
                        max(sa.card_min, sb.card_min), min(sa.card_max, sb.card_max))
        return ResolvedRole(a.name, spec, cls, a.origin, a.index)

    # -- per-frame validation -------------------------------------------------------
    def _validate_frame(self, rf: ResolvedFrame) -> None:
        f, n = rf.frame, rf.frame.name
        roles = set(rf.role_names())
        if f.layer not in (1, 2, 3):
            self._issue(n, "SG-FRM-010", f"layer must be 1..3 (layer 4 never defines a frame), got {f.layer}")
        if (f.layer <= 2) != (f.authority is Authority.GRAMMAR):
            self._issue(n, "SG-FRM-010", f"layer {f.layer} requires authority {'GRAMMAR' if f.layer <= 2 else 'DOMAIN'}")
        names = [r.name for r in rf.roles]
        if len(names) != len(set(names)):
            self._issue(n, "I-05", "duplicate role names after resolution")

        def need(role: str, what: str) -> None:
            if role not in roles:
                self._issue(n, "SG-FRM-001", f"{what} references unknown role {role!r}", role)

        for p in f.perspectives:
            need(p.focus_role, f"perspective {p.name}")
        for a, b in f.disjoint_roles:
            need(a, "disjoint_roles")
            need(b, "disjoint_roles")
        for p in f.presuppositions:
            need(p.role, "presupposition")
        if f.control:
            need(f.control.controller_role, "control hint")
            need(f.control.content_role, "control hint")
        for role, fn in f.role_functions:
            need(role, "role_functions")
            if not self.ontology.has(fn):
                self._issue(n, "I-02", f"role_functions: unknown function {fn!r}")
        for pat in (*f.initial, *f.final, *(c.pattern for c in f.consequences)):
            for a in pat.args:
                if a.startswith("value:"):
                    if not self.ontology.has(a[6:]):
                        self._issue(n, "I-02", f"pattern {pat.predicate}: unknown concept {a[6:]!r}")
                elif a.startswith("param:"):
                    if a[6:] not in rf.params:
                        self._issue(n, "SG-FRM-001", f"pattern {pat.predicate}: unknown parameter {a[6:]!r}")
                else:
                    need(a, f"pattern {pat.predicate}")
        for comp in f.components:
            if comp.frame not in self._frames:
                self._issue(n, "I-02", f"component frame {comp.frame!r} unknown")
                continue
            cr = self._resolved.get(comp.frame)
            for composite_role, component_role in comp.role_map:
                need(composite_role, f"component {comp.frame}")
                if cr is not None and cr.role(component_role) is None:
                    self._issue(n, "SG-FRM-001", f"component {comp.frame} has no role {component_role!r}")
        if self.require_tests and not f.tests.complete():
            missing = [k for k in ("valid", "incomplete", "invalid", "contrastive") if not getattr(f.tests, k)]
            self._issue(n, "SG-FRM-008", f"missing test groups: {missing}")

    def _check_component_cycles(self) -> None:
        graph = {n: [c.frame for c in f.components if c.frame in self._frames] for n, f in self._frames.items()}
        state: dict[str, int] = {}

        def dfs(n: str, path: list[str]) -> None:
            state[n] = 1
            for m in graph[n]:
                if state.get(m) == 1:
                    self._issue(n, "VC-G01", f"component cycle {' -> '.join(path + [n, m])}")
                elif m not in state:
                    dfs(m, path + [n])
            state[n] = 2

        for n in graph:
            if n not in state:
                dfs(n, [])

    def topo_order(self) -> list[str]:
        """Parents before children (needed to persist frames: children reference parent rows)."""
        order: list[str] = []
        seen: set[str] = set()

        def visit(n: str) -> None:
            if n in seen:
                return
            seen.add(n)
            for link in self._frames[n].parents:
                if link.parent in self._frames:
                    visit(link.parent)
            order.append(n)

        for n in self._frames:
            visit(n)
        return order

    # -- relationships ----------------------------------------------------------------
    def is_specialization_of(self, child: str, parent: str) -> bool:
        if child == parent:
            return True
        return parent in self._spec_ancestors(child)

    def _spec_ancestors(self, name: str) -> set[str]:
        out: set[str] = set()
        stack = list(self.resolved(name).specializes)
        while stack:
            n = stack.pop()
            if n not in out:
                out.add(n)
                stack.extend(self.resolved(n).specializes)
        return out

    def role_map_to(self, child: str, parent: str) -> dict[str, str] | None:
        """child role -> parent role along SPECIALIZES links; None if not a specialization."""
        if child == parent:
            return {r: r for r in self.resolved(child).role_names()}
        rf = self.resolved(child)
        for link in rf.frame.parents:
            if link.kind is not LinkKind.SPECIALIZES:
                continue
            up = {cr: pr for cr, pr in link.role_map}
            sub = self.role_map_to(link.parent, parent)
            if sub is None:
                continue
            out: dict[str, str] = {}
            for r in rf.role_names():
                pr = up.get(r, r)
                if pr in sub:
                    out[r] = sub[pr]
            return out
        return None

    # -- instance validation (VC-S05..S08, VC-T06) -----------------------------------------
    def validate_bindings(self, frame: str, bindings: Sequence[RoleBinding], *, allow_abstract: bool = False) -> list[Issue]:
        usage = []
        for b in bindings:
            key = str(b.filler.ref) if b.filler is not None and b.filler.ref is not None else None
            usage.append((b.role, b.ord, b.value_state is ValueState.SPECIFIED, key))
        return self.validate_role_usage(frame, usage, allow_abstract=allow_abstract)

    def validate_role_usage(self, frame: str, usage: Sequence[tuple[str, int, bool, str | None]], *,
                            allow_abstract: bool = False) -> list[Issue]:
        """Structural role checks on (role, ord, is_specified, filler_key) tuples. Shared by RoleBinding
        validation (storage) and APPLY-node validation (expression typechecker)."""
        out: list[Issue] = []
        if frame not in self._frames:
            return [Issue("VC-S05", f"unknown frame {frame!r}", None, frame)]
        rf = self.resolved(frame)
        if rf.frame.abstract and not allow_abstract:
            out.append(Issue("VC-S05", f"frame {frame} is abstract and cannot be instantiated", None, frame))
        by_role: dict[str, list[tuple[int, bool, str | None]]] = {}
        tier1_hint = {r.spec.tier1_parent: r.name for r in rf.roles if r.spec.tier == 2}
        for role, ord_, specified, key in usage:
            if role in rf.params:
                out.append(Issue("SG-FRM-002", f"{role} is a frame parameter; instances never set parameters", role, frame))
                continue
            if rf.role(role) is None:
                hint = ""
                if role in TIER1_ROLES and role in tier1_hint:
                    hint = f"; use {tier1_hint[role]} (a specialization of {role})"
                out.append(Issue("VC-S06", f"role {role} is not defined by frame {frame}{hint}", role, frame))
                continue
            by_role.setdefault(role, []).append((ord_, specified, key))
        for r in rf.roles:
            entries = by_role.get(r.name, [])
            if r.required and not entries:
                out.append(Issue("VC-S07", f"REQUIRED role {r.name} must be bound or in an explicit hole state", r.name, frame))
            n_specified = sum(1 for _, sp, _ in entries if sp)
            if entries and all(sp for _, sp, _ in entries) and n_specified < r.spec.card_min:
                out.append(Issue("VC-S08", f"role {r.name} needs at least {r.spec.card_min} fillers", r.name, frame))
            if n_specified > r.spec.card_max:
                out.append(Issue("VC-S08", f"role {r.name} allows at most {r.spec.card_max} fillers, got {n_specified}", r.name, frame))
        for a, b in rf.frame.disjoint_roles:
            fa = {k for _, _, k in by_role.get(a, []) if k is not None}
            fb = {k for _, _, k in by_role.get(b, []) if k is not None}
            if fa & fb:
                out.append(Issue("VC-T06", f"roles {a} and {b} are disjoint but share a referent", a, frame))
        return out

    def project_bindings(self, child: str, parent: str, bindings: Sequence[RoleBinding]) -> list[RoleBinding]:
        """SG-FRM-003 projection test: a valid child instance, projected through
        SPECIALIZES links, must be a valid parent instance."""
        mp = self.role_map_to(child, parent)
        if mp is None:
            raise InvariantViolation(f"{child} does not specialize {parent}", "SG-FRM-002")
        return [dataclasses.replace(b, role=mp[b.role]) for b in bindings if b.role in mp]

    def check_append_only(self, old: ResolvedFrame, new: ResolvedFrame) -> list[Issue]:
        """SG-FRM-006: a new frame version keeps every old role at its index."""
        out: list[Issue] = []
        for r in old.roles:
            nr = new.role(r.name)
            if nr is None:
                out.append(Issue("SG-FRM-006", f"role {r.name} removed", r.name, new.name))
            elif nr.index != r.index:
                out.append(Issue("SG-FRM-006", f"role {r.name} moved from index {r.index} to {nr.index}", r.name, new.name))
            elif (nr.spec.expected_kind, nr.spec.tier, nr.spec.parent_role) != (r.spec.expected_kind, r.spec.tier, r.spec.parent_role):
                out.append(Issue("SG-FRM-006", f"role {r.name} changed kind/tier (MAJOR change)", r.name, new.name))
        return out


def _renamed(spec: RoleSpec, name: str) -> RoleSpec:
    if spec.name == name:
        return spec
    if spec.tier == 1:  # renaming a universal role makes it a frame-specific role under that parent
        return RoleSpec(name, 2, spec.name, spec.expected_kind, spec.expected_class, spec.requiredness,
                        spec.card_min, spec.card_max, spec.coercion_allowed)
    return RoleSpec(name, spec.tier, spec.parent_role, spec.expected_kind, spec.expected_class, spec.requiredness,
                    spec.card_min, spec.card_max, spec.coercion_allowed)
