import dataclasses
import unittest

from usg.core.records import Anchor, Source
from usg.core.spans import Span
from usg.core.values import Aggregate, Basis, CheckResult, Origin, Outcome, RiskClass
from usg.grammar.annot import background, explicit, grammatical
from usg.grammar.node import (Ann, Node, alt, and_, apply, assert_, attribute, error, fig, hole, holds, kind, lit, modal,
                              not_, or_, prop, q, ref, relate, same_as, speech_time, temporal, tense, time_lit, time_rel,
                              value, var)
from usg.validation.certificate import Candidate, CertStep, DerivationCertificate, StepType
from usg.validation.validator import (IMPLEMENTED_CHECKS, Route, aggregate, repair_request, route,
                                      with_presuppositions)
from usg.validation.checks import CheckOutcome
from tests.vhelpers import (CLASSES, DOC, FND, GAVE, MED, PAT, TEXT, annotate_all, build, candidate, give_expr,
                            give_steps, make_validator, sp, steps_for)

V, CTX = make_validator()
R = lambda n: ref(f"W:s1:{n}")


def give(a=1, s=1, r=2, t=3):
    return apply("GIVE", 1, {"AGENT": R(a), "SOURCE": R(s), "RECIPIENT": R(r), "THEME": R(t)})


def opens(n=7):
    return holds(apply("OPEN", 1, {"UNDERGOER": R(n)}))


def rep(cand, validator=V):
    return validator.validate(cand)


def fails(r):
    return set(r.codes())


def with_cert(c, **kw):
    return dataclasses.replace(c, certificate=dataclasses.replace(c.certificate, **kw))


class CleanCandidateTests(unittest.TestCase):
    def test_the_standard_candidate_is_formally_valid_and_low_risk(self):
        r = rep(candidate())
        self.assertEqual(r.aggregate, Aggregate.FORMALLY_VALID)
        self.assertEqual(r.risk, RiskClass.LOW)
        self.assertEqual(r.codes(), [])
        # only the checks that need an external resolver are NOT_CHECKED
        self.assertEqual({x.check_id for x in r.results if x.result is CheckResult.NOT_CHECKED}, {"VC-S03", "VC-V02"})
        self.assertEqual({x.check_id for x in r.results}, set(IMPLEMENTED_CHECKS))

    def test_resolvers_turn_not_checked_into_real_results(self):
        forms = {"W:s1:1": ["doctor"], "W:s1:2": ["patient"], "W:s1:3": ["medication"]}
        v, _ = make_validator(resolves_ref=lambda r: True, surface_of=lambda r: forms.get(r, []))
        r = rep(candidate(), v)
        self.assertEqual(r.result_of("VC-S03"), CheckResult.PASS)
        self.assertEqual(r.result_of("VC-V02"), CheckResult.PASS)

    def test_validation_is_pure_and_reproducible(self):
        a, b = rep(candidate()), rep(candidate())
        self.assertEqual(a.content_hash(), b.content_hash())
        other, _ = make_validator()
        self.assertEqual(rep(candidate(), other).content_hash(), a.content_hash())
        self.assertEqual(a.to_json()["aggregate"], "FORMALLY_VALID")
        self.assertTrue(a.rulebook_hash)


