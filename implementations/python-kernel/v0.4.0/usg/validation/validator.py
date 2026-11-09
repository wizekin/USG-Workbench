"""Pure five-level validator. Missing contextual checks never imply world truth."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping

from .. import GRAMMAR_VERSION, ONTOLOGY_RELEASE, RULESET_RELEASE
from ..core.values import Aggregate, CheckResult as CR, Origin, Outcome, RiskClass
from ..grammar.canon import canonicalize
from ..grammar.node import Node, and_, role_entries, walk
from ..grammar.serialize import canonical_string
from ..grammar.typecheck import Typechecker
from ..grammar.timeval import resolve_node
from ..util import canonical_json, sha256_hex
from .certificate import Candidate, PRODUCER_KINDS, StepType
from .checks import CHECKS, CheckOutcome
from .rules import Rulebook

IMPLEMENTED_CHECKS = frozenset(c.check_id for c in CHECKS if int(c.level) < 5)
_LEAF_OPS = frozenset({"REF", "KIND", "VALUE", "LIT"})
_SUPPORT_OPS = frozenset({"APPLY", "RELATE", "PROPERTY", "NOT", "Q", "MODAL", "TENSE", "ATTRIBUTE", "COND", "COUNTERFACTUAL", "FIG"})


@dataclass
class ValidationContext:
    typechecker: Typechecker
    rulebook: Rulebook = field(default_factory=lambda: Rulebook(implemented_checks=IMPLEMENTED_CHECKS))
    resolves_ref: Callable | None = None
    surface_of: Callable | None = None
    replays: Mapping[str, Callable] = field(default_factory=dict)
    allow_provisional: bool = False
    contextual: Callable | None = None


@dataclass(frozen=True)
class ValidationReport:
    results: tuple[CheckOutcome, ...]
    aggregate: Aggregate
    risk: RiskClass
    risk_reasons: tuple[str, ...]
    outcome: Outcome
    rulebook_hash: str

    def failed(self):
        return [x for x in self.results if x.result is CR.FAIL]

    def codes(self):
        return sorted(set(x.check_id for x in self.failed()))

    def result_of(self, code):
        xs = [x.result for x in self.results if x.check_id == code]
        return next((r for r in (CR.FAIL, CR.UNCERTAIN, CR.PASS, CR.NOT_CHECKED) if r in xs), CR.NOT_CHECKED)

    def to_json(self):
        return {"results": [x.to_json() for x in self.results], "aggregate": self.aggregate.value,
                "risk": self.risk.name, "risk_reasons": list(self.risk_reasons), "outcome": self.outcome.value,
                "rulebook_hash": self.rulebook_hash}

    def content_hash(self):
        return sha256_hex(canonical_json(self.to_json()))


def aggregate(results):
    checked = [x for x in results if int(x.level) < 5]
    if any(x.result is CR.FAIL for x in checked):
        return Aggregate.INVALID
    if any(x.result is CR.UNCERTAIN for x in checked):
        return Aggregate.UNCERTAIN
    return Aggregate.FORMALLY_VALID


class Validator:
    def __init__(self, context: ValidationContext):
        self.ctx = context

    def validate(self, c: Candidate) -> ValidationReport:
        results = {cid: [CheckOutcome(cid, CR.PASS)] for cid in IMPLEMENTED_CHECKS}
        risk, reasons = RiskClass.LOW, []

        def add(cid, detail, element=None, result=CR.FAIL):
            if results[cid][0].result is CR.PASS:
                results[cid] = []
            results[cid].append(CheckOutcome(cid, result, detail, element))

        def report():
            xs = tuple(x for cid in sorted(results) for x in results[cid])
            if self.ctx.contextual:
                try:
                    contextual = tuple(self.ctx.contextual(c))
                    if any(int(x.level) != 5 for x in contextual):
                        raise ValueError('contextual check level')
                    xs += contextual
                except Exception:
                    xs += tuple(CheckOutcome(f'VC-C{i:02}', CR.UNCERTAIN, 'contextual service unavailable') for i in range(1,8))
            return ValidationReport(xs, aggregate(xs), risk, tuple(reasons), c.certificate.outcome, self.ctx.rulebook.content_hash())

        try:
            cert, e = c.certificate, c.expression
            if e.op != "ASSERT" or cert.producer_kind not in PRODUCER_KINDS:
                add("VC-S01", "expected ASSERT and an automated producer")
            if cert.source_hash != c.source.text_hash or cert.grammar_version != GRAMMAR_VERSION or cert.ontology_release != ONTOLOGY_RELEASE or cert.ruleset_release != RULESET_RELEASE:
                add("VC-S02", "source or release mismatch")
            if not 0 <= c.unit_span.start < c.unit_span.end <= len(c.source.text):
                add("VC-S02", "unit outside stored source")
            if len({s.step_id for s in cert.steps}) != len(cert.steps):
                add("VC-S01", "duplicate step ids")
            if any(x.result is CR.FAIL for cid in ("VC-S01", "VC-S02") for x in results[cid]):
                for cid in results:
                    if cid not in {"VC-S01", "VC-S02"}:
                        results[cid] = [CheckOutcome(cid, CR.NOT_CHECKED)]
                return report()
            nodes = list(walk(e))
            tc = self.ctx.typechecker
            tr = tc.check(e, candidate=self.ctx.allow_provisional)
            mapping = {"I-02": "VC-S03", "SG-CON-002": "VC-S05", "SG-CON-003": "VC-T04", "SG-CON-007": "VC-S14",
                       "SG-CON-008": "VC-S11", "SG-TYP-001": "VC-T02", "SG-TYP-002": "VC-T07", "SG-KNW-003": "VC-G09"}
            for issue in tr.issues:
                cid = mapping.get(issue.code, issue.code)
                if issue.code == "SG-CON-006":
                    cid = "VC-T01" if "role " in issue.message else "VC-S09"
                if issue.code == "SG-FRM-004" or (issue.code == "SG-FRM-002" and "parameter" in issue.message):
                    cid = "VC-S06"
                if cid not in results:
                    cid = "VC-S09"
                add(cid, issue.message, issue.role)
            for issue in tr.warnings:
                if issue.code == "W-TYPE-UNDETERMINED":
                    add("VC-T02", issue.message, issue.role, CR.UNCERTAIN)
                    risk = max(risk, RiskClass.MEDIUM)
                elif issue.code == "W-FIGURATIVE":
                    risk = max(risk, RiskClass.MEDIUM)
            if not self.ctx.resolves_ref and not any(x.result is CR.FAIL for x in results["VC-S03"]):
                results["VC-S03"] = [CheckOutcome("VC-S03", CR.NOT_CHECKED)]
            if not self.ctx.surface_of:
                results["VC-V02"] = [CheckOutcome("VC-V02", CR.NOT_CHECKED)]
            spans = [sp for s in cert.steps for sp in s.spans]
            for path, n in nodes:
                label = ".".join(map(str, path)) + ":" + n.op
                if n.op == "ERROR":
                    add("VC-S11", "ERROR is candidate-only", label)
                if n.op == "REF" and self.ctx.resolves_ref and not self.ctx.resolves_ref(str(n.get("ref"))):
                    add("VC-S03", "referent does not resolve", label)
                if n.op == "KIND" and str(n.get("concept")).startswith("P:"):
                    risk = max(risk, RiskClass.HIGH)
                    if not self.ctx.allow_provisional:
                        add("VC-S15", "provisional id in canonical record", label)
                if n.op == "APPLY" and tc.lib.has(n.get("frame")):
                    rf = tc.lib.resolved(n.get("frame"))
                    if rf.frame.abstract or n.get("version") != rf.frame.version:
                        add("VC-S05", "abstract or unpinned frame", label)
                ann = n.ann
                if n.op in _SUPPORT_OPS | _LEAF_OPS and ann is None:
                    add("VC-V01", "element lacks support", label)
                if ann:
                    spans.extend(ann.spans)
                    for r in ann.rules:
                        if r not in self.ctx.rulebook:
                            add("VC-S04", "unregistered rule " + str(r), label)
                    if ann.basis not in {"EXPLICIT", "GRAMMATICAL", "BACKGROUND"}:
                        add("VC-V03", "unknown basis", label)
                    elif ann.basis == "EXPLICIT" and not ann.spans:
                        add("VC-V03", "EXPLICIT requires a span", label)
                    elif ann.basis in {"GRAMMATICAL", "BACKGROUND"}:
                        if not ann.rules:
                            add("VC-V03", "derived element needs a rule", label)
                        for r in ann.rules:
                            rid = self.ctx.rulebook.resolve(r) or ""
                            inference = rid.startswith(("SG-KNW-", "SG-EVD-"))
                            if (ann.basis == "BACKGROUND") != inference:
                                add("VC-V03", "basis and rule class disagree", label)
                    if ann.basis == "BACKGROUND":
                        risk = max(risk, RiskClass.MEDIUM)
                        if c.declared_origin is not Origin.BACKGROUND_INFERENCE:
                            add("VC-V06", "background is not source-stated", label)
                        if not any(s.step_type is StepType.INFERENCE for s in cert.steps):
                            add("VC-V09", "background lacks inference step", label)
                    if self.ctx.surface_of and n.op == "REF" and ann.basis == "EXPLICIT" and ann.spans:
                        forms = self.ctx.surface_of(str(n.get("ref")))
                        cited = " ".join(c.source.text[a:b] for a, b in ann.spans)
                        if forms and not any(re.search(r"(?<!\w)" + re.escape(x) + r"(?!\w)", cited, re.I) for x in forms):
                            add("VC-V02", "span does not support referent", label)
                if n.op == "TIME_REL" and (n.get("resolved_start") or n.get("resolved_end")):
                    raw = Node(n.op, n.args, {k: v for k, v in n.params if not k.startswith("resolved_")}, n.ann)
                    if resolve_node(raw, c.source.anchor) != n:
                        add("VC-V05", "relative time does not replay against anchor", label)
            for sp in spans:
                if len(sp) != 2 or not all(isinstance(x, int) and not isinstance(x, bool) for x in sp) or not c.unit_span.start <= sp[0] < sp[1] <= c.unit_span.end:
                    add("VC-S10", "span outside source/unit or empty")
            for s in cert.steps:
                if s.rule_id not in self.ctx.rulebook:
                    add("VC-S04", "unregistered rule " + s.rule_id)
                if s.step_type is StepType.INFERENCE:
                    if not s.premises or any(p not in {x.step_id for x in cert.steps if x is not s} for p in s.premises) or not s.rule_id.startswith("SG-KNW-"):
                        add("VC-V09", "invalid inference premises or rule")
                if s.rule_id in self.ctx.replays:
                    ok, why = self.ctx.replays[s.rule_id](s, c)
                    if not ok:
                        add("VC-V05", why)
                if s.step_type is StepType.CANONICALIZATION and canonicalize(e, anchor=c.source.anchor, relations=tc.relations) != e:
                    add("VC-V05", "claimed canonical expression is not canonical")
            frame_steps = [dict(s.inputs).get("frame") for s in cert.steps if s.step_type is StepType.FRAME_SELECTION]
            role_steps = {(dict(s.inputs).get("frame"), dict(s.inputs).get("role")) for s in cert.steps if s.step_type is StepType.ROLE_ASSIGNMENT}
            ref_steps = {dict(s.inputs).get("referent") for s in cert.steps if s.step_type is StepType.REFERENT_CREATION}
            for _, n in nodes:
                if n.op == "APPLY":
                    if n.get("frame") not in frame_steps:
                        add("VC-V04", "frame selection step missing")
                    for role, o, filler in role_entries(n):
                        if filler.op != "HOLE" and (n.get("frame"), f"{role}#{o}") not in role_steps:
                            add("VC-V04", "role assignment step missing: " + role)
                if n.op == "REF" and str(n.get("ref")).startswith("W:") and n.get("ref") not in ref_steps:
                    add("VC-V04", "referent creation step missing")
            has_alt = any(n.op == "ALT" for _, n in nodes)
            if (cert.outcome is Outcome.AMBIGUOUS) != has_alt or (cert.outcome is Outcome.RESOLVED and cert.unresolved):
                add("VC-V04", "outcome and retained ambiguity/unresolved items disagree")
            self._logic(e, add)
            if with_presuppositions(e, tc.lib) != e:
                add("VC-G08", "factive content not emitted inside its context")
            text = c.unit_text.lower().replace("not only", "")
            ops = {n.op for _, n in nodes}
            neg = bool(re.search(r"\b(not|never|no|لم|لن)\b|n['’]t\b", text))
            has_neg = "NOT" in ops or any(n.op == "Q" and n.get("quant") == "NO" for _, n in nodes)
            if neg and not has_neg:
                add("VC-V07", "negative cue dropped")
            if not neg and has_neg:
                add("VC-V07", "negation has no source cue", result=CR.UNCERTAIN)
            for pattern, required in ((r"\b(may|might|must|can|could|should)\b", "MODAL"), (r"\bif\b", "COND"), (r"\b(every|all|each|some)\b", "Q"), (r"\bwill\b", "TENSE")):
                if re.search(pattern, text) and required not in ops:
                    add("VC-V07", "operator cue dropped: " + required, result=CR.UNCERTAIN)
            nums = set(re.findall(r"\b\d+\b", text))
            encoded = {str(n.get("value")) for _, n in nodes if n.op == "LIT"} | {str(n.get("n")) for _, n in nodes if n.op == "Q"}
            if nums - encoded:
                add("VC-V08", "numeric cue absent from IR", result=CR.UNCERTAIN)
            if has_alt or "FIG" in ops:
                risk = max(risk, RiskClass.MEDIUM)
            if "Q" in ops and "NOT" in ops:
                risk = max(risk, RiskClass.HIGH)
                reasons.append("negation scoping over a quantifier")
            return report()
        except (ValueError, TypeError, KeyError, AttributeError, IndexError, RecursionError) as ex:
            add("VC-S01", "malformed candidate: " + type(ex).__name__)
            return report()

    def _logic(self, e, add):
        buckets={}
        def context(n,key=(),opaque=False,path=()):
            if n.op=='ASSERT':
                context(n.args[0],key+('ASSERT:'+canonical_json(n.params_dict()),),opaque,path+(0,))
            elif n.op=='TENSE':
                context(n.args[1],key+('TENSE:'+n.get('tense')+canonical_string(n.args[0])+':'+str(path),),opaque,path+(1,))
            elif n.op=='AND':
                for i,a in enumerate(n.args):context(a,key,opaque,path+(i,))
            elif n.op in {'ATTRIBUTE','MODAL','ALT','Q','COND','COUNTERFACTUAL','OR','IMPLIES'}:
                # Each alternative/antecedent and each holder has its own scope.
                for i,a in enumerate(n.args):
                    if getattr(a.sort,'value',a.sort)=='PROP':context(a,key+(n.op+str(path)+':'+str(i),),True,path+(i,))
            else:
                buckets.setdefault(key,[]).append(n)
                if opaque and n.op=='SAME_AS' and n.get('scope')!='WITHIN':
                    add('VC-G09','identity escapes opaque context')
                if n.op=='HOLDS' and n.args[0].op=='APPLY':
                    for role,_,filler in role_entries(n.args[0]):
                        if role=='CONTENT':context(filler,key+('CONTENT:'+str(path),),True,path+(0,))
        context(e)
        from ..cognition.entailments import frame_entailments
        for leaves in buckets.values():
            positive={canonical_string(x) for x in leaves if x.op!='NOT'}
            if any(x.op=='NOT' and canonical_string(x.args[0]) in positive for x in leaves):
                add('VC-G03','contradictory conjuncts in one context')
            grouped={}
            for n in leaves:
                if n.op=='RELATE':grouped.setdefault(n.get('relation'),[]).append(tuple(canonical_string(a) for a in n.args))
            for name,edges in grouped.items():
                rd=self.ctx.typechecker.relations.get(name)
                if rd is None:continue
                if rd.irreflexive and any(a==b for a,b in edges):add('VC-G02',name+' is irreflexive')
                if rd.asymmetric and any((b,a) in edges for a,b in edges):add('VC-G02',name+' is asymmetric')
                if not rd.cycles_allowed:
                    adj={}
                    for a,b in edges:adj.setdefault(a,set()).add(b)
                    def reaches(start):
                        todo=list(adj.get(start,()));seen=set()
                        while todo:
                            at=todo.pop()
                            if at==start:return True
                            if at not in seen:
                                seen.add(at);todo.extend(adj.get(at,()))
                        return False
                    if any(reaches(a) for a in adj):add('VC-G01',name+' contains a cycle')
            # Only completed events in this exact temporal/context bucket license
            # final-state constraints. Typical outcomes are excluded upstream.
            effects=[]
            for n in leaves:
                if n.op=='HOLDS':effects.extend(frame_entailments(n,self.ctx.typechecker.lib,'local'))
            onto=self.ctx.typechecker.lib.ontology
            for effect in effects:
                if effect['relation']!='HAS_VALUE' or len(effect['arguments'])!=2:continue
                subject,expected=effect['arguments']
                for n in leaves:
                    negative=n.op=='NOT';atom=n.args[0] if negative else n
                    if atom.op!='PROPERTY' or atom.args[0].op!='REF' or atom.args[0].get('ref')!=subject or atom.args[1].op!='VALUE':continue
                    actual=atom.args[1].get('concept')
                    if negative and actual==expected or not negative and onto.has(actual) and onto.has(expected) and onto.disjoint(actual,expected):
                        add('VC-G05','essential completed effect contradicts a property in the same context')


def with_presuppositions(e, lib):
    def need(x):
        if x.op == "HOLDS" and x.args[0].op == "APPLY" and x.args[0].get("frame") == "KNOW":
            return [f for r, _, f in role_entries(x.args[0]) if r == "CONTENT"]
        return []
    # Suppress the local expansion of a KNOW already accompanied by its factive content.
    if e.op == "AND":
        args = []
        for a in e.args:
            if need(a) and all(p in e.args for p in need(a)):
                args.append(a)
            else:
                fixed = with_presuppositions(a, lib)
                args.extend(fixed.args if fixed.op == "AND" else (fixed,))
        return Node(e.op, tuple(args), e.params, e.ann)
    n = Node(e.op, tuple(with_presuppositions(a, lib) for a in e.args), e.params, e.ann)
    return and_(n, *need(n)) if need(n) else n


class Route(str, Enum):
    REPAIR = "REPAIR"
    REJECT = "REJECT"
    ACCEPT_PROVISIONAL = "ACCEPT_PROVISIONAL"
    PRESERVE_AMBIGUITY = "PRESERVE_AMBIGUITY"
    REVIEW = "REVIEW"
    DEFER = "DEFER"


@dataclass(frozen=True)
class Routing:
    route: Route
    reason: str


def route(report, *, retries_left=0, panel_available=True):
    if report.aggregate is Aggregate.INVALID:
        integrity = bool(set(report.codes()) & {"VC-S01", "VC-S02"})
        return Routing(Route.REPAIR if retries_left > 0 and not integrity else Route.REJECT, "validation failed")
    if report.outcome is Outcome.AMBIGUOUS:
        return Routing(Route.PRESERVE_AMBIGUITY, "retain alternatives")
    if report.aggregate is Aggregate.UNCERTAIN or report.risk >= RiskClass.HIGH:
        return Routing(Route.REVIEW if panel_available else Route.DEFER, "automated checks required")
    return Routing(Route.ACCEPT_PROVISIONAL, "source-supported; not verified world knowledge")


@dataclass(frozen=True)
class RepairItem:
    check_id: str
    detail: str
    rule_ids: tuple[str, ...]
    rule_text: tuple[str, ...]


def repair_request(report, rulebook):
    return [RepairItem(x.check_id, x.detail, tuple(r.rule_id for r in rulebook.rules_for_check(x.check_id)),
                       tuple(r.description for r in rulebook.rules_for_check(x.check_id))) for x in report.failed()]
