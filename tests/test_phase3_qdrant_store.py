"""Qdrant local-mode evaluation: canonical payload preservation and vector retrieval."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from qdrant_client import QdrantClient
from tools.semantic_graph_store_v1_0_0.canonical import canonical_bytes
from tools.semantic_graph_store_qdrant_v1_0_0 import (
    CanonicalDocumentStore, IntegrityError, InvalidDocumentError, RevisionConflictError,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
BASE = next(x["document"] for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")


class QdrantStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "qdrant"
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

    def test_append_only_revisions_idempotency_and_stale_writer_rejection(self):
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

    def test_competing_threads_are_serialized_for_compare_and_swap(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        self.store.put_document(self.document)
        barrier = Barrier(2)
        first = deepcopy(self.document)
        first["extensions"]["writer"] = "first"
        second = deepcopy(self.document)
        second["extensions"]["writer"] = "second"

        def attempt(changed):
            barrier.wait()
            try:
                return self.store.put_document(changed, expected_revision=1).revision
            except RevisionConflictError:
                return "CONFLICT"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [pool.submit(attempt, first), pool.submit(attempt, second)]
            outcomes = [item.result() for item in results]
        self.assertEqual(sorted(str(x) for x in outcomes), ["2", "CONFLICT"])
        self.assertEqual([x["revision"] for x in self.store.list_revisions(self.document["documentId"])], [1, 2])

    def test_persistent_reopen_preserves_revisions(self):
        self.store.put_document(self.document)
        changed = deepcopy(self.document)
        changed["extensions"]["revisionNote"] = "revision two"
        self.store.put_document(changed, expected_revision=1)
        self.store.close()
        self.store = CanonicalDocumentStore(self.path)
        self.assertEqual([x["revision"] for x in self.store.list_revisions(self.document["documentId"])], [1, 2])
        self.assertEqual(self.store.get_document(self.document["documentId"]).revision, 2)

    def test_local_mode_rejects_second_client_for_same_storage_path(self):
        with self.assertRaises(RuntimeError):
            QdrantClient(path=str(self.path))

    def test_snapshot_tampering_is_detected(self):
        self.store.put_document(self.document)
        point_id = self.store._point_id(self.document["documentId"], 1)
        self.store._client.set_payload(
            collection_name="usg_canonical_revisions",
            payload={"canonical_json": "{}"}, points=[point_id], wait=True,
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

    def test_vector_retrieval_with_known_answer_and_payload(self):
        records = [
            {"record_id": "00000000-0000-0000-0000-000000000001", "document_id": "doc-a",
             "text": "red running shoes", "vector": [1.0, 0.0, 0.0, 0.0]},
            {"record_id": "00000000-0000-0000-0000-000000000002", "document_id": "doc-b",
             "text": "blue running shoes", "vector": [0.8, 0.2, 0.0, 0.0]},
            {"record_id": "00000000-0000-0000-0000-000000000003", "document_id": "doc-c",
             "text": "waterproof rain jacket", "vector": [0.0, 1.0, 0.0, 0.0]},
        ]
        self.store.replace_retrieval_records(records)
        hits = self.store.search_vectors([0.95, 0.05, 0.0, 0.0], limit=2)
        self.assertEqual(hits[0]["record_id"], records[0]["record_id"])
        self.assertEqual(hits[0]["document_id"], "doc-a")
        self.assertEqual(len(hits), 2)

    def test_integrity_report(self):
        self.store.put_document(self.document)
        self.assertEqual(self.store.verify_integrity(self.document["documentId"])["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
