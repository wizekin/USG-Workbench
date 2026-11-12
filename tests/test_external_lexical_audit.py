import unittest

from tools.usg_external_lexical_v0_1_0.audit import audit_crawl_state


class TestExternalLexicalStateAudit(unittest.TestCase):
    def fixture(self):
        checkpoint = {
            "batch_number": 2, "processed_headwords": 12,
            "processed_entries": 8, "processed_senses": 10,
            "failed_headwords": 1, "failed_pages": 0,
            "retried_headwords": 1, "recovered_headwords": 1,
            "retry_failed_headwords": 0, "retry_dead_letter_headwords": 0,
            "stored_bytes": 300, "retry_queue": [],
        }
        manifest = {
            "batch_count": 2, "processed_headwords": 12,
            "processed_entries": 8, "processed_senses": 10,
            "failed_headwords": 1, "failed_pages": 0,
            "retried_headwords": 1, "recovered_headwords": 1,
            "retry_failed_headwords": 0, "retry_dead_letter_headwords": 0,
            "stored_bytes": 300, "pending_retries": 0,
            "last_batch": {"path": "shards/snapshot/batch-000002-run.jsonl.gz", "bytes": 200},
        }
        shards = [
            {"type": "file", "path": "shards/snapshot/batch-000001-run.jsonl.gz", "size": 100, "sha": "blob-one"},
            {"type": "file", "path": "shards/snapshot/batch-000002-run.jsonl.gz", "size": 200, "sha": "blob-two"},
        ]
        return checkpoint, manifest, shards

    def test_consistent_state_passes(self):
        report = audit_crawl_state(*self.fixture())
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["checks"]["physical_stored_bytes"], 300)
        self.assertFalse(report["mutated_data"])

    def test_identical_duplicate_batch_is_warning_and_bytes_are_physical(self):
        checkpoint, manifest, shards = self.fixture()
        duplicate = dict(shards[1], path="shards/snapshot/batch-000002-retry.jsonl.gz")
        shards.append(duplicate)
        manifest["stored_bytes"] += duplicate["size"]
        checkpoint["stored_bytes"] += duplicate["size"]
        report = audit_crawl_state(checkpoint, manifest, shards)
        self.assertEqual(report["status"], "passed_with_warnings")
        self.assertTrue(report["checks"]["duplicate_batches"][0]["identical_blob"])
        self.assertEqual(report["checks"]["physical_stored_bytes"], 500)
        self.assertEqual(report["checks"]["logical_batch_count"], 2)
        self.assertEqual(report["checks"]["duplicate_physical_copy_count"], 1)

    def test_inventory_counts_logical_batches_separately_from_identical_physical_copies(self):
        from tools.usg_external_lexical_v0_1_0.audit import build_shard_inventory_report

        files = [
            {"path": "snapshot/batch-000001-run-a.jsonl.gz", "size_bytes": 100, "sha256": "a"},
            {"path": "snapshot/batch-000002-run-a.jsonl.gz", "size_bytes": 200, "sha256": "b"},
            {"path": "snapshot/batch-000002-run-b.jsonl.gz", "size_bytes": 200, "sha256": "b"},
        ]
        report = build_shard_inventory_report(
            files, {"source_snapshot_id": "snapshot", "batch_count": 2}
        )
        self.assertEqual(report["physical_file_count"], 3)
        self.assertEqual(report["logical_batch_count"], 2)
        self.assertEqual(report["duplicate_physical_copy_count"], 1)
        self.assertEqual(report["total_size_bytes"], 500)
        self.assertTrue(report["matches_manifest"])
        self.assertEqual(report["consistency_status"], "matched")

    def test_inventory_flags_conflicting_copies_of_one_batch(self):
        from tools.usg_external_lexical_v0_1_0.audit import build_shard_inventory_report

        files = [
            {"path": "snapshot/batch-000001-run-a.jsonl.gz", "size_bytes": 100, "sha256": "a"},
            {"path": "snapshot/batch-000001-run-b.jsonl.gz", "size_bytes": 101, "sha256": "different"},
        ]
        report = build_shard_inventory_report(
            files, {"source_snapshot_id": "snapshot", "batch_count": 1}
        )
        self.assertFalse(report["matches_manifest"])
        self.assertEqual(report["conflicting_batch_numbers"], [1])
        self.assertEqual(report["duplicate_physical_copy_count"], 0)

    def test_checkpoint_manifest_counter_mismatch_fails(self):
        checkpoint, manifest, shards = self.fixture()
        manifest["processed_senses"] += 1
        report = audit_crawl_state(checkpoint, manifest, shards)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("processed_senses" in error for error in report["errors"]))

    def test_physical_byte_mismatch_fails(self):
        checkpoint, manifest, shards = self.fixture()
        manifest["stored_bytes"] = 999
        checkpoint["stored_bytes"] = 999
        report = audit_crawl_state(checkpoint, manifest, shards)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("physical shard bytes" in error for error in report["errors"]))

    def test_missing_last_batch_shard_fails(self):
        checkpoint, manifest, shards = self.fixture()
        shards.pop()
        manifest["stored_bytes"] = 100
        checkpoint["stored_bytes"] = 100
        report = audit_crawl_state(checkpoint, manifest, shards)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("last_batch path" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
