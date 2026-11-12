"""GitHub Actions evidence collector tests with deterministic API fixtures."""
from __future__ import annotations
import json
import unittest

from tools.system_evidence.github_actions import collect_workflow_runs


class FakeResponse:
    def __init__(self, value):
        self.payload = json.dumps(value).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.payload


class GitHubActionsEvidenceTests(unittest.TestCase):
    def make_opener(self, payloads):
        def opener(request, timeout=30):
            url = request.full_url
            if url not in payloads:
                raise RuntimeError("unexpected request: " + url)
            return FakeResponse(payloads[url])
        return opener

    def test_collects_latest_run_artifacts_no_runs_and_disabled(self):
        base = "https://api.github.com/repos/wizekin/USG-Workbench"
        payloads = {
            base + "/actions/workflows?per_page=100": {
                "workflows": [
                    {"id": 1, "name": "Phase 5", "path": ".github/workflows/phase5.yml", "state": "active"},
                    {"id": 2, "name": "Open World", "path": ".github/workflows/open-world.yml", "state": "active"},
                    {"id": 3, "name": "New Workflow", "path": ".github/workflows/new.yml", "state": "active"},
                    {"id": 4, "name": "Disabled", "path": ".github/workflows/disabled.yml", "state": "disabled_manually"},
                ]
            },
            base + "/actions/workflows/1/runs?per_page=1&exclude_pull_requests=true": {
                "workflow_runs": [{
                    "id": 101, "run_number": 11, "run_attempt": 1, "event": "schedule",
                    "status": "completed", "conclusion": "success", "created_at": "2026-11-12T05:00:00Z",
                    "updated_at": "2026-11-12T05:01:00Z", "head_sha": "abc", "head_branch": "main",
                    "head_commit": {"message": "test"}, "html_url": "https://example.test/101"
                }]
            },
            base + "/actions/workflows/2/runs?per_page=1&exclude_pull_requests=true": {
                "workflow_runs": [{
                    "id": 102, "run_number": 12, "run_attempt": 1, "event": "schedule",
                    "status": "completed", "conclusion": "failure", "created_at": "2026-11-12T05:00:00Z",
                    "updated_at": "2026-11-12T05:01:00Z", "head_sha": "def", "head_branch": "main",
                    "head_commit": {"message": "test"}, "html_url": "https://example.test/102"
                }]
            },
            base + "/actions/workflows/3/runs?per_page=1&exclude_pull_requests=true": {"workflow_runs": []},
            base + "/actions/runs/101/artifacts?per_page=100": {
                "total_count": 1,
                "artifacts": [{"id": 201, "name": "pud-report", "size_in_bytes": 321,
                               "expired": False, "created_at": "2026-11-12T05:00:30Z",
                               "updated_at": "2026-11-12T05:00:30Z",
                               "archive_download_url": "https://example.test/artifact/201"}]
            },
            base + "/actions/runs/102/artifacts?per_page=100": {"total_count": 0, "artifacts": []},
        }
        report = collect_workflow_runs("wizekin/USG-Workbench", "token",
                                       opener=self.make_opener(payloads), workers=1)
        self.assertEqual(report["workflow_count"], 4)
        self.assertEqual(report["latest_run_count"], 2)
        self.assertEqual(report["status_counts"]["success"], 1)
        self.assertEqual(report["status_counts"]["failure"], 1)
        self.assertEqual(report["status_counts"]["no_runs"], 1)
        self.assertEqual(report["status_counts"]["disabled"], 1)
        failed = next(item for item in report["workflows"] if item["workflow_id"] == 2)
        self.assertEqual(failed["latest_run"]["conclusion"], "failure")
        successful = next(item for item in report["workflows"] if item["workflow_id"] == 1)
        self.assertEqual(successful["latest_run"]["artifact_count"], 1)
        self.assertEqual(successful["latest_run"]["artifacts"][0]["name"], "pud-report")
        self.assertFalse(failed["latest_run"]["artifacts"])

    def test_api_collection_error_is_not_reported_as_a_pass(self):
        base = "https://api.github.com/repos/wizekin/USG-Workbench"
        payloads = {
            base + "/actions/workflows?per_page=100": {
                "workflows": [{"id": 9, "name": "Unavailable", "path": ".github/workflows/x.yml", "state": "active"}]
            }
        }
        report = collect_workflow_runs("wizekin/USG-Workbench", "token",
                                       opener=self.make_opener(payloads), workers=1)
        self.assertEqual(report["status_counts"]["collection_error"], 1)
        self.assertEqual(len(report["collection_errors"]), 1)
        self.assertEqual(report["latest_run_count"], 0)

    def test_artifact_metadata_failure_is_separate_from_workflow_run_success(self):
        base = "https://api.github.com/repos/wizekin/USG-Workbench"
        payloads = {
            base + "/actions/workflows?per_page=100": {
                "workflows": [{"id": 5, "name": "Artifact Test", "path": ".github/workflows/test.yml", "state": "active"}]
            },
            base + "/actions/workflows/5/runs?per_page=1&exclude_pull_requests=true": {
                "workflow_runs": [{"id": 105, "status": "completed", "conclusion": "success",
                                   "created_at": "2026-11-12T05:00:00Z", "head_sha": "abc"}]
            }
        }
        report = collect_workflow_runs("wizekin/USG-Workbench", "token",
                                       opener=self.make_opener(payloads), workers=1)
        self.assertEqual(report["status_counts"]["success"], 1)
        self.assertEqual(len(report["collection_errors"]), 0)
        self.assertEqual(len(report["artifact_collection_errors"]), 1)
        self.assertEqual(report["workflows"][0]["latest_run"]["artifact_count"], 0)

    def test_requires_repository_and_token(self):
        with self.assertRaises(ValueError):
            collect_workflow_runs("not-a-repository", "token")
        with self.assertRaises(ValueError):
            collect_workflow_runs("wizekin/USG-Workbench", "")


if __name__ == "__main__":
    unittest.main()
