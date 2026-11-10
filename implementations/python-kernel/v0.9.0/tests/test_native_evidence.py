import unittest

from usg_evidence_v09 import (
    MODEL_VERSION, AlignmentStatus, EvidenceSpan, NativeEvidenceV09,
    ReferenceSpace, SemanticSupportStatus, TypedReference, same_evidence,
)


class NativeEvidenceV09Tests(unittest.TestCase):
    def setUp(self):
        self.source = TypedReference(ReferenceSpace.SOURCE, "opaque/source-A")
        self.span = EvidenceSpan(self.source, 2, 9)

    def make_evidence(self, **changes):
        values = dict(
            external_id="opaque/evidence-A",
            source_ref=self.source,
            span=self.span,
            quote="evidence",
            alignment_status=AlignmentStatus.EXACT,
            semantic_support_status=SemanticSupportStatus.NOT_ESTABLISHED,
        )
        values.update(changes)
        return NativeEvidenceV09(**values)

    def test_version(self):
        self.assertEqual(MODEL_VERSION, "0.9.0")

    def test_exact_alignment_does_not_default_semantic_support(self):
        item = self.make_evidence()
        self.assertEqual(item.alignment_status, AlignmentStatus.EXACT)
        self.assertEqual(item.semantic_support_status, SemanticSupportStatus.NOT_ESTABLISHED)

    def test_all_alignment_values_are_distinct(self):
        self.assertEqual(set(AlignmentStatus), {
            AlignmentStatus.EXACT, AlignmentStatus.MISMATCH, AlignmentStatus.UNVERIFIED
        })

    def test_all_support_values_are_distinct(self):
        self.assertEqual(len(SemanticSupportStatus), 6)

    def test_source_and_span_must_use_source_space(self):
        with self.assertRaises(ValueError):
            EvidenceSpan(TypedReference(ReferenceSpace.EVIDENCE, "x"), 0, 1)

    def test_span_rejects_negative_start(self):
        with self.assertRaises(ValueError):
            EvidenceSpan(self.source, -1, 1)

    def test_span_rejects_empty_or_reversed_range(self):
        for start, end in ((2, 2), (3, 2)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                EvidenceSpan(self.source, start, end)

    def test_span_rejects_boolean_offsets(self):
        with self.assertRaises(ValueError):
            EvidenceSpan(self.source, True, 2)

    def test_span_requires_unicode_code_points(self):
        with self.assertRaises(ValueError):
            EvidenceSpan(self.source, 0, 1, "utf16_code_unit")

    def test_evidence_and_span_source_must_match(self):
        other = TypedReference(ReferenceSpace.SOURCE, "opaque/source-B")
        with self.assertRaises(ValueError):
            self.make_evidence(span=EvidenceSpan(other, 2, 9))

    def test_quote_is_preserved_exactly(self):
        quote = "  Exact  quote\n"
        self.assertEqual(self.make_evidence(quote=quote).quote, quote)

    def test_ordered_repeated_rule_references_are_preserved(self):
        refs = ("rule:2", "rule:1", "rule:2")
        self.assertEqual(self.make_evidence(supporting_rule_refs=refs).supporting_rule_refs, refs)

    def test_empty_rule_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_evidence(supporting_rule_refs=("rule:1", ""))

    def test_native_verification_meaning_is_optional_and_opaque(self):
        self.assertIsNone(self.make_evidence().native_verification_meaning)
        text = "source alignment only; no entailment assertion"
        self.assertEqual(self.make_evidence(native_verification_meaning=text).native_verification_meaning, text)

    def test_wrong_status_types_are_rejected(self):
        with self.assertRaises(TypeError):
            self.make_evidence(alignment_status="EXACT")
        with self.assertRaises(TypeError):
            self.make_evidence(semantic_support_status="CORROBORATED")

    def test_identity_uses_only_opaque_record_id(self):
        a = self.make_evidence(quote="one quote")
        b = self.make_evidence(quote="different quote")
        self.assertTrue(same_evidence(a, b))
        c = self.make_evidence(external_id="another-id")
        self.assertFalse(same_evidence(a, c))


if __name__ == "__main__":
    unittest.main()
