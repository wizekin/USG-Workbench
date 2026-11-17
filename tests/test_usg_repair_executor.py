"""Tests for the bounded, deterministic repair executor."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.usg_repair_executor_v0_1_0.executor import (
    execute_plan,
    git_blob_sha1,
    validate_plan,
)


BASE = "a" * 40
EVIDENCE = "https://github.com/wizekin/USG-Workbench/actions/runs/44030813370"


class RepairExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "tools/system_evidence").mkdir(parents=True)
        self.target = self.root / "tools/system_evidence/sample.py"
        self.target.write_text("alpha = 1\nbeta = 2\n", encoding="utf-8")
        self.result_path = self.root / "repair-result.json"

    def tearDown(self):
        self.temp.cleanup()

    def plan(self, **overrides):
        payload = self.target.read_bytes()
        value = {
            "contract": "USG-BOUNDED-REPAIR-PLAN/0.1.0",
            "repair_id": "sys16-test-repair",
            "status": "ready",
            "base_commit": BASE,
            "description": "A bounded reporting repair used only by executor tests.",
            "patches": [{
                "path": "tools/system_evidence/sample.py",
                "scope": "reporting",
                "expected_git_blob_sha1": git_blob_sha1(payload),
                "edits": [{
                    "match_text": "alpha = 1",
                    "replacement_text": "alpha = 3",
                    "expected_occurrences": 1,
                }],
            }],
            "validation_profile": "system_evidence_github_actions",
            "evidence": [EVIDENCE],
            "rollback_note": "Revert the isolated PR with git revert.",
        }
        value.update(overrides)
        return value

    def runner(self, returncode=0):
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, returncode, "tests ran", "")

        return run, calls

    def test_dry_run_validates_without_writing_or_running_tests(self):
        original = self.target.read_text(encoding="utf-8")
        runner, calls = self.runner()
        report, code = execute_plan(
            self.plan(), self.root, BASE, apply=False,
            result_path=self.result_path, ancestor_checker=lambda *_: True,
            command_runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "validated_dry_run")
        self.assertEqual(self.target.read_text(encoding="utf-8"), original)
        self.assertFalse(calls)
        self.assertTrue(self.result_path.exists())

    def test_apply_runs_only_registered_commands_and_records_hashes(self):
        runner, calls = self.runner()
        report, code = execute_plan(
            self.plan(), self.root, BASE, apply=True,
            result_path=self.result_path, ancestor_checker=lambda *_: True,
            command_runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "applied_validated")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "alpha = 3\nbeta = 2\n")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], [
            "python", "-m", "unittest", "discover", "-s", "tests",
            "-p", "test_system_evidence_github_actions.py", "-v",
        ])
        self.assertNotEqual(report["patches"][0]["before_sha256"], report["patches"][0]["after_sha256"])

    def test_multiple_exact_edits_and_occurrence_counts_apply_in_order(self):
        self.target.write_text("alpha = 1\\nbeta = 2\\nalpha = 1\\n", encoding="utf-8")
        plan = self.plan()
        plan["patches"][0]["expected_git_blob_sha1"] = git_blob_sha1(self.target.read_bytes())
        plan["patches"][0]["edits"] = [
            {
                "match_text": "alpha = 1",
                "replacement_text": "alpha = 3",
                "expected_occurrences": 2,
            },
            {
                "match_text": "beta = 2",
                "replacement_text": "beta = 4",
                "expected_occurrences": 1,
            },
        ]
        runner, _ = self.runner()
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True, command_runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["patches"][0]["edit_count"], 2)
        self.assertEqual(
            self.target.read_text(encoding="utf-8"),
            "alpha = 3\\nbeta = 4\\nalpha = 3\\n",
        )

    def test_ci_scope_cannot_target_accepted_phase4_or_phase5_tests(self):
        (self.root / "tests").mkdir(parents=True)
        target = self.root / "tests/test_phase4_benchmark.py"
        target.write_text("alpha = 1\\nbeta = 2\\n", encoding="utf-8")
        plan = self.plan()
        plan["patches"][0]["path"] = "tests/test_phase4_benchmark.py"
        plan["patches"][0]["scope"] = "ci"
        plan["patches"][0]["expected_git_blob_sha1"] = git_blob_sha1(target.read_bytes())
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True,
        )
        self.assertEqual(code, 2)
        self.assertIn("allowlist", report["error"])
        self.assertEqual(target.read_text(encoding="utf-8"), "alpha = 1\\nbeta = 2\\n")

    def test_failed_validation_restores_every_patched_file(self):
        original = self.target.read_bytes()
        runner, _ = self.runner(returncode=1)
        report, code = execute_plan(
            self.plan(), self.root, BASE, apply=True,
            result_path=self.result_path, ancestor_checker=lambda *_: True,
            command_runner=runner,
        )
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "rolled_back_test_failure")
        self.assertEqual(self.target.read_bytes(), original)

    def test_stale_blob_is_rejected_before_mutation(self):
        plan = self.plan()
        plan["patches"][0]["expected_git_blob_sha1"] = "b" * 40
        original = self.target.read_bytes()
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True,
        )
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "rejected")
        self.assertEqual(self.target.read_bytes(), original)

    def test_base_commit_must_be_ancestor(self):
        original = self.target.read_bytes()
        report, code = execute_plan(
            self.plan(), self.root, "c" * 40, apply=True,
            ancestor_checker=lambda *_: False,
        )
        self.assertEqual(code, 2)
        self.assertIn("not an ancestor", report["error"])
        self.assertEqual(self.target.read_bytes(), original)

    def test_path_traversal_and_protected_runtime_paths_are_rejected(self):
        for path in ("../outside.py", "implementations/semantic.py", "resources/active.json"):
            with self.subTest(path=path):
                plan = self.plan()
                plan["patches"][0]["path"] = path
                report, code = execute_plan(
                    plan, self.root, BASE, apply=True,
                    ancestor_checker=lambda *_: True,
                )
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "rejected")

    def test_symlink_target_is_rejected(self):
        outside = self.root / "outside.py"
        outside.write_text("alpha = 1\n", encoding="utf-8")
        link = self.root / "tools/system_evidence/link.py"
        link.symlink_to(outside)
        plan = self.plan()
        plan["patches"][0]["path"] = "tools/system_evidence/link.py"
        plan["patches"][0]["expected_git_blob_sha1"] = git_blob_sha1(outside.read_bytes())
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True,
        )
        self.assertEqual(code, 2)
        self.assertIn("symlink", report["error"])

    def test_secret_like_replacement_is_rejected(self):
        plan = self.plan()
        plan["patches"][0]["edits"][0]["replacement_text"] = "token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456'"
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True,
        )
        self.assertEqual(code, 2)
        self.assertIn("secret", report["error"])

    def test_regression_fixture_scope_cannot_change_gold_label_keys(self):
        fixture_dir = self.root / "tests/fixtures/regressions"
        fixture_dir.mkdir(parents=True)
        fixture_target = fixture_dir / "example.json"
        fixture_target.write_text('{"status": "candidate"}\\n', encoding="utf-8")
        plan = self.plan()
        plan["patches"][0]["path"] = "tests/fixtures/regressions/example.json"
        plan["patches"][0]["scope"] = "regression_fixture"
        plan["patches"][0]["expected_git_blob_sha1"] = git_blob_sha1(fixture_target.read_bytes())
        plan["patches"][0]["edits"][0]["match_text"] = '"status": "candidate"'
        plan["patches"][0]["edits"][0]["replacement_text"] = '"gold_label": "Agent"'
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True,
        )
        self.assertEqual(code, 2)
        self.assertIn("gold labels", report["error"])

    def test_exact_occurrence_count_is_enforced(self):
        plan = self.plan()
        plan["patches"][0]["edits"][0]["expected_occurrences"] = 2
        report, code = execute_plan(
            plan, self.root, BASE, apply=True,
            ancestor_checker=lambda *_: True,
        )
        self.assertEqual(code, 2)
        self.assertIn("expected 2 exact match", report["error"])

    def test_workflow_does_not_report_failed_repair_or_pr_publication_as_success(self):
        workflow_path = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "usg-bounded-repair-executor.yml"
        )
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn('if [ "${{ steps.apply.outcome }}" != "success" ]; then', workflow)
        self.assertIn('if [ "${{ steps.paths.outcome }}" != "success" ]; then', workflow)
        self.assertIn('if [ "${{ steps.repair-pr.outcome }}" = "failure" ]', workflow)
        self.assertIn('echo "Repair PR publication failed;', workflow)
        self.assertIn("exit 1", workflow)

    def test_plan_cannot_supply_arbitrary_commands(self):
        plan = self.plan()
        plan["commands"] = ["rm", "-rf", "/"]
        with self.assertRaises(Exception):
            validate_plan(plan)


if __name__ == "__main__":
    unittest.main()
