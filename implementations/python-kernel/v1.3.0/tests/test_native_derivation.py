import unittest

from usg_derivation_v13 import (
    MODEL_VERSION, DerivationMethod, DerivationModelInfo, DerivationStatus,
    NativeDerivationV13, same_derivation,
)


class NativeDerivationV13Tests(unittest.TestCase):
    def make_item(self, **changes):
        values = dict(
            external_id="d:1", method=DerivationMethod.DETERMINISTIC_RULE,
            input_refs=("x:1", "e:1"), output_refs=("x:2",),
            status=DerivationStatus.PROPOSED,
        )
        values.update(changes)
        return NativeDerivationV13(**values)

    def test_version(self):
        self.assertEqual(MODEL_VERSION, "1.3.0")

    def test_all_methods_and_statuses_are_distinct(self):
        self.assertEqual(len(DerivationMethod), 6)
        self.assertEqual(len(DerivationStatus), 5)

    def test_identity_is_opaque(self):
        self.assertTrue(same_derivation(self.make_item(), self.make_item(status=DerivationStatus.REJECTED)))
        self.assertFalse(same_derivation(self.make_item(), self.make_item(external_id="d:2")))

    def test_id_required(self):
        with self.assertRaises(ValueError):
            self.make_item(external_id="")

    def test_method_and_status_must_be_explicit(self):
        with self.assertRaises(TypeError):
            self.make_item(method="IMPORT")
        with self.assertRaises(TypeError):
            self.make_item(status="VALIDATED")

    def test_input_output_and_rule_refs_preserve_order_and_repetition(self):
        item = self.make_item(input_refs=("r:2", "r:1", "r:2"),
                              output_refs=("o:1", "o:1"), rule_ids=("rule:2", "rule:1", "rule:2"))
        self.assertEqual(item.input_refs, ("r:2", "r:1", "r:2"))
        self.assertEqual(item.output_refs, ("o:1", "o:1"))
        self.assertEqual(item.rule_ids, ("rule:2", "rule:1", "rule:2"))

    def test_reference_arrays_must_be_tuples(self):
        with self.assertRaises(TypeError):
            self.make_item(input_refs=["x:1"])
        with self.assertRaises(TypeError):
            self.make_item(output_refs=["x:1"])
        with self.assertRaises(TypeError):
            self.make_item(rule_ids=["rule:1"])

    def test_reference_values_must_be_nonempty_strings(self):
        with self.assertRaises(ValueError):
            self.make_item(input_refs=("x:1", ""))
        with self.assertRaises(ValueError):
            self.make_item(output_refs=(None,))

    def test_optional_fields_remain_absent(self):
        item = self.make_item()
        self.assertIsNone(item.component)
        self.assertIsNone(item.model)
        self.assertIsNone(item.timestamp)
        self.assertEqual(item.rule_ids, ())
        self.assertEqual(item.diagnostics, ())

    def test_model_metadata_preserves_nested_data(self):
        info = DerivationModelInfo(provider="local", name="model", revision="rev-1",
                                   metadata={"runtime": {"quant": "q4"}})
        self.assertEqual(info.metadata, {"runtime": {"quant": "q4"}})

    def test_model_info_types_are_checked(self):
        with self.assertRaises(TypeError):
            DerivationModelInfo(provider=12)
        with self.assertRaises(TypeError):
            DerivationModelInfo(metadata=["not", "mapping"])

    def test_model_metadata_keys_are_strings(self):
        with self.assertRaises(ValueError):
            DerivationModelInfo(metadata={1: "bad"})

    def test_timestamp_is_preserved_as_exact_string(self):
        value = "2026-11-10T06:00:00Z"
        self.assertEqual(self.make_item(timestamp=value).timestamp, value)

    def test_diagnostics_preserve_order(self):
        item = self.make_item(diagnostics=("first", "second", "first"))
        self.assertEqual(item.diagnostics, ("first", "second", "first"))

    def test_diagnostics_require_tuple_of_strings(self):
        with self.assertRaises(TypeError):
            self.make_item(diagnostics=["diagnostic"])
        with self.assertRaises(TypeError):
            self.make_item(diagnostics=("valid", 7))

    def test_unknown_method_and_status_remain_explicit(self):
        item = self.make_item(method=DerivationMethod.UNKNOWN, status=DerivationStatus.UNKNOWN)
        self.assertEqual(item.method, DerivationMethod.UNKNOWN)
        self.assertEqual(item.status, DerivationStatus.UNKNOWN)

    def test_model_proposal_does_not_self_validate(self):
        item = self.make_item(method=DerivationMethod.MODEL_PROPOSAL,
                              status=DerivationStatus.PROPOSED)
        self.assertEqual(item.status, DerivationStatus.PROPOSED)


if __name__ == "__main__":
    unittest.main()
