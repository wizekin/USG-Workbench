from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.2.1"))
from interoperability.python_adapter.document_v121 import (
    document_to_kernel_v121, kernel_v121_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_unresolved_v121 import ReferenceSpace, TypedReference, UnresolvedStatus


class KernelV121UnresolvedAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0", "documentId": "test:doc",
            "sources": [{"id": "s:1", "text": "Alice.", "language": "en", "offsetUnit": "unicode_code_point"}], "primarySourceRef": "s:1",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [], "mentions": [],
            "expressions": [{"id": "x:1", "op": "LIT", "sort": "VAL", "operandRefs": [], "params": {"value": "Alice", "vtype": "STRING"}}],
            "rootExpressionRefs": ["x:1"], "assertions": [],
            "evidence": [{"id": "e:1", "sourceRef": "s:1",
                "span": {"sourceRef": "s:1", "start": 0, "end": 5, "offsetUnit": "unicode_code_point"},
                "quote": "Alice", "alignmentStatus": "EXACT",
                "semanticSupportStatus": "NOT_ESTABLISHED"}],
            "contexts": [], "expressionRelations": [],
            "unresolvedItems": [{
                "id": "u:1", "status": "AMBIGUOUS", "reason": "Two readings",
                "scopeRef": "x:1", "evidenceRefs": ["e:1", "e:1"],
                "candidateRefs": ["opaque:candidate"],
            }],
            "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": []},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {},
        }

    def test_scope_and_evidence_references_project_with_explicit_types(self):
        item = document_to_kernel_v121(self.make_document(), validate=True).unresolved_items["u:1"]
        self.assertEqual(item.scope_ref, TypedReference(ReferenceSpace.EXPRESSION, "x:1"))
        self.assertEqual(item.evidence_refs, (
            TypedReference(ReferenceSpace.EVIDENCE, "e:1"),
            TypedReference(ReferenceSpace.EVIDENCE, "e:1"),
        ))

    def test_dangling_scope_reference_keeps_item_canonical_only(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["scopeRef"] = "missing:x"
        imported = document_to_kernel_v121(doc, validate=False)
        self.assertNotIn("u:1", imported.unresolved_items)
        self.assertEqual(kernel_v121_document_to_contract(imported, validate=False)["unresolvedItems"], doc["unresolvedItems"])

    def test_dangling_evidence_reference_keeps_item_canonical_only(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["evidenceRefs"] = ["missing:e"]
        imported = document_to_kernel_v121(doc, validate=False)
        self.assertNotIn("u:1", imported.unresolved_items)

    def test_candidate_references_remain_opaque(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["candidateRefs"] = ["no-known-target-space"]
        item = document_to_kernel_v121(doc, validate=True).unresolved_items["u:1"]
        self.assertEqual(item.candidate_refs, ("no-known-target-space",))

    def test_native_scope_edit_must_resolve_to_expression(self):
        imported = document_to_kernel_v121(self.make_document(), validate=True)
        old = imported.unresolved_items["u:1"]
        imported.unresolved_items["u:1"] = replace(
            old, scope_ref=TypedReference(ReferenceSpace.EXPRESSION, "missing:x"))
        with self.assertRaises(ContractMappingError):
            kernel_v121_document_to_contract(imported, validate=False)

    def test_native_evidence_edit_must_resolve(self):
        imported = document_to_kernel_v121(self.make_document(), validate=True)
        old = imported.unresolved_items["u:1"]
        imported.unresolved_items["u:1"] = replace(
            old, evidence_refs=(TypedReference(ReferenceSpace.EVIDENCE, "missing:e"),))
        with self.assertRaises(ContractMappingError):
            kernel_v121_document_to_contract(imported, validate=False)

    def test_native_edit_merges_only_unresolved_item(self):
        doc = self.make_document()
        imported = document_to_kernel_v121(doc, validate=True)
        old = imported.unresolved_items["u:1"]
        imported.unresolved_items["u:1"] = replace(old, status=UnresolvedStatus.INCOMPLETE)
        out = kernel_v121_document_to_contract(imported, validate=True)
        self.assertEqual(out["unresolvedItems"][0]["status"], "INCOMPLETE")
        self.assertEqual(out["expressions"], doc["expressions"])
        self.assertEqual(out["evidence"], doc["evidence"])
        self.assertEqual(out["extensions"], doc["extensions"])


if __name__ == "__main__":
    unittest.main()
