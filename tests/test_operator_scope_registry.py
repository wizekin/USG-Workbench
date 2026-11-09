"""Source-backed conformance checks for USG-OSR/1.0."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "interoperability/operator-scope-registry/v1.0.0.json"
SCHEMA_PATH = ROOT / "specifications/operator-scope-registry-1.0.schema.json"
WB_CORE = ROOT / "implementations/semantic-workbench-js/v0.5.4/semantic-core.js"
WB_COMPOSER = ROOT / "implementations/semantic-workbench-js/v0.5.4/semantic-composer.js"
PY_NODE = ROOT / "implementations/python-kernel/v0.4.0/usg/grammar/node.py"


class OperatorScopeRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.core = WB_CORE.read_text(encoding="utf-8")
        cls.composer = WB_COMPOSER.read_text(encoding="utf-8")
        cls.python = PY_NODE.read_text(encoding="utf-8")

    def test_registry_identity_and_baseline_versions(self):
        self.assertEqual(self.registry["registryId"], "USG-OSR/1.0")
        self.assertEqual(self.registry["registryVersion"], "1.0.0")
        self.assertEqual(self.registry["baselines"]["workbench"]["version"], "0.5.4")
        self.assertEqual(self.registry["baselines"]["pythonKernel"]["version"], "0.4.0")
        self.assertEqual(self.schema["properties"]["registryId"]["const"], "USG-OSR/1.0")

    def test_operator_dispositions_are_unique_and_source_declared(self):
        entries = self.registry["operatorMappings"]
        keys = [(e["sourceType"], e["sourceOperatorType"], e["sourceOperator"]) for e in entries]
        self.assertEqual(len(keys), len(set(keys)))
        for entry in entries:
            self.assertIn(entry["status"], {"EXACT", "CONDITIONAL_EXACT", "PARTIAL_ONLY", "UNSUPPORTED"})
            self.assertIn(entry["sourceType"], {"OPERATOR"})
            self.assertTrue(entry["conditions"] is not None)
            if entry["status"] in {"PARTIAL_ONLY", "UNSUPPORTED"}:
                self.assertIsNone(entry["target"])
        self.assertIn("MODAL_OPERATORS", self.core)
        for modal in ("MIGHT", "MAY", "COULD", "CAN", "MUST", "SHOULD", "WILL", "WOULD", "EXPECTED", "UNKNOWN"):
            self.assertRegex(self.core, rf"['"]{modal}['"]")
        self.assertIn("NEGATION", self.core)
        self.assertIn("POLARITY", self.core)
        self.assertIn("UNRESOLVED_SCOPE", self.core)

    def test_python_modal_and_operator_signatures_exist(self):
        for operator in ("NOT", "AND", "OR", "COND", "IMPLIES", "Q", "MODAL", "TENSE"):
            self.assertRegex(self.python, rf'"{operator}": Sig\\(')
        self.assertIn('"force"', self.python)
        self.assertIn('"flavor"', self.python)
        self.assertIn("FORCES = frozenset", self.python)
        self.assertIn("FLAVORS = frozenset", self.python)
        self.assertIn("QUANTIFIERS = frozenset", self.python)

    def test_quantifier_mappings_preserve_distinct_scope_forms(self):
        entries = {e["sourceOperator"]: e for e in self.registry["quantifierMappings"]}
        for name in ("FORALL", "EXISTS", "EXACTLY_ONE", "AT_LEAST_ONE", "AT_MOST_ONE", "NO", "NOT(FORALL)", "UNKNOWN"):
            self.assertIn(name, entries)
        self.assertEqual(entries["NO"]["target"]["scopeTransform"], "NOT(scope)")
        self.assertEqual(entries["NOT(FORALL)"]["target"]["operator"], "NOT")
        self.assertIn("FORALL", self.core)
        self.assertIn("EXACTLY_ONE", self.core)

    def test_connective_mappings_preserve_conditional_and_unless(self):
        entries = {e["sourceConnective"]: e for e in self.registry["connectiveMappings"]}
        for name in ("AND", "OR", "CONDITIONAL", "EXCEPTION", "WHEN", "CONCESSIVE", "CONTRAST"):
            self.assertIn(name, entries)
        self.assertEqual(entries["CONDITIONAL"]["target"]["operator"], "COND")
        self.assertEqual(entries["EXCEPTION"]["target"]["operator"], "COND")
        self.assertEqual(entries["EXCEPTION"]["target"]["antecedentTransform"], "identity")
        self.assertIn("negated_exception_condition_equivalent_to_if_not_P_then_Q", self.core)
        self.assertIn("exception_relation_asserted", self.core)
        self.assertIn("conditional_not_asserted", self.core)
        self.assertIn("CONDITIONAL", self.composer)
        self.assertIn("unless", self.composer.lower())

    def test_scope_policy_forbids_loss_and_confusion(self):
        policy = self.registry["policy"]
        self.assertIn("Never drop", policy["lossBehavior"])
        self.assertIn("IMPLIES", policy["lossBehavior"])
        requirements = " ".join(self.registry["scopePolicy"]["requirements"])
        for phrase in ("nesting order", "cycles", "missing targets", "disconnected"):
            self.assertIn(phrase, requirements)


if __name__ == "__main__":
    unittest.main()
