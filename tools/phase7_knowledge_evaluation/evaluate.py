"""Reproducible Phase 7 acceptance evaluator over frozen project-authored bilingual fixtures."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any

from tools.phase7_knowledge_contract.validate import validate_bundle
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.phase7_knowledge_repository.repository import canonical_bundle_bytes
from tools.phase7_knowledge_alignment.proposals import build_bilingual_alignment_bundle
from tools.phase7_knowledge_relations import RELATION_REGISTRY_VERSION, reconcile_relations
from tools.phase7_knowledge_retrieval import retrieve_candidates
from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "evaluations/phase7/phase7-acceptance-fixtures-0.1.0.json"
RESOURCE_PATH = ROOT / "resources/lexical/v0.3.0/en-ar-discourse-lexicon.json"
CREATED_AT = "2026-11-12T00:00:00Z"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _conflict_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Create one isolated contradictory provider fixture without changing the base bundle."""
    result = deepcopy(bundle)
    concepts = [item for item in result["records"] if item["kind"] == "CONCEPT"]
    if len(concepts) < 1:
        raise AssertionError("alignment fixture must contain a concept")
    second = deepcopy(concepts[0])
    second["id"] = "acceptance:concept:second"
    second["payload"] = {**second["payload"], "label": "acceptance second concept"}
    result["records"].append(second)
    base_source = deepcopy(result["sources"][0])
    base_evidence = deepcopy(result["evidence"][0])
    evidence_ids = []
    for index, (provider, status) in enumerate((("acceptance-provider-a", "SUPPORTS"),
                                                ("acceptance-provider-b", "CONTRADICTS"))):
        source = deepcopy(base_source)
        source.update({"id": f"acceptance:source:{index}", "provider": provider,
                       "source_type": "OTHER", "source_locator": f"fixture:{provider}",
                       "attribution": "Synthetic acceptance fixture"})
        result["sources"].append(source)
        evidence = deepcopy(base_evidence)
        evidence.update({"id": f"acceptance:evidence:{index}", "source_id": source["id"],
                         "support_status": status, "notes": "Synthetic conflict test only"})
        result["evidence"].append(evidence)
        evidence_ids.append(evidence["id"])
    result["relations"] = [{
        "id": "acceptance:relation:conflict",
        "subject_record_id": concepts[0]["id"], "predicate": "RELATED_TO",
        "object_record_id": second["id"], "direction": "DIRECTED", "state": "CANDIDATE",
        "evidence_ids": evidence_ids, "context_ids": [],
        "relation_registry_version": RELATION_REGISTRY_VERSION,
    }]
    return result


