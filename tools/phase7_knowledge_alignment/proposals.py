"""Deterministic bilingual alignment proposals with an explicit no-equivalence default.

The project lexical resource's concept_ref is treated as a grouping hint only.
Every generated sense-to-concept mapping remains UNRESOLVED until a later
evidence assessment and profile-specific acceptance policy.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from tools.phase7_knowledge_contract.validate import validate_bundle
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository


class AlignmentProposalError(ValueError):
    """A bilingual alignment resource is malformed or inconsistent."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _id(prefix: str, *parts: Any) -> str:
    return prefix + ":" + sha256("\0".join(map(str, parts)).encode("utf-8")).hexdigest()[:32]


def build_bilingual_alignment_bundle(resource: dict[str, Any], *, created_at: str) -> dict[str, Any]:
    """Create candidate lexical records and unresolved many-to-many sense/concept links."""
    if not isinstance(resource, dict) or not isinstance(resource.get("entries"), list):
        raise AlignmentProposalError("resource must contain an entries array")
    if not isinstance(created_at, str) or "T" not in created_at:
        raise AlignmentProposalError("created_at must be an explicit ISO-8601 date-time")
    try:
        datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AlignmentProposalError("created_at must be an ISO-8601 date-time") from exc
    resource_id = resource.get("resource_id")
    version = resource.get("version")
    provenance = resource.get("provenance")
    if not isinstance(resource_id, str) or not resource_id or not isinstance(version, str) or not version:
        raise AlignmentProposalError("resource_id and version are required")
    if not isinstance(provenance, str) or not provenance.strip():
        raise AlignmentProposalError("resource provenance is required")
    digest = sha256(_canonical(resource)).hexdigest()
    source_id = _id("source", resource_id, version, digest)
    source = {
        "id": source_id, "provider": resource_id, "source_type": "LEXICAL_DATABASE",
        "source_locator": f"repository-resource:{resource_id}@{version}", "retrieved_at": created_at,
        "license_id": None, "rights_status": "INTERNAL", "redistribution": "NOT_APPLICABLE",
        "attribution": provenance, "content_digest": digest,
        "adapter_id": "usg-phase7-bilingual-alignment-proposer", "adapter_version": "0.1.0",
    }
    resource_evidence_id = _id("evidence", resource_id, version, digest)
    evidence = [{
        "id": resource_evidence_id, "source_id": source_id, "evidence_type": "OTHER",
        "support_status": "UNASSESSED", "locator": f"repository-resource:{resource_id}@{version}",
        "text_digest": digest, "captured_at": created_at, "transformation_ids": [],
        "notes": "The resource concept_ref is a candidate grouping hint, not independent proof of equivalence or identity.",
    }]
    contexts: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    seen_senses: dict[str, dict[str, Any]] = {}
    lemmas: dict[tuple[str, str, str], str] = {}
    concepts: dict[str, str] = {}
    skipped = 0

    for entry in resource["entries"]:
        if not isinstance(entry, dict):
            raise AlignmentProposalError("every lexical resource entry must be an object")
        language = entry.get("language")
        if language not in {"en", "ar"}:
            skipped += 1
            continue
        required = ("form", "lemma", "part_of_speech", "sense_id", "concept_ref")
        if any(not isinstance(entry.get(key), str) or not entry[key] for key in required):
            skipped += 1
            continue
        sense_key = entry["sense_id"]
        signature = (language, entry["lemma"], entry["part_of_speech"], entry["concept_ref"])
        context_id = _id("context", "language", language)
        if sense_key in seen_senses:
            if seen_senses[sense_key] != signature:
                raise AlignmentProposalError(f"conflicting duplicate sense_id: {sense_key}")
            # Multiple forms/features may belong to one lexical sense. Preserve each
            # form and its evidence, but do not duplicate the sense or mapping.
            duplicate_evidence_id = _id("evidence", resource_id, version, sense_key, entry["form"], _id("entry", _canonical(entry).hex()))
            if any(item["id"] == duplicate_evidence_id for item in evidence):
                continue
            evidence.append({
                "id": duplicate_evidence_id, "source_id": source_id, "evidence_type": "OTHER",
                "support_status": "UNASSESSED",
                "locator": f"repository-resource:{resource_id}@{version}#sense:{sense_key}#form:{entry['form']}",
                "text_digest": sha256(_canonical(entry)).hexdigest(), "captured_at": created_at,
                "transformation_ids": [],
                "notes": "Additional surface-form observation for an existing lexical sense; not a separate sense.",
            })
            sense_record_id = _id("lexical-sense", resource_id, version, sense_key)
            sense_record = next(x for x in records if x["id"] == sense_record_id)
            sense_record["evidence_ids"].append(duplicate_evidence_id)
            mapping_record = next(x for x in mappings if x["source_record_id"] == sense_record_id)
            mapping_record["evidence_ids"].append(duplicate_evidence_id)
            form_id = _id("lexical-form", language, entry["form"])
            if not any(x["id"] == form_id for x in records):
                records.append({
                    "id": form_id, "kind": "LEXICAL_FORM", "version": 1, "state": "CANDIDATE",
                    "created_at": created_at, "source_ids": [source_id], "evidence_ids": [duplicate_evidence_id],
                    "context_ids": [context_id],
                    "payload": {"form": entry["form"], "language": language,
                                "script": "Latn" if language == "en" else "Arab",
                                "features": deepcopy(entry.get("features", {}))},
                })
            continue
        seen_senses[sense_key] = signature
        contexts.setdefault(context_id, {
            "id": context_id, "context_type": "LANGUAGE", "value": language,
            "language_profile": language,
        })
        lemma_key = (language, entry["lemma"], entry["part_of_speech"])
        lemma_id = lemmas.get(lemma_key)
        if lemma_id is None:
            lemma_id = _id("lemma", *lemma_key)
            lemmas[lemma_key] = lemma_id
            records.append({
                "id": lemma_id, "kind": "LEMMA", "version": 1, "state": "CANDIDATE",
                "created_at": created_at, "source_ids": [source_id], "evidence_ids": [],
                "context_ids": [context_id],
                "payload": {"lemma": entry["lemma"], "language": language,
                            "part_of_speech": entry["part_of_speech"]},
            })
        entry_evidence_id = _id("evidence", resource_id, version, sense_key)
        evidence.append({
            "id": entry_evidence_id, "source_id": source_id, "evidence_type": "OTHER",
            "support_status": "UNASSESSED",
            "locator": f"repository-resource:{resource_id}@{version}#sense:{sense_key}",
            "text_digest": sha256(_canonical(entry)).hexdigest(), "captured_at": created_at,
            "transformation_ids": [],
            "notes": "Project resource entry; its concept_ref is an unresolved alignment hint, not a validated translation.",
        })
        sense_id = _id("lexical-sense", resource_id, version, sense_key)
        records.append({
            "id": sense_id, "kind": "LEXICAL_SENSE", "version": 1, "state": "CANDIDATE",
            "created_at": created_at, "source_ids": [source_id], "evidence_ids": [entry_evidence_id],
            "context_ids": [context_id],
            "payload": {
                "lemma_record_id": lemma_id, "language": language, "definition": None,
                "sense_source_id": sense_key, "resource_concept_ref_hint": entry["concept_ref"],
                "definition_withheld": True,
            },
        })
        form_id = _id("lexical-form", language, entry["form"])
        if not any(x["id"] == form_id for x in records):
            records.append({
                "id": form_id, "kind": "LEXICAL_FORM", "version": 1, "state": "CANDIDATE",
                "created_at": created_at, "source_ids": [source_id], "evidence_ids": [entry_evidence_id],
                "context_ids": [context_id],
                "payload": {"form": entry["form"], "language": language,
                            "script": "Latn" if language == "en" else "Arab", "features": deepcopy(entry.get("features", {}))},
            })
        concept_ref = entry["concept_ref"]
        concept_id = concepts.get(concept_ref)
        if concept_id is None:
            concept_id = _id("concept", resource_id, version, concept_ref)
            concepts[concept_ref] = concept_id
            concept_evidence_id = _id("evidence", resource_id, version, "concept-ref", concept_ref)
            evidence.append({
                "id": concept_evidence_id, "source_id": source_id, "evidence_type": "OTHER",
                "support_status": "UNASSESSED",
                "locator": f"repository-resource:{resource_id}@{version}#concept_ref:{concept_ref}",
                "text_digest": sha256(concept_ref.encode("utf-8")).hexdigest(),
                "captured_at": created_at, "transformation_ids": [],
                "notes": "Opaque resource grouping key only; not a globally established concept identity.",
            })
            records.append({
                "id": concept_id, "kind": "CONCEPT", "version": 1, "state": "UNRESOLVED",
                "created_at": created_at, "source_ids": [source_id],
                "evidence_ids": [concept_evidence_id], "context_ids": [context_id],
                "payload": {
                    "concept_type": "UNRESOLVED", "namespace": f"{resource_id}@{version}",
                    "label": concept_ref, "identity_status": "UNRESOLVED",
                },
            })
        mapping_id = _id("mapping", sense_id, concept_id, digest)
        mappings.append({
            "id": mapping_id, "source_record_id": sense_id, "target_record_id": concept_id,
            "mapping_type": "UNRESOLVED", "state": "UNRESOLVED",
            "evidence_ids": [entry_evidence_id, resource_evidence_id],
            "context_ids": [context_id],
            "notes": "Candidate sense-to-concept alignment from a project resource hint only. Not equivalent, accepted, or identity evidence.",
        })

    bundle = {
        "contract": "USG-KNOWLEDGE/0.1.0", "namespace": f"urn:usg:alignment:{resource_id}:{version}",
        "bundle_id": _id("alignment-bundle", resource_id, version, digest),
        "created_at": created_at, "records": records, "sources": [source],
        "evidence": evidence, "contexts": list(contexts.values()),
        "mappings": mappings, "relations": [],
        "extensions": {
            "source_contract": "USG-LEXICAL-RESOURCE/PROJECT-AUTHORED",
            "source_resource_id": resource_id, "source_resource_version": version,
            "source_resource_digest": digest, "alignment_policy": "candidate-hint-only/0.1.0",
            "equivalence_inferred": False, "promotion_allowed": False,
            "skipped_entry_count": skipped,
        },
    }
    errors = validate_bundle(bundle)
    if errors:
        raise AlignmentProposalError("alignment bundle failed validation: " + "; ".join(errors))
    return bundle


def ingest_bilingual_alignment_bundle(repository: SQLiteKnowledgeRepository, resource: dict[str, Any], *,
                                      created_at: str):
    return repository.put_bundle(build_bilingual_alignment_bundle(resource, created_at=created_at))


__all__ = ["AlignmentProposalError", "build_bilingual_alignment_bundle",
           "ingest_bilingual_alignment_bundle"]
