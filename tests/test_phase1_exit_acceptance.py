from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _version in (
    "v0.8.0", "v0.9.0", "v1.0.0", "v1.1.0",
    "v1.2.0", "v1.2.1", "v1.3.0", "v1.4.0",
):
    sys.path.insert(0, str(ROOT / "implementations/python-kernel" / _version))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v0.5.0"))

from interoperability.python_adapter.document_v15 import (
    document_to_kernel_v15,
    kernel_v15_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from test_python_kernel_v15_document_adapter import CompleteDocumentAdapterV15Tests


class Phase1ExitAcceptanceTests(unittest.TestCase):
    def make_document(self):
        # Reuse the composed-adapter golden fixture, including its typed,
        # resolvable Expression scopeRef and Evidence references.
        return CompleteDocumentAdapterV15Tests().make_document()

    def test_complete_canonical_document_passes_schema_and_cross_family_validation(self):
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
        self.assertEqual(
            set(imported.mapping_report["familyReports"]),
            {
                "sources_expressions", "referents", "mentions", "assertions",
                "evidence", "contexts", "expressionRelations", "unresolvedItems",
                "derivations", "definitions",
            },
        )
        self.assertEqual(imported.mapping_report["targetVersion"], "1.5.1")

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
