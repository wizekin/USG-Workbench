"""Tests for cross-implementation and Phase 7 knowledge evidence discovery."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.system_evidence.system_intelligence import collect_system_intelligence


class SystemIntelligenceTests(unittest.TestCase):
    def test_matrix_surfaces_unproven_capabilities_and_pending_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix_path = root / "evaluations/system-wide/cross-implementation-matrix-2026-11-12.json"
            matrix_path.parent.mkdir(parents=True)
            matrix_path.write_text(json.dumps({
                "contract": "USG-CROSS-IMPLEMENTATION-MATRIX/0.1.0",
                "assessment_date": "2026-11-12",
                "implementations": [{
                    "id": "js", "version": "0.5",
                    "capabilities": [
                        {"id": "browser", "status": "component_tested"},
                        {"id": "semantic_equivalence", "status": "not_tested", "evidence": []},
                    ],
                }],
                "cross_implementation_gates": [
                    {"id": "CIC-01", "status": "not_started", "requirement": "freeze fixtures"}
                ],
                "policy": {"no_runtime_contract_changes": True},
            }), encoding="utf-8")
            result = collect_system_intelligence(root)
        summary = result["summary"]["cross_implementation"]
        self.assertEqual(summary["implementation_count"], 1)
        self.assertEqual(summary["capability_count"], 2)
        self.assertEqual(summary["pending_gate_count"], 1)
        kinds = {item["kind"] for item in result["findings"]}
        self.assertIn("cross_implementation_conformance_gaps", kinds)
        self.assertIn("cross_implementation_gates_pending", kinds)

    def test_phase7_unresolved_mappings_are_reported_without_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "documentation/PHASE-7-COMPLETION-RECORD.md"
            path.parent.mkdir(parents=True)
            path.write_text("43/43 cross-language sense-to-concept mapping proposals remained UNRESOLVED.",
                            encoding="utf-8")
            result = collect_system_intelligence(root)
        knowledge = result["summary"]["knowledge_layer"]
        self.assertEqual(knowledge["unresolved_mapping_count"], 43)
        self.assertFalse(knowledge["promotion_allowed"])
        self.assertEqual(result["findings"][0]["kind"], "knowledge_layer_unresolved_mapping_candidates")

    def test_missing_inputs_are_explicit_not_zero_or_success(self):
        with tempfile.TemporaryDirectory() as directory:
            result = collect_system_intelligence(Path(directory))
        self.assertEqual(result["summary"]["cross_implementation"]["status"], "not_collected")
        self.assertEqual(result["summary"]["knowledge_layer"]["status"], "not_collected")
        self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
