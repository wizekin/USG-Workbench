"""Step 7.6 typed relation and source reconciliation acceptance tests."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.phase7_knowledge_relations import (
    RELATION_REGISTRY_VERSION, RelationValidationError, load_relation_registry,
    validate_relations, reconcile_relations,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "examples/phase7-knowledge-bundle-0.1.0.json").read_text(encoding="utf-8"))


def make_bundle():
    bundle = deepcopy(FIXTURE)
    concepts = [x for x in bundle["records"] if x["kind"] == "CONCEPT"]
    second = deepcopy(concepts[0])
    second["id"] = "concept:relation-target"
    second["payload"]["label"] = "relation-target"
    bundle["records"].append(second)
    source = bundle["sources"][0]
    evidence_ids = []
    for i, status in enumerate(("SUPPORTS", "CONTRADICTS", "SUPPORTS")):
        sid = f"src-relation-{i}"
        eid = f"ev-relation-{i}"
        bundle["sources"].append({
            "id": sid, "provider": "provider-a" if i == 0 else ("provider-b" if i == 1 else "provider-a"),
            "source_type": "DICTIONARY", "source_locator": None,
            "retrieved_at": "2026-11-12T12:00:00Z", "license_id": None,
            "rights_status": "UNKNOWN", "redistribution": "UNKNOWN",
            "attribution": "test fixture provider",
        })
        bundle["evidence"].append({
            "id": eid, "source_id": sid, "evidence_type": "RELATION_OBSERVATION",
            "support_status": status, "captured_at": "2026-11-12T12:00:00Z",
            "transformation_ids": [], "locator": f"test:{i}",
        })
        evidence_ids.append(eid)
    bundle["relations"] = [{
        "id": "relation:claim-a", "subject_record_id": concepts[0]["id"],
        "predicate": "RELATED_TO", "object_record_id": concepts[1]["id"],
        "direction": "DIRECTED", "state": "CANDIDATE",
        "evidence_ids": evidence_ids, "context_ids": [],
        "relation_registry_version": RELATION_REGISTRY_VERSION,
    }]
    return bundle


class Phase7TypedRelationTests(unittest.TestCase):
    def test_registry_is_versioned_and_disallows_implicit_inference(self):
        registry = load_relation_registry()
        self.assertEqual(registry["contract"], "USG-KNOWLEDGE-RELATIONS/0.1.0")
        self.assertTrue(all(not x["symmetric"] and not x["transitive"] and
                            not x["causal"] and not x["inference_allowed"] and
                            x["inverse_of"] is None for x in registry["relation_types"]))

    def test_valid_directed_relation_passes_domain_and_range(self):
        bundle = make_bundle()
        self.assertEqual(validate_relations(bundle), [])

    def test_unknown_predicate_is_rejected(self):
        bundle = make_bundle()
        bundle["relations"][0]["predicate"] = "CAUSES"
        self.assertTrue(any("unknown predicate" in x for x in validate_relations(bundle)))

    def test_domain_and_range_mismatch_is_rejected(self):
        bundle = make_bundle()
        bundle["relations"][0]["predicate"] = "SUBCLASS_OF"
        self.assertTrue(any("subject kind" in x for x in validate_relations(bundle)))
        self.assertTrue(any("object kind" in x for x in validate_relations(bundle)))

    def test_wrong_registry_version_is_rejected(self):
        bundle = make_bundle()
        bundle["relations"][0]["relation_registry_version"] = "future"
        self.assertTrue(any("relation_registry_version" in x for x in validate_relations(bundle)))

    def test_support_and_contradiction_are_both_preserved(self):
        report = reconcile_relations(make_bundle())
        claim = report["claims"][0]
        self.assertEqual(claim["disposition"], "CONFLICT")
        self.assertEqual(claim["supporting_providers"], ["provider-a"])
        self.assertEqual(claim["contradicting_providers"], ["provider-b"])
        self.assertEqual(claim["independent_provider_count"], 2)
        self.assertFalse(claim["winner_selected"])

    def test_duplicate_evidence_from_one_provider_does_not_count_as_independent(self):
        report = reconcile_relations(make_bundle())
        self.assertEqual(report["claims"][0]["supporting_providers"].count("provider-a"), 1)
        self.assertEqual(report["claims"][0]["independent_provider_count"], 2)

    def test_reconciliation_never_performs_relation_closure_or_voting(self):
        report = reconcile_relations(make_bundle())
        for field in ("inference_performed", "inverse_closure_performed",
                      "transitive_closure_performed", "causal_inference_performed",
                      "source_voting_performed"):
            self.assertFalse(report[field])

    def test_reconciliation_is_deterministic(self):
        first = reconcile_relations(make_bundle())
        second = reconcile_relations(make_bundle())
        self.assertEqual(first, second)

    def test_invalid_relation_cannot_be_reconciled(self):
        bundle = make_bundle()
        bundle["relations"][0]["evidence_ids"] = []
        with self.assertRaises(RelationValidationError):
            reconcile_relations(bundle)


if __name__ == "__main__":
    unittest.main()
