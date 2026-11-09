import unittest

from usg.config import Config
from usg.foundation.builder import build_foundation
from usg.grammar.canon import canonicalize
from usg.grammar.node import (Node, alt, and_, apply, assert_, attribute, compose, different_from, error, extent, fig, hole, holds,
                              kind, lit, modal, not_, or_, prop, q, ref, relate, same_as, speech_time, temporal, tense,
                              time_lit, value, var)
from usg.grammar.typecheck import Typechecker

FND = build_foundation()
LIB = FND.frames
CLASSES = {
    "REFERENT:1": ["Doctor"], "REFERENT:2": ["Patient"], "REFERENT:3": ["Medication"], "REFERENT:4": ["Pump"],
    "REFERENT:5": ["Apple"], "REFERENT:6": ["Argument"], "REFERENT:7": ["Person"], "REFERENT:8": ["Tablet"],
    "REFERENT:9": ["Car"], "REFERENT:10": ["Hospital"],
}
TC = Typechecker(LIB, FND.relations, classes_of=lambda r: CLASSES.get(r, ()), mappings={"M_TAKE_IN"})
R = lambda n: ref(f"REFERENT:{n}")


def give(a=1, s=1, r=2, t=3, **extra):
    return apply("GIVE", 1, {"AGENT": R(a), "SOURCE": R(s), "RECIPIENT": R(r), "THEME": R(t), **extra})


def codes(n, **kw):
    return TC.check(n, **kw).codes()


class FrameApplicationTests(unittest.TestCase):
    def test_well_formed_assertion(self):
        e = assert_(tense("PAST", speech_time(), give()), origin="SOURCE_TEXT")
        rep = TC.check(e)
        self.assertTrue(rep.ok, rep.codes())
        self.assertEqual(rep.warnings, [])  # every class constraint is derivable

    def test_required_roles_must_be_bound_or_explicit_holes(self):
        no_theme = apply("GIVE", 1, {"AGENT": R(1), "SOURCE": R(1), "RECIPIENT": R(2)})
        self.assertEqual(codes(holds(no_theme)), ["VC-S07"])
        agentless = apply("GIVE", 1, {"AGENT": hole(), "SOURCE": hole(), "RECIPIENT": R(2), "THEME": R(3)})
        self.assertEqual(codes(holds(agentless)), [])  # the agentless passive: nothing invented

    def test_closed_role_list_and_tier1_hint(self):
        bad = apply("TREAT", 1, {"AGENT": R(1), "UNDERGOER": R(2)})
        rep = TC.check(holds(bad))
        self.assertEqual(rep.codes().count("VC-S06"), 2)
        self.assertTrue(any("PRACTITIONER" in i.message for i in rep.issues))

    def test_abstract_unknown_and_version_mismatch(self):
        self.assertEqual(codes(holds(apply("TRANSFER", 1, {"SOURCE": R(1), "RECIPIENT": R(2), "THEME": R(3)}))), ["VC-S05"])
        self.assertEqual(codes(holds(apply("NO_SUCH_FRAME", 1, {}))), ["VC-S05"])
        self.assertEqual(codes(holds(apply("GIVE", 7, {"AGENT": R(1), "SOURCE": R(1), "RECIPIENT": R(2), "THEME": R(3)}))), ["I-12"])

    def test_parameters_are_never_set_by_instances(self):
        n = apply("SEE", 1, {"EXPERIENCER": R(1), "STIMULUS": R(2), "MODALITY": lit("HEARING")})
        self.assertIn("SG-FRM-002", codes(holds(n)))

    def test_disjoint_roles_cannot_share_a_referent(self):
        n = apply("COMMERCIAL_TRANSACTION", 1, {"BUYER": R(1), "SELLER": R(1), "GOODS": R(9)})
        self.assertEqual(codes(holds(n)), ["VC-T06"])

    def test_filler_sorts_must_match_the_role_kind(self):
        eats_a_proposition = apply("EAT", 1, {"EATER": R(1), "FOOD": holds(give())})
        rep = TC.check(holds(eats_a_proposition))
        self.assertEqual(rep.codes(), ["SG-CON-006"])
        self.assertIn("TERM", rep.issues[0].message)
        wrong_time = apply("MOVE", 1, {"MOVER": R(1), "TIME": R(2)})  # TIME expects a TIME node
        self.assertEqual(codes(holds(wrong_time)), ["SG-CON-006"])
        self.assertEqual(codes(holds(apply("MOVE", 1, {"MOVER": R(1), "TIME": time_lit("INSTANT", "2026-10-15")}))), [])

    def test_attitude_contents_have_the_right_sorts(self):
        eat = apply("EAT", 1, {"EATER": R(7), "FOOD": R(5)})
        # WANT's content is an unasserted SITUATION; the same referent is shared by both frames (reentrancy)
        want = apply("WANT", 1, {"EXPERIENCER": R(7), "CONTENT": eat})
        self.assertEqual(codes(holds(want)), [])
        self.assertEqual(codes(holds(apply("WANT", 1, {"EXPERIENCER": R(7), "CONTENT": holds(eat)}))), ["SG-CON-006"])
        # BELIEVE's content is a PROPOSITION
        self.assertEqual(codes(holds(apply("BELIEVE", 1, {"EXPERIENCER": R(7), "CONTENT": holds(eat)}))), [])
        self.assertEqual(codes(holds(apply("BELIEVE", 1, {"EXPERIENCER": R(7), "CONTENT": eat}))), ["SG-CON-006"])


