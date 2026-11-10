from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "implementations" / "python-kernel" / "v0.5.0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(KERNEL))

from interoperability.python_adapter.kernel_v05 import (
    contract_graph_roots_to_kernel_v05_partial,
    contract_graph_roots_to_kernel_v05,
    kernel_v05_graph_to_contract,
)
from usg.grammar.node import inference_eligible, metadata_value
from usg.grammar.scope import alpha_equivalent, check_native_scope


def expression(node_id, op, sort, operands=(), params=None, **extra):
    return {"id": node_id, "op": op, "sort": sort,
            "operandRefs": list(operands), "params": params or {}, **extra}


class KernelV05AdapterTests(unittest.TestCase):
    def fixture(self):
        return [
            expression("e:alice", "REF", "TERM", params={"ref": "REFERENT:1"}),
            expression("e:tool", "REF", "TERM", params={"ref": "REFERENT:2"}),
            expression("e:pred", "PREDICATE_APP", "SIT", ["e:alice", "e:tool"], {
                "predicate": "NEEDS", "roles": ["SUBJECT", "OBJECT"],
                "argumentRequirements": {"requiredRoles": ["SUBJECT", "OBJECT"]},
                "temporalFrame": {"tense": "present", "aspect": "simple"},
                "evidenceRefs": ["evidence:1"],
            }, semanticKind="STATE", interpretationStatus="SOURCE_PROPOSED", nativeId="wb:pred"),
            expression("e:holds", "HOLDS", "PROP", ["e:pred"]),
            expression("e:other", "NOT", "PROP", ["e:holds"]),
            expression("e:conn", "CONNECTIVE", "PROP", ["e:holds", "e:other"], {
                "connective": "CONCESSIVE", "operandRoles": ["concession", "main"],
                "marker": "although", "logicalStatus": "SOURCE_ASSERTED",
            }),
            expression("e:x", "VAR", "TERM", params={"name": "x", "binderId": "binder:1"}),
            expression("e:person", "REF", "TERM", params={"ref": "REFERENT:3"}),
            expression("e:body", "RELATE", "PROP", ["e:x", "e:person"], {"relation": "OWNS"}),
            expression("e:q", "QUANTIFIER", "PROP", ["e:body"], {
                "operatorType": "GENERAL", "operator": "FORALL", "binderId": "binder:1",
                "variable": "x", "scopeKind": "WHOLE_EXPRESSION",
                "restrictor": {"kind": "CLASS", "referent": "REFERENT:3"},
                "variableBinding": {"binderId": "binder:1", "variable": "x", "role": "owner"},
                "surfaceText": "every person",
            }),
        ]

    def test_native_three_constructors_preserve_sorts_roles_order_and_metadata(self):
        data = self.fixture()
        result = contract_graph_roots_to_kernel_v05_partial(data, ["e:pred", "e:conn", "e:q"])
        self.assertFalse(result.failed_roots)
        pred, conn, quant = (result.roots[x] for x in ("e:pred", "e:conn", "e:q"))
        self.assertEqual(pred.op, "PREDICATE_APP")
        self.assertEqual(pred.sort.value, "SIT")
        self.assertEqual(pred.get("roles"), ("SUBJECT", "OBJECT"))
        self.assertEqual(metadata_value(pred, "temporalFrame"), {"tense": "present", "aspect": "simple"})
        self.assertEqual(conn.sort.value, "PROP")
        self.assertEqual(conn.get("connective"), "CONCESSIVE")
        self.assertEqual(conn.get("operandRoles"), ("concession", "main"))
        self.assertEqual(quant.sort.value, "PROP")
        self.assertEqual(quant.get("binderId"), "binder:1")
        self.assertEqual(metadata_value(quant, "restrictor"), {"kind": "CLASS", "referent": "REFERENT:3"})
        self.assertEqual(check_native_scope(quant), [])

    def test_reverse_serialization_round_trips_native_constructs_and_sidecar_fields(self):
        result = contract_graph_roots_to_kernel_v05_partial(self.fixture(), ["e:pred", "e:conn", "e:q"])
        doc = kernel_v05_graph_to_contract(result)
        by_id = {item["id"]: item for item in doc["expressions"]}
        self.assertEqual(doc["rootExpressionRefs"], ["e:pred", "e:conn", "e:q"])
        self.assertEqual(by_id["e:pred"]["sort"], "SIT")
        self.assertEqual(by_id["e:pred"]["params"]["roles"], ["SUBJECT", "OBJECT"])
        self.assertEqual(by_id["e:pred"]["params"]["temporalFrame"], {"tense": "present", "aspect": "simple"})
        self.assertEqual(by_id["e:pred"]["semanticKind"], "STATE")
        self.assertEqual(by_id["e:pred"]["nativeId"], "wb:pred")
        self.assertEqual(by_id["e:conn"]["params"]["connective"], "CONCESSIVE")
        self.assertEqual(by_id["e:q"]["params"]["variableBinding"]["binderId"], "binder:1")
        self.assertEqual(doc["mapping"]["status"], "LOSSLESS")

    def test_quantifier_alpha_equivalence_uses_binding_identity_not_display_name(self):
        data = self.fixture()
        left = contract_graph_roots_to_kernel_v05(data, ["e:q"])["e:q"]
        changed = [dict(item) for item in data]
        for item in changed:
            if item["id"] == "e:x":
                item["params"] = {"name": "person", "binderId": "binder:2"}
            if item["id"] == "e:body":
                item["operandRefs"] = ["e:x", "e:person"]
            if item["id"] == "e:q":
                item["params"] = dict(item["params"], binderId="binder:2", variable="person",
                    variableBinding={"binderId": "binder:2", "variable": "person", "role": "owner"})
        right = contract_graph_roots_to_kernel_v05(changed, ["e:q"])["e:q"]
        self.assertTrue(alpha_equivalent(left, right))

    def test_unknown_operator_is_preserved_as_opaque_and_never_inference_eligible(self):
        data = self.fixture() + [
            expression("e:new", "FUTURE_OPERATOR", "PROP", ["e:holds"], {"novel": "value"})
        ]
        result = contract_graph_roots_to_kernel_v05_partial(data, ["e:new"])
        self.assertFalse(result.failed_roots)
        self.assertEqual(result.roots["e:new"].op, "OPAQUE")
        self.assertFalse(inference_eligible(result.roots["e:new"]))
        self.assertIn("e:new", result.mapping_report["unmappedRefs"])
        out = kernel_v05_graph_to_contract(result)
        opaque = next(item for item in out["expressions"] if item["id"] == "e:new")
        self.assertEqual(opaque["op"], "OPAQUE")
        self.assertEqual(opaque["params"]["sourceOp"], "FUTURE_OPERATOR")
        self.assertEqual(opaque["params"]["payload"]["params"], {"novel": "value"})

    def test_invalid_known_node_is_not_silently_downgraded_to_opaque(self):
        data = self.fixture() + [
            expression("e:bad", "CONNECTIVE", "PROP", ["e:holds", "e:other"], {
                "connective": "CONDITIONAL", "operandRoles": ["consequent", "antecedent"]
            })
        ]
        result = contract_graph_roots_to_kernel_v05_partial(data, ["e:bad"])
        self.assertIn("e:bad", result.failed_roots)
        self.assertNotIn("e:bad", result.roots)
        out = kernel_v05_graph_to_contract(result)
        self.assertIn("e:bad", out["rootExpressionRefs"])
        retained = {item["id"] for item in out["expressions"]}
        self.assertIn("e:bad", retained)
        self.assertIn("e:holds", retained)
        self.assertIn("e:bad", out["mapping"]["unmappedRefs"])

    def test_shared_dag_identity_is_preserved(self):
        data = self.fixture()
        result = contract_graph_roots_to_kernel_v05(data, ["e:conn"])
        self.assertIs(result["e:conn"].args[0], result["e:conn"].args[1].args[0])

    def test_unresolved_reference_is_distinct_from_opaque(self):
        data = self.fixture() + [
            expression("e:unresolved", "UNRESOLVED_REF", "ANY", params={
                "referenceId": "mention:it", "reason": "antecedent unknown", "sourceSort": "TERM",
                "role": "OBJECT",
            })
        ]
        result = contract_graph_roots_to_kernel_v05_partial(data, ["e:unresolved"])
        node = result.roots["e:unresolved"]
        self.assertEqual(node.op, "UNRESOLVED_REF")
        self.assertFalse(inference_eligible(node))


if __name__ == "__main__":
    unittest.main()
