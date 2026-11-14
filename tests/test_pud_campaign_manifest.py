"""Tests for campaign bundle manifest auxiliary-file integrity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.open_world_evaluation.pud_campaign_manifest import include_auxiliary_files


class PudCampaignManifestTests(unittest.TestCase):
    def test_auxiliary_files_are_hashed_and_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bundle-manifest.json").write_text(json.dumps({
                "manifest_version": "1.0.0",
                "files": [{"name": "campaign-report.json", "size_bytes": 2, "sha256": "ab"}],
            }), encoding="utf-8")
            (root / "source-manifest.json").write_text("source", encoding="utf-8")
            (root / "structural-frequency-report.json").write_text("frequency", encoding="utf-8")
            manifest = include_auxiliary_files(
                root, ["source-manifest.json", "structural-frequency-report.json"]
            )
            names = [item["name"] for item in manifest["files"]]
            self.assertEqual(names, sorted(names))
            source = next(item for item in manifest["files"] if item["name"] == "source-manifest.json")
            self.assertEqual(source["size_bytes"], 6)
            self.assertEqual(source["sha256"], hashlib.sha256(b"source").hexdigest())

    def test_identical_repeat_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bundle-manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
            (root / "LICENSE.txt").write_text("license", encoding="utf-8")
            first = include_auxiliary_files(root, ["LICENSE.txt"])
            second = include_auxiliary_files(root, ["LICENSE.txt"])
            self.assertEqual(first, second)

    def test_missing_or_unsafe_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bundle-manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                include_auxiliary_files(root, ["missing.json"])
            with self.assertRaises(ValueError):
                include_auxiliary_files(root, ["../outside.json"])


if __name__ == "__main__":
    unittest.main()
