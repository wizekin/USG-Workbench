from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.0.0"))

from interoperability.python_adapter.document_v10 import (
    document_to_kernel_v10, kernel_v10_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_context_v10 import ContextKind, ReferenceSpace, TypedReference


class KernelV10ContextDocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": "test:document",
            "sources": [{"id": "s:1", "text": "The seller believes prices may change."}],
            "primarySourceRef": "s:1",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [{"id": "r:1", "label": "seller"}],
            "mentions": [], "expressions": [], "rootExpressionRefs": [],
            "assertions": [], "evidence": [],
            "contexts": [{
                "id": "c:1", "kind": "HISTORICAL_BELIEF",
                "parentRef": "c:0", "sourceRef": "s:1", "agentRef": "r:1",
                "name": "seller's belief", "metadata": {"scope": {"kind": "belief"}},
            }, {
                "id": "c:0", "kind": "WORLD", "name": "outer world",
            }],
            "expressionRelations": [], "unresolvedItems": [], "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_exact_context_fields_and_typed_references_project(self):
        imported = document_to_kernel_v10(self.make_document(), validate=False)
        item = imported.contexts["c:1"]
        self.assertEqual(item.kind, ContextKind.HISTORICAL_BELIEF)
        self.assertEqual(item.parent_ref, TypedReference(ReferenceSpace.CONTEXT, "c:0"))
        self.assertEqual(item.source_ref, TypedReference(ReferenceSpace.SOURCE, "s:1"))
        self.assertEqual(item.agent_ref, TypedReference(ReferenceSpace.REFERENT, "r:1"))
        self.assertEqual(item.name, "seller's belief")
        self.assertEqual(item.metadata, {"scope": {"kind": "belief"}})
        self.assertEqual(imported.mapping_report["targetVersion"], "1.0.0")

    def test_all_context_kinds_project_without_coercion(self):
        for kind in ContextKind:
            with self.subTest(kind=kind):
                doc = self.make_document()
                doc["contexts"] = [{"id": "c:1", "kind": kind.value}]
                imported = document_to_kernel_v10(doc, validate=False)
                self.assertEqual(imported.contexts["c:1"].kind, kind)

    def test_dangling_parent_keeps_whole_context_canonical_only(self):
        doc = self.make_document()
        doc["contexts"][0]["parentRef"] = "missing:context"
        imported = document_to_kernel_v10(doc, validate=False)
        self.assertNotIn("c:1", imported.contexts)
        self.assertEqual(kernel_v10_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_dangling_source_keeps_whole_context_canonical_only(self):
        doc = self.make_document()
        doc["contexts"][0]["sourceRef"] = "missing:source"
        imported = document_to_kernel_v10(doc, validate=False)
        self.assertNotIn("c:1", imported.contexts)

    def test_dangling_agent_keeps_whole_context_canonical_only(self):
        doc = self.make_document()
        doc["contexts"][0]["agentRef"] = "missing:referent"
        imported = document_to_kernel_v10(doc, validate=False)
        self.assertNotIn("c:1", imported.contexts)

    def test_unknown_kind_keeps_context_canonical_only(self):
        doc = self.make_document()
        doc["contexts"][0]["kind"] = "FUTURE_CONTEXT"
        imported = document_to_kernel_v10(doc, validate=False)
        self.assertNotIn("c:1", imported.contexts)
        self.assertEqual(kernel_v10_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_unknown_context_fields_are_partial_and_preserved(self):
        doc = self.make_document()
        doc["contexts"][0]["futureField"] = {"retain": True}
        imported = document_to_kernel_v10(doc, validate=False)
        self.assertIn("c:1", imported.contexts)
        entry = imported.record_mapping["contexts"]["records"]["c:1"]
        self.assertEqual(entry["status"], "PARTIAL")
        self.assertIn("futureField", entry["unmappedFields"])
        self.assertEqual(kernel_v10_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_optional_fields_remain_absent(self):
        doc = self.make_document()
        doc["contexts"] = [{"id": "c:1", "kind": "UNKNOWN"}]
        item = document_to_kernel_v10(doc, validate=False).contexts["c:1"]
        self.assertIsNone(item.parent_ref)
        self.assertIsNone(item.source_ref)
        self.assertIsNone(item.agent_ref)
        self.assertIsNone(item.name)
        self.assertIsNone(item.metadata)

    def test_native_edits_merge_only_into_context_records(self):
        doc = self.make_document()
        doc["contexts"][0]["legacyField"] = "preserve"
        imported = document_to_kernel_v10(doc, validate=False)
        old = imported.contexts["c:1"]
        imported.contexts["c:1"] = replace(
            old, kind=ContextKind.CONDITIONAL, name="updated",
            metadata={"updated": [1, 2]},
        )
        out = kernel_v10_document_to_contract(imported, validate=False)
        item = next(x for x in out["contexts"] if x["id"] == "c:1")
        self.assertEqual(item["kind"], "CONDITIONAL")
        self.assertEqual(item["name"], "updated")
        self.assertEqual(item["metadata"], {"updated": [1, 2]})
        self.assertEqual(item["legacyField"], "preserve")
        self.assertEqual(out["sources"], doc["sources"])
        self.assertEqual(out["referents"], doc["referents"])
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_changed_parent_must_resolve(self):
        imported = document_to_kernel_v10(self.make_document(), validate=False)
        old = imported.contexts["c:1"]
        missing = TypedReference(ReferenceSpace.CONTEXT, "missing:context")
        imported.contexts["c:1"] = replace(old, parent_ref=missing)
        with self.assertRaises(ContractMappingError):
            kernel_v10_document_to_contract(imported, validate=False)

    def test_changed_source_must_resolve(self):
        imported = document_to_kernel_v10(self.make_document(), validate=False)
        old = imported.contexts["c:1"]
        missing = TypedReference(ReferenceSpace.SOURCE, "missing:source")
        imported.contexts["c:1"] = replace(old, source_ref=missing)
        with self.assertRaises(ContractMappingError):
            kernel_v10_document_to_contract(imported, validate=False)

    def test_changed_agent_must_resolve(self):
        imported = document_to_kernel_v10(self.make_document(), validate=False)
        old = imported.contexts["c:1"]
        missing = TypedReference(ReferenceSpace.REFERENT, "missing:referent")
        imported.contexts["c:1"] = replace(old, agent_ref=missing)
        with self.assertRaises(ContractMappingError):
            kernel_v10_document_to_contract(imported, validate=False)

    def test_wrong_reference_space_is_rejected_by_model(self):
        with self.assertRaises(ValueError):
            TypedReference(ReferenceSpace.SOURCE, "s:1")
            replace(document_to_kernel_v10(self.make_document(), validate=False).contexts["c:1"],
                    parent_ref=TypedReference(ReferenceSpace.SOURCE, "s:1"))

    def test_stale_canonical_snapshot_is_rejected(self):
        imported = document_to_kernel_v10(self.make_document(), validate=False)
        imported.document["contexts"][0]["name"] = "changed behind adapter"
        with self.assertRaises(ContractMappingError):
            kernel_v10_document_to_contract(imported, validate=False)

    def test_non_context_record_families_remain_canonical_only(self):
        doc = self.make_document()
        doc["expressions"] = [{"id": "x:1", "op": "LIT", "sort": "PROP",
                               "operandRefs": [], "params": {}}]
        imported = document_to_kernel_v10(doc, validate=False)
        self.assertEqual(imported.record_mapping["expressions"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v10_document_to_contract(imported, validate=False)["expressions"], doc["expressions"])

    def test_wrong_profile_is_rejected(self):
        doc = self.make_document()
        doc["profileId"] = "USG-SEM/2.0"
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v10(doc, validate=False)

    def test_non_mapping_document_is_rejected(self):
        with self.assertRaises(TypeError):
            document_to_kernel_v10([], validate=False)


if __name__ == "__main__":
    unittest.main()
