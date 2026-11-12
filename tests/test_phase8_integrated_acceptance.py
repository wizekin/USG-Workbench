"""Tests for the Phase 8 integrated acceptance review gate."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.system_evidence.acceptance import evaluate_phase8_acceptance


ROOT = Path(__file__).resolve().parents[1]


class Phase8AcceptanceTests(unittest.TestCase):
    def make_report(self):
        phases = [{"id": f"P{i}", "name": f"Phase {i}", "status": "in_progress", "open_work": ""}
                  for i in range(1, 9)]
        return {
            "phase_status": phases,
            "source_families": [{"id": item} for item in [
                "canonical_semantic_interchange", "phase_development_history",
                "phase7_knowledge_layer", "open_world_evaluation_foundation",
                "evidence_driven_growth_planner", "external_lexical_acquisition",
                "system_assessments_and_backlog", "system_evidence_catalogue_and_phase_manifest"
            ]],
            "source_registry": {}, "resource_consumption_map": {}, "asset_summary": {},
            "open_world": {}, "external_lexical": {"pud_evaluation": {
                "status": "fresh_for_current_shard_count",
                "rights_and_runtime_boundary": {"runtime_promotion_allowed": False}}},
            "workflow_evidence": {"status": "collected", "workflow_count": 12},
            "growth_plan": {}, "discoveries": [], "evidence_quality_diagnostics": [],
            "system_intelligence": {"cross_implementation": {"status": "collected"}, "knowledge_layer": {"status": "collected"}},
            "integrated_priorities": [], "review_proposals": [],
            "governance": {"runtime_mutations_performed": False,
                           "candidate_resources_promoted": False,
                           "phase_statuses_changed": False,
                           "canonical_contracts_changed": False,
                           "amendments_require_review": True},
        }

    def test_integrated_gate_is_review_eligible_but_never_accepts_phase(self):
        report = self.make_report()
        result = evaluate_phase8_acceptance(report, ROOT)
        self.assertEqual(result["status"], "eligible_for_review")
        self.assertFalse(result["phase_accepted"])
        self.assertTrue(result["governance"]["human_acceptance_required"])
        self.assertTrue(all(item["passed"] for item in result["checks"]))

    def test_missing_required_source_blocks_review(self):
        report = self.make_report()
        report["source_families"] = [item for item in report["source_families"]
                                     if item["id"] != "external_lexical_acquisition"]
        result = evaluate_phase8_acceptance(report, ROOT)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["phase_accepted"])
        failed = {item["check_id"] for item in result["checks"] if not item["passed"]}
        self.assertIn("P8-RESOURCE-COVERAGE", failed)

    def test_proposal_that_mutates_phase_status_blocks_review(self):
        report = self.make_report()
        report["review_proposals"] = [{
            "proposal_id": "P8-PROP-UNSAFE", "review_status": "draft_requires_review",
            "implementation_status": "not_implemented",
            "phase_status_mutation_allowed": True,
            "canonical_contract_mutation_allowed": False,
            "runtime_promotion_allowed": False,
        }]
        result = evaluate_phase8_acceptance(report, ROOT)
        self.assertEqual(result["status"], "blocked")
        failed = {item["check_id"] for item in result["checks"] if not item["passed"]}
        self.assertIn("P8-PROPOSAL-COVERAGE", failed)
        self.assertIn("P8-PROPOSAL-GOVERNANCE", failed)

    def test_workflow_evidence_must_be_live_and_nonempty(self):
        report = self.make_report()
        report["workflow_evidence"] = {"status": "not_collected", "workflow_count": 0}
        result = evaluate_phase8_acceptance(report, ROOT)
        self.assertEqual(result["status"], "blocked")
        failed = {item["check_id"] for item in result["checks"] if not item["passed"]}
        self.assertIn("P8-WORKFLOW-OBSERVABILITY", failed)


if __name__ == "__main__":
    unittest.main()
