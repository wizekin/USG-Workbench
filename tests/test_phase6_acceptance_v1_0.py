"""Tests for the graph-first automatic Phase 6 acceptance factory."""
import unittest
from collections import Counter

from tools.phase6_acceptance_v1_0.generate import (
    BENCHMARK_ID, PROFILE_SPECS, build, corpus_sha256, validate,
)


class Phase6AutomaticAcceptanceFactoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = build()

    def test_factory_covers_all_five_construction_families_in_both_languages(self):
        self.assertEqual(self.corpus["benchmark_id"], BENCHMARK_ID)
        self.assertEqual(len(self.corpus["cases"]), 500)
        self.assertEqual(len(self.corpus["construction_inventory"]), 10)
        self.assertEqual(len(PROFILE_SPECS), 10)
        self.assertEqual(set(self.corpus["languages"]), {"en", "ar"})

    def test_every_profile_meets_the_20_20_10_fixture_minimum(self):
        counts = {}
        for case in self.corpus["cases"]:
            key = f'{case["language"]}/{case["profile"]}'
            counts.setdefault(key, Counter())
            counts[key][case["gold_class"].lower()] += 1
        self.assertEqual(set(counts), set(self.corpus["construction_inventory"]))
        for key, row in counts.items():
            self.assertEqual(
                {name: row[name] for name in ("positive", "negative", "ambiguous")},
                {"positive": 20, "negative": 20, "ambiguous": 10},
                key,
            )

    def test_generation_oracle_is_created_without_runtime_predictions(self):
        metadata = self.corpus["generation"]
        self.assertTrue(metadata["reference_graph_created_before_text_realization"])
        self.assertFalse(metadata["uses_human_annotations_for_new_cases"])
        self.assertFalse(metadata["uses_model_labels"])
        self.assertFalse(metadata["uses_phase6_candidate_predictions"])
        self.assertFalse(metadata["reads_phase6_development_fixtures"])
        self.assertFalse(metadata["uses_candidate_lexicon"])
        self.assertFalse(metadata["uses_external_corpus"])

    def test_all_generated_role_and_marker_spans_match_exact_source_slices(self):
        for case in self.corpus["cases"]:
            text = case["text"]
            for span in case.get("expected_node_spans", []):
                self.assertEqual(text[span["start"]:span["end"]], span["surface"], case["id"])
            for span in case.get("expected", {}).get("required_role_spans", []):
                self.assertEqual(text[span["start"]:span["end"]], span["surface"], case["id"])
            for span in case.get("expected", {}).get("required_markers", []):
                self.assertEqual(text[span["start"]:span["end"]], span["surface"], case["id"])

    def test_generation_is_reproducible(self):
        again = build()
        self.assertEqual(corpus_sha256(self.corpus), corpus_sha256(again))

    def test_step_6_12_to_6_14_integration_checks_are_registered(self):
        checks = {item["step"] for item in self.corpus["integration_checks"]}
        self.assertEqual(checks, {"6.12", "6.13", "6.14"})

    def test_validator_rejects_a_corrupted_reference_span(self):
        import copy
        broken = copy.deepcopy(self.corpus)
        target = next(
            case for case in broken["cases"]
            if case.get("expected", {}).get("required_role_spans")
        )
        target["expected"]["required_role_spans"][0]["surface"] = "not-the-source"
        with self.assertRaises(ValueError):
            validate(broken)


if __name__ == "__main__":
    unittest.main()
