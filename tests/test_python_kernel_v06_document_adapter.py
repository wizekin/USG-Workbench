from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations" / "python-kernel" / "v0.6.0"))

from interoperability.python_adapter.document_v06 import (
    document_to_kernel_v06,
    kernel_v06_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_identity_v06 import (
    IdentityScope, IdentityStatus, IntroductionKind, ReferenceSpace,
)


class KernelV06DocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        source_text = "😀 Alice arrived."
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
            "referents": [{
                "id": "test:referent", "label": "Alice", "semanticKind": "ENTITY",
                "aliases": ["A."], "conceptRefs": [],
                "number": "SINGULAR", "genericity": "SPECIFIC",
                "introducedIn": {"kind": "WORLD"},
                "identity": {
                    "status": "AMBIGUOUS", "scope": "WORKSPACE",
                    "equivalenceRefs": [], "basis": "explicit source evidence",
                },
                "sourceRef": "test:source",
                "sourceSpan": {
                    "sourceRef": "test:source", "start": 0, "end": 1,
                    "offsetUnit": "unicode_code_point",
                },
            }],
            "mentions": [{
                "id": "test:mention", "surfaceText": "Alice",
                "resolutionStatus": "LINKED", "mentionType": "PROPER_NOUN",
                "referentRef": "test:referent",
                "sourceSpan": {
                    "sourceRef": "test:source", "start": 2, "end": 7,
                    "offsetUnit": "unicode_code_point",
                },
            }],
            "expressions": [],
            "rootExpressionRefs": [],
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

    def test_exact_referent_fields_project_to_distinct_typed_model(self):
        imported = document_to_kernel_v06(self.make_document())
        native = imported.referents["test:referent"]
        self.assertEqual(native.external_id, "test:referent")
        self.assertEqual(native.identity.status, IdentityStatus.AMBIGUOUS)
        self.assertEqual(native.identity.scope, IdentityScope.WORKSPACE)
        self.assertEqual(native.introduced_in.kind, IntroductionKind.WORLD)
        self.assertEqual(native.source_ref.space, ReferenceSpace.SOURCE)
        self.assertEqual(native.source_span, (0, 1))
        self.assertEqual(imported.record_mapping["referents"]["status"], "LOSSLESS")
        self.assertEqual(imported.mapping_report["targetVersion"], "0.6.0")

    def test_unicode_code_point_span_is_checked_against_source_text(self):
        imported = document_to_kernel_v06(self.make_document())
        self.assertEqual(imported.referents["test:referent"].source_span, (0, 1))

    def test_equivalence_refs_are_explicit_typed_links_without_merging(self):
        document = self.make_document()
        document["referents"].append({
            "id": "test:referent-2", "label": "Alice", "identity": {}
        })
        document["referents"][0]["identity"]["equivalenceRefs"] = ["test:referent-2"]
        imported = document_to_kernel_v06(document)
        link = imported.referents["test:referent"].identity.equivalence_refs[0]
        self.assertEqual(link.space, ReferenceSpace.REFERENT)
        self.assertEqual(link.external_id, "test:referent-2")
        self.assertNotEqual(
            imported.referents["test:referent"].external_id,
            imported.referents["test:referent-2"].external_id,
        )

    def test_concept_refs_and_equivalence_refs_remain_distinct(self):
        document = self.make_document()
        document["definitions"]["concepts"] = [{"id": "test:concept"}]
        document["referents"][0]["conceptRefs"] = ["test:concept"]
        imported = document_to_kernel_v06(document, validate=False)
        ref = imported.referents["test:referent"].concept_refs[0]
        self.assertEqual(ref.space, ReferenceSpace.CONCEPT)

    def test_supported_non_world_context_maps_only_when_target_is_expression(self):
        document = self.make_document()
        document["expressions"] = [{"id": "test:context-node"}]
        document["referents"][0]["introducedIn"] = {
            "kind": "HYPOTHETICAL", "contextRef": "test:context-node"
        }
        imported = document_to_kernel_v06(document, validate=False)
        context = imported.referents["test:referent"].introduced_in
        self.assertEqual(context.kind, IntroductionKind.HYPOTHETICAL)
        self.assertEqual(context.context_ref.space, ReferenceSpace.NODE)

    def test_untyped_or_unknown_introduction_reference_remains_canonical_only(self):
        document = self.make_document()
        document["contexts"] = [{"id": "test:context", "kind": "HYPOTHETICAL"}]
        document["referents"][0]["introducedIn"] = {
            "kind": "HYPOTHETICAL", "contextRef": "test:context"
        }
        imported = document_to_kernel_v06(document, validate=False)
        entry = imported.record_mapping["referents"]["records"]["test:referent"]
        self.assertEqual(entry["status"], "PARTIAL")
        self.assertIn("introducedIn.contextRef", entry["unmappedFields"])

    def test_unknown_extension_fields_are_preserved_and_reported(self):
        document = self.make_document()
        document["referents"][0]["nativeId"] = "workbench:ref:1"
        document["referents"][0]["identity"]["provenance"] = {"reviewer": "system"}
        imported = document_to_kernel_v06(document)
        entry = imported.record_mapping["referents"]["records"]["test:referent"]
        self.assertEqual(entry["status"], "PARTIAL")
        self.assertIn("nativeId", entry["unmappedFields"])
        self.assertIn("identity.provenance", entry["unmappedFields"])
        exported = kernel_v06_document_to_contract(imported)
        self.assertEqual(exported["referents"], document["referents"])

    def test_dangling_equivalence_link_is_not_typed_or_dropped(self):
        document = self.make_document()
        document["referents"][0]["identity"]["equivalenceRefs"] = ["missing:referent"]
        imported = document_to_kernel_v06(document)
        entry = imported.record_mapping["referents"]["records"]["test:referent"]
        self.assertIn("identity.equivalenceRefs", entry["unmappedFields"])
        exported = kernel_v06_document_to_contract(imported)
        self.assertEqual(
            exported["referents"][0]["identity"]["equivalenceRefs"],
            ["missing:referent"],
        )

    def test_native_edit_updates_only_referent_and_preserves_mentions(self):
        document = self.make_document()
        imported = document_to_kernel_v06(document)
        original = imported.referents["test:referent"]
        imported.referents["test:referent"] = replace(
            original,
            identity=replace(original.identity, status=IdentityStatus.RESOLVED),
            label="Alice Smith",
        )
        exported = kernel_v06_document_to_contract(imported)
        self.assertEqual(exported["referents"][0]["label"], "Alice Smith")
        self.assertEqual(exported["referents"][0]["identity"]["status"], "RESOLVED")
        self.assertEqual(exported["mentions"], document["mentions"])
        self.assertEqual(exported["sources"], document["sources"])
        self.assertEqual(exported["extensions"], document["extensions"])

    def test_absent_identity_fields_are_not_defaulted_on_export(self):
        document = self.make_document()
        document["referents"][0].pop("identity")
        imported = document_to_kernel_v06(document)
        exported = kernel_v06_document_to_contract(imported)
        self.assertNotIn("identity", exported["referents"][0])

    def test_invalidated_span_is_rejected_by_full_document_validation(self):
        document = self.make_document()
        imported = document_to_kernel_v06(document)
        original = imported.referents["test:referent"]
        imported.referents["test:referent"] = replace(original, source_span=(0, 99))
        with self.assertRaises(ContractMappingError):
            kernel_v06_document_to_contract(imported)

    def test_canonical_snapshot_mutation_is_rejected(self):
        imported = document_to_kernel_v06(self.make_document())
        imported.document["referents"][0]["label"] = "tampered"
        with self.assertRaises(ContractMappingError):
            kernel_v06_document_to_contract(imported)

    def test_other_record_families_remain_canonical_only(self):
        document = self.make_document()
        imported = document_to_kernel_v06(document)
        self.assertEqual(imported.record_mapping["mentions"]["status"], "UNMAPPED")
        self.assertEqual(imported.record_mapping["mentions"]["unmappedRefs"], ["test:mention"])
        exported = kernel_v06_document_to_contract(imported)
        self.assertEqual(exported["mentions"], document["mentions"])

    def test_unsupported_schema_enum_is_partial_when_validation_is_disabled(self):
        document = self.make_document()
        document["referents"][0]["semanticKind"] = "FUTURE_KIND"
        imported = document_to_kernel_v06(document, validate=False)
        entry = imported.record_mapping["referents"]["records"]["test:referent"]
        self.assertIn("semanticKind", entry["unmappedFields"])
        self.assertEqual(
            kernel_v06_document_to_contract(imported, validate=False)["referents"][0]["semanticKind"],
            "FUTURE_KIND",
        )


if __name__ == "__main__":
    unittest.main()