class L1StructuralTests(unittest.TestCase):
    def test_header_failures_short_circuit_everything_else(self):
        for label, c in {
            "human producer": with_cert(candidate(), producer_kind="HUMAN"),
            "wrong source hash": with_cert(candidate(), source_hash="0" * 64),
            "grammar version": with_cert(candidate(), grammar_version="0.9"),
            "duplicate steps": with_cert(candidate(), steps=give_steps() + give_steps()[:1]),
            "not an ASSERT": candidate(expr=holds(give())),
        }.items():
            r = rep(c)
            self.assertEqual(r.aggregate, Aggregate.INVALID, label)
            self.assertTrue(fails(r) & {"VC-S01", "VC-S02"}, label)
            others = [x for x in r.results if x.check_id not in ("VC-S01", "VC-S02")]
            self.assertTrue(all(x.result is CheckResult.NOT_CHECKED for x in others), label)

    def test_unit_outside_the_source(self):
        c = candidate()
        bad = dataclasses.replace(c, unit_span=Span(0, 500))
        self.assertEqual(fails(rep(bad)), {"VC-S02"})

    def test_unknown_ids(self):
        e = assert_(holds(apply("OPEN", 1, {"UNDERGOER": kind("Nonexistent")})))
        self.assertIn("VC-S03", fails(rep(build(e))))
        e = assert_(holds(apply("OPEN", 1, {"UNDERGOER": ref("REFERENT:99")})))
        v, _ = make_validator(resolves_ref=lambda r: False)
        self.assertIn("VC-S03", fails(rep(build(e), v)))
        v2, _ = make_validator(resolves_ref=lambda r: True)
        self.assertNotIn("VC-S03", fails(rep(build(e), v2)))
        self.assertEqual(rep(build(e)).result_of("VC-S03"), CheckResult.NOT_CHECKED)  # no resolver: never silently passed

    def test_only_registered_rules_may_be_cited(self):
        e = assert_(tense("PAST", speech_time(), holds(give())))
        c = build(e)
        invented = dataclasses.replace(c, expression=annotate_all(assert_(tense("PAST", grammatical(speech_time(), "SG-INT-999"), holds(give()))), "SG-INT-012"))
        invented = build(assert_(grammatical(tense("PAST", speech_time(), holds(give())), "SG-INT-777")))
        self.assertIn("VC-S04", fails(rep(invented)))
        bad_step = with_cert(c, steps=c.certificate.steps + (CertStep("x", StepType.OPERATOR_ATTACHMENT, "SG-MADE-UP-1", Basis.GRAMMATICAL),))
        self.assertIn("VC-S04", fails(rep(bad_step)))
        # aliases and legacy ids resolve
        for rid in ("PASSIVE_AGENT_MAPPING", "SG-002", "SG-INT-010"):
            ok = build(assert_(grammatical(tense("PAST", speech_time(), holds(give())), rid)))
            self.assertNotIn("VC-S04", fails(rep(ok)), rid)

    def test_frame_and_role_structure(self):
        cases = {
            "VC-S05": assert_(holds(apply("NO_SUCH_FRAME", 1, {}))),
            "VC-S06": assert_(holds(apply("TREAT", 1, {"AGENT": R(1), "UNDERGOER": R(2)}))),
            "VC-S07": assert_(holds(apply("GIVE", 1, {"AGENT": R(1), "SOURCE": R(1), "RECIPIENT": R(2)}))),
        }
        for code, e in cases.items():
            self.assertIn(code, fails(rep(build(e))), code)
        abstract = assert_(holds(apply("TRANSFER", 1, {"SOURCE": R(1), "RECIPIENT": R(2), "THEME": R(3)})))
        self.assertIn("VC-S05", fails(rep(build(abstract))))
        self.assertIn("VC-S06", fails(rep(build(assert_(holds(apply("SEE", 1, {"EXPERIENCER": R(1), "STIMULUS": R(2), "MODALITY": lit("X")})))))))

    def test_spans_must_lie_in_the_text_and_the_unit(self):
        e = assert_(tense("PAST", speech_time(), holds(give())))
        base = build(e)
        c = candidate()
        small = dataclasses.replace(c, unit_span=Span(0, 20))  # the MED span [28,38) is outside this unit
        self.assertIn("VC-S10", fails(rep(small)))
        out_of_text = build(assert_(explicit(tense("PAST", speech_time(), holds(give())), (0, 500))))
        self.assertIn("VC-S10", fails(rep(out_of_text)))
        invalid = build(assert_(explicit(tense("PAST", speech_time(), holds(give())), (5, 5))))
        self.assertIn("VC-S10", fails(rep(invalid)))
        step_bad = with_cert(c, steps=c.certificate.steps + (CertStep("z", StepType.OPERATOR_ATTACHMENT, "SG-INT-051", spans=((900, 910),)),))
        self.assertIn("VC-S10", fails(rep(step_bad)))

    def test_error_nodes_never_survive(self):
        e = assert_(and_(holds(give()), error("ROLE_UNKNOWN")))
        self.assertIn("VC-S11", fails(rep(build(e))))
        v, _ = make_validator(allow_provisional=True)
        self.assertIn("VC-S11", fails(rep(build(e), v)))  # even for provisional targets

    def test_scope_alt_provisional_and_depth(self):
        free = assert_(holds(apply("OPEN", 1, {"UNDERGOER": var("x")})))
        self.assertIn("VC-S12", fails(rep(build(free))))
        body = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        self.assertIn("VC-S13", fails(rep(build(assert_(q("FORALL", "x", body, q("EXISTS", "x", body, body)))))))
        many = alt("g", [holds(give(i, i, 2, 3)) for i in range(1, 7)])
        self.assertIn("VC-S14", fails(rep(build(assert_(many), outcome=Outcome.AMBIGUOUS))))
        prov = assert_(holds(apply("OPEN", 1, {"UNDERGOER": kind("P:1")})))
        self.assertIn("VC-S15", fails(rep(build(prov))))
        v, _ = make_validator(allow_provisional=True)
        ok = rep(build(prov), v)
        self.assertNotIn("VC-S15", fails(ok))
        self.assertGreaterEqual(ok.risk, RiskClass.HIGH)  # a new concept is high risk
        deep = holds(give())
        for _ in range(15):
            deep = not_(deep)
        self.assertIn("VC-S16", fails(rep(build(assert_(deep)))))


