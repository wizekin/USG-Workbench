import unittest

from tools.phase6_auto_reference_v1_0.generate import build, validate, PROFILES
from tools.phase6_auto_reference_v1_0.evaluate import run


class TestPhase6AutomaticSyntheticReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.lexicon = build()
        validate(cls.corpus, cls.lexicon)
        cls.result = run()
        cls.evaluation = cls.result["report"]["evaluation"]

    def test_has_500_cases_across_all_ten_profiles(self):
        self.assertEqual(len(self.corpus["cases"]), 500)
        self.assertEqual(len(self.corpus["construction_inventory"]), 10)
        self.assertEqual(len(PROFILES), 10)
        for profile in self.corpus["construction_inventory"].values():
            self.assertEqual(profile, {"positive": 20, "negative": 20, "ambiguous": 10})

    def test_generation_is_independent_and_automatic(self):
        metadata = self.corpus["generation"]
        self.assertFalse(metadata["uses_human_annotations"])
        self.assertFalse(metadata["uses_model_labels"])
        self.assertFalse(metadata["reads_development_fixtures"])
        self.assertFalse(metadata["reads_candidate_lexicon"])
        self.assertFalse(metadata["candidate_predictions_used_during_generation"])
        self.assertIsNone(metadata["external_corpus_dependency"])
        self.assertEqual(self.lexicon["license"], "CC0-1.0")
        self.assertEqual(self.lexicon["status"], "BENCHMARK_ONLY")

    def test_case_ids_and_source_spans_are_valid(self):
        ids = [case["id"] for case in self.corpus["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.corpus["cases"]:
            for role, span in case["expected_role_spans"].items():
                self.assertEqual(case["text"][span["start"]:span["end"]], span["surface"])
                self.assertEqual(case["expected_role_bindings"][role], span["surface"])

    def test_all_ten_synthetic_profile_gates_pass(self):
        self.assertTrue(self.evaluation["all_synthetic_profile_gates_passed"])
        self.assertEqual(self.evaluation["failed_case_ids"], [], self.evaluation["failure_diagnostics"])
        self.assertEqual(self.evaluation["profile_count"], 10)
        for metrics in self.evaluation["by_profile"].values():
            self.assertEqual(metrics["positive_detection"], 1.0)
            self.assertEqual(metrics["exact_role_accuracy"], 1.0)
            self.assertEqual(metrics["exact_span_accuracy"], 1.0)
            self.assertEqual(metrics["relation_accuracy"], 1.0)
            self.assertEqual(metrics["negative_abstention"], 1.0)
            self.assertEqual(metrics["ambiguity_preservation"], 1.0)
            self.assertEqual(metrics["false_unique_ambiguities"], 0)

    def test_no_production_construction_is_enabled(self):
        self.assertEqual(self.evaluation["benchmark_enabled_constructions"], [])
        self.assertEqual(self.evaluation["runtime_capability_state"], "CANDIDATE_ONLY")
        self.assertFalse(self.evaluation["naturalistic_semantic_accuracy_claimed"])


if __name__ == "__main__":
    unittest.main()
