"""Step 5.11 end-to-end gold-corpus benchmark tests."""
import unittest

from tools.phase5_interpretation_benchmark_v0_2_0.run import (
    CORPUS, corpus_summary, evaluate, load_and_validate, quality_gate, run_pipeline,
)


class Phase5Step511BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = load_and_validate(CORPUS)
        cls.predictions, cls.performance = run_pipeline(cls.corpus)
        cls.report = evaluate(cls.corpus, cls.predictions)

    def test_frozen_corpus_has_balanced_language_and_class_coverage(self):
        summary = corpus_summary(self.corpus)
        self.assertEqual(summary["case_count"], 100)
        self.assertEqual(summary["minimum_fixture_gate"], {"ar": True, "en": True})

    def test_real_pipeline_runs_every_case_once(self):
        self.assertEqual(len(self.predictions["predictions"]), 100)
        ids = [item["case_id"] for item in self.predictions["predictions"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {item["id"] for item in self.corpus["cases"]})

    def test_performance_report_is_finite_and_version_pinned(self):
        self.assertEqual(self.performance["case_count"], 100)
        self.assertGreaterEqual(self.performance["total_elapsed_ms"], 0)
        self.assertGreaterEqual(self.performance["peak_traced_memory_bytes"], 0)
        self.assertEqual(len(self.performance["resource_manifest_digest"]), 64)
        self.assertEqual(len(self.performance["corpus_sha256"]), 64)
        self.assertEqual(self.performance["enabled_constructions_observed"], [
            "ar.simple_transitive.svo", "ar.simple_transitive.vso", "en.simple_transitive.svo"
        ])

    def test_evaluation_reports_language_specific_precision_recall_and_abstention(self):
        for language in ("en", "ar"):
            metrics = self.report["by_language"][language]
            self.assertEqual(metrics["case_count"], 50)
            self.assertEqual(metrics["positive_gold_count"], 20)
            self.assertEqual(metrics["positive_completion_status_cases"], 20)
            self.assertEqual(metrics["negative_gold_count"], 20)
            self.assertEqual(metrics["ambiguous_gold_count"], 10)
            self.assertIn("construction_precision", metrics)
            self.assertIn("construction_recall", metrics)
            self.assertIn("negative_abstention_rate", metrics)
            self.assertIn("ambiguous_abstention_rate", metrics)

    def test_quality_gates_pass_independently_for_both_languages(self):
        gate = quality_gate(self.report)
        self.assertTrue(gate["passed"], gate)
        for language in ("en", "ar"):
            self.assertTrue(gate["by_language"][language]["passed"])

    def test_interrogative_force_is_not_misreported_as_a_complete_assertion(self):
        from tools.usg_interpretation_v0_2_0 import Phase5InterpretationService
        service = Phase5InterpretationService()
        digest = self.performance["resource_manifest_digest"]
        for text, language in (("Ada writes code?", "en"), ("كتب الطالب الرسالة؟", "ar")):
            with self.subTest(text=text):
                result = service.interpret(text, language, resource_manifest_digest=digest)
                self.assertEqual(result["completion_status"], "UNSUPPORTED")
                self.assertIn("UNSUPPORTED_INTERROGATIVE_FORCE", {
                    item["code"] for item in result["diagnostics"]
                })

    def test_ambiguous_and_unsupported_cases_never_receive_guessed_role_graphs(self):
        gold = {item["id"]: item for item in self.corpus["cases"]}
        for prediction in self.predictions["predictions"]:
            if gold[prediction["case_id"]]["gold_class"] != "POSITIVE":
                self.assertIsNone(prediction["construction_id"])
                self.assertEqual(prediction["role_bindings"], {})
                self.assertEqual(prediction["role_spans"], {})
                if gold[prediction["case_id"]]["gold_class"] == "AMBIGUOUS":
                    self.assertIn(prediction["completion_status"], {"AMBIGUOUS", "PARTIAL", "UNSUPPORTED"})


if __name__ == "__main__":
    unittest.main()