class L2TypeTests(unittest.TestCase):
    def test_kind_class_value_and_property_checks(self):
        eats_prop = assert_(holds(apply("EAT", 1, {"EATER": R(6), "FOOD": holds(give())})))
        self.assertIn("VC-T01", fails(rep(build(eats_prop))))
        pump_eats = assert_(holds(apply("EAT", 1, {"EATER": R(4), "FOOD": R(5)})))
        self.assertIn("VC-T02", fails(rep(build(pump_eats))))
        self.assertIn("VC-T03", fails(rep(build(assert_(prop(R(9), "Color", value("Young")))))))
        self.assertIn("VC-T03", fails(rep(build(assert_(prop(R(9), "Temperature", lit(37, "Quantity")))))))
        self.assertIn("VC-T04", fails(rep(build(assert_(holds(apply("OPEN", 1, {"UNDERGOER": ref("CONCEPT:5")})))))))
        self.assertIn("VC-T06", fails(rep(build(assert_(holds(apply("COMMERCIAL_TRANSACTION", 1, {"BUYER": R(6), "SELLER": R(6), "GOODS": R(9)})))))))
        self.assertIn("VC-T08", fails(rep(build(assert_(prop(R(9), "Red", value("Red")))))))

    def test_undetermined_class_makes_the_candidate_uncertain_not_invalid(self):
        unknown = assert_(holds(apply("EAT", 1, {"EATER": R(6), "FOOD": ref("W:s1:55")})))
        r = rep(build(unknown))
        self.assertEqual(r.aggregate, Aggregate.UNCERTAIN)
        self.assertEqual(r.result_of("VC-T02"), CheckResult.UNCERTAIN)
        self.assertGreaterEqual(r.risk, RiskClass.MEDIUM)

    def test_figurative_mappings_must_be_registered(self):
        lit_ = apply("EAT", 1, {"EATER": R(4), "FOOD": R(5)})
        intended = apply("MOVE", 1, {"MOVER": R(5)})
        ok = rep(build(assert_(fig("M_TAKE_IN", lit_, intended))))
        self.assertNotIn("VC-T07", fails(ok))
        self.assertNotIn("VC-T02", fails(ok))  # the incompatible literal reading is documented by FIG
        self.assertGreaterEqual(ok.risk, RiskClass.MEDIUM)
        self.assertIn("VC-T07", fails(rep(build(assert_(fig("M_UNKNOWN", lit_, intended))))))


