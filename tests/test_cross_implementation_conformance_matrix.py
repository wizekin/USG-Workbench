"""Validate that the published cross-implementation matrix is evidence-backed."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "evaluations/system-wide/cross-implementation-matrix-2026-11-12.json"


class CrossImplementationMatrixTests(unittest.TestCase):
    def test_matrix_contract_and_guardrails(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(matrix["contract"], "USG-CROSS-IMPLEMENTATION-MATRIX/0.1.0")
        self.assertTrue(matrix["policy"]["component_tests_are_not_cross_conformance"])
        self.assertTrue(matrix["policy"]["no_runtime_contract_changes"])
        self.assertTrue(matrix["policy"]["candidate_lexical_evidence_is_not_promoted"])

    def test_every_component_test_claim_has_existing_evidence(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        for implementation in matrix["implementations"]:
            self.assertTrue((ROOT / implementation["primary_path"]).exists())
            for capability in implementation["capabilities"]:
                if capability["status"] == "component_tested":
                    self.assertTrue(capability["evidence"], capability["id"])
                    for evidence in capability["evidence"]:
                        with self.subTest(capability=capability["id"], evidence=evidence):
                            self.assertTrue((ROOT / evidence).exists(), evidence)

    def test_cross_runtime_gates_are_not_claimed_complete(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["status"] for item in matrix["cross_implementation_gates"]],
            ["not_started"] * 5,
        )
        for implementation in matrix["implementations"]:
            for capability in implementation["capabilities"]:
                if capability["id"] == "cross_runtime_semantic_equivalence":
                    self.assertEqual(capability["status"], "not_tested")


if __name__ == "__main__":
    unittest.main()