def run_evaluation() -> dict[str, Any]:
    started = time.perf_counter()
    fixture = _load(FIXTURE_PATH)
    resource = _load(RESOURCE_PATH)
    if fixture["resource"]["git_blob_sha"] != "a8fa4c60d4d14c0b488e5078c2d1a956e41f4577":
        raise AssertionError("frozen lexical resource Git blob changed; create a new evaluation fixture version")
    if resource["resource_id"] != fixture["resource"]["resource_id"] or resource["version"] != fixture["resource"]["version"]:
        raise AssertionError("evaluation resource identity/version mismatch")
    created = build_bilingual_alignment_bundle(resource, created_at=CREATED_AT)
    replay = build_bilingual_alignment_bundle(resource, created_at=CREATED_AT)
    if canonical_bundle_bytes(created) != canonical_bundle_bytes(replay):
        raise AssertionError("alignment bundle replay is not deterministic")
    bundle_digest = sha256(canonical_bundle_bytes(created)).hexdigest()
    validation_errors = validate_bundle(created)
    if validation_errors:
        raise AssertionError("alignment bundle failed validation: " + "; ".join(validation_errors))

    checks = []
    for case in fixture["positive_cases"]:
        result = retrieve_candidates([created], case["query"], language=case["language"],
                                     context_filters={"LANGUAGE": case["language"]})
        forms = [item for item in result["results"]
                 if item["record_kind"] == "LEXICAL_FORM" and item["payload"]["form"] == case["query"]]
        senses = sorted({item["payload"].get("sense_source_id") for item in result["results"]
                         if item["record_kind"] == "LEXICAL_SENSE"})
        expected_senses = sorted(case["expected_senses"])
        passed = len(forms) == 1 and senses == expected_senses
        checks.append({"case_id": case["case_id"], "kind": "POSITIVE_EXACT_FORM",
                       "language": case["language"], "passed": passed,
                       "actual_form_count": len(forms), "expected_sense_ids": expected_senses,
                       "actual_sense_ids": senses})
    for case in fixture["wrong_language_negative_cases"] + fixture["oov_negative_cases"]:
        result = retrieve_candidates([created], case["query"], language=case["language"])
        forms = [item for item in result["results"] if item["record_kind"] == "LEXICAL_FORM"]
        passed = not forms
        checks.append({"case_id": case["case_id"],
                       "kind": "WRONG_LANGUAGE_NEGATIVE" if case in fixture["wrong_language_negative_cases"] else "OOV_NEGATIVE",
                       "language": case["language"], "passed": passed, "actual_form_count": len(forms)})
    polysemy = []
    for case in fixture["polysemy_cases"]:
        result = retrieve_candidates([created], case["query"], language=case["language"])
        senses = sorted({item["payload"].get("sense_source_id") for item in result["results"]
                         if item["record_kind"] == "LEXICAL_SENSE"})
        polysemy.append({"language": case["language"], "query": case["query"],
                         "expected_senses": sorted(case["expected_senses"]),
                         "actual_senses": senses, "passed": senses == sorted(case["expected_senses"])})
    mapping_states = [item["state"] for item in created["mappings"]]
    mapping_safe = bool(mapping_states) and all(state == "UNRESOLVED" for state in mapping_states)
    source = created["sources"][0]
    provenance_safe = bool(source.get("provider") and source.get("attribution") and
                           source.get("content_digest") and source.get("source_locator"))
    rights_safe = (source.get("rights_status") == "INTERNAL" and
                   source.get("redistribution") == "NOT_APPLICABLE" and
                   all(record.get("state") in {"CANDIDATE", "UNRESOLVED"} for record in created["records"]))
    conflict_report = reconcile_relations(_conflict_bundle(created))
    conflict_claims = conflict_report["claims"]
    conflict_safe = (len(conflict_claims) == 1 and conflict_claims[0]["disposition"] == "CONFLICT"
                     and len(conflict_claims[0]["supporting_providers"]) == 1
                     and len(conflict_claims[0]["contradicting_providers"]) == 1
                     and not conflict_claims[0]["winner_selected"])
    store = CanonicalDocumentStore(":memory:")
    try:
        with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
            repository = SQLiteKnowledgeRepository(connection)
        with store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True):
            snapshot = repository.put_bundle(created)
        restored = repository.get_snapshot(snapshot.snapshot_id)
        round_trip_safe = restored is not None and restored.digest == bundle_digest
    finally:
        store.close()

    positive_count = len(fixture["positive_cases"])
    negative_count = len(fixture["wrong_language_negative_cases"]) + len(fixture["oov_negative_cases"])
    all_passed = (all(item["passed"] for item in checks) and all(item["passed"] for item in polysemy)
                  and mapping_safe and provenance_safe and rights_safe and conflict_safe
                  and round_trip_safe and bundle_digest == sha256(canonical_bundle_bytes(replay)).hexdigest())
    report = {
        "contract": "USG-PHASE7-ACCEPTANCE-REPORT/0.1.0",
        "fixture_version": fixture["fixture_version"],
        "resource": fixture["resource"],
        "status": "PASS" if all_passed else "FAIL",
        "scope": "Frozen project-authored English/MSA Arabic lexical retrieval, unresolved mapping, provider-conflict, provenance, and SQLite replay profile only.",
        "counts": {
            "positive_exact_form_cases": positive_count,
            "wrong_language_negative_cases": len(fixture["wrong_language_negative_cases"]),
            "oov_negative_cases": len(fixture["oov_negative_cases"]),
            "total_retrieval_cases": len(checks),
            "polysemy_cases": len(polysemy),
            "mapping_proposals": len(created["mappings"]),
            "unresolved_mapping_proposals": sum(state == "UNRESOLVED" for state in mapping_states),
        },
        "gates": {
            "retrieval_cases": all(item["passed"] for item in checks),
            "polysemy_preservation": all(item["passed"] for item in polysemy),
            "all_alignment_mappings_remain_unresolved": mapping_safe,
            "source_provenance_complete": provenance_safe,
            "rights_and_candidate_lifecycle_preserved": rights_safe,
            "provider_conflict_preserved_without_winner": conflict_safe,
            "sqlite_snapshot_round_trip_and_digest": round_trip_safe,
            "deterministic_alignment_replay": bundle_digest == sha256(canonical_bundle_bytes(replay)).hexdigest(),
            "false_merge_count": 0 if mapping_safe else None,
            "unsupported_promotion_count": 0 if rights_safe and mapping_safe else None,
        },
        "polysemy": polysemy,
        "retrieval_cases": checks,
        "conflict_report": conflict_report,
        "bundle_sha256": bundle_digest,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "limitations": [
            "The source is a bounded project-authored lexical resource, not a broad naturalistic corpus.",
            "Resource concept_ref values remain opaque grouping hints; every mapping stays UNRESOLVED.",
            "Exact-form retrieval does not establish broad morphology, unrestricted language understanding, or semantic truth.",
            "Provider conflict is exercised with a synthetic adversarial fixture, not independent real-world providers.",
            "External redistribution-rights policy remains covered by the dedicated rights-aware adapter test suite.",
            "Phase 7 does not claim general AGI, complete knowledge, or unrestricted semantic reasoning.",
        ],
    }
    if not all_passed:
        raise AssertionError("Phase 7 acceptance failed: " + json.dumps(report["gates"], sort_keys=True))
    return report


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON report destination")
    args = parser.parse_args(argv)
    report = run_evaluation()
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
