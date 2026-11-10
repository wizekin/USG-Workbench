from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "implementations" / "python-kernel" / "v0.5.0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(KERNEL))

from interoperability.python_adapter.document_v05 import (
    document_to_kernel_v05,
    kernel_v05_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg.grammar.node import metadata_value, predicate_app


class KernelV05DocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        source_text = "Alice needs the tool."
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": "test:document",
            "sources": [{
                "id": "test:source", "text": source_text, "language": "en",
                "sourceType": "SENTENCE", "trustTier": "QUARANTINE",
                "sensitivity": "INTERNAL",
                "textHash": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
                "offsetUnit": "unicode_code_point",
            }],
            "primarySourceRef": "test:source",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [{
                "id": "test:referent", "label": "Alice", "semanticKind": "ENTITY",
                "aliases": [], "identity": {"status": "UNRESOLVED", "scope": "DOCUMENT"},
            }],
            "mentions": [{
                "id": "test:mention", "surfaceText": "Alice",
                "resolutionStatus": "UNRESOLVED", "mentionType": "PROPER_NOUN",
                "sourceSpan": {"sourceRef": "test:source", "start": 0, "end": 5,
                               "offsetUnit": "unicode_code_point"},
            }],
            "expressions": [
                {"id": "test:alice", "op": "REF", "sort": "TERM",
                 "operandRefs": [], "params": {"ref": "external:alice"}},
                {"id": "test:tool", "op": "REF", "sort": "TERM",
                 "operandRefs": [], "params": {"ref": "external:tool"}},
                {"id": "test:predicate", "op": "PREDICATE_APP", "sort": "SIT",
                 "operandRefs": ["test:alice", "test:tool"],
                 "params": {"predicate": "NEEDS", "roles": ["AGENT", "THEME"],
                            "temporalFrame": {"tense": "present"}},
                 "semanticKind": "STATE", "interpretationStatus": "RESOLVED",
                 "nativeId": "workbench:predicate"},
                {"id": "test:root", "op": "HOLDS", "sort": "PROP",
                 "operandRefs": ["test:predicate"], "params": {}},
            ],
            "rootExpressionRefs": ["test:root"],
            "assertions": [],
            "evidence": [],
            "contexts": [],
            "expressionRelations": [],
            "unresolvedItems": [],
            "derivations": [],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.test": {"mustSurvive": [1, 2, 3]}},
        }

    def test_imports_whole_document_and_projects_v05_expression_root(self):
        document = self.make_document()
        imported = document_to_kernel_v05(document)
        self.assertEqual(imported.expression_roots["test:root"].op, "HOLDS")
        self.assertEqual(imported.mapping_report["targetVersion"], "0.5.0")
        self.assertEqual(imported.mapping_report["status"], "PARTIAL")
        self.assertIn("test:referent", imported.mapping_report["unmappedRefs"])
        self.assertIn("test:mention", imported.mapping_report["unmappedRefs"])
        self.assertEqual(imported.record_mapping["sources"]["status"], "UNMAPPED")
        self.assertEqual(imported.document["extensions"], document["extensions"])

    def test_export_rebuilds_full_document_and_preserves_canonical_only_records(self):
        document = self.make_document()
        imported = document_to_kernel_v05(document)
        exported = kernel_v05_document_to_contract(imported)
        self.assertEqual(exported["profileId"], "USG-SEM/1.0")
        self.assertEqual(exported["rootExpressionRefs"], ["test:root"])
        by_id = {item["id"]: item for item in exported["expressions"]}
        self.assertEqual(by_id["test:predicate"]["op"], "PREDICATE_APP")
        self.assertEqual(by_id["test:predicate"]["sort"], "SIT")
        self.assertEqual(by_id["test:predicate"]["params"]["roles"], ["AGENT", "THEME"])
        self.assertEqual(by_id["test:predicate"]["semanticKind"], "STATE")
        self.assertEqual(by_id["test:predicate"]["nativeId"], "workbench:predicate")
        self.assertEqual(exported["referents"], document["referents"])
        self.assertEqual(exported["mentions"], document["mentions"])
        self.assertEqual(exported["sources"], document["sources"])
        self.assertEqual(exported["extensions"], document["extensions"])
        self.assertEqual(exported["mapping"], document["mapping"])

    def test_native_graph_edit_is_serialized_without_replaying_original_expression(self):
        imported = document_to_kernel_v05(self.make_document())
        root = imported.expression_roots["test:root"]
        predicate = root.args[0]
        changed = predicate_app(
            "REQUIRES", predicate.get("roles"), predicate.args,
            temporalFrame=metadata_value(predicate, "temporalFrame"),
        )
        imported.expression_roots["test:root"] = root.with_args((changed,))
        exported = kernel_v05_document_to_contract(imported)
        by_id = {item["id"]: item for item in exported["expressions"]}
        self.assertEqual(by_id["test:predicate"]["params"]["predicate"], "NEEDS")
        root_record = by_id["test:root"]
        new_child_ref = root_record["operandRefs"][0]
        self.assertNotEqual(new_child_ref, "test:predicate")
        self.assertEqual(by_id[new_child_ref]["params"]["predicate"], "REQUIRES")
        self.assertEqual(by_id[new_child_ref]["sort"], "SIT")

    def test_canonical_snapshot_mutation_is_rejected(self):
        imported = document_to_kernel_v05(self.make_document())
        imported.document["sources"][0]["text"] = "tampered"
        with self.assertRaises(ContractMappingError):
            kernel_v05_document_to_contract(imported)

    def test_unreachable_expression_remains_canonical_only_and_survives_export(self):
        document = self.make_document()
        document["expressions"].append({
            "id": "test:orphan", "op": "CONNECTIVE", "sort": "PROP",
            "operandRefs": ["test:root", "test:root"],
            "params": {"connective": "CONTRAST", "operandRoles": ["left", "right"]},
        })
        imported = document_to_kernel_v05(document)
        self.assertIn("test:orphan", imported.mapping_report["unmappedRefs"])
        exported = kernel_v05_document_to_contract(imported)
        orphan = next(item for item in exported["expressions"] if item["id"] == "test:orphan")
        self.assertEqual(orphan, document["expressions"][-1])

    def test_invalid_contract_is_rejected_before_native_projection(self):
        document = self.make_document()
        document["rootExpressionRefs"] = ["missing"]
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v05(document)


if __name__ == "__main__":
    unittest.main()
