"""Step 7.8 read-only Phase 2/4/5/6 adapter tests."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.phase7_knowledge_integration import KnowledgeReadAdapter, KnowledgeIntegrationError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "examples/phase7-knowledge-bundle-0.1.0.json").read_text(encoding="utf-8"))


class Phase7ReadOnlyIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.store = CanonicalDocumentStore(":memory:")
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
            self.repository = SQLiteKnowledgeRepository(connection)
        accepted = deepcopy(FIXTURE)
        accepted["bundle_id"] = "integration:accepted"
        for record in accepted["records"]:
            record["state"] = "ACCEPTED"
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
            self.repository.put_bundle(accepted)
        candidate = deepcopy(FIXTURE)
        candidate["bundle_id"] = "integration:candidate"
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
            self.repository.put_bundle(candidate)
        self.adapter = KnowledgeReadAdapter(self.repository)

    def tearDown(self):
        self.store.close()

    def test_phase2_receives_only_accepted_or_profile_validated_knowledge(self):
        result = self.adapter.for_phase2("bank", language="en")
        self.assertTrue(result["retrieval"]["results"])
        self.assertTrue(all(x["state"] == "ACCEPTED" for x in result["retrieval"]["results"]))
        self.assertFalse(result["candidate_only"])

    def test_phase4_and_phase5_default_to_non_candidate_records(self):
        for method in (self.adapter.for_phase4, self.adapter.for_phase5):
            result = method("bank", language="en")
            self.assertTrue(result["retrieval"]["results"])
            self.assertTrue(all(x["state"] in {"ACCEPTED", "VALIDATED_FOR_PROFILE"}
                                for x in result["retrieval"]["results"]))

    def test_phase4_can_explicitly_request_candidate_evidence_without_promotion(self):
        result = self.adapter.for_phase4("bank", language="en", include_candidate_evidence=True)
        self.assertTrue(result["retrieval"]["results"])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["runtime_mutation_performed"])

    def test_phase6_adapter_exposes_candidate_only_records(self):
        result = self.adapter.for_phase6_candidate("bank", language="en")
        self.assertTrue(result["candidate_only"])
        self.assertTrue(result["retrieval"]["results"])
        self.assertTrue(all(x["state"] in {"CANDIDATE", "UNRESOLVED"}
                            for x in result["retrieval"]["results"]))
        self.assertFalse(result["promotion_allowed"])

    def test_adapter_is_read_only_and_does_not_advance_repository_version(self):
        before = self.repository.version
        self.adapter.for_phase2("bank", language="en")
        self.adapter.for_phase6_candidate("bank", language="en")
        self.assertEqual(self.repository.version, before)
        self.assertFalse(self.adapter.for_phase2("bank")["runtime_mutation_performed"])

    def test_unknown_consumer_is_rejected(self):
        with self.assertRaises(KnowledgeIntegrationError):
            self.adapter.query("PHASE7", "bank")


if __name__ == "__main__":
    unittest.main()
