"""Phase 7 SQLite knowledge repository integration and immutability tests."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.phase7_knowledge_repository import (
    KNOWLEDGE_REPOSITORY_VERSION, SQLiteKnowledgeRepository,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "examples/phase7-knowledge-bundle-0.1.0.json").read_text(encoding="utf-8"))


class Phase7SQLiteKnowledgeRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.store = CanonicalDocumentStore(":memory:")
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
            self.repository = SQLiteKnowledgeRepository(connection)

    def tearDown(self):
        self.store.close()

    def write(self, operation):
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
            return operation()

    def read(self, operation):
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE):
            return operation()

    def test_repository_uses_the_exact_canonical_store_connection(self):
        self.assertIs(self.repository.connection, self.store._connection)
        self.assertEqual(self.repository.version, 1)
        self.assertEqual(KNOWLEDGE_REPOSITORY_VERSION, "sqlite-usg-knowledge-repository/0.1.0")

    def test_installation_requires_caller_owned_transaction(self):
        other = sqlite3.connect(":memory:")
        try:
            with self.assertRaises(RuntimeError):
                SQLiteKnowledgeRepository(other)
        finally:
            other.close()

    def test_bundle_round_trip_and_digest_verification(self):
        snapshot = self.write(lambda: self.repository.put_bundle(deepcopy(FIXTURE)))
        self.assertEqual(snapshot.bundle_version, 1)
        self.assertEqual(snapshot.status, "STORED")
        loaded = self.read(lambda: self.repository.get_snapshot(snapshot.snapshot_id))
        self.assertEqual(loaded.bundle, FIXTURE)
        self.assertEqual(loaded.digest, snapshot.digest)
        self.assertEqual(loaded.status, "VERIFIED")

    def test_identical_bundle_is_idempotent(self):
        first = self.write(lambda: self.repository.put_bundle(deepcopy(FIXTURE)))
        second = self.write(lambda: self.repository.put_bundle(deepcopy(FIXTURE)))
        self.assertEqual(first.snapshot_id, second.snapshot_id)
        self.assertEqual(second.bundle_version, 1)
        self.assertEqual(second.status, "UNCHANGED")
        self.assertEqual(self.repository.version, 2)

    def test_new_content_creates_a_new_immutable_bundle_version(self):
        first = self.write(lambda: self.repository.put_bundle(deepcopy(FIXTURE)))
        revised = deepcopy(FIXTURE)
        revised["bundle_id"] = FIXTURE["bundle_id"]
        revised["records"][0]["payload"]["script"] = "Latin"
        second = self.write(lambda: self.repository.put_bundle(revised))
        self.assertNotEqual(first.snapshot_id, second.snapshot_id)
        self.assertEqual(second.bundle_version, 2)
        self.assertEqual(self.repository.get_latest(FIXTURE["bundle_id"]).snapshot_id, second.snapshot_id)

    def test_snapshots_and_indexes_are_append_only(self):
        snapshot = self.write(lambda: self.repository.put_bundle(deepcopy(FIXTURE)))
        with self.assertRaises(sqlite3.IntegrityError):
            self.write(lambda: self.repository.connection.execute(
                "UPDATE usg_knowledge_bundle_snapshot SET namespace='changed' WHERE snapshot_id=?",
                (snapshot.snapshot_id,),
            ))
        with self.assertRaises(sqlite3.IntegrityError):
            self.write(lambda: self.repository.connection.execute(
                "DELETE FROM usg_knowledge_record_index WHERE snapshot_id=?",
                (snapshot.snapshot_id,),
            ))

    def test_rollback_removes_the_entire_uncommitted_snapshot(self):
        with self.assertRaises(RuntimeError):
            with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
                repository = SQLiteKnowledgeRepository(connection)
                repository.put_bundle(deepcopy(FIXTURE))
                raise RuntimeError("force rollback")
        self.assertEqual(self.read(lambda: self.repository.list_snapshots()), ())
        self.assertEqual(self.repository.version, 1)

    def test_canonical_semantic_document_tables_remain_available(self):
        snapshot = self.write(lambda: self.repository.put_bundle(deepcopy(FIXTURE)))
        self.assertIsNotNone(snapshot)
        tables = self.read(lambda: {row[0] for row in self.repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )})
        self.assertIn("documents", tables)
        self.assertIn("document_revisions", tables)
        self.assertIn("usg_knowledge_bundle_snapshot", tables)

    def test_invalid_bundle_is_rejected_before_any_write(self):
        invalid = deepcopy(FIXTURE)
        invalid["records"][0]["payload"].pop("script")
        with self.assertRaises(ValueError):
            self.write(lambda: self.repository.put_bundle(invalid))
        self.assertEqual(self.read(lambda: self.repository.list_snapshots()), ())


if __name__ == "__main__":
    unittest.main()
