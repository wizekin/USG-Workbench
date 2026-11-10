"""LMDB parity, integrity, recovery, and concurrency tests for Phase 3."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import lmdb

from tools.semantic_graph_store_lmdb_v1_0_0 import (
    CanonicalDocumentStore, DocumentNotFoundError, IntegrityError,
    InvalidDocumentError, RevisionConflictError,
)
from tools.semantic_graph_store_v1_0_0.canonical import canonical_bytes

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)
BASE = next(item["document"] for item in FIXTURES["fixtures"] if item["id"] == "EXEC-MP-POSITIVE-001")


class LMDBCanonicalGraphStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "graph.lmdb")
        self.store = CanonicalDocumentStore(self.path)
        self.document = deepcopy(BASE)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_exact_canonical_round_trip_and_integrity(self):
        stored = self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(stored.revision, 1)
        self.assertEqual(loaded.status, "VERIFIED")
        self.assertEqual(canonical_bytes(loaded.document), canonical_bytes(self.document))
        self.assertEqual(loaded.digest, sha256(canonical_bytes(self.document)).hexdigest())
        self.assertEqual(self.store.verify_integrity(self.document["documentId"])["status"], "PASS")

    def test_unicode_whitespace_and_combining_sequences_are_exact(self):
        source = self.document["sources"][0]
        source_text = "A😀e\u0301  \r\nB."
        source["text"] = source_text
        source["textHash"] = sha256(source_text.encode("utf-8")).hexdigest()
        source["hashAlgorithm"] = "SHA-256"
        source["encoding"] = "UTF-8"
        self.store.put_document(self.document)
        self.assertEqual(
            self.store.get_document(self.document["documentId"]).document["sources"][0]["text"],
            source_text,
        )

    def test_idempotent_write_and_immutable_revision_history(self):
        first = self.store.put_document(self.document)
        repeated = self.store.put_document(self.document)
        self.assertEqual(repeated.status, "UNCHANGED")
        self.assertEqual(repeated.revision, first.revision)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "revision two"
        second = self.store.put_document(changed, expected_revision=1)
        self.assertEqual((second.revision, second.predecessor_revision), (2, 1))
        self.assertNotIn("revisionNote", self.store.get_document(changed["documentId"], 1).document["extensions"])
        self.assertEqual([x["revision"] for x in self.store.list_revisions(changed["documentId"])], [1, 2])

    def test_stale_writer_is_rejected_without_overwrite(self):
        self.store.put_document(self.document)
        newer = deepcopy(self.document)
        newer["extensions"]["revisionNote"] = "newer"
        self.store.put_document(newer, expected_revision=1)
        stale = deepcopy(self.document)
        stale["extensions"]["revisionNote"] = "stale"
        with self.assertRaises(RevisionConflictError):
            self.store.put_document(stale, expected_revision=1)
        self.assertEqual(
            self.store.get_document(stale["documentId"]).document["extensions"]["revisionNote"],
            "newer",
        )

    def test_failed_index_write_rolls_back_all_named_databases(self):
        with patch.object(self.store, "_write_indexes", side_effect=RuntimeError("injected index failure")):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                self.store.put_document(self.document)
        with self.assertRaises(DocumentNotFoundError):
            self.store.get_document(self.document["documentId"])
        with self.store._env.begin() as txn:
            self.assertIsNone(txn.get(self.store._key(self.document["documentId"]), db=self.store._db["documents"]))
            self.assertEqual(txn.stat(db=self.store._db["revisions"])["entries"], 0)
            self.assertEqual(txn.stat(db=self.store._db["snapshots"])["entries"], 0)

    def test_snapshot_tampering_is_detected(self):
        self.store.put_document(self.document)
        key = self.store._key(self.document["documentId"], 1)
        with self.store._env.begin(write=True) as txn:
            txn.put(key, b"{}", db=self.store._db["snapshots"])
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])

    def test_index_drift_is_detected_and_rebuilt(self):
        self.store.put_document(self.document)
        expression = self.document["expressions"][0]
        key = self.store._key(self.document["documentId"], 1, expression["id"])
        with self.store._env.begin(write=True) as txn:
            txn.delete(key, db=self.store._db["expression_index"])
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])
        counts = self.store.rebuild_indexes(self.document["documentId"])
        self.assertEqual(counts["expression_index"], len(self.document["expressions"]))
        self.assertEqual(self.store.get_document(self.document["documentId"]).status, "VERIFIED")

    def test_large_graph_is_not_truncated(self):
        extra = [
            {
                "id": f"expr-extra-{i}", "op": "PREDICATE_APP", "sort": "PROP",
                "operandRefs": [], "params": {"predicate": f"EXTRA_{i}"},
                "interpretationStatus": "RESOLVED",
            }
            for i in range(1200)
        ]
        self.document["expressions"].extend(extra)
        stored = self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(len(loaded.document["expressions"]), len(self.document["expressions"]))
        self.assertEqual(
            self.store.storage_stats()["databases"]["expression_index"]["entries"],
            len(self.document["expressions"]),
        )
        self.assertEqual(stored.revision, 1)

    def test_long_composite_index_identity_does_not_hit_lmdb_key_size_limit(self):
        # Both identifiers are within the USG-SEM schema's 256-character bound,
        # but their combined composite key would exceed LMDB's default 511-byte key limit.
        self.document["documentId"] = "d" * 256
        self.document["expressions"].append({
            "id": "e" * 256, "op": "PREDICATE_APP", "sort": "PROP",
            "operandRefs": [], "params": {"predicate": "LONG_IDENTIFIER"},
            "interpretationStatus": "RESOLVED",
        })
        stored = self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(loaded.digest, stored.digest)
        self.assertEqual(len(loaded.document["expressions"][-1]["id"]), 256)

    def test_invalid_document_is_rejected_before_write(self):
        invalid = deepcopy(self.document)
        invalid.pop("profileId")
        with self.assertRaises(InvalidDocumentError):
            self.store.put_document(invalid)
        self.assertEqual(self.store.storage_stats()["databases"]["revisions"]["entries"], 0)

    def test_interrupted_transaction_is_atomic_after_reopen(self):
        with self.assertRaises(RuntimeError):
            with self.store._env.begin(write=True) as txn:
                txn.put(b"partial", b"not committed", db=self.store._db["snapshots"])
                raise RuntimeError("simulated process interruption before commit")
        self.store.close()
        self.store = CanonicalDocumentStore(self.path)
        with self.store._env.begin() as txn:
            self.assertIsNone(txn.get(b"partial", db=self.store._db["snapshots"]))
        with self.assertRaises(DocumentNotFoundError):
            self.store.get_document(self.document["documentId"])

    def test_concurrent_readers_can_read_while_writer_commits(self):
        self.store.put_document(self.document)
        errors = []
        started = threading.Event()

        def reader():
            try:
                started.set()
                for _ in range(25):
                    result = self.store.get_document(self.document["documentId"])
                    self.assertEqual(result.status, "VERIFIED")
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=reader)
        thread.start()
        started.wait(timeout=2)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "concurrent update"
        self.store.put_document(changed, expected_revision=1)
        thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(self.store.get_document(self.document["documentId"]).revision, 2)

    def test_rejects_source_hash_mismatch(self):
        self.document["sources"][0]["textHash"] = "0" * 64
        self.document["sources"][0]["hashAlgorithm"] = "SHA-256"
        self.document["sources"][0]["encoding"] = "UTF-8"
        with self.assertRaises(InvalidDocumentError):
            self.store.put_document(self.document)


if __name__ == "__main__":
    unittest.main()
