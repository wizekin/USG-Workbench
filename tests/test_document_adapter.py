from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "implementations" / "python-kernel" / "v0.4.0"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(KERNEL))

from interoperability.python_adapter import ContractMappingError, document_to_python, validate_contract_document


class DocumentAdapterTests(unittest.TestCase):
    def make_document(self):
        source_text = "Alice needs the tool."
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": "test:document",
            "sources": [{
                "id": "test:source",
                "text": source_text,
                "language": "en",
                "sourceType": "SENTENCE",
                "trustTier": "QUARANTINE",
                "sensitivity": "INTERNAL",
                "textHash": source_hash,
                "hashAlgorithm": "SHA-256",
                "encoding": "UTF-8",
                "offsetUnit": "unicode_code_point",
            }],
            "primarySourceRef": "test:source",
            "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
            "referents": [{
                "id": "test:referent:alice",
                "label": "Alice",
                "semanticKind": "ENTITY",
                "aliases": ["the speaker"],
                "identity": {"status": "UNRESOLVED", "scope": "DOCUMENT"},
            }],
            "mentions": [{
                "id": "test:mention:alice",
                "surfaceText": "Alice",
                "resolutionStatus": "UNRESOLVED",
                "mentionType": "PROPER_NOUN",
                "sourceSpan": {
                    "sourceRef": "test:source", "start": 0, "end": 5,
                    "offsetUnit": "unicode_code_point",
                },
            }],
            "expressions": [
                {"id": "test:expr:alice", "op": "REF", "sort": "TERM",
                 "operandRefs": [], "params": {"ref": "external:alice"}},
                {"id": "test:expr:tool", "op": "REF", "sort": "TERM",
                 "operandRefs": [], "params": {"ref": "external:tool"}},
                {"id": "test:expr:needs", "op": "RELATE", "sort": "PROP",
                 "operandRefs": ["test:expr:alice", "test:expr:tool"],
                 "params": {"relation": "NEEDS"},
                 "annotations": {"spans": [{
                     "sourceRef": "test:source", "start": 0, "end": len(source_text),
                     "offsetUnit": "unicode_code_point",
                 }]}},
            ],
            "rootExpressionRefs": ["test:expr:needs"],
            "assertions": [{
                "id": "test:assertion",
                "expressionRef": "test:expr:needs",
                "origin": "SOURCE_TEXT",
                "epistemicStatus": "SOURCE_ASSERTED",
                "commitment": "AUTHOR",
                "evaluationContext": {"kind": "WORLD"},
                "lifecycleStage": "STRUCTURED",
                "sourceRef": "test:source",
            }],
            "evidence": [{
                "id": "test:evidence",
                "sourceRef": "test:source",
                "span": {
                    "sourceRef": "test:source", "start": 0, "end": len(source_text),
                    "offsetUnit": "unicode_code_point",
                },
                "quote": source_text,
                "alignmentStatus": "EXACT",
                "semanticSupportStatus": "NOT_ESTABLISHED",
            }],
            "contexts": [{"id": "test:world", "kind": "WORLD", "sourceRef": "test:source"}],
            "expressionRelations": [],
            "unresolvedItems": [{
                "id": "test:unresolved",
                "status": "UNRESOLVED",
                "reason": "Antecedent not established",
                "surfaceText": "it",
                "scopeRef": "test:expr:needs",
            }],
            "derivations": [{
                "id": "test:derivation",
                "method": "IMPORT",
                "inputRefs": ["test:source"],
                "outputRefs": ["test:expr:needs"],
                "status": "VALIDATED",
            }],
            "validation": {
                "structuralStatus": "NOT_CHECKED",
                "checks": [],
                "validator": "fixture",
                "contractVersion": "USG-SEM/1.0",
            },
            "mapping": {
                "sourceProfile": "fixture",
                "sourceVersion": "1",
                "status": "LOSSLESS",
                "unmappedRefs": [],
            },
            "extensions": {"org.usg.fixture": {"opaque": ["preserve", "all", "items"]}},
        }

    def test_complete_document_is_preserved_and_supported_records_project(self):
        document = self.make_document()
        imported = document_to_python(document)
        self.assertEqual(imported.sources["test:source"].text, "Alice needs the tool.")
        self.assertEqual(imported.expression_roots["test:expr:needs"].op, "RELATE")
        self.assertIn("test:assertion", imported.assertions)
        self.assertEqual(imported.mapping_report["status"], "PARTIAL")
        self.assertIn("test:referent:alice", imported.mapping_report["unmappedRefs"])
        self.assertIn("test:mention:alice", imported.mapping_report["unmappedRefs"])
        self.assertIn("test:evidence", imported.mapping_report["unmappedRefs"])
        self.assertIn("test:unresolved", imported.mapping_report["unmappedRefs"])
        self.assertEqual(imported.export_contract_document(), document)

    def test_document_snapshot_mutation_is_not_exported_as_stale_data(self):
        imported = document_to_python(self.make_document())
        imported.document["sources"][0]["text"] = "changed"
        with self.assertRaises(ContractMappingError):
            imported.export_contract_document()

    def test_unsupported_constructor_is_preserved_and_reported(self):
        document = self.make_document()
        document["expressions"][0]["id"] = "test:expr:arg"
        document["expressions"][1]["id"] = "test:expr:arg2"
        document["expressions"][2] = {
            "id": "test:expr:predication",
            "op": "PREDICATE_APP",
            "sort": "SIT",
            "operandRefs": ["test:expr:arg", "test:expr:arg2"],
            "params": {"predicate": "NEEDS", "roles": ["AGENT", "THEME"]},
        }
        document["expressions"].append({
            "id": "test:expr:holds", "op": "HOLDS", "sort": "PROP",
            "operandRefs": ["test:expr:predication"], "params": {},
        })
        document["rootExpressionRefs"] = ["test:expr:holds"]
        document["assertions"][0]["expressionRef"] = "test:expr:holds"
        imported = document_to_python(document)
        self.assertEqual(imported.expression_roots, {})
        self.assertEqual(imported.mapping_report["status"], "PARTIAL")
        self.assertIn("test:expr:predication", imported.mapping_report["unmappedRefs"])
        self.assertEqual(imported.export_contract_document(), document)

    def test_multiple_roots_preserve_shared_dag_identity(self):
        document = self.make_document()
        document["expressions"].append({
            "id": "test:expr:not", "op": "NOT", "sort": "PROP",
            "operandRefs": ["test:expr:needs"], "params": {},
        })
        document["rootExpressionRefs"] = ["test:expr:needs", "test:expr:not"]
        imported = document_to_python(document)
        first = imported.expression_roots["test:expr:needs"]
        second = imported.expression_roots["test:expr:not"]
        self.assertIs(first, second.args[0])

    def test_schema_and_reference_validation_reject_dangling_operands(self):
        document = self.make_document()
        document["expressions"][2]["operandRefs"] = ["missing:expression", "test:expr:tool"]
        errors = validate_contract_document(document)
        self.assertTrue(any("dangling operandRef" in error for error in errors))

    def test_unknown_source_enum_is_preserved_but_not_projected(self):
        document = self.make_document()
        document["sources"][0]["trustTier"] = "UNKNOWN"
        imported = document_to_python(document)
        self.assertNotIn("test:source", imported.sources)
        self.assertIn("test:source", imported.mapping_report["unmappedRefs"])
        self.assertEqual(imported.export_contract_document(), document)

    def test_invalid_schema_is_rejected_before_projection(self):
        document = self.make_document()
        document["profileId"] = "USG-SEM/9.9"
        with self.assertRaises(ContractMappingError):
            document_to_python(document)


if __name__ == "__main__":
    unittest.main()
