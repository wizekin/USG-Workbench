"""Step 7.7 deterministic contextual retrieval acceptance tests."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.phase7_knowledge_retrieval import RetrievalError, retrieve_candidates

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "examples/phase7-knowledge-bundle-0.1.0.json").read_text(encoding="utf-8"))


class Phase7ContextualRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.bundle = deepcopy(FIXTURE)
        self.bundle["contexts"].append({
            "id": "context:domain:finance", "context_type": "DOMAIN",
            "value": "finance", "scope": "test-only",
        })
        for record in self.bundle["records"]:
            if record["kind"] in {"LEMMA", "LEXICAL_SENSE", "LEXICAL_FORM"}:
                record.setdefault("context_ids", []).append("context:domain:finance")
        self.bundle["mappings"] = [{
            "id": "mapping:bank", "source_record_id": "sense:en:bank:financial",
            "target_record_id": "concept:financial-institution",
            "mapping_type": "UNRESOLVED", "state": "UNRESOLVED",
            "evidence_ids": [self.bundle["evidence"][0]["id"]],
            "context_ids": ["context:domain:finance"],
        }]

    def test_exact_form_retrieves_linked_sense_and_mapping_target(self):
        result = retrieve_candidates([self.bundle], "bank", language="en")
        kinds = {x["record_kind"] for x in result["results"]}
        self.assertTrue({"LEXICAL_FORM", "LEMMA", "LEXICAL_SENSE", "CONCEPT"}.issubset(kinds))
        self.assertFalse(result["fuzzy_matching_performed"])

    def test_context_filter_is_explicit_and_excludes_nonmatching_records(self):
        result = retrieve_candidates([self.bundle], "bank", language="en",
                                     context_filters={"DOMAIN": "finance"})
        self.assertGreater(result["result_count"], 0)
        self.assertTrue(all("context:domain:finance" in x["context_ids"] for x in result["results"]))

    def test_wrong_language_profile_excludes_language_specific_records(self):
        result = retrieve_candidates([self.bundle], "bank", language="ar")
        self.assertEqual(result["result_count"], 0)

    def test_unresolved_mapping_remains_secondary_not_promoted(self):
        result = retrieve_candidates([self.bundle], "bank", language="en")
        concept = next(x for x in result["results"] if x["record_kind"] == "CONCEPT")
        self.assertEqual(concept["state"], "UNRESOLVED")
        self.assertEqual(concept["priority_band"], "SECONDARY")

    def test_equal_rank_is_reported_as_ambiguous(self):
        result = retrieve_candidates([self.bundle], "bank", language="en")
        self.assertIn("ambiguous_top_rank", result)
        self.assertTrue(all("tied_for_top_rank" in x for x in result["results"]))

    def test_ranking_is_deterministic_and_explained(self):
        a = retrieve_candidates([self.bundle], "bank", language="en")
        b = retrieve_candidates([self.bundle], "bank", language="en")
        self.assertEqual(a, b)
        self.assertTrue(all(x["explanation"] for x in a["results"]))

    def test_scores_are_not_probabilities_or_truth_values(self):
        result = retrieve_candidates([self.bundle], "bank")
        self.assertFalse(result["ranking_score_is_probability"])
        self.assertFalse(result["ranking_score_is_truth"])
        self.assertFalse(result["inference_performed"])

    def test_invalid_query_and_limit_are_rejected(self):
        with self.assertRaises(RetrievalError):
            retrieve_candidates([self.bundle], "  ")
        with self.assertRaises(RetrievalError):
            retrieve_candidates([self.bundle], "bank", limit=0)

    def test_candidate_only_state_filter_is_respected(self):
        result = retrieve_candidates([self.bundle], "bank", include_states=("CANDIDATE",))
        self.assertTrue(all(x["state"] == "CANDIDATE" for x in result["results"]))


if __name__ == "__main__":
    unittest.main()
