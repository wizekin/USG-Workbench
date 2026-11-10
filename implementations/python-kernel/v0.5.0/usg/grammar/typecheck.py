"""Static checks of an expression against the frame library and the ontology
(spec Part 3 §3.3-3.15; validation levels L1-L3 of Part 5).

Reported as ``Issue`` objects carrying the rule/check code, split into
ISSUES (the expression is invalid) and WARNINGS (accepted, but review priority
rises: UNDETERMINED class membership, a documented figurative reading).

  SG-CON-006  sort discipline (also enforced by the Node constructor)
  SG-CON-002  frame application well-formedness: frame exists at the pinned version,
              roles defined (closed list), REQUIRED roles bound or explicit holes,
              cardinality, disjoint roles, parameters never set by instances
  SG-CON-003  role fillers are referents / literals / kind-references / nested
              descriptions, never a bare concept id
  SG-CON-007  ALT: ordinal ranks, bounded group size
  SG-CON-008  ERROR nodes only in candidates
  SG-TYP-001  exact semantic-kind and three-valued class compatibility;
              INCOMPATIBLE needs a registered mapping
  SG-TYP-002  a figurative reading cites a registered mapping (FIG)
  SG-KNW-003  'WITHIN' identity only inside an attribution context
  VC-S12/S13  free variables / shadowing        VC-S15  no provisional id in a trusted expression
  VC-S16      nesting depth                     VC-G06  temporal consistency
  VC-T03      value in the property's domain, quantities carry units
  VC-T08      a VALUE used where a PROPERTY is expected
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Collection, Mapping, Sequence

from ..config import Config
from ..core.ids import Ref
from ..core.kinds import KIND_TO_SORT, SemKind, Sort, can_fill_role
from ..errors import InvariantViolation
from ..model.frames import FrameLibrary, Issue
from ..model.relations import RelationDef
from ..ontology import Compat
from .node import (ALLEN, ANY, ASPECTS, ATTRIBUTE_MODES, COMP_KINDS, COUNT_QUANTIFIERS, FLAVORS, FORCES,
                   IDENTITY_SCOPES, QUANTIFIERS, TENSES, TIME_FORMS, Node, depth, role_entries, sort_of)
from .scope import check_scope
from .timeval import check_temporal, parse_interval

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REFERENT_OK = ("REFERENT:", "W:")


@dataclass
class TypeReport:
    issues: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def codes(self) -> list[str]:
        return [i.code for i in self.issues]

    def raise_if_invalid(self) -> None:
        if self.issues:
            first = self.issues[0]
            more = f" (+{len(self.issues) - 1} more)" if len(self.issues) > 1 else ""
            raise InvariantViolation(f"{first.message}{more}", first.code)


@dataclass(frozen=True)
class _Ctx:
    in_fig_literal: bool = False
    in_attribute: bool = False
    is_root: bool = False
    variable_classes: tuple[tuple[str, str], ...] = ()


class Typechecker:
    def __init__(self, library: FrameLibrary, relations: Mapping[str, RelationDef] | None = None,
                 config: Config | None = None, classes_of: Callable[[str], Sequence[str]] | None = None,
                 mappings: Collection[str] | None = None):
        self.lib = library
        self.onto = library.ontology
        self.relations = dict(relations if relations is not None else library.relations)
        self.config = config or Config()
        self.classes_of = classes_of
        self.mappings = set(mappings) if mappings is not None else None  # registered figurative mappings

    # -- helpers -------------------------------------------------------------------
    def _concept_name(self, s: str) -> str | None:
        if self.onto.has(s):
            return s
        if s.startswith("CONCEPT:"):
            try:
                return self.onto.names.get(Ref.parse(s))
            except InvariantViolation:
                return None
        return None

    def _expression_kind(self, node: Node) -> SemKind | None:
        """Return the exact semantic kind when the expression determines it.

        Sorts intentionally remain coarse (for example EVENT/PROCESS/STATE all
        have SIT sort).  Role constraints are narrower than sorts, so this
        helper derives the kind from the expression constructor or frame.
        ``None`` means the current grammar does not determine one exact kind.
        """
        op = node.op
        if op == "KIND":
            name = self._concept_name(str(node.get("concept")))
            return self.onto.kind_of(name) if name is not None else None
        if op == "VALUE":
            return SemKind.VALUE
        if op == "LIT":
            return SemKind.QUANTITY if node.get("vtype") == "Quantity" else SemKind.VALUE
        if op in ("REF", "VAR", "REIFY"):
            # TERM denotes an entity, including a situation explicitly reified
            # as an entity. A plain SIT is never silently coerced to TERM.
            return SemKind.ENTITY
        if op in ("TIME_LIT", "TIME_REL", "SPEECH_TIME", "UNRESOLVED_TIME", "EXTENT"):
            return SemKind.TIME
        if op == "APPLY":
            frame = str(node.get("frame"))
            if not self.lib.has(frame):
                return None
            # EVENT / STATE / PROCESS are the three SIT semantic kinds.  The
            # frame catalogue also has SYSTEM templates; SYSTEM is deliberately
            # not guessed to be one of those kinds.
            try:
                return SemKind(self.lib.get(frame).situation_kind.value)
            except ValueError:
                return None
        if op == "ASPECT":
            return self._expression_kind(node.args[0])
        if op == "COMPOSE":
            # Part 3 §3.18 defines COMPOSE as a composite process built from
            # smaller situations.  Its result is therefore PROCESS, even
            # though its children may individually be EVENT or PROCESS.
            return SemKind.PROCESS
        if op == "ALT":
            # The caller checks each alternative independently; this branch is
            # useful when an ALT is nested under a transparent constructor.
            kinds = [self._expression_kind(child) for child in node.args]
            return kinds[0] if kinds and kinds[0] is not None and all(k == kinds[0] for k in kinds) else None

        # The following constructors have one semantic kind for their result.
        result = {
            "HOLDS": SemKind.PROPOSITION,
            "RELATE": SemKind.PROPOSITION,
            "PROPERTY": SemKind.PROPOSITION,
            "NOT": SemKind.PROPOSITION,
            "AND": SemKind.PROPOSITION,
            "OR": SemKind.PROPOSITION,
            "IMPLIES": SemKind.PROPOSITION,
            "COND": SemKind.PROPOSITION,
            "COUNTERFACTUAL": SemKind.PROPOSITION,
            "Q": SemKind.PROPOSITION,
            "MODAL": SemKind.PROPOSITION,
            "TENSE": SemKind.PROPOSITION,
            "TEMPORAL": SemKind.PROPOSITION,
            "ATTRIBUTE": SemKind.PROPOSITION,
            "SAME_AS": SemKind.PROPOSITION,
            "DIFFERENT_FROM": SemKind.PROPOSITION,
            "DIRECT": SemKind.PROPOSITION,
            "FIG": SemKind.PROPOSITION,
            "ASSERT": SemKind.PROPOSITION,
        }.get(op)
        if result is not None:
            return result

        # For operators whose broad sort has only one semantic kind, the sort
        # itself is sufficient. VAL and SIT remain intentionally ambiguous.
        sort = sort_of(node)
        if sort is Sort.TERM:
            return SemKind.ENTITY
        if sort is Sort.PROP:
            return SemKind.PROPOSITION
        if sort is Sort.TIME:
            return SemKind.TIME
        return None

    def _check_expected_kind(self, filler: Node, expected: SemKind, *, role: str,
                             frame: str, ctx: _Ctx, rep: TypeReport) -> bool:
        """Enforce the exact kind constraint, preserving ALT alternatives.

        False means the binding is already incompatible (or has been recorded
        as figurative) and later class checks should not add a second verdict.
        """
        if filler.op in ("HOLE", "ERROR"):
            return True
        if filler.op == "ALT":
            compatible = True
            for alternative in filler.args:
                compatible = self._check_expected_kind(
                    alternative, expected, role=role, frame=frame, ctx=ctx, rep=rep
                ) and compatible
            return compatible

        actual = self._expression_kind(filler)
        if actual is None:
            rep.warnings.append(Issue(
                "W-TYPE-UNDETERMINED",
                f"{frame}.{role}: semantic kind cannot be established for this expression; "
                f"the role requires {expected.value}", role, frame,
            ))
            return True
        if actual is expected:
            return True

        message = (f"{frame}.{role}: expected semantic kind {expected.value}, "
                   f"got {actual.value}; kinds are not interchangeable merely "
                   "because they share an expression sort")
        if ctx.in_fig_literal:
            rep.warnings.append(Issue("W-FIGURATIVE", message + "; documented by FIG", role, frame))
        else:
            rep.issues.append(Issue("SG-TYP-001", message, role, frame))
        return False

    # -- entry point ------------------------------------------------------------------
    def check(self, node: Node, *, candidate: bool = False, closed: bool | None = None) -> TypeReport:
        rep = TypeReport()
        is_assertion = node.op == "ASSERT"
        if depth(node) > int(self.config.get("max_nesting_depth")):
            rep.issues.append(Issue("VC-S16", f"nesting depth {depth(node)} exceeds the limit {self.config.get('max_nesting_depth')}"))
            return rep
        for code, msg in check_scope(node, closed=is_assertion if closed is None else closed):
            rep.issues.append(Issue(code, msg))
        for code, msg in check_temporal(node):
            rep.issues.append(Issue(code, msg))
        self._visit(node, _Ctx(is_root=True), candidate, rep)
        return rep

    # -- traversal ----------------------------------------------------------------------
    def _visit(self, n: Node, ctx: _Ctx, cand: bool, rep: TypeReport) -> None:
        op = n.op
        p = n.params_dict()
        err = lambda code, msg: rep.issues.append(Issue(code, msg))

        if op == "ERROR" and not cand:
            err("SG-CON-008", f"ERROR node {p.get('code')!r} is only legal in candidates, never in canonical expressions")
        elif op == "ASSERT" and not ctx.is_root:
            err("SG-CON-006", "ASSERT is a top-level wrapper and cannot be nested")
        elif op == "REF":
            ref = str(p["ref"])
            if not ref.startswith(_REFERENT_OK):
                err("SG-CON-003", f"REF {ref!r} is not a referent: a bare concept id can never fill a role (use KIND)")
        elif op == "KIND":
            c = str(p["concept"])
            if c.startswith("P:") and not cand:
                err("VC-S15", f"provisional concept {c} in a trusted expression")
            elif not c.startswith("P:"):
                name = self._concept_name(c)
                if name is None:
                    err("I-02", f"KIND references unknown concept {c!r}")
                elif not can_fill_role(self.onto.kind_of(name)):
                    err("SG-CON-003", f"KIND references {name}, a definition kind ({self.onto.kind_of(name).value}) that cannot fill a frame role")
        elif op == "VALUE":
            name = self._concept_name(str(p["concept"]))
            if name is None:
                err("I-02", f"VALUE references unknown concept {p['concept']!r}")
            elif self.onto.kind_of(name) is not SemKind.VALUE:
                err("VC-T08", f"{name} is a {self.onto.kind_of(name).value}, not a VALUE")
        elif op == "LIT":
            if p["vtype"] == "Quantity" and "unit" not in p:
                err("VC-T03", "a Quantity literal needs a unit (a bare number is not a measurement)")
        elif op == "Q":
            q = p["quant"]
            if q not in QUANTIFIERS:
                err("SG-CON-006", f"unknown quantifier {q!r}")
            if q in COUNT_QUANTIFIERS:
                if not isinstance(p.get("n"), int) or isinstance(p.get("n"), bool) or p["n"] < 0:
                    err("SG-CON-006", f"{q} needs a non-negative integer n")
            elif "n" in p:
                err("SG-CON-006", f"{q} takes no n")
            if not _IDENT.match(str(p["var"])):
                err("SG-CON-006", f"invalid variable name {p['var']!r}")
        elif op == "MODAL":
            if p["force"] not in FORCES or p["flavor"] not in FLAVORS:
                err("SG-CON-006", f"bad modality force/flavor {p['force']!r}/{p['flavor']!r}")
        elif op == "TENSE" and p["tense"] not in TENSES:
            err("SG-CON-006", f"unknown tense {p['tense']!r}")
        elif op == "ASPECT" and p["aspect"] not in ASPECTS:
            err("SG-CON-006", f"unknown aspect {p['aspect']!r}")
        elif op == "TEMPORAL" and p["allen"] not in ALLEN:
            err("SG-CON-006", f"{p['allen']!r} is not one of Allen's thirteen relations")
        elif op == "COMPOSE" and p["kind"] not in COMP_KINDS:
            err("SG-CON-006", f"unknown composition kind {p['kind']!r}")
        elif op == "ATTRIBUTE" and p["mode"] not in ATTRIBUTE_MODES:
            err("SG-CON-006", f"unknown attribution mode {p['mode']!r}")
        elif op in ("SAME_AS", "DIFFERENT_FROM"):
            sc = p.get("scope")
            if sc is not None and sc not in IDENTITY_SCOPES:
                err("SG-CON-006", f"unknown identity scope {sc!r}")
            if sc == "WITHIN" and not ctx.in_attribute:
                err("SG-KNW-003", "WITHIN identity is only valid inside an attribution context")
        elif op == "TIME_LIT":
            form = p["form"]
            if form not in TIME_FORMS:
                err("SG-CON-006", f"unknown time form {form!r}")
            elif form in ("INSTANT", "INTERVAL") and ("T" not in str(p["value"])) and parse_interval(form, str(p["value"])) is None:
                err("SG-CON-006", f"unparseable {form} value {p['value']!r}")
        elif op == "RELATE":
            rel = p["relation"]
            rd = self.relations.get(rel)
            if rd is None:
                err("I-02", f"unknown relation {rel!r}")
            else:
                for arg, expect, what in ((n.args[0], rd.domain_kind, "domain"), (n.args[1], rd.range_kind, "range")):
                    if expect is not None and arg.op == "KIND":
                        name = self._concept_name(str(arg.get("concept")))
                        if name is not None and self.onto.kind_of(name) is not expect:
                            err("VC-T05", f"{rel}: {what} must be a {expect.value}, got {self.onto.kind_of(name).value}")
        elif op == "PROPERTY":
            self._property(n, rep)
        elif op == "ALT":
            self._alt(n, rep)
        elif op == "FIG":
            m = str(p["mapping"])
            if not m:
                err("SG-TYP-002", "FIG must cite a mapping")
            elif self.mappings is not None and m not in self.mappings:
                err("SG-TYP-002", f"figurative mapping {m!r} is not registered")
        elif op == "APPLY":
            self._apply(n, ctx, rep)

        variable_classes = ctx.variable_classes
        if op == 'Q':
            def restrictions(x):
                if x.op == 'AND':
                    return [pair for arg in x.args for pair in restrictions(arg)]
                if x.op == 'RELATE' and x.get('relation') == 'INSTANCE_OF' and x.args[0].op == 'VAR' and x.args[0].get('name') == n.get('var') and x.args[1].op == 'KIND':
                    concept = self._concept_name(str(x.args[1].get('concept')))
                    return [(n.get('var'),concept)] if concept else []
                return []
            variable_classes += tuple(restrictions(n.args[0]))
        for i, a in enumerate(n.args):
            child = _Ctx(
                in_fig_literal=ctx.in_fig_literal or (op == "FIG" and i == 0),
                in_attribute=ctx.in_attribute or (op == "ATTRIBUTE" and i == 1),
                is_root=False,
                variable_classes=variable_classes if op != 'Q' or i < 2 else ctx.variable_classes,
            )
            self._visit(a, child, cand, rep)

    # -- PROPERTY ---------------------------------------------------------------------
    def _property(self, n: Node, rep: TypeReport) -> None:
        pname = self._concept_name(str(n.get("property")))
        if pname is None:
            rep.issues.append(Issue("I-02", f"unknown property concept {n.get('property')!r}"))
            return
        if self.onto.kind_of(pname) is not SemKind.PROPERTY:
            rep.issues.append(Issue("VC-T08", f"{pname} is a {self.onto.kind_of(pname).value}, not a PROPERTY "
                                    "(use PROPERTY(bearer, property, VALUE(...)), e.g. COLOR + RED)"))
            return
        val = n.args[1]
        if val.op == "VALUE":
            vname = self._concept_name(str(val.get("concept")))
            if vname is not None and self.onto.kind_of(vname) is SemKind.VALUE and not self.onto.value_in_domain(pname, vname):
                rep.issues.append(Issue("VC-T03", f"{vname} is not in the value domain of {pname}"))

    # -- ALT ----------------------------------------------------------------------------
    def _alt(self, n: Node, rep: TypeReport) -> None:
        cap = int(self.config.get("alt_max_per_group"))
        if len(n.args) > cap:
            rep.issues.append(Issue("SG-CON-007", f"ALT group {n.get('group')!r} has {len(n.args)} alternatives (limit {cap})"))
        ranks = n.get("ranks")
        if (not all(isinstance(r, int) and not isinstance(r, bool) and r >= 1 for r in ranks)) or len(set(ranks)) != len(ranks):
            rep.issues.append(Issue("SG-CON-007", "ALT ranks must be distinct ordinal integers >= 1 (never probabilities)"))

    # -- APPLY ----------------------------------------------------------------------------
    def _apply(self, n: Node, ctx: _Ctx, rep: TypeReport) -> None:
        name, ver = n.get("frame"), n.get("version")
        if not self.lib.has(name):
            rep.issues.append(Issue("VC-S05", f"unknown frame {name!r}", None, name))
            return
        f = self.lib.get(name)
        if f.version != ver:
            rep.issues.append(Issue("I-12", f"expression pins {name}@{ver} but the library has version {f.version}", None, name))
        entries = role_entries(n)
        usage = []
        for role, o, filler in entries:
            key = str(filler.get("ref")) if filler.op == "REF" else None
            usage.append((role, o, filler.op != "HOLE", key))
        rep.issues.extend(self.lib.validate_role_usage(name, usage))
        rf = self.lib.resolved(name)
        for role, o, filler in entries:
            r = rf.role(role)
            if r is None or filler.op == "HOLE":
                continue
            want = KIND_TO_SORT.get(r.spec.expected_kind)
            got = sort_of(filler)
            if want is not None and got not in (want, ANY):
                rep.issues.append(Issue("SG-CON-006", f"role {role} of {name} expects sort {want.value}, got {getattr(got, 'value', got)}", role, name))
                continue
            kind_compatible = self._check_expected_kind(
                filler, r.spec.expected_kind, role=role, frame=name, ctx=ctx, rep=rep
            )
            if not kind_compatible or r.cls is None or filler.op not in ("REF", "KIND", "VAR"):
                continue
            if filler.op == 'VAR':
                classes = [concept for name,concept in ctx.variable_classes if name == filler.get('name')]
            elif filler.op == "KIND":
                c = self._concept_name(str(filler.get("concept")))
                classes = [c] if c else []
            else:
                classes = list(self.classes_of(str(filler.get("ref")))) if self.classes_of else []
            verdict = self.onto.classes_compatible(classes, r.cls)
            if verdict is Compat.INCOMPATIBLE:
                if ctx.in_fig_literal:
                    rep.warnings.append(Issue("W-FIGURATIVE", f"{name}.{role}: literal reading is incompatible with {r.cls}; "
                                              "documented by FIG", role, name))
                else:
                    rep.issues.append(Issue("SG-TYP-001", f"{name}.{role}: {classes} is incompatible with {r.cls} "
                                            "(a figurative or coerced reading needs a registered FIG mapping)", role, name))
            elif verdict is Compat.UNDETERMINED:
                rep.warnings.append(Issue("W-TYPE-UNDETERMINED", f"{name}.{role}: membership in {r.cls} is neither derivable nor refutable",
                                          role, name))
