import unittest

from usg_expression_relation_v11 import (
    MODEL_VERSION, NativeExpressionRelationV11, ReferenceSpace, RelationType,
    TypedReference, VerificationStatus, same_expression_relation,
)


class NativeExpressionRelationV11Tests(unittest.TestCase):
    def setUp(self):
        self.source = TypedReference(ReferenceSpace.EXPRESSION, "x:source")
        self.target = TypedReference(ReferenceSpace.EXPRESSION, "x:target")
        self.evidence = TypedReference(ReferenceSpace.EVIDENCE, "e:1")

    def make_relation(self, **changes):
        values = dict(
            external_id="rel:1",
            relation_type=RelationType.RELATED_TO,
            source_expression_ref=self.source,
            target_expression_ref=self.target,
            verification_status=VerificationStatus.NOT_INDEPENDENTLY_VERIFIED,
        )
        values.update(changes)
        return NativeExpressionRelationV11(**values)

    def test_version(self):
        self.assertEqual(MODEL_VERSION, "1.1.0")

    def test_all_relation_types_are_distinct(self):
        self.assertEqual(len(RelationType), 9)

    def test_all_verification_statuses_are_distinct(self):
        self.assertEqual(len(VerificationStatus), 5)

    def test_identity_is_opaque_record_id(self):
        a = self.make_relation()
        b = self.make_relation(relation_type=RelationType.CAUSE)
        c = self.make_relation(external_id="rel:2")
        self.assertTrue(same_expression_relation(a, b))
        self.assertFalse(same_expression_relation(a, c))

    def test_required_identity(self):
        with self.assertRaises(ValueError):
            self.make_relation(external_id="")

    def test_relation_type_must_be_explicit(self):
        with self.assertRaises(TypeError):
            self.make_relation(relation_type="CAUSE")

    def test_source_and_target_must_be_expression_refs(self):
        self.assertEqual(self.make_relation().source_expression_ref.space, ReferenceSpace.EXPRESSION)
        with self.assertRaises(ValueError):
            self.make_relation(source_expression_ref=self.evidence)
        with self.assertRaises(ValueError):
            self.make_relation(target_expression_ref=self.evidence)

    def test_verification_status_must_be_explicit(self):
        with self.assertRaises(TypeError):
            self.make_relation(verification_status="CORROBORATED")

    def test_evidence_refs_are_typed_and_ordered(self):
        refs = (self.evidence, TypedReference(ReferenceSpace.EVIDENCE, "e:2"), self.evidence)
        self.assertEqual(self.make_relation(evidence_refs=refs).evidence_refs, refs)

    def test_evidence_refs_reject_wrong_space(self):
        with self.assertRaises(ValueError):
            self.make_relation(evidence_refs=(self.source,))

    def test_evidence_refs_require_tuple(self):
        with self.assertRaises(TypeError):
            self.make_relation(evidence_refs=[self.evidence])

    def test_attribution_preserves_nested_data(self):
        value = {"speakerRef": "r:1", "scope": {"kind": "belief", "tags": ["a", "b"]}}
        self.assertEqual(self.make_relation(attribution=value).attribution, value)

    def test_attribution_requires_mapping(self):
        with self.assertRaises(TypeError):
            self.make_relation(attribution=["not", "object"])

    def test_attribution_keys_must_be_strings(self):
        with self.assertRaises(ValueError):
            self.make_relation(attribution={1: "bad"})

    def test_attribution_is_copied_from_input(self):
        value = {"nested": {"items": [1]}}
        relation = self.make_relation(attribution=value)
        value["nested"]["items"].append(2)
        self.assertEqual(relation.attribution, {"nested": {"items": [1]}})

    def test_unknown_verification_is_not_promoted(self):
        item = self.make_relation(verification_status=VerificationStatus.UNKNOWN)
        self.assertEqual(item.verification_status, VerificationStatus.UNKNOWN)

    def test_relation_does_not_infer_symmetric_inverse_or_transitive_links(self):
        item = self.make_relation(relation_type=RelationType.CAUSE)
        self.assertEqual(item.source_expression_ref, self.source)
        self.assertEqual(item.target_expression_ref, self.target)

    def test_reference_ids_are_opaque(self):
        ref = TypedReference(ReferenceSpace.EXPRESSION, "not-parsed/as:meaning")
        self.assertEqual(ref.external_id, "not-parsed/as:meaning")


if __name__ == "__main__":
    unittest.main()
