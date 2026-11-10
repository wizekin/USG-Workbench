"""DuckDB canonical-store compatibility tests."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from tools.semantic_graph_store_v1_0_0.canonical import canonical_bytes
from tools.semantic_graph_store_duckdb_v1_0_0 import (
    CanonicalDocumentStore, IntegrityError, InvalidDocumentError, RevisionConflictError,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
BASE = next(x["document"] for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")


class DuckDBStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "usg.duckdb"
        self.store = CanonicalDocumentStore(self.path)
        self.document = deepcopy(BASE)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_exact_canonical_unicode_round_trip(self):
        source = self.document["sources"][0]
        source["text"] = "A😀e\u0301  \r\nB."
        source["textHash"] = sha256(source["text"].encode("utf-8")).hexdigest()
        source["hashAlgorithm"] = "SHA-256"
        source["encoding"] = "UTF-8"
        self.store.put_document(self.document)
        loaded = self.store.get_document(self.document["documentId"])
        self.assertEqual(canonical_bytes(loaded.document), canonical_bytes(self.document))
        self.assertEqual(loaded.status, "VERIFIED")

    def test_idempotent_revision_history_and_cas(self):
        first = self.store.put_document(self.document)
        same = self.store.put_document(self.document)
        self.assertEqual(same.revision, 1)
        self.assertEqual(same.status, "UNCHANGED")
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "revision two"
        second = self.store.put_document(changed, expected_revision=1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.predecessor_revision, 1)
        self.assertEqual([x["revision"] for x in self.store.list_revisions(self.document["documentId"])], [1, 2])
        stale = deepcopy(changed)
        stale["extensions"]["revisionNote"] = "stale"
        with self.assertRaises(RevisionConflictError):
            self.store.put_document(stale, expected_revision=1)

    def test_index_drift_detection_and_rebuild(self):
        self.store.put_document(self.document)
        self.store._connection.execute(
            "DELETE FROM expression_index WHERE document_id=? AND revision=1 AND expression_id=?",
            [self.document["documentId"], self.document["expressions"][0]["id"]]
        )
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])
        counts = self.store.rebuild_indexes(self.document["documentId"])
        self.assertEqual(counts["expression_index"], len(self.document["expressions"]))
        self.assertEqual(self.store.get_document(self.document["documentId"]).status, "VERIFIED")

    def test_snapshot_tampering_is_detected(self):
        self.store.put_document(self.document)
        self.store._connection.execute(
            "UPDATE document_revisions SET canonical_json=? WHERE document_id=? AND revision=1",
            [b"{}", self.document["documentId"]]
        )
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
        self.assertEqual(
            len(self.store.get_document(self.document["documentId"]).document["expressions"]),
            len(self.document["expressions"])
        )

    def test_invalid_document_rejected_before_write(self):
        invalid = deepcopy(self.document)
        invalid.pop("profileId")
        with self.assertRaises(InvalidDocumentError):
            self.store.put_document(invalid)

    def test_multiple_connections_can_write_distinct_documents_in_one_process(self):
        self.store.close()
        stores = [CanonicalDocumentStore(self.path) for _ in range(4)]
        try:
            def write(index):
                doc = deepcopy(BASE)
                doc["documentId"] = f"concurrent-{index}"
                stores[index].put_document(doc)
                return stores[index].get_document(doc["documentId"]).revision
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(write, range(4)))
            self.assertEqual(results, [1, 1, 1, 1])
        finally:
            for store in stores:
                store.close()
        self.store = CanonicalDocumentStore(self.path)

    def test_read_only_reopen(self):
        self.store.put_document(self.document)
        self.store.close()
        reader = CanonicalDocumentStore(self.path, read_only=True)
        try:
            self.assertEqual(reader.get_document(self.document["documentId"]).status, "VERIFIED")
        finally:
            reader.close()
        self.store = CanonicalDocumentStore(self.path)


if __name__ == "__main__":
    unittest.main()
