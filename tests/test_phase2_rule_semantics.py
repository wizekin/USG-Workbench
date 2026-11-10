"""Tests for Phase 2 Step 2.4 rule semantics and safety contract."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.semantic_rule_semantics_v1_0_0.validator import (
    DEFAULT_CONTRACT, DEFAULT_REGISTRY, DEFAULT_REGISTRY_SCHEMA, DEFAULT_SCHEMA,
    SemanticsValidationError, validate_semantics,
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Phase2RuleSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load(DEFAULT_CONTRACT)
        cls.registry = load(DEFAULT_REGISTRY)
        cls.schema = load(DEFAULT_SCHEMA)
        cls.registry_schema = load(DEFAULT_REGISTRY_SCHEMA)

    def test_semantics_contract_schema_and_registry_cross_validation_pass(self):
        report = validate_semantics(self.contract, self.registry, self.schema, self.registry_schema)
        self.assertTrue(report["valid"])
        self.assertEqual(report["rule_count"], 4)
        self.assertEqual(report["constraint_kind_count"], 19)
        self.assertFalse(report["execution_enabled"])

    def test_all_rule_model_constraint_kinds_have_formal_semantics(self):
        declared = set(self.registry_schema["$defs"]["constraint"]["properties"]["kind"]["enum"])
        defined = {item["kind"] for item in self.contract["constraint_semantics"]}
        self.assertEqual(declared, defined)

    def test_all_registry_diagnostics_are_catalogued(self):
        catalog = {item["code"] for item in self.contract["diagnostic_catalog"]}
        for rule in self.registry["rules"]:
            self.assertTrue(set(rule["diagnostics"]).issubset(catalog))
            self.assertTrue({item["failure_diagnostic"] for item in rule["constraints"]}.issubset(catalog))
            self.assertTrue({item["diagnostic"] for item in rule["non_applicability"]}.issubset(catalog))

    def test_applicability_outcomes_remain_distinct(self):
        codes = {item["code"] for item in self.contract["outcomes"]}
        self.assertEqual(codes, {
            "APPLICABLE", "NOT_APPLICABLE", "UNKNOWN", "UNRESOLVED", "AMBIGUOUS",
            "CONFLICTING", "UNSUPPORTED", "INVALID_INPUT", "RESOURCE_INTERRUPTED",
        })
        outcomes = {item["code"]: item for item in self.contract["outcomes"]}
        self.assertTrue(outcomes["APPLICABLE"]["may_create_conclusion_candidate"])
        for code, outcome in outcomes.items():
            if code != "APPLICABLE":
                self.assertFalse(outcome["may_create_conclusion_candidate"], code)

    def test_source_asserted_is_the_only_initially_eligible_status(self):
        policy = self.contract["assertion_eligibility_policies"][0]
        self.assertEqual(policy["token"], "RULE_ELIGIBLE_ASSERTION")
        self.assertEqual(policy["allowed_epistemic_statuses"], ["SOURCE_ASSERTED"])
        self.assertFalse(policy["inferred_premise_chaining_allowed"])
        blocked = {item["epistemic_status"]: item["outcome"] for item in policy["blocked_status_outcomes"]}
        self.assertEqual(blocked["DISPUTED"], "CONFLICTING")
        self.assertEqual(blocked["UNKNOWN"], "UNKNOWN")
        self.assertEqual(policy["missing_status_outcome"], "UNRESOLVED")
        self.assertEqual(policy["unknown_origin_outcome"], "UNKNOWN")
        self.assertEqual(
            {item["commitment"] for item in policy["commitment_rules"]},
            {"AUTHOR", "ATTRIBUTED", "NONE"},
        )
        self.assertTrue(next(item for item in policy["commitment_rules"] if item["commitment"] == "ATTRIBUTED")["require_attributed_to_ref"])

    def test_conflict_policy_forbids_automatic_winner_selection(self):
        policy = self.contract["conflict_policy"]
        self.assertEqual(policy["winner_selection"], "FORBIDDEN")
        self.assertEqual(policy["recency_tiebreak"], "FORBIDDEN")
        self.assertEqual(policy["frequency_tiebreak"], "FORBIDDEN")
        self.assertEqual(policy["confidence_tiebreak"], "FORBIDDEN")

    def test_open_world_is_default_and_closed_world_is_task_scoped(self):
        policy = self.contract["open_world_policy"]
        self.assertEqual(policy["default"], "OPEN")
        self.assertFalse(policy["absence_means_negation"])
        self.assertFalse(policy["scope_is_global"])
        self.assertGreaterEqual(len(policy["closed_world_requires"]), 5)

    def test_scope_axes_are_all_explicit(self):
        axes = {item["axis"] for item in self.contract["scope_policies"]}
        self.assertEqual(axes, {
            "typed_identity", "context", "attribution", "polarity", "modality",
            "quantifier", "temporal", "roles", "definition_grounding",
        })

    def test_resource_interruption_never_truncates_or_drops_inputs(self):
        policy = self.contract["resource_policy"]
        self.assertFalse(policy["semantic_truncation"])
        self.assertFalse(policy["drop_unprocessed_input"])
        self.assertFalse(policy["claim_complete_after_interruption"])
        self.assertIn("INCOMPLETE", policy["on_interruption"])

    def test_registry_constraint_kind_without_semantics_is_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract["constraint_semantics"][0]["kind"] = "typed_reference"
        with self.assertRaisesRegex(SemanticsValidationError, "constraint semantics coverage mismatch"):
            validate_semantics(contract, self.registry, self.schema, self.registry_schema)

    def test_registry_diagnostic_without_catalogue_entry_is_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract["diagnostic_catalog"] = [
            item for item in contract["diagnostic_catalog"] if item["code"] != "RULE_PREMISE_INELIGIBLE"
        ]
        with self.assertRaisesRegex(SemanticsValidationError, "diagnostics missing"):
            validate_semantics(contract, self.registry, self.schema, self.registry_schema)

    def test_inference_cannot_be_enabled_during_step_2_4(self):
        contract = copy.deepcopy(self.contract)
        contract["execution_enabled"] = True
        with self.assertRaises(SemanticsValidationError):
            validate_semantics(contract, self.registry, self.schema, self.registry_schema)

    def test_truth_promotion_and_semantic_truncation_are_forbidden(self):
        contract = copy.deepcopy(self.contract)
        contract["safety_invariants"]["automatic_truth_promotion"] = True
        with self.assertRaises(SemanticsValidationError):
            validate_semantics(contract, self.registry, self.schema, self.registry_schema)
        contract = copy.deepcopy(self.contract)
        contract["resource_policy"]["semantic_truncation"] = True
        with self.assertRaises(SemanticsValidationError):
            validate_semantics(contract, self.registry, self.schema, self.registry_schema)


if __name__ == "__main__":
    unittest.main()
