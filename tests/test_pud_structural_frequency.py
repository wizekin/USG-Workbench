"""Tests for reproducible bilingual PUD structural-frequency diagnostics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.open_world_evaluation import pud_structural_frequency as sf


CONLLU = """# sent_id = s1
# text = Researchers measured samples which changed.
1\tResearchers\tresearcher\tNOUN\tNNS\t_\t2\tnsubj\t_\t_
2\tmeasured\tmeasure\tVERB\tVBD\t_\t0\troot\t_\t_
3\tsamples\tsample\tNOUN\tNNS\t_\t2\tobj\t_\t_
4\twhich\twhich\tPRON\tWDT\t_\t5\tnsubj\t_\t_
5\tchanged\tchange\tVERB\tVBD\t_\t3\tacl:relcl\t_\t_

# sent_id = s2
# text = The result was stable.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\tresult\tresult\tNOUN\tNN\t_\t0\troot\t_\t_
3\twas\tbe\tAUX\tVBD\t_\t2\tcop\t_\t_
4\tstable\tstable\tADJ\tJJ\t_\t2\txcomp\t_\t_

# sent_id = s3
# text = The sample was measured.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\tsample\tsample\tNOUN\tNN\t_\t4\tnsubj:pass\t_\t_
3\twas\tbe\tAUX\tVBD\t_\t4\taux:pass\t_\t_
4\tmeasured\tmeasure\tVERB\tVBN\t_\t0\troot\t_\t_

# sent_id = s4
# text = They reported that the result improved.
1\tThey\tthey\tPRON\tPRP\t_\t2\tnsubj\t_\t_
2\treported\treport\tVERB\tVBD\t_\t0\troot\t_\t_
3\tthat\tthat\tSCONJ\tIN\t_\t6\tmark\t_\t_
4\tthe\tthe\tDET\tDT\t_\t5\tdet\t_\t_
5\tresult\tresult\tNOUN\tNN\t_\t6\tnsubj\t_\t_
6\timproved\timprove\tVERB\tVBD\t_\t2\tccomp\t_\t_

# sent_id = s5
# text = Contact a@example.org for details.
1\tContact\tcontact\tVERB\tVB\t_\t0\troot\t_\t_
2\ta@example.org\ta@example.org\tNOUN\tNN\t_\t1\tobj\t_\t_
"""


class PudStructuralFrequencyTests(unittest.TestCase):
    def test_counts_sentence_level_proxies_and_active_order(self):
        result = sf.analyze_language(
            CONLLU.encode("utf-8"),
            language="en",
            source={
                "repository": "UniversalDependencies/UD_English-PUD",
                "commit": "commit",
                "file": "test.conllu",
                "blob_sha": "blob",
            },
        )
        population = result["population"]
        counts = result["construction_counts"]
        self.assertEqual(population["source_sentence_count"], 5)
        self.assertEqual(population["privacy_rejected_count"], 1)
        self.assertEqual(population["analyzed_sentence_count"], 4)
        self.assertEqual(counts["relative_clause_anywhere"]["count"], 1)
        self.assertEqual(counts["active_transitive_root"]["count"], 1)
        self.assertEqual(counts["copular_predicate_root"]["count"], 1)
        self.assertEqual(counts["clause_complement_root"]["count"], 2)
        self.assertEqual(counts["clause_complement_anywhere"]["count"], 2)
        self.assertEqual(counts["passive_verb_root"]["count"], 1)
        self.assertEqual(result["active_transitive_surface_order"]["SVO"]["count"], 1)

    def test_deduplication_precedes_frequency_denominators(self):
        duplicate = CONLLU.replace(
            "# text = The result was stable.",
            "# text = Researchers measured samples which changed.",
        )
        result = sf.analyze_language(
            duplicate.encode("utf-8"),
            language="en",
            source={"repository": "r", "commit": "c", "file": "f", "blob_sha": "b"},
        )
        self.assertEqual(result["population"]["duplicate_count"], 1)
        self.assertEqual(
            result["population"]["analyzed_sentence_count"],
            result["population"]["unique_screened_sentence_count"],
        )

    def test_git_blob_hash_matches_git_object_format(self):
        payload = b"hello\n"
        expected = hashlib.sha1(b"blob 6\0" + payload).hexdigest()
        self.assertEqual(sf.git_blob_sha1(payload), expected)

    def test_report_checks_pinned_source_and_manifest_boundaries(self):
        payload = CONLLU.replace(
            "# text = Contact a@example.org for details.",
            "# text = The final result was stable.",
        ).encode("utf-8")
        fake_sources = {
            language: {
                "repository": f"example/{language}",
                "commit": f"commit-{language}",
                "file": f"{language}.conllu",
                "blob_sha": sf.git_blob_sha1(payload),
                "treebank": f"treebank-{language}",
                "language": language,
            }
            for language in ("en", "ar")
        }
        manifest_sources = {
            language: {
                **fake_sources[language],
                "content_sha256": hashlib.sha256(payload).hexdigest(),
                "sentence_count": 5,
            }
            for language in ("en", "ar")
        }
        manifest = {
            "dataset_id": "UD-PUD-EN-AR",
            "license": "CC BY-SA 3.0",
            "semantic_gold": {"available": False},
            "privacy_review": {"status": "approved_for_bounded_internal_evaluation"},
            "sources": manifest_sources,
            "translation_profile": {"arabic": "translated"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(sf, "SOURCES", fake_sources):
                report = sf.build_report(path, fetcher=lambda url: payload)
        self.assertEqual(report["contract"], sf.REPORT_CONTRACT)
        self.assertEqual(report["evidence_type"], "ud_syntactic_proxy_not_semantic_gold")
        self.assertFalse(report["semantic_gold"]["available"])
        self.assertEqual(set(report["languages"]), {"en", "ar"})

    def test_report_rejects_semantic_gold_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source-manifest.json"
            path.write_text(json.dumps({
                "license": "CC BY-SA 3.0",
                "semantic_gold": {"available": True},
                "privacy_review": {"status": "approved_for_bounded_internal_evaluation"},
                "sources": {},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no-semantic-gold"):
                sf.build_report(path, fetcher=lambda url: b"")


if __name__ == "__main__":
    unittest.main()
