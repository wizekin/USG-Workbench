import unittest

from usg.core.ids import IdSpace, Ref, WHandle
from usg.core.kinds import DEFINITION_KINDS, KIND_TO_SORT, SemKind, can_fill_role
from usg.core.records import (Anchor, Assertion, ContentType, Filler, FrameInstance, IntroducedIn, LanguageAnnotation,
                              Literal, Referent, RoleBinding, Source)
from usg.core.roles import TIER1_ROLES, RoleSpec, Requiredness, tier1, tier2
from usg.core.spans import Span
from usg.core.values import (Basis, CommitmentKind, Component, EpistemicStatus, EvalContextKind, FillerKind,
                             IntroducedInKind, Lifecycle, Number, Origin, ReferentScope, RiskClass, ValueState,
                             check_epistemic_transition, check_lifecycle_transition, eligible_for_trusted_view)
from usg.errors import InvariantViolation


def R(space, n=1):
    return Ref(space, n)


class IdTests(unittest.TestCase):
    def test_ref_format_parse(self):
        r = Ref(IdSpace.CONCEPT, 12)
        self.assertEqual(str(r), "CONCEPT:12")
        self.assertEqual(Ref.parse("CONCEPT:12"), r)
        self.assertEqual(str(Ref(IdSpace.PROVISIONAL, 5)), "P:5")
        self.assertTrue(Ref.parse("P:5").is_provisional)

    def test_zero_and_bad_ids_rejected(self):
        for n in (0, -1):
            with self.assertRaises(InvariantViolation):
                Ref(IdSpace.CONCEPT, n)
        with self.assertRaises(InvariantViolation):
            Ref.parse("nonsense")
        with self.assertRaises(InvariantViolation):
            Ref.parse("BOGUS:1")
        with self.assertRaises(InvariantViolation):
            Ref(IdSpace.CONCEPT, True)

    def test_workspace_handle_is_not_a_ref(self):
        h = WHandle("t1", 3)
        self.assertEqual(str(h), "W:t1:3")
        self.assertNotIsInstance(h, Ref)


class KindTests(unittest.TestCase):
    def test_fifteen_kinds_and_definition_kinds(self):
        self.assertEqual(len(SemKind), 15)
        self.assertEqual(DEFINITION_KINDS, {SemKind.ROLE, SemKind.RELATION, SemKind.FRAME, SemKind.CONSTRAINT})
        self.assertFalse(can_fill_role(SemKind.FRAME))
        self.assertTrue(can_fill_role(SemKind.ENTITY))

    def test_sorts(self):
        self.assertEqual(KIND_TO_SORT[SemKind.EVENT].value, "SIT")
        self.assertEqual(KIND_TO_SORT[SemKind.PROPOSITION].value, "PROP")


