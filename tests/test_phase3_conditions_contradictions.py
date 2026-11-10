"""Tests for Phase 3 Step 3.5 conditions and contradiction services."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.document_analysis_services_v1_0_0 import DocumentAnalysisService

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)


def base_document():
    item = next(x for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")
    return deepcopy(item["document"])


class DocumentAnalysisServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = DocumentAnalysisService()

    def test_if_condition_map_preserves_exact_operands_and_assertion_links(self):
        doc = base_document()
        result = self.service.conditions(doc)
        item = next(x for x in result["conditions"] if x["kind"] == "IF")
        self.assertEqual(item["antecedent_ref"], "expr-a")
        self.assertEqual(item["consequent_ref"], "expr-b")
        self.assertEqual(item["linked_assertion_refs"], ["assert-imp"])
        self.assertEqual(item["status"], "CONDITIONAL_STRUCTURE_ONLY")

    def test_unless_exception_map_does_not_treat_missing_exception_as_true(self):
        doc = base_document()
        doc["expressions"].append({
            "id": "expr-unless", "op": "COND", "sort": "PROP",
            "operandRefs": ["expr-b", "expr-c"],
            "params": {"conditionalKind": "UNLESS"},
            "interpretationStatus": "RESOLVED"
        })
        result = self.service.conditions(doc)
        item = next(x for x in result["exceptions"] if x["operator_expression_ref"] == "expr-unless")
        self.assertEqual(item["exception_ref"], "expr-c")
        self.assertEqual(item["consequent_ref"], "expr-b")
        self.assertEqual(item["status"], "EXPLICIT_EXCEPTION_LINK")
        self.assertFalse(result["safety"]["exception_absence_entails_consequent"])

    def test_nested_negation_is_returned_without_flattening(self):
        doc = base_document()
        doc["expressions"].extend([
            {"id":"expr-not-a","op":"NOT","sort":"PROP","operandRefs":["expr-a"],"params":{},"interpretationStatus":"RESOLVED"},
            {"id":"expr-not-not-a","op":"NOT","sort":"PROP","operandRefs":["expr-not-a"],"params":{},"interpretationStatus":"RESOLVED"},
        ])
        result = self.service.conditions(doc)
        negations = {x["operator_expression_ref"]: x for x in result["negations"]}
        self.assertEqual(negations["expr-not-a"]["negated_expression_ref"], "expr-a")
        self.assertEqual(negations["expr-not-not-a"]["negated_expression_ref"], "expr-not-a")

    def test_direct_not_conflict_same_context_and_commitment(self):
        doc = base_document()
        doc["expressions"].append({
            "id":"expr-not-a","op":"NOT","sort":"PROP","operandRefs":["expr-a"],"params":{},"interpretationStatus":"RESOLVED"
        })
        doc["assertions"].append({
            "id":"assert-not-a","expressionRef":"expr-not-a","origin":"SOURCE_TEXT",
            "epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR",
            "evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"
        })
        result = self.service.contradictions(doc)
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual(result["conflicts"][0]["status"], "CONFLICTING")
        self.assertEqual(result["conflicts"][0]["winner_selection"], "FORBIDDEN")

    def test_different_context_blocks_conflict(self):
        doc = base_document()
        doc["expressions"].append({
            "id":"expr-not-a","op":"NOT","sort":"PROP","operandRefs":["expr-a"],"params":{},"interpretationStatus":"RESOLVED"
        })
        doc["assertions"].append({
            "id":"assert-not-a","expressionRef":"expr-not-a","origin":"SOURCE_TEXT",
            "epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR",
            "evaluationContext":{"kind":"WORLD","contextRef":"ctx-other"},"lifecycleStage":"STRUCTURED"
        })
        self.assertEqual(self.service.contradictions(doc)["conflicts"], [])

    def test_different_attribution_blocks_conflict(self):
        doc = base_document()
        doc["referents"].append({"id":"speaker-x","label":"Speaker X"})
        doc["expressions"].append({
            "id":"expr-not-a","op":"NOT","sort":"PROP","operandRefs":["expr-a"],"params":{},"interpretationStatus":"RESOLVED"
        })
        doc["assertions"].append({
            "id":"assert-not-a","expressionRef":"expr-not-a","origin":"SOURCE_TEXT",
            "epistemicStatus":"SOURCE_ASSERTED","commitment":"ATTRIBUTED","attributedToRef":"speaker-x",
            "evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"
        })
        self.assertEqual(self.service.contradictions(doc)["conflicts"], [])

    def test_disputed_and_unknown_statuses_are_not_silently_promoted(self):
        doc = base_document()
        doc["expressions"].append({
            "id":"expr-not-a","op":"NOT","sort":"PROP","operandRefs":["expr-a"],"params":{},"interpretationStatus":"RESOLVED"
        })
        doc["assertions"].append({
            "id":"assert-not-a","expressionRef":"expr-not-a","origin":"SOURCE_TEXT",
            "epistemicStatus":"UNKNOWN","commitment":"AUTHOR",
            "evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"
        })
        self.assertEqual(self.service.contradictions(doc)["conflicts"], [])

    def test_combined_result_pins_same_snapshot_and_preserves_evidence_axes(self):
        doc = base_document()
        original = deepcopy(doc)
        result = self.service.analyze(doc)
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(result["conditions"]["document_sha256"], result["contradictions"]["document_sha256"])
        self.assertIn("alignment_assessments", result["contradictions"]["evidence_axes"])
        self.assertIn("semantic_support_assessments", result["contradictions"]["evidence_axes"])
        self.assertEqual(doc, original)
        self.assertFalse(result["safety"]["evidence_axes_collapsed"])


if __name__ == "__main__":
    unittest.main()
