from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v0.9.0"))

from interoperability.python_adapter.document_v09 import (
    document_to_kernel_v09, kernel_v09_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_evidence_v09 import (
    AlignmentStatus, SemanticSupportStatus, ReferenceSpace, TypedReference,
    EvidenceSpan,
)


class KernelV09DocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": "test:document",
            "sources": [{"id": "s:1", "text": "😀The exact quoted phrase appears here."}],
            "primarySourceRef": "s:1",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [], "mentions": [],
            "expressions": [{"id": "x:1", "op": "LIT", "sort": "PROP", "operandRefs": [], "params": {}}],
            "rootExpressionRefs": ["x:1"], "assertions": [],
            "evidence": [{
                "id": "e:1", "sourceRef": "s:1",
                "span": {"sourceRef": "s:1", "start": 1, "end": 5, "offsetUnit": "unicode_code_point"},
                "quote": "The ", "alignmentStatus": "EXACT",
                "semanticSupportStatus": "NOT_ESTABLISHED",
                "supportingRuleRefs": ["rule:2", "rule:1", "rule:2"],
                "nativeVerificationMeaning": "alignment only",
            }],
            "contexts": [], "expressionRelations": [], "unresolvedItems": [], "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_exact_evidence_fields_and_source_reference_project(self):
        imported = document_to_kernel_v09(self.make_document(), validate=False)
        item = imported.evidence["e:1"]
        self.assertEqual(item.source_ref.space, ReferenceSpace.SOURCE)
        self.assertEqual(item.span.start, 1)
        self.assertEqual(item.span.end, 5)
        self.assertEqual(item.span.offset_unit, "unicode_code_point")
        self.assertEqual(item.quote, "The ")
        self.assertEqual(item.alignment_status, AlignmentStatus.EXACT)
        self.assertEqual(item.semantic_support_status, SemanticSupportStatus.NOT_ESTABLISHED)
        self.assertEqual(item.supporting_rule_refs, ("rule:2", "rule:1", "rule:2"))
        self.assertEqual(imported.mapping_report["targetVersion"], "0.9.0")

    def test_exact_alignment_does_not_promote_semantic_support(self):
        item = document_to_kernel_v09(self.make_document(), validate=False).evidence["e:1"]
        self.assertEqual(item.alignment_status, AlignmentStatus.EXACT)
        self.assertEqual(item.semantic_support_status, SemanticSupportStatus.NOT_ESTABLISHED)

    def test_unknown_required_status_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["evidence"][0]["semanticSupportStatus"] = "FUTURE_STATUS"
        imported = document_to_kernel_v09(doc, validate=False)
        self.assertNotIn("e:1", imported.evidence)
        self.assertEqual(imported.record_mapping["evidence"]["records"]["e:1"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v09_document_to_contract(imported, validate=False)["evidence"], doc["evidence"])

    def test_dangling_source_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["evidence"][0]["sourceRef"] = "missing:source"
        imported = document_to_kernel_v09(doc, validate=False)
        self.assertNotIn("e:1", imported.evidence)
        self.assertEqual(kernel_v09_document_to_contract(imported, validate=False)["evidence"], doc["evidence"])

    def test_span_source_must_match_evidence_source(self):
        doc = self.make_document()
        doc["evidence"][0]["span"]["sourceRef"] = "other:source"
        imported = document_to_kernel_v09(doc, validate=False)
        self.assertNotIn("e:1", imported.evidence)

    def test_invalid_span_keeps_record_canonical_only(self):
        for start, end in ((-1, 2), (3, 3), (4, 2)):
            with self.subTest(start=start, end=end):
                doc = self.make_document()
                doc["evidence"][0]["span"].update(start=start, end=end)
                imported = document_to_kernel_v09(doc, validate=False)
                self.assertNotIn("e:1", imported.evidence)

    def test_unknown_span_metadata_is_preserved_as_partial(self):
        doc = self.make_document()
        doc["evidence"][0]["span"]["futureField"] = "keep"
        imported = document_to_kernel_v09(doc, validate=False)
        self.assertIn("e:1", imported.evidence)
        entry = imported.record_mapping["evidence"]["records"]["e:1"]
        self.assertEqual(entry["status"], "PARTIAL")
        self.assertIn("span.futureField", entry["unmappedFields"])
        self.assertEqual(kernel_v09_document_to_contract(imported, validate=False)["evidence"], doc["evidence"])

    def test_unknown_top_level_metadata_is_preserved_as_partial(self):
        doc = self.make_document()
        doc["evidence"][0]["futureField"] = {"preserve": True}
        imported = document_to_kernel_v09(doc, validate=False)
        self.assertEqual(imported.record_mapping["evidence"]["records"]["e:1"]["status"], "PARTIAL")
        self.assertEqual(kernel_v09_document_to_contract(imported, validate=False)["evidence"], doc["evidence"])

    def test_non_string_rule_reference_list_is_not_coerced(self):
        doc = self.make_document()
        doc["evidence"][0]["supportingRuleRefs"] = ["rule:1", 7]
        imported = document_to_kernel_v09(doc, validate=False)
        self.assertEqual(imported.evidence["e:1"].supporting_rule_refs, ())
        self.assertIn("supportingRuleRefs", imported.record_mapping["evidence"]["records"]["e:1"]["unmappedFields"])
        self.assertEqual(kernel_v09_document_to_contract(imported, validate=False)["evidence"], doc["evidence"])

    def test_native_edits_merge_only_into_evidence_and_preserve_sidecars(self):
        doc = self.make_document()
        doc["evidence"][0]["legacyMetadata"] = "keep"
        imported = document_to_kernel_v09(doc, validate=False)
        old = imported.evidence["e:1"]
        imported.evidence["e:1"] = replace(
            old,
            quote="updated quote",
            alignment_status=AlignmentStatus.UNVERIFIED,
            semantic_support_status=SemanticSupportStatus.PROPOSED,
            supporting_rule_refs=("rule:3", "rule:2", "rule:3"),
            native_verification_meaning="updated note",
        )
        out = kernel_v09_document_to_contract(imported, validate=False)
        item = out["evidence"][0]
        self.assertEqual(item["quote"], "updated quote")
        self.assertEqual(item["alignmentStatus"], "UNVERIFIED")
        self.assertEqual(item["semanticSupportStatus"], "PROPOSED")
        self.assertEqual(item["supportingRuleRefs"], ["rule:3", "rule:2", "rule:3"])
        self.assertEqual(item["nativeVerificationMeaning"], "updated note")
        self.assertEqual(item["legacyMetadata"], "keep")
        self.assertEqual(out["expressions"], doc["expressions"])
        self.assertEqual(out["sources"], doc["sources"])
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_changed_source_must_resolve(self):
        imported = document_to_kernel_v09(self.make_document(), validate=False)
        old = imported.evidence["e:1"]
        missing = TypedReference(ReferenceSpace.SOURCE, "missing:source")
        imported.evidence["e:1"] = replace(
            old, source_ref=missing,
            span=EvidenceSpan(missing, old.span.start, old.span.end))
        with self.assertRaises(ContractMappingError):
            kernel_v09_document_to_contract(imported, validate=False)

    def test_changed_source_without_matching_span_is_rejected(self):
        doc = self.make_document()
        doc["sources"].append({"id": "s:2", "text": "other"})
        imported = document_to_kernel_v09(doc, validate=False)
        old = imported.evidence["e:1"]
        with self.assertRaises(ValueError):
            replace(old, source_ref=TypedReference(ReferenceSpace.SOURCE, "s:2"))

    def test_changed_span_must_match_source_reference(self):
        imported = document_to_kernel_v09(self.make_document(), validate=False)
        old = imported.evidence["e:1"]
        other = TypedReference(ReferenceSpace.SOURCE, "s:1")
        imported.evidence["e:1"] = replace(
            old, span=EvidenceSpan(other, 2, 4))
        out = kernel_v09_document_to_contract(imported, validate=False)
        self.assertEqual(out["evidence"][0]["span"]["start"], 2)

    def test_wrong_reference_space_is_rejected(self):
        imported = document_to_kernel_v09(self.make_document(), validate=False)
        old = imported.evidence["e:1"]
        with self.assertRaises(ValueError):
            replace(old, source_ref=TypedReference(ReferenceSpace.EVIDENCE, "e:1"))

    def test_stale_snapshot_is_rejected(self):
        imported = document_to_kernel_v09(self.make_document(), validate=False)
        imported.document["evidence"][0]["quote"] = "changed behind adapter"
        with self.assertRaises(ContractMappingError):
            kernel_v09_document_to_contract(imported, validate=False)

    def test_non_evidence_records_remain_canonical_only(self):
        imported = document_to_kernel_v09(self.make_document(), validate=False)
        self.assertEqual(imported.record_mapping["expressions"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v09_document_to_contract(imported, validate=False)["sources"], self.make_document()["sources"])


if __name__ == "__main__":
    unittest.main()
