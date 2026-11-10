"""Tests for Phase 3 Step 3.6 local API and CLI."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.usg_local_api_v1_0_0 import USGApplication, create_server
from tools.usg_local_api_v1_0_0.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]
EXEC_FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
QUERY_FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/query-v1.0.0/fixtures.json").read_text(encoding="utf-8"))


def sample_document():
    return deepcopy(next(x["document"] for x in EXEC_FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001"))


def sample_query():
    return deepcopy(next(x["query"] for x in QUERY_FIXTURES["fixtures"] if x["id"] == "QUERY-DERIVED-MP-001"))


class LocalAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "usg.sqlite3")
        self.app = USGApplication(self.db)
        self.document = sample_document()

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def call(self, method, path, body=None):
        return self.app.dispatch(method, path, body)

    def test_health_and_validation(self):
        status, health = self.call("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["storage"], "SQLite")
        status, result = self.call("POST", "/v1/validate", self.document)
        self.assertEqual(status, 200)
        self.assertEqual(result["completion_status"], "VALID")
        self.assertEqual(result["document_id"], self.document["documentId"])

    def test_invalid_document_is_422(self):
        doc = deepcopy(self.document)
        doc["profileId"] = "NOT-USG"
        status, result = self.call("POST", "/v1/validate", doc)
        self.assertEqual(status, 422)
        self.assertEqual(result["completion_status"], "INVALID_INPUT")

    def test_store_get_revision_and_export_are_lossless(self):
        status, stored = self.call("POST", "/v1/documents", {"document": self.document})
        self.assertEqual(status, 201)
        self.assertEqual(stored["revision"], 1)
        status, fetched = self.call("GET", "/v1/documents/" + self.document["documentId"])
        self.assertEqual(status, 200)
        self.assertEqual(fetched["document"], self.document)
        status, exported = self.call("GET", "/v1/documents/" + self.document["documentId"] + "/export")
        self.assertEqual(status, 200)
        self.assertEqual(exported, self.document)

    def test_idempotent_write_and_compare_and_swap_conflict(self):
        self.call("POST", "/v1/documents", {"document": self.document})
        status, again = self.call("POST", "/v1/documents", {"document": self.document})
        self.assertEqual(status, 200)
        self.assertTrue(again["idempotent"])
        revised = deepcopy(self.document)
        revised["extensions"] = {"version": 2}
        status, conflict = self.call("POST", "/v1/documents", {"document": revised, "expected_revision": 0})
        self.assertEqual(status, 409)
        self.assertEqual(conflict["error"], "REVISION_CONFLICT")
        status, updated = self.call("POST", "/v1/documents", {"document": revised, "expected_revision": 1})
        self.assertEqual(status, 201)
        self.assertEqual(updated["revision"], 2)

    def test_check_and_revisions(self):
        self.call("POST", "/v1/documents", {"document": self.document})
        doc_id = self.document["documentId"]
        status, report = self.call("GET", f"/v1/documents/{doc_id}/check")
        self.assertEqual(status, 200)
        self.assertEqual(report["status"], "PASS")
        status, revisions = self.call("GET", f"/v1/documents/{doc_id}/revisions")
        self.assertEqual(status, 200)
        self.assertEqual([x["revision"] for x in revisions["revisions"]], [1])

    def test_query_conditions_and_contradictions_use_stored_snapshot(self):
        self.call("POST", "/v1/documents", {"document": self.document})
        doc_id = self.document["documentId"]
        status, result = self.call("POST", "/v1/query", {
            "document_id": doc_id, "query": sample_query(), "revision": 1
        })
        self.assertEqual(status, 200)
        self.assertEqual(result["document_revision"], 1)
        self.assertEqual(result["query_result"]["goal_status"], "DERIVED_NOT_VERIFIED")
        status, conditions = self.call("GET", f"/v1/documents/{doc_id}/conditions")
        self.assertEqual(status, 200)
        self.assertTrue(conditions["conditions"])
        status, conflicts = self.call("GET", f"/v1/documents/{doc_id}/contradictions")
        self.assertEqual(status, 200)
        self.assertEqual(conflicts["conflicts"], [])

    def test_raw_text_interpretation_uses_phase4_pipeline(self):
        status, result = self.call("POST", "/v1/interpret", {
            "text": "Ada writes code", "language": "en", "persist": True
        })
        self.assertEqual(status, 200)
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(result["document"]["profileId"], "USG-SEM/1.0")
        self.assertEqual(result["persistence"]["status"], "STORED")

    def test_unknown_routes_and_missing_documents(self):
        self.assertEqual(self.call("GET", "/unknown")[0], 404)
        self.assertEqual(self.call("GET", "/v1/documents/missing")[0], 404)

    def test_revision_and_expected_revision_validation(self):
        self.assertEqual(self.call("GET", "/v1/documents/x?revision=zero")[0], 400)
        self.assertEqual(self.call("POST", "/v1/documents", {"document": self.document, "expected_revision": -1})[0], 400)

    def test_server_refuses_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            create_server(self.app, host="0.0.0.0", port=0)
        server = create_server(self.app, host="127.0.0.1", port=0)
        try:
            self.assertTrue(server.server_address[0].startswith("127."))
        finally:
            server.server_close()

    def test_cli_exposes_expected_commands(self):
        parser = build_parser()
        args = parser.parse_args(["serve"])
        self.assertEqual(args.command, "serve")
        self.assertEqual(args.host, "127.0.0.1")
        args = parser.parse_args(["query", "doc-x", "query.json"])
        self.assertEqual(args.command, "query")


if __name__ == "__main__":
    unittest.main()
