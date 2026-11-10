import unittest
from usg_unresolved_v121 import (
    MODEL_VERSION, ReferenceSpace, TypedReference, UnresolvedStatus,
    NativeUnresolvedItemV121,
)


class NativeUnresolvedItemV121Tests(unittest.TestCase):
    def test_version_and_statuses(self):
        self.assertEqual(MODEL_VERSION, "1.2.1")
        self.assertEqual(len(UnresolvedStatus), 7)

    def test_scope_reference_is_typed_expression(self):
        ref = TypedReference(ReferenceSpace.EXPRESSION, "x:1")
        item = NativeUnresolvedItemV121("u:1", UnresolvedStatus.UNRESOLVED, "reason", scope_ref=ref)
        self.assertEqual(item.scope_ref, ref)

    def test_scope_reference_rejects_evidence_space(self):
        with self.assertRaises(ValueError):
            NativeUnresolvedItemV121("u:1", UnresolvedStatus.UNRESOLVED, "reason",
                                     scope_ref=TypedReference(ReferenceSpace.EVIDENCE, "e:1"))

    def test_evidence_references_are_typed_ordered_and_repeated(self):
        refs = (TypedReference(ReferenceSpace.EVIDENCE, "e:2"),
                TypedReference(ReferenceSpace.EVIDENCE, "e:1"),
                TypedReference(ReferenceSpace.EVIDENCE, "e:2"))
        item = NativeUnresolvedItemV121("u:1", UnresolvedStatus.UNRESOLVED, "reason",
                                        evidence_refs=refs)
        self.assertEqual(item.evidence_refs, refs)

    def test_evidence_references_reject_expression_space(self):
        with self.assertRaises(ValueError):
            NativeUnresolvedItemV121("u:1", UnresolvedStatus.UNRESOLVED, "reason",
                                     evidence_refs=(TypedReference(ReferenceSpace.EXPRESSION, "x:1"),))

    def test_candidate_references_remain_opaque_ordered_strings(self):
        item = NativeUnresolvedItemV121("u:1", UnresolvedStatus.AMBIGUOUS, "reason",
                                        candidate_refs=("candidate:2", "candidate:1", "candidate:2"))
        self.assertEqual(item.candidate_refs, ("candidate:2", "candidate:1", "candidate:2"))


if __name__ == "__main__":
    unittest.main()
