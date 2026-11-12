"""Tests for the read-only Phase 6 continuation tracker."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.phase6_continuation_tracker.report import (
    build_report,
    load_json,
    render_markdown,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evaluations" / "phase6-continuation" / "tracker.json"
SCHEMA = ROOT / "specifications" / "phase6-continuation-tracker-1.0.schema.json"


class Phase6ContinuationTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(MANIFEST)

    def test_manifest_matches_versioned_schema(self) -> None:
        validate_manifest(self.manifest, SCHEMA)

    def test_every_workstream_has_unique_marker_and_is_non_blocking(self) -> None:
        validate_manifest(self.manifest)
        ids = [item["id"] for item in self.manifest["work_items"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item["pr_search_marker"] == item["id"] for item in self.manifest["work_items"]))
        self.assertTrue(all(item["phase7_blocking"] is False for item in self.manifest["work_items"]))

    def test_duplicate_ids_are_rejected(self) -> None:
        bad = copy.deepcopy(self.manifest)
        bad["work_items"][1]["id"] = bad["work_items"][0]["id"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_manifest(bad)

    def test_manifest_cannot_make_phase6_a_phase7_gate(self) -> None:
        bad = copy.deepcopy(self.manifest)
        bad["phase_status"]["phase7_blocking"] = True
        with self.assertRaisesRegex(ValueError, "non-blocking"):
            validate_manifest(bad)

    def test_offline_report_does_not_claim_github_activity_or_acceptance(self) -> None:
        report = build_report(
            self.manifest,
            "wizekin/USG-Workbench",
            offline=True,
            source_commit="test-sha",
        )
        self.assertEqual(report["monitoring_mode"], "offline")
        self.assertEqual(report["bounded_phase6_exit"], "accepted_for_registered_scopes")
        self.assertFalse(report["phase7_blocking"])
        self.assertEqual(report["work_item_count"], len(self.manifest["work_items"]))
        self.assertTrue(all(item["github_observation"]["status"] == "manifest_only" for item in report["work_items"]))

    def test_markdown_report_explains_non_blocking_status(self) -> None:
        report = build_report(self.manifest, "wizekin/USG-Workbench", offline=True)
        markdown = render_markdown(report)
        self.assertIn("Phase 7 blocking: **No**", markdown)
        self.assertIn("P6-CONT-01", markdown)
        self.assertIn("candidate_only_unless_separately_accepted", markdown)


if __name__ == "__main__":
    unittest.main()
