from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from interoperability.python_adapter.document_v07 import (
    document_to_kernel_v07, kernel_v07_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_discourse_v07 import ReferenceSpace, TypedReference, MentionResolutionStatus


class KernelV07DocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        source_text = "😀Alex met Alex."
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": "test:document",
            "sources": [{
                "id": "test:source", "text": source_text, "language": "en",
                "sourceType": "SENTENCE", "trustTier": "STANDARD",
                "sensitivity": "INTERNAL",
                "textHash": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
                "offsetUnit": "unicode_code_point",
            }],
            "primarySourceRef": "test:source",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [
                {"id": "test:referent", "label": "Alex"},
                {"id": "test:referent-2", "label": "Other"},
            ],
            "mentions": [
                {
                    "id": "test:mention-1", "surfaceText": "Alex",
                    "resolutionStatus": "LINKED", "mentionType": "PROPER_NOUN",
                    "referentRef": "test:referent",
                    "sourceSpan": {"sourceRef": "test:source", "start": 1, "end": 5,
                                   "offsetUnit": "unicode_code_point"},
                },
                {
                    "id": "test:mention-2", "surfaceText": "Alex",
                    "resolutionStatus": "RESOLVED",
                    "referentRef": "test:referent",
                    "antecedentMentionRef": "test:mention-1",
                    "antecedentReferentRef": "test:referent",
                    "sourceSpan": {"sourceRef": "test:source", "start": 11, "end": 15,
                                   "offsetUnit": "unicode_code_point"},
                },
            ],
            "expressions": [], "rootExpressionRefs": [],
            "assertions": [], "evidence": [], "contexts": [],
            "expressionRelations": [], "unresolvedItems": [], "derivations": [],
            "validation": {
                "structuralStatus": "NOT_CHECKED", "checks": [],
                "validator": "fixture", "contractVersion": "USG-SEM/1.0",
            },
            "mapping": {
                "sourceProfile": "fixture", "sourceVersion": "1",
                "status": "LOSSLESS", "unmappedRefs": [],
            },
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_exact_mention_fields_and_typed_links_project(self):
        imported = document_to_kernel_v07(self.make_document(), validate=False)
        first = imported.mentions["test:mention-1"]
        second = imported.mentions["test:mention-2"]
        self.assertEqual(first.referent_ref.space, ReferenceSpace.REFERENT)
        self.assertEqual(second.antecedent_mention_ref.space, ReferenceSpace.MENTION)
        self.assertEqual(second.antecedent_referent_ref.space, ReferenceSpace.REFERENT)
        self.assertEqual(first.source_ref.space, ReferenceSpace.SOURCE)
        self.assertEqual(first.source_span, (1, 5))
        self.assertEqual(imported.mapping_report["targetVersion"], "0.7.0")

    def test_occurrence_identity_is_distinct_from_equal_surface_and_shared_referent(self):
        imported = document_to_kernel_v07(self.make_document(), validate=False)
        first = imported.mentions["test:mention-1"]
        second = imported.mentions["test:mention-2"]
        self.assertEqual(first.surface_text, second.surface_text)
        self.assertEqual(first.referent_ref, second.referent_ref)
        self.assertNotEqual(first.external_id, second.external_id)

    def test_dangling_links_remain_canonical_only(self):
        document = self.make_document()
        document["mentions"][0]["referentRef"] = "missing:referent"
        document["mentions"][0]["antecedentMentionRef"] = "missing:mention"
        imported = document_to_kernel_v07(document, validate=False)
        entry = imported.record_mapping["mentions"]["records"]["test:mention-1"]
        self.assertIn("referentRef", entry["unmappedFields"])
        self.assertIn("antecedentMentionRef", entry["unmappedFields"])
        exported = kernel_v07_document_to_contract(imported, validate=False)
        self.assertEqual(exported["mentions"][0]["referentRef"], "missing:referent")
        self.assertEqual(exported["mentions"][0]["antecedentMentionRef"], "missing:mention")

    def test_unicode_codepoint_span_requires_exact_surface_alignment(self):
        imported = document_to_kernel_v07(self.make_document(), validate=False)
        self.assertEqual(imported.mentions["test:mention-1"].source_span, (1, 5))
        document = self.make_document()
        document["mentions"][0]["sourceSpan"]["start"] = 0
        imported = document_to_kernel_v07(document, validate=False)
        entry = imported.record_mapping["mentions"]["records"]["test:mention-1"]
        self.assertIn("sourceSpan", entry["unmappedFields"])
        self.assertIsNone(imported.mentions["test:mention-1"].source_span)

    def test_unknown_status_is_not_coerced_and_is_preserved(self):
        document = self.make_document()
        document["mentions"][0]["resolutionStatus"] = "FUTURE_STATUS"
        imported = document_to_kernel_v07(document, validate=False)
        entry = imported.record_mapping["mentions"]["records"]["test:mention-1"]
        self.assertIn("resolutionStatus", entry["unmappedFields"])
        exported = kernel_v07_document_to_contract(imported, validate=False)
        self.assertEqual(exported["mentions"][0]["resolutionStatus"], "FUTURE_STATUS")

    def test_native_edit_changes_only_mention_and_preserves_sidecars(self):
        document = self.make_document()
        document["mentions"][0]["nativeId"] = "workbench:mention:1"
        document["mentions"][0]["futureField"] = {"keep": True}
        imported = document_to_kernel_v07(document, validate=False)
        original = imported.mentions["test:mention-1"]
        imported.mentions["test:mention-1"] = replace(
            original, surface_text="Alexandra",
            mention_type="NOMINAL",
            referent_ref=TypedReference(ReferenceSpace.REFERENT, "test:referent-2"),
        )
        exported = kernel_v07_document_to_contract(imported, validate=False)
        changed = exported["mentions"][0]
        self.assertEqual(changed["surfaceText"], "Alexandra")
        self.assertEqual(changed["mentionType"], "NOMINAL")
        self.assertEqual(changed["referentRef"], "test:referent-2")
        self.assertEqual(changed["nativeId"], "workbench:mention:1")
        self.assertEqual(changed["futureField"], {"keep": True})
        self.assertEqual(exported["referents"], document["referents"])
        self.assertEqual(exported["sources"], document["sources"])
        self.assertEqual(exported["extensions"], document["extensions"])
        self.assertEqual(exported["mentions"][1], document["mentions"][1])

    def test_source_span_edit_requires_explicit_source_and_validates_full_document(self):
        document = self.make_document()
        imported = document_to_kernel_v07(document, validate=False)
        original = imported.mentions["test:mention-1"]
        imported.mentions["test:mention-1"] = replace(original, source_span=(0, 99))
        with self.assertRaises(ContractMappingError):
            kernel_v07_document_to_contract(imported, validate=True)

    def test_wrong_reference_space_is_rejected_by_native_model(self):
        imported = document_to_kernel_v07(self.make_document(), validate=False)
        original = imported.mentions["test:mention-1"]
        with self.assertRaises(ValueError):
            replace(
                original, referent_ref=TypedReference(ReferenceSpace.MENTION, "test:mention-2")
            )

    def test_stale_canonical_snapshot_is_rejected(self):
        imported = document_to_kernel_v07(self.make_document(), validate=False)
        imported.document["mentions"][0]["surfaceText"] = "tampered"
        with self.assertRaises(ContractMappingError):
            kernel_v07_document_to_contract(imported, validate=False)

    def test_all_other_record_families_remain_canonical_only(self):
        document = self.make_document()
        imported = document_to_kernel_v07(document, validate=False)
        self.assertEqual(imported.record_mapping["referents"]["status"], "UNMAPPED")
        exported = kernel_v07_document_to_contract(imported, validate=False)
        self.assertEqual(exported["referents"], document["referents"])
        self.assertEqual(exported["expressions"], document["expressions"])


if __name__ == "__main__":
    unittest.main()
