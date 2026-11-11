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
            "kernel-lab-local-api-cli",
            "workbench-to-canonical-adapter",
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
        self.assertEqual(len(suite["tests"]), 9)

    def test_local_api_oracle_covers_persistence_and_loopback_boundary(self):
        suite = SUITES["kernel-lab-local-api-cli"]
        self.assertIn("loopback-only", suite["oracle"])
        self.assertEqual(suite["tests"], ["test_phase3_local_api_cli.py"])

    def test_workbench_adapter_oracle_checks_canonical_schema_and_offsets(self):
        suite = SUITES["workbench-to-canonical-adapter"]
        self.assertIn("Unicode offset conversion", suite["oracle"])
        self.assertEqual(suite["claim"], "fixture_backed_adapter_contract_conformance")


if __name__ == "__main__":
    unittest.main()
