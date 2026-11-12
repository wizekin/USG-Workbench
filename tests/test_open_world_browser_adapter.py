"""End-to-end browser adapter tests for the JavaScript Semantic Workbench."""
from __future__ import annotations

import os
import unittest

from tools.open_world_evaluation.browser_adapter import (
    ADAPTER_ID,
    stable_workbench_projection,
    browser_request_is_allowed,
    interpret_in_browser,
)
from tools.open_world_evaluation.execute_cases import execute_case
from tools.open_world_evaluation.generate_scenarios import ScenarioGenerator


class BrowserAdapterProjectionTests(unittest.TestCase):
    def test_projection_ignores_run_ids_but_preserves_semantic_content(self):
        def record(claim_id, created_at):
            return {
                "engine": "rule_fallback",
                "intent": "ASSERTION",
                "interpretation": "A thermometer measures temperature.",
                "claims": [{
                    "id": claim_id,
                    "createdAt": created_at,
                    "subject": {"text": "thermometer", "surfaceText": "thermometer", "type": "instrument"},
                    "predicate": "MEASURES",
                    "object": {"text": "temperature", "surfaceText": "temperature", "type": "property"},
                    "polarity": "positive",
                    "tense": "present",
                    "modality": "asserted",
                    "conditions": [],
                    "evidence": {"quote": "A thermometer measures temperature.", "start": 0, "end": 37, "verified": True},
                    "provenance": "local_rule",
                    "sourceKind": "interpreted_text",
                    "confidence": 0.86,
                }],
                "unresolved": [],
                "warnings": [],
            }
        first = stable_workbench_projection(record("claim-1", "2026-01-01T00:00:00Z"),
                                            "A thermometer measures temperature.")
        second = stable_workbench_projection(record("claim-99", "2026-11-12T00:00:00Z"),
                                             "A thermometer measures temperature.")
        self.assertEqual(first, second)
        self.assertEqual(first["claim_count"], 1)
        self.assertEqual(first["claims"][0]["predicate"], "MEASURES")
        self.assertEqual(first["source"]["sha256"] and len(first["source"]["sha256"]), 64)

    def test_browser_network_policy_allows_only_local_workbench(self):
        self.assertTrue(browser_request_is_allowed("http://127.0.0.1:8765/"))
        self.assertTrue(browser_request_is_allowed("http://localhost:8765/api/health"))
        self.assertTrue(browser_request_is_allowed("data:text/plain,fixture"))
        self.assertFalse(browser_request_is_allowed("https://example.com/"))
        self.assertFalse(browser_request_is_allowed("http://192.168.1.1/"))
        self.assertFalse(browser_request_is_allowed("file:///etc/passwd"))

    def test_registered_target_declares_browser_adapter_contract(self):
        from pathlib import Path
        import json
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "tools/open_world_evaluation/target_profiles.json").read_text(encoding="utf-8"))
        target = next(item for item in registry["targets"] if item["component_id"] == "js-semantic-workbench-v054")
        self.assertEqual(target["execution_adapter"], "tools.open_world_evaluation.browser_adapter.interpret_in_browser")
        self.assertEqual(target["supported_language_hints"], ["en"])
        self.assertEqual(target["browser_network_policy"], "loopback_only")

    def test_browser_target_receives_explicit_resource_budget(self):
        generator = ScenarioGenerator(
            seed="sys04-resource-budget",
            target_ids=["js-semantic-workbench-v054"],
            created_at="2026-11-12T00:00:00Z",
        )
        case = generator.generate(1)[0]
        self.assertEqual(case["resource_limits"]["memory_megabytes"], 4096)
        self.assertEqual(case["resource_limits"]["wall_time_seconds"], 45)
        self.assertFalse(case["resource_limits"]["network_access"])

    def test_non_english_input_is_explicitly_unsupported(self):
        case = {"input": {"text": "الطالب يقرأ الكتاب.", "language_hint": "ar"}}
        result = __import__(
            "tools.open_world_evaluation.browser_adapter",
            fromlist=["interpret_in_browser"],
        ).interpret_in_browser(case)
        self.assertEqual(result["outcome"], "unsupported")
        self.assertIn("English-only", result["reason"])
        self.assertEqual(result["execution_metadata"]["adapter"], ADAPTER_ID)


@unittest.skipUnless(os.environ.get("USG_RUN_BROWSER_TESTS") == "1",
                     "real Chromium smoke test runs in the dedicated GitHub Actions job")
class BrowserAdapterEndToEndTests(unittest.TestCase):
    def test_direct_browser_adapter_runs_real_workbench_ui(self):
        result = interpret_in_browser({
            "input": {
                "text": "A thermometer measures temperature.",
                "language_hint": "en",
            }
        })
        self.assertEqual(result["outcome"], "completed", result)
        self.assertGreaterEqual(result["target_result"]["claim_count"], 1)
        self.assertEqual(result["execution_metadata"]["ollama_used"], False)

    def test_isolated_worker_runs_real_workbench_browser(self):
        generator = ScenarioGenerator(
            seed="sys04-playwright-browser-smoke",
            target_ids=["js-semantic-workbench-v054"],
            created_at="2026-11-12T00:00:00Z",
        )
        case = generator.generate(1)[0]
        case["input"]["text"] = "A thermometer measures temperature."
        case["input"]["language_hint"] = "en"
        from hashlib import sha256
        case["input"]["utf8_sha256"] = sha256(
            case["input"]["text"].encode("utf-8")
        ).hexdigest()
        record = execute_case(case, commit_sha="a" * 40, max_wall_seconds=60)
        self.assertEqual(record["outcome"], "completed", record.get("capture", {}).get("inline_output"))
        result = record["capture"]["inline_output"]
        target = result["target_result"]
        self.assertEqual(target["pipeline_contract"], "USG-WB-SEM/1.0")
        self.assertGreaterEqual(target["claim_count"], 1)
        self.assertEqual(target["source"]["text"], case["input"]["text"])
        self.assertEqual(result["execution_metadata"]["ollama_used"], False)
        self.assertEqual(result["execution_metadata"]["adapter"], "playwright-js-semantic-workbench")
        self.assertEqual(result["execution_metadata"]["memory_limit_enforcement"], "ephemeral_hosted_runner_vm")


if __name__ == "__main__":
    unittest.main()
