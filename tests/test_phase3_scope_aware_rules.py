"""Adversarial tests for Phase 3 Step 3.4 scope-aware rules."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.scope_aware_rules_v1_0_0 import ScopeAwareRuleAnalyzer

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)


def base_document():
    item = next(x for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")
    return deepcopy(item["document"])


class ScopeAwareRuleTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = ScopeAwareRuleAnalyzer()

    def test_if_preserves_exact_antecedent_and_consequent_order(self):
        doc = base_document()
        result = self.analyzer.analyze(doc)
        frame = next(x for x in result["operator_frames"] if x["operator"] == "IMPLIES")
        self.assertEqual(frame["conditional_kind"], "IF")
        self.assertEqual(frame["antecedent_ref"], "expr-a")
        self.assertEqual(frame["consequent_ref"], "expr-b")
        self.assertEqual(frame["inference_policy"], "REQUIRES_SEPARATE_ENABLED_RULE_AND_MATCHED_PREMISES")

    def test_not_preserves_nested_scope_without_flattening(self):
        doc = base_document()
        doc["expressions"].append({
            "id": "expr-not-a", "op": "NOT", "sort": "PROP",
            "operandRefs": ["expr-a"], "params": {}, "interpretationStatus": "RESOLVED"
        })
        doc["expressions"].append({
            "id": "expr-not-not-a", "op": "NOT", "sort": "PROP",
            "operandRefs": ["expr-not-a"], "params": {}, "interpretationStatus": "RESOLVED"
        })
        result = self.analyzer.analyze(doc)
        frames = {x["expression_ref"]: x for x in result["operator_frames"]}
        self.assertEqual(frames["expr-not-a"]["negated_expression_ref"], "expr-a")
        self.assertEqual(frames["expr-not-not-a"]["negated_expression_ref"], "expr-not-a")
        self.assertFalse(result["safety"]["operator_scope_flattened"])

    def test_unless_requires_explicit_adapter_mapping_and_never_infers_from_absence(self):
        doc = base_document()
        doc["expressions"].append({
            "id": "expr-unless", "op": "COND", "sort": "PROP",
            "operandRefs": ["expr-a", "expr-b"],
            "params": {"conditionalKind": "UNLESS"},
            "interpretationStatus": "RESOLVED"
        })
        result = self.analyzer.analyze(doc)
        frame = next(x for x in result["operator_frames"] if x["expression_ref"] == "expr-unless")
        self.assertEqual(frame["conditional_kind"], "UNLESS")
        self.assertEqual(frame["consequent_ref"], "expr-a")
        self.assertEqual(frame["exception_ref"], "expr-b")
        self.assertIn("EXCEPTION_ABSENCE_NEVER_ASSERTS_CONSEQUENT", frame["inference_policy"])
        self.assertFalse(result["safety"]["exception_absence_entails_consequent"])

    def test_unsupported_conditional_shape_abstains(self):
        doc = base_document()
        doc["expressions"].append({
            "id": "expr-cond-unknown", "op": "COND", "sort": "PROP",
            "operandRefs": ["expr-a", "expr-b"], "params": {},
            "interpretationStatus": "RESOLVED"
        })
        result = self.analyzer.analyze(doc)
        frame = next(x for x in result["operator_frames"] if x["expression_ref"] == "expr-cond-unknown")
        self.assertEqual(frame["scope_status"], "UNSUPPORTED")
        self.assertIn("UNLESS_REPRESENTATION_UNSUPPORTED", frame["diagnostics"])

    def test_attribution_binding_is_preserved_and_never_transferred(self):
        doc = base_document()
        doc["referents"].append({"id": "speaker-x", "label": "Speaker X"})
        doc["assertions"][0]["commitment"] = "ATTRIBUTED"
        doc["assertions"][0]["attributedToRef"] = "speaker-x"
        result = self.analyzer.analyze(doc)
        binding = next(x for x in result["assertion_bindings"] if x["assertion_ref"] == "assert-a")
        self.assertEqual(binding["commitment"], "ATTRIBUTED")
        self.assertEqual(binding["attributed_to_ref"], "speaker-x")
        self.assertFalse(result["safety"]["attribution_transfer"])

    def test_different_contexts_and_commitments_remain_distinct(self):
        doc = base_document()
        doc["assertions"][0]["evaluationContext"]["contextRef"] = "ctx-other"
        doc["assertions"][0]["commitment"] = "NONE"
        result = self.analyzer.analyze(doc)
        bindings = {x["assertion_ref"]: x for x in result["assertion_bindings"]}
        self.assertEqual(bindings["assert-a"]["context_ref"], "ctx-other")
        self.assertEqual(bindings["assert-imp"]["context_ref"], "ctx-world")
        self.assertNotEqual(bindings["assert-a"]["commitment"], bindings["assert-imp"]["commitment"])

    def test_invalid_document_returns_invalid_without_partial_frames(self):
        doc = base_document()
        doc["expressions"][0]["op"] = "NOT"
        result = self.analyzer.analyze(doc)
        self.assertEqual(result["completion_status"], "INVALID_INPUT")
        self.assertEqual(result["operator_frames"], [])

    def test_deterministic_and_input_immutable(self):
        doc = base_document()
        before = deepcopy(doc)
        first = self.analyzer.analyze(doc)
        second = self.analyzer.analyze(doc)
        self.assertEqual(first, second)
        self.assertEqual(doc, before)
        self.assertFalse(first["safety"]["truth_promotion"])


if __name__ == "__main__":
    unittest.main()
