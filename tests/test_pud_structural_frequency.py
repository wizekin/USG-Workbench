"""Tests for the PUD structural-frequency diagnostic boundary and counts."""
from __future__ import annotations

import hashlib
import json
import unittest

from tools.open_world_evaluation.pud_naturalistic_pilot import _git_blob_sha1
from tools.open_world_evaluation.pud_structural_frequency import build_structural_frequency_report


def _metadata(language: str) -> dict:
    return {
        "repository": (
            "UniversalDependencies/UD_English-PUD"
            if language == "en"
            else "UniversalDependencies/UD_Arabic-PUD"
        ),
        "commit": "a" * 40 if language == "en" else "b" * 40,
        "file": "en_pud-ud-test.conllu" if language == "en" else "ar_pud-ud-test.conllu",
        "git_blob_sha1": "c" * 40,
        "readme_sha1": "d" * 40,
        "license_blob_sha1": "e" * 40,
        "git_blob_sha1_verified": True,
        "readme_blob_sha1_verified": True,
        "license_blob_sha1_verified": True,
        "content_sha256": "f" * 64,
        "license": "CC BY-SA 3.0",
        "sentence_count": 1000,
        "syntactic_word_count": 21000 if language == "en" else 20700,
    }


class PudStructuralFrequencyTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {"en": _metadata("en"), "ar": _metadata("ar")}
        self.cases = {
            "en": [
                {"language": "en", "construction": "en.nominal.adjective_modifier"},
                {"language": "en", "construction": "en.nominal.adjective_modifier"},
                {"language": "en", "construction": "en.genitive.of_phrase"},
            ],
            "ar": [
                {"language": "ar", "construction": "ar.nominal.adjective_modifier"},
                {"language": "ar", "construction": "ar.prepositional.nominal_modifier"},
            ],
        }

    def test_counts_are_separate_by_language_and_family(self):
        report = build_structural_frequency_report(
            cases_by_language=self.cases,
            dataset_metadata=self.metadata,
            generated_at="2026-11-13T19:00:00Z",
        )
        self.assertEqual(
            report["cross_language_family_counts"]["nominal_adjective_modifier"]["language_counts"],
            {"en": 2, "ar": 1},
        )
        self.assertEqual(report["source_profiles"]["en"]["eligible_structural_case_count"], 3)
        self.assertEqual(report["source_profiles"]["ar"]["eligible_structural_case_count"], 2)

    def test_candidate_is_annotation_only_and_not_semantic_gold(self):
        report = build_structural_frequency_report(
            cases_by_language=self.cases,
            dataset_metadata=self.metadata,
            generated_at="2026-11-13T19:00:00Z",
        )
        self.assertEqual(
            report["candidate_selection"]["status"],
            "candidate_for_SYS09_independent_annotation",
        )
        self.assertFalse(report["interpretation_boundary"]["ud_annotations_are_usg_semantic_gold"])
        self.assertFalse(report["interpretation_boundary"]["runtime_promotion_allowed"])

    def test_report_is_deterministic_and_contains_no_sentence_text(self):
        first = build_structural_frequency_report(
            cases_by_language=self.cases,
            dataset_metadata=self.metadata,
            generated_at="2026-11-13T19:00:00Z",
        )
        second = build_structural_frequency_report(
            cases_by_language=self.cases,
            dataset_metadata=self.metadata,
            generated_at="2026-11-13T19:00:00Z",
        )
        self.assertEqual(first, second)
        self.assertNotIn('"text"', json.dumps(first))

    def test_missing_language_and_mismatched_case_are_rejected(self):
        with self.assertRaises(ValueError):
            build_structural_frequency_report(
                cases_by_language={"en": []},
                dataset_metadata=self.metadata,
                generated_at="2026-11-13T19:00:00Z",
            )
        invalid = {"en": [{"language": "ar", "construction": "en.nominal.adjective_modifier"}], "ar": []}
        with self.assertRaises(ValueError):
            build_structural_frequency_report(
                cases_by_language=invalid,
                dataset_metadata=self.metadata,
                generated_at="2026-11-13T19:00:00Z",
            )

    def test_empty_bilingual_counts_do_not_select_a_candidate(self):
        report = build_structural_frequency_report(
            cases_by_language={"en": [], "ar": []},
            dataset_metadata=self.metadata,
            generated_at="2026-11-13T19:00:00Z",
        )
        self.assertEqual(
            report["candidate_selection"]["status"],
            "insufficient_bilingual_structural_evidence",
        )

    def test_git_blob_hash_verification_uses_git_object_header(self):
        payload = b"hello\n"
        expected = hashlib.sha1(b"blob 6\0hello\n").hexdigest()
        self.assertEqual(_git_blob_sha1(payload), expected)


if __name__ == "__main__":
    unittest.main()
