from __future__ import annotations

import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.usg_external_lexical_v0_1_0.pud_evaluation import (
    evaluate, evaluate_morphology, load_candidate_evidence, load_candidate_inventory, normalize,
)


class ExternalLexicalPudEvaluationTests(unittest.TestCase):
    def test_normalization_is_language_aware(self):
        self.assertEqual(normalize("Bank", "en"), "bank")
        self.assertEqual(normalize("بنك", "ar"), "بنك")

    def test_reads_shards_and_separates_lemmas_from_observed_forms(self):
        record = {"entries": [
            {"lemma": "bank", "part_of_speech": "noun",
             "forms": [{"form": "banks", "tags": ["plural"]}]},
            {"lemma": "run", "part_of_speech": "verb", "forms": []},
            {"lemma": "quick", "part_of_speech": "adjective", "forms": []},
            {"lemma": "unknown", "part_of_speech": "unmapped", "forms": []},
        ]}
        with TemporaryDirectory() as temp:
            path = Path(temp) / "batch.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")
            evidence = load_candidate_evidence(temp)
            inventory = load_candidate_inventory(temp)
        self.assertEqual(evidence["forms"]["bank"], {"NOUN"})
        self.assertEqual(evidence["forms"]["banks"], {"NOUN"})
        self.assertEqual(evidence["lemmas"]["bank"], {"NOUN"})
        self.assertNotIn("banks", evidence["lemmas"])
        self.assertEqual(evidence["observed_forms"]["banks"], {"NOUN"})
        self.assertEqual(inventory["run"], {"VERB"})
        self.assertNotIn("unknown", inventory)
        self.assertEqual(evidence["entry_count"], 3)
        self.assertEqual(evidence["shard_count"], 1)
        self.assertEqual(evidence["form_tag_counts"], {"plural": 1})
        self.assertEqual(evidence["tagged_form_records"], 1)
        self.assertEqual(evidence["morphology_candidates"]["banks"], {("NOUN", "Number", "Plur")})
        self.assertEqual(evidence["mapped_morphology_tag_counts"], {"plural": 1})

    def test_reports_oov_ambiguity_pos_and_lemma_coverage(self):
        sentences = [{"tokens": [
            {"form": "bank", "lemma": "bank", "upos": "NOUN"},
            {"form": "run", "lemma": "run", "upos": "VERB"},
            {"form": "mystery", "lemma": "mystery", "upos": "NOUN"},
            {"form": "fast", "lemma": "fast", "upos": "ADV"},
        ]}]
        inventory = {"bank": {"NOUN", "VERB"}, "run": {"NOUN"}, "fast": {"ADV"}}
        lemmas = {"bank": {"NOUN"}, "run": {"VERB"}}
        report = evaluate(sentences, inventory, "en", lemmas)
        totals = report["totals"]
        self.assertEqual(totals["tokens"], 4)
        self.assertEqual(totals["seen_tokens"], 3)
        self.assertEqual(totals["oov_tokens"], 1)
        self.assertEqual(totals["gold_tag_in_candidates"], 2)
        self.assertEqual(totals["ambiguous_seen_tokens"], 1)
        self.assertAlmostEqual(totals["token_coverage"], 0.75)
        self.assertAlmostEqual(totals["gold_tag_hit_rate_when_seen"], 2 / 3)
        self.assertEqual(totals["gold_lemma_seen"], 2)
        self.assertEqual(totals["gold_lemma_and_upos_hit"], 2)
        self.assertAlmostEqual(totals["gold_lemma_coverage"], 0.5)
        self.assertAlmostEqual(totals["gold_lemma_upos_candidate_recall"], 0.5)
        ambiguity = report["candidate_ambiguity"]
        self.assertEqual(ambiguity["single_candidate_seen_tokens"], 2)
        self.assertEqual(ambiguity["multi_candidate_seen_tokens"], 1)
        self.assertEqual(ambiguity["candidate_label_count_distribution"], {"1": 2, "2": 1})
        self.assertAlmostEqual(ambiguity["mean_candidate_labels_when_seen"], 4 / 3)
        self.assertFalse(ambiguity["candidate_precision_measured"])

    def test_identical_physical_shards_are_deduplicated_for_evaluation(self):
        record = {"entries": [
            {"lemma": "bank", "part_of_speech": "noun", "forms": []},
        ]}
        with TemporaryDirectory() as temp:
            first = Path(temp) / "batch-000001-first.jsonl.gz"
            second = Path(temp) / "batch-000001-retry-copy.jsonl.gz"
            with gzip.open(first, "wt", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")
            second.write_bytes(first.read_bytes())
            evidence = load_candidate_evidence(temp)
        self.assertEqual(evidence["physical_shard_count"], 2)
        self.assertEqual(evidence["shard_count"], 1)
        self.assertEqual(evidence["duplicate_shard_count"], 1)
        self.assertEqual(evidence["entry_count"], 1)
        self.assertEqual(evidence["forms"]["bank"], {"NOUN"})
        self.assertEqual(len(evidence["shard_content_sha256"]), 1)

    def test_morphology_candidates_are_compared_with_pinned_ud_features(self):
        sentences = [{"tokens": [
            {"form": "books", "lemma": "book", "upos": "NOUN", "feats": (("Number", "Plur"),)},
            {"form": "better", "lemma": "good", "upos": "ADJ", "feats": (("Degree", "Cmp"),)},
            {"form": "fast", "lemma": "fast", "upos": "ADV", "feats": (("Degree", "Pos"),)},
        ]}]
        inventory = {
            "books": {("NOUN", "Number", "Plur")},
            "better": {("ADJ", "Degree", "Cmp")},
            "fast": {("ADV", "Degree", "Cmp")},
        }
        report = evaluate_morphology(sentences, inventory)
        totals = report["totals"]
        self.assertEqual(totals["gold_feature_instances"], 2)
        self.assertEqual(totals["candidate_feature_instances"], 3)
        self.assertEqual(totals["matched_feature_instances"], 2)
        self.assertAlmostEqual(totals["candidate_pool_precision"], 2 / 3)
        self.assertAlmostEqual(totals["candidate_recall"], 1.0)
        self.assertAlmostEqual(totals["gold_feature_token_recall"], 1.0)

    def test_lemma_metrics_are_optional_for_legacy_callers(self):
        report = evaluate(
            [{"tokens": [{"form": "bank", "upos": "NOUN"}]}],
            {"bank": {"NOUN"}}, "en"
        )
        self.assertIsNone(report["lexicon_lemma_count"])
        self.assertIsNone(report["totals"]["gold_lemma_coverage"])

    def test_empty_shard_directory_fails_closed(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                load_candidate_evidence(temp)

    def test_malformed_entries_container_fails_closed(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "bad.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                stream.write(json.dumps({"entries": {}}) + "\n")
            with self.assertRaisesRegex(ValueError, "entries is not a list"):
                load_candidate_evidence(temp)


if __name__ == "__main__":
    unittest.main()
