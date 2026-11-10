from __future__ import annotations
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v1.3.0"))

from interoperability.python_adapter.document_v13 import (
    document_to_kernel_v13, kernel_v13_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_derivation_v13 import DerivationMethod, DerivationStatus, DerivationModelInfo


class KernelV13DerivationDocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        return {
            "profileId": "USG-SEM/1.0", "documentId": "test:doc",
            "sources": [{"id": "s:1", "text": "source"}], "primarySourceRef": "s:1",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [], "mentions": [], "expressions": [], "rootExpressionRefs": [],
            "assertions": [], "evidence": [], "contexts": [], "expressionRelations": [],
            "unresolvedItems": [],
            "derivations": [{
                "id": "d:1", "method": "MODEL_PROPOSAL", "component": "composer",
                "ruleIds": ["rule:2", "rule:1", "rule:2"],
                "inputRefs": ["x:1", "e:1", "x:1"], "outputRefs": ["x:2", "x:2"],
                "model": {"provider": "local", "name": "qwen", "revision": "r1",
                          "runtime": {"quant": "q4"}},
                "timestamp": "2026-11-10T06:00:00Z", "status": "PROPOSED",
                "diagnostics": ["first", "second", "first"],
            }],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"preserve": True}},
        }

    def test_exact_fields_and_heterogeneous_refs_project(self):
        item = document_to_kernel_v13(self.make_document(), validate=False).derivations["d:1"]
        self.assertEqual(item.method, DerivationMethod.MODEL_PROPOSAL)
        self.assertEqual(item.status, DerivationStatus.PROPOSED)
        self.assertEqual(item.input_refs, ("x:1", "e:1", "x:1"))
        self.assertEqual(item.output_refs, ("x:2", "x:2"))
        self.assertEqual(item.rule_ids, ("rule:2", "rule:1", "rule:2"))
        self.assertEqual(item.model.provider, "local")
        self.assertEqual(item.model.metadata, {"runtime": {"quant": "q4"}})
        self.assertEqual(item.timestamp, "2026-11-10T06:00:00Z")
        self.assertEqual(item.diagnostics, ("first", "second", "first"))

    def test_all_methods_and_statuses_project(self):
        for method in DerivationMethod:
            for status in DerivationStatus:
                with self.subTest(method=method, status=status):
                    doc = self.make_document()
                    doc["derivations"][0]["method"] = method.value
                    doc["derivations"][0]["status"] = status.value
                    item = document_to_kernel_v13(doc, validate=False).derivations["d:1"]
                    self.assertEqual(item.method, method)
                    self.assertEqual(item.status, status)

    def test_unknown_method_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["derivations"][0]["method"] = "FUTURE_METHOD"
        imported = document_to_kernel_v13(doc, validate=False)
        self.assertNotIn("d:1", imported.derivations)

    def test_unknown_status_keeps_record_canonical_only(self):
        doc = self.make_document()
        doc["derivations"][0]["status"] = "FUTURE_STATUS"
        imported = document_to_kernel_v13(doc, validate=False)
        self.assertNotIn("d:1", imported.derivations)

    def test_malformed_required_refs_keep_record_canonical_only(self):
        for field in ("inputRefs", "outputRefs"):
            with self.subTest(field=field):
                doc = self.make_document()
                doc["derivations"][0][field] = ["valid", ""]
                imported = document_to_kernel_v13(doc, validate=False)
                self.assertNotIn("d:1", imported.derivations)

    def test_unknown_properties_are_partial_and_preserved(self):
        doc = self.make_document()
        doc["derivations"][0]["futureField"] = {"keep": True}
        imported = document_to_kernel_v13(doc, validate=False)
        self.assertEqual(imported.record_mapping["derivations"]["records"]["d:1"]["status"], "PARTIAL")
        self.assertEqual(kernel_v13_document_to_contract(imported, validate=False)["derivations"], doc["derivations"])

    def test_native_edits_merge_only_into_derivations_and_preserve_model_extras(self):
        doc = self.make_document()
        doc["derivations"][0]["legacyField"] = "keep"
        imported = document_to_kernel_v13(doc, validate=False)
        old = imported.derivations["d:1"]
        imported.derivations["d:1"] = replace(
            old, method=DerivationMethod.DETERMINISTIC_RULE,
            status=DerivationStatus.VALIDATED, component="validator",
            rule_ids=("rule:new",), diagnostics=("updated",),
            model=DerivationModelInfo(provider="new-provider", name="new-model",
                                      metadata={"runtime": {"quant": "q8"}}),
        )
        out = kernel_v13_document_to_contract(imported, validate=False)
        item = out["derivations"][0]
        self.assertEqual(item["method"], "DETERMINISTIC_RULE")
        self.assertEqual(item["status"], "VALIDATED")
        self.assertEqual(item["component"], "validator")
        self.assertEqual(item["ruleIds"], ["rule:new"])
        self.assertEqual(item["diagnostics"], ["updated"])
        self.assertEqual(item["model"]["provider"], "new-provider")
        self.assertEqual(item["model"]["runtime"], {"quant": "q8"})
        self.assertEqual(item["legacyField"], "keep")
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_unknown_model_properties_are_preserved(self):
        doc = self.make_document()
        doc["derivations"][0]["model"]["futureModelField"] = {"keep": True}
        imported = document_to_kernel_v13(doc, validate=False)
        item = imported.derivations["d:1"]
        self.assertEqual(item.model.metadata["futureModelField"], {"keep": True})
        self.assertEqual(kernel_v13_document_to_contract(imported, validate=False)["derivations"], doc["derivations"])

    def test_opaque_input_output_refs_are_not_resolved(self):
        doc = self.make_document()
        doc["derivations"][0]["inputRefs"] = ["opaque:not-in-current-collections"]
        item = document_to_kernel_v13(doc, validate=False).derivations["d:1"]
        self.assertEqual(item.input_refs, ("opaque:not-in-current-collections",))

    def test_stale_snapshot_is_rejected(self):
        imported = document_to_kernel_v13(self.make_document(), validate=False)
        imported.document["derivations"][0]["status"] = "REJECTED"
        with self.assertRaises(ContractMappingError):
            kernel_v13_document_to_contract(imported, validate=False)

    def test_non_derivation_families_remain_canonical_only(self):
        doc = self.make_document()
        doc["contexts"] = [{"id": "c:1", "kind": "WORLD"}]
        imported = document_to_kernel_v13(doc, validate=False)
        self.assertEqual(imported.record_mapping["contexts"]["status"], "UNMAPPED")
        self.assertEqual(kernel_v13_document_to_contract(imported, validate=False)["contexts"], doc["contexts"])

    def test_wrong_profile_is_rejected(self):
        doc = self.make_document()
        doc["profileId"] = "USG-SEM/2.0"
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v13(doc, validate=False)

    def test_non_mapping_document_is_rejected(self):
        with self.assertRaises(TypeError):
            document_to_kernel_v13([], validate=False)


if __name__ == "__main__":
    unittest.main()
