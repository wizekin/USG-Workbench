"""Tests for OW-8 adaptive cluster discovery and formatting-only expansion."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.open_world_evaluation.adaptive_discovery import (
    build_adaptive_discovery, scan_history, write_outputs,
)
from tools.open_world_evaluation.generate_scenarios import ScenarioGenerator
from tools.open_world_evaluation.score_cases import score_pair
from tools.open_world_evaluation.validate_protocol import validate_instance

STAMP = "2026-11-11T16:00:00Z"
COMMIT = "f" * 40


def make_case():
    case = ScenarioGenerator(
        seed="ow8-adaptive-test-seed",
        target_ids=["phase4-bounded-interpreter"],
        created_at=STAMP,
    ).generate(1)[0]
    case["input"]["text"] = "Ada writes code."
    case["input"]["utf8_sha256"] = hashlib.sha256(b"Ada writes code.").hexdigest()
    return case


def make_record(case, outcome="crashed"):
    payload = {"outcome": outcome, "reason": "test-fixture"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.0.0",
        "attempt_id": "OWA-ADAPTIVE-TEST-0001",
        "case_id": case["case_id"],
        "target": {
            "component_id": case["target"]["component_id"],
            "component_version": case["target"]["component_version"],
            "entry_point": case["target"]["entry_point"],
            "commit_sha": COMMIT,
        },
        "started_at": STAMP,
        "finished_at": "2026-11-11T16:00:01Z",
        "outcome": outcome,
        "execution": {"duration_ms": 1.0, "timed_out": outcome == "timeout"},
        "capture": {
            "output_sha256": hashlib.sha256(raw).hexdigest(),
            "output_media_type": "application/json",
            "inline_output": payload,
        },
        "validation": {"diagnostics": []},
        "scoring": [],
        "artifacts": [],
    }


class AdaptiveDiscoveryTests(unittest.TestCase):
    def test_runtime_failures_generate_only_formatting_variants(self):
        case = make_case()
        record = make_record(case)
        score = score_pair(case, record)
        with tempfile.TemporaryDirectory() as folder:
            followups, report = build_adaptive_discovery(
                campaign_id="OWC-OW8-TEST-0001",
                cases=[case], results=[record], scores=[score],
                history_root=Path(folder), max_cases=5,
                variants_per_case=5, created_at=STAMP,
            )
        self.assertGreater(len(followups), 0)
        self.assertLessEqual(len(followups), 5)
        self.assertEqual(report["candidate_new_cluster_count"], 1)
        original_non_whitespace = "".join(case["input"]["text"].split())
        for followup in followups:
            self.assertEqual("".join(followup["input"]["text"].split()), original_non_whitespace)
            self.assertEqual(validate_instance("scenario", followup), [])
            self.assertEqual(followup["population"], "unconstrained_random")
            self.assertEqual(followup["oracle"]["type"], "none")

    def test_unsupported_ambiguous_partial_and_not_executed_are_not_expanded(self):
        for outcome in ("unsupported", "ambiguous", "partial", "not_executed"):
            case = make_case()
            record = make_record(case, outcome=outcome)
            score = score_pair(case, record)
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as folder:
                followups, report = build_adaptive_discovery(
                    campaign_id="OWC-OW8-TEST-0002",
                    cases=[case], results=[record], scores=[score],
                    history_root=Path(folder), created_at=STAMP,
                )
                self.assertEqual(followups, [])
                self.assertEqual(report["current_failure_cluster_count"], 0)

    def test_controlled_diagnostic_population_is_not_mutated(self):
        case = make_case()
        case["population"] = "controlled_diagnostic"
        case["oracle"] = {"type": "structural", "independent": True, "oracle_id": "fixture"}
        record = make_record(case)
        score = score_pair(case, record)
        with tempfile.TemporaryDirectory() as folder:
            followups, report = build_adaptive_discovery(
                campaign_id="OWC-OW8-TEST-0003",
                cases=[case], results=[record], scores=[score],
                history_root=Path(folder), created_at=STAMP,
            )
        self.assertEqual(followups, [])
        self.assertEqual(report["skipped_controlled_diagnostics"], 1)

    def test_historical_cluster_comparison_recognizes_previous_target_specific_cluster(self):
        case = make_case()
        record = make_record(case)
        score = score_pair(case, record)
        signature = ("crashed", case["target"]["component_id"])
        from tools.open_world_evaluation.adaptive_discovery import cluster_id
        cluster, label = cluster_id(signature)
        with tempfile.TemporaryDirectory() as folder:
            prior = Path(folder) / "prior" / "campaign-report.json"
            prior.parent.mkdir(parents=True)
            prior.write_text(json.dumps({
                "campaign_id": "OWC-PRIOR-CAMPAIGN-0001",
                "novel_clusters": [{"cluster_id": cluster, "proposed_label": label}],
            }), encoding="utf-8")
            followups, report = build_adaptive_discovery(
                campaign_id="OWC-OW8-TEST-0004",
                cases=[case], results=[record], scores=[score],
                history_root=Path(folder), created_at=STAMP,
            )
        self.assertEqual(report["history_campaign_count"], 1)
        self.assertEqual(report["historically_observed_cluster_count"], 1)
        self.assertEqual(report["candidate_new_cluster_count"], 0)

    def test_history_scanner_excludes_current_campaign(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "self" / "campaign-report.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "campaign_id": "OWC-CURRENT-CAMPAIGN-0001",
                "novel_clusters": [],
            }), encoding="utf-8")
            history = scan_history(Path(folder), exclude_campaign_id="OWC-CURRENT-CAMPAIGN-0001")
        self.assertEqual(history["history_campaign_count"], 0)

    def test_discovery_outputs_are_write_once(self):
        case = make_case()
        record = make_record(case)
        score = score_pair(case, record)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            followups, report = build_adaptive_discovery(
                campaign_id="OWC-OW8-TEST-0005",
                cases=[case], results=[record], scores=[score],
                history_root=root / "history", created_at=STAMP,
            )
            cases_path, report_path = root / "followups.jsonl", root / "discovery.json"
            write_outputs(followups, report, cases_path, report_path)
            with self.assertRaises(FileExistsError):
                write_outputs(followups, report, cases_path, report_path)


if __name__ == "__main__":
    unittest.main()
