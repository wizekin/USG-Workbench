from __future__ import annotations

import copy
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "implementations" / "python-kernel" / "v0.4.0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(KERNEL))
sys.path.insert(0, str(ROOT / "tests"))

from test_document_adapter import DocumentAdapterTests
from interoperability.python_adapter import ContractMappingError, document_to_python
from interoperability.python_adapter.reverse import python_to_contract_document
from usg.grammar.node import Ann, Node


class PythonReverseSerializerTests(unittest.TestCase):
    def imported_fixture(self):
        return document_to_python(DocumentAdapterTests().make_document())

    def test_current_native_projections_are_serialized_and_schema_validated(self):
        imported = self.imported_fixture()
        result = python_to_contract_document(imported)
        self.assertEqual(result["profileId"], "USG-SEM/1.0")
        self.assertEqual(result["sources"][0]["text"], "Alice needs the tool.")
        self.assertEqual(result["rootExpressionRefs"], ["test:expr:needs"])
        root = next(x for x in result["expressions"] if x["id"] == "test:expr:needs")
        self.assertEqual(root["op"], "RELATE")
        self.assertEqual(root["operandRefs"], ["test:expr:alice", "test:expr:tool"])
        self.assertEqual(result["assertions"][0]["expressionRef"], "test:expr:needs")
        self.assertEqual(result["mapping"]["status"], "PARTIAL")
        self.assertIn("test:referent:alice", result["mapping"]["unmappedRefs"])

    def test_modified_python_node_is_serialized_not_replaced_by_snapshot(self):
        imported = self.imported_fixture()
        original = imported.expression_roots["test:expr:needs"]
        imported.expression_roots["test:expr:needs"] = Node("NOT", (original,))
        result = python_to_contract_document(imported)
        new_root = result["rootExpressionRefs"][0]
        self.assertTrue(new_root.startswith("py:node:"))
        record = next(x for x in result["expressions"] if x["id"] == new_root)
        self.assertEqual(record["op"], "NOT")
        self.assertEqual(record["operandRefs"], ["test:expr:needs"])
        self.assertEqual(result["assertions"][0]["expressionRef"], new_root)

    def test_annotation_source_association_is_not_guessed_after_span_change(self):
        imported = self.imported_fixture()
        original = imported.expression_roots["test:expr:needs"]
        imported.expression_roots["test:expr:needs"] = original.with_ann(
            Ann(spans=((1, 3),), rules=("changed-rule",), basis="EXPLICIT")
        )
        result = python_to_contract_document(imported)
        self.assertEqual(result["mapping"]["status"], "PARTIAL")
        namespace = result["extensions"]["org.usg.python-kernel.v0.4.0"]
        preservation = namespace["reverseSerializerPreservation"]
        archived_nodes = [key for key in preservation if key.startswith("py:node:")]
        self.assertTrue(archived_nodes)
        self.assertIn("nativeAnnotation", preservation[archived_nodes[0]])

    def test_unsupported_original_roots_and_records_are_preserved(self):
        document = DocumentAdapterTests().make_document()
        document["expressions"].extend([
            {
                "id": "test:expr:unsupported-predicate",
                "op": "PREDICATE_APP",
                "sort": "SIT",
                "operandRefs": [],
                "params": {"predicate": "UNKNOWN", "roles": []},
            },
            {
                "id": "test:expr:unsupported-root",
                "op": "HOLDS",
                "sort": "PROP",
                "operandRefs": ["test:expr:unsupported-predicate"],
                "params": {},
            },
        ])
        document["rootExpressionRefs"].append("test:expr:unsupported-root")
        imported = document_to_python(document)
        result = python_to_contract_document(imported)
        ids = {item["id"] for item in result["expressions"]}
        self.assertIn("test:expr:unsupported-predicate", ids)
        self.assertIn("test:expr:unsupported-root", ids)
        self.assertIn("test:expr:unsupported-root", result["rootExpressionRefs"])
        self.assertIn("test:expr:unsupported-predicate", result["mapping"]["unmappedRefs"])
        self.assertIn("test:expr:unsupported-root", result["mapping"]["unmappedRefs"])

    def test_stale_canonical_snapshot_is_refused(self):
        imported = self.imported_fixture()
        imported.document["extensions"]["changed"] = True
        with self.assertRaises(ContractMappingError):
            python_to_contract_document(imported)


if __name__ == "__main__":
    unittest.main()
