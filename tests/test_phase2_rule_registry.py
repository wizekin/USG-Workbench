"""Tests for the declarative Phase 2 rule model and registry."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.semantic_rule_registry_v1_0_0.validator import (
    DEFAULT_FIXTURES,
    DEFAULT_REGISTRY,
    DEFAULT_SCHEMA,
    RegistryValidationError,
    validate_registry,
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Phase2RuleRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load(DEFAULT_REGISTRY)
        cls.fixtures = load(DEFAULT_FIXTURES)
        cls.schema = load(DEFAULT_SCHEMA)

    def test_registry_schema_and_cross_references_validate(self):
        report = validate_registry(self.registry, self.fixtures, self.schema)
        self.assertTrue(report["valid"])
        self.assertEqual(report["rule_count"], 4)
        self.assertFalse(report["execution_enabled"])

    def test_all_rules_remain_disabled_and_non_truth_promoting(self):
        self.assertFalse(self.registry["execution_enabled"])
        for rule in self.registry["rules"]:
            with self.subTest(rule=rule["rule_id"]):
                self.assertEqual(rule["activation_state"], "SPECIFIED_NOT_EXECUTABLE")
                self.assertTrue(all(not item["truth_promotion"] for item in rule["conclusion_templates"]))
                self.assertTrue(rule["execution_semantics"]["deterministic"])
                self.assertFalse(rule["execution_semantics"]["semantic_truncation"])

    def test_every_rule_has_positive_and_negative_or_boundary_coverage(self):
        for rule in self.registry["rules"]:
            expectations = {item["expectation"] for item in rule["test_coverage"]}
            self.assertIn("positive", expectations)
            self.assertTrue(expectations & {"negative", "boundary", "adversarial", "unsupported", "unresolved"})

    def test_benchmark_policy_rule_ids_and_versions_are_registered(self):
        registered = {(rule["rule_id"], rule["version"]) for rule in self.registry["rules"]}
        for fixture in self.fixtures["fixtures"]:
            for rule in fixture["task"]["reference_policy"]["rules"]:
                self.assertIn((rule["id"], rule["version"]), registered)

    def test_unknown_benchmark_fixture_reference_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["test_coverage"][0]["fixture_id"] = "USG-BENCH-DOES-NOT-EXIST"
        with self.assertRaisesRegex(RegistryValidationError, "unknown benchmark fixture"):
            validate_registry(registry, self.fixtures, self.schema)

    def test_unregistered_benchmark_reference_policy_rule_is_rejected(self):
        fixtures = copy.deepcopy(self.fixtures)
        fixtures["fixtures"][0]["task"]["reference_policy"]["rules"] = [
            {"id": "not-registered", "version": "9.9.9"}
        ]
        with self.assertRaisesRegex(RegistryValidationError, "references unregistered rule"):
            validate_registry(self.registry, fixtures, self.schema)

    def test_missing_negative_coverage_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["test_coverage"] = [
            item for item in registry["rules"][0]["test_coverage"]
            if item["expectation"] == "positive"
        ]
        with self.assertRaisesRegex(RegistryValidationError, "requires negative"):
            validate_registry(registry, self.fixtures, self.schema)

    def test_undeclared_variable_binding_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["premises"][0]["match"]["field_bindings"]["expression_ref"] = "UNDECLARED"
        with self.assertRaisesRegex(RegistryValidationError, "undeclared variable"):
            validate_registry(registry, self.fixtures, self.schema)

    def test_undeclared_conclusion_template_variable_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["conclusion_templates"][0]["template"]["expression_ref"] = "$UNDECLARED"
        with self.assertRaisesRegex(RegistryValidationError, "undeclared variable"):
            validate_registry(registry, self.fixtures, self.schema)

    def test_duplicate_rule_identity_and_version_are_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"].append(copy.deepcopy(registry["rules"][0]))
        with self.assertRaisesRegex(RegistryValidationError, "duplicate rule identity/version"):
            validate_registry(registry, self.fixtures, self.schema)

    def test_closed_world_rule_requires_explicit_complete_domain_constraints(self):
        registry = copy.deepcopy(self.registry)
        rule = next(item for item in registry["rules"] if item["assumptions"]["world_assumption"] == "EXPLICIT_CLOSED_COMPLETE_ONLY")
        rule["constraints"] = [item for item in rule["constraints"] if item["kind"] != "domain_complete"]
        with self.assertRaisesRegex(RegistryValidationError, "closed-world rule missing constraints"):
            validate_registry(registry, self.fixtures, self.schema)

    def test_rule_registry_cannot_be_activated_in_step_2_3(self):
        registry = copy.deepcopy(self.registry)
        registry["execution_enabled"] = True
        with self.assertRaises(RegistryValidationError):
            validate_registry(registry, self.fixtures, self.schema)

    def test_schema_rejects_unknown_rule_fields(self):
        registry = copy.deepcopy(self.registry)
        registry["rules"][0]["magic_auto_infer"] = True
        with self.assertRaisesRegex(RegistryValidationError, "schema:"):
            validate_registry(registry, self.fixtures, self.schema)


if __name__ == "__main__":
    unittest.main()
