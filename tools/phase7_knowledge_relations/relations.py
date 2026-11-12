"""Typed relation registry, domain/range checks, and evidence-preserving reconciliation."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from tools.phase7_knowledge_contract.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "specifications" / "usg-knowledge-relation-registry-0.1.0.json"
RELATION_REGISTRY_VERSION = "usg-knowledge-relations/0.1.0"


class RelationValidationError(ValueError):
    """A relation is not permitted by the declared registry profile."""


def load_relation_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("contract") != "USG-KNOWLEDGE-RELATIONS/0.1.0":
        raise RelationValidationError("unsupported relation registry contract")
    entries = registry.get("relation_types")
    if not isinstance(entries, list) or not entries:
        raise RelationValidationError("relation registry must declare relation_types")
    names = [item.get("predicate") for item in entries]
    if len(names) != len(set(names)) or any(not isinstance(name, str) or not name for name in names):
        raise RelationValidationError("relation predicates must be unique non-empty strings")
    for item in entries:
        if item.get("symmetric") or item.get("transitive") or item.get("causal") or item.get("inference_allowed"):
            raise RelationValidationError("0.1.0 registry forbids implicit closure and inference")
        if item.get("inverse_of") is not None:
            raise RelationValidationError("inverse relations require a separate explicit rule contract")
        if not item.get("domain") or not item.get("range"):
            raise RelationValidationError(f"{item['predicate']}: domain and range are required")
    return registry


def validate_relations(bundle: dict[str, Any], registry: dict[str, Any] | None = None) -> list[str]:
    registry = registry or load_relation_registry()
    errors = validate_bundle(bundle)
    if errors:
        return errors
    entries = {item["predicate"]: item for item in registry["relation_types"]}
    records = {item["id"]: item for item in bundle["records"]}
    for relation in bundle["relations"]:
        predicate = relation["predicate"]
        spec = entries.get(predicate)
        if spec is None:
            errors.append(f"relation {relation['id']}: unknown predicate {predicate}")
            continue
        subject = records.get(relation["subject_record_id"])
        obj = records.get(relation["object_record_id"])
        if subject and subject["kind"] not in spec["domain"]:
            errors.append(f"relation {relation['id']}: subject kind {subject['kind']} is outside {predicate} domain")
        if obj and obj["kind"] not in spec["range"]:
            errors.append(f"relation {relation['id']}: object kind {obj['kind']} is outside {predicate} range")
        version = relation.get("relation_registry_version")
        if version != RELATION_REGISTRY_VERSION:
            errors.append(f"relation {relation['id']}: relation_registry_version must be {RELATION_REGISTRY_VERSION}")
    return sorted(errors)


def reconcile_relations(bundle: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Aggregate evidence by exact directed claim; retain provider disagreement without voting."""
    registry = registry or load_relation_registry()
    errors = validate_relations(bundle, registry)
    if errors:
        raise RelationValidationError("; ".join(errors))
    sources = {item["id"]: item for item in bundle["sources"]}
    evidence = {item["id"]: item for item in bundle["evidence"]}
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for relation in bundle["relations"]:
        key = (relation["subject_record_id"], relation["predicate"], relation["object_record_id"])
        grouped.setdefault(key, []).append(relation)
    claims = []
    for (subject, predicate, obj), relations in sorted(grouped.items()):
        evidence_ids = sorted({eid for relation in relations for eid in relation["evidence_ids"]})
        support, contradict, unassessed = set(), set(), set()
        evidence_rows = []
        for evidence_id in evidence_ids:
            item = evidence[evidence_id]
            provider = sources[item["source_id"]]["provider"]
            status = item["support_status"]
            target = support if status == "SUPPORTS" else contradict if status == "CONTRADICTS" else unassessed
            target.add(provider)
            evidence_rows.append({"evidence_id": evidence_id, "provider": provider, "support_status": status})
        if support and contradict:
            disposition = "CONFLICT"
        elif support:
            disposition = "SUPPORT_ONLY"
        elif contradict:
            disposition = "CONTRADICTION_ONLY"
        else:
            disposition = "UNASSESSED"
        claims.append({
            "subject_record_id": subject, "predicate": predicate, "object_record_id": obj,
            "relation_ids": sorted(item["id"] for item in relations),
            "evidence": evidence_rows,
            "supporting_providers": sorted(support), "contradicting_providers": sorted(contradict),
            "unassessed_providers": sorted(unassessed),
            "disposition": disposition,
            "independent_provider_count": len(support | contradict | unassessed),
            "winner_selected": False,
        })
    return {
        "contract": "USG-KNOWLEDGE-RECONCILIATION/0.1.0",
        "relation_registry_version": RELATION_REGISTRY_VERSION,
        "claims": claims,
        "inference_performed": False,
        "inverse_closure_performed": False,
        "transitive_closure_performed": False,
        "causal_inference_performed": False,
        "source_voting_performed": False,
    }