class LifecycleTests(unittest.TestCase):
    def test_engines_cannot_advance_beyond_discovered(self):
        check_lifecycle_transition(None, Lifecycle.DISCOVERED, Component.LEARNING_ENGINE)
        for to in (Lifecycle.VALIDATED_FORMALLY, Lifecycle.REVIEWED_SEMANTICALLY, Lifecycle.CORROBORATED,
                   Lifecycle.PROMOTED):
            with self.assertRaises(InvariantViolation):
                check_lifecycle_transition(Lifecycle.STRUCTURED, to, Component.LEARNING_ENGINE)

    def test_stage_owners(self):
        check_lifecycle_transition(Lifecycle.DISCOVERED, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        check_lifecycle_transition(Lifecycle.STRUCTURED, Lifecycle.VALIDATED_FORMALLY, Component.VALIDATOR)
        check_lifecycle_transition(Lifecycle.VALIDATED_FORMALLY, Lifecycle.REVIEWED_SEMANTICALLY, Component.AUTOMATED_PANEL)
        check_lifecycle_transition(Lifecycle.REVIEWED_SEMANTICALLY, Lifecycle.CORROBORATED, Component.EVALUATION_PROCESS)
        check_lifecycle_transition(Lifecycle.CORROBORATED, Lifecycle.PROMOTED, Component.PROMOTION_CONTROLLER)
        # LOW-risk path may skip review/corroboration stages
        check_lifecycle_transition(Lifecycle.VALIDATED_FORMALLY, Lifecycle.PROMOTED, Component.PROMOTION_CONTROLLER)

    def test_only_promotion_controller_promotes(self):
        for actor in (Component.VALIDATOR, Component.AUTOMATED_PANEL, Component.CONTROLLER, Component.INTERPRETER,
                      Component.BIG_MODEL_GATEWAY, Component.MODEL_GATEWAY):
            with self.assertRaises(InvariantViolation):
                check_lifecycle_transition(Lifecycle.CORROBORATED, Lifecycle.PROMOTED, actor)

    def test_no_backward_or_terminal_moves(self):
        with self.assertRaises(InvariantViolation):
            check_lifecycle_transition(Lifecycle.VALIDATED_FORMALLY, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        with self.assertRaises(InvariantViolation):
            check_lifecycle_transition(Lifecycle.REJECTED, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        with self.assertRaises(InvariantViolation):
            check_lifecycle_transition(Lifecycle.PROMOTED, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        check_lifecycle_transition(Lifecycle.PROMOTED, Lifecycle.DEPRECATED, Component.PROMOTION_CONTROLLER)
        with self.assertRaises(InvariantViolation):
            check_lifecycle_transition(Lifecycle.STRUCTURED, Lifecycle.DEPRECATED, Component.PROMOTION_CONTROLLER)

    def test_new_record_starts_at_discovered(self):
        with self.assertRaises(InvariantViolation):
            check_lifecycle_transition(None, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)

    def test_deferred_reentry(self):
        check_lifecycle_transition(Lifecycle.STRUCTURED, Lifecycle.DEFERRED, Component.CONTROLLER)
        check_lifecycle_transition(Lifecycle.DEFERRED, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        with self.assertRaises(InvariantViolation):
            check_lifecycle_transition(Lifecycle.DEFERRED, Lifecycle.PROMOTED, Component.PROMOTION_CONTROLLER)


class EpistemicTests(unittest.TestCase):
    E = EpistemicStatus

    def test_creation_statuses(self):
        check_epistemic_transition(None, self.E.SOURCE_ASSERTED, Component.VALIDATOR)
        check_epistemic_transition(None, self.E.INFERRED, Component.RULE_ENGINE)
        with self.assertRaises(InvariantViolation):
            check_epistemic_transition(None, self.E.SOURCE_ASSERTED, Component.INTERPRETER)
        with self.assertRaises(InvariantViolation):
            check_epistemic_transition(None, self.E.VERIFIED, Component.EVALUATION_PROCESS)

    def test_inference_never_becomes_source_stated(self):
        with self.assertRaises(InvariantViolation) as cm:
            check_epistemic_transition(self.E.INFERRED, self.E.SOURCE_ASSERTED, Component.EVALUATION_PROCESS)
        self.assertEqual(cm.exception.code, "SG-EVD-003")

    def test_verified_only_by_evaluation(self):
        for actor in (Component.LEARNING_ENGINE, Component.GENERALIZATION_ENGINE, Component.INTERPRETER,
                      Component.PROMOTION_CONTROLLER, Component.AUTOMATED_PANEL, Component.MODEL_GATEWAY):
            with self.assertRaises(InvariantViolation) as cm:
                check_epistemic_transition(self.E.SOURCE_ASSERTED, self.E.VERIFIED, actor)
            self.assertEqual(cm.exception.code, "SG-EVD-009")
        check_epistemic_transition(self.E.SOURCE_ASSERTED, self.E.VERIFIED, Component.EVALUATION_PROCESS)
        check_epistemic_transition(self.E.INFERRED, self.E.VERIFIED, Component.EVALUATION_PROCESS)
        check_epistemic_transition(self.E.VERIFIED, self.E.DISPUTED, Component.EVALUATION_PROCESS)

    def test_trusted_view(self):
        ok = eligible_for_trusted_view(self.E.VERIFIED, CommitmentKind.AUTHOR, EvalContextKind.WORLD)
        self.assertTrue(ok)
        self.assertFalse(eligible_for_trusted_view(self.E.SOURCE_ASSERTED, CommitmentKind.AUTHOR, EvalContextKind.WORLD))
        self.assertFalse(eligible_for_trusted_view(self.E.VERIFIED, CommitmentKind.ATTRIBUTED, EvalContextKind.WORLD))
        self.assertFalse(eligible_for_trusted_view(self.E.VERIFIED, CommitmentKind.AUTHOR, EvalContextKind.FICTION))
        self.assertTrue(eligible_for_trusted_view(self.E.VERIFIED, CommitmentKind.AUTHOR, EvalContextKind.DOMAIN_MODEL))

    def test_risk_class_raise_caps(self):
        self.assertEqual(RiskClass.LOW.raised(), RiskClass.MEDIUM)
        self.assertEqual(RiskClass.HIGH.raised(5), RiskClass.VERY_HIGH)
        self.assertLess(RiskClass.LOW, RiskClass.HIGH)


class RoleTests(unittest.TestCase):
    def test_tier1_catalogue(self):
        self.assertEqual(len(TIER1_ROLES), 19)
        self.assertIn("UNDERGOER", TIER1_ROLES)
        self.assertNotIn("PATIENT", TIER1_ROLES)  # avoids clash with the concept Patient

    def test_tier2_needs_tier1_parent(self):
        r = tier2("EXAMINER", "AGENT", required=True)
        self.assertEqual(r.tier1_parent, "AGENT")
        self.assertEqual(r.display, "role:EXAMINER")
        self.assertEqual(r.requiredness, Requiredness.REQUIRED)
        self.assertEqual(r.card_min, 1)
        with self.assertRaises(InvariantViolation):
            RoleSpec("EXAMINER", 2, None)
        with self.assertRaises(InvariantViolation):
            RoleSpec("EXAMINER", 2, "NOT_A_ROLE")
        with self.assertRaises(InvariantViolation):
            RoleSpec("AGENT", 2, "AGENT")  # tier-2 name collides with tier-1 name
        with self.assertRaises(InvariantViolation):
            RoleSpec("MADE_UP", 1, None)
        self.assertEqual(tier1("AGENT").tier1_parent, "AGENT")

    def test_cardinality(self):
        with self.assertRaises(InvariantViolation):
            RoleSpec("X", 2, "AGENT", card_min=2, card_max=1)


class RecordTests(unittest.TestCase):
    def test_source_hash_and_spans(self):
        s = Source("The doctor gave the patient medication.", anchor=Anchor(document_date="2026-10-16"))
        self.assertEqual(len(s.text_hash), 64)
        self.assertEqual(s.span_text(Span(4, 10)), "doctor")
        self.assertFalse(s.remote_shareable)
        with self.assertRaises(InvariantViolation):
            Source("")
        with self.assertRaises(InvariantViolation):
            Source("abc", text_hash="deadbeef")
        with self.assertRaises(InvariantViolation):
            s.span_text(Span(0, 999))

    def test_span_validation(self):
        for a, b in ((-1, 3), (3, 3), (5, 2)):
            with self.assertRaises(InvariantViolation):
                Span(a, b)
        self.assertTrue(Span(0, 5).overlaps(Span(4, 8)))
        self.assertTrue(Span(0, 8).contains(Span(2, 4)))

    def test_filler_never_bare_concept(self):
        with self.assertRaises(InvariantViolation):
            Filler(FillerKind.REFERENT, ref=R(IdSpace.CONCEPT))
        with self.assertRaises(InvariantViolation):
            Filler(FillerKind.INSTANCE, ref=R(IdSpace.REFERENT))
        Filler.referent(R(IdSpace.REFERENT))
        Filler.kind_ref(R(IdSpace.CONCEPT))
        Filler.lit("2", "Integer")
        with self.assertRaises(InvariantViolation):
            Literal(1.5, "Decimal")  # canonical literals avoid binary floats

    def test_binding_rules(self):
        f = Filler.referent(R(IdSpace.REFERENT))
        RoleBinding("AGENT", ValueState.SPECIFIED, Basis.EXPLICIT, f, span=Span(0, 3))
        RoleBinding("AGENT", ValueState.SPECIFIED, Basis.GRAMMATICAL, f, rule="SG-INT-010")
        with self.assertRaises(InvariantViolation):  # explicit needs span
            RoleBinding("AGENT", ValueState.SPECIFIED, Basis.EXPLICIT, f)
        with self.assertRaises(InvariantViolation):  # grammatical needs rule
            RoleBinding("AGENT", ValueState.SPECIFIED, Basis.GRAMMATICAL, f)
        with self.assertRaises(InvariantViolation):  # background needs a rule
            RoleBinding("AGENT", ValueState.SPECIFIED, Basis.BACKGROUND, f)
        with self.assertRaises(InvariantViolation):  # specified needs filler
            RoleBinding("AGENT", ValueState.SPECIFIED, Basis.EXPLICIT, None, span=Span(0, 3))
        # hole states never carry content: nothing may be invented
        RoleBinding("EXAMINER", ValueState.UNSPECIFIED)
        for st in (ValueState.UNSPECIFIED, ValueState.UNKNOWN, ValueState.NOT_APPLICABLE, ValueState.WITHHELD):
            with self.assertRaises(InvariantViolation):
                RoleBinding("EXAMINER", st, filler=f)
            with self.assertRaises(InvariantViolation):
                RoleBinding("EXAMINER", st, basis=Basis.BACKGROUND, rule="x")

    def test_frame_instance_duplicates(self):
        b1 = RoleBinding("AGENT", ValueState.UNSPECIFIED)
        b2 = RoleBinding("AGENT", ValueState.UNKNOWN)
        with self.assertRaises(InvariantViolation):
            FrameInstance(R(IdSpace.FRAME), 1, (b1, b2))
        fi = FrameInstance(R(IdSpace.FRAME), 1, (b1, RoleBinding("AGENT", ValueState.UNKNOWN, ord=1)))
        self.assertIsNotNone(fi.binding("AGENT", 1))
        with self.assertRaises(InvariantViolation):
            FrameInstance(R(IdSpace.CONCEPT), 1, ())  # frame ref must be a frame

    def test_referent_rules(self):
        Referent(SemKind.ENTITY, (R(IdSpace.CONCEPT),), Number.PLURAL, cardinality=2)
        with self.assertRaises(InvariantViolation):
            Referent(SemKind.FRAME)  # definition kinds cannot be referents
        with self.assertRaises(InvariantViolation):
            Referent(SemKind.ENTITY, scope=ReferentScope.RESOLVED_INDIVIDUAL)
        with self.assertRaises(InvariantViolation):
            Referent(SemKind.ENTITY, number=Number.MASS, cardinality=3)
        with self.assertRaises(InvariantViolation):
            Referent(SemKind.ENTITY, (R(IdSpace.REFERENT),))
        with self.assertRaises(InvariantViolation):
            Referent(SemKind.ENTITY, cardinality=(3, 1))

    def test_introduced_in_needs_context_ref(self):
        IntroducedIn()
        IntroducedIn(IntroducedInKind.CONTENT_OF, R(IdSpace.INSTANCE))
        with self.assertRaises(InvariantViolation):
            IntroducedIn(IntroducedInKind.NEGATED)

    def test_assertion_invariants(self):
        src = R(IdSpace.SOURCE)
        a = Assertion.new(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.SOURCE_TEXT, source=src)
        self.assertEqual(a.epistemic_status, EpistemicStatus.SOURCE_ASSERTED)
        inf = Assertion.new(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.BACKGROUND_INFERENCE, source=src)
        self.assertEqual(inf.epistemic_status, EpistemicStatus.INFERRED)
        with self.assertRaises(InvariantViolation):  # I-08
            Assertion.new(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.SOURCE_TEXT)
        Assertion.new(ContentType.EDGE, R(IdSpace.INSTANCE), Origin.CURATED)  # authorized origin ok
        with self.assertRaises(InvariantViolation):  # inference cannot be SOURCE_ASSERTED
            Assertion(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.BACKGROUND_INFERENCE,
                      EpistemicStatus.SOURCE_ASSERTED, source=src)
        with self.assertRaises(InvariantViolation):
            Assertion(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.SOURCE_TEXT, EpistemicStatus.INFERRED, source=src)
        with self.assertRaises(InvariantViolation):  # attributed needs the committing referent
            Assertion.new(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.SOURCE_TEXT, source=src,
                          commitment=CommitmentKind.ATTRIBUTED)
        with self.assertRaises(InvariantViolation):  # validated stage needs evidence
            Assertion.new(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.SOURCE_TEXT, source=src,
                          lifecycle=Lifecycle.VALIDATED_FORMALLY)

    def test_assertion_status_changes_go_through_rules(self):
        a = Assertion.new(ContentType.INSTANCE, R(IdSpace.INSTANCE), Origin.SOURCE_TEXT, source=R(IdSpace.SOURCE))
        with self.assertRaises(InvariantViolation):
            a.with_status(EpistemicStatus.VERIFIED, Component.INTERPRETER)
        v = a.with_status(EpistemicStatus.VERIFIED, Component.EVALUATION_PROCESS)
        self.assertEqual(v.epistemic_status, EpistemicStatus.VERIFIED)
        with self.assertRaises(InvariantViolation):
            a.with_stage(Lifecycle.PROMOTED, Component.LEARNING_ENGINE)
        b = a.with_stage(Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        self.assertEqual(b.lifecycle, Lifecycle.STRUCTURED)

    def test_language_annotation_boundary(self):
        LanguageAnnotation("en", (("voice", "passive"), ("definiteness", "definite")))
        for feat in ("tense", "modality", "negation", "evidentiality"):
            with self.assertRaises(InvariantViolation):
                LanguageAnnotation("en", ((feat, "x"),))


if __name__ == "__main__":
    unittest.main()
