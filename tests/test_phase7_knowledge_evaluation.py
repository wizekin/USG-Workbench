"""Step 7.10 frozen bilingual evaluation and exit acceptance tests."""
import unittest
from tools.phase7_knowledge_evaluation import run_evaluation


class Phase7AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_evaluation()

    def test_frozen_bilingual_retrieval_suite_passes(self):
        self.assertEqual(self.report["status"], "PASS")
        self.assertEqual(self.report["counts"]["positive_exact_form_cases"], 46)
        self.assertEqual(self.report["counts"]["wrong_language_negative_cases"], 46)
        self.assertEqual(self.report["counts"]["oov_negative_cases"], 10)
        self.assertTrue(self.report["gates"]["retrieval_cases"])

    def test_polysemy_and_unresolved_mapping_are_preserved(self):
        self.assertTrue(self.report["gates"]["polysemy_preservation"])
        self.assertTrue(self.report["gates"]["all_alignment_mappings_remain_unresolved"])
        self.assertEqual(self.report["counts"]["unresolved_mapping_proposals"],
                         self.report["counts"]["mapping_proposals"])

    def test_provenance_rights_conflict_and_sqlite_replay_gates_pass(self):
        for gate in ("source_provenance_complete", "rights_and_candidate_lifecycle_preserved",
                     "provider_conflict_preserved_without_winner",
                     "sqlite_snapshot_round_trip_and_digest", "deterministic_alignment_replay"):
            with self.subTest(gate=gate):
                self.assertTrue(self.report["gates"][gate])

    def test_no_false_merges_or_unsupported_promotions(self):
        self.assertEqual(self.report["gates"]["false_merge_count"], 0)
        self.assertEqual(self.report["gates"]["unsupported_promotion_count"], 0)


if __name__ == "__main__":
    unittest.main()
