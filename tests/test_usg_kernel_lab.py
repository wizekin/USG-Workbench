from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations" / "python-kernel" / "v0.7.0"))

SERVER_PATH = ROOT / "tools" / "usg-kernel-lab" / "server.py"
SPEC = importlib.util.spec_from_file_location("usg_kernel_lab_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)
_apply_native_edits = SERVER._apply_native_edits
_native_json = SERVER._native_json
from interoperability.python_adapter.document_v07 import (
    document_to_kernel_v07, kernel_v07_document_to_contract,
)


def sample_document():
    text = "😀Alex met Alex. Later, she smiled."
    return {
        "profileId": "USG-SEM/1.0",
        "documentId": "lab:test",
        "sources": [{
            "id": "lab:source", "text": text, "language": "en",
            "sourceType": "SENTENCE", "trustTier": "STANDARD",
            "sensitivity": "INTERNAL", "offsetUnit": "unicode_code_point",
            "textHash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
        }],
        "primarySourceRef": "lab:source",
        "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
        "referents": [{"id": "lab:alex", "label": "Alex", "semanticKind": "ENTITY"}],
        "mentions": [
            {"id": "lab:m1", "surfaceText": "Alex", "resolutionStatus": "LINKED",
             "mentionType": "PROPER_NOUN", "referentRef": "lab:alex",
             "sourceSpan": {"sourceRef": "lab:source", "start": 1, "end": 5,
                            "offsetUnit": "unicode_code_point"}},
            {"id": "lab:m2", "surfaceText": "Alex", "resolutionStatus": "RESOLVED",
             "referentRef": "lab:alex", "antecedentMentionRef": "lab:m1",
             "antecedentReferentRef": "lab:alex",
             "sourceSpan": {"sourceRef": "lab:source", "start": 10, "end": 14,
                            "offsetUnit": "unicode_code_point"}},
            {"id": "lab:m3", "surfaceText": "she", "resolutionStatus": "UNRESOLVED",
             "mentionType": "PRONOUN",
             "sourceSpan": {"sourceRef": "lab:source", "start": 23, "end": 26,
                            "offsetUnit": "unicode_code_point"}},
        ],
        "expressions": [], "rootExpressionRefs": [], "assertions": [],
        "evidence": [], "contexts": [], "expressionRelations": [],
        "unresolvedItems": [], "derivations": [],
        "validation": {"structuralStatus": "NOT_CHECKED", "checks": []},
        "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                    "status": "LOSSLESS", "unmappedRefs": []},
        "extensions": {"org.usg.kernel-lab": {"preserve": True}},
    }


class KernelLabTests(unittest.TestCase):
    def test_inspection_returns_native_mentions_and_mapping(self):
        imported = document_to_kernel_v07(sample_document(), validate=True)
        rows = [_native_json(item) for item in imported.mentions.values()]
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["referentRef"], "lab:alex")
        self.assertEqual(rows[2]["sourceSpan"], [23, 26])
        self.assertEqual(imported.mapping_report["targetVersion"], "0.7.0")

    def test_native_edits_export_and_preserve_other_records(self):
        original = sample_document()
        imported = document_to_kernel_v07(original, validate=True)
        rows = [_native_json(item) for item in imported.mentions.values()]
        rows[0]["mentionType"] = "PERSON_NAME"
        _apply_native_edits(imported, rows)
        exported = kernel_v07_document_to_contract(imported, validate=True)
        self.assertEqual(exported["mentions"][0]["mentionType"], "PERSON_NAME")
        self.assertEqual(exported["referents"], original["referents"])
        self.assertEqual(exported["extensions"], original["extensions"])
        self.assertEqual(exported["mentions"][1], original["mentions"][1])

    def test_wrong_or_missing_mention_ids_are_rejected(self):
        imported = document_to_kernel_v07(sample_document(), validate=True)
        with self.assertRaises(ValueError):
            _apply_native_edits(imported, [])

    def test_invalid_native_source_span_is_rejected_on_export(self):
        imported = document_to_kernel_v07(sample_document(), validate=True)
        rows = [_native_json(item) for item in imported.mentions.values()]
        rows[0]["sourceSpan"] = [0, 5]
        _apply_native_edits(imported, rows)
        with self.assertRaises(Exception):
            kernel_v07_document_to_contract(imported, validate=True)


if __name__ == "__main__":
    unittest.main()
