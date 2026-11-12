"""Tests for the evidence-driven, non-mutating growth controller."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.open_world_evaluation.growth_controller import build_growth_plan, render_markdown


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def campaign(root: Path, campaign_id: str, created_at: str, stage: str, code: str):
    folder = root / "evaluations/open-world/campaigns" / campaign_id
    case_id = "OW-RAND-" + campaign_id[-8:]
    case = {
        "case_id": case_id,
        "population": "naturalistic",
        "input": {"text": "The bird flies.", "language_hint": "en"},
        "target": {"component_id": "phase5-bounded-interpreter"},
    }
    result = {
        "case_id": case_id,
        "outcome": "partial",
        "target": {"component_id": "phase5-bounded-interpreter"},
        "capture": {"inline_output": {"target_result": {
            "pipeline_contract": "USG-INTERPRET/0.2.0",
            "pipeline_version": "phase5-interpretation-integration/0.3.0",
            "resource_manifest_digest": "a" * 64,
            "diagnostics": [{"stage": stage, "code": code}],
        }}},
    }
    write_json(folder / "campaign-report.json", {
        "campaign_id": campaign_id,
        "created_at": created_at,
        "status": "partial",
        "tested_commit_sha": "b" * 40,
        "outcome_counts": {"partial": 1},
    })
    write_jsonl(folder / "scenario-cases.jsonl", [case])
    write_jsonl(folder / "execution-results.jsonl", [result])


class GrowthControllerTests(unittest.TestCase):
    def test_ranks_recurring_first_blockers_and_keeps_candidate_only_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign(root, "OWC-GROWTH-TEST-0001", "2026-11-10T00:00:00Z",
                     "lexical", "LEXICAL_UNRESOLVED_TOKEN")
            campaign(root, "OWC-GROWTH-TEST-0002", "2026-11-11T00:00:00Z",
                     "lexical", "LEXICAL_UNRESOLVED_TOKEN")
            campaign(root, "OWC-GROWTH-TEST-0003", "2026-11-12T00:00:00Z",
                     "syntax", "SYNTAX_INCOMPLETE")
            write_json(root / "evaluations/system-wide/2026-11-12/assessment.json", {
                "assessment_id": "baseline-test",
                "open_world": {"populations": {"naturalistic": 0}},
                "lexical_diagnostics": {
                    "crawl_processed_headwords": 602,
                    "external_pud_exact_surface_coverage": 0.0244,
                    "external_pud_oov_rate": 0.9756,
                },
                "phase_benchmarks": {"phase6": {"step_6_6": "blocked"}},
            })
            write_json(root / "evaluations/system-wide/cross-implementation-matrix-2026-11-12.json", {
                "cross_implementation_gates": [{"id": "CIC-01", "status": "not_started"}],
            })
            plan = build_growth_plan(root, max_campaigns=3, generated_at="2026-11-12T00:00:00Z")
            self.assertEqual(plan["campaigns_analyzed"], 3)
            self.assertEqual(plan["ranked_actions"][0]["stage"], "lexical")
            self.assertEqual(plan["ranked_actions"][0]["campaign_recurrence_count"], 2)
            self.assertEqual(plan["ranked_actions"][0]["first_blocking_diagnostic_counts"],
                             {"LEXICAL_UNRESOLVED_TOKEN": 2})
            self.assertEqual(plan["baseline"]["external_lexical_oov_rate"], 0.9756)
            self.assertFalse(plan["safety_policy"]["automatic_runtime_promotion_allowed"])
            self.assertTrue(all(not item["runtime_change_allowed"] for item in plan["ranked_actions"]))
            self.assertIn("does not edit runtime code", render_markdown(plan))

    def test_max_campaigns_uses_latest_campaigns_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign(root, "OWC-GROWTH-TEST-0001", "2026-11-10T00:00:00Z",
                     "lexical", "LEXICAL_UNRESOLVED_TOKEN")
            campaign(root, "OWC-GROWTH-TEST-0002", "2026-11-11T00:00:00Z",
                     "syntax", "SYNTAX_INCOMPLETE")
            plan = build_growth_plan(root, max_campaigns=1, generated_at="2026-11-12T00:00:00Z")
            self.assertEqual(plan["campaigns_analyzed"], 1)
            self.assertEqual(plan["ranked_actions"][0]["stage"], "syntax")

    def test_empty_evidence_is_explicit_and_does_not_invent_actions(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = build_growth_plan(Path(temp), generated_at="2026-11-12T00:00:00Z")
            self.assertEqual(plan["campaigns_analyzed"], 0)
            self.assertEqual(plan["ranked_actions"], [])
            self.assertFalse(plan["safety_policy"]["runtime_mutations_performed"])

    def test_campaign_limit_is_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build_growth_plan(Path(temp), max_campaigns=101)


if __name__ == "__main__":
    unittest.main()
