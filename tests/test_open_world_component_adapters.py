"""Acceptance tests for OW-10 component registration and smoke adapters."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "documentation/USG-OPEN-WORLD-CAPABILITY-INVENTORY.json"
PROFILES = ROOT / "tools/open_world_evaluation/target_profiles.json"

class ComponentAdapterRegistryTests(unittest.TestCase):
    def test_every_inventory_component_has_exactly_one_target_profile(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        inventory_ids = {item["id"] for item in inventory["components"]}
        profile_ids = [item["component_id"] for item in profiles["targets"]]
        self.assertEqual(set(profile_ids), inventory_ids)
        self.assertEqual(len(profile_ids), len(set(profile_ids)))

    def test_smoke_module_paths_are_repository_relative_and_nonempty(self):
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        for profile in profiles["targets"]:
            for relative_path, module_name in profile.get("smoke_modules", []):
                self.assertIsInstance(relative_path, str)
                self.assertIsInstance(module_name, str)
                self.assertTrue(module_name)
                resolved = (ROOT / relative_path).resolve()
                self.assertTrue(resolved == ROOT or ROOT in resolved.parents)
                self.assertTrue(resolved.exists(), f"missing adapter path: {relative_path}")

    def test_smoke_only_profiles_do_not_claim_semantic_accuracy(self):
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        for profile in profiles["targets"]:
            if profile.get("smoke_modules"):
                self.assertIn("smoke", profile["entry_point"].lower() + profile["interface"].lower())

if __name__ == "__main__":
    unittest.main()
