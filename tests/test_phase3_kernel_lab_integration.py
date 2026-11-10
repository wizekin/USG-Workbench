"""Phase 3 Step 3.7 browser-to-API-to-SQLite integration tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations" / "python-kernel" / "v0.7.0"))
SERVER_PATH = ROOT / "tools" / "usg-kernel-lab" / "server.py"
SPEC = importlib.util.spec_from_file_location("usg_kernel_lab_phase3_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SERVER
SPEC.loader.exec_module(SERVER)

EXEC_FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)
QUERY_FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/query-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)


def sample_document():
    return next(x["document"] for x in EXEC_FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")


def sample_query():
    return next(x["query"] for x in QUERY_FIXTURES["fixtures"] if x["id"] == "QUERY-DERIVED-MP-001")


class KernelLabPersistentIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db = str(Path(self.temp.name) / "kernel-lab.sqlite3")
        self.server = SERVER.create_lab_server(db, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        try:
            with urlopen(request, timeout=10) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return response.status, json.loads(raw.decode("utf-8"))
                return response.status, raw
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_browser_serves_integrated_persistent_workspace(self):
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"persistentDocumentId", html)
        self.assertIn(b"queryPersistentBtn", html)
        status, health = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["documentStore"], "SQLite")
        self.assertEqual(health["persistentApi"], "USG-LOCAL-API/1.0.0")

    def test_browser_api_saves_loads_checks_and_exports_exact_document(self):
        document = sample_document()
        doc_id = document["documentId"]
        status, saved = self.request("POST", "/v1/documents", {"document": document})
        self.assertEqual(status, 201)
        self.assertEqual(saved["revision"], 1)

        status, loaded = self.request("GET", f"/v1/documents/{doc_id}")
        self.assertEqual(status, 200)
        self.assertEqual(loaded["document"], document)
        self.assertEqual(loaded["status"], "VERIFIED")

        status, integrity = self.request("GET", f"/v1/documents/{doc_id}/check")
        self.assertEqual(status, 200)
        self.assertEqual(integrity["status"], "PASS")

        status, exported = self.request("GET", f"/v1/documents/{doc_id}/export")
        self.assertEqual(status, 200)
        self.assertEqual(exported, document)

    def test_stored_query_conditions_and_conflicts_share_same_revision(self):
        document = sample_document()
        doc_id = document["documentId"]
        self.request("POST", "/v1/documents", {"document": document})

        status, query = self.request("POST", "/v1/query", {
            "document_id": doc_id, "query": sample_query(), "revision": 1
        })
        self.assertEqual(status, 200)
        self.assertEqual(query["document_revision"], 1)
        self.assertEqual(query["query_result"]["goal_status"], "DERIVED_NOT_VERIFIED")

        status, conditions = self.request("GET", f"/v1/documents/{doc_id}/conditions?revision=1")
        self.assertEqual(status, 200)
        self.assertEqual(conditions["document_sha256"], query["document_sha256"])

        status, conflicts = self.request("GET", f"/v1/documents/{doc_id}/contradictions?revision=1")
        self.assertEqual(status, 200)
        self.assertEqual(conflicts["document_sha256"], query["document_sha256"])
        self.assertEqual(conflicts["conflicts"], [])

    def test_ui_server_rejects_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            SERVER.create_lab_server(":memory:", host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