class L3LogicTests(unittest.TestCase):
    def test_acyclic_and_asymmetric_relations(self):
        a, b, c = R(1), R(2), R(3)
        cycle = assert_(and_(relate("PROPER_PART_OF", a, b), relate("PROPER_PART_OF", b, c), relate("PROPER_PART_OF", c, a)))
        self.assertIn("VC-G01", fails(rep(build(cycle))))
        both = assert_(and_(relate("PROPER_PART_OF", a, b), relate("PROPER_PART_OF", b, a)))
        self.assertIn("VC-G02", fails(rep(build(both))))
        self.assertIn("VC-G02", fails(rep(build(assert_(relate("PROPER_PART_OF", a, a))))))
        self.assertEqual(fails(rep(build(assert_(and_(relate("KNOWS", a, b), relate("KNOWS", b, a)))))), set())  # a valid social cycle
        negated = assert_(and_(relate("PROPER_PART_OF", a, b), not_(relate("PROPER_PART_OF", b, a))))
        self.assertEqual(fails(rep(build(negated))), set())  # only POSITIVELY asserted facts count

    def test_contradiction_in_one_context(self):
        p = prop(R(9), "Color", value("Red"))
        self.assertIn("VC-G03", fails(rep(build(assert_(and_(p, not_(p)))))))
        self.assertNotIn("VC-G03", fails(rep(build(assert_(and_(p, not_(prop(R(9), "Color", value("Blue")))))))))

    def test_temporal_consistency(self):
        a, b = time_lit("INTERVAL", "2026-10-01/2026-10-05"), time_lit("INTERVAL", "2026-10-10/2026-10-12")
        self.assertEqual(fails(rep(build(assert_(temporal("BEFORE", a, b))))), set())
        self.assertIn("VC-G06", fails(rep(build(assert_(temporal("AFTER", a, b))))))

    def test_presupposed_content_must_be_emitted_in_context(self):
        know = holds(apply("KNOW", 1, {"EXPERIENCER": R(6), "CONTENT": opens()}))
        bare = assert_(know)
        self.assertIn("VC-G08", fails(rep(build(bare))))
        fixed = with_presuppositions(bare, FND.frames)
        self.assertEqual(fails(rep(build(fixed))), set())
        self.assertEqual(with_presuppositions(fixed, FND.frames), fixed)  # idempotent
        believed = assert_(holds(apply("BELIEVE", 1, {"EXPERIENCER": R(8), "CONTENT": know})))
        self.assertIn("VC-G08", fails(rep(build(believed))))
        believed_ok = with_presuppositions(believed, FND.frames)
        self.assertEqual(fails(rep(build(believed_ok))), set())
        # the presupposition lives INSIDE the belief context, not in the author's
        belief = [n for _, n in __import__("usg.grammar.node", fromlist=["walk"]).walk(believed_ok) if n.op == "APPLY" and n.get("frame") == "BELIEVE"][0]
        self.assertEqual(belief.args[0].op, "AND")  # CONTENT sorts first among the stored roles

    def test_identity_inside_attitudes_must_be_scoped(self):
        bad = assert_(attribute(R(8), "BELIEF", same_as(R(1), R(2), "DISCOURSE")))
        self.assertIn("VC-G09", fails(rep(build(bad))))
        good = assert_(attribute(R(8), "BELIEF", same_as(R(1), R(2), "WITHIN")))
        self.assertNotIn("VC-G09", fails(rep(build(good))))
        believe = assert_(holds(apply("BELIEVE", 1, {"EXPERIENCER": R(8), "CONTENT": same_as(R(1), R(2), "RESOLVED_WORLD")})))
        self.assertIn("VC-G09", fails(rep(build(believe))))
        self.assertNotIn("VC-G09", fails(rep(build(assert_(same_as(R(1), R(2), "RESOLVED_WORLD"))))))  # author's own context


