"""Regression tests for Phase 2 Step 2.7 evidence and conflict assessment."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from tools.semantic_evidence_assessment_v1_0_0.assessor import EvidenceAssessmentEngine

ROOT = Path(__file__).resolve().parents[1]
DOC_SCHEMA = json.loads((ROOT / "specifications/usg-sem-1.0.schema.json").read_text(encoding="utf-8"))
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/evidence-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
FIXTURE_SCHEMA = json.loads((ROOT / "benchmarks/semantic-reasoning/evidence-v1.0.0/fixtures.schema.json").read_text(encoding="utf-8"))


class Phase2EvidenceAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = EvidenceAssessmentEngine()

    def test_benchmark_schema_and_all_canonical_documents(self):
        self.assertEqual(list(Draft202012Validator(FIXTURE_SCHEMA).iter_errors(FIXTURES)), [])
        self.assertEqual(len(FIXTURES["fixtures"]), 13)
        for fixture in FIXTURES["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                self.assertEqual(list(Draft202012Validator(DOC_SCHEMA).iter_errors(fixture["document"])), [])
                result = self.engine.assess(fixture["document"], fixture["task"])
                expected = fixture["expected"]
                if "alignment" in expected:
                    self.assertEqual(result["alignment_assessments"][0]["computed_alignment_status"], expected["alignment"])
                if "support" in expected:
                    self.assertEqual(result["semantic_support_assessments"][0]["assessed_status"], expected["support"])
                if "relation" in expected:
                    self.assertEqual(result["relation_claims"][0]["assessed_status"], expected["relation"])
                if "conflicts" in expected:
                    self.assertEqual(len(result["conflicts"]), expected["conflicts"])
                if "independence" in expected:
                    self.assertEqual(result["corroboration_assessments"][0]["source_independence"], expected["independence"])
                    self.assertEqual(result["corroboration_assessments"][0]["corroboration_status"], expected["corroboration"])
                if "external" in expected:
                    self.assertEqual(result["external_verification"][0]["assessed_status"], expected["external"])

    def test_exact_quote_alignment_does_not_establish_semantic_support(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-ALIGN-EXACT-001")
        result = self.engine.assess(fixture["document"], fixture["task"])
        self.assertEqual(result["alignment_assessments"][0]["computed_alignment_status"], "EXACT")
        self.assertEqual(result["semantic_support_assessments"][0]["assessed_status"], "NOT_ESTABLISHED")
        self.assertFalse(result["safety"]["truth_promotion"])

    def test_declared_rule_supported_label_is_not_promoted(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-DECLARED-RULE-SUPPORT-001")
        result = self.engine.assess(fixture["document"], fixture["task"])
        self.assertEqual(result["semantic_support_assessments"][0]["assessed_status"], "DECLARED_RULE_SUPPORTED_UNVERIFIED")

    def test_relation_type_does_not_verify_contradiction(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-RELATION-CONTRADICTS-UNVERIFIED-001")
        result = self.engine.assess(fixture["document"], fixture["task"])
        self.assertEqual(result["relation_claims"][0]["relation_type"], "CONTRADICTS")
        self.assertEqual(result["relation_claims"][0]["assessed_status"], "UNVERIFIED_RELATION_CLAIM")

    def test_conflict_requires_exact_context_and_attribution(self):
        same = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-EXACT-COMPLEMENT-CONFLICT-001")
        other_context = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-CONTEXT-ISOLATED-001")
        other_attribution = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-ATTRIBUTION-ISOLATED-001")
        self.assertEqual(len(self.engine.assess(same["document"], same["task"])["conflicts"]), 1)
        self.assertEqual(self.engine.assess(other_context["document"], other_context["task"])["conflicts"], [])
        self.assertEqual(self.engine.assess(other_attribution["document"], other_attribution["task"])["conflicts"], [])

    def test_source_diversity_does_not_establish_independence_or_corroboration(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-MULTIPLE-SOURCES-NO-INDEPENDENCE-001")
        result = self.engine.assess(fixture["document"], fixture["task"])
        assessment = result["corroboration_assessments"][0]
        self.assertEqual(assessment["source_diversity"], "MULTIPLE_SOURCE_RECORDS")
        self.assertEqual(assessment["source_independence"], "NOT_ESTABLISHED")
        self.assertEqual(assessment["corroboration_status"], "NOT_ESTABLISHED")

    def test_external_verification_declaration_is_not_verification(self):
        fixture = next(x for x in FIXTURES["fixtures"] if x["id"] == "EV-EXTERNAL-VERIFICATION-DECLARED-001")
        result = self.engine.assess(fixture["document"], fixture["task"])
        self.assertEqual(result["external_verification"][0]["declared_result"], "VERIFIED")
        self.assertEqual(result["external_verification"][0]["assessed_status"], "DECLARED_UNVERIFIED")

    def test_assessment_is_deterministic_and_does_not_mutate_document(self):
        fixture = FIXTURES["fixtures"][0]
        document = copy.deepcopy(fixture["document"])
        first = self.engine.assess(document, fixture["task"])
        second = self.engine.assess(document, fixture["task"])
        self.assertEqual(first, second)
        self.assertEqual(document, fixture["document"])


if __name__ == "__main__":
    unittest.main()
