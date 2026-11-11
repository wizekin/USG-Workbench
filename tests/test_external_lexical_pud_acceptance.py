import unittest

from tools.usg_external_lexical_v0_1_0.acceptance import validate_report


def valid_report():
    return {
        "evaluation_type": "EXTERNAL_CRAWL_LEXICAL_GENERALIZATION_PUD",
        "pud_repository": "UniversalDependencies/UD_English-PUD",
        "pud_commit": "a697bab43d4111073356de0df5802488bca3de7e",
        "pud_file": "en_pud-ud-test.conllu",
        "pud_git_blob_sha1": "828f827759e7a9f89a8c42bfe79402dd65db71c3",
        "pud_sentences": 1000,
        "lexical_source_is_candidate_only": True,
        "runtime_promotion_allowed": False,
        "source_text_persisted": False,
        "lexical_shard_count": 1,
        "mapped_dictionary_entry_count": 2,
        "totals": {
            "tokens": 10, "seen_tokens": 3, "oov_tokens": 7,
            "gold_tag_in_candidates": 2, "ambiguous_seen_tokens": 1,
            "single_candidate_seen_tokens": 2, "multi_candidate_seen_tokens": 1,
            "candidate_label_total": 4, "gold_lemma_seen": 2,
            "gold_lemma_and_upos_hit": 2, "tokens_with_gold_lemma": 10,
            "token_coverage": 0.3, "oov_rate": 0.7,
        },
        "candidate_ambiguity": {
            "candidate_label_count_distribution": {"1": 2, "2": 1},
            "candidate_precision_measured": False,
        },
        "morphology_evaluation": {
            "totals": {
                "tokens": 10, "gold_feature_instances": 2,
                "candidate_feature_instances": 3, "matched_feature_instances": 2,
                "candidate_pool_precision": 2 / 3, "candidate_recall": 1.0,
            }
        },
    }


class ExternalLexicalPudAcceptanceTests(unittest.TestCase):
    def test_accepts_reproducible_candidate_only_report(self):
        result = validate_report(valid_report())
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["quality_thresholds_applied"])
        self.assertFalse(result["runtime_promotion_allowed"])

    def test_rejects_inconsistent_token_partition(self):
        report = valid_report()
        report["totals"]["oov_tokens"] = 8
        with self.assertRaisesRegex(ValueError, "seen and OOV"):
            validate_report(report)

    def test_rejects_candidate_promotion(self):
        report = valid_report()
        report["runtime_promotion_allowed"] = True
        with self.assertRaisesRegex(ValueError, "candidate-only"):
            validate_report(report)

    def test_rejects_ambiguity_histogram_mismatch(self):
        report = valid_report()
        report["candidate_ambiguity"]["candidate_label_count_distribution"] = {"1": 3}
        with self.assertRaisesRegex(ValueError, "histogram"):
            validate_report(report)


if __name__ == "__main__":
    unittest.main()
