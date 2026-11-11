"""Transparent lexical analysis; all semantic classifications remain provisional."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any


def _id(*parts: str) -> str:
    return hashlib.sha256("\0".join(map(str, parts)).encode("utf-8")).hexdigest()[:24]


def _normal_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def classify_definition_pattern(definition: str) -> dict[str, Any]:
    """Recognize a small set of visible definition forms; never assert an ontology fact."""
    text = definition.strip()
    patterns = [
        ("person_who", re.compile(r"^(?:a|an|the)\s+(?:person|someone|somebody|individual|one)\s+who\b", re.I), "person"),
        ("act_or_process_of", re.compile(r"^(?:the\s+)?(act|action|process|practice|state|condition|quality|ability|result|property|study)\s+of\b", re.I), None),
        ("kind_or_type_of", re.compile(r"^(?:a|an|the)\s+(?:type|kind|sort|form|class|category)\s+of\b", re.I), None),
        ("one_who", re.compile(r"^(?:a|an|the)\s+one\s+who\b", re.I), "person"),
    ]
    for pattern_type, expression, candidate in patterns:
        match = expression.search(text)
        if match:
            category = candidate or (match.group(1).lower() if pattern_type == "act_or_process_of" else None)
            return {
                "pattern_type": pattern_type,
                "category_candidate": category,
                "matched_prefix": match.group(0),
                "extraction_method": "deterministic_regex_v1",
                "heuristic_strength": "narrow_pattern_match",
                "validation_status": "unvalidated_observation",
            }
    nominal = re.match(r"^(?:a|an|the)\s+([^,.;]{2,100})", text, re.I)
    if nominal:
        candidate = nominal.group(1).strip()
        return {
            "pattern_type": "initial_nominal_phrase",
            "category_candidate": candidate,
            "matched_prefix": nominal.group(0),
            "extraction_method": "deterministic_regex_v1",
            "heuristic_strength": "broad_pattern_match",
            "validation_status": "unvalidated_observation",
        }
    return {
        "pattern_type": "unclassified_definition",
        "category_candidate": None,
        "matched_prefix": None,
        "extraction_method": "deterministic_regex_v1",
        "heuristic_strength": "none",
        "validation_status": "unvalidated_observation",
    }


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    entries = bundle.get("entries", [])
    sources = bundle.get("sources", [])
    if not isinstance(entries, list):
        return {"status": "invalid", "findings": [{"code": "entries_not_list", "severity": "error"}]}
    if not isinstance(sources, list) or not sources:
        findings.append({"code": "missing_source_provenance", "severity": "error"})
    elif any(not isinstance(source, dict) or not source.get("provider") for source in sources):
        findings.append({"code": "incomplete_source_provenance", "severity": "error"})
    seen_entries: set[str] = set()
    seen_senses: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            findings.append({"code": "entry_not_object", "severity": "error"})
            continue
        entry_id = entry.get("entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            findings.append({"code": "entry_missing_id", "severity": "error"})
        elif entry_id in seen_entries:
            findings.append({"code": "duplicate_entry_id", "severity": "error"})
        else:
            seen_entries.add(entry_id)
        if not entry.get("lemma"):
            findings.append({"code": "entry_missing_lemma", "severity": "error"})
        if not entry.get("part_of_speech"):
            findings.append({"code": "entry_missing_part_of_speech", "severity": "warning"})
        senses = entry.get("senses", [])
        if not isinstance(senses, list):
            findings.append({"code": "senses_not_list", "severity": "error"})
            continue
        for sense in senses:
            if not isinstance(sense, dict):
                findings.append({"code": "sense_not_object", "severity": "error"})
                continue
            sense_id = sense.get("sense_id")
            if not isinstance(sense_id, str) or not sense_id:
                findings.append({"code": "sense_missing_id", "severity": "error"})
            elif sense_id in seen_senses:
                findings.append({"code": "duplicate_sense_id", "severity": "error"})
            else:
                seen_senses.add(sense_id)
            if not isinstance(sense.get("definition"), str) or not sense["definition"].strip():
                findings.append({"code": "sense_missing_definition", "severity": "error"})
            if not isinstance(sense.get("relations", []), list):
                findings.append({"code": "sense_relations_not_list", "severity": "error"})
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for relation in entry.get("relations", []) or []:
            if not isinstance(relation, dict):
                findings.append({"code": "entry_relation_not_object", "severity": "error"})
                continue
            if relation.get("scope") == "sense":
                source_id = relation.get("source_sense_id")
                if source_id not in seen_senses:
                    findings.append({"code": "relation_source_sense_missing", "severity": "error"})
        for sense in entry.get("senses", []) or []:
            if not isinstance(sense, dict):
                continue
            for relation in sense.get("relations", []) or []:
                if not isinstance(relation, dict):
                    findings.append({"code": "sense_relation_not_object", "severity": "error"})
                    continue
                if relation.get("scope") != "sense" or relation.get("source_sense_id") != sense.get("sense_id"):
                    findings.append({"code": "sense_relation_scope_mismatch", "severity": "error"})
    errors = [item for item in findings if item["severity"] == "error"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    return {
        "status": "invalid" if errors else ("valid_with_warnings" if warnings else "valid"),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": findings,
        "promotion_allowed": False,
        "promotion_note": "Structural validity does not establish semantic correctness or authorize runtime promotion.",
    }


def build_semantic_candidate_graph(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a provenance-bearing graph from explicit source relations and observed forms."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for entry in entries:
        lemma = str(entry.get("lemma", ""))
        entry_id = str(entry.get("entry_id", ""))
        lemma_node = "lemma:" + _normal_text(lemma)
        nodes.setdefault(lemma_node, {"node_id": lemma_node, "node_type": "lemma_candidate", "label": lemma})
        nodes[entry_id] = {
            "node_id": entry_id,
            "node_type": "lexical_entry",
            "lemma_node": lemma_node,
            "provider": entry.get("provider"),
            "part_of_speech": entry.get("part_of_speech"),
        }
        edges.append({
            "edge_id": "edge-" + _id(entry_id, lemma_node, "entry_lemma"),
            "source": entry_id,
            "target": lemma_node,
            "type": "entry_has_lemma",
            "scope": "entry",
            "status": "structural_mapping",
        })
        for sense in entry.get("senses", []) or []:
            if not isinstance(sense, dict):
                continue
            sense_id = str(sense.get("sense_id", ""))
            if not sense_id:
                continue
            nodes[sense_id] = {
                "node_id": sense_id,
                "node_type": "lexical_sense_candidate",
                "entry_id": entry_id,
                "definition": sense.get("definition"),
                "part_of_speech": sense.get("part_of_speech") or entry.get("part_of_speech"),
                "provider": entry.get("provider"),
            }
            edges.append({
                "edge_id": "edge-" + _id(entry_id, sense_id, "entry_has_sense"),
                "source": entry_id,
                "target": sense_id,
                "type": "entry_has_sense",
                "scope": "entry",
                "status": "structural_mapping",
            })
            for relation in sense.get("relations", []) or []:
                target = relation.get("target_lemma")
                if not isinstance(target, str) or not target.strip():
                    continue
                target_node = "lemma:" + _normal_text(target)
                nodes.setdefault(target_node, {"node_id": target_node, "node_type": "lemma_candidate", "label": target})
                edges.append({
                    "edge_id": str(relation.get("relation_id") or ("edge-" + _id(sense_id, target, relation.get("type")))),
                    "source": sense_id,
                    "target": target_node,
                    "type": relation.get("type"),
                    "scope": "sense",
                    "status": relation.get("status", "source_asserted_unvalidated"),
                    "evidence": relation.get("evidence"),
                })
        for relation in entry.get("relations", []) or []:
            target = relation.get("target_lemma")
            if not isinstance(target, str) or not target.strip():
                continue
            target_node = "lemma:" + _normal_text(target)
            nodes.setdefault(target_node, {"node_id": target_node, "node_type": "lemma_candidate", "label": target})
            edges.append({
                "edge_id": str(relation.get("relation_id") or ("edge-" + _id(entry_id, target, relation.get("type")))),
                "source": entry_id,
                "target": target_node,
                "type": relation.get("type"),
                "scope": relation.get("scope", "entry"),
                "status": relation.get("status", "source_asserted_unvalidated"),
                "evidence": relation.get("evidence"),
            })
        for form in entry.get("forms", []) or []:
            if not isinstance(form, dict) or not isinstance(form.get("form"), str):
                continue
            form_label = form["form"]
            form_node = "form:" + _normal_text(form_label)
            nodes.setdefault(form_node, {"node_id": form_node, "node_type": "surface_form_candidate", "label": form_label})
            edges.append({
                "edge_id": "edge-" + _id(entry_id, form_label, "observed_form"),
                "source": entry_id,
                "target": form_node,
                "type": "observed_form",
                "scope": "entry",
                "tags": form.get("tags", []),
                "status": "source_asserted_unvalidated",
            })
    return {
        "graph_version": "usg-lexical-candidate-graph/0.1.0",
        "nodes": list(nodes.values()),
        "edges": edges,
        "interpretation_boundary": "Candidate graph only; edges preserve provider scope and do not establish synonymy, identity, entailment, or truth.",
    }


def analyze_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    validation = validate_bundle(bundle)
    pattern_observations: list[dict[str, Any]] = []
    morphology_observations: list[dict[str, Any]] = []
    definitions_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    entries = bundle.get("entries", []) if isinstance(bundle.get("entries"), list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        provider = str(entry.get("provider", "unknown"))
        lemma = str(entry.get("lemma", ""))
        pos = str(entry.get("part_of_speech") or "unspecified")
        for form in entry.get("forms", []) or []:
            if not isinstance(form, dict) or not isinstance(form.get("form"), str):
                continue
            tags = form.get("tags", []) if isinstance(form.get("tags"), list) else []
            tag_text = " ".join(str(tag).casefold() for tag in tags)
            if any(term in tag_text for term in ("plural", "past", "participle", "comparative", "superlative", "infinitive")):
                morphology_class = "tagged_inflection_or_form_variant"
            else:
                morphology_class = "observed_form_unclassified"
            morphology_observations.append({
                "observation_id": "morph-" + _id(provider, lemma, form["form"], tag_text),
                "provider": provider,
                "lemma": lemma,
                "form": form["form"],
                "tags": tags,
                "morphology_class": morphology_class,
                "validation_status": "source_observation_not_independent_morphological_analysis",
            })
        for sense in entry.get("senses", []) or []:
            if not isinstance(sense, dict):
                continue
            definition = sense.get("definition")
            if not isinstance(definition, str) or not definition.strip():
                continue
            pattern = classify_definition_pattern(definition)
            observation = {
                "observation_id": "pattern-" + _id(provider, sense.get("sense_id", ""), pattern["pattern_type"], definition),
                "provider": provider,
                "sense_id": sense.get("sense_id"),
                "source_record_id": entry.get("source_record_id"),
                "lemma": lemma,
                "part_of_speech": sense.get("part_of_speech") or pos,
                "definition_raw": definition,
                **pattern,
            }
            pattern_observations.append(observation)
            definitions_by_key.setdefault((lemma.casefold(), pos.casefold()), []).append({
                "provider": provider, "sense_id": sense.get("sense_id"), "definition": definition,
            })
    disagreements = []
    for (lemma, pos), records in definitions_by_key.items():
        providers = sorted({item["provider"] for item in records})
        if len(providers) > 1:
            normalized = {_normal_text(item["definition"]) for item in records}
            if len(normalized) > 1:
                disagreements.append({
                    "lemma": lemma,
                    "part_of_speech": pos,
                    "records": records,
                    "note": "Providers returned non-identical definitions. They remain separate; no source is selected as authoritative.",
                })
    return {
        "analysis_version": "usg-external-lexical-analysis/0.1.0",
        "validation": validation,
        "definition_pattern_observations": pattern_observations,
        "morphology_observations": morphology_observations,
        "semantic_candidate_graph": build_semantic_candidate_graph(entries),
        "cross_source_disagreements": disagreements,
        "promotion_policy": {
            "automatic_promotion": False,
            "reason": "External lexical records and deterministic pattern matches are observations. Only separately tested and explicitly approved mappings may become runtime lexical resources.",
        },
    }
