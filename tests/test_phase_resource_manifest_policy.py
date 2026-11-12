"""Governance gate: each Phase 8+ roadmap has a machine-readable resource manifest."""
import json
from pathlib import Path
import re
import unittest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "specifications/usg-phase-resource-manifest-0.1.0.schema.json").read_text(encoding="utf-8"))
MANIFEST_DIR = ROOT / "config/phase-resource-manifests"


class PhaseResourceManifestPolicyTests(unittest.TestCase):
    def test_all_phase_8_plus_roadmaps_have_a_resource_manifest(self):
        found = []
        for path in (ROOT / "documentation").glob("PHASE-*-*ROADMAP.md"):
            match = re.match(r"PHASE-(\d+)-", path.name)
            if match and int(match.group(1)) >= 8:
                found.append(int(match.group(1)))
        self.assertTrue(found, "expected at least one Phase 8+ roadmap")
        for phase_number in sorted(set(found)):
            candidates = list(MANIFEST_DIR.glob(f"phase{phase_number}-*.json"))
            self.assertTrue(candidates, f"Phase {phase_number} roadmap has no resource manifest")
            for manifest_path in candidates:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(data)
                self.assertEqual(data["phase_id"], f"P{phase_number}")

    def test_phase8_manifest_declares_core_sources_and_candidate_boundaries(self):
        path = MANIFEST_DIR / "phase8-system-evidence-integration.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {item["source_family_id"] for item in data["resources"] if item["requirement"] == "required"}
        self.assertIn("canonical_semantic_interchange", required)
        self.assertIn("open_world_evaluation_foundation", required)
        self.assertIn("external_lexical_acquisition", required)
        self.assertIn("phase7_knowledge_layer", required)
        self.assertTrue(data["governance"]["candidate_resources_remain_separate"])
        self.assertFalse(data["governance"]["phase_status_auto_mutation"])
        gate_ids = {item["gate_id"] for item in data["acceptance_gates"]}
        self.assertTrue({"P8-FRESHNESS", "P8-PROPOSALS", "P8-INTEGRATED-ACCEPTANCE"} <= gate_ids)


if __name__ == "__main__":
    unittest.main()
