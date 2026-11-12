"""Validate append-only system evidence snapshots published by the collector workflow."""
from __future__ import annotations
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "specifications/usg-system-evidence-catalogue-0.1.0.schema.json").read_text(encoding="utf-8"))
SNAPSHOT_ROOT = ROOT / "evaluations/system-wide/evidence-catalogue"


class PublishedEvidenceSnapshotTests(unittest.TestCase):
    def test_all_published_catalogue_snapshots_validate_and_are_append_only(self):
        if not SNAPSHOT_ROOT.is_dir():
            self.skipTest("No published evidence snapshots yet; first snapshot is created by the scheduled workflow.")
        snapshots = sorted(path for path in SNAPSHOT_ROOT.iterdir() if path.is_dir())
        self.assertEqual(len(snapshots), len({path.name for path in snapshots}))
        for directory in snapshots:
            with self.subTest(snapshot=directory.name):
                catalogue_path = directory / "catalogue.json"
                markdown_path = directory / "catalogue.md"
                metadata_path = directory / "collection-metadata.json"
                self.assertTrue(catalogue_path.is_file())
                self.assertTrue(markdown_path.is_file())
                self.assertTrue(metadata_path.is_file())
                catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(catalogue)
                self.assertEqual(catalogue["contract"], "USG-SYSTEM-EVIDENCE-CATALOGUE/0.1.0")
                self.assertEqual(metadata["snapshot_policy"], "append_only")
                self.assertEqual(metadata["snapshot_id"], directory.name)
                self.assertEqual(catalogue["repository"]["commit_sha"], metadata["main_commit_sha"])
                external_manifest = directory / "external-lexical-manifest.json"
                if external_manifest.is_file():
                    self.assertEqual(catalogue["external_lexical"]["manifest_sha256"],
                                     __import__("hashlib").sha256(external_manifest.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
