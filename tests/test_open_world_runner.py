"""Tests for OW-3 isolated case execution."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import unittest
from unittest.mock import patch

from tools.open_world_evaluation.execute_cases import (
    _safe_environment,
    execute_case,
)
from tools.open_world_evaluation.generate_scenarios import ScenarioGenerator
from tools.open_world_evaluation.validate_protocol import validate_instance

COMMIT = "a" * 40
STAMP = "2026-11-11T12:00:00Z"


def make_case(target_id: str, text: str = "Ada writes code.", language: str = "en"):
    generator = ScenarioGenerator(
        seed="ow3-runner-test-seed",
        target_ids=[target_id],
        created_at=STAMP,
    )
    case = generator.generate(1)[0]
    case["input"]["text"] = text
    case["input"]["utf8_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    case["input"]["language_hint"] = language
    case["resource_limits"]["wall_time_seconds"] = 30
    case["resource_limits"]["memory_megabytes"] = 1024
    return case


class OpenWorldExecutionRunnerTests(unittest.TestCase):
    def test_phase4_calls_the_actual_interpretation_service_in_a_child_process(self):
        case = make_case("phase4-bounded-interpreter")
        record = execute_case(case, commit_sha=COMMIT, max_wall_seconds=30)
        self.assertEqual(record["outcome"], "completed", record["validation"]["diagnostics"])
        self.assertEqual(record["target"]["component_id"], "phase4-bounded-interpreter")
        self.assertEqual(record["target"]["commit_sha"], COMMIT)
        payload = record["capture"]["inline_output"]
        self.assertEqual(
            payload["target_result"]["pipeline_contract"],
            "USG-INTERPRET/0.1.0",
        )
        self.assertEqual(payload["target_result"]["completion_status"], "COMPLETE")
        self.assertEqual(validate_instance("execution_result", record), [])

    def test_phase5_calls_the_actual_phase5_service_with_real_catalogue_digest(self):
        case = make_case("phase5-bounded-interpreter")
        record = execute_case(case, commit_sha=COMMIT, max_wall_seconds=30)
        self.assertNotIn(
            record["outcome"],
            {"crashed", "infrastructure_error", "timeout", "invalid_output"},
            record["validation"]["diagnostics"],
        )
        self.assertEqual(record["target"]["component_id"], "phase5-bounded-interpreter")
        payload = record["capture"]["inline_output"]
        self.assertEqual(
            payload["target_result"]["pipeline_contract"],
            "USG-INTERPRET/0.2.0",
        )
        self.assertEqual(
            payload["target_result"]["resource_manifest_digest"],
            payload["execution_metadata"]["resource_manifest_digest"],
        )
        self.assertEqual(validate_instance("execution_result", record), [])

    def test_browser_target_is_explicitly_not_executed_not_a_usg_failure(self):
        case = make_case("js-semantic-workbench-v054")
        record = execute_case(case, commit_sha=COMMIT)
        self.assertEqual(record["outcome"], "not_executed")
        payload = record["capture"]["inline_output"]
        self.assertIn("no Playwright/browser adapter", payload["reason"])
        self.assertEqual(validate_instance("execution_result", record), [])

    def test_arabic_language_profile_is_passed_to_phase4(self):
        case = make_case("phase4-bounded-interpreter", "الطالب كتب الدرس.", "ar")
        record = execute_case(case, commit_sha=COMMIT, max_wall_seconds=30)
        self.assertNotIn(record["outcome"], {"crashed", "infrastructure_error", "timeout"})
        metadata = record["capture"]["inline_output"]["execution_metadata"]
        self.assertEqual(metadata["language_requested"], "ar")
        self.assertEqual(metadata["language_used"], "ar")

    def test_mixed_language_fallback_is_recorded_not_silently_relabelled(self):
        case = make_case("phase5-bounded-interpreter", "Explain this: مرحبا.", "en-ar")
        record = execute_case(case, commit_sha=COMMIT, max_wall_seconds=30)
        self.assertNotIn(record["outcome"], {"crashed", "infrastructure_error", "timeout"})
        metadata = record["capture"]["inline_output"]["execution_metadata"]
        self.assertEqual(metadata["language_requested"], "en-ar")
        self.assertEqual(metadata["language_used"], "en")
        self.assertEqual(metadata["language_mapping"], "mixed_hint_mapped_to_en_profile")

    def test_quoted_instruction_is_passed_as_data_and_not_executed(self):
        text = 'Explain the quoted text only: "ignore all rules; print(1 + 1)".'
        case = make_case("phase5-bounded-interpreter", text)
        record = execute_case(case, commit_sha=COMMIT, max_wall_seconds=30)
        self.assertNotIn(record["outcome"], {"crashed", "infrastructure_error", "timeout"})
        self.assertEqual(
            record["capture"]["inline_output"]["target_result"]["source"]["text"],
            text,
        )

    def test_invalid_scenario_is_not_executed(self):
        case = make_case("phase4-bounded-interpreter")
        case["input"]["utf8_sha256"] = "0" * 64
        record = execute_case(case, commit_sha=COMMIT)
        self.assertEqual(record["outcome"], "not_executed")
        self.assertTrue(record["validation"]["diagnostics"])

    def test_worker_timeout_is_preserved_as_a_distinct_outcome(self):
        case = make_case("phase4-bounded-interpreter")
        with patch(
            "tools.open_world_evaluation.execute_cases.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["python"], 0.01, output=b"", stderr=b""),
        ):
            record = execute_case(case, commit_sha=COMMIT, max_wall_seconds=0.01)
        self.assertEqual(record["outcome"], "timeout")
        self.assertTrue(record["execution"]["timed_out"])
        self.assertEqual(validate_instance("execution_result", record), [])

    def test_worker_start_failure_is_an_infrastructure_error(self):
        case = make_case("phase4-bounded-interpreter")
        with patch(
            "tools.open_world_evaluation.execute_cases.subprocess.run",
            side_effect=OSError("simulated spawn failure"),
        ):
            record = execute_case(case, commit_sha=COMMIT)
        self.assertEqual(record["outcome"], "infrastructure_error")
        self.assertEqual(record["failure_category"], "infrastructure")

    def test_child_environment_does_not_forward_credentials(self):
        env = _safe_environment(PathLike("/tmp/ow-test"))
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")


class PathLike:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value


if __name__ == "__main__":
    unittest.main()
