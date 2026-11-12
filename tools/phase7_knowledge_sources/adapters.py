"""Rights-aware, non-mutating adapters for external lexical candidates and USG-SEM documents."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker
from tools.phase7_knowledge_contract.validate import validate_bundle
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.usg_external_lexical_v0_1_0.adapter import adapt_candidate_package, validate_candidate_package

ROOT = Path(__file__).resolve().parents[2]
LEXICAL_SCHEMA = ROOT / "specifications/usg-lexical-candidates-0.1.0.schema.json"

class KnowledgeSourceAdapterError(ValueError):
    """Source input cannot be adapted under the Phase 7 safety contract."""

def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(raw.encode("utf-8")).hexdigest()

def _id(prefix: str, *parts: Any) -> str:
    return prefix + ":" + sha256("\0".join(map(str, parts)).encode("utf-8")).hexdigest()[:32]

def _timestamp(value: str) -> str:
    if not isinstance(value, str) or "T" not in value:
        raise KnowledgeSourceAdapterError("retrieved_at must be an explicit ISO-8601 date-time")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise KnowledgeSourceAdapterError("retrieved_at must be an ISO-8601 date-time") from exc
    return value

def _rights(provider: str, metadata: dict, overrides: dict | None) -> dict:
    override = (overrides or {}).get(provider, {})
    status = override.get("rights_status", "UNKNOWN")
    redistribution = override.get("redistribution", "UNKNOWN")
    if status not in {"KNOWN_PERMITTED", "RESTRICTED", "UNKNOWN", "PROHIBITED", "INTERNAL"}:
        raise KnowledgeSourceAdapterError(f"invalid rights status for {provider}")
    if redistribution not in {"ALLOWED", "RESTRICTED", "UNKNOWN", "PROHIBITED", "NOT_APPLICABLE"}:
        raise KnowledgeSourceAdapterError(f"invalid redistribution status for {provider}")
    if redistribution == "ALLOWED" and status == "KNOWN_PERMITTED" and not override.get("license_id"):
        raise KnowledgeSourceAdapterError(f"{provider}: an explicit license_id is required for KNOWN_PERMITTED redistribution")
    if redistribution == "ALLOWED" and status not in {"KNOWN_PERMITTED", "INTERNAL"}:
        raise KnowledgeSourceAdapterError(f"{provider}: ALLOWED redistribution requires explicit known-permitted rights")
    attribution = override.get("attribution") or metadata.get("attribution") or provider
    if not isinstance(attribution, str) or not attribution.strip():
        raise KnowledgeSourceAdapterError(f"{provider}: attribution is required")
    return {
        "rights_status": status, "redistribution": redistribution,
        "license_id": override.get("license_id") or metadata.get("license"),
        "attribution": attribution,
        "retain_text": status in {"KNOWN_PERMITTED", "INTERNAL"} and redistribution == "ALLOWED",
    }

def _check_bundle(bundle: dict) -> dict:
    errors = validate_bundle(bundle)
    if errors:
        raise KnowledgeSourceAdapterError("adapted knowledge bundle is invalid: " + "; ".join(errors))
    return bundle

def adapt_lexical_candidate_package(
    package: dict, *, retrieved_at: str, rights_overrides: dict[str, dict[str, str]] | None = None
) -> dict:
    """Convert external candidates; definition text is withheld unless rights are explicitly cleared."""
    retrieved_at = _timestamp(retrieved_at)
    schema = json.loads(LEXICAL_SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(package))
    if errors:
        raise KnowledgeSourceAdapterError("lexical package schema failure: " + "; ".join(x.message for x in errors[:4]))
    check = validate_candidate_package(package)
    if check["status"] != "valid":
        raise KnowledgeSourceAdapterError("invalid candidate package: " + ", ".join(x["code"] for x in check["findings"]))
    adapted = adapt_candidate_package(package)
    metadata = {x["provider"]: x for x in package.get("source_provenance", []) if isinstance(x, dict) and x.get("provider")}
    providers = {x["source_provider"] for x in adapted["candidates"]}
    extras = set(rights_overrides or {}) - providers
    if extras:
        raise KnowledgeSourceAdapterError("rights override for unknown provider(s): " + ", ".join(sorted(extras)))

    sources, source_ids, rights_by_provider = [], {}, {}
    for provider in sorted(providers):
        meta = metadata.get(provider, {"provider": provider})
        rights = _rights(provider, meta, rights_overrides)
        rights_by_provider[provider] = rights
        locator = meta.get("record_url") or meta.get("provider_url")
        if not locator and meta.get("record_urls"):
            locator = meta["record_urls"][0]
        sid = _id("source", provider, locator or "", rights["license_id"] or "")
        source_ids[provider] = sid
        sources.append({
            "id": sid, "provider": provider, "source_type": "LEXICAL_DATABASE",
            "source_locator": locator, "retrieved_at": retrieved_at,
            "license_id": rights["license_id"], "rights_status": rights["rights_status"],
            "redistribution": rights["redistribution"], "attribution": rights["attribution"],
            "content_digest": None, "adapter_id": "usg-phase7-lexical-candidate-adapter",
            "adapter_version": "0.1.0",
        })

    records, evidence, contexts = [], [], {}
    lemma_ids, form_ids = {}, set()
    for candidate in adapted["candidates"]:
        provider = candidate["source_provider"]
        rights = rights_by_provider[provider]
        sid = source_ids[provider]
        language, lemma = candidate["language"], candidate["lemma"]
        pos = candidate.get("part_of_speech") or "UNSPECIFIED"
        context_id = _id("context", "language", language)
        contexts.setdefault(context_id, {
            "id": context_id, "context_type": "LANGUAGE", "value": language,
            "language_profile": language,
        })
        lemma_key = (language, lemma, pos)
        lemma_id = lemma_ids.get(lemma_key)
        if lemma_id is None:
            lemma_id = _id("lemma", *lemma_key)
            lemma_ids[lemma_key] = lemma_id
            records.append({
                "id": lemma_id, "kind": "LEMMA", "version": 1, "state": "CANDIDATE",
                "created_at": retrieved_at, "source_ids": [sid], "evidence_ids": [],
                "context_ids": [context_id],
                "payload": {"lemma": lemma, "language": language, "part_of_speech": pos},
            })
        sense_id = _id("sense", provider, candidate["source_id"], candidate["source_entry_id"],
                       candidate.get("source_sense_id") or candidate["candidate_id"])
        evidence_id = _id("evidence", sense_id, package["content_digest"])
        definition = candidate.get("definition") if rights["retain_text"] else None
        evidence.append({
            "id": evidence_id, "source_id": sid,
            "evidence_type": "DEFINITION" if definition else "OTHER",
            "support_status": "UNASSESSED",
            "locator": f"{candidate['source_id']}#{candidate['source_entry_id']}#{candidate.get('source_sense_id') or ''}",
            "text_digest": sha256(definition.encode("utf-8")).hexdigest() if definition else None,
            "captured_at": retrieved_at, "transformation_ids": [],
            "notes": "External candidate evidence; not independent corroboration. " +
                     ("Text retained under explicit rights policy." if definition else "Definition withheld: redistribution rights are not explicitly cleared."),
        })
        records.append({
            "id": sense_id, "kind": "LEXICAL_SENSE", "version": 1, "state": "CANDIDATE",
            "created_at": retrieved_at, "source_ids": [sid], "evidence_ids": [evidence_id],
            "context_ids": [context_id],
            "payload": {
                "lemma_record_id": lemma_id, "language": language, "definition": definition,
                "sense_source_id": candidate.get("source_sense_id") or candidate["candidate_id"],
                "source_candidate_id": candidate["candidate_id"], "definition_withheld": not bool(definition),
                "part_of_speech": pos,
            },
        })
        forms = [package["queried_form"]]
        if rights["retain_text"]:
            forms.extend(x["form"] for x in candidate.get("observed_forms", [])
                         if isinstance(x, dict) and isinstance(x.get("form"), str))
        for form in forms:
            fid = _id("lexform", language, form)
            if fid in form_ids:
                continue
            form_ids.add(fid)
            records.append({
                "id": fid, "kind": "LEXICAL_FORM", "version": 1, "state": "CANDIDATE",
                "created_at": retrieved_at, "source_ids": [sid], "evidence_ids": [evidence_id],
                "context_ids": [context_id],
                "payload": {"form": form, "language": language,
                            "script": "Latn" if language.startswith("en") else ("Arab" if language.startswith("ar") else "Zyyy")},
            })
    bundle = {
        "contract": "USG-KNOWLEDGE/0.1.0", "namespace": "urn:usg:external-lexical-candidates",
        "bundle_id": _id("lexical-bundle", package["queried_form"].casefold()),
        "created_at": retrieved_at, "records": records, "sources": sources,
        "evidence": evidence, "contexts": list(contexts.values()), "mappings": [], "relations": [],
        "extensions": {"source_contract": package["contract"], "source_package_digest": package["content_digest"],
                       "candidate_only": True, "promotion_allowed": False,
                       "source_disagreements_preserved": True, "rights_policy_applied": rights_overrides or {}},
    }
    _check_bundle(bundle)
    return {
        "bundle": bundle, "candidate_count": len(adapted["candidates"]),
        "retained_definition_count": sum(x["kind"] == "LEXICAL_SENSE" and bool(x["payload"]["definition"]) for x in records),
        "withheld_definition_count": sum(x["kind"] == "LEXICAL_SENSE" and x["payload"]["definition_withheld"] for x in records),
        "promotion_allowed": False,
    }

def adapt_canonical_document(document: dict) -> dict:
    """Project validated USG-SEM definitions; source text and truth claims are not imported."""
    if not isinstance(document, dict) or document.get("profileId") != "USG-SEM/1.0":
        raise KnowledgeSourceAdapterError("input must be a USG-SEM/1.0 document")
    if document.get("validation", {}).get("structuralStatus") != "PASS":
        raise KnowledgeSourceAdapterError("document must declare structuralStatus PASS")
    try:
        with CanonicalDocumentStore(":memory:") as validator:
            stored = validator.put_document(deepcopy(document))
    except Exception as exc:
        raise KnowledgeSourceAdapterError(f"canonical document validation failed: {exc}") from exc
    definitions, doc_id, created_at = document["definitions"], document["documentId"], document["createdAt"]
    digest = stored.digest
    source_map, sources = {}, []
    for src in document.get("sources", []):
        sid = _id("source", doc_id, src["id"])
        source_map[src["id"]] = sid
        sources.append({
            "id": sid, "provider": "USG-SEM/1.0 canonical document", "source_type": "USG_DOCUMENT",
            "source_locator": f"{doc_id}#source:{src['id']}", "retrieved_at": created_at,
            "license_id": None, "rights_status": "INTERNAL", "redistribution": "NOT_APPLICABLE",
            "attribution": f"Internal canonical document {doc_id}; original source text is not copied.",
            "content_digest": digest, "adapter_id": "usg-phase7-canonical-document-adapter",
            "adapter_version": "0.1.0",
        })
    if not sources:
        raise KnowledgeSourceAdapterError("canonical document has no source records")
    primary = document.get("primarySourceRef")
    source_id = source_map.get(primary, sources[0]["id"])
    language = next((s.get("language") for s in document["sources"] if s.get("id") == primary and isinstance(s.get("language"), str)), "und")
    context_id = _id("context", "language", language)
    contexts = [{"id": context_id, "context_type": "LANGUAGE", "value": language, "language_profile": language}]
    records, evidence = [], []
    def add_record(kind, key, version, payload, locator, snippet):
        rid = _id(kind.lower().replace("_", "-"), doc_id, key, version)
        eid = _id("evidence", doc_id, rid, digest)
        evidence.append({
            "id": eid, "source_id": source_id, "evidence_type": "CANONICAL_DOCUMENT",
            "support_status": "UNASSESSED", "locator": locator, "text_digest": _hash(snippet),
            "captured_at": created_at, "transformation_ids": [],
            "notes": "USG-SEM/1.0 structural conformance only; no truth or entailment claim.",
        })
        records.append({
            "id": rid, "kind": kind, "version": int(version), "state": "VALIDATED_FOR_PROFILE",
            "created_at": created_at, "source_ids": [source_id], "evidence_ids": [eid],
            "context_ids": [context_id], "payload": payload,
        })
    for concept in definitions.get("concepts", []):
        add_record("CONCEPT", concept["id"], concept.get("version", 1), {
            "concept_type": concept.get("semanticKind", "UNSPECIFIED"),
            "namespace": definitions.get("ontologyRelease") or "USG-SEM/1.0",
            "label": concept["label"], "definition": concept.get("definition"),
            "source_concept_id": concept["id"], "validation_scope": "USG-SEM/1.0 structural conformance",
        }, f"{doc_id}#/definitions/concepts/{concept['id']}", concept)
    for frame in definitions.get("frames", []):
        add_record("PREDICATE_FRAME", frame["id"], frame.get("version", 1), {
            "frame_key": frame["id"], "version": int(frame.get("version", 1)),
            "roles": list(frame.get("roles", [])), "label": frame["label"],
            "semantic_kind": frame.get("semanticKind"),
        }, f"{doc_id}#/definitions/frames/{frame['id']}", frame)
    for kind in sorted({x.get("semanticKind") for x in definitions.get("concepts", []) if x.get("semanticKind")}):
        add_record("SEMANTIC_CLASS", kind, 1, {
            "class_key": f"USG-SEM/1.0:{kind}",
            "definition": f"Semantic-kind category declared by USG-SEM/1.0: {kind}.",
        }, f"{doc_id}#/definitions/semanticKinds/{kind}", {"semanticKind": kind})
    bundle = {
        "contract": "USG-KNOWLEDGE/0.1.0",
        "namespace": "urn:usg:sem:1.0:" + str(definitions.get("ontologyRelease") or "unversioned"),
        "bundle_id": _id("usg-sem-bundle", doc_id), "created_at": created_at,
        "records": records, "sources": sources, "evidence": evidence, "contexts": contexts,
        "mappings": [], "relations": [],
        "extensions": {"source_contract": "USG-SEM/1.0", "source_document_id": doc_id,
                       "source_document_digest": digest, "canonical_document_validation": "STRUCTURAL_PASS",
                       "role_definitions": deepcopy(definitions.get("roles", [])),
                       "relation_definitions": deepcopy(definitions.get("relations", [])),
                       "promotion_allowed": False},
    }
    _check_bundle(bundle)
    return {"bundle": bundle, "source_document_digest": digest, "record_count": len(records),
            "promotion_allowed": False}

def ingest_lexical_candidate_package(repository: SQLiteKnowledgeRepository, package: dict, *,
                                      retrieved_at: str, rights_overrides: dict | None = None):
    return repository.put_bundle(adapt_lexical_candidate_package(
        package, retrieved_at=retrieved_at, rights_overrides=rights_overrides)["bundle"])

def ingest_canonical_document(repository: SQLiteKnowledgeRepository, document: dict):
    return repository.put_bundle(adapt_canonical_document(document)["bundle"])

__all__ = ["KnowledgeSourceAdapterError", "adapt_lexical_candidate_package",
           "adapt_canonical_document", "ingest_lexical_candidate_package", "ingest_canonical_document"]
