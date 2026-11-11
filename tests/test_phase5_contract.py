"""Frozen Phase 5 interpretation contract invariants."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "documentation" / "PHASE-5-STEP-5.1-INTERPRETATION-EXPANSION-CONTRACT.md"


class Phase5ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CONTRACT.read_text(encoding="utf-8")

    def test_contract_version_and_compatibility_boundaries_are_frozen(self):
        self.assertIn("USG-INTERPRET/0.2.0", self.text)
        self.assertIn("USG-INTERPRET/0.1.0", self.text)
        self.assertIn("USG-SEM/1.0", self.text)
        self.assertIn("SQLite", self.text)
        self.assertIn("Phase 5A–5Y", self.text)

    def test_all_completion_statuses_are_defined(self):
        for status in (
            "COMPLETE", "PARTIAL", "AMBIGUOUS", "UNSUPPORTED",
            "INVALID_INPUT", "INCOMPLETE_RESOURCE_LIMIT", "FAILED_VALIDATION",
        ):
            self.assertIn(f"`{status}`", self.text)

    def test_source_fidelity_and_conservative_scope_are_normative(self):
        for phrase in (
            "Unicode code-point", "source[start:end] == surface_text",
            "MUST NOT", "association weight", "every conjunct/disjunct",
            "human-review", "unsupported inference",
        ):
            self.assertIn(phrase, self.text)

    def test_benchmark_thresholds_and_next_gate_are_present(self):
        for phrase in ("20 positive", "20 negative/adversarial", "10 ambiguous/boundary",
                       "100%", "0.95", "0.90", "Step 5.2"):
            self.assertIn(phrase, self.text)


if __name__ == "__main__":
    unittest.main()
