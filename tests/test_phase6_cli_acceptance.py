"""Executable CLI conformance tests for the integrated Phase 6 interpretation."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.usg_local_api_v1_0_0.cli import build_parser, main


class Phase6CliAcceptanceTests(unittest.TestCase):
    def test_parser_exposes_the_integrated_phase6_interpret_command(self):
        args = build_parser().parse_args([
            "phase6-interpret", "source.txt", "--language", "en", "--no-persist"
        ])
        self.assertEqual(args.command, "phase6-interpret")
        self.assertEqual(args.language, "en")
        self.assertTrue(args.no_persist)

    def test_cli_dispatches_to_the_shared_phase6_interpreter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("Ada writes code.", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main([
                    "phase6-interpret", str(source), "--language", "en",
                    "--no-persist", "--db", ":memory:",
                ])
            self.assertEqual(code, 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["interpretation"]["pipeline_contract"], "USG-INTERPRET/0.3.0")
            self.assertEqual(result["interpretation"]["source"]["text"], "Ada writes code.")
            self.assertEqual(result["interpretation"]["capability_state"], "CANDIDATE_ONLY")


if __name__ == "__main__":
    unittest.main()
