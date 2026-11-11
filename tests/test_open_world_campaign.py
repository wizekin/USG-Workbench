"""Tests for OW-5 campaign reports, append-only storage, and failure minimization."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tools.open_world_evaluation.campaign_pipeline import (
    build_campaign_report,
    render_markdown,
    store_campaign_bundle,
)
from tools.open_world_evaluation.minimize_failures import delta_debug_text


COMMIT = "e" * 40
STAMP = "2026-11-11T14:00:00Z"
OUTCOMES = [
    "completed", "unsupported", "ambiguous", "abstained", "partial",
    "invalid_output", "timeout", "crashed", "infrastructure_error", "not_executed",
]


def make_case(case_id, population, target="phase4-bounded-interpreter"):
    text = "Ada writes code."
    return {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "population": population,
        "created_at": STAMP,
        "generator": {
            "id": "ow5-test", "version": "1.0.0", "seed_mode": "explicit",
            "master_seed": "0123456789abcdef", "case_seed": "fedcba9876543210",
            "generation_trace": ["fixture"], "mutation_ops": [],
        },
        "source": (
            {
                "kind": "public_documentation",
                "source_id": "ow5-public-fixture",
                "source_url": "https://example.org/ow5-fixture",
                "retrieved_at": STAMP,
                "license_status": "approved",
                "redistribution_allowed": True,
                "privacy_review_status": "approved",
                "attribution": "OW-5 synthetic test publisher",
                "content_digest": "f" * 64,
            }
            if population == "naturalistic"
            else {"kind": "synthetic", "source_id": "ow5-tests"}
        ),
        "input": {
            "text": text,
            "utf8_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "language_hint": "en",
        },
        "target": {
            "component_id": target,
            "component_version": "0.1.0" if target.startswith("phase4") else "0.5.4",
            "entry_point": "test-entry-point",
            "interface": "python_api" if target.startswith("phase4") else "browser_ui",
        },
        "taxonomy": {"labels": ["fixture"], "unclassified": False},
        "oracle": (\n            {"type": "structural", "independent": True, "oracle_id": "ow5-fixture-oracle"}\n            if population == "controlled_diagnostic"\n            else {"type": "none", "independent": False}\n        ),
        "resource_limits": {
            "wall_time_seconds": 5, "memory_megabytes": 256,
            "max_input_bytes": 10000, "network_access": False,
        },
    }


def make_result(case, outcome, attempt):
    payload = {"outcome": outcome, "reason": "fixture"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.0.0",
        "attempt_id": f"OWA-TEST-{attempt:04d}",
        "case_id": case["case_id"],
        "target": {
            "component_id": case["target"]["component_id"],
            "component_version": case["target"]["component_version"],
            "entry_point": case["target"]["entry_point"],
            "commit_sha": COMMIT,
        },
        "started_at": STAMP,
        "finished_at": "2026-11-11T14:00:01Z",
        "outcome": outcome,
        "execution": {"duration_ms": 1.0, "timed_out": False},
        "capture": {
            "output_sha256": hashlib.sha256(raw).hexdigest(),
            "output_media_type": "application/json",
            "inline_output": payload,
        },
        "validation": {"diagnostics": []},
        "scoring": [],
        "artifacts": [],
    }


def write_jsonl(path, items):
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items),
        encoding="utf-8",
    )


class OpenWorldCampaignPipelineTests(unittest.TestCase):
    def test_report_preserves_all_populations_even_when_empty(self):
        cases = [
            make_case("OW-CASE-00000001", "unconstrained_random"),
            make_case("OW-CASE-00000002", "unconstrained_random"),
        ]
        results = [
            make_result(cases[0], "completed", 1),
            make_result(cases[1], "unsupported", 2),
        ]
        report = build_campaign_report(
            campaign_id="OWC-TEST-CAMPAIGN-0001",
            cases=cases, results=results, scores=[],
            tested_commit_sha=COMMIT,
        )
        self.assertEqual(len(report["population_results"]), 3)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["population_results"][1]["attempted"], 0)
        self.assertEqual(report["outcome_counts"]["unsupported"], 1)

    def test_campaign_report_schema_and_count_consistency(self):
        cases = [
            make_case("OW-CASE-00000001", "unconstrained_random"),
            make_case("OW-CASE-00000002", "naturalistic"),
            make_case("OW-CASE-00000003", "controlled_diagnostic"),
        ]
        results = [make_result(case, "completed", i) for i, case in enumerate(cases, 1)]
        report = build_campaign_report(
            campaign_id="OWC-TEST-CAMPAIGN-0002",
            cases=cases, results=results, scores=[],
            tested_commit_sha=COMMIT,
        )
        self.assertEqual(report["status"], "complete")
        schema_path = Path(__file__).resolve().parents[1] / "tools/open_world_evaluation/schemas/campaign-report.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report))
        self.assertEqual(errors, [])
        self.assertEqual(report["attempted"], 3)
        self.assertEqual(sum(report["outcome_counts"].values()), 3)

    def test_failure_signatures_are_clustered_without_marking_reviewed(self):
        cases = [
            make_case("OW-CASE-00000001", "unconstrained_random"),
            make_case("OW-CASE-00000002", "unconstrained_random"),
        ]
        results = [
            make_result(cases[0], "crashed", 1),
            make_result(cases[1], "crashed", 2),
        ]
        report = build_campaign_report(
            campaign_id="OWC-TEST-CAMPAIGN-0003",
            cases=cases, results=results, scores=[],
            tested_commit_sha=COMMIT,
        )
        self.assertEqual(len(report["novel_clusters"]), 1)
        self.assertEqual(report["novel_clusters"][0]["case_count"], 2)
        self.assertFalse(report["novel_clusters"][0]["reviewed"])

    def test_markdown_report_includes_limits_and_outcomes(self):
        cases = [make_case("OW-CASE-00000001", "unconstrained_random")]
        results = [make_result(cases[0], "not_executed", 1)]
        report = build_campaign_report(
            campaign_id="OWC-TEST-CAMPAIGN-0004",
            cases=cases, results=results, scores=[],
            tested_commit_sha=COMMIT,
        )
        markdown = render_markdown(report)
        self.assertIn("not_executed", markdown)
        self.assertIn("Limitations", markdown)
        self.assertIn("finite sample", markdown)

    def test_append_only_bundle_stores_hash_manifest_and_refuses_overwrite(self):
        cases = [make_case("OW-CASE-00000001", "unconstrained_random")]
        results = [make_result(cases[0], "completed", 1)]
        scores = []
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            case_path, result_path, score_path = (
                root / "cases.jsonl", root / "results.jsonl", root / "scores.jsonl"
            )
            write_jsonl(case_path, cases)
            write_jsonl(result_path, results)
            write_jsonl(score_path, scores)
            output_root = root / "stored"
            saved = store_campaign_bundle(
                campaign_id="OWC-TEST-CAMPAIGN-0005",
                cases_path=case_path, results_path=result_path, scores_path=score_path,
                output_root=output_root, tested_commit_sha=COMMIT,
            )
            manifest = json.loads((saved / "bundle-manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["append_only"])
            self.assertTrue((saved / "campaign-report.json").is_file())
            self.assertTrue((saved / "campaign-report.md").is_file())
            with self.assertRaises(FileExistsError):
                store_campaign_bundle(
                    campaign_id="OWC-TEST-CAMPAIGN-0005",
                    cases_path=case_path, results_path=result_path, scores_path=score_path,
                    output_root=output_root, tested_commit_sha=COMMIT,
                )

    def test_delta_debug_minimizer_reduces_text_only_while_failure_is_preserved(self):
        original = "REMOVE1 KEEP REMOVE2 REMOVE3"
        minimized, attempts = delta_debug_text(
            original,
            lambda candidate: "KEEP" in candidate,
            max_attempts=20,
        )
        self.assertIn("KEEP", minimized)
        self.assertLess(len(minimized.split()), len(original.split()))
        self.assertGreater(attempts, 0)

    def test_delta_debug_budget_is_respected(self):
        attempts_seen = []
        def predicate(candidate):
            attempts_seen.append(candidate)
            return False
        _, attempts = delta_debug_text("one two three four five", predicate, max_attempts=3)
        self.assertEqual(attempts, 3)
        self.assertEqual(len(attempts_seen), 3)


if __name__ == "__main__":
    unittest.main()
