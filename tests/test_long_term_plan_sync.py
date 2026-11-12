from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from tools.system_evidence.long_term_plan_sync import (
    build_report,
    collect_phase8_acceptance,
    matching_workstreams,
    parse_backlog_statuses,
    parse_continuation_statuses,
    read_json,
    render_markdown,
    validate_plan,
)


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/usg-long-term-development-plan-0.1.0.json"
SCHEMA_PATH = ROOT / "specifications/usg-long-term-development-plan-0.1.0.schema.json"
WORKFLOW_PATH = ROOT / ".github/workflows/usg-long-term-roadmap-sync.yml"


class LongTermPlanSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = read_json(PLAN_PATH)
        self.registry = {
            "phases": [
                {"id": f"P{i}", "name": f"Phase {i}", "status": "registered_status",
                 "roadmap": f"documentation/PHASE-{i}-ROADMAP.md",
                 "acceptance": None, "open_work": "bounded test state"}
                for i in range(1, 9)
            ]
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_sync_workflow_has_valid_github_expression_markers_and_safe_triggers(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("EVENT_BEFORE: ${{ github.event.before }}", workflow)
        self.assertIn("EVENT_NAME: ${{ github.event_name }}", workflow)
        self.assertIn("EVENT_SHA: ${{ github.sha }}", workflow)
        self.assertIn("token: ${{ secrets.GITHUB_TOKEN }}", workflow)
        self.assertNotIn("EVENT_BEFORE: {{", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn("evaluations/roadmap/plan-sync/latest.json", workflow)
        self.assertNotIn("evaluations/roadmap/plan-sync/**", workflow)

    def test_master_plan_validates_against_its_schema(self):
        schema = read_json(SCHEMA_PATH)
        validate_plan(self.plan, schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(self.plan)

    def test_backlog_parser_reads_only_explicit_implementation_status_rows(self):
        markdown = """
| ID | Priority | Work item |
|---|---|---|
| SYS-01 | P0 | Reconcile counts |
| SYS-02 | P0 | Attribute failures |

## Implementation status
| ID | Current state | Evidence |
|---|---|---|
| SYS-01 | **Complete** | PR |
| SYS-02 | **Complete for registered profiles** | PR |
| SYS-03 | **Pilot generator complete; campaign pending** | PR |
"""
        statuses = parse_backlog_statuses(markdown)
        self.assertEqual(statuses["SYS-01"], "Complete")
        self.assertEqual(statuses["SYS-02"], "Complete for registered profiles")
        self.assertEqual(statuses["SYS-03"], "Pilot generator complete; campaign pending")

    def test_continuation_parser_preserves_machine_status(self):
        statuses = parse_continuation_statuses({
            "work_items": [
                {"id": "P6-CONT-01", "status": "backlog"},
                {"id": "P6-CONT-04", "status": "candidate_only"},
            ]
        })
        self.assertEqual(statuses, {
            "P6-CONT-01": "backlog",
            "P6-CONT-04": "candidate_only",
        })

    def test_path_changes_map_to_impacted_future_workstreams(self):
        matches = matching_workstreams(self.plan, [
            "interoperability/common-fixture-contract.json",
            "tools/usg_external_lexical_v0_1_0/audit.py",
        ])
        by_phase = {item["phase_id"]: item for item in matches}
        self.assertIn("P9", by_phase)
        self.assertIn("P11", by_phase)
        self.assertTrue(by_phase["P9"]["matched_paths"])

    def test_missing_acceptance_artifact_does_not_mark_phase8_accepted(self):
        result = collect_phase8_acceptance(self.root)
        self.assertEqual(result["status"], "not_verified")
        self.assertFalse(result["phase_accepted"])

    def test_phase8_acceptance_requires_exact_commit_and_true_acceptance_flag(self):
        directory = self.root / "evaluations/system-wide/evidence-catalogue/123-1"
        directory.mkdir(parents=True)
        artifact = {
            "status": "accepted",
            "phase_accepted": True,
            "checks_passed": 2,
            "checks_total": 2,
            "checks": [{"check_id": "A", "passed": True}, {"check_id": "B", "passed": True}],
            "acceptance_decision": {
                "decision": "accepted",
                "phase_id": "P8",
                "source_commit_sha": "abc123",
                "validated_commit_sha": "abc123",
                "workflow_run_id": "123",
                "workflow_run_attempt": "1",
                "decision_id": "decision",
            },
        }
        (directory / "phase8-integrated-acceptance.json").write_text(
            json.dumps(artifact), encoding="utf-8"
        )
        result = collect_phase8_acceptance(self.root)
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["phase_accepted"])

        artifact["acceptance_decision"]["validated_commit_sha"] = "different"
        (directory / "phase8-integrated-acceptance.json").write_text(
            json.dumps(artifact), encoding="utf-8"
        )
        result = collect_phase8_acceptance(self.root)
        self.assertFalse(result["phase_accepted"])

    def test_report_shows_linked_evidence_without_accepting_future_phases(self):
        backlog = {"SYS-12": "Initial inventory complete; conformance not tested"}
        continuation = {"P6-CONT-04": "candidate_only"}
        report = build_report(
            self.root, self.plan, self.registry, backlog, continuation,
            ["interoperability/shared-fixtures.json"], "commit123", "push",
            generated_at="2026-11-12T12:00:00Z",
        )
        phases = {item["phase_id"]: item for item in report["phase_snapshots"]}
        self.assertEqual(phases["P9"]["planned_status"], "planned_not_started")
        self.assertFalse(report["phase8_formal_acceptance"]["phase_accepted"])
        self.assertTrue(report["change_observation"]["requires_plan_review"])
        self.assertFalse(report["governance"]["future_phase_implementation_started"])
        rendered = render_markdown(report)
        self.assertIn("Phase 8 acceptance evidence", rendered)
        self.assertIn("P9", rendered)


if __name__ == "__main__":
    unittest.main()