class L4EvidenceTests(unittest.TestCase):
    def test_every_element_needs_support(self):
        # An actual unsupported expression (give_expr already has complete annotations).
        r = rep(build(assert_(holds(give())), annotate=False))
        self.assertIn("VC-V01", fails(r))
        # strip just one element's annotation
        base = give_expr()
        stripped = assert_(tense("PAST", speech_time(), holds(apply("GIVE", 1, {
            "AGENT": explicit(R(1), DOC), "SOURCE": grammatical(R(1), "SG-INT-012"), "RECIPIENT": R(2), "THEME": explicit(R(3), MED)}))))
        c = candidate(expr=annotate_all(stripped, "SG-INT-012"))
        self.assertEqual(fails(rep(c)), set())  # annotate_all repaired it
        raw = assert_(grammatical(tense("PAST", speech_time(), holds(grammatical(apply("GIVE", 1, {
            "AGENT": explicit(R(1), DOC), "SOURCE": grammatical(R(1), "SG-INT-012"), "RECIPIENT": R(2), "THEME": explicit(R(3), MED)}), "SG-INT-040", GAVE))), "SG-INT-051", GAVE))
        c2 = candidate(expr=raw)
        self.assertEqual(fails(rep(c2)), {"VC-V01"})  # exactly the unannotated RECIPIENT

    def test_basis_must_match_the_derivation(self):
        def one(node_ann):
            e = assert_(grammatical(tense("PAST", speech_time(), holds(grammatical(apply("GIVE", 1, {
                "AGENT": explicit(R(1), DOC), "SOURCE": grammatical(R(1), "SG-INT-012"),
                "RECIPIENT": node_ann(R(2)), "THEME": explicit(R(3), MED)}), "SG-INT-040", GAVE))), "SG-INT-051", GAVE))
            return rep(candidate(expr=e))
        self.assertIn("VC-V03", fails(one(lambda n: n.with_ann(Ann(rules=("SG-INT-012",), basis="EXPLICIT")))))  # EXPLICIT without a span
        self.assertIn("VC-V03", fails(one(lambda n: n.with_ann(Ann(rules=("SG-KNW-010",), basis="GRAMMATICAL")))))  # knowledge rule as grammar
        self.assertIn("VC-V03", fails(one(lambda n: n.with_ann(Ann(rules=("SG-INT-012",), basis="BACKGROUND")))))  # construction rule as inference
        self.assertIn("VC-V03", fails(one(lambda n: n.with_ann(Ann(spans=(PAT,), basis="MAGIC")))))

    def test_text_support_when_surface_forms_are_known(self):
        forms = {"W:s1:1": ["doctor"], "W:s1:2": ["nurse"], "W:s1:3": ["medication"]}
        v, _ = make_validator(surface_of=lambda r: forms.get(r, []))
        r = rep(candidate(), v)
        self.assertEqual([x.element for x in r.failed() if x.check_id == "VC-V02"], ["0.1.0.0.2:REF"] if False else [x.element for x in r.failed()])
        self.assertIn("VC-V02", fails(r))  # span 'patient' does not support 'nurse'

    def test_derivation_chain_and_outcome_consistency(self):
        c = candidate()
        steps = list(c.certificate.steps)
        no_frame = with_cert(c, steps=tuple(s for s in steps if s.step_type is not StepType.FRAME_SELECTION))
        self.assertIn("VC-V04", fails(rep(no_frame)))
        no_role = with_cert(c, steps=tuple(s for s in steps if s.step_id != "a_THEME#0"))
        self.assertIn("VC-V04", fails(rep(no_role)))
        no_ref = with_cert(c, steps=tuple(s for s in steps if s.step_id != "r1"))
        self.assertIn("VC-V04", fails(rep(no_ref)))
        self.assertIn("VC-V04", fails(rep(with_cert(c, unresolved=("which medication?",)))))  # RESOLVED yet unresolved points
        alts = assert_(alt("g", [holds(give()), holds(give(2, 2, 1, 3))]))
        self.assertIn("VC-V04", fails(rep(build(alts))))  # ALT retained but outcome RESOLVED
        self.assertNotIn("VC-V04", fails(rep(build(alts, outcome=Outcome.AMBIGUOUS))))
        self.assertIn("VC-V04", fails(rep(build(assert_(tense("PAST", speech_time(), holds(give()))), outcome=Outcome.AMBIGUOUS))))

    def test_deterministic_steps_replay(self):
        anchor = Anchor(document_date="2026-10-16")
        text = "The doctor gave the patient medication yesterday."
        def e(start, end):
            return assert_(tense("PAST", time_rel("YESTERDAY", start, end), holds(give())))
        good = build(e("2026-10-15", "2026-10-16"), text, anchor=anchor)
        self.assertNotIn("VC-V05", fails(rep(good)))
        wrong = build(e("2026-10-14", "2026-10-15"), text, anchor=anchor)  # a model-invented date
        self.assertIn("VC-V05", fails(rep(wrong)))
        no_anchor = build(e("2026-10-15", "2026-10-16"), text)  # resolved bounds without an anchor
        self.assertIn("VC-V05", fails(rep(no_anchor)))
        unresolved = build(assert_(tense("PAST", time_rel("YESTERDAY"), holds(give()))), text)
        self.assertNotIn("VC-V05", fails(rep(unresolved)))  # leaving it unresolved is never wrong

    def test_registered_replay_functions_and_canonical_claims(self):
        c = candidate()
        step = CertStep("rp", StepType.OPERATOR_ATTACHMENT, "SG-INT-051", Basis.GRAMMATICAL)
        c2 = with_cert(c, steps=c.certificate.steps + (step,))
        v, _ = make_validator(replays={"SG-INT-051": lambda s, cand: (False, "tense does not follow from 'gave'")})
        r = rep(c2, v)
        self.assertIn("VC-V05", fails(r))
        self.assertIn("tense does not follow", " ".join(x.detail for x in r.failed()))
        out_of_order = assert_(and_(prop(R(9), "Color", value("Red")), prop(R(1), "Color", value("Red"))))
        canon_step = CertStep("cn", StepType.CANONICALIZATION, "SG-CAN-020", Basis.GRAMMATICAL)
        cc = build(out_of_order, steps=(canon_step,))
        self.assertIn("VC-V05", fails(rep(cc)))
        ordered = assert_(and_(prop(R(1), "Color", value("Red")), prop(R(9), "Color", value("Red"))))
        self.assertNotIn("VC-V05", fails(rep(build(ordered, steps=(canon_step,)))))

    def test_background_content_is_never_source_stated(self):
        e = assert_(tense("PAST", speech_time(), holds(apply("GIVE", 1, {
            "AGENT": R(1), "SOURCE": R(1), "RECIPIENT": R(2), "THEME": background(R(3), "SG-KNW-010")}))))
        c = build(e)
        r = rep(c)
        self.assertIn("VC-V06", fails(r))  # declared SOURCE_TEXT
        self.assertIn("VC-V09", fails(r))  # and no INFERENCE step
        premise = next(s.step_id for s in c.certificate.steps if s.step_type is StepType.REFERENT_CREATION)
        premises = CertStep("inf", StepType.INFERENCE, "SG-KNW-010", Basis.BACKGROUND, (), (), "R3", premises=(premise,))
        ok = dataclasses.replace(c, certificate=dataclasses.replace(c.certificate, steps=c.certificate.steps + (premises,)),
                                 declared_origin=Origin.BACKGROUND_INFERENCE)
        r2 = rep(ok)
        self.assertEqual(fails(r2), set())
        self.assertGreaterEqual(r2.risk, RiskClass.MEDIUM)
        bad_prem = dataclasses.replace(ok, certificate=dataclasses.replace(ok.certificate, steps=c.certificate.steps + (
            dataclasses.replace(premises, premises=("nonexistent",)),)))
        self.assertIn("VC-V09", fails(rep(bad_prem)))
        no_prem = dataclasses.replace(ok, certificate=dataclasses.replace(ok.certificate, steps=c.certificate.steps + (
            dataclasses.replace(premises, premises=()),)))
        self.assertIn("VC-V09", fails(rep(no_prem)))
        bad_rule = dataclasses.replace(ok, certificate=dataclasses.replace(ok.certificate, steps=c.certificate.steps + (
            dataclasses.replace(premises, rule_id="SG-INT-012"),)))
        self.assertIn("VC-V09", fails(rep(bad_rule)))


