"""Repository tests for the OW-0 implementation inventory."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.open_world_evaluation.validate_inventory import (
    INVENTORY_PATH,
    validate_inventory,
)


ROOT = Path(__file__).resolve().parents[1]


class OpenWorldInventoryTests(unittest.TestCase):
    def test_inventory_paths_and_structure_are_valid(self):
        errors = validate_inventory(ROOT)
        self.assertEqual(errors, [], "\n".join(errors))

    def test_inventory_keeps_distinct_implementation_targets(self):
        data = json.loads((ROOT / INVENTORY_PATH).read_text(encoding="utf-8"))
        ids = {item["id"] for item in data["components"]}
        self.assertIn("js-semantic-workbench-v054", ids)
        self.assertIn("python-reference-kernel-v04-v05", ids)
        self.assertIn("python-native-semantic-models-v06-v14", ids)
        self.assertIn("phase4-bounded-interpreter", ids)
        self.assertIn("phase5-bounded-interpreter", ids)
        self.assertIn("phase6-candidate-expansion", ids)

    def test_inventory_explicitly_records_open_world_implementation_gaps(self):
        data = json.loads((ROOT / INVENTORY_PATH).read_text(encoding="utf-8"))
        joined = " ".join(data["known_gaps"]).lower()
        self.assertIn("scenario generator", joined)
        self.assertIn("isolated runner", joined)
        self.assertIn("append-only", joined)

    def test_no_component_claims_unrestricted_language_coverage(self):
        data = json.loads((ROOT / INVENTORY_PATH).read_text(encoding="utf-8"))
        for component in data["components"]:
            self.assertTrue(component["limitations"], component["id"])
            self.assertTrue(component["evaluation_policy"], component["id"])


if __name__ == "__main__":
    unittest.main()
