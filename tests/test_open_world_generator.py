"""Deterministic and protocol tests for the OW-2 scenario generator."""

from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tools.open_world_evaluation.generate_scenarios import (
    ScenarioGenerator,
    write_jsonl,
)
from tools.open_world_evaluation.validate_protocol import validate_instance

STAMP = "2026-11-11T11:00:00Z"
SEED = "OW-2-repeatability-test-seed"


class OpenWorldScenarioGeneratorTests(unittest.TestCase):
    def generator(self, seed=SEED):
        return ScenarioGenerator(seed=seed, created_at=STAMP)

    def test_fixed_seed_and_timestamp_are_reproducible(self):
        first = self.generator().generate(30)
        second = self.generator().generate(30)
        self.assertEqual(first, second)

    def test_different_seeds_change_generated_prompts(self):
        first = self.generator("seed-A-0123456789").generate(20)
        second = self.generator("seed-B-0123456789").generate(20)
        self.assertNotEqual(
            [case["input"]["text"] for case in first],
            [case["input"]["text"] for case in second],
        )

    def test_generated_cases_validate_against_ow1_protocol(self):
        cases = self.generator().generate(120)
        self.assertEqual(len(cases), 120)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(validate_instance("scenario", case), [])

    def test_default_target_assignment_is_balanced(self):
        cases = self.generator().generate(31)
        counts = Counter(case["target"]["component_id"] for case in cases)
        self.assertEqual(len(counts), 3)
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_target_matrix_reuses_each_prompt_across_every_target(self):
        cases = self.generator().generate(7, target_matrix=True)
        self.assertEqual(len(cases), 21)
        for offset in range(0, len(cases), 3):
            group = cases[offset:offset + 3]
            self.assertEqual(len({case["input"]["text"] for case in group}), 1)
            self.assertEqual(len({case["target"]["component_id"] for case in group}), 3)

    def test_unclassified_cases_are_retained_in_the_random_population(self):
        cases = self.generator().generate(60)
        unknown = sum(case["taxonomy"]["unclassified"] for case in cases)
        self.assertGreaterEqual(unknown, 20)
        self.assertEqual(
            sum(not case["taxonomy"]["labels"] for case in cases),
            unknown,
        )

    def test_generation_and_mutation_traces_are_recorded(self):
        cases = self.generator().generate(100)
        self.assertTrue(all(case["generator"]["generation_trace"] for case in cases))
        self.assertTrue(all("master_seed" in case["generator"] for case in cases))
        self.assertTrue(any(case["generator"]["mutation_ops"] for case in cases))

    def test_entropy_seed_is_recorded_when_no_seed_is_supplied(self):
        first = ScenarioGenerator(created_at=STAMP)
        second = ScenarioGenerator(created_at=STAMP)
        self.assertEqual(first.seed_mode, "entropy")
        self.assertEqual(len(first.master_seed), 64)
        self.assertNotEqual(first.master_seed, second.master_seed)

    def test_jsonl_manifest_contains_hash_and_prevents_overwrite(self):
        generator = self.generator()
        cases = generator.generate(4)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "cases.jsonl"
            manifest_path = write_jsonl(
                cases, output, generator=generator,
                requested_count=4, target_matrix=False,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["case_count"], 4)
            self.assertEqual(len(manifest["jsonl_sha256"]), 64)
            self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), 4)
            with self.assertRaises(FileExistsError):
                write_jsonl(
                    cases, output, generator=generator,
                    requested_count=4, target_matrix=False,
                )

    def test_unknown_target_and_invalid_count_are_rejected(self):
        with self.assertRaises(ValueError):
            ScenarioGenerator(seed=SEED, target_ids=["not-a-real-target"])
        with self.assertRaises(ValueError):
            self.generator().generate(0)


if __name__ == "__main__":
    unittest.main()
