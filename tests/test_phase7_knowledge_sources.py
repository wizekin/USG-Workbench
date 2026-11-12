"""Rights-aware Phase 7 source adapter tests."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.phase7_knowledge_sources import (
    KnowledgeSourceAdapterError, adapt_canonical_document,
    adapt_lexical_candidate_package, ingest_canonical_document,
)
from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))


def lexical_package():
    return {
        "contract":"USG-LEXICAL-CANDIDATES/0.1.0","queried_form":"bank","candidate_count":2,
        "candidates":[
            {"candidate_id":"river","lemma":"bank","language":"en","part_of_speech":"noun",
             "definition":"Land alongside a river.","examples":[],"features":[],
             "observed_forms":[{"form":"banks","tags":["plural"]}],"source_provider":"fixture",
             "source_id":"source-a","source_entry_id":"entry-a","source_sense_id":"sense-a",
             "relations":[],"promotion_status":"candidate_only"},
            {"candidate_id":"financial","lemma":"bank","language":"en","part_of_speech":"noun",
             "definition":"A financial institution.","examples":[],"features":[],"observed_forms":[],
             "source_provider":"fixture","source_id":"source-a","source_entry_id":"entry-a",
             "source_sense_id":"sense-b","relations":[],"promotion_status":"candidate_only"},
        ],
        "entry_relations":[],"definition_pattern_observations":[],
        "semantic_candidate_graph":{"nodes":[],"edges":[]},
        "source_provenance":[{"provider":"fixture","provider_url":"https://example.invalid/dictionary",
                              "license":"unverified","attribution":"Fixture source"}],
        "validation":{"status":"valid","promotion_allowed":False},"content_digest":"a"*64,
        "promotion_allowed":False,"integration_note":"Synthetic candidate fixture.",
    }


def canonical_document():
    doc = deepcopy(FIXTURES["fixtures"][0]["document"])
    doc["definitions"]["ontologyRelease"] = "fixture-ontology-1"
    doc["definitions"]["concepts"] = [{
        "id":"concept-bank","label":"Bank","semanticKind":"ENTITY","version":1,
        "definition":"Synthetic concept fixture."
    }]
    doc["definitions"]["roles"] = [{"id":"role-agent","label":"Agent","constraints":{}}]
    doc["definitions"]["frames"] = [{
        "id":"frame-transfer","label":"Transfer","version":1,"semanticKind":"EVENT",
        "roles":["role-agent"]
    }]
    doc["definitions"]["relations"] = [{"id":"relation-before","label":"BEFORE","properties":{}}]
    doc["validation"]["structuralStatus"] = "PASS"
    return doc


class Phase7KnowledgeSourceAdapterTests(unittest.TestCase):
    def test_unknown_rights_withhold_external_definition_text_by_default(self):
        result = adapt_lexical_candidate_package(lexical_package(), retrieved_at="2026-11-12T10:00:00Z")
        senses = [x for x in result["bundle"]["records"] if x["kind"] == "LEXICAL_SENSE"]
        self.assertEqual(result["withheld_definition_count"], 2)
        self.assertTrue(all(x["payload"]["definition"] is None for x in senses))
        self.assertTrue(all(x["payload"]["definition_withheld"] for x in senses))
        self.assertTrue(all(x["state"] == "CANDIDATE" for x in senses))
        self.assertEqual(result["bundle"]["sources"][0]["rights_status"], "UNKNOWN")
        self.assertFalse(result["bundle"]["extensions"]["promotion_allowed"])

    def test_explicit_license_and_rights_policy_allows_definition_retention(self):
        result = adapt_lexical_candidate_package(
            lexical_package(), retrieved_at="2026-11-12T10:00:00Z",
            rights_overrides={"fixture":{"rights_status":"KNOWN_PERMITTED","redistribution":"ALLOWED",
                                         "license_id":"CC-BY-4.0","attribution":"Fixture source, CC-BY-4.0"}},
        )
        senses = [x for x in result["bundle"]["records"] if x["kind"] == "LEXICAL_SENSE"]
        self.assertEqual(result["retained_definition_count"], 2)
        self.assertEqual({x["payload"]["definition"] for x in senses},
                         {"Land alongside a river.", "A financial institution."})
        self.assertTrue(all(x["state"] == "CANDIDATE" for x in senses))

    def test_unknown_or_unlicensed_rights_cannot_be_marked_redistributable(self):
        for override in (
            {"rights_status":"UNKNOWN","redistribution":"ALLOWED"},
            {"rights_status":"KNOWN_PERMITTED","redistribution":"ALLOWED"},
        ):
            with self.subTest(override=override), self.assertRaises(KnowledgeSourceAdapterError):
                adapt_lexical_candidate_package(
                    lexical_package(), retrieved_at="2026-11-12T10:00:00Z",
                    rights_overrides={"fixture":override},
                )

    def test_prohibited_provider_content_is_withheld(self):
        result = adapt_lexical_candidate_package(
            lexical_package(), retrieved_at="2026-11-12T10:00:00Z",
            rights_overrides={"fixture":{"rights_status":"PROHIBITED","redistribution":"PROHIBITED"}},
        )
        senses = [x for x in result["bundle"]["records"] if x["kind"] == "LEXICAL_SENSE"]
        self.assertEqual(len(senses), 2)
        self.assertTrue(all(x["payload"]["definition"] is None for x in senses))

    def test_provider_senses_remain_distinct_and_are_not_auto_mapped(self):
        bundle = adapt_lexical_candidate_package(
            lexical_package(), retrieved_at="2026-11-12T10:00:00Z"
        )["bundle"]
        senses = [x for x in bundle["records"] if x["kind"] == "LEXICAL_SENSE"]
        self.assertEqual(len(senses), 2)
        self.assertNotEqual(senses[0]["id"], senses[1]["id"])
        self.assertEqual(bundle["mappings"], [])
        self.assertEqual(bundle["relations"], [])

    def test_adaptation_is_deterministic_for_fixed_inputs(self):
        first = adapt_lexical_candidate_package(lexical_package(), retrieved_at="2026-11-12T10:00:00Z")
        second = adapt_lexical_candidate_package(lexical_package(), retrieved_at="2026-11-12T10:00:00Z")
        self.assertEqual(first["bundle"], second["bundle"])

    def test_unknown_rights_override_provider_is_rejected(self):
        with self.assertRaises(KnowledgeSourceAdapterError):
            adapt_lexical_candidate_package(
                lexical_package(), retrieved_at="2026-11-12T10:00:00Z",
                rights_overrides={"typo":{"rights_status":"KNOWN_PERMITTED","redistribution":"ALLOWED",
                                          "license_id":"CC-BY-4.0"}},
            )

    def test_canonical_document_adapter_preserves_definitions_without_mutation(self):
        doc = canonical_document()
        before = deepcopy(doc)
        result = adapt_canonical_document(doc)
        self.assertEqual(doc, before)
        bundle = result["bundle"]
        self.assertEqual(bundle["extensions"]["source_contract"], "USG-SEM/1.0")
        self.assertTrue(any(x["kind"] == "CONCEPT" for x in bundle["records"]))
        self.assertTrue(any(x["kind"] == "PREDICATE_FRAME" for x in bundle["records"]))
        self.assertTrue(any(x["kind"] == "SEMANTIC_CLASS" for x in bundle["records"]))
        self.assertEqual(bundle["relations"], [])
        self.assertTrue(all(x["state"] == "VALIDATED_FOR_PROFILE" for x in bundle["records"]))
        self.assertFalse(result["promotion_allowed"])

    def test_canonical_adapter_rejects_unvalidated_or_invalid_documents(self):
        doc = canonical_document()
        doc["validation"]["structuralStatus"] = "FAIL"
        with self.assertRaises(KnowledgeSourceAdapterError):
            adapt_canonical_document(doc)
        invalid = canonical_document()
        invalid["documentId"] = "invalid id with spaces"
        with self.assertRaises(KnowledgeSourceAdapterError):
            adapt_canonical_document(invalid)

    def test_canonical_bundle_can_be_ingested_into_the_existing_sqlite_authority(self):
        doc = canonical_document()
        with CanonicalDocumentStore(":memory:") as store:
            with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
                repository = SQLiteKnowledgeRepository(connection)
            with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
                snapshot = ingest_canonical_document(repository, doc)
            with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE):
                loaded = repository.get_snapshot(snapshot.snapshot_id)
            self.assertEqual(loaded.bundle["extensions"]["source_contract"], "USG-SEM/1.0")
            self.assertEqual(loaded.bundle["contract"], "USG-KNOWLEDGE/0.1.0")


if __name__ == "__main__":
    unittest.main()
