"""Regression tests for autonomous-growth campaign accounting and attribution."""
import unittest

from tools.open_world_evaluation.growth_diagnostics import (
    build_execution_accounting,
    build_stage_attribution,
    load_stage_dependency_graph,
)


def case(case_id, target="phase5-bounded-interpreter", population="unconstrained_random", language="en"):
    return {
        "case_id": case_id,
        "population": population,
        "target": {"component_id": target},
        "input": {"language_hint": language},
    }


def result(case_id, outcome, target="phase5-bounded-interpreter", inline_output=None):
    return {
        "case_id": case_id,
        "outcome": outcome,
        "target": {"component_id": target},
        "capture": {"inline_output": inline_output},
    }


class ExecutionAccountingTests(unittest.TestCase):
    def test_not_executed_records_are_not_counted_as_actual_attempts(self):
        cases = [case(f"case-{i}") for i in range(1, 5)]
        results = [
            result("case-1", "completed"),
            result("case-2", "not_executed"),
            result("case-3", "not_executed"),
            result("case-3", "partial"),
        ]
        accounting = build_execution_accounting(cases, results)
        self.assertEqual(accounting["scenario_count"], 4)
        self.assertEqual(accounting["result_record_count"], 4)
        self.assertEqual(accounting["actual_attempt_count"], 2)
        self.assertEqual(accounting["not_executed_record_count"], 2)
        self.assertEqual(accounting["scenario_count_with_result_record"], 3)
        self.assertEqual(accounting["scenario_count_with_actual_attempt"], 2)
        self.assertEqual(accounting["scenario_count_only_not_executed"], 1)
        self.assertEqual(accounting["scenario_count_without_result_record"], 1)
        self.assertEqual(accounting["scenario_count_with_multiple_result_records"], 1)
        target = accounting["target_accounting"][0]
        self.assertEqual(target["actual_attempt_count"], 2)
        self.assertEqual(target["not_executed_record_count"], 2)

    def test_empty_campaign_has_explicit_zero_counts(self):
        accounting = build_execution_accounting([], [])
        self.assertEqual(accounting["scenario_count"], 0)
        self.assertEqual(accounting["actual_attempt_count"], 0)
        self.assertEqual(accounting["not_executed_record_count"], 0)
        self.assertEqual(accounting["target_accounting"], [])


class FirstBlockingStageTests(unittest.TestCase):
    def test_earliest_blocker_and_later_stage_cooccurrences_are_separate(self):
        item = case("case-lexical", language="en-ar")
        output = {
            "target_result": {
                "diagnostics": [
                    {"stage": "syntax", "code": "SYNTAX_INCOMPLETE"},
                    {"stage": "lexical", "code": "LEXICAL_UNRESOLVED_TOKEN"},
                    {"stage": "semantic_composition", "code": "SEMANTIC_CLAUSE_UNRESOLVED"},
                ]
            }
        }
        report = build_stage_attribution(
            [item], [result("case-lexical", "partial", inline_output=output)]
        )
        self.assertEqual(report["first_blocking_stage_counts"], {"lexical": 1})
        self.assertEqual(report["dependency_related_later_stage_counts"], {
            "semantic_composition": 1, "syntax": 1,
        })
        group = report["breakdown_by_target_population_language"][0]
        self.assertEqual(group["language"], "en-ar")
        self.assertEqual(group["first_blocking_stage_counts"], {"lexical": 1})
        self.assertIn("not proof that an upstream failure caused them", report["causality_warning"])

    def test_parallel_phase5_blockers_are_both_retained_as_first_blockers(self):
        output = {"target_result": {"diagnostics": [
            {"stage": "syntax", "code": "SYNTAX_INCOMPLETE"},
            {"stage": "discourse", "code": "DISCOURSE_ANTECEDENT_UNRESOLVED"},
        ]}}
        report = build_stage_attribution(
            [case("case-parallel")],
            [result("case-parallel", "partial", inline_output=output)],
        )
        self.assertEqual(report["first_blocking_stage_counts"], {
            "discourse": 1, "syntax": 1,
        })
        self.assertEqual(report["records_with_multiple_parallel_first_blockers"], 1)
        self.assertEqual(report["dependency_related_later_stage_counts"], {})

    def test_phase4_stage_list_statuses_are_read_using_phase4_dependencies(self):
        output = {"target_result": {"stages": [
            {"stage": "syntax", "status": "INCOMPLETE"},
            {"stage": "semantic_composition", "status": "PARTIAL"},
            {"stage": "discourse", "status": "PARTIAL"},
        ]}}
        report = build_stage_attribution(
            [case("case-phase4", target="phase4-bounded-interpreter")],
            [result("case-phase4", "partial", target="phase4-bounded-interpreter", inline_output=output)],
        )
        self.assertEqual(report["first_blocking_stage_counts"], {"discourse": 1, "syntax": 1})
        self.assertEqual(report["dependency_related_later_stage_counts"], {
            "semantic_composition": 1,
        })

    def test_dependency_graph_is_acyclic_and_unknown_target_is_not_guessed(self):
        graph = load_stage_dependency_graph()
        self.assertIn("phase5-bounded-interpreter", graph["profiles"])
        report = build_stage_attribution(
            [case("case-unregistered", target="unknown-interpreter")],
            [result("case-unregistered", "partial", target="unknown-interpreter",
                    inline_output={"target_result": {"diagnostics": [
                        {"stage": "lexical", "code": "LEXICAL_UNRESOLVED_TOKEN"},
                    ]}})],
        )
        self.assertEqual(report["first_blocking_stage_counts"], {})
        self.assertEqual(report["unconfigured_target_record_counts"], {"unknown-interpreter": 1})

    def test_warnings_do_not_become_blocking_diagnostics(self):
        output = {"target_result": {"diagnostics": [
            {"stage": "lexical", "code": "LEXICAL_LOW_CONFIDENCE", "severity": "warning"},
        ]}}
        report = build_stage_attribution(
            [case("case-warning")],
            [result("case-warning", "completed", inline_output=output)],
        )
        self.assertEqual(report["first_blocking_stage_counts"], {})
        self.assertEqual(report["records_without_observed_blocking_diagnostic"], 1)

    def test_not_executed_records_are_excluded_from_stage_attribution(self):
        report = build_stage_attribution(
            [case("case-skipped")],
            [result("case-skipped", "not_executed")],
        )
        self.assertEqual(report["analyzed_actual_attempt_count"], 0)
        self.assertEqual(report["not_executed_record_count_excluded"], 1)

    def test_unmapped_stage_is_reported_without_guessing_a_first_blocker(self):
        output = {"target_result": {"diagnostics": [
            {"stage": "experimental_new_stage", "code": "NEW_STAGE_INCOMPLETE"},
        ]}}
        report = build_stage_attribution(
            [case("case-unknown")],
            [result("case-unknown", "partial", inline_output=output)],
        )
        self.assertEqual(report["first_blocking_stage_counts"], {})
        self.assertEqual(report["unmapped_blocking_stage_counts"], {"experimental_new_stage": 1})


if __name__ == "__main__":
    unittest.main()