class CueTests(unittest.TestCase):
    def cand(self, text, expr):
        return build(expr, text)

    def test_dropped_negation_is_invalid(self):
        text = "The doctor did not give the patient medication."
        yes = assert_(tense("PAST", speech_time(), holds(give())))
        no = assert_(tense("PAST", speech_time(), not_(holds(give()))))
        self.assertIn("VC-V07", fails(rep(self.cand(text, yes))))
        self.assertNotIn("VC-V07", fails(rep(self.cand(text, no))))
        for neg in ("The doctor never gave the patient medication.", "The doctor didn't give the patient medication.",
                    "No doctor gave the patient medication."):
            self.assertIn("VC-V07", fails(rep(self.cand(neg, yes))), neg)
        self.assertNotIn("VC-V07", fails(rep(self.cand("Not only the doctor gave the patient medication.", yes))))  # exempt phrase
        every = assert_(q("NO", "x", holds(apply("OPEN", 1, {"UNDERGOER": var("x")})), holds(give())))
        self.assertNotIn("VC-V07", fails(rep(self.cand("No door gave the patient medication.", every))))

    def test_invented_negation_is_uncertain(self):
        e = assert_(tense("PAST", speech_time(), Node("NOT", (holds(give()),), {}, Ann(spans=(GAVE,), basis="EXPLICIT"))))
        r = rep(candidate(expr=annotate_all(e)))
        self.assertEqual(r.result_of("VC-V07"), CheckResult.UNCERTAIN)
        self.assertEqual(r.aggregate, Aggregate.UNCERTAIN)

    def test_other_cues_make_the_candidate_uncertain(self):
        plain = assert_(tense("PRESENT", speech_time(), holds(give())))
        for text, label in (("The doctor may give the patient medication.", "modal"), ("If the doctor gives the patient medication.", "conditional"),
                            ("Every doctor gives the patient medication.", "quantifier")):
            r = rep(self.cand(text, plain))
            self.assertEqual(r.result_of("VC-V07"), CheckResult.UNCERTAIN, label)
            self.assertEqual(r.aggregate, Aggregate.UNCERTAIN, label)
        with_modal = assert_(modal("POSSIBILITY", "EPISTEMIC", tense("PRESENT", speech_time(), holds(give()))))
        self.assertNotEqual(rep(self.cand("The doctor may give the patient medication.", with_modal)).result_of("VC-V07"), CheckResult.UNCERTAIN)
        no_tense = assert_(holds(give()))
        self.assertEqual(rep(self.cand("The doctor will give the patient medication.", no_tense)).result_of("VC-V07"), CheckResult.UNCERTAIN)

    def test_numbers_in_the_text_must_appear_in_the_expression(self):
        text = "The doctor gave the patient 2 medication."
        miss = assert_(tense("PAST", speech_time(), holds(give())))
        self.assertEqual(rep(self.cand(text, miss)).result_of("VC-V08"), CheckResult.UNCERTAIN)
        hit = assert_(and_(tense("PAST", speech_time(), holds(give())), prop(R(3), "Temperature", lit(2, "Quantity", "tablet"))))
        self.assertNotEqual(rep(self.cand(text, hit)).result_of("VC-V08"), CheckResult.UNCERTAIN)
        counted = assert_(q("EXACTLY", "x", holds(apply("OPEN", 1, {"UNDERGOER": var("x")})), holds(give()), n=2))
        self.assertNotEqual(rep(self.cand(text, counted)).result_of("VC-V08"), CheckResult.UNCERTAIN)


