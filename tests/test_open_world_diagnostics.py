"""Tests for importing and scoring controlled Phase 4/5 diagnostic fixtures."""

from __future__ import annotations

import unittest

from tools.open_world_evaluation.import_diagnostics import import_diagnostic_scenarios
from tools.open_world_evaluation.score_cases import _diagnostic_oracle_metrics
from tools.open_world_evaluation.validate_protocol import validate_instance

STAMP = "2026-11-11T15:00:00Z"


class OpenWorldDiagnosticImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.manifest = import_diagnostic_scenarios(created_at=STAMP)

    def test_imports_phase4_and_phase5_controlled_fixture_sets(self):
        self.assertEqual(len(self.cases), 106)
        self.assertEqual(self.manifest["by_target"]["phase4-bounded-interpreter"], 6)
        self.assertEqual(self.manifest["by_target"]["phase5-bounded-interpreter"], 100)

    def test_every_imported_diagnostic_scenario_validates(self):
        for case in self.cases:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(validate_instance("scenario", case), [])

    def test_phase4_expected_status_and_expression_count_score_independently(self):
        case = next(
            item for item in self.cases
            if item["target"]["component_id"] == "phase4-bounded-interpreter"
            and item["oracle"]["expected"]["expected_completion_status"] == "COMPLETE"
        )
        result = {
            "pipeline_contract": "USG-INTERPRET/0.1.0",
            "completion_status": case["oracle"]["expected"]["expected_completion_status"],
            "document": {
                "expressions": [{}] * case["oracle"]["expected"]["expected_expression_count"]
            },
        }
        metrics = _diagnostic_oracle_metrics(case, result)
        self.assertEqual(len(metrics), 2)
        self.assertTrue(all(metric["value"] == 1.0 for metric in metrics))
        self.assertTrue(all(metric["oracle_independent"] for metric in metrics))

    def test_phase5_gold_roles_and_spans_score_separately(self):
        case = next(
            item for item in self.cases
            if item["target"]["component_id"] == "phase5-bounded-interpreter"
            and item["oracle"]["expected"]["gold_class"] == "POSITIVE"
        )
        expected = case["oracle"]["expected"]
        token_ids = {}
        tokens = []
        for index, (role, span) in enumerate(expected["expected_role_spans"].items()):
            token_id = f"tok:{index}"
            token_ids[role] = token_id
            tokens.append({
                "token": {
                    "token_id": token_id,
                    "start": span["start"],
                    "end": span["end"],
                    "surface_text": span["surface"],
                }
            })
        target_result = {
            "completion_status": "COMPLETE",
            "stages": {
                "lexical": {"artifact": {"tokens": tokens}},
                "syntax": {"artifact": {"clauses": [{
                    "candidates": [{
                        "construction_id": expected["expected_construction"],
                        "role_token_refs": [[role, token_ids[role]] for role in expected["expected_roles"]],
                    }]
                }]}},
                "semantic_composition": {"artifact": {
                    "status": "COMPOSED", "candidates": [{}],
                }},
            },
        }
        metrics = _diagnostic_oracle_metrics(case, target_result)
        values = {metric["metric_id"]: metric["value"] for metric in metrics}
        self.assertEqual(values["phase5_completion_status_exact"], 1.0)
        self.assertEqual(values["phase5_construction_exact"], 1.0)
        self.assertEqual(values["phase5_role_bindings_exact"], 1.0)
        self.assertEqual(values["phase5_role_spans_exact"], 1.0)

    def test_phase5_negative_and_ambiguous_cases_require_abstention(self):
        case = next(
            item for item in self.cases
            if item["target"]["component_id"] == "phase5-bounded-interpreter"
            and item["oracle"]["expected"]["gold_class"] in {"NEGATIVE", "AMBIGUOUS"}
        )
        target_result = {
            "completion_status": "UNSUPPORTED",
            "stages": {
                "lexical": {"artifact": {"tokens": []}},
                "syntax": {"artifact": {"clauses": []}},
                "semantic_composition": {"artifact": {"status": "UNRESOLVED", "candidates": []}},
            },
        }
        metrics = _diagnostic_oracle_metrics(case, target_result)
        self.assertTrue(any(
            metric["metric_id"] == "phase5_nonpositive_abstention"
            and metric["value"] == 1.0
            for metric in metrics
        ))


if __name__ == "__main__":
    unittest.main()