class ExactSemanticKindTests(unittest.TestCase):
    def test_event_state_and_process_are_not_interchangeable_within_sit(self):
        eat = apply("EAT", 1, {"EATER": R(7), "FOOD": R(5)})  # EVENT
        allergic = apply("ALLERGIC", 1, {"EXPERIENCER": R(2), "STIMULUS": R(3)})  # STATE
        work = apply("WORK", 1, {"WORKER": R(7)})  # PROCESS

        want_event = holds(apply("WANT", 1, {"EXPERIENCER": R(7), "CONTENT": eat}))
        want_state = holds(apply("WANT", 1, {"EXPERIENCER": R(7), "CONTENT": allergic}))
        attempt_process = holds(apply("ATTEMPT", 1, {"AGENT": R(7), "CONTENT": work}))
        composed_process = compose("SEQUENCE", eat, eat)
        attempt_composed_process = holds(apply("ATTEMPT", 1, {
            "AGENT": R(7), "CONTENT": composed_process
        }))
        transform_with_process = holds(apply("PHYSICAL_TRANSFORMATION", 1, {
            "INPUT": R(5), "OUTPUT": R(5), "PROCESS": composed_process
        }))

        self.assertEqual(codes(want_event), [])
        self.assertEqual(codes(want_state), ["SG-TYP-001"])
        self.assertEqual(codes(attempt_process), ["SG-TYP-001"])
        self.assertEqual(codes(attempt_composed_process), ["SG-TYP-001"])
        self.assertEqual(codes(transform_with_process), [])

    def test_system_situation_kind_is_not_guessed_as_process(self):
        system = apply("COMPOSITE_STRUCTURE", 1, {"WHOLE": R(5), "PART": R(3)})
        nested = holds(apply("PHYSICAL_TRANSFORMATION", 1, {
            "INPUT": R(5), "OUTPUT": R(5), "PROCESS": system
        }))

        report = TC.check(nested)
        self.assertTrue(report.ok, report.codes())
        self.assertEqual([w.code for w in report.warnings], ["W-TYPE-UNDETERMINED"])
        self.assertIn("semantic kind cannot be established", report.warnings[0].message)

    def test_value_and_quantity_are_not_interchangeable_within_val(self):
        proper_value = holds(apply("MOVE", 1, {"MOVER": R(1), "MANNER": value("Red")}))
        quantity_in_value_role = holds(apply("MOVE", 1, {
            "MOVER": R(1), "MANNER": lit(37, "Quantity", "celsius")
        }))

        self.assertEqual(codes(proper_value), [])
        self.assertEqual(codes(quantity_in_value_role), ["SG-TYP-001"])

    def test_unmapped_property_kind_is_checked(self):
        valid = holds(apply("COMPARE", 1, {"ITEMS": [R(1), R(2)], "CRITERION": kind("Color")}))
        wrong = holds(apply("COMPARE", 1, {"ITEMS": [R(1), R(2)], "CRITERION": kind("Red")}))

        self.assertEqual(codes(valid), [])
        self.assertEqual(codes(wrong), ["SG-TYP-001"])

    def test_every_alt_branch_must_match_the_role_kind(self):
        event = apply("EAT", 1, {"EATER": R(7), "FOOD": R(5)})
        state = apply("ALLERGIC", 1, {"EXPERIENCER": R(2), "STIMULUS": R(3)})
        mixed = holds(apply("WANT", 1, {
            "EXPERIENCER": R(7), "CONTENT": alt("event-or-state", [event, state])
        }))

        self.assertEqual(codes(mixed), ["SG-TYP-001"])

    def test_kind_mismatch_inside_fig_literal_is_recorded_as_figurative(self):
        state = apply("ALLERGIC", 1, {"EXPERIENCER": R(2), "STIMULUS": R(3)})
        event = apply("EAT", 1, {"EATER": R(7), "FOOD": R(5)})
        literal = apply("WANT", 1, {"EXPERIENCER": R(7), "CONTENT": state})
        intended = apply("WANT", 1, {"EXPERIENCER": R(7), "CONTENT": event})

        report = TC.check(fig("M_TAKE_IN", literal, intended))
        self.assertTrue(report.ok, report.codes())
        self.assertEqual([w.code for w in report.warnings], ["W-FIGURATIVE"])


