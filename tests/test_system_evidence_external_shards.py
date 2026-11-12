"""Content-addressed external lexical shard inventory tests."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.system_evidence.external_shards import inventory_and_deduplicate


class ExternalShardInventoryTests(unittest.TestCase):
    def test_duplicate_files_are_retained_but_evaluation_input_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shards = root / "shards"
            unique = root / "unique"
            shards.mkdir()
            (shards / "batch-001.jsonl.gz").write_bytes(b"same bytes")
            (shards / "batch-002-retry.jsonl.gz").write_bytes(b"same bytes")
            (shards / "batch-003.jsonl.gz").write_bytes(b"different bytes")
            manifest = {"source_snapshot_id": "snapshot-x", "batch_count": 2}
            report = inventory_and_deduplicate(shards, unique, manifest)
            self.assertEqual(report["file_count"], 2)
            self.assertEqual(report["physical_file_count"], 3)
            self.assertEqual(report["duplicate_file_count"], 1)
            self.assertEqual(report["status"], "matches_manifest_with_duplicates")
            self.assertTrue(report["matches_manifest"])
            self.assertEqual(len(list(unique.rglob("*.jsonl.gz"))), 2)
            self.assertEqual(len(report["duplicate_groups"]), 1)
            self.assertEqual(report["duplicate_groups"][0]["duplicate_paths"], ["batch-002-retry.jsonl.gz"])

    def test_inventory_mismatch_remains_explicit_after_deduplication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shards, unique = root / "shards", root / "unique"
            shards.mkdir()
            (shards / "batch-1.jsonl.gz").write_bytes(b"one")
            (shards / "batch-2.jsonl.gz").write_bytes(b"two")
            report = inventory_and_deduplicate(shards, unique, {"batch_count": 3})
            self.assertEqual(report["file_count"], 2)
            self.assertEqual(report["status"], "count_mismatch")
            self.assertFalse(report["matches_manifest"])

    def test_no_shards_is_not_reported_as_zero_batches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shards, unique = root / "shards", root / "unique"
            shards.mkdir()
            report = inventory_and_deduplicate(shards, unique, {"batch_count": 0})
            self.assertEqual(report["status"], "matches_manifest")
            self.assertEqual(report["file_count"], 0)


if __name__ == "__main__":
    unittest.main()
