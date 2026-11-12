"""Explainable candidate retrieval; ranking never implies truth or entailment."""
from __future__ import annotations
from typing import Any

RETRIEVAL_POLICY_VERSION = "usg-knowledge-retrieval/0.1.0"
_STATE_WEIGHT = {"ACCEPTED": 20, "VALIDATED_FOR_PROFILE": 15, "CANDIDATE": 5, "UNRESOLVED": 0,
                 "DEPRECATED": -5, "REJECTED": -20}


class RetrievalError(ValueError):
    """Invalid retrieval request or malformed knowledge bundle."""


def _norm(value: Any) -> str:
    return " ".join(str(value).casefold().split())


def retrieve_candidates(
    bundles: list[dict[str, Any]], query: str, *, language: str | None = None,
    context_filters: dict[str, str] | None = None, include_states: tuple[str, ...] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Find exact lexical/lemma matches and their explicitly linked senses/mappings.

    Context filters are exact typed filters. Scores are deterministic ranking units,
    not probabilities, confidence, truth, or semantic correctness.
    """
    needle = _norm(query)
    if not needle:
        raise RetrievalError("query must contain non-whitespace text")
    if limit < 1 or limit > 500:
        raise RetrievalError("limit must be between 1 and 500")
    filters = {_norm(k).upper(): _norm(v) for k, v in (context_filters or {}).items()}
    allowed = set(include_states or _STATE_WEIGHT)
    results: dict[str, dict[str, Any]] = {}

    for bundle in bundles:
        if bundle.get("contract") != "USG-KNOWLEDGE/0.1.0":
            raise RetrievalError("all bundles must use USG-KNOWLEDGE/0.1.0")
        records = {r["id"]: r for r in bundle.get("records", [])}
        contexts = {c["id"]: c for c in bundle.get("contexts", [])}
        mappings = bundle.get("mappings", [])
        relations = bundle.get("relations", [])
        evidence_by_record = {r["id"]: list(r.get("evidence_ids", [])) for r in records.values()}
        direct_matches: dict[str, tuple[int, str]] = {}

        for record in records.values():
            if record.get("state") not in allowed:
                continue
            payload = record.get("payload", {})
            kind = record.get("kind")
            match_score = 0
            match_reason = ""
            if kind == "LEXICAL_FORM" and _norm(payload.get("form", "")) == needle:
                match_score, match_reason = 100, "exact lexical-form match"
            elif kind == "LEMMA" and _norm(payload.get("lemma", "")) == needle:
                match_score, match_reason = 95, "exact lemma match"
            if match_score:
                direct_matches[record["id"]] = (match_score, match_reason)

        matched_lemmas = {rid for rid in direct_matches if records[rid]["kind"] == "LEMMA"}
        for record in records.values():
            if record.get("kind") == "LEXICAL_SENSE" and record.get("state") in allowed:
                if record.get("payload", {}).get("lemma_record_id") in matched_lemmas:
                    direct_matches[record["id"]] = (90, "sense linked to exact matched lemma")

        # Forms that are exactly the lemma spelling can reach senses through the
        # language-scoped lemma object; no fuzzy or translation-based link is made.
        for rid, (score, reason) in list(direct_matches.items()):
            if records[rid]["kind"] == "LEXICAL_FORM":
                p = records[rid]["payload"]
                for lemma in records.values():
                    lp = lemma.get("payload", {})
                    if (lemma["kind"] == "LEMMA" and _norm(lp.get("lemma", "")) == needle
                            and lp.get("language") == p.get("language") and lemma["state"] in allowed):
                        direct_matches.setdefault(lemma["id"], (95, "surface form equals language-scoped lemma"))
                        for sense in records.values():
                            if (sense["kind"] == "LEXICAL_SENSE"
                                    and sense["payload"].get("lemma_record_id") == lemma["id"]
                                    and sense["state"] in allowed):
                                direct_matches.setdefault(sense["id"], (90, "sense linked to exact matched lemma"))

        linked: dict[str, tuple[int, str]] = dict(direct_matches)
        matched_senses = {rid for rid in direct_matches if records[rid]["kind"] == "LEXICAL_SENSE"}
        for mapping in mappings:
            if mapping.get("source_record_id") in matched_senses:
                target = mapping.get("target_record_id")
                if target in records and records[target]["state"] in allowed:
                    linked.setdefault(target, (80, "explicit sense-to-concept mapping candidate"))
        matched_concepts = {rid for rid in linked if records[rid]["kind"] == "CONCEPT"}
        for relation in relations:
            if relation.get("subject_record_id") in matched_concepts:
                target = relation.get("object_record_id")
                if target in records and records[target]["state"] in allowed:
                    linked.setdefault(target, (70, "explicit outgoing typed relation"))
            if relation.get("object_record_id") in matched_concepts:
                target = relation.get("subject_record_id")
                if target in records and records[target]["state"] in allowed:
                    linked.setdefault(target, (70, "explicit incoming typed relation"))

        for rid, (base, reason) in linked.items():
            record = records[rid]
            if language and record.get("payload", {}).get("language") not in (None, language):
                continue
            record_contexts = [contexts[cid] for cid in record.get("context_ids", []) if cid in contexts]
            if any(not any(_norm(c.get("context_type")) == key and _norm(c.get("value")) == value
                           for c in record_contexts) for key, value in filters.items()):
                continue
            score = base + _STATE_WEIGHT.get(record.get("state"), 0)
            explanations = [reason]
            if language and record.get("payload", {}).get("language") == language:
                score += 10
                explanations.append("language profile matched")
            for key, value in filters.items():
                if any(_norm(c.get("context_type")) == key and _norm(c.get("value")) == value
                       for c in record_contexts):
                    score += 10
                    explanations.append(f"context matched: {key}={value}")
            current = results.get(rid)
            candidate = {
                "record_id": rid, "record_kind": record["kind"], "state": record["state"],
                "bundle_id": bundle.get("bundle_id"), "bundle_namespace": bundle.get("namespace"),
                "score": score, "priority_band": "PRIMARY" if record["state"] in {"ACCEPTED", "VALIDATED_FOR_PROFILE"} else "SECONDARY",
                "explanation": explanations, "evidence_ids": sorted(evidence_by_record[rid]),
                "context_ids": sorted(record.get("context_ids", [])),
                "payload": record["payload"],
            }
            if current is None or (candidate["score"], candidate["record_id"]) > (current["score"], current["record_id"]):
                results[rid] = candidate

    ordered = sorted(results.values(), key=lambda x: (-x["score"], x["record_id"]))[:limit]
    top_score = ordered[0]["score"] if ordered else None
    top_ties = [item["record_id"] for item in ordered if item["score"] == top_score] if top_score is not None else []
    for item in ordered:
        item["tied_for_top_rank"] = item["record_id"] in top_ties and len(top_ties) > 1
    return {
        "contract": "USG-KNOWLEDGE-RETRIEVAL/0.1.0",
        "policy_version": RETRIEVAL_POLICY_VERSION,
        "query": query, "language_filter": language, "context_filters": dict(context_filters or {}),
        "ranking_score_is_probability": False, "ranking_score_is_truth": False,
        "inference_performed": False, "fuzzy_matching_performed": False,
        "ambiguous_top_rank": len(top_ties) > 1,
        "top_tie_record_ids": top_ties,
        "result_count": len(ordered), "results": ordered,
    }
