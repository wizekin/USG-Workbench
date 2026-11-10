"""Regression tests for Phase 2 Step 2.8 structured query interface."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from tools.semantic_query_interface_v1_0_0.interface import QueryInterface

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/query-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
FIXTURE_SCHEMA = json.loads((ROOT / "benchmarks/semantic-reasoning/query-v1.0.0/fixtures.schema.json").read_text(encoding="utf-8"))
EXECUTOR_FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
EVIDENCE_FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/evidence-v1.0.0/fixtures.json").read_text(encoding="utf-8"))


def resolve_document(reference):
    if reference["benchmark_id"] == "USG-INFERENCE-EXECUTOR-BENCHMARK":
        bundle = EXECUTOR_FIXTURES
    elif reference["benchmark_id"] == "USG-EVIDENCE-ASSESSMENT-BENCHMARK":
        bundle = EVIDENCE_FIXTURES
    else:
        raise AssertionError("unregistered benchmark reference")
    matches = [item for item in bundle["fixtures"] if item["id"] == reference["fixture_id"]]
    if len(matches) != 1:
        raise AssertionError("fixture reference must resolve exactly once")
    return matches[0]["document"]


class Phase2QueryInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interface = QueryInterface()

    def test_query_benchmark_schema_and_every_fixture(self):
        self.assertEqual(list(Draft202012Validator(FIXTURE_SCHEMA).iter_errors(FIXTURES)), [])
        self.assertEqual(len(FIXTURES["fixtures"]), 13)
        for fixture in FIXTURES["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                document = resolve_document(fixture["document_ref"])
                result = self.interface.run(document, fixture["query"])
                expected = fixture["expected"]
                for field in ("completion_status", "goal_status"):
                    self.assertEqual(result[field], expected[field])
                if "candidate_count" in expected:
                    self.assertEqual(len(result["inference_candidates"]), expected["candidate_count"])
                if "derivation_count" in expected:
                    self.assertEqual(len(result["derivations"]), expected["derivation_count"])
                if "source_assertion_count" in expected:
                    self.assertEqual(len(result["source_assertions"]), expected["source_assertion_count"])
                if "conflict_count" in expected:
                    self.assertEqual(len(result["conflicts"]), expected["conflict_count"])

    def test_derived_candidate_has_derivation_trace_and_no_truth_promotion(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "QUERY-DERIVED-MP-001")
        result = self.interface.run(resolve_document(fixture["document_ref"]), fixture["query"])
        self.assertEqual(result["goal_status"], "DERIVED_NOT_VERIFIED")
        self.assertEqual(result["derivations"][0]["rule_id"], "benchmark-rule:modus-ponens")
        self.assertFalse(result["safety"]["truth_promotion"])

    def test_no_match_is_open_world_not_false(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "QUERY-OPEN-WORLD-NO-MATCH-001")
        result = self.interface.run(resolve_document(fixture["document_ref"]), fixture["query"])
        self.assertEqual(result["goal_status"], "NOT_ESTABLISHED")
        self.assertFalse(result["safety"]["absence_means_false"])
        self.assertTrue(result["unresolved_questions"])

    def test_conflict_projection_preserves_both_assertions_without_winner(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "QUERY-EXACT-CONFLICT-001")
        result = self.interface.run(resolve_document(fixture["document_ref"]), fixture["query"])
        self.assertEqual(result["goal_status"], "CONFLICTING")
        self.assertEqual(result["conflicts"][0]["winner_selection"], "FORBIDDEN")

    def test_query_is_exact_and_deterministic(self):
        fixture = FIXTURES["fixtures"][0]
        document = resolve_document(fixture["document_ref"])
        first = self.interface.run(document, fixture["query"])
        second = self.interface.run(document, fixture["query"])
        self.assertEqual(first, second)
        self.assertEqual(first["goal"]["expression_ref"], "expr-b")


if __name__ == "__main__":
    unittest.main()
