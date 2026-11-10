"""Tests for revision-pinned persistent query integration (Phase 3 Step 3.3)."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore, DocumentNotFoundError
from tools.semantic_query_interface_v1_0_0 import QueryInterface
from tools.semantic_query_interface_v1_0_0.persistent import PersistentQueryService

ROOT = Path(__file__).resolve().parents[1]
QUERY_FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/query-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)
EXECUTOR_FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)


def resolve_document(reference):
    if reference["benchmark_id"] != "USG-INFERENCE-EXECUTOR-BENCHMARK":
        raise AssertionError("unregistered benchmark reference")
    matches = [item for item in EXECUTOR_FIXTURES["fixtures"] if item["id"] == reference["fixture_id"]]
    if len(matches) != 1:
        raise AssertionError("fixture reference must resolve exactly once")
    return matches[0]["document"]


class PersistentQueryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CanonicalDocumentStore(Path(self.temp.name) / "usg.sqlite3")
        self.interface = QueryInterface()
        self.service = PersistentQueryService(self.store, self.interface)
        self.fixture = next(
            item for item in QUERY_FIXTURES["fixtures"]
            if item["id"] == "QUERY-DERIVED-MP-001"
        )
        self.document = deepcopy(resolve_document(self.fixture["document_ref"]))
        self.query = deepcopy(self.fixture["query"])

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_query_runs_from_verified_persisted_snapshot_and_pins_revision(self):
        stored = self.store.put_document(self.document)
        result = self.service.run(stored.document_id, self.query)

        self.assertEqual(result["profile_id"], "USG-PERSISTENT-QUERY/1.0.0")
        self.assertEqual(result["document_id"], stored.document_id)
        self.assertEqual(result["document_revision"], 1)
        self.assertEqual(result["document_sha256"], stored.digest)
        self.assertEqual(result["query_result"]["document_sha256"], stored.digest)
        self.assertEqual(result["query_result"]["goal_status"], "DERIVED_NOT_VERIFIED")
        self.assertTrue(result["safety"]["revision_pinned"])
        self.assertFalse(result["safety"]["canonical_document_mutated"])

    def test_persistent_query_does_not_mutate_caller_document_or_store(self):
        before = deepcopy(self.document)
        stored = self.store.put_document(self.document)
        self.service.run(stored.document_id, self.query)

        self.assertEqual(self.document, before)
        reloaded = self.store.get_document(stored.document_id, revision=1)
        self.assertEqual(reloaded.document, before)
        self.assertEqual(reloaded.digest, stored.digest)

    def test_explicit_revision_is_used_instead_of_current_pointer(self):
        stored = self.store.put_document(self.document)
        # A second immutable revision is created by changing only opaque metadata.
        revised = deepcopy(self.document)
        revised["extensions"] = {"benchmarkRevision": "revision-2"}
        second = self.store.put_document(revised, expected_revision=1)

        historical = self.service.run(stored.document_id, self.query, revision=1)
        current = self.service.run(stored.document_id, self.query)

        self.assertEqual(second.revision, 2)
        self.assertEqual(historical["document_revision"], 1)
        self.assertEqual(historical["document_sha256"], stored.digest)
        self.assertEqual(current["document_revision"], 2)
        self.assertEqual(current["document_sha256"], second.digest)

    def test_missing_document_fails_without_partial_success(self):
        with self.assertRaises(DocumentNotFoundError):
            self.service.run("missing-document", self.query)


if __name__ == "__main__":
    unittest.main()
