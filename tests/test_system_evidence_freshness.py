"""Tests for Phase 8 freshness and evidence-consistency diagnostics."""
from __future__ import annotations

import unittest

from tools.system_evidence.freshness import evidence_quality_diagnostics


class EvidenceFreshnessTests(unittest.TestCase):
    def test_stale_and_future_timestamps_are_distinguished(self):
        external = {"progress": {"updated_at": "2026-11-01T00:00:00Z"},
                    "pud_evaluation": {"generated_at": "2026-11-13T00:00:00Z"}}
        results = evidence_quality_diagnostics(
            external, [], {"generated_at": "2026-11-12T11:30:00Z"},
            "2026-11-12T12:00:00Z")
        kinds = {item["kind"] for item in results}
        self.assertIn("evidence_source_stale", kinds)
        self.assertIn("evidence_timestamp_in_future", kinds)

    def test_missing_timestamps_remain_unknown_not_fresh_or_stale(self):
        results = evidence_quality_diagnostics(
            {"progress": {}, "pud_evaluation": {}}, [], None,
            "2026-11-12T12:00:00Z")
        self.assertEqual(results, [])

    def test_manifest_and_pud_shard_contradictions_are_detected(self):
        external = {
            "progress": {"batch_count": 4, "processed_headwords": 12, "expected_headwords": 10},
            "shard_inventory": {"file_count": 3},
            "pud_evaluation": {"evaluated_shard_count": 2},
        }
        results = evidence_quality_diagnostics(external, [], None, "2026-11-12T12:00:00Z")
        kinds = {item["kind"] for item in results}
        self.assertIn("external_lexical_progress_contradiction", kinds)
        self.assertIn("external_lexical_shard_count_contradiction", kinds)
        self.assertIn("external_lexical_pud_shard_contradiction", kinds)

    def test_campaign_population_and_execution_accounting_must_reconcile(self):
        campaigns = [{
            "campaign_id": "CAMP-X", "scenario_count": 10,
            "population_case_counts": {"random": 7, "diagnostic": 2},
            "execution_accounting": {"actual_attempt_count": 8, "not_executed_record_count": 1},
            "report_path": "evaluations/open-world/campaigns/CAMP-X/campaign-report.json",
        }]
        results = evidence_quality_diagnostics({}, campaigns, None, "2026-11-12T12:00:00Z")
        kinds = {item["kind"] for item in results}
        self.assertIn("campaign_population_count_contradiction", kinds)
        self.assertIn("campaign_execution_accounting_contradiction", kinds)

    def test_valid_campaign_accounting_produces_no_contradiction(self):
        campaigns = [{
            "campaign_id": "CAMP-Y", "scenario_count": 10,
            "population_case_counts": {"random": 8, "diagnostic": 2},
            "execution_accounting": {"actual_attempt_count": 9, "not_executed_record_count": 1},
        }]
        results = evidence_quality_diagnostics({}, campaigns, None, "2026-11-12T12:00:00Z")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
