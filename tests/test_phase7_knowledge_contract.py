"""Tests for the additive USG-KNOWLEDGE/0.1.0 contract and validator."""
import copy
import json
import unittest
from pathlib import Path

from tools.phase7_knowledge_contract.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[1]


class Phase7KnowledgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "examples/phase7-knowledge-bundle-0.1.0.json").read_text(encoding="utf-8"))

    def test_example_bundle_passes_schema_and_cross_reference_validation(self):
        self.assertEqual(validate_bundle(self.fixture), [])

    def test_duplicate_record_ids_are_rejected(self):
        bundle = copy.deepcopy(self.fixture)
        bundle["records"].append(copy.deepcopy(bundle["records"][0]))
        self.assertTrue(any("duplicate IDs" in e for e in validate_bundle(bundle)))

    def test_unknown_source_reference_is_rejected(self):
        bundle = copy.deepcopy(self.fixture)
        bundle["evidence"][0]["source_id"] = "source:missing"
        self.assertTrue(any("unknown source_id" in e for e in validate_bundle(bundle)))

    def test_sense_must_reference_a_lemma(self):
        bundle = copy.deepcopy(self.fixture)
        sense = next(x for x in bundle["records"] if x["kind"] == "LEXICAL_SENSE")
        sense["payload"]["lemma_record_id"] = "concept:financial-institution"
        self.assertTrue(any("must reference a LEMMA" in e for e in validate_bundle(bundle)))

    def test_mapping_requires_existing_records_and_evidence(self):
        bundle = copy.deepcopy(self.fixture)
        bundle["mappings"].append({"id":"mapping:bad","source_record_id":"missing","target_record_id":"concept:financial-institution","mapping_type":"EQUIVALENT","state":"CANDIDATE","evidence_ids":["missing-evidence"],"context_ids":[]})
        errors = validate_bundle(bundle)
        self.assertTrue(any("mapping:bad" in e and "existing records" in e for e in errors))
        self.assertTrue(any("mapping:bad" in e and "unknown evidence" in e for e in errors))

    def test_restricted_or_unknown_rights_cannot_claim_redistribution_allowed(self):
        bundle = copy.deepcopy(self.fixture)
        bundle["sources"][0]["rights_status"] = "UNKNOWN"
        bundle["sources"][0]["redistribution"] = "ALLOWED"
        self.assertTrue(any("redistribution cannot be ALLOWED" in e for e in validate_bundle(bundle)))

    def test_relation_evidence_and_endpoints_are_checked(self):
        bundle = copy.deepcopy(self.fixture)
        bundle["relations"].append({"id":"relation:bad","subject_record_id":"missing","predicate":"RELATED_TO","object_record_id":"concept:financial-institution","direction":"DIRECTED","state":"CANDIDATE","evidence_ids":["missing-evidence"],"context_ids":[]})
        errors = validate_bundle(bundle)
        self.assertTrue(any("relation:bad" in e and "existing records" in e for e in errors))
        self.assertTrue(any("relation:bad" in e and "unknown evidence" in e for e in errors))

    def test_each_record_kind_requires_its_typed_payload_minimum(self):
        bundle = copy.deepcopy(self.fixture)
        form = next(x for x in bundle["records"] if x["kind"] == "LEXICAL_FORM")
        del form["payload"]["script"]
        self.assertTrue(any("script" in e for e in validate_bundle(bundle)))

    def test_unknown_record_kind_is_rejected(self):
        bundle = copy.deepcopy(self.fixture)
        bundle["records"][0]["kind"] = "UNKNOWN_KIND"
        self.assertTrue(validate_bundle(bundle))

    def test_candidate_state_is_not_auto_promoted(self):
        bundle = copy.deepcopy(self.fixture)
        self.assertTrue(all(x["state"] in {"CANDIDATE", "UNRESOLVED"} for x in bundle["records"]))


if __name__ == "__main__":
    unittest.main()
