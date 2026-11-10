from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.2.1"))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v0.5.0"))

from interoperability.python_adapter.document_v15 import (
    document_to_kernel_v15, kernel_v15_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from test_python_kernel_v15_document_adapter import CompleteDocumentAdapterV15Tests
from usg_unresolved_v121 import ReferenceSpace, TypedReference


class Phase1ExitAcceptanceTests(unittest.TestCase):
    def make_document(self):
        return CompleteDocumentAdapterV15Tests().make_document()

    def test_complete_document_passes_schema_and_cross_family_validation(self):
        document = self.make_document()
        imported = document_to_kernel_v15(document, validate=True)
        exported = kernel_v15_document_to_contract(imported, validate=True)
        self.assertEqual(exported, document)

    def test_all_canonical_record_families_have_explicit_mapping_reports(self):
        imported = document_to_kernel_v15(self.make_document(), validate=True)
        expected = {
            "sources", "expressions", "referents", "mentions", "assertions",
            "evidence", "contexts", "expressionRelations", "unresolvedItems",
            "derivations", "concepts", "frames", "roles", "relations",
        }
        self.assertEqual(set(imported.record_mapping), expected)
        self.assertEqual(set(imported.mapping_report["familyReports"]), {
            "sources_expressions", "referents", "mentions", "assertions", "evidence",
            "contexts", "expressionRelations", "unresolvedItems", "derivations", "definitions",
        })
        self.assertEqual(imported.mapping_report["targetVersion"], "1.5.1")

    def test_unresolved_scope_is_typed_expression_reference(self):
        imported = document_to_kernel_v15(self.make_document(), validate=True)
        scope_ref = imported.adapters["unresolvedItems"].unresolved_items["u:1"].scope_ref
        self.assertEqual(scope_ref, TypedReference(ReferenceSpace.EXPRESSION, "x:root"))

    def test_document_sidecars_are_preserved_verbatim(self):
        document = self.make_document()
        imported = document_to_kernel_v15(document, validate=True)
        exported = kernel_v15_document_to_contract(imported, validate=True)
        for field in ("validation", "mapping", "extensions"):
            with self.subTest(field=field):
                self.assertEqual(exported[field], document[field])

    def test_stale_canonical_snapshot_is_rejected(self):
        imported = document_to_kernel_v15(self.make_document(), validate=True)
        imported.document["extensions"]["org.usg.phase1"]["mustSurvive"].append(4)
        with self.assertRaises(ContractMappingError):
            kernel_v15_document_to_contract(imported, validate=False)


if __name__ == "__main__":
    unittest.main()
