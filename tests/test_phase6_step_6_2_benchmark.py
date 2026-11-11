"""Step 6.2 corpus and evaluator acceptance tests."""
import unittest
from tools.phase6_interpretation_benchmark_v0_3_0.run import load_corpus, evaluate, quality_gate


class Phase6Step62BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_corpus()

    def test_frozen_corpus_has_required_per_language_construction_denominators(self):
        self.assertEqual(len(self.corpus["cases"]), 400)
        for language, constructions in self.corpus["construction_inventory"].items():
            for construction in constructions:
                rows = [x for x in self.corpus["cases"] if x["language"] == language and x["target_construction"] == construction["construction_id"]]
                self.assertEqual(sum(x["gold_class"] == "POSITIVE" for x in rows), 20)
                self.assertEqual(sum(x["gold_class"] == "NEGATIVE" for x in rows), 20)
                self.assertEqual(sum(x["gold_class"] == "AMBIGUOUS" for x in rows), 10)

    def test_gold_spans_are_exact_unicode_code_point_slices(self):
        for case in self.corpus["cases"]:
            for span in case["expected_role_spans"].values():
                self.assertEqual(case["text"][span["start"]:span["end"]], span["surface"])

    def test_nonpositive_target_fixtures_do_not_force_pipeline_status_or_graph(self):
        for case in self.corpus["cases"]:
            if case["gold_class"] != "POSITIVE":
                self.assertIsNone(case["expected_completion_status"])
                self.assertIsNone(case["gold_construction"])
                self.assertEqual(case["expected_roles"], {})
                self.assertEqual(case["expected_role_spans"], {})

    def test_evaluator_refuses_missing_denominators_and_rewards_abstention(self):
        predictions = {"predictions": []}
        report = evaluate(self.corpus, predictions)
        self.assertFalse(quality_gate(report)["passed"])
        for metrics in report["by_construction"].values():
            self.assertEqual(metrics["negative_abstention"], 1.0)
            self.assertEqual(metrics["ambiguous_abstention"], 1.0)
            self.assertEqual(metrics["recall"], 0.0)


if __name__ == "__main__":
    unittest.main()
