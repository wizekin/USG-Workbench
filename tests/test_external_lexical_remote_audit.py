import base64
import json
import unittest
from unittest.mock import patch

from tools.usg_external_lexical_v0_1_0.remote_audit import audit_github_branch


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class TestRemoteLexicalAudit(unittest.TestCase):
    def test_remote_audit_uses_checkpoint_snapshot_and_only_its_shards(self):
        checkpoint = {
            "source_snapshot_id": "snapshot-a", "batch_number": 1,
            "processed_headwords": 1, "processed_entries": 1, "processed_senses": 1,
            "failed_headwords": 0, "failed_pages": 0, "retried_headwords": 0,
            "recovered_headwords": 0, "retry_failed_headwords": 0,
            "retry_dead_letter_headwords": 0, "stored_bytes": 25, "retry_queue": [],
        }
        manifest = {
            "batch_count": 1, "processed_headwords": 1,
            "processed_entries": 1, "processed_senses": 1,
            "failed_headwords": 0, "failed_pages": 0, "retried_headwords": 0,
            "recovered_headwords": 0, "retry_failed_headwords": 0,
            "retry_dead_letter_headwords": 0, "stored_bytes": 25,
            "pending_retries": 0,
            "last_batch": {"path": "shards/snapshot-a/batch-000001-run.jsonl.gz", "bytes": 25},
        }

        def contents(value):
            return {"encoding": "base64", "content": base64.b64encode(
                json.dumps(value).encode("utf-8")
            ).decode("ascii"), "sha": "contents-sha"}

        responses = [
            contents(checkpoint),
            contents(manifest),
            {"sha": "tree-sha", "truncated": False, "tree": [
                {"type": "blob", "path": "shards/snapshot-a/batch-000001-run.jsonl.gz",
                 "size": 25, "sha": "blob-a"},
                {"type": "blob", "path": "shards/snapshot-b/batch-000001-old.jsonl.gz",
                 "size": 999, "sha": "blob-b"},
            ]},
        ]
        urls = []

        def opener(request, timeout=30):
            urls.append(request.full_url)
            return FakeResponse(responses.pop(0))

        report = audit_github_branch("wizekin/USG-Workbench", "usg-external-lexical-data",
                                     token="test-token", opener=opener)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["source"]["snapshot_id"], "snapshot-a")
        self.assertEqual(report["checks"]["shard_file_count"], 1)
        self.assertTrue(all("state/" in url or "git/trees/" in url for url in urls))

    def test_truncated_tree_fails_closed(self):
        checkpoint = {"source_snapshot_id": "snapshot-a"}
        manifest = {}
        def contents(value):
            return {"encoding": "base64", "content": base64.b64encode(
                json.dumps(value).encode("utf-8")
            ).decode("ascii")}
        responses = [contents(checkpoint), contents(manifest),
                     {"truncated": True, "tree": []}]
        def opener(request, timeout=30):
            return FakeResponse(responses.pop(0))
        with self.assertRaisesRegex(RuntimeError, "truncated"):
            audit_github_branch("wizekin/USG-Workbench", "usg-external-lexical-data",
                                opener=opener)


if __name__ == "__main__":
    unittest.main()