class ThreeValuedTypingTests(unittest.TestCase):
    def test_incompatible_class_is_rejected(self):
        eat = apply("EAT", 1, {"EATER": R(4), "FOOD": R(5)})  # a pump eats an apple
        rep = TC.check(holds(eat))
        self.assertEqual(rep.codes(), ["SG-TYP-001"])
        self.assertIn("FIG", rep.issues[0].message)
        bought = apply("COMMERCIAL_TRANSACTION", 1, {"BUYER": R(7), "SELLER": R(1), "GOODS": R(6)})  # "bought the argument"
        self.assertEqual(codes(holds(bought)), ["SG-TYP-001"])

    def test_compatible_and_undetermined(self):
        ok = apply("EAT", 1, {"EATER": R(7), "FOOD": R(5)})
        self.assertEqual(TC.check(holds(ok)).warnings, [])
        tablet = apply("EAT", 1, {"EATER": R(7), "FOOD": R(8)})  # Tablet: neither derivable nor refutable
        rep = TC.check(holds(tablet))
        self.assertTrue(rep.ok)
        self.assertEqual([w.code for w in rep.warnings], ["W-TYPE-UNDETERMINED"])
        unknown = apply("EAT", 1, {"EATER": R(7), "FOOD": R(99)})  # no class information at all: open world
        rep = TC.check(holds(unknown))
        self.assertTrue(rep.ok)
        self.assertEqual([w.code for w in rep.warnings], ["W-TYPE-UNDETERMINED"])

    def test_kind_references_are_checked_by_their_concept(self):
        generic = apply("EAT", 1, {"EATER": kind("Animal"), "FOOD": kind("Apple")})
        self.assertTrue(TC.check(holds(generic)).ok)
        self.assertEqual(codes(holds(apply("EAT", 1, {"EATER": kind("Pump"), "FOOD": kind("Apple")}))), ["SG-TYP-001"])

    def test_multiple_inheritance_hospital_is_a_place_and_an_institution(self):
        self.assertEqual(codes(holds(apply("MOVE", 1, {"MOVER": R(1), "DESTINATION_LOCATION": R(10)}))), [])
        self.assertEqual(codes(holds(apply("WORK", 1, {"WORKER": R(1), "WORKPLACE": R(10), "EMPLOYER": R(10)}))), [])
        self.assertEqual(codes(holds(apply("MOVE", 1, {"MOVER": R(1), "DESTINATION_LOCATION": R(7)}))), ["SG-TYP-001"])  # a person is no place


class FigurativeTests(unittest.TestCase):
    def literal(self):
        return apply("EAT", 1, {"EATER": R(4), "FOOD": R(5)})

    def intended(self):
        return apply("MOVE", 1, {"MOVER": R(5)})

    def test_registered_mapping_documents_the_incompatible_literal(self):
        n = assert_(fig("M_TAKE_IN", self.literal(), self.intended()))
        rep = TC.check(n)
        self.assertTrue(rep.ok, rep.codes())
        self.assertEqual([w.code for w in rep.warnings], ["W-FIGURATIVE"])  # review priority rises

    def test_unregistered_mapping_is_rejected(self):
        n = assert_(fig("M_MADE_UP", self.literal(), self.intended()))
        self.assertEqual(codes(n), ["SG-TYP-002"])

    def test_incompatibility_outside_fig_is_still_an_error(self):
        n = assert_(and_(fig("M_TAKE_IN", self.literal(), self.intended()), holds(self.literal())))
        self.assertEqual(codes(n), ["SG-TYP-001"])