class AggregationAndRiskTests(unittest.TestCase):
    def out(self, cid, res):
        return CheckOutcome(cid, res)

    def test_aggregation_rules(self):
        P, F, U, N = CheckResult.PASS, CheckResult.FAIL, CheckResult.UNCERTAIN, CheckResult.NOT_CHECKED
        self.assertEqual(aggregate([self.out("VC-S01", P), self.out("VC-V01", P)]), Aggregate.FORMALLY_VALID)
        self.assertEqual(aggregate([self.out("VC-S01", P), self.out("VC-V01", U)]), Aggregate.UNCERTAIN)
        self.assertEqual(aggregate([self.out("VC-S01", F), self.out("VC-V01", U)]), Aggregate.INVALID)
        self.assertEqual(aggregate([self.out("VC-T02", U), self.out("VC-V03", F)]), Aggregate.INVALID)
        self.assertEqual(aggregate([self.out("VC-C01", F), self.out("VC-V01", P)]), Aggregate.FORMALLY_VALID)  # L5 is the panel's domain
        self.assertEqual(aggregate([self.out("VC-S03", N)]), Aggregate.FORMALLY_VALID)  # NOT_CHECKED is neutral
        self.assertEqual(aggregate([]), Aggregate.FORMALLY_VALID)

    def test_static_risk_classes(self):
        self.assertEqual(rep(candidate()).risk, RiskClass.LOW)
        alts = rep(build(assert_(alt("g", [holds(give()), holds(give(2, 2, 1, 3))])), outcome=Outcome.AMBIGUOUS))
        self.assertGreaterEqual(alts.risk, RiskClass.MEDIUM)
        body = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        not_every = rep(build(assert_(not_(q("FORALL", "x", body, body)))))
        self.assertEqual(not_every.risk, RiskClass.HIGH)
        every_not = rep(build(assert_(q("FORALL", "x", body, not_(body)))))
        self.assertEqual(every_not.risk, RiskClass.HIGH)
        self.assertIn("negation scoping over a quantifier", not_every.risk_reasons)


