from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.2.0"))

from interoperability.python_adapter.document_v12 import (
    document_to_kernel_v12, kernel_v12_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_unresolved_v12 import UnresolvedStatus


class KernelV12UnresolvedItemDocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0", "documentId": "test:doc",
            "sources": [{"id": "s:1", "text": "source"}], "primarySourceRef": "s:1",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [], "mentions": [], "expressions": [], "rootExpressionRefs": [],
            "assertions": [],
            "evidence": [{"id": "e:1", "sourceRef": "s:1",
                "span": {"sourceRef": "s:1", "start": 0, "end": 1, "offsetUnit": "unicode_code_point"},
                "quote": "s", "alignmentStatus": "EXACT",
                "semanticSupportStatus": "NOT_ESTABLISHED"}],
            "contexts": [], "expressionRelations": [],
            "unresolvedItems": [{
                "id": "u:1", "status": "AMBIGUOUS", "reason": "Two readings remain",
                "surfaceText": "they", "scopeRef": "opaque:scope",
                "scopeLabel": "local clause", "evidenceRefs": ["e:1", "e:1"],
                "candidateRefs": ["candidate:2", "candidate:1", "candidate:2"],
                "nativeStatus": "parser-ambiguous",
            }],
            "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_exact_fields_and_opaque_references_project(self):
        item = document_to_kernel_v12(self.make_document(), validate=False).unresolved_items["u:1"]
        self.assertEqual(item.status, UnresolvedStatus.AMBIGUOUS)
        self.assertEqual(item.reason, "Two readings remain")
        self.assertEqual(item.scope_ref, "opaque:scope")
        self.assertEqual(item.evidence_refs, ("e:1", "e:1"))
        self.assertEqual(item.candidate_refs, ("candidate:2", "candidate:1", "candidate:2"))
        self.assertEqual(item.native_status, "parser-ambiguous")

    def test_all_statuses_project_without_coercion(self):
        for status in UnresolvedStatus:
            with self.subTest(status=status):
                doc = self.make_document()
                doc["unresolvedItems"][0]["status"] = status.value
                item = document_to_kernel_v12(doc, validate=False).unresolved_items["u:1"]
                self.assertEqual(item.status, status)

    def test_dangling_evidence_ref_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["evidenceRefs"] = ["missing:e"]
        imported = document_to_kernel_v12(doc, validate=False)
        self.assertNotIn("u:1", imported.unresolved_items)
        self.assertEqual(kernel_v12_document_to_contract(imported, validate=False)["unresolvedItems"], doc["unresolvedItems"])

    def test_unknown_status_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["status"] = "FUTURE_STATUS"
        imported = document_to_kernel_v12(doc, validate=False)
        self.assertNotIn("u:1", imported.unresolved_items)

    def test_unknown_properties_are_partial_and_preserved(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["futureField"] = {"keep": True}
        imported = document_to_kernel_v12(doc, validate=False)
        self.assertEqual(imported.record_mapping["unresolvedItems"]["records"]["u:1"]["status"], "PARTIAL")
        self.assertEqual(kernel_v12_document_to_contract(imported, validate=False)["unresolvedItems"], doc["unresolvedItems"])

    def test_candidate_refs_are_opaque_not_resolved_or_retyped(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["candidateRefs"] = ["not-a-known-record-space"]
        item = document_to_kernel_v12(doc, validate=False).unresolved_items["u:1"]
        self.assertEqual(item.candidate_refs, ("not-a-known-record-space",))

    def test_native_edits_merge_only_into_unresolved_items(self):
        doc = self.make_document()
        doc["unresolvedItems"][0]["legacyField"] = "keep"
        imported = document_to_kernel_v12(doc, validate=False)
        old = imported.unresolved_items["u:1"]
        imported.unresolved_items["u:1"] = replace(
            old, status=UnresolvedStatus.INCOMPLETE, reason="more data needed",
            candidate_refs=("candidate:new",), scope_ref="opaque:new-scope",
        )
        out = kernel_v12_document_to_contract(imported, validate=False)
        item = out["unresolvedItems"][0]
        self.assertEqual(item["status"], "INCOMPLETE")
        self.assertEqual(item["reason"], "more data needed")
        self.assertEqual(item["candidateRefs"], ["candidate:new"])
        self.assertEqual(item["scopeRef"], "opaque:new-scope")
        self.assertEqual(item["legacyField"], "keep")
        self.assertEqual(out["evidence"], doc["evidence"])
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_changed_evidence_refs_must_resolve(self):
        imported = document_to_kernel_v12(self.make_document(), validate=False)
        old = imported.unresolved_items["u:1"]
        imported.unresolved_items["u:1"] = replace(old, evidence_refs=("missing:e",))
        with self.assertRaises(ContractMappingError):
            kernel_v12_document_to_contract(imported, validate=False)

    def test_changed_candidate_refs_remain_opaque(self):
        imported = document_to_kernel_v12(self.make_document(), validate=False)
        old = imported.unresolved_items["u:1"]
        imported.unresolved_items["u:1"] = replace(old, candidate_refs=("unknown:space",))
        out = kernel_v12_document_to_contract(imported, validate=False)
        self.assertEqual(out["unresolvedItems"][0]["candidateRefs"], ["unknown:space"])

    def test_stale_canonical_snapshot_is_rejected(self):
        imported = document_to_kernel_v12(self.make_document(), validate=False)
        imported.document["unresolvedItems"][0]["reason"] = "changed"
        with self.assertRaises(ContractMappingError):
            kernel_v12_document_to_contract(imported, validate=False)

    def test_non_unresolved_families_remain_canonical_only(self):
        doc = self.make_document()
        doc["contexts"] = [{"id": "c:1", "kind": "WORLD"}]
        imported = document_to_kernel_v12(doc, validate=False)
        self.assertEqual(imported.record_mapping["contexts"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v12_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_wrong_profile_is_rejected(self):
        doc = self.make_document()
        doc["profileId"] = "USG-SEM/2.0"
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v12(doc, validate=False)

    def test_non_mapping_document_is_rejected(self):
        with self.assertRaises(TypeError):
            document_to_kernel_v12([], validate=False)


if __name__ == "__main__":
    unittest.main()