class StructuralRuleTests(unittest.TestCase):
    def test_bare_concept_ids_cannot_be_referents(self):
        bad = holds(apply("OPEN", 1, {"UNDERGOER": ref("CONCEPT:5")}))
        self.assertEqual(codes(bad), ["SG-CON-003"])
        self.assertEqual(codes(holds(apply("OPEN", 1, {"UNDERGOER": kind("Door")}))), [])
        self.assertEqual(codes(holds(apply("OPEN", 1, {"UNDERGOER": kind("Nonexistent")}))), ["I-02"])

    def test_provisional_concepts_only_in_candidates(self):
        n = holds(apply("OPEN", 1, {"UNDERGOER": kind("P:1")}))
        self.assertEqual(codes(n), ["VC-S15"])
        self.assertEqual(codes(n, candidate=True), [])

    def test_error_nodes_only_in_candidates(self):
        n = assert_(and_(holds(give()), error("ROLE_UNKNOWN")))
        self.assertEqual(codes(n), ["SG-CON-008"])
        self.assertTrue(TC.check(n, candidate=True).ok)

    def test_assert_cannot_be_nested(self):
        n = and_(assert_(holds(give())), holds(give()))
        self.assertIn("SG-CON-006", codes(n))

    def test_scope_checks_are_part_of_validation(self):
        free = assert_(holds(apply("OPEN", 1, {"UNDERGOER": var("x")})))
        self.assertEqual(codes(free), ["VC-S12"])
        self.assertTrue(TC.check(free, closed=False).ok)
        body = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        shadow = assert_(q("FORALL", "x", body, q("EXISTS", "x", body, body)))
        self.assertEqual(codes(shadow), ["VC-S13"])

    def test_quantifier_parameters(self):
        body = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        self.assertEqual(codes(assert_(q("EXACTLY", "x", body, body))), ["SG-CON-006"])  # needs n
        self.assertEqual(codes(assert_(q("EXISTS", "x", body, body, n=2))), ["SG-CON-006"])  # takes no n
        self.assertEqual(codes(assert_(q("SOME", "x", body, body))), ["SG-CON-006"])  # unknown quantifier
        self.assertEqual(codes(assert_(q("EXACTLY", "x", body, body, n=2))), [])
        self.assertEqual(codes(assert_(q("GEN", "x", body, body))), [])  # generic: never FORALL

    def test_modal_tense_and_attribute_values(self):
        g = holds(give())
        self.assertEqual(codes(modal("POSSIBILITY", "DEONTIC", g)), [])
        self.assertEqual(codes(modal("MAYBE", "DEONTIC", g)), ["SG-CON-006"])
        self.assertEqual(codes(tense("PLUPERFECT", speech_time(), g)), ["SG-CON-006"])
        self.assertEqual(codes(attribute(R(1), "TRUSTED_BY", g)), ["SG-CON-006"])
        self.assertEqual(codes(attribute(R(1), "REPORT", g)), [])

    def test_within_identity_needs_an_attribution_context(self):
        self.assertEqual(codes(same_as(R(1), R(2), "WITHIN")), ["SG-KNW-003"])
        inside = attribute(R(7), "BELIEF", same_as(R(1), R(2), "WITHIN"))
        self.assertEqual(codes(inside), [])
        self.assertEqual(codes(same_as(R(1), R(2), "RESOLVED_WORLD")), [])

    def test_alt_limits_and_ranks(self):
        opts = [holds(give(i, i, 2, 3)) for i in range(1, 7)]
        self.assertEqual(codes(alt("g", opts[:4])), [])
        self.assertEqual(codes(alt("g", opts[:5])), ["SG-CON-007"])  # budget: 4 alternatives per group
        self.assertEqual(codes(alt("g", opts[:2], ranks=[1, 1])), ["SG-CON-007"])
        self.assertEqual(codes(alt("g", opts[:2], ranks=[0, 1])), ["SG-CON-007"])
        small = Typechecker(LIB, FND.relations, Config({"alt_max_per_group": 2}))
        self.assertEqual(small.check(alt("g", opts[:3])).codes(), ["SG-CON-007"])

    def test_nesting_depth_limit(self):
        n = holds(give())
        for _ in range(15):
            n = not_(n)
        self.assertEqual(codes(assert_(n)), ["VC-S16"])

    def test_relation_and_property_checks(self):
        self.assertEqual(codes(relate("NO_SUCH_RELATION", R(1), R(2))), ["I-02"])
        self.assertEqual(codes(relate("HAS_PART", R(1), R(2))), [])
        self.assertEqual(codes(prop(R(9), "Color", value("Red"))), [])
        self.assertEqual(codes(prop(R(9), "Red", value("Red"))), ["VC-T08"])  # a VALUE used where a PROPERTY is expected
        self.assertEqual(codes(prop(R(9), "Color", value("Young"))), ["VC-T03"])  # outside the property's value domain
        self.assertEqual(codes(prop(R(9), "Color", value("Door"))), ["VC-T08"])  # not a VALUE at all
        self.assertEqual(codes(prop(R(9), "NoSuchProperty", value("Red"))), ["I-02"])
        self.assertEqual(codes(prop(R(9), "Temperature", lit(37, "Quantity"))), ["VC-T03"])  # a measurement needs a unit
        self.assertEqual(codes(prop(R(9), "Temperature", lit(37, "Quantity", "celsius"))), [])

    def test_temporal_checks_are_part_of_validation(self):
        a = time_lit("INTERVAL", "2026-10-01/2026-10-05")
        b = time_lit("INTERVAL", "2026-10-10/2026-10-12")
        self.assertEqual(codes(temporal("BEFORE", a, b)), [])
        self.assertEqual(codes(temporal("AFTER", a, b)), ["VC-G06"])
        self.assertEqual(codes(time_lit("INSTANT", "2026-13-45") and tense("PAST", time_lit("INSTANT", "2026-13-45"), holds(give()))),
                         ["SG-CON-006"])


