"""LanceDB evaluation tests: canonical snapshots, table versions, vector and FTS retrieval."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from tools.semantic_graph_store_v1_0_0.canonical import canonical_bytes
from tools.semantic_graph_store_lancedb_v1_0_0 import (
    CanonicalDocumentStore, IntegrityError, InvalidDocumentError, RevisionConflictError,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
BASE = next(x["document"] for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")


class LanceDBStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CanonicalDocumentStore(Path(self.temp.name) / "lance")
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

    def test_append_only_revision_history_and_stale_writer_rejection(self):
        first = self.store.put_document(self.document)
        same = self.store.put_document(self.document)
        self.assertEqual(same.revision, 1)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "second"
        second = self.store.put_document(changed, expected_revision=1)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.predecessor_revision, 1)
        self.assertEqual([x["revision"] for x in self.store.list_revisions(self.document["documentId"])], [1, 2])
        stale = deepcopy(changed)
        stale["extensions"]["revisionNote"] = "stale"
        with self.assertRaises(RevisionConflictError):
            self.store.put_document(stale, expected_revision=1)

    def test_table_time_travel_preserves_older_snapshot(self):
        self.store.put_document(self.document)
        table = self.store._table
        version_one = table.version
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "revision two"
        self.store.put_document(changed, expected_revision=1)
        self.assertGreater(table.version, version_one)
        table.checkout(version_one)
        rows = table.to_arrow().to_pylist()
        self.assertEqual(len(rows), 1)
        table.checkout_latest()
        self.assertEqual(len(table.to_arrow().to_pylist()), 2)

    def test_snapshot_tampering_is_detected(self):
        self.store.put_document(self.document)
        self.store._table.update(
            where=f"document_id = '{self.document['documentId']}' AND revision = 1",
            values={"canonical_json": "'{}'"},
        )
        with self.assertRaises(IntegrityError):
            self.store.get_document(self.document["documentId"])

    def test_invalid_document_rejected_before_write(self):
        invalid = deepcopy(self.document)
        invalid.pop("profileId")
        with self.assertRaises(InvalidDocumentError):
            self.store.put_document(invalid)

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

    def test_vector_and_full_text_retrieval_sidecar(self):
        records = [
            {"record_id": "a", "document_id": "doc-a", "text": "red running shoes",
             "vector": [1.0, 0.0, 0.0, 0.0]},
            {"record_id": "b", "document_id": "doc-b", "text": "blue running shoes",
             "vector": [0.9, 0.1, 0.0, 0.0]},
            {"record_id": "c", "document_id": "doc-c", "text": "waterproof rain jacket",
             "vector": [0.0, 1.0, 0.0, 0.0]},
        ]
        self.store.replace_retrieval_records(records)
        table = self.store._db.open_table("retrieval_records")
        from lancedb.index import FTS
        table.create_index("text", config=FTS())
        vector_hits = self.store.search_vectors([0.95, 0.05, 0.0, 0.0], limit=2)
        self.assertEqual(vector_hits[0]["record_id"], "b")
        text_hits = self.store.search_text("running", limit=3)
        self.assertGreaterEqual(len(text_hits), 2)
        self.assertTrue(all("running" in row["text"] for row in text_hits))

    def test_integrity_report(self):
        self.store.put_document(self.document)
        self.assertEqual(self.store.verify_integrity(self.document["documentId"])["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
