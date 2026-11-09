# ---------------------------------------------------------------------------------------------
# generic builders for fault-injection tests
# ---------------------------------------------------------------------------------------------
from usg.grammar.node import Ann, Node, role_entries, walk  # noqa: E402
from usg.validation.validator import _LEAF_OPS, _SUPPORT_OPS  # noqa: E402
from usg.core.records import Anchor, Source
from usg.core.spans import Span
from usg.core.values import Basis, Outcome
from usg.foundation.builder import build_foundation
from usg.grammar.annot import explicit, grammatical
from usg.grammar.node import apply, assert_, holds, ref, speech_time, tense
from usg.grammar.typecheck import Typechecker
from usg.validation.certificate import Candidate, CertStep, DerivationCertificate, StepType
from usg.validation.rules import Rulebook
from usg.validation.validator import IMPLEMENTED_CHECKS, ValidationContext, Validator

def annotate_all(node, rule="SG-INT-012"):
    """Give every claim-bearing node that lacks support a GRAMMATICAL annotation citing ``rule``."""
    args = tuple(annotate_all(a, rule) for a in node.args)
    ann = node.ann
    if ann is None and (node.op in _SUPPORT_OPS or node.op in _LEAF_OPS):
        ann = Ann(rules=(rule,), basis="GRAMMATICAL")
    return Node(node.op, args, node.params, ann)


def steps_for(expr):
    """A complete derivation for every APPLY / W-handle of ``expr`` (so VC-V04 passes)."""
    S, out, seen = StepType, [], set()
    n = 0
    for _, nd in walk(expr):
        if nd.op == "APPLY":
            name = nd.get("frame")
            out.append(CertStep(f"f{n}", S.FRAME_SELECTION, "SG-INT-040", Basis.GRAMMATICAL, (), (("frame", name),), name))
            n += 1
            for role, o, f in role_entries(nd):
                if f.op == "HOLE":
                    continue
                out.append(CertStep(f"a{n}", S.ROLE_ASSIGNMENT, "SG-INT-012", Basis.GRAMMATICAL, (),
                                    (("frame", name), ("role", f"{role}#{o}")), role))
                n += 1
        if nd.op == "REF" and str(nd.get("ref")).startswith("W:") and nd.get("ref") not in seen:
            seen.add(nd.get("ref"))
            out.append(CertStep(f"r{n}", S.REFERENT_CREATION, "SG-INT-001", Basis.GRAMMATICAL, (), (("referent", nd.get("ref")),), "E"))
            n += 1
    return tuple(out)


def build(expr, text=None, *, annotate=True, outcome=Outcome.RESOLVED, anchor=None, unit=None, steps=None, **cert_kw):
    from usg.core.values import Origin
    text = TEXT if text is None else text
    e = annotate_all(expr) if annotate else expr
    src = Source(text, anchor=anchor)
    cert = DerivationCertificate(src.text_hash, steps=steps_for(e) if steps is None else steps, outcome=outcome, **cert_kw)
    return Candidate(src, unit or Span(0, len(text)), e, cert)


def sp(text, word, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = text.index(word, i + 1)
    return (i, i + len(word))









FND = build_foundation()
TEXT = "The doctor gave the patient medication."
DOC, GAVE, PAT, MED = (4, 10), (11, 15), (20, 27), (28, 38)
CLASSES = {"W:s1:1": ["Doctor"], "W:s1:2": ["Patient"], "W:s1:3": ["Medication"], "W:s1:4": ["Pump"], "W:s1:5": ["Apple"]}


def make_validator(**kw):
    tc = Typechecker(FND.frames, FND.relations, classes_of=lambda r: CLASSES.get(r, ()), mappings=kw.pop("mappings", {"M_TAKE_IN"}))
    ctx = ValidationContext(tc, Rulebook(implemented_checks=IMPLEMENTED_CHECKS), **kw)
    return Validator(ctx), ctx


def give_expr():
    r1 = explicit(ref("W:s1:1"), DOC)
    src = grammatical(ref("W:s1:1"), "SG-INT-012")
    r2 = explicit(ref("W:s1:2"), PAT)
    r3 = explicit(ref("W:s1:3"), MED)
    ap = grammatical(apply("GIVE", 1, {"AGENT": r1, "SOURCE": src, "RECIPIENT": r2, "THEME": r3}), "SG-INT-040", GAVE)
    return assert_(grammatical(tense("PAST", speech_time(), holds(ap)), "SG-INT-051", GAVE), origin="SOURCE_TEXT")


def give_steps():
    S = StepType
    steps = [CertStep(f"r{i}", S.REFERENT_CREATION, "SG-INT-001", Basis.EXPLICIT, (sp,), (("referent", f"W:s1:{i}"),), f"E{i}")
             for i, sp in ((1, DOC), (2, PAT), (3, MED))]
    steps.append(CertStep("l1", S.LEXICAL_SENSE, "SG-INT-040", Basis.GRAMMATICAL, (GAVE,), (("word", "gave"),), "GIVE"))
    steps.append(CertStep("f1", S.FRAME_SELECTION, "SG-INT-040", Basis.GRAMMATICAL, (GAVE,), (("frame", "GIVE"),), "GIVE"))
    for role, rid, sp, basis in (("AGENT#0", "SG-INT-012", DOC, Basis.EXPLICIT), ("SOURCE#0", "SG-INT-012", DOC, Basis.GRAMMATICAL),
                                 ("RECIPIENT#0", "SG-INT-012", PAT, Basis.EXPLICIT), ("THEME#0", "SG-INT-012", MED, Basis.EXPLICIT)):
        steps.append(CertStep(f"a_{role}", S.ROLE_ASSIGNMENT, rid, basis, (sp,), (("frame", "GIVE"), ("role", role)), role))
    steps.append(CertStep("o1", S.OPERATOR_ATTACHMENT, "SG-INT-051", Basis.GRAMMATICAL, (GAVE,), (("tense", "PAST"),), "TENSE"))
    return tuple(steps)


def candidate(expr=None, steps=None, text=TEXT, unit=None, anchor=None, **cert_kw):
    from usg.core.values import Origin
    src = Source(text, anchor=anchor)
    cert = DerivationCertificate(src.text_hash, steps=give_steps() if steps is None else steps, **cert_kw)
    origin = cert_kw.pop("declared_origin", Origin.SOURCE_TEXT)
    return Candidate(src, unit or Span(0, len(text)), expr if expr is not None else give_expr(), cert)
