from __future__ import annotations

import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.usg_external_lexical_v0_1_0.pud_evaluation import (
    evaluate, load_candidate_evidence, load_candidate_inventory, normalize,
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

    def test_lemma_metrics_are_optional_for_legacy_callers(self):
        report = evaluate(
            [{"tokens": [{"form": "bank", "upos": "NOUN"}]},
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
