"""Tests for inventory-backed open-world coverage ledger."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tools.open_world_evaluation.coverage_ledger import build_coverage_ledger
from tools.open_world_evaluation.generate_scenarios import ScenarioGenerator


STAMP = "2026-11-11T17:00:00Z"
COMMIT = "1" * 40


def case(target_id: str, *, language="en", unclassified=False):
    item = ScenarioGenerator(
        seed="ow9-coverage-ledger-test",
        target_ids=[target_id],
        created_at=STAMP,
    ).generate(1)[0]
    item["input"]["language_hint"] = language
    item["taxonomy"] = {
        "labels": [] if unclassified else ["fixture_test"],
        "unclassified": unclassified,
    }
    item["generator"]["generation_trace"].append("family=coverage_test")
    return item


def record(item, outcome):
    payload = {"outcome": outcome, "reason": "coverage fixture"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.0.0",
        "attempt_id": f"OWA-COVERAGE-{item['case_id']}",
        "case_id": item["case_id"],
        "target": {
            "component_id": item["target"]["component_id"],
            "component_version": item["target"]["component_version"],
            "entry_point": item["target"]["entry_point"],
            "commit_sha": COMMIT,
        },
        "started_at": STAMP,
        "finished_at": STAMP,
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


class CoverageLedgerTests(unittest.TestCase):
    def test_entrypoint_coverage_is_not_misreported_as_capability_coverage(self):
        cases = [
            case("phase4-bounded-interpreter", unclassified=True),
            case("phase5-bounded-interpreter", language="ar"),
            case("js-semantic-workbench-v054"),
        ]
        results = [
            record(cases[0], "completed"),
            record(cases[1], "partial"),
            record(cases[2], "not_executed"),
        ]
        ledger = build_coverage_ledger(
            cases=cases, results=results, campaign_id="OWC-OW9-TEST-0001",
            created_at=STAMP,
        )
        by_id = {row["component_id"]: row for row in ledger["entrypoint_coverage"]}
        self.assertEqual(by_id["phase4-bounded-interpreter"]["entrypoint_coverage_status"], "entrypoint_exercised")
        self.assertEqual(by_id["phase5-bounded-interpreter"]["entrypoint_coverage_status"], "entrypoint_exercised")
        self.assertEqual(by_id["js-semantic-workbench-v054"]["entrypoint_coverage_status"], "not_executed_only")
        self.assertEqual(
            by_id["phase5-bounded-interpreter"]["capability_assessment"],
            "not_assessed_by_entrypoint_sampling",
        )
        self.assertEqual(ledger["unclassified_case_count"], 1)
        self.assertEqual(ledger["generator_family_counts"]["coverage_test"], 3)

    def test_inventory_components_without_target_profiles_are_visible_as_gaps(self):
        ledger = build_coverage_ledger(cases=[], results=[], created_at=STAMP)
        self.assertIn("python-native-semantic-models-v06-v14", ledger["not_registered_component_ids"])
        self.assertIn("phase6-candidate-expansion", ledger["not_registered_component_ids"])
        model_row = next(
            item for item in ledger["entrypoint_coverage"]
            if item["component_id"] == "python-native-semantic-models-v06-v14"
        )
        self.assertEqual(model_row["entrypoint_coverage_status"], "not_registered_in_open_world_target_profiles")

    def test_unknown_target_ids_are_reported_not_dropped(self):
        item = case("phase4-bounded-interpreter")
        item["target"]["component_id"] = "future-unregistered-target"
        ledger = build_coverage_ledger(cases=[item], results=[], created_at=STAMP)
        self.assertEqual(ledger["unknown_target_ids"], ["future-unregistered-target"])
        self.assertIn("python-native-semantic-models-v06-v14", ledger["not_registered_component_ids"])
        self.assertEqual(ledger["case_count"], 1)

    def test_historical_ledger_comparison_only_labels_unseen_as_candidates(self):
        item = case("phase4-bounded-interpreter")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prior" / "coverage-ledger.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "observed_taxonomy_labels": ["fixture_test"],
                "target_component_ids": ["phase4-bounded-interpreter"],
                "observed_generator_families": ["coverage_test"],
            }), encoding="utf-8")
            ledger = build_coverage_ledger(
                cases=[item], results=[], history_root=Path(folder), created_at=STAMP
            )
        self.assertEqual(ledger["historical_comparison"]["candidate_new_taxonomy_labels"], [])
        self.assertEqual(ledger["historical_comparison"]["candidate_new_targets"], [])
        self.assertEqual(ledger["historical_comparison"]["candidate_new_generator_families"], [])

    def test_coverage_ledger_matches_json_schema(self):
        ledger = build_coverage_ledger(cases=[], results=[], created_at=STAMP)
        schema_path = Path(__file__).resolve().parents[1] / "tools/open_world_evaluation/schemas/coverage-ledger.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(ledger))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
