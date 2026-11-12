"""Step 7.9 shared knowledge inspection service and CLI tests."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import importlib.util
import threading
from urllib.request import Request, urlopen

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.phase7_knowledge_inspection import KnowledgeInspectionService
from tools.phase7_knowledge_inspection.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "examples/phase7-knowledge-bundle-0.1.0.json").read_text(encoding="utf-8"))


class Phase7KnowledgeInspectionTests(unittest.TestCase):
    def setUp(self):
        self.store = CanonicalDocumentStore(":memory:")
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
            self.repository = SQLiteKnowledgeRepository(connection)
        bundle = deepcopy(FIXTURE)
        bundle["bundle_id"] = "inspection:test"
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
            self.repository.put_bundle(bundle)
        self.service = KnowledgeInspectionService(self.repository)

    def tearDown(self):
        self.store.close()

    def test_bundle_listing_returns_snapshot_metadata(self):
        result = self.service.list_bundles()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["bundles"][0]["bundle_id"], "inspection:test")

    def test_record_inspection_includes_source_evidence_and_context(self):
        record_id = next(x["id"] for x in FIXTURE["records"] if x["kind"] == "LEXICAL_SENSE")
        result = self.service.inspect_record(record_id)
        self.assertIsNotNone(result)
        self.assertTrue(result["sources"])
        self.assertTrue(result["evidence"])
        self.assertFalse(result["truth_adjudicated"])
        self.assertFalse(result["promotion_performed"])

    def test_unknown_record_returns_none(self):
        self.assertIsNone(self.service.inspect_record("record:missing"))

    def test_conflict_ledger_is_explicit_and_never_selects_winner(self):
        result = self.service.list_conflicts()
        self.assertEqual(result["count"], 0)
        self.assertFalse(result["winner_selected"])

    def test_query_uses_same_read_only_consumer_adapter(self):
        result = self.service.query("bank", consumer="PHASE2", language="en")
        self.assertEqual(result["consumer"], "PHASE2")
        self.assertFalse(result["runtime_mutation_performed"])

    def test_kernel_lab_api_exposes_knowledge_inspection_endpoints(self):
        server_path = ROOT / "tools/usg-kernel-lab/server.py"
        spec = importlib.util.spec_from_file_location("usg_kernel_lab_server", server_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            server = module.create_lab_server(Path(directory) / "lab.sqlite3", port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urlopen(base + "/api/knowledge/bundles") as response:
                    bundles = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertEqual(bundles["count"], 0)
                request = Request(base + "/api/knowledge/query",
                    data=json.dumps({"query": "bank", "consumer": "PHASE2"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}, method="POST")
                with urlopen(request) as response:
                    query = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertFalse(query["runtime_mutation_performed"])
                with urlopen(base + "/health") as response:
                    health = json.loads(response.read().decode("utf-8"))
                self.assertEqual(health["phase7KnowledgeInspection"], "USG-KNOWLEDGE-INSPECTION/0.1.0")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_cli_parser_exposes_bundles_query_inspect_and_conflicts(self):
        parser = build_parser()
        for argv, expected in [
            (["--db", "usg.sqlite3", "bundles"], "bundles"),
            (["--db", "usg.sqlite3", "query", "bank", "--consumer", "PHASE6"], "query"),
            (["--db", "usg.sqlite3", "inspect", "sense:bank"], "inspect"),
            (["--db", "usg.sqlite3", "conflicts"], "conflicts"),
        ]:
            self.assertEqual(parser.parse_args(argv).command, expected)


if __name__ == "__main__":
    unittest.main()
