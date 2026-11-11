"""Aggregate selected independent tests for the Python reference kernel v0.4.0."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "implementations" / "python-kernel" / "v0.4.0"
sys.path.insert(0, str(KERNEL))

# Import the kernel's own tests package (which contains vhelpers used by
# test_validator) rather than relying on the repository's top-level tests.
from tests import test_core, test_frames, test_grammar, test_validator


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None):
    suite = unittest.TestSuite()
    for module in (test_core, test_frames, test_grammar, test_validator):
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


if __name__ == "__main__":
    unittest.main()
