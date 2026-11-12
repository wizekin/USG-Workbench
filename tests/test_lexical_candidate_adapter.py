"""Contract and regression tests for candidate-only lexical adaptation."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.usg_external_lexical_v0_1_0.adapter import (
    CandidatePackageError,
    adapt_candidate_package,
    validate_candidate_package,
)
from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0.lexical import (
    LexicalAnalyzer,
    bundled_lexical_resource_v0_5_0,
)


def package():
    return {
        "contract": "USG-LEXICAL-CANDIDATES/0.1.0",
        "queried_form": "bank",
        "candidate_count": 2,
        "candidates": [
            {
                "candidate_id": "sense-river",
                "lemma": "bank",
                "language": "en",
                "part_of_speech": "noun",
                "definition": "Land alongside a river.",
                "examples": [],
                "features": [],
                "observed_forms": [{"form": "banks", "tags": ["plural"]}],
                "source_provider": "fixture",
                "source_id": "fixture-source",
                "source_entry_id": "bank-entry",
                "source_sense_id": "river-sense",
                "relations": [],
                "promotion_status": "candidate_only",
            },
            {
                "candidate_id": "sense-financial",
                "lemma": "bank",
                "language": "en",
                "part_of_speech": "noun",
                "definition": "A financial institution.",
                "examples": [],
                "features": [],
                "observed_forms": [],
                "source_provider": "fixture",
                "source_id": "fixture-source",
                "source_entry_id": "bank-entry",
                "source_sense_id": "financial-sense",
                "relations": [],
                "promotion_status": "candidate_only",
            },
        ],
        "entry_relations": [],
        "definition_pattern_observations": [],
        "semantic_candidate_graph": {"nodes": [], "edges": []},
        "source_provenance": [{"provider": "fixture", "license": "fixture-only"}],
        "validation": {"status": "valid", "promotion_allowed": False},
        "content_digest": "a" * 64,
        "promotion_allowed": False,
        "integration_note": "Candidate only.",
    }


class LexicalCandidateAdapterTests(unittest.TestCase):
    def test_valid_package_adapts_deterministically_without_promotion(self):
        candidate_package = package()
        result = adapt_candidate_package(candidate_package)
        self.assertEqual(result["contract"], "USG-LEXICAL-ADAPTER/0.1.0")
        self.assertEqual(result["source_contract"], candidate_package["contract"])
        self.assertEqual(result["source_content_digest"], "a" * 64)
        self.assertEqual(
            [item["candidate_id"] for item in result["candidates"]],
            ["sense-financial", "sense-river"],
        )
        self.assertFalse(result["promotion_allowed"])
        self.assertEqual(len(result["adapter_digest"]), 64)
        self.assertEqual(candidate_package["candidates"][0]["candidate_id"], "sense-river")

    def test_candidate_count_mismatch_is_rejected(self):
        candidate_package = package()
        candidate_package["candidate_count"] = 99
        result = validate_candidate_package(candidate_package)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("candidate_count_mismatch", {item["code"] for item in result["findings"]})
        with self.assertRaises(CandidatePackageError):
            adapt_candidate_package(candidate_package)

    def test_automatic_promotion_and_missing_provenance_are_rejected(self):
        candidate_package = package()
        candidate_package["promotion_allowed"] = True
        candidate_package["source_provenance"] = []
        result = validate_candidate_package(candidate_package)
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("promotion_boundary_violation", codes)
        self.assertIn("missing_source_provenance", codes)

    def test_duplicate_candidate_ids_and_missing_source_identity_are_rejected(self):
        candidate_package = package()
        candidate_package["candidates"][1]["candidate_id"] = "sense-river"
        candidate_package["candidates"][0]["source_sense_id"] = None
        result = validate_candidate_package(candidate_package)
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("duplicate_candidate_id", codes)
        self.assertIn("candidate_missing_source_sense_id", codes)

    def test_published_json_schema_accepts_valid_package(self):
        import jsonschema

        root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (root / "specifications" / "usg-lexical-candidates-0.1.0.schema.json").read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator(schema).validate(package())

    def test_oov_and_ambiguity_regressions_remain_explicit(self):
        analyzer = LexicalAnalyzer(bundled_lexical_resource_v0_5_0())
        source = ingest_source("The bank saw a flarble and zentropic object.", "en")
        result = analyzer.analyze(source)
        by_form = {
            item.token.surface_text.casefold(): item
            for item in result.tokens if item.token.kind == "WORD"
        }
        self.assertEqual(by_form["bank"].status, "AMBIGUOUS")
        self.assertGreaterEqual(len(by_form["bank"].candidates), 2)
        for form in ("flarble", "zentropic"):
            with self.subTest(form=form):
                self.assertEqual(by_form[form].status, "UNRESOLVED")
                self.assertEqual(by_form[form].candidates, ())

    def test_arabic_oov_remains_unresolved_without_invented_lemma(self):
        analyzer = LexicalAnalyzer(bundled_lexical_resource_v0_5_0())
        source = ingest_source("زغردةز", "ar")
        result = analyzer.analyze(source)
        words = [item for item in result.tokens if item.token.kind == "WORD"]
        self.assertEqual(len(words), 1)
        self.assertEqual(words[0].status, "UNRESOLVED")
        self.assertEqual(words[0].candidates, ())


if __name__ == "__main__":
    unittest.main()
