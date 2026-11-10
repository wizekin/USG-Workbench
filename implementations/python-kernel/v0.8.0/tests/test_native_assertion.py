from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from usg_assertion_v08 import (
    MODEL_VERSION, AssertionOrigin, CommitmentKind, EpistemicStatus,
    EvaluationContext, EvaluationContextKind, LifecycleStage,
    NativeAssertionV08, ReferenceSpace, TypedReference, same_assertion,
)


class NativeAssertionV08Tests(unittest.TestCase):
    def ref(self, space, value):
        return TypedReference(space, value)

    def make(self, **changes):
        values = dict(
            external_id="a:1",
            expression_ref=self.ref(ReferenceSpace.EXPRESSION, "x:1"),
            origin=AssertionOrigin.SOURCE_TEXT,
            epistemic_status=EpistemicStatus.SOURCE_ASSERTED,
            commitment=CommitmentKind.AUTHOR,
            evaluation_context=EvaluationContext(EvaluationContextKind.WORLD),
            lifecycle_stage=LifecycleStage.DISCOVERED,
        )
        values.update(changes)
        return NativeAssertionV08(**values)

    def test_version_and_required_claim_fields(self):
        item = self.make()
        self.assertEqual(MODEL_VERSION, "0.8.0")
        self.assertEqual(item.expression_ref.external_id, "x:1")
        self.assertEqual(item.evaluation_context.kind, EvaluationContextKind.WORLD)

    def test_assertion_identity_is_not_expression_identity(self):
        left = self.make(external_id="a:1")
        right = self.make(external_id="a:2")
        self.assertFalse(same_assertion(left, right))
        self.assertTrue(same_assertion(left, replace(right, external_id="a:1")))
        self.assertEqual(left.expression_ref, right.expression_ref)

    def test_all_contract_origin_and_epistemic_values_are_distinct(self):
        origins = list(AssertionOrigin)
        statuses = list(EpistemicStatus)
        self.assertEqual(len(origins), 6)
        self.assertEqual(len(statuses), 5)
        self.assertNotEqual(EpistemicStatus.SOURCE_ASSERTED, EpistemicStatus.VERIFIED)

    def test_commitment_and_attribution_are_independent_fields(self):
        item = self.make(
            commitment=CommitmentKind.ATTRIBUTED,
            attributed_to_ref=self.ref(ReferenceSpace.REFERENT, "r:agent"),
        )
        self.assertEqual(item.commitment, CommitmentKind.ATTRIBUTED)
        self.assertEqual(item.attributed_to_ref.space, ReferenceSpace.REFERENT)

    def test_model_does_not_invent_commitment_implications(self):
        # USG-SEM requires no attribute merely because commitment is ATTRIBUTED.
        item = self.make(commitment=CommitmentKind.ATTRIBUTED)
        self.assertIsNone(item.attributed_to_ref)

    def test_multiple_evidence_references_preserve_order_and_repetition(self):
        refs = (
            self.ref(ReferenceSpace.EVIDENCE, "e:2"),
            self.ref(ReferenceSpace.EVIDENCE, "e:1"),
            self.ref(ReferenceSpace.EVIDENCE, "e:2"),
        )
        item = self.make(evidence_refs=refs)
        self.assertEqual(item.evidence_refs, refs)

    def test_evaluation_context_reference_is_typed_and_optional(self):
        context = EvaluationContext(
            EvaluationContextKind.HYPOTHETICAL,
            self.ref(ReferenceSpace.CONTEXT, "c:1"),
            "supposition",
        )
        item = self.make(evaluation_context=context)
        self.assertEqual(item.evaluation_context.context_ref.external_id, "c:1")
        self.assertIsNone(self.make().evaluation_context.context_ref)

    def test_source_definition_and_alternative_group_are_separate_spaces(self):
        item = self.make(
            source_ref=self.ref(ReferenceSpace.SOURCE, "s:1"),
            definition_ref=self.ref(ReferenceSpace.DEFINITION, "d:1"),
            alternative_group_ref=self.ref(ReferenceSpace.ALTERNATIVE_GROUP, "g:1"),
        )
        self.assertEqual(item.source_ref.space, ReferenceSpace.SOURCE)
        self.assertEqual(item.definition_ref.space, ReferenceSpace.DEFINITION)
        self.assertEqual(item.alternative_group_ref.space, ReferenceSpace.ALTERNATIVE_GROUP)

    def test_lifecycle_values_remain_distinct(self):
        self.assertNotEqual(
            LifecycleStage.FORMALLY_VALIDATED,
            LifecycleStage.AUTOMATICALLY_EVALUATED,
        )
        self.assertNotEqual(LifecycleStage.CORROBORATED, LifecycleStage.PROMOTED)

    def test_wrong_reference_spaces_are_rejected(self):
        with self.assertRaises(ValueError):
            self.make(expression_ref=self.ref(ReferenceSpace.ASSERTION, "a:2"))
        with self.assertRaises(ValueError):
            self.make(source_ref=self.ref(ReferenceSpace.CONTEXT, "c:1"))
        with self.assertRaises(ValueError):
            self.make(attributed_to_ref=self.ref(ReferenceSpace.SOURCE, "s:1"))
        with self.assertRaises(ValueError):
            self.make(evidence_refs=(self.ref(ReferenceSpace.SOURCE, "s:1"),))
        with self.assertRaises(ValueError):
            self.make(alternative_group_ref=self.ref(ReferenceSpace.DEFINITION, "d:1"))

    def test_absent_optional_values_are_not_defaulted_into_references(self):
        item = self.make()
        self.assertIsNone(item.source_ref)
        self.assertIsNone(item.attributed_to_ref)
        self.assertEqual(item.evidence_refs, ())
        self.assertIsNone(item.definition_ref)
        self.assertIsNone(item.alternative_group_ref)

    def test_empty_ids_and_invalid_enums_are_rejected(self):
        with self.assertRaises(ValueError):
            self.make(external_id="")
        with self.assertRaises(TypeError):
            self.make(origin="SOURCE_TEXT")


if __name__ == "__main__":
    unittest.main()
