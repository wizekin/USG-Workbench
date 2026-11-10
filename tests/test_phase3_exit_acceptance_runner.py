"""Contract tests for the machine-readable Phase 3 acceptance report."""
from __future__ import annotations

import unittest

from tools.phase3_exit_acceptance_v1_0_0.run import build_report


class Phase3ExitAcceptanceReportTests(unittest.TestCase):
    def test_all_required_checks_must_pass(self):
        report = build_report([
            {"check_id": "store", "status": "PASS"},
            {"check_id": "scope", "status": "PASS"},
        ], "abc123")
        self.assertEqual(report["acceptance_status"], "PASS")
        self.assertEqual(report["source_commit"], "abc123")
        self.assertEqual(report["passed_check_count"], 2)
        self.assertEqual(report["failed_check_ids"], [])

    def test_one_critical_failure_blocks_acceptance_without_aggregate_score(self):
        report = build_report([
            {"check_id": "store", "status": "PASS"},
            {"check_id": "truth-safety", "status": "FAIL"},
            {"check_id": "package", "status": "PASS"},
        ])
        self.assertEqual(report["acceptance_status"], "FAIL")
        self.assertEqual(report["failed_check_ids"], ["truth-safety"])
        self.assertNotIn("score", report)
        self.assertNotIn("aggregate_score", report)

    def test_non_negotiable_invariants_are_explicit(self):
        report = build_report([{"check_id": "all", "status": "PASS"}])
        safety = report["critical_invariants"]
        self.assertEqual(report["canonical_storage_backend"], "SQLite")
        self.assertFalse(safety["truth_promotion"])
        self.assertFalse(safety["implicit_closed_world"])
        self.assertFalse(safety["semantic_truncation"])
        self.assertFalse(safety["human_review_dependency"])
        self.assertFalse(safety["public_network_binding"])


if __name__ == "__main__":
    unittest.main()
