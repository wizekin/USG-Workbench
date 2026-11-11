"""Contract and validation tests for OW-1 evaluation protocol schemas."""

from __future__ import annotations

import copy
import hashlib
import unittest
from pathlib import Path

from tools.open_world_evaluation.validate_protocol import (
    SCHEMA_DIR,
    OUTCOMES,
    load_schemas,
    validate_campaign_report,
    validate_instance,
)

STAMP = "2026-11-11T10:00:00Z"
SHA = "a" * 64
COMMIT = "b" * 40


def make_case(population="controlled_diagnostic"):
    text = "The child reads a book."
    source = {"kind": "diagnostic_fixture", "source_id": "fixture-01"}
    if population == "naturalistic":
        source = {
            "kind": "public_documentation",
            "source_id": "public-doc-01",
            "source_url": "https://example.org/docs",
            "retrieved_at": STAMP,
            "license_status": "approved",
            "redistribution_allowed": True,
            "privacy_review_status": "approved",
            "attribution": "Example publisher",
            "content_digest": SHA,
            "transformations": ["extract one sentence"],
        }
    return {
        "schema_version": "1.0.0",
        "case_id": "OW-CASE-00000001",
        "population": population,
        "created_at": STAMP,
        "generator": {
            "id": "ow-protocol-tests",
            "version": "1.0.0",
            "seed_mode": "explicit",
            "master_seed": "0123456789abcdef",
            "case_seed": "fedcba9876543210",
        },
        "source": source,
        "input": {
            "text": text,
            "utf8_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "language_hint": "en",
        },
        "target": {
            "component_id": "phase5-bounded-interpreter",
            "component_version": "0.2.0",
            "entry_point": "Phase5InterpretationService.interpret",
            "interface": "python_api",
            "contract_versions": ["USG-INTERPRET/0.2.0"],
        },
        "taxonomy": {"labels": ["simple_transitive"], "unclassified": False},
        "oracle": {
            "type": "structural" if population == "controlled_diagnostic" else "none",
            "independent": population == "controlled_diagnostic",
            "oracle_id": "independent-fixture-01" if population == "controlled_diagnostic" else "",
        },
        "resource_limits": {
            "wall_time_seconds": 10,
            "memory_megabytes": 512,
            "max_input_bytes": 100000,
            "network_access": False,
        },
    }


def make_result(outcome="unsupported"):
    return {
        "schema_version": "1.0.0",
        "attempt_id": "OWA-ATTEMPT-0001",
        "case_id": "OW-CASE-00000001",
        "target": {
            "component_id": "phase5-bounded-interpreter",
            "component_version": "0.2.0",
            "entry_point": "Phase5InterpretationService.interpret",
            "commit_sha": COMMIT,
        },
        "started_at": STAMP,
        "finished_at": "2026-11-11T10:00:01Z",
        "outcome": outcome,
        "execution": {"duration_ms": 10.5, "timed_out": False},
        "capture": {"output_sha256": SHA, "output_media_type": "application/json"},
        "validation": {"diagnostics": []},
        "scoring": [],
        "artifacts": [],
    }


def make_report():
    rows = []
    totals = {outcome: 0 for outcome in OUTCOMES}
    for population, outcome in (
        ("unconstrained_random", "completed"),
        ("naturalistic", "unsupported"),
        ("controlled_diagnostic", None),
    ):
        counts = {key: 0 for key in OUTCOMES}
        if outcome:
            counts[outcome] = 1
            totals[outcome] += 1
        rows.append({
            "population": population,
            "attempted": sum(counts.values()),
            "completed": counts["completed"],
            "outcome_counts": counts,
            "coverage": {},
        })
    return {
        "schema_version": "1.0.0",
        "campaign_id": "OWC-PILOT-00000001",
        "status": "complete",
        "created_at": STAMP,
        "started_at": STAMP,
        "finished_at": "2026-11-11T10:01:00Z",
        "repository": "wizekin/USG-Workbench",
        "tested_commit_sha": COMMIT,
        "protocol_version": "1.0.0",
        "generator_version": "1.0.0",
        "evaluator_version": "1.0.0",
        "master_seed": "0123456789abcdef",
        "attempted": sum(totals.values()),
        "completed": totals["completed"],
        "outcome_counts": totals,
        "population_results": rows,
        "coverage": {},
        "failure_families": [],
        "novel_clusters": [],
        "limitations": ["Unit-test fixture; not an actual USG campaign."],
        "artifacts": [],
    }


class OpenWorldProtocolTests(unittest.TestCase):
    def test_all_draft_2020_12_schemas_are_valid(self):
        schemas = load_schemas()
        self.assertEqual(set(schemas), {"source", "scenario", "execution_result", "campaign_report"})
        for schema in schemas.values():
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )

    def test_controlled_diagnostic_requires_independent_oracle(self):
        case = make_case()
        self.assertEqual(validate_instance("scenario", case), [])
        case["oracle"] = {"type": "none", "independent": False}
        self.assertTrue(validate_instance("scenario", case))

    def test_naturalistic_requires_approved_license_redistribution_and_privacy_review(self):
        case = make_case("naturalistic")
        self.assertEqual(validate_instance("scenario", case), [])
        for key, value in (
            ("license_status", "unknown"),
            ("redistribution_allowed", False),
            ("privacy_review_status", "pending"),
        ):
            broken = copy.deepcopy(case)
            broken["source"][key] = value
            self.assertTrue(validate_instance("scenario", broken), key)

    def test_unconstrained_random_can_be_unclassified_and_without_oracle(self):
        case = make_case("unconstrained_random")
        case["taxonomy"] = {"labels": [], "unclassified": True}
        case["oracle"] = {"type": "none", "independent": False}
        self.assertEqual(validate_instance("scenario", case), [])

    def test_input_digest_is_checked_against_exact_utf8_text(self):
        case = make_case()
        case["input"]["utf8_sha256"] = "0" * 64
        self.assertTrue(validate_instance("scenario", case))

    def test_all_execution_outcomes_are_separately_representable(self):
        for outcome in OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertEqual(validate_instance("execution_result", make_result(outcome)), [])

    def test_campaign_population_and_outcome_counts_reconcile(self):
        report = make_report()
        self.assertEqual(validate_campaign_report(report), [])
        bad = copy.deepcopy(report)
        bad["attempted"] += 1
        self.assertTrue(validate_campaign_report(bad))
        bad = copy.deepcopy(report)
        bad["population_results"][0]["outcome_counts"]["crashed"] = 1
        self.assertTrue(validate_campaign_report(bad))

    def test_all_four_schema_files_exist(self):
        for filename in (
            "source-provenance.schema.json",
            "scenario.schema.json",
            "execution-result.schema.json",
            "campaign-report.schema.json",
        ):
            self.assertTrue((SCHEMA_DIR / filename).is_file(), filename)


if __name__ == "__main__":
    unittest.main()
