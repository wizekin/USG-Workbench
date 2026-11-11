"""Tests for the Phase 5 v0.2.0 benchmark corpus and evaluator."""
import unittest

from tools.phase5_interpretation_benchmark_v0_2_0.run import (
    CORPUS, corpus_summary, evaluate, load_and_validate,
)


class Phase5BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_and_validate()

    def test_corpus_meets_per_language_fixture_minimums(self):
        summary = corpus_summary(self.corpus)
        self.assertEqual(summary["case_count"], 100)
        self.assertEqual(summary["by_language"]["en"],
                         {"POSITIVE": 20, "NEGATIVE": 20, "AMBIGUOUS": 10})
        self.assertEqual(summary["by_language"]["ar"],
                         {"POSITIVE": 20, "NEGATIVE": 20, "AMBIGUOUS": 10})
        self.assertTrue(all(summary["minimum_fixture_gate"].values()))

    def test_every_positive_role_span_is_exact_source_aligned(self):
        for case in self.corpus["cases"]:
            for span in case["expected_role_spans"].values():
                self.assertEqual(case["text"][span["start"]:span["end"]], span["surface"])

    def test_perfect_synthetic_predictions_score_one_without_claiming_model_performance(self):
        predictions = {"predictions": []}
        for case in self.corpus["cases"]:
            predictions["predictions"].append({
                "case_id": case["id"],
                "completion_status": case["expected_completion_status"],
                "construction_id": case["expected_construction"],
                "role_bindings": case["expected_roles"],
                "role_spans": case["expected_role_spans"],
            })
        report = evaluate(self.corpus, predictions)
        for language in ("en", "ar"):
            metrics = report["by_language"][language]
            self.assertEqual(metrics["construction_precision"], 1.0)
            self.assertEqual(metrics["construction_recall"], 1.0)
            self.assertEqual(metrics["completion_status_accuracy"], 1.0)
            self.assertEqual(metrics["role_binding_exact_accuracy"], 1.0)
            self.assertEqual(metrics["role_span_exact_and_valid_accuracy"], 1.0)

    def test_false_positive_and_missed_positive_are_counted(self):
        predictions = {"predictions": []}
        for case in self.corpus["cases"]:
            row = {
                "case_id": case["id"],
                "completion_status": case["expected_completion_status"],
                "construction_id": case["expected_construction"],
                "role_bindings": case["expected_roles"],
                "role_spans": case["expected_role_spans"],
            }
            if case["id"] == "en.positive.01":
                row["construction_id"] = None
            if case["id"] == "en.negative.01":
                row["construction_id"] = "en.simple_transitive.svo"
            predictions["predictions"].append(row)
        report = evaluate(self.corpus, predictions)
        metrics = report["by_language"]["en"]
        self.assertEqual(metrics["construction_true_positive"], 19)
        self.assertEqual(metrics["construction_false_positive"], 1)
        self.assertEqual(metrics["construction_false_negative"], 1)
        self.assertLess(metrics["construction_precision"], 1.0)
        self.assertLess(metrics["construction_recall"], 1.0)

    def test_invalid_prediction_span_is_not_counted_as_valid(self):
        case = next(x for x in self.corpus["cases"] if x["id"] == "en.positive.01")
        predictions = {"predictions": [{
            "case_id": case["id"], "completion_status": "COMPLETE",
            "construction_id": case["expected_construction"],
            "role_bindings": case["expected_roles"],
            "role_spans": {"AGENT": {"start": 0, "end": 3, "surface": "bad"}},
        }]}
        report = evaluate(self.corpus, predictions)
        self.assertEqual(report["by_language"]["en"]["role_span_exact_and_valid_accuracy"], 0.0)


if __name__ == "__main__":
    unittest.main()