class WorkedExamplesTests(unittest.TestCase):
    """The worked examples of the specification (Part 3 §3.21)."""

    def test_negated_giving_inside_a_causal_explanation(self):
        # "The doctor did not give the patient medication because the patient was allergic to it."
        allergic = apply("ALLERGIC", 1, {"EXPERIENCER": R(2), "STIMULUS": R(3)})
        no_give = not_(give())
        reading1 = apply("CAUSATION", 1, {"CAUSE": holds(allergic), "EFFECT": no_give,
                                           "CAUSE_TYPE": lit("EXPLANATORY_REASON")})
        reading2 = not_(holds(apply("CAUSATION", 1, {"CAUSE": holds(allergic), "EFFECT": holds(give()),
                                                      "CAUSE_TYPE": lit("EXPLANATORY_REASON")})))
        e = assert_(alt("g3", [holds(reading1), reading2]))
        rep = TC.check(e)
        self.assertTrue(rep.ok, rep.codes())
        # the negated transfer lives inside a proposition: no GIVE event is recorded as having happened
        self.assertEqual(no_give.op, "NOT")
        self.assertEqual(no_give.args[0].op, "HOLDS")

    def test_active_and_passive_share_one_expression(self):
        active = holds(apply("EXAMINATION", 1, {"EXAMINER": R(1), "EXAMINED_ENTITY": R(2)}))
        passive = holds(apply("EXAMINATION", 1, {"EXAMINED_ENTITY": R(2), "EXAMINER": R(1)}))
        self.assertEqual(active, passive)
        agentless = holds(apply("EXAMINATION", 1, {"EXAMINED_ENTITY": R(2), "EXAMINER": hole()}))
        self.assertTrue(TC.check(agentless).ok)  # the examiner is a hole, never invented
        self.assertNotEqual(active, agentless)

    def test_give_versus_offer_stay_distinct(self):
        gave = holds(give())
        offered = holds(apply("OFFER", 1, {"OFFERER": R(1), "OFFEREE": R(2),
                                           "CONTENT": apply("GIVE", 1, {"AGENT": R(1), "SOURCE": R(1), "RECIPIENT": R(2), "THEME": R(3)})}))
        self.assertTrue(TC.check(offered).ok)
        self.assertNotEqual(canonicalize(gave, relations=FND.relations), canonicalize(offered, relations=FND.relations))

    def test_wanting_to_eat_shares_one_referent_across_two_frames(self):
        e = assert_(tense("PRESENT", speech_time(), holds(apply("WANT", 1, {
            "EXPERIENCER": R(7), "CONTENT": apply("EAT", 1, {"EATER": R(7), "FOOD": R(5)})}))))
        self.assertTrue(TC.check(e).ok)

    def test_scope_ambiguity_is_kept_as_alt(self):
        # "John did not eat every apple": NOT>FORALL (default) vs FORALL>NOT, retained only when evidence supports both
        body = holds(apply("EAT", 1, {"EATER": R(7), "FOOD": var("x")}))
        restr = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        a = not_(q("FORALL", "x", restr, body))
        b = q("FORALL", "x", restr, not_(body))
        e = assert_(alt("scope", [a, b]))
        self.assertTrue(TC.check(e).ok, TC.check(e).codes())
        self.assertNotEqual(canonicalize(a), canonicalize(b))


if __name__ == "__main__":
    unittest.main()
