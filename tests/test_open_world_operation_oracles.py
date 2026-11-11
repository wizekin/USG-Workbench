"""OW-11 operation-oracle registry contract tests."""
import unittest

from tools.open_world_evaluation.operation_oracles import SUITES


class OperationOracleRegistryTests(unittest.TestCase):
    def test_each_operation_suite_has_independent_oracle_description(self):
        self.assertEqual(set(SUITES), {
            "phase2-structured-semantic-reasoning",
            "phase3-canonical-sqlite-store",
            "phase6-candidate-expansion",
            "python-usg-sem-document-adapters-v15",
            "python-native-semantic-models-v06-v14",
        })
        for target_id, suite in SUITES.items():
            with self.subTest(target=target_id):
                self.assertTrue(suite["tests"])
                self.assertTrue(suite["oracle"])
                self.assertIn("oracle", suite)
                self.assertIn("claim", suite)

    def test_candidate_only_phase6_oracle_is_not_described_as_accuracy(self):
        suite = SUITES["phase6-candidate-expansion"]
        self.assertIn("development-only", suite["oracle"])
        self.assertEqual(suite["claim"], "mixed_gold_and_development_oracles")

    def test_v15_adapter_has_round_trip_fixture_oracle(self):
        suite = SUITES["python-usg-sem-document-adapters-v15"]
        self.assertIn("round-trip preservation", suite["oracle"])
        self.assertEqual(suite["claim"], "fixture_backed_adapter_contract_conformance")

    def test_native_model_suite_is_explicitly_version_bounded(self):
        suite = SUITES["python-native-semantic-models-v06-v14"]
        self.assertIn("versioned native model", suite["oracle"])
        self.assertEqual(len(suite["tests"]), 2)


if __name__ == "__main__":
    unittest.main()
