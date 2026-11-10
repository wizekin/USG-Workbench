import unittest

from usg_unresolved_v12 import (
    MODEL_VERSION, NativeUnresolvedItemV12, UnresolvedStatus, same_unresolved_item,
)


class NativeUnresolvedItemV12Tests(unittest.TestCase):
    def make_item(self, **changes):
        values = dict(external_id="u:1", status=UnresolvedStatus.UNRESOLVED,
                      reason="No safe interpretation is available")
        values.update(changes)
        return NativeUnresolvedItemV12(**values)

    def test_version(self):
        self.assertEqual(MODEL_VERSION, "1.2.0")

    def test_all_contract_statuses_are_distinct(self):
        self.assertEqual({x.value for x in UnresolvedStatus}, {
            "UNRESOLVED", "UNSUPPORTED", "AMBIGUOUS", "INCOMPLETE",
            "CONFLICTING", "RESOURCE_INTERRUPTED", "UNKNOWN",
        })

    def test_identity_is_opaque_record_id(self):
        self.assertTrue(same_unresolved_item(self.make_item(), self.make_item(reason="different")))
        self.assertFalse(same_unresolved_item(self.make_item(), self.make_item(external_id="u:2")))

    def test_id_required(self):
        with self.assertRaises(ValueError):
            self.make_item(external_id="")

    def test_status_must_be_explicit(self):
        with self.assertRaises(TypeError):
            self.make_item(status="UNKNOWN")

    def test_reason_is_required_string(self):
        with self.assertRaises(TypeError):
            self.make_item(reason=None)

    def test_optional_fields_remain_absent(self):
        item = self.make_item()
        self.assertIsNone(item.surface_text)
        self.assertIsNone(item.scope_ref)
        self.assertIsNone(item.scope_label)
        self.assertEqual(item.evidence_refs, ())
        self.assertEqual(item.candidate_refs, ())
        self.assertIsNone(item.native_status)

    def test_exact_text_fields_are_preserved(self):
        item = self.make_item(surface_text="  exact\ntext ", scope_ref="opaque:any-space",
                               scope_label="uncertain scope", native_status="local-status")
        self.assertEqual(item.surface_text, "  exact\ntext ")
        self.assertEqual(item.scope_ref, "opaque:any-space")
        self.assertEqual(item.scope_label, "uncertain scope")
        self.assertEqual(item.native_status, "local-status")

    def test_scope_reference_is_opaque_not_type_inferred(self):
        item = self.make_item(scope_ref="same-looking-id")
        self.assertEqual(item.scope_ref, "same-looking-id")

    def test_evidence_and_candidate_references_preserve_order_and_repetition(self):
        item = self.make_item(evidence_refs=("e:2", "e:1", "e:2"),
                              candidate_refs=("candidate:3", "candidate:1", "candidate:3"))
        self.assertEqual(item.evidence_refs, ("e:2", "e:1", "e:2"))
        self.assertEqual(item.candidate_refs, ("candidate:3", "candidate:1", "candidate:3"))

    def test_reference_lists_must_be_tuples(self):
        with self.assertRaises(TypeError):
            self.make_item(evidence_refs=["e:1"])
        with self.assertRaises(TypeError):
            self.make_item(candidate_refs=["c:1"])

    def test_reference_values_must_be_nonempty_strings(self):
        with self.assertRaises(ValueError):
            self.make_item(evidence_refs=("e:1", ""))
        with self.assertRaises(ValueError):
            self.make_item(candidate_refs=(None,))

    def test_status_values_are_not_collapsed(self):
        self.assertNotEqual(UnresolvedStatus.AMBIGUOUS, UnresolvedStatus.UNRESOLVED)
        self.assertNotEqual(UnresolvedStatus.INCOMPLETE, UnresolvedStatus.RESOURCE_INTERRUPTED)
        self.assertNotEqual(UnresolvedStatus.UNKNOWN, UnresolvedStatus.UNSUPPORTED)

    def test_optional_text_fields_reject_non_strings(self):
        for field in ("surface_text", "scope_ref", "scope_label", "native_status"):
            with self.subTest(field=field), self.assertRaises(TypeError):
                self.make_item(**{field: 42})


if __name__ == "__main__":
    unittest.main()
