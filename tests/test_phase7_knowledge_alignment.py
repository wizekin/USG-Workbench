"""Candidate-only English/MSA alignment proposal tests."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.phase7_knowledge_alignment import (
    AlignmentProposalError, build_bilingual_alignment_bundle,
    ingest_bilingual_alignment_bundle,
)
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = json.loads((ROOT / "resources/lexical/v0.3.0/en-ar-discourse-lexicon.json").read_text(encoding="utf-8"))


class Phase7BilingualAlignmentTests(unittest.TestCase):
    def test_resource_generates_unresolved_many_to_many_sense_concept_proposals(self):
        bundle = build_bilingual_alignment_bundle(RESOURCE, created_at="2026-11-12T12:00:00Z")
        self.assertEqual(bundle["contract"], "USG-KNOWLEDGE/0.1.0")
        self.assertEqual(bundle["extensions"]["alignment_policy"], "candidate-hint-only/0.1.0")
        self.assertFalse(bundle["extensions"]["equivalence_inferred"])
        self.assertFalse(bundle["extensions"]["promotion_allowed"])
        self.assertEqual(len(bundle["mappings"]), 2)
        self.assertTrue(all(x["mapping_type"] == "UNRESOLVED" for x in bundle["mappings"]))
        self.assertTrue(all(x["state"] == "UNRESOLVED" for x in bundle["mappings"]))

    def test_english_and_arabic_pronoun_candidates_share_only_unresolved_grouping_hints(self):
        bundle = build_bilingual_alignment_bundle(RESOURCE, created_at="2026-11-12T12:00:00Z")
        senses = {x["payload"]["sense_source_id"]: x for x in bundle["records"] if x["kind"] == "LEXICAL_SENSE"}
        expected = {("en:pronoun.he", "ar:pronoun.huwa"), ("en:pronoun.she", "ar:pronoun.hiya")}
        mapped = set()
        for mapping in bundle["mappings"]:
            source = next(x for x in senses.values() if x["id"] == mapping["source_record_id"])
            target = next(x for x in bundle["records"] if x["id"] == mapping["target_record_id"])
            mapped.add((source["payload"]["sense_source_id"], target["payload"]["label"]))
            self.assertEqual(target["state"], "UNRESOLVED")
            self.assertIn("not equivalent", mapping["notes"].lower())
        self.assertEqual({(a, b) for a, b in mapped},
                         {("en:pronoun.he", "concept:pronoun.third-singular-masculine"),
                          ("en:pronoun.she", "concept:pronoun.third-singular-feminine")})

    def test_polysemous_bank_senses_are_not_collapsed(self):
        bundle = build_bilingual_alignment_bundle(RESOURCE, created_at="2026-11-12T12:00:00Z")
        bank = [x for x in bundle["records"] if x["kind"] == "LEXICAL_SENSE"
                and x["payload"]["language"] == "en"
                and x["payload"]["lemma_record_id"] == next(
                    y["id"] for y in bundle["records"] if y["kind"] == "LEMMA"
                    and y["payload"]["lemma"] == "bank"
                )]
        self.assertEqual(len(bank), 2)
        self.assertEqual({x["payload"]["resource_concept_ref_hint"] for x in bank},
                         {"concept:bank.financial", "concept:bank.river"})
        self.assertEqual(bundle["mappings"], [
            x for x in bundle["mappings"]
            if x["source_record_id"] not in {item["id"] for item in bank}
        ])

    def test_every_generated_record_remains_candidate_or_unresolved(self):
        bundle = build_bilingual_alignment_bundle(RESOURCE, created_at="2026-11-12T12:00:00Z")
        self.assertTrue(all(x["state"] in {"CANDIDATE", "UNRESOLVED"} for x in bundle["records"]))
        self.assertTrue(all(x["state"] == "UNRESOLVED" for x in bundle["mappings"]))
        self.assertEqual(bundle["relations"], [])

    def test_output_is_deterministic_for_fixed_resource_and_timestamp(self):
        first = build_bilingual_alignment_bundle(RESOURCE, created_at="2026-11-12T12:00:00Z")
        second = build_bilingual_alignment_bundle(RESOURCE, created_at="2026-11-12T12:00:00Z")
        self.assertEqual(first, second)

    def test_resource_is_not_mutated(self):
        resource = deepcopy(RESOURCE)
        before = deepcopy(resource)
        build_bilingual_alignment_bundle(resource, created_at="2026-11-12T12:00:00Z")
        self.assertEqual(resource, before)

    def test_duplicate_sense_ids_with_conflicting_data_are_rejected(self):
        resource = deepcopy(RESOURCE)
        duplicate = deepcopy(resource["entries"][0])
        duplicate["form"] = "changed"
        resource["entries"].append(duplicate)
        with self.assertRaises(AlignmentProposalError):
            build_bilingual_alignment_bundle(resource, created_at="2026-11-12T12:00:00Z")

    def test_ingestion_uses_existing_canonical_sqlite_authority(self):
        with CanonicalDocumentStore(":memory:") as store:
            with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
                repository = SQLiteKnowledgeRepository(connection)
            with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
                snapshot = ingest_bilingual_alignment_bundle(
                    repository, RESOURCE, created_at="2026-11-12T12:00:00Z"
                )
            with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE):
                loaded = repository.get_snapshot(snapshot.snapshot_id)
            self.assertEqual(loaded.bundle["extensions"]["source_resource_id"], RESOURCE["resource_id"])
            self.assertEqual(loaded.bundle["mappings"], snapshot.bundle["mappings"])


if __name__ == "__main__":
    unittest.main()
