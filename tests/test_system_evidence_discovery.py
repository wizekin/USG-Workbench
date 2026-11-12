"""Tests for Phase 8 discovery deduplication, routing impact, and integrated priorities."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.system_evidence.discovery import (
    classify_impacts, deduplicate_discoveries, discovery_key,
    build_review_proposals, integrated_priorities, related_backlog_items,
)


class Phase8DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "evaluations/system-wide/evidence-catalogue/100").mkdir(parents=True)
        (self.root / "documentation").mkdir()
        (self.root / "documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md").write_text(
            "| SYS-03 | naturalistic |\n| SYS-15 | growth |\n| SYS-16 | repair |\n",
            encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def finding(self, summary="first wording", severity="medium"):
        return {
            "id": "SYS-EVID-1", "kind": "growth_planner_recommendation",
            "severity": severity, "summary": summary,
            "evidence_refs": ["growth_plan.ranked_actions", "CASE-1"],
            "phase_impacts": ["P5", "P8"], "route": "existing_phase_amendment_proposal",
            "review_status": "observed_requires_review", "runtime_change_allowed": False,
            "details": {"priority_score": 19, "campaign_recurrence_count": 3,
                        "acceptance_gate": "independent_lexical_evaluation"},
        }

    def test_identity_is_independent_of_summary_wording_and_order(self):
        a = self.finding()
        b = self.finding("rephrased")
        b["evidence_refs"].reverse()
        self.assertEqual(discovery_key(a), discovery_key(b))

    def test_duplicate_findings_collapse_and_prior_snapshots_are_linked(self):
        prior = self.finding()
        prior["discovery_key"] = discovery_key(prior)
        (self.root / "evaluations/system-wide/evidence-catalogue/100/catalogue.json").write_text(
            json.dumps({"generated_at": "2026-11-12T00:00:00Z", "discoveries": [prior]}),
            encoding="utf-8")
        result = deduplicate_discoveries([self.finding(), self.finding("same observation")], self.root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["duplicate_observation_count"], 1)
        self.assertTrue(result[0]["previously_observed"])
        self.assertEqual(result[0]["prior_observation_count"], 1)
        self.assertEqual(result[0]["deduplication_status"], "recurring")

    def test_impact_classification_does_not_mutate_phase_status(self):
        phases = [
            {"id": "P7", "status": "accepted"},
            {"id": "P8", "status": "definition_in_progress"},
        ]
        result = classify_impacts({"phase_impacts": ["P7", "P8"], "details": {}}, phases)
        self.assertTrue(result["cross_cutting"])
        self.assertEqual(result["impacts"][0]["disposition"], "accepted_scope_amendment_review")
        self.assertFalse(result["phase_status_mutation_allowed"])
        self.assertEqual(phases[0]["status"], "accepted")

    def test_normative_change_is_routed_to_migration_review(self):
        result = classify_impacts({
            "phase_impacts": ["P1"], "details": {"normative_contract_change": True}
        }, [{"id": "P1", "status": "accepted"}])
        self.assertTrue(result["migration_review_required"])

    def test_backlog_links_only_existing_ids(self):
        findings = [self.finding()]
        findings[0]["kind"] = "latest_open_world_campaign_has_no_naturalistic_population"
        links = related_backlog_items(findings, self.root)
        self.assertEqual(links[findings[0]["id"]], ["SYS-03"])

    def test_integrated_queue_preserves_growth_metrics_and_has_no_score(self):
        result = integrated_priorities([self.finding()])
        self.assertEqual(result[0]["source_metrics"]["priority_score"], 19)
        self.assertEqual(result[0]["source_metrics"]["campaign_recurrence_count"], 3)
        self.assertNotIn("combined_score", result[0])
        self.assertFalse(result[0]["runtime_change_allowed"])
        self.assertTrue(result[0]["review_required"])

    def test_review_proposals_are_stable_and_never_implement_or_mutate(self):
        finding = self.finding()
        finding["discovery_key"] = discovery_key(finding)
        finding["impact_classification"] = {
            "migration_review_required": False,
            "impacts": [{"phase_id": "P7", "phase_status": "accepted"}],
        }
        finding["route"] = "existing_phase_amendment_proposal"
        first = build_review_proposals([finding], [
            {"id": "P7", "name": "Knowledge layer", "status": "accepted", "open_work": "bounded"}
        ])
        second = build_review_proposals([finding], [
            {"id": "P7", "name": "Knowledge layer", "status": "accepted", "open_work": "bounded"}
        ])
        self.assertEqual(first[0]["proposal_id"], second[0]["proposal_id"])
        self.assertEqual(first[0]["proposal_type"], "accepted_phase_amendment")
        self.assertEqual(first[0]["review_status"], "draft_requires_review")
        self.assertEqual(first[0]["implementation_status"], "not_implemented")
        self.assertFalse(first[0]["phase_status_mutation_allowed"])
        self.assertFalse(first[0]["canonical_contract_mutation_allowed"])
        self.assertFalse(first[0]["runtime_promotion_allowed"])

    def test_contract_change_proposal_requires_versioned_migration(self):
        finding = self.finding()
        finding["discovery_key"] = discovery_key(finding)
        finding["impact_classification"] = {"migration_review_required": True}
        proposals = build_review_proposals([finding], [])
        self.assertEqual(proposals[0]["proposal_type"], "versioned_contract_migration_review")


if __name__ == "__main__":
    unittest.main()