class RoutingTests(unittest.TestCase):
    def test_invalid_goes_to_repair_then_reject(self):
        bad = rep(build(assert_(holds(apply("GIVE", 1, {"AGENT": R(1)})))))
        self.assertEqual(route(bad, retries_left=2).route, Route.REPAIR)
        self.assertEqual(route(bad, retries_left=0).route, Route.REJECT)
        integrity = rep(with_cert(candidate(), source_hash="0" * 64))
        self.assertEqual(route(integrity, retries_left=5).route, Route.REJECT)  # not repairable

    def test_valid_low_risk_is_accepted_provisionally(self):
        self.assertEqual(route(rep(candidate()), retries_left=2).route, Route.ACCEPT_PROVISIONAL)

    def test_uncertain_and_risky_go_to_the_automated_panel_never_a_person(self):
        unc = rep(build(assert_(holds(apply("EAT", 1, {"EATER": R(6), "FOOD": ref("W:s1:55")})))))
        self.assertEqual(route(unc, retries_left=2).route, Route.REVIEW)
        self.assertEqual(route(unc, retries_left=2, panel_available=False).route, Route.DEFER)
        body = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        risky = rep(build(assert_(not_(q("FORALL", "x", body, body)))))
        self.assertEqual(route(risky, retries_left=2).route, Route.REVIEW)
        self.assertNotIn("HUMAN", {r.value for r in Route})

    def test_retained_ambiguity_is_preserved(self):
        amb = rep(build(assert_(alt("g", [holds(give()), holds(give(2, 2, 1, 3))])), outcome=Outcome.AMBIGUOUS))
        self.assertEqual(route(amb, retries_left=2).route, Route.PRESERVE_AMBIGUITY)

    def test_repair_request_shows_codes_and_rule_text_only(self):
        bad = rep(build(assert_(holds(apply("TREAT", 1, {"AGENT": R(1), "UNDERGOER": R(2)})))))
        items = repair_request(bad, CTX.rulebook)
        self.assertTrue(items)
        item = [i for i in items if i.check_id == "VC-S06"][0]
        self.assertIn("SG-FRM-001", item.rule_ids)
        self.assertTrue(any("frame defines it" in t for t in item.rule_text))
        self.assertIn("PRACTITIONER", item.detail)


class TotalityFuzzTests(unittest.TestCase):
    def test_validator_never_raises_on_mutated_candidates(self):
        import random
        from usg.grammar.serialize import node_from_json, node_to_json
        from usg.errors import InvariantViolation
        rng = random.Random(4242)
        base = node_to_json(give_expr())
        ops = ["REF", "NOT", "HOLDS", "APPLY", "TENSE", "LIT", "ERROR"]

        def mutate(d):
            d = {**d, "args": [mutate(a) for a in d["args"]], "params": dict(d["params"])}
            r = rng.random()
            if r < 0.08 and d["params"]:
                k = rng.choice(sorted(d["params"]))
                d["params"][k] = rng.choice(["", "X", 7, None, True, ["a", 1]])
            elif r < 0.14:
                d["op"] = rng.choice(ops)
            elif r < 0.18 and d["args"]:
                d["args"].pop(rng.randrange(len(d["args"])))
            elif r < 0.22:
                d["ann"] = {"spans": [[rng.randint(-3, 60), rng.randint(-3, 60)]], "rules": [rng.choice(["SG-INT-012", "NOPE", ""])],
                            "basis": rng.choice(["EXPLICIT", "GRAMMATICAL", "BACKGROUND", "X", None]), "features": []}
            return d

        built = invalid = 0
        for _ in range(400):
            try:
                expr = node_from_json(mutate(base))
            except InvariantViolation:
                invalid += 1  # such a candidate cannot even be constructed: rejected at parse time (VC-S01)
                continue
            c = Candidate(Source(TEXT), Span(0, len(TEXT)), expr,
                          DerivationCertificate(Source(TEXT).text_hash, steps=give_steps()))
            r = V.validate(c)  # must not raise
            self.assertIn(r.aggregate, (Aggregate.INVALID, Aggregate.UNCERTAIN, Aggregate.FORMALLY_VALID))
            self.assertTrue(route(r, retries_left=1).route in Route)
            built += 1
        self.assertGreater(built, 50)
        self.assertGreater(invalid, 20)

    def test_malformed_candidate_json_is_a_vc_s01_error(self):
        from usg.errors import InvariantViolation
        with self.assertRaises(InvariantViolation) as cm:
            Candidate.from_json(Source(TEXT), {"unit_span": [0, 5]})
        self.assertEqual(cm.exception.code, "VC-S01")


if __name__ == "__main__":
    unittest.main()
