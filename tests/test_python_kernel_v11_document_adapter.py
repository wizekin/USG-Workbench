from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.1.0"))

from interoperability.python_adapter.document_v11 import (
    document_to_kernel_v11, kernel_v11_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_expression_relation_v11 import (
    ReferenceSpace, RelationType, TypedReference, VerificationStatus,
)


class KernelV11ExpressionRelationDocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0", "documentId": "test:doc",
            "sources": [{"id": "s:1", "text": "source"}], "primarySourceRef": "s:1",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [], "mentions": [],
            "expressions": [
                {"id": "x:1", "op": "LIT", "sort": "PROP", "operandRefs": [], "params": {}},
                {"id": "x:2", "op": "LIT", "sort": "PROP", "operandRefs": [], "params": {}},
            ],
            "rootExpressionRefs": ["x:1", "x:2"], "assertions": [],
            "evidence": [{"id": "e:1", "sourceRef": "s:1",
                "span": {"sourceRef": "s:1", "start": 0, "end": 1, "offsetUnit": "unicode_code_point"},
                "quote": "s", "alignmentStatus": "EXACT",
                "semanticSupportStatus": "NOT_ESTABLISHED"}],
            "contexts": [],
            "expressionRelations": [{
                "id": "rel:1", "type": "SUPPORTS",
                "sourceExpressionRef": "x:1", "targetExpressionRef": "x:2",
                "verificationStatus": "NOT_INDEPENDENTLY_VERIFIED",
                "evidenceRefs": ["e:1", "e:1"],
                "attribution": {"speakerRef": "r:1", "scope": {"kind": "belief"}},
            }],
            "unresolvedItems": [], "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_exact_relation_fields_and_typed_references_project(self):
        item = document_to_kernel_v11(self.make_document(), validate=False).expression_relations["rel:1"]
        self.assertEqual(item.relation_type, RelationType.SUPPORTS)
        self.assertEqual(item.source_expression_ref, TypedReference(ReferenceSpace.EXPRESSION, "x:1"))
        self.assertEqual(item.target_expression_ref, TypedReference(ReferenceSpace.EXPRESSION, "x:2"))
        self.assertEqual(item.verification_status, VerificationStatus.NOT_INDEPENDENTLY_VERIFIED)
        self.assertEqual(item.evidence_refs, (
            TypedReference(ReferenceSpace.EVIDENCE, "e:1"),
            TypedReference(ReferenceSpace.EVIDENCE, "e:1"),
        ))
        self.assertEqual(item.attribution["scope"]["kind"], "belief")

    def test_all_relation_types_and_verification_statuses_project(self):
        for relation_type in RelationType:
            for status in VerificationStatus:
                with self.subTest(relation_type=relation_type, status=status):
                    doc = self.make_document()
                    doc["expressionRelations"][0]["type"] = relation_type.value
                    doc["expressionRelations"][0]["verificationStatus"] = status.value
                    item = document_to_kernel_v11(doc, validate=False).expression_relations["rel:1"]
                    self.assertEqual(item.relation_type, relation_type)
                    self.assertEqual(item.verification_status, status)

    def test_dangling_source_expression_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["sourceExpressionRef"] = "missing:x"
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertNotIn("rel:1", imported.expression_relations)
        self.assertEqual(kernel_v11_document_to_contract(imported, validate=False)["expressionRelations"], doc["expressionRelations"])

    def test_dangling_target_expression_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["targetExpressionRef"] = "missing:x"
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertNotIn("rel:1", imported.expression_relations)

    def test_dangling_evidence_ref_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["evidenceRefs"] = ["missing:e"]
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertNotIn("rel:1", imported.expression_relations)

    def test_unknown_type_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["type"] = "FUTURE_RELATION"
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertNotIn("rel:1", imported.expression_relations)

    def test_unknown_status_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["verificationStatus"] = "FUTURE_STATUS"
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertNotIn("rel:1", imported.expression_relations)

    def test_unknown_properties_are_partial_and_preserved(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["futureField"] = {"keep": True}
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertEqual(imported.record_mapping["expressionRelations"]["records"]["rel:1"]["status"], "PARTIAL")
        self.assertEqual(kernel_v11_document_to_contract(imported, validate=False)["expressionRelations"], doc["expressionRelations"])

    def test_native_edits_merge_only_into_expression_relations(self):
        doc = self.make_document()
        doc["expressionRelations"][0]["legacyField"] = "keep"
        imported = document_to_kernel_v11(doc, validate=False)
        old = imported.expression_relations["rel:1"]
        imported.expression_relations["rel:1"] = replace(
            old, relation_type=RelationType.CAUSE,
            verification_status=VerificationStatus.DISPUTED,
            evidence_refs=(TypedReference(ReferenceSpace.EVIDENCE, "e:1"),),
            attribution={"edited": True},
        )
        out = kernel_v11_document_to_contract(imported, validate=False)
        item = out["expressionRelations"][0]
        self.assertEqual(item["type"], "CAUSE")
        self.assertEqual(item["verificationStatus"], "DISPUTED")
        self.assertEqual(item["evidenceRefs"], ["e:1"])
        self.assertEqual(item["attribution"], {"edited": True})
        self.assertEqual(item["legacyField"], "keep")
        self.assertEqual(out["expressions"], doc["expressions"])
        self.assertEqual(out["evidence"], doc["evidence"])
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_changed_expression_reference_must_resolve(self):
        imported = document_to_kernel_v11(self.make_document(), validate=False)
        old = imported.expression_relations["rel:1"]
        missing = TypedReference(ReferenceSpace.EXPRESSION, "missing:x")
        imported.expression_relations["rel:1"] = replace(old, source_expression_ref=missing)
        with self.assertRaises(ContractMappingError):
            kernel_v11_document_to_contract(imported, validate=False)

    def test_changed_evidence_reference_must_resolve(self):
        imported = document_to_kernel_v11(self.make_document(), validate=False)
        old = imported.expression_relations["rel:1"]
        missing = TypedReference(ReferenceSpace.EVIDENCE, "missing:e")
        imported.expression_relations["rel:1"] = replace(old, evidence_refs=(missing,))
        with self.assertRaises(ContractMappingError):
            kernel_v11_document_to_contract(imported, validate=False)

    def test_wrong_reference_space_is_rejected_by_native_model(self):
        imported = document_to_kernel_v11(self.make_document(), validate=False)
        old = imported.expression_relations["rel:1"]
        wrong = TypedReference(ReferenceSpace.EVIDENCE, "e:1")
        with self.assertRaises(ValueError):
            replace(old, source_expression_ref=wrong)

    def test_stale_canonical_snapshot_is_rejected(self):
        imported = document_to_kernel_v11(self.make_document(), validate=False)
        imported.document["expressionRelations"][0]["type"] = "CAUSE"
        with self.assertRaises(ContractMappingError):
            kernel_v11_document_to_contract(imported, validate=False)

    def test_non_relation_families_remain_canonical_only(self):
        doc = self.make_document()
        doc["contexts"] = [{"id": "c:1", "kind": "WORLD"}]
        imported = document_to_kernel_v11(doc, validate=False)
        self.assertEqual(imported.record_mapping["contexts"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v11_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_wrong_profile_is_rejected(self):
        doc = self.make_document()
        doc["profileId"] = "USG-SEM/2.0"
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v11(doc, validate=False)

    def test_non_mapping_document_is_rejected(self):
        with self.assertRaises(TypeError):
            document_to_kernel_v11([], validate=False)


if __name__ == "__main__":
    unittest.main()
