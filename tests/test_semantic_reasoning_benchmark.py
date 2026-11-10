"""Phase 2 Step 2.2 benchmark corpus/evaluator tests.

These tests validate the benchmark contract with synthetic candidate-result data.
They do not invoke or claim an inference engine.
"""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.semantic_reasoning_benchmark_v1_0_0.evaluator import (
    DEFAULT_FIXTURE_SCHEMA,
    DEFAULT_RESULT_SCHEMA,
    DEFAULT_FIXTURES,
    DEFAULT_THRESHOLDS,
    evaluate,
    load_json,
    validate_schema,
)


ROOT = Path(__file__).resolve().parents[1]


def perfect_result(fixture):
    expected = fixture["expected"]
    conclusions = list(expected["conclusions"])
    derivations = []
    for specification in expected["required_derivations"]:
        item = dict(specification["expected_fields"])
        item.setdefault("derivation_id", specification["derivation_id"])
        item.setdefault("conclusion_id", specification["conclusion_id"])
        for field in specification["required_fields"]:
            if field not in item:
                item[field] = [] if field.endswith("_refs") else "TEST_VALUE"
        derivations.append(item)

    result = {
        "fixture_id": fixture["id"],
        "completion_status": expected["completion_status"],
        "conclusions": conclusions,
        "diagnostics": list(expected["diagnostics"]),
        "scope_bindings": [
            {"check_id": item["check_id"], "binding": copy.deepcopy(item["expected_binding"])}
            for item in expected["scope_checks"]
        ],
        "evidence_assessments": [
            {"check_id": item["check_id"], "assessment": copy.deepcopy(item["expected_assessment"])}
            for item in expected["evidence_checks"]
        ],
        "derivations": derivations,
        "preserved_item_ids": list(expected["preserved_item_ids"]),
    }

    resource_expected = expected.get("resource_expectations")
    if resource_expected:
        result["resource"] = {
            "interrupted": resource_expected["expected_interrupted"],
            "truncated": resource_expected["expected_truncated"],
            "input_item_count": resource_expected["expected_input_item_count"],
            "preserved_item_count": resource_expected["minimum_preserved_items"],
            "processed_operations": 2,
        }

    snapshot = {
        key: copy.deepcopy(value)
        for key, value in result.items()
        if key != "fixture_id"
    }
    result["repeat_outputs"] = [copy.deepcopy(snapshot), copy.deepcopy(snapshot)]
    return result


def perfect_bundle(fixtures):
    return {
        "benchmark_id": fixtures["benchmark_id"],
        "benchmark_version": fixtures["benchmark_version"],
        "results": [perfect_result(fixture) for fixture in fixtures["fixtures"]],
    }


class SemanticReasoningBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_json(DEFAULT_FIXTURES)
        cls.thresholds = load_json(DEFAULT_THRESHOLDS)
        cls.bundle = perfect_bundle(cls.fixtures)

    def test_fixture_corpus_matches_declared_count_and_has_stable_unique_ids(self):
        fixtures = self.fixtures["fixtures"]
        self.assertEqual(self.fixtures["fixture_count"], len(fixtures))
        identifiers = [item["id"] for item in fixtures]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(fixtures), 35)

    def test_all_required_case_types_and_semantic_domains_are_covered(self):
        fixture_types = {
            case_type
            for fixture in self.fixtures["fixtures"]
            for case_type in fixture["case_types"]
        }
        self.assertTrue({
            "positive", "negative", "boundary", "adversarial", "ambiguous",
            "unresolved", "conflicting", "unsupported", "incomplete",
        }.issubset(fixture_types))

        categories = {item["category"] for item in self.fixtures["fixtures"]}
        self.assertGreaterEqual(len(categories), 15)
        self.assertTrue({"identity", "operator-scope", "evidence", "inference", "resource"}.issubset(categories))

    def test_every_fixture_has_input_task_versions_and_explicit_expectations(self):
        for fixture in self.fixtures["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                self.assertEqual(fixture["versions"]["usg_sem_profile"], "1.0")
                self.assertEqual(fixture["versions"]["workbench"], "0.5.4")
                self.assertEqual(fixture["versions"]["python_document_adapter"], "1.5.1")
                self.assertEqual(fixture["input_snapshot"]["profile_id"], "USG-SEM/1.0")
                self.assertTrue(fixture["task"]["goal"])
                for key in (
                    "completion_status", "conclusions", "prohibited_conclusions",
                    "diagnostics", "scope_checks", "evidence_checks",
                    "required_derivations", "preserved_item_ids",
                ):
                    self.assertIn(key, fixture["expected"])

    def test_every_expected_conclusion_has_a_required_derivation_trace(self):
        for fixture in self.fixtures["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                expected = set(fixture["expected"]["conclusions"])
                traced = {
                    item["conclusion_id"]
                    for item in fixture["expected"]["required_derivations"]
                }
                self.assertTrue(
                    expected.issubset(traced),
                    f"Missing provenance expectations for {sorted(expected - traced)}",
                )

    def test_thresholds_are_frozen_before_any_inference_implementation(self):
        self.assertIs(self.thresholds["frozen_before_inference_implementation"], True)
        gates = {item["metric"]: item for item in self.thresholds["gates"]}
        self.assertEqual(gates["false_inference_rate"]["operator"], "<=")
        self.assertEqual(gates["false_inference_rate"]["threshold"], 0.0)
        self.assertEqual(gates["precision"]["threshold"], 1.0)
        self.assertEqual(gates["supported_case_recall"]["threshold"], 0.95)
        self.assertEqual(gates["per_category_supported_case_recall"]["threshold"], 0.90)
        for metric in (
            "scope_binding_accuracy", "evidence_assessment_accuracy",
            "provenance_completeness", "preservation_accuracy",
            "completion_status_accuracy", "diagnostic_accuracy",
            "determinism_accuracy", "resource_behavior_accuracy",
        ):
            self.assertEqual(gates[metric]["threshold"], 1.0)

    def test_fixture_and_candidate_result_schemas_validate(self):
        validate_schema(self.fixtures, DEFAULT_FIXTURE_SCHEMA)
        validate_schema(self.bundle, DEFAULT_RESULT_SCHEMA)

    def test_perfect_reference_bundle_passes_all_gates(self):
        report = evaluate(self.fixtures, self.thresholds, self.bundle)
        self.assertTrue(report["accepted"], report)
        self.assertEqual(report["metrics"]["precision"], 1.0)
        self.assertEqual(report["metrics"]["supported_case_recall"], 1.0)
        self.assertEqual(report["metrics"]["false_inference_rate"], 0.0)
        self.assertEqual(report["metrics"]["scope_binding_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["evidence_assessment_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["provenance_completeness"], 1.0)
        self.assertEqual(report["metrics"]["preservation_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["determinism_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["resource_behavior_accuracy"], 1.0)
        self.assertTrue(all(gate["passed"] for gate in report["gates"]))

    def test_prohibited_conclusion_fails_zero_false_inference_gate(self):
        bundle = copy.deepcopy(self.bundle)
        target = next(
            item for item in bundle["results"]
            if item["fixture_id"] == "USG-BENCH-IDENTITY-002"
        )
        target["conclusions"].append("COREF:m-a:m-b")
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["counts"]["prohibited_emissions"], 1)
        self.assertGreater(report["metrics"]["false_inference_rate"], 0.0)

    def test_scope_and_evidence_axes_are_scored_exactly(self):
        scope_bundle = copy.deepcopy(self.bundle)
        scope_result = next(
            item for item in scope_bundle["results"]
            if item["fixture_id"] == "USG-BENCH-SCOPE-NEGATION-001"
        )
        scope_result["scope_bindings"][0]["binding"]["operator"] = "EXISTS"
        scope_report = evaluate(self.fixtures, self.thresholds, scope_bundle)
        self.assertFalse(scope_report["accepted"])
        self.assertLess(scope_report["metrics"]["scope_binding_accuracy"], 1.0)

        evidence_bundle = copy.deepcopy(self.bundle)
        evidence_result = next(
            item for item in evidence_bundle["results"]
            if item["fixture_id"] == "USG-BENCH-EVIDENCE-ALIGN-001"
        )
        evidence_result["evidence_assessments"][0]["assessment"]["semantic_support_status"] = "CORROBORATED"
        evidence_report = evaluate(self.fixtures, self.thresholds, evidence_bundle)
        self.assertFalse(evidence_report["accepted"])
        self.assertLess(evidence_report["metrics"]["evidence_assessment_accuracy"], 1.0)

    def test_missing_rule_version_fails_provenance_gate(self):
        bundle = copy.deepcopy(self.bundle)
        result = next(item for item in bundle["results"] if item["fixture_id"] == "USG-BENCH-PROVENANCE-001")
        result["derivations"][0].pop("rule_version")
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertLess(report["metrics"]["provenance_completeness"], 1.0)

    def test_silent_loss_and_resource_truncation_fail(self):
        bundle = copy.deepcopy(self.bundle)
        result = next(item for item in bundle["results"] if item["fixture_id"] == "USG-BENCH-RESOURCE-INTERRUPTION-001")
        result["preserved_item_ids"].remove("expr-12")
        result["resource"]["truncated"] = True
        result["resource"]["preserved_item_count"] = 11
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertLess(report["metrics"]["preservation_accuracy"], 1.0)
        self.assertLess(report["metrics"]["resource_behavior_accuracy"], 1.0)

    def test_nondeterministic_repeat_and_repeat_snapshot_mismatch_fail(self):
        bundle = copy.deepcopy(self.bundle)
        result = next(item for item in bundle["results"] if item["fixture_id"] == "USG-BENCH-DETERMINISM-001")
        result["repeat_outputs"][1]["conclusions"] = ["ASSERTED:B", "ASSERTED:A"]
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertLess(report["metrics"]["determinism_accuracy"], 1.0)

        bundle = copy.deepcopy(self.bundle)
        result = next(item for item in bundle["results"] if item["fixture_id"] == "USG-BENCH-DETERMINISM-001")
        result["conclusions"] = ["ASSERTED:B", "ASSERTED:A"]
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertLess(report["metrics"]["determinism_accuracy"], 1.0)

    def test_missing_fixture_result_is_a_structural_failure(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["results"].pop()
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertTrue(any("missing fixture results" in item for item in report["structural_errors"]))

    def test_category_recall_prevents_aggregate_hiding(self):
        bundle = copy.deepcopy(self.bundle)
        target = next(
            item for item in bundle["results"]
            if item["fixture_id"] == "USG-BENCH-CONDITIONAL-MP-001"
        )
        target["conclusions"] = []
        target["repeat_outputs"] = [
            {
                "completion_status":target["completion_status"],
                "conclusions":[],
                "diagnostics":target["diagnostics"],
                "scope_bindings":target["scope_bindings"],
                "evidence_assessments":target["evidence_assessments"],
                "derivations":target["derivations"],
                "preserved_item_ids":target["preserved_item_ids"],
            }
        ] * 2
        report = evaluate(self.fixtures, self.thresholds, bundle)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["category_recall"]["conditionals-connectives"], 0.0)
        self.assertLess(report["metrics"]["per_category_supported_case_recall"], 0.90)


if __name__ == "__main__":
    unittest.main()
