"""Phase 3 Step 3.8 packaging and reproducible manifest tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_release_manifest.py"


class Phase3PackagingTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_hashes_every_listed_file(self):
        spec = importlib.util.spec_from_file_location("usg_release_manifest", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        first = module.build_manifest()
        second = module.build_manifest()
        self.assertEqual(first, second)
        self.assertGreater(first["file_count"], 0)
        for entry in first["files"]:
            raw = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(entry["size_bytes"], len(raw))
            self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())

    def test_manifest_cli_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "manifest.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(target)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(manifest["manifest_profile"], "USG-RELEASE-MANIFEST/1.0.0")
            self.assertEqual(manifest["canonical_storage_backend"], "SQLite")

    def test_sample_document_and_query_are_valid_json_and_versioned(self):
        document = json.loads((ROOT / "examples/phase3/sample-usg-sem-1.0.json").read_text(encoding="utf-8"))
        query = json.loads((ROOT / "examples/phase3/sample-query.json").read_text(encoding="utf-8"))
        self.assertEqual(document["profileId"], "USG-SEM/1.0")
        self.assertEqual(query["goal"]["expression_ref"], "expr-b")
        self.assertEqual(query["inference_task"]["world_assumption"], "OPEN")

    def test_cli_exposes_lab_one_command_demo_and_other_commands(self):
        result = subprocess.run(
            [sys.executable, "-m", "tools.usg_local_api_v1_0_0.cli", "--help"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("lab", result.stdout)
        self.assertIn("serve", result.stdout)
        lab_help = subprocess.run(
            [sys.executable, "-m", "tools.usg_local_api_v1_0_0.cli", "lab", "--help"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(lab_help.returncode, 0, lab_help.stderr)
        self.assertIn("--db", lab_help.stdout)


if __name__ == "__main__":
    unittest.main()
