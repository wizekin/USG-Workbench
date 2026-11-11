"""Phase 5 Step 5.10 integrated API, catalogue, run replay, and CLI tests."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.usg_interpretation_v0_1_0.resources import SemanticAssociation
from tools.usg_local_api_v1_0_0.application import USGApplication
from tools.usg_local_api_v1_0_0.cli import build_parser


class Phase5IntegratedAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "usg.sqlite3"
        self.app = USGApplication(self.database)

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def call(self, method, path, body=None):
        return self.app.dispatch(method, path, body)

    def interpret(self, persist=True):
        return self.call("POST", "/v2/interpret", {
            "text": "Ada writes code. She reads code.",
            "language": "en",
            "persist": persist,
        })

    def test_health_reports_integrated_phase5_contracts(self):
        status, result = self.call("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(result["phase5_pipeline"], "USG-INTERPRET/0.2.0")
        self.assertEqual(result["resource_catalogue"], "sqlite-semantic-resource-catalogue/0.1.0")

    def test_bundled_resource_catalogue_is_seeded_and_deterministic(self):
        status, first = self.call("GET", "/v2/resources")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(first["manifest"]["resources"]), 10)
        self.assertEqual(len(first["resource_manifest_digest"]), 64)
        status, second = self.call("GET", "/v2/resources")
        self.assertEqual(status, 200)
        self.assertEqual(first["resource_manifest_digest"], second["resource_manifest_digest"])

    def test_role_checked_adapter_uses_the_store_owned_connection(self):
        with self.assertRaises(PermissionError):
            with self.app.store.resource_catalogue_session(role="UNTRUSTED"):
                pass
        with self.app.store.resource_catalogue_session(
            role=RESOURCE_CATALOGUE_ROLE
        ) as connection:
            self.assertIs(connection, self.app.resource_catalogue.connection)
            self.assertFalse(connection.in_transaction)
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute(
                    "INSERT INTO usg_resource_descriptor "
                    "(resource_id,resource_type,version,sha256,language,provenance,registered_at) "
                    "VALUES('blocked','OTHER','1.0.0',?,'en','blocked',0)",
                    ("a" * 64,),
                )
        with self.app.store.resource_catalogue_session(
            role=RESOURCE_CATALOGUE_ROLE, write=True
        ) as connection:
            self.assertTrue(connection.in_transaction)
        with self.app.store.resource_catalogue_session(
            role=RESOURCE_CATALOGUE_ROLE
        ) as connection:
            self.assertFalse(connection.in_transaction)

    def test_catalogue_write_rolls_back_with_the_caller_transaction(self):
        association = SemanticAssociation(
            "rollback-association", "concept:a", "concept:b", "RELATED_TO",
            "CONTEXTUAL", 0.5, 0, "rollback test fixture",
        )
        with self.assertRaises(RuntimeError):
            with self.app.store.resource_catalogue_session(
                role=RESOURCE_CATALOGUE_ROLE, write=True
            ):
                self.app.resource_catalogue.register_association(association, 100.0)
                raise RuntimeError("injected transaction failure")
        status, result = self.call(
            "GET", "/v2/associations?source_ref=concept%3Aa"
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["count"], 0)

    def test_phase5_interpretation_returns_all_stage_artifacts_and_exact_source(self):
        status, result = self.interpret(persist=False)
        self.assertEqual(status, 200)
        self.assertEqual(result["pipeline_contract"], "USG-INTERPRET/0.2.0")
        self.assertEqual(result["source"]["text"], "Ada writes code. She reads code.")
        self.assertEqual(result["source"]["offset_unit"], "unicode_code_point")
        self.assertEqual(
            set(result["stages"]),
            {"lexical", "segmentation", "operators", "syntax", "semantic_composition", "discourse"},
        )
        self.assertIn("candidates", result["document_composition"])
        self.assertFalse(result["safety"]["usg_sem_document_emitted"])
        self.assertNotIn("persistence", result)

    def test_phase5_runs_persist_idempotently_and_replay_exactly(self):
        status, first = self.interpret()
        self.assertEqual(status, 200)
        self.assertEqual(first["persistence"]["status"], "STORED")
        run_id = first["persistence"]["run_id"]
        status, second = self.interpret()
        self.assertEqual(status, 200)
        self.assertEqual(second["persistence"]["run_id"], run_id)
        self.assertEqual(second["persistence"]["status"], "UNCHANGED")

        status, stored = self.call("GET", "/v2/interpretations/" + run_id)
        self.assertEqual(status, 200)
        self.assertEqual(stored["result"]["source"]["text"], first["source"]["text"])
        status, exported = self.call("GET", "/v2/interpretations/" + run_id + "/export")
        self.assertEqual(status, 200)
        self.assertEqual(exported, stored["result"])

        status, replay = self.call("POST", "/v2/interpretations/" + run_id + "/replay", {})
        self.assertEqual(status, 200)
        self.assertTrue(replay["deterministic_match"])
        self.assertEqual(replay["stored_result_sha256"], replay["replayed_result_sha256"])

        status, listed = self.call("GET", "/v2/interpretations?limit=10")
        self.assertEqual(status, 200)
        self.assertEqual(listed["count"], 1)

    def test_replay_refuses_a_changed_resource_manifest(self):
        status, result = self.interpret()
        self.assertEqual(status, 200)
        run_id = result["persistence"]["run_id"]
        association = {
            "association_id": "manifest-change-association",
            "source_ref": "concept:source",
            "target_ref": "concept:target",
            "relation": "RELATED_TO",
            "association_kind": "CONTEXTUAL",
            "weight": 0.4,
            "observation_count": 1,
            "provenance": "test fixture",
        }
        status, _ = self.call("POST", "/v2/associations", association)
        self.assertEqual(status, 201)
        status, error = self.call(
            "POST", "/v2/interpretations/" + run_id + "/replay", {}
        )
        self.assertEqual(status, 409)
        self.assertEqual(error["error"], "REPLAY_RESOURCE_MISMATCH")

    def test_association_creation_retrieval_and_usage_are_provisional(self):
        association = {
            "association_id": "association-api-1",
            "source_ref": "concept:source",
            "target_ref": "concept:target",
            "relation": "RELATED_TO",
            "association_kind": "FUNCTIONAL",
            "weight": 0.6,
            "observation_count": 2,
            "provenance": "explicit test fixture",
        }
        status, created = self.call("POST", "/v2/associations", association)
        self.assertEqual(status, 201)
        self.assertEqual(created["status"], "PROVISIONAL")
        self.assertFalse(created["identity_resolution"])

        status, retrieved = self.call(
            "GET", "/v2/associations?source_ref=concept%3Asource"
        )
        self.assertEqual(status, 200)
        self.assertEqual(retrieved["count"], 1)
        candidate = retrieved["associations"][0]
        self.assertEqual(candidate["association"]["status"], "PROVISIONAL")
        self.assertFalse(candidate["identity_resolution"])

        status, used = self.call(
            "POST", "/v2/associations/association-api-1/use", {"context_ref": "context:test"}
        )
        self.assertEqual(status, 201)
        self.assertTrue(used["usage_recorded"])

        status, after_use = self.call(
            "GET", "/v2/associations?source_ref=concept%3Asource"
        )
        self.assertEqual(status, 200)
        self.assertEqual(after_use["associations"][0]["total_observations"], 3)

    def test_invalid_phase5_requests_and_unknown_runs_are_rejected(self):
        status, error = self.call("POST", "/v2/interpret", {"text": "", "language": "en"})
        self.assertEqual(status, 400)
        self.assertEqual(error["error"], "PHASE5_INTERPRET_REQUEST_INVALID")
        status, error = self.call("GET", "/v2/interpretations/run:missing")
        self.assertEqual(status, 404)
        self.assertEqual(error["error"], "INTERPRETATION_RUN_NOT_FOUND")

    def test_cli_exposes_phase5_commands(self):
        parser = build_parser()
        args = parser.parse_args(["interpret-v2", "source.txt", "--language", "ar"])
        self.assertEqual(args.command, "interpret-v2")
        self.assertEqual(args.language, "ar")
        self.assertFalse(args.no_persist)
        self.assertEqual(parser.parse_args(["resources"]).command, "resources")
        self.assertEqual(parser.parse_args(["associations", "concept:x"]).source_ref, "concept:x")
        self.assertEqual(parser.parse_args(["replay", "run:abc"]).run_id, "run:abc")


if __name__ == "__main__":
    unittest.main()
