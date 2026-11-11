from __future__ import annotations

import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.usg_external_lexical_v0_1_0.pud_evaluation import (
    evaluate, load_candidate_inventory, normalize,
)


class ExternalLexicalPudEvaluationTests(unittest.TestCase):
    def test_normalization_is_language_aware(self):
        self.assertEqual(normalize("Bank", "en"), "bank")
        self.assertEqual(normalize("بنك", "ar"), "بنك")

    def test_reads_crawler_shards_and_maps_observed_forms(self):
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
            inventory = load_candidate_inventory(temp)
        self.assertEqual(inventory["bank"], {"NOUN"})
        self.assertEqual(inventory["banks"], {"NOUN"})
        self.assertEqual(inventory["run"], {"VERB"})
        self.assertNotIn("unknown", inventory)

    def test_reports_oov_ambiguity_and_gold_candidate_recall(self):
        sentences = [{"tokens": [
            {"form": "bank", "upos": "NOUN"},
            {"form": "run", "upos": "VERB"},
            {"form": "mystery", "upos": "NOUN"},
            {"form": "fast", "upos": "ADV"},
        ]}]
        inventory = {"bank": {"NOUN", "VERB"}, "run": {"NOUN"}, "fast": {"ADV"}}
        report = evaluate(sentences, inventory, "en")
        totals = report["totals"]
        self.assertEqual(totals["tokens"], 4)
        self.assertEqual(totals["seen_tokens"], 3)
        self.assertEqual(totals["oov_tokens"], 1)
        self.assertEqual(totals["gold_tag_in_candidates"], 2)
        self.assertEqual(totals["ambiguous_seen_tokens"], 1)
        self.assertAlmostEqual(totals["token_coverage"], 0.75)
        self.assertAlmostEqual(totals["gold_tag_hit_rate_when_seen"], 2 / 3)

    def test_empty_shard_directory_fails_closed(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                load_candidate_inventory(temp)


if __name__ == "__main__":
    unittest.main()
