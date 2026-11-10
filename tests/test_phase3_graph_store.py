"""Tests for Phase 3 Step 3.2 canonical SQLite graph persistence."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.semantic_graph_store_v1_0_0 import (
    CanonicalDocumentStore,
    DocumentNotFoundError,
    IntegrityError,
    InvalidDocumentError,
    RevisionConflictError,
)
from tools.semantic_graph_store_v1_0_0.canonical import canonical_bytes, parse_canonical

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR_FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)
BASE_DOCUMENT = next(
    item["document"] for item in EXECUTOR_FIXTURES["fixtures"]
    if item["id"] == "EXEC-MP-POSITIVE-001"
)


class CanonicalEncodingTests(unittest.TestCase):
    def test_key_order_is_canonical_but_array_order_is_preserved(self):
        left = {"z": [{"b": 2, "a": 1}, {"a": 3}], "a": "first"}
        right = {"a": "first", "z": [{"a": 1, "b": 2}, {"a": 3}]}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))
        self.assertNotEqual(
            canonical_bytes({"items": ["one", "two"]}),
            canonical_bytes({"items": ["two", "one"]}),
        )

    def test_unicode_whitespace_and_combining_sequences_are_exact(self):
        value = {"source": "A😀e\u0301  \r\nB.", "extension": "é"}
        raw = canonical_bytes(value)
        self.assertIn("😀".encode("utf-8"), raw)
        self.assertEqual(parse_canonical(raw), value)
        self.assertEqual(canonical_bytes(parse_canonical(raw)), raw)

    def test_non_json_values_and_non_finite_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            canonical_bytes({"bad": float("nan")})
        with self.assertRaises(ValueError):
            canonical_bytes({"bad": object()})


class CanonicalGraphStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database_path = str(Path(self.temp.name) / "usg-store.sqlite3")
        self.store = CanonicalDocumentStore(self.database_path)
        self.document = deepcopy(BASE_DOCUMENT)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_store_and_load_preserve_complete_canonical_snapshot(self):
        stored = self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(stored.revision, 1)
        self.assertEqual(loaded.status, "VERIFIED")
        self.assertEqual(canonical_bytes(loaded.document), canonical_bytes(self.document))
        self.assertEqual(loaded.digest, sha256(canonical_bytes(self.document)).hexdigest())
        self.assertEqual(loaded.document["rootExpressionRefs"], self.document["rootExpressionRefs"])

    def test_idempotent_retry_does_not_create_a_new_revision(self):
        first = self.store.put_document(self.document)
        repeated = self.store.put_document(self.document)
        self.assertEqual(first.revision, repeated.revision)
        self.assertEqual(repeated.status, "UNCHANGED")
        self.assertEqual(len(self.store.list_revisions(self.document["documentId"])), 1)

    def test_changed_snapshot_appends_immutable_revision(self):
        first = self.store.put_document(self.document)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "second snapshot"
        second = self.store.put_document(changed, expected_revision=first.revision)
        old = self.store.get_document(changed["documentId"], revision=1)
        current = self.store.get_document(changed["documentId"])
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.predecessor_revision, 1)
        self.assertNotIn("revisionNote", old.document["extensions"])
        self.assertEqual(current.document["extensions"]["revisionNote"], "second snapshot")
        self.assertEqual([x["revision"] for x in self.store.list_revisions(changed["documentId"])], [1, 2])

    def test_stale_writer_cannot_overwrite_newer_revision(self):
        first = self.store.put_document(self.document)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "newer"
        self.store.put_document(changed, expected_revision=first.revision)
        stale = deepcopy(self.document)
        stale["extensions"]["revisionNote"] = "stale"
        with self.assertRaises(RevisionConflictError):
            self.store.put_document(stale, expected_revision=first.revision)
        self.assertEqual(
            self.store.get_document(self.document["documentId"]).document["extensions"]["revisionNote"],
            "newer",
        )

    def test_changed_existing_document_requires_compare_and_swap(self):
        self.store.put_document(self.document)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "no expected revision"
        with self.assertRaises(RevisionConflictError):
            self.store.put_document(changed)

    def test_failed_index_write_rolls_back_document_revision_and_indexes(self):
        with patch.object(self.store, "_write_indexes", side_effect=RuntimeError("injected index failure")):
            with self.assertRaises(RuntimeError):
                self.store.put_document(self.document)
        with self.assertRaises(DocumentNotFoundError):
            self.store.get_document(self.document["documentId"])
        count = self.store._connection.execute("SELECT COUNT(*) FROM document_revisions").fetchone()[0]
        self.assertEqual(count, 0)

    def test_index_drift_is_detected_and_rebuildable(self):
        self.store.put_document(self.document)
        self.store._connection.execute(
            "DELETE FROM expression_index WHERE document_id=? AND revision=1 AND expression_id=?",
            (self.document["documentId"], "expr-a"),
        )
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])
        counts = self.store.rebuild_indexes(self.document["documentId"])
        self.assertEqual(counts["expression_index"], len(self.document["expressions"]))
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(canonical_bytes(loaded.document), canonical_bytes(self.document))

    def test_snapshot_hash_tampering_is_detected(self):
        self.store.put_document(self.document)
        self.store._connection.execute("DROP TRIGGER immutable_document_revision_update")
        self.store._connection.execute(
            "UPDATE document_revisions SET canonical_json=? WHERE document_id=? AND revision=1",
            (b"{}", self.document["documentId"]),
        )
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])

    def test_unicode_source_text_round_trips_exactly(self):
        document = deepcopy(self.document)
        source = document["sources"][0]
        source_text = "A😀e\u0301  \r\nB."
        source["text"] = source_text
        source["textHash"] = sha256(source_text.encode("utf-8")).hexdigest()
        source["hashAlgorithm"] = "SHA-256"
        source["encoding"] = "UTF-8"
        self.store.put_document(document)
        loaded = self.store.get_document(document["documentId"])
        self.assertEqual(loaded.document["sources"][0]["text"], source_text)
        self.assertEqual(loaded.document["sources"][0]["textHash"], source["textHash"])

    def test_large_expression_graph_is_not_semantically_truncated(self):
        document = deepcopy(self.document)
        extra = [
            {
                "id": f"expr-extra-{index}",
                "op": "PREDICATE_APP",
                "sort": "PROP",
                "operandRefs": [],
                "params": {"predicate": f"EXTRA_{index}"},
                "interpretationStatus": "RESOLVED",
            }
            for index in range(1200)
        ]
        document["expressions"].extend(extra)
        stored = self.store.put_document(document)
        loaded = self.store.get_document(document["documentId"])
        self.assertEqual(len(loaded.document["expressions"]), len(document["expressions"]))
        self.assertEqual(
            self.store._connection.execute(
                "SELECT COUNT(*) FROM expression_index WHERE document_id=? AND revision=?",
                (document["documentId"], stored.revision),
            ).fetchone()[0],
            len(document["expressions"]),
        )

    def test_invalid_document_is_rejected_before_persistence(self):
        invalid = deepcopy(self.document)
        invalid.pop("profileId")
        with self.assertRaises(InvalidDocumentError):
            self.store.put_document(invalid)
        self.assertEqual(
            self.store._connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            0,
        )

    def test_integrity_report_is_machine_readable(self):
        self.store.put_document(self.document)
        report = self.store.verify_integrity(self.document["documentId"])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["record_counts"]["expressions"], len(self.document["expressions"]))
        self.assertEqual(report["diagnostics"], [])


if __name__ == "__main__":
    unittest.main()
