from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.4.0"))

from interoperability.python_adapter.document_v14 import (
    document_to_kernel_v14, kernel_v14_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_definitions_v14 import SemanticKind


class KernelV14DefinitionsDocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0", "documentId": "test:doc",
            "sources": [{"id": "s:1", "text": "source"}], "primarySourceRef": "s:1",
            "definitions": {
                "grammarVersion": "grammar-1", "ontologyRelease": "ontology-1",
                "concepts": [{"id": "c:1", "label": "CUSTOMER", "semanticKind": "ENTITY",
                              "version": 2, "definition": "A customer", "lifecycleStage": "ACTIVE"}],
                "frames": [{"id": "f:1", "label": "TRANSFER", "version": 1,
                            "semanticKind": "EVENT", "roles": ["AGENT", "THEME", "AGENT"]}],
                "roles": [{"id": "r:1", "label": "AGENT",
                           "constraints": {"allowedKinds": ["ENTITY"]}}],
                "relations": [{"id": "rel:1", "label": "CAUSES",
                               "properties": {"symmetric": False}}],
            },
            "referents": [], "mentions": [], "expressions": [], "rootExpressionRefs": [],
            "assertions": [], "evidence": [], "contexts": [], "expressionRelations": [],
            "unresolvedItems": [], "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_all_four_definition_groups_project(self):
        item = document_to_kernel_v14(self.make_document(), validate=False).catalogue
        self.assertEqual(item.concepts[0].semantic_kind, SemanticKind.ENTITY)
        self.assertEqual(item.frames[0].roles, ("AGENT", "THEME", "AGENT"))
        self.assertEqual(item.roles[0].constraints, {"allowedKinds": ["ENTITY"]})
        self.assertEqual(item.relations[0].properties, {"symmetric": False})
        self.assertEqual(item.grammar_version, "grammar-1")
        self.assertEqual(item.ontology_release, "ontology-1")

    def test_all_semantic_kinds_project(self):
        for kind in SemanticKind:
            with self.subTest(kind=kind):
                doc = self.make_document()
                doc["definitions"]["concepts"][0]["semanticKind"] = kind.value
                imported = document_to_kernel_v14(doc, validate=False)
                self.assertEqual(imported.catalogue.concepts[0].semantic_kind, kind)

    def test_unknown_concept_kind_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["definitions"]["concepts"][0]["semanticKind"] = "FUTURE_KIND"
        imported = document_to_kernel_v14(doc, validate=False)
        self.assertEqual(len(imported.catalogue.concepts), 0)
        self.assertEqual(imported.record_mapping["concepts"]["records"]["c:1"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v14_document_to_contract(imported, validate=False)["definitions"], doc["definitions"])

    def test_unknown_optional_frame_kind_keeps_frame_canonical_only(self):
        doc = self.make_document()
        doc["definitions"]["frames"][0]["semanticKind"] = "FUTURE_KIND"
        imported = document_to_kernel_v14(doc, validate=False)
        self.assertEqual(len(imported.catalogue.frames), 0)

    def test_unknown_record_properties_are_canonical_only_and_partial(self):
        doc = self.make_document()
        doc["definitions"]["concepts"][0]["futureField"] = {"keep": True}
        imported = document_to_kernel_v14(doc, validate=False)
        self.assertEqual(imported.record_mapping["concepts"]["records"]["c:1"]["status"], "PARTIAL")
        self.assertEqual(kernel_v14_document_to_contract(imported, validate=False)["definitions"], doc["definitions"])

    def test_native_edits_merge_only_into_definition_groups(self):
        doc = self.make_document()
        imported = document_to_kernel_v14(doc, validate=False)
        concept = replace(imported.catalogue.concepts[0], label="CLIENT", version=3)
        frame = replace(imported.catalogue.frames[0], roles=("AGENT", "RECIPIENT"))
        role = replace(imported.catalogue.roles[0], constraints={"min": 2})
        relation = replace(imported.catalogue.relations[0], properties={"symmetric": True})
        imported.catalogue = replace(
            imported.catalogue, concepts=(concept,), frames=(frame,),
            roles=(role,), relations=(relation,), grammar_version="grammar-2",
        )
        out = kernel_v14_document_to_contract(imported, validate=False)
        definitions = out["definitions"]
        self.assertEqual(definitions["concepts"][0]["label"], "CLIENT")
        self.assertEqual(definitions["concepts"][0]["version"], 3)
        self.assertEqual(definitions["frames"][0]["roles"], ["AGENT", "RECIPIENT"])
        self.assertEqual(definitions["roles"][0]["constraints"], {"min": 2})
        self.assertEqual(definitions["relations"][0]["properties"], {"symmetric": True})
        self.assertEqual(definitions["grammarVersion"], "grammar-2")
        self.assertEqual(out["sources"], doc["sources"])
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_unknown_fields_cannot_be_silently_modified(self):
        doc = self.make_document()
        doc["definitions"]["concepts"][0]["futureField"] = "keep"
        imported = document_to_kernel_v14(doc, validate=False)
        concept = replace(imported.catalogue.concepts[0], canonical_extras={"futureField": "changed"})
        imported.catalogue = replace(imported.catalogue, concepts=(concept,))
        with self.assertRaises(ContractMappingError):
            kernel_v14_document_to_contract(imported, validate=False)

    def test_stale_snapshot_is_rejected(self):
        imported = document_to_kernel_v14(self.make_document(), validate=False)
        imported.document["definitions"]["concepts"][0]["label"] = "changed behind adapter"
        with self.assertRaises(ContractMappingError):
            kernel_v14_document_to_contract(imported, validate=False)

    def test_other_record_families_remain_canonical_only(self):
        doc = self.make_document()
        doc["contexts"] = [{"id": "c:1", "kind": "WORLD"}]
        imported = document_to_kernel_v14(doc, validate=False)
        self.assertEqual(imported.record_mapping["contexts"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v14_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_wrong_profile_is_rejected(self):
        doc = self.make_document()
        doc["profileId"] = "USG-SEM/2.0"
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v14(doc, validate=False)

    def test_non_mapping_document_is_rejected(self):
        with self.assertRaises(TypeError):
            document_to_kernel_v14([], validate=False)


if __name__ == "__main__":
    unittest.main()
