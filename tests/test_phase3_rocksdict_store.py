"""Correctness and workload tests for the RocksDB USG evaluation adapter."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from tools.semantic_graph_store_v1_0_0.canonical import canonical_bytes
from tools.semantic_graph_store_rocksdict_v1_0_0 import (
    CanonicalDocumentStore, IntegrityError, InvalidDocumentError, RevisionConflictError,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)
BASE = next(x["document"] for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")


class RocksDBStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "rocksdb"
        self.store = CanonicalDocumentStore(self.path)
        self.document = deepcopy(BASE)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_exact_canonical_round_trip_and_unicode(self):
        source = self.document["sources"][0]
        source["text"] = "A😀e\u0301  \r\nB."
        source["textHash"] = sha256(source["text"].encode("utf-8")).hexdigest()
        source["hashAlgorithm"] = "SHA-256"
        source["encoding"] = "UTF-8"
        self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(canonical_bytes(loaded.document), canonical_bytes(self.document))
        self.assertEqual(loaded.status, "VERIFIED")

    def test_idempotency_revision_history_and_cas(self):
        first = self.store.put_document(self.document)
        again = self.store.put_document(self.document)
        self.assertEqual(again.revision, 1)
        self.assertEqual(again.status, "UNCHANGED")
        changed = deepcopy(self.document)
        changed["extensions"]["note"] = "revision two"
        second = self.store.put_document(changed, expected_revision=1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.predecessor_revision, 1)
        self.assertEqual([x["revision"] for x in self.store.list_revisions(self.document["documentId"])], [1, 2])
        stale = deepcopy(changed)
        stale["extensions"]["note"] = "stale writer"
        with self.assertRaises(RevisionConflictError):
            self.store.put_document(stale, expected_revision=1)
        self.assertEqual(self.store.get_document(self.document["documentId"]).revision, 2)

    def test_index_drift_detection_and_rebuild(self):
        self.store.put_document(self.document)
        family = "expression"
        key = self.store._index_key(family, self.document["documentId"], 1, self.document["expressions"][0]["id"])
        del self.store._db[key]
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])
        counts = self.store.rebuild_indexes(self.document["documentId"])
        self.assertEqual(counts["expression_index"], len(self.document["expressions"]))
        self.assertEqual(self.store.get_document(self.document["documentId"]).status, "VERIFIED")

    def test_snapshot_tampering_is_detected(self):
        self.store.put_document(self.document)
        self.store._db[self.store._snapshot_key(self.document["documentId"], 1)] = b"{}"
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])

    def test_large_graph_is_not_truncated(self):
        self.document["expressions"].extend([
            {"id": f"extra-{i}", "op": "PREDICATE_APP", "sort": "PROP",
             "operandRefs": [], "params": {"predicate": f"EXTRA_{i}"},
             "interpretationStatus": "RESOLVED"}
            for i in range(1200)
        ])
        self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(len(loaded.document["expressions"]), len(self.document["expressions"]))

    def test_invalid_document_is_rejected_before_write(self):
        invalid = deepcopy(self.document)
        invalid.pop("profileId")
        with self.assertRaises(InvalidDocumentError):
            self.store.put_document(invalid)

    def test_concurrent_readers_and_serialized_writers_in_one_process(self):
        first = self.store.put_document(self.document)

        def reader():
            seen = []
            for _ in range(20):
                loaded = self.store.get_document(self.document["documentId"])
                self.assertEqual(loaded.status, "VERIFIED")
                seen.append(loaded.revision)
            return seen

        def writer():
            for index in range(2, 5):
                changed = deepcopy(self.document)
                changed["extensions"]["threadRevision"] = index
                self.store.put_document(changed, expected_revision=index - 1)

        with ThreadPoolExecutor(max_workers=5) as pool:
            readers = [pool.submit(reader) for _ in range(4)]
            writer_future = pool.submit(writer)
            writer_future.result()
            observations = [future.result() for future in readers]

        self.assertEqual(self.store.get_document(self.document["documentId"]).revision, 4)
        self.assertTrue(all(all(1 <= revision <= 4 for revision in rows) for rows in observations))

    def test_reopen_recovery(self):
        self.store.put_document(self.document)
        self.store.close()
        reopened = CanonicalDocumentStore(self.path)
        try:
            self.assertEqual(canonical_bytes(reopened.get_document(self.document["documentId"]).document),
                             canonical_bytes(self.document))
        finally:
            reopened.close()


if __name__ == "__main__":
    unittest.main()
