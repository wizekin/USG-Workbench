"""Tests for the licensed PUD naturalistic evaluation population."""
from __future__ import annotations

import unittest

from tools.open_world_evaluation.pud_naturalistic_pilot import (
    build_naturalistic_cases,
    parse_conllu_sentences,
    screen_public_sentence,
    select_sentences,
)


TARGETS = [
    {
        "component_id": "phase5-bounded-interpreter",
        "component_version": "0.2.0",
        "entry_point": "tools.usg_interpretation_v0_2_0",
        "interface": "python_api",
        "contract_versions": ["USG-INTERPRET/0.2.0"],
        "resource_limits": {"wall_time_seconds": 15, "memory_megabytes": 512},
    },
    {
        "component_id": "js-semantic-workbench-v054",
        "component_version": "0.5.4",
        "entry_point": "implementations/semantic-workbench-js/v0.5.4",
        "interface": "browser_ui",
        "contract_versions": ["USG-WB-SEM/1.0"],
        "resource_limits": {"wall_time_seconds": 45, "memory_megabytes": 4096},
    },
]


class PudNaturalisticPilotTests(unittest.TestCase):
    def test_conllu_parser_extracts_sentence_id_and_verbatim_text(self):
        conllu = """# sent_id = n01001001
# text = A researcher measured the sample.
1\tA\ta\tDET\tDT\t_\t2\tdet\t_\t_
2\tresearcher\tresearcher\tNOUN\tNN\t_\t3\tnsubj\t_\t_
3\tmeasured\tmeasure\tVERB\tVBD\t_\t0\troot\t_\t_
4\tthe\tthe\tDET\tDT\t_\t5\tdet\t_\t_
5\tsample\tsample\tNOUN\tNN\t_\t3\tobj\t_\t_

# sent_id = n01001002
# text = The sample was small.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\tsample\tsample\tNOUN\tNN\t_\t3\tnsubj\t_\t_
3\twas\tbe\tAUX\tVBD\t_\t0\troot\t_\t_
4\tsmall\tsmall\tADJ\tJJ\t_\t3\txcomp\t_\t_
"""
        sentences = parse_conllu_sentences(conllu)
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0]["sentence_id"], "n01001001")
        self.assertEqual(sentences[0]["text"], "A researcher measured the sample.")

    def test_privacy_screen_rejects_direct_contact_patterns(self):
        self.assertTrue(screen_public_sentence("A researcher measured the sample.")[0])
        self.assertEqual(screen_public_sentence("Contact a@example.org")[1], "email_pattern")
        self.assertEqual(screen_public_sentence("See https://example.org")[1], "url_pattern")

    def test_selection_is_deterministic_and_deduplicated(self):
        rows = [
            {"sentence_id": "s1", "text": "A sample was measured."},
            {"sentence_id": "s2", "text": "A   sample was measured."},
            {"sentence_id": "s3", "text": "The result was stable."},
        ]
        first, stats = select_sentences(rows, language="en", sample_count=2)
        second, _ = select_sentences(rows, language="en", sample_count=2)
        self.assertEqual(first, second)
        self.assertEqual(stats["duplicate_count"], 1)
        self.assertEqual(stats["selected_count"], 2)

    def test_cases_are_naturalistic_unlabeled_and_source_traceable(self):
        groups = {
            "en": [{"sentence_id": "n01001001", "text": "A researcher measured the sample."}],
            "ar": [{"sentence_id": "n02001001", "text": "قام الباحث بقياس العينة."}],
        }
        cases, manifest = build_naturalistic_cases(
            groups,
            targets=TARGETS,
            sample_per_language=1,
            created_at="2026-11-12T00:00:00Z",
            retrieved_at="2026-11-12T00:00:00Z",
            source_file_digests={"en": "a" * 64, "ar": "b" * 64},
            target_matrix=True,
        )
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(case["population"] == "naturalistic" for case in cases))
        self.assertTrue(all(case["oracle"] == {"type": "none", "independent": False} for case in cases))
        self.assertTrue(all(case["source"]["kind"] == "open_license_dataset" for case in cases))
        self.assertTrue(all(case["source"]["license_status"] == "approved" for case in cases))
        self.assertTrue(all(case["source"]["privacy_review_status"] == "approved" for case in cases))
        self.assertTrue(all(case["taxonomy"]["unclassified"] for case in cases))
        self.assertTrue(all(case["source"]["source_url"].startswith("https://github.com/UniversalDependencies/") for case in cases))
        self.assertFalse(manifest["semantic_gold"]["available"])
        self.assertIn("All Arabic PUD sentences are translations", manifest["translation_profile"]["arabic"])
        self.assertEqual(manifest["license"], "CC BY-SA 3.0")
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))


if __name__ == "__main__":
    unittest.main()
