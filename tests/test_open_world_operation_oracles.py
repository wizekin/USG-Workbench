"""OW-11 operation-oracle registry contract tests."""
import unittest

from tools.open_world_evaluation.operation_oracles import SUITES


class OperationOracleRegistryTests(unittest.TestCase):
    def test_each_operation_suite_has_independent_oracle_description(self):
        self.assertEqual(set(SUITES), {
            "phase2-structured-semantic-reasoning",
            "phase3-canonical-sqlite-store",
            "phase6-candidate-expansion",
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


if __name__ == "__main__":
    unittest.main()
