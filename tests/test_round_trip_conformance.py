from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "implementations" / "python-kernel" / "v0.4.0"
BRIDGE = ROOT / "tests" / "round_trip_conformance_bridge.js"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(KERNEL))
sys.path.insert(0, str(ROOT / "tests"))

from interoperability.python_adapter import document_to_python
from interoperability.python_adapter.reverse import python_to_contract_document
from test_document_adapter import DocumentAdapterTests


def run_bridge(mode: str, payload: dict | None = None, *args: str) -> dict:
    command = ["node", str(BRIDGE), mode, *args]
    encoded = None if payload is None else json.dumps(payload, ensure_ascii=False)
    completed = subprocess.run(
        command,
        input=encoded,
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    if completed.returncode:
        raise AssertionError(
            f"Workbench bridge failed ({mode}):\n{completed.stderr}\n{completed.stdout}"
        )
    return json.loads(completed.stdout)


class RoundTripSemanticInvariantTests(unittest.TestCase):
    def test_complete_workbench_python_workbench_path_preserves_semantic_invariants(self):
        first = run_bridge("to-contract")
        original_model = first["model"]
        original = first["document"]
        source_report = first["report"]

        self.assertEqual(original["profileId"], "USG-SEM/1.0")
        self.assertEqual(original["sources"][0]["text"], original_model["source"]["text"])
        self.assertEqual(source_report["status"], "PARTIAL",
                         "candidate relation verification must remain explicitly partial")
        by_native = {item.get("nativeId"): item for item in original["expressions"] if item.get("nativeId")}
        holds = next(item for item in original["expressions"]
                     if item["op"] == "HOLDS" and item["operandRefs"] == [by_native["needs"]["id"]])
        self.assertEqual(holds["sort"], "PROP")
        self.assertEqual(by_native["not-needs"]["operandRefs"], [holds["id"]])
        modal = by_native["might-not-needs"]
        self.assertEqual(modal["params"]["force"], "POSSIBILITY")
        self.assertEqual(modal["params"]["flavor"], "EPISTEMIC")
        self.assertEqual(modal["params"]["nativeForce"], "epistemic_possibility")

        imported = document_to_python(original)
        self.assertEqual(imported.sources, {},
                         "Workbench UNKNOWN trust/sensitivity labels must not be coerced into Python enums")
        self.assertIn(original["primarySourceRef"], imported.mapping_report["unmappedRefs"])
        self.assertEqual(imported.mapping_report["status"], "PARTIAL")
        self.assertTrue(imported.mapping_report["unmappedRefs"],
                        "Workbench-only constructors/metadata must be reported, not coerced")
        self.assertEqual(imported.expression_roots, {},
                         "PREDICATE_APP/CONNECTIVE are not native Python 0.4.0 constructors")

        returned = python_to_contract_document(imported)
        self.assertEqual(returned["profileId"], "USG-SEM/1.0")
        self.assertEqual(returned["sources"][0]["text"], original_model["source"]["text"])
        self.assertEqual(returned["rootExpressionRefs"], original["rootExpressionRefs"])
        self.assertEqual(returned["expressions"], original["expressions"],
                         "unsupported graph nodes must survive the Python boundary unchanged")
        self.assertEqual(returned["mapping"]["status"], "PARTIAL")

        final = run_bridge("from-contract", returned)
        reconstructed = final["model"]
        self.assertTrue(final["validation"]["valid"], final["validation"]["errors"])
        self.assertEqual(reconstructed["source"]["text"], original_model["source"]["text"])
        self.assertEqual(reconstructed["rootExpressionIds"], original_model["rootExpressionIds"])
        self.assertEqual(final["report"]["status"], "PARTIAL")
        self.assertFalse(final["report"]["restoredNativeSnapshot"],
                         "Python envelope edits invalidate the stale Workbench native snapshot")
        self.assertFalse(final["report"]["snapshot"]["projectionValid"])

        expressions = {item["id"]: item for item in reconstructed["expressions"]}
        self.assertEqual(expressions["needs"]["predicate"], "NEEDS")
        self.assertEqual(
            [(arg["role"], arg["entityId"]) for arg in expressions["needs"]["arguments"]],
            [("subject", "alice"), ("object", "tool")],
        )
        self.assertEqual(expressions["not-needs"]["operator"], "NOT")
        self.assertEqual(expressions["not-needs"]["scope"]["targetId"], "needs")
        self.assertEqual(expressions["might-not-needs"]["operator"], "MIGHT")
        self.assertEqual(expressions["might-not-needs"]["scope"]["targetId"], "not-needs")

        # NOT(FORALL x P) and NOT(EXISTS x P) are distinct graph structures.
        self.assertEqual(expressions["forall-root"]["operator"], "FORALL")
        self.assertEqual(expressions["forall-root"]["scope"]["targetId"], "needs")
        self.assertEqual(expressions["not-forall-root"]["scope"]["targetId"], "forall-root")
        self.assertEqual(expressions["exists-root"]["operator"], "EXISTS")
        self.assertEqual(expressions["exists-root"]["scope"]["targetId"], "needs")
        self.assertEqual(expressions["no-root"]["scope"]["targetId"], "exists-root")
        self.assertEqual(expressions["forall-root"]["variableBinding"]["variable"], "x")
        self.assertEqual(expressions["forall-root"]["restrictor"]["entityId"], "person-class")

        self.assertEqual(expressions["if-root"]["connective"], "CONDITIONAL")
        self.assertEqual(expressions["if-root"]["antecedentId"], "not-needs")
        self.assertEqual(expressions["if-root"]["consequentId"], "agrees")
        self.assertEqual(expressions["unless-root"]["connective"], "EXCEPTION")
        self.assertEqual(expressions["unless-root"]["marker"], "unless")
        self.assertEqual(expressions["unless-root"]["antecedentId"], "not-needs")
        self.assertEqual(expressions["when-root"]["connective"], "WHEN")
        self.assertEqual(expressions["concessive-root"]["connective"], "CONCESSIVE")
        self.assertNotEqual(expressions["when-root"]["connective"],
                            expressions["concessive-root"]["connective"])

        self.assertEqual(expressions["agrees"]["grammaticalTense"], "past")
        self.assertEqual(expressions["agrees"]["aspect"], "perfect")
        self.assertEqual(expressions["agrees"]["temporalFrame"]["temporalAdverbials"], ["today"])
        self.assertEqual(expressions["needs"]["attribution"]["status"], "source_asserted")
        self.assertEqual(expressions["needs"]["completeness"]["status"], "complete")
        self.assertEqual(reconstructed["mentions"][0]["surfaceText"], "Alice")
        unresolved = next(m for m in reconstructed["mentions"] if m["id"] == "it-mention")
        self.assertIsNone(unresolved["entityId"])
        self.assertEqual(unresolved["resolutionStatus"], "unresolved")
        self.assertEqual(reconstructed["unresolvedItems"][0]["status"], "unresolved")

        # Exact evidence remains aligned, including the supplementary Unicode prefix.
        needs_evidence = next(e for e in reconstructed["evidence"] if e["quote"] == "needs")
        self.assertEqual(reconstructed["source"]["text"][needs_evidence["start"]:needs_evidence["end"]],
                         needs_evidence["quote"])
        self.assertEqual(needs_evidence["quote"], "needs")
        self.assertEqual(reconstructed["relations"][0]["verification"], "candidate_not_proof")
        self.assertEqual(reconstructed["acceptanceBoundary"] if "acceptanceBoundary" in reconstructed else None, None)
        self.assertIsNone(final["report"]["archivalNativeFields"],
                          "a stale native snapshot must not restore workflow-only fields")
        self.assertEqual(returned["assertions"], [],
                         "Workbench attribution must not be fabricated into assertion records")

    def test_python_native_supported_projection_executes_without_coercion(self):
        document = DocumentAdapterTests().make_document()
        imported = document_to_python(document)
        self.assertIn("test:expr:needs", imported.expression_roots)
        self.assertEqual(imported.expression_roots["test:expr:needs"].op, "RELATE")
        self.assertIn("test:assertion", imported.assertions)

        returned = python_to_contract_document(imported)
        root = next(x for x in returned["expressions"] if x["id"] == "test:expr:needs")
        self.assertEqual(root["op"], "RELATE")
        self.assertEqual(root["operandRefs"], ["test:expr:alice", "test:expr:tool"])
        self.assertEqual(returned["assertions"][0]["expressionRef"], "test:expr:needs")
        self.assertEqual(returned["mapping"]["status"], "PARTIAL")

    def test_source_builder_warnings_and_opaque_constructors_remain_explicit(self):
        result = run_bridge("warning")
        self.assertEqual(result["sourceReport"]["status"], "PARTIAL")
        self.assertTrue(any(ref.startswith("wb:warning:")
                            for ref in result["sourceReport"]["unmappedRefs"]))
        self.assertEqual(result["resultReport"]["status"], "PARTIAL")
        self.assertTrue(result["resultReport"]["unmappedRefs"])

    def test_canonical_edits_override_stale_native_payload(self):
        first = run_bridge("to-contract")
        document = copy.deepcopy(first["document"])
        needs = next(x for x in document["expressions"] if x.get("nativeId") == "needs")
        needs["params"]["predicate"] = "WANTS"
        needs["params"]["eventFrame"]["predicate"] = "WANTS"
        result = run_bridge("from-contract", document)
        self.assertTrue(result["validation"]["valid"], result["validation"]["errors"])
        self.assertEqual(next(x for x in result["model"]["expressions"] if x["id"] == "needs")["predicate"],
                         "WANTS")
        self.assertEqual(result["report"]["status"], "PARTIAL")
        self.assertFalse(result["report"]["snapshot"]["projectionValid"])
        self.assertFalse(result["report"]["restoredNativeSnapshot"])

    def test_large_multi_root_graph_has_no_semantic_count_cap(self):
        result = run_bridge("large", None, "512")
        self.assertEqual(result["inputCount"], 512)
        self.assertEqual(result["canonicalCount"], 1536,
                         "512 predications plus two ordered argument nodes each")
        self.assertEqual(result["outputCount"], 512)
        self.assertEqual(result["rootCount"], 512)
        self.assertTrue(result["validation"]["valid"], result["validation"]["errors"])


if __name__ == "__main__":
    unittest.main()
