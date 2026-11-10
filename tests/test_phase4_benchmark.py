import json
import unittest
from pathlib import Path

from tools.phase4_interpretation_benchmark_v0_1_0.run import evaluate

ROOT = Path(__file__).resolve().parents[1]


class Phase4BenchmarkTests(unittest.TestCase):
    def test_frozen_benchmark_meets_all_acceptance_metrics(self):
        fixtures = json.loads((ROOT / "benchmarks/phase4-interpretation/v0.1.0/fixtures.json").read_text(encoding="utf-8"))
        report = evaluate(fixtures)
        self.assertEqual(report["case_count"], 6)
        self.assertTrue(all(report["acceptance"].values()), report["metrics"])
        self.assertEqual(report["metrics"]["truth_policy_violation_count"], 0)

    def test_corpus_contains_supported_and_abstention_cases(self):
        fixtures = json.loads((ROOT / "benchmarks/phase4-interpretation/v0.1.0/fixtures.json").read_text(encoding="utf-8"))
        statuses = {x["expected_completion_status"] for x in fixtures["cases"]}
        self.assertIn("COMPLETE", statuses)
        self.assertIn("PARTIAL", statuses)
        self.assertIn("UNSUPPORTED", statuses)


if __name__ == "__main__":
    unittest.main()
