"""Unified bilingual Phase 6 candidate interpretation over the Phase 5 pipeline.

This is an integrated candidate interpreter, not a claim of unrestricted parsing.
It reuses the versioned Phase 5 lexical, segmentation, syntax, operator and
discourse stages, then adds the Phase 6 candidate graph and strict-template
fallback. Every emitted span is checked against the original source.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

from tools.usg_interpretation_v0_2_0 import (
    Phase5InterpretationService, bundled_resource_descriptors,
)
from .engine import compose, project_loss_aware, CompositionError
from .extract import extract_candidate_graph

VERSION = "usg-phase6-integrated-interpreter/0.1.0"


def _stable(prefix: str, value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), default=str).encode("utf-8")
    return prefix + "_" + sha256(raw).hexdigest()[:20]


def _manifest_digest() -> str:
    descriptors = [
        {name: getattr(item, name) for name in item.__dataclass_fields__}
        for item in bundled_resource_descriptors()
    ]
    raw = json.dumps(descriptors, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def _source_span(source: str, start: int, end: int) -> dict:
    if type(start) is not int or type(end) is not int or start < 0 or end <= start or end > len(source):
        raise CompositionError("integrated Phase 6 stage returned an invalid source span")
    return {"start": start, "end": end, "surface": source[start:end]}


def _token_span(source: str, token: dict) -> dict:
    return _source_span(source, token["start"], token["end"])


def _merge_template_graph(base: dict, template: dict) -> None:
    """Append a closed-template graph without colliding with Phase 5 IDs."""
    id_map = {node["id"]: _stable("template", node["id"]) for node in template["nodes"]}
    for node in template["nodes"]:
        item = deepcopy(node)
        item["id"] = id_map[node["id"]]
        item["origin"] = "PHASE6_CLOSED_TEMPLATE"
        base["nodes"].append(item)
    for edge in template.get("relations", []):
        item = deepcopy(edge)
        item["source"] = id_map[item["source"]]
        item["target"] = id_map[item["target"]]
        base["relations"].append(item)
    for clause in template.get("clauses", []):
        item = deepcopy(clause)
        item["id"] = id_map.get(item["id"], _stable("template_clause", item["id"]))
        if item.get("parent_id"):
            item["parent_id"] = id_map.get(item["parent_id"], _stable("template_clause", item["parent_id"]))
        base["clauses"].append(item)
    for operator in template.get("operators", []):
        item = deepcopy(operator)
        item["target_id"] = id_map[item["target_id"]]
        base["operators"].append(item)
    for reference in template.get("references", []):
        item = deepcopy(reference)
        item["mention_id"] = id_map[item["mention_id"]]
        item["antecedent_candidates"] = [id_map[value] for value in item.get("antecedent_candidates", [])]
        base["references"].append(item)
    base["features"].extend(template.get("features", []))
    base["provenance"].extend(template.get("provenance", []))
    if template.get("voice") not in (None, "UNKNOWN"):
        base["voice"] = template["voice"]
    if template.get("speech_act") not in (None, "UNKNOWN"):
        base["speech_act"] = template["speech_act"]


def _phase5_graph(source: str, phase5: dict) -> tuple[dict, list[str]]:
    graph = {
        "nodes": [], "relations": [], "clauses": [], "operators": [],
        "references": [], "features": [], "speech_act": "UNKNOWN",
        "voice": "UNKNOWN", "provenance": [],
    }
    diagnostics: list[str] = []
    stages = phase5.get("stages", {})
    lexical = stages.get("lexical", {}).get("artifact", {})
    syntax = stages.get("syntax", {}).get("artifact", {})
    segmentation = stages.get("segmentation", {}).get("artifact", {})
    operators = stages.get("operators", {}).get("artifact", {})
    discourse = stages.get("discourse", {}).get("artifact", {})
    tokens = {
        item["token"]["token_id"]: item["token"]
        for item in lexical.get("tokens", [])
        if isinstance(item, dict) and isinstance(item.get("token"), dict)
    }
    clause_roots: dict[str, list[str]] = {}
    token_nodes: dict[str, list[str]] = {}

    def add_node(node_id: str, kind: str, token: dict, *, role: str,
                 candidate_id: str | None = None, construction_id: str | None = None) -> str:
        if node_id not in {item["id"] for item in graph["nodes"]}:
            node = {
                "id": node_id, "kind": kind, "role": role,
                "span": _token_span(source, token),
                "origin": "PHASE5_PIPELINE",
            }
            if candidate_id:
                node["candidate_id"] = candidate_id
            if construction_id:
                node["construction_id"] = construction_id
            graph["nodes"].append(node)
        token_nodes.setdefault(token["token_id"], []).append(node_id)
        return node_id

    for clause in syntax.get("clauses", []):
        clause_ref = clause.get("clause_ref")
        for candidate in clause.get("candidates", []):
            role_refs = dict(candidate.get("role_token_refs", []))
            construction_id = candidate.get("construction_id")
            candidate_id = candidate.get("candidate_id")
            if not {"AGENT", "ACTION", "PATIENT"}.issubset(role_refs):
                diagnostics.append("PHASE5_SYNTAX_CANDIDATE_MISSING_CORE_ROLE")
                continue
            role_nodes = {}
            for role in ("AGENT", "ACTION", "PATIENT"):
                token = tokens.get(role_refs[role])
                if token is None:
                    diagnostics.append("PHASE5_SYNTAX_REFERENCES_MISSING_TOKEN")
                    role_nodes = {}
                    break
                node_id = _stable("p6n", [candidate_id, role, role_refs[role]])
                kind = "EVENT" if role == "ACTION" else "ENTITY"
                role_nodes[role] = add_node(
                    node_id, kind, token, role=role,
                    candidate_id=candidate_id, construction_id=construction_id,
                )
            if not role_nodes:
                continue
            predicate_id = role_nodes["ACTION"]
            clause_roots.setdefault(clause_ref, []).append(predicate_id)
            for role in ("AGENT", "PATIENT"):
                token = tokens[role_refs[role]]
                graph["relations"].append({
                    "type": role, "source": predicate_id,
                    "target": role_nodes[role],
                    "evidence": _token_span(source, token),
                    "candidate_id": candidate_id,
                    "construction_id": construction_id,
                })
            graph["provenance"].append({
                "rule_id": construction_id or "phase5.syntax.candidate",
                "resource_id": phase5.get("pipeline_version", "USG-INTERPRET/0.2.0"),
                "candidate_id": candidate_id,
            })

    # Preserve the segmentation tree and the explicit inter-clause marker.
    boundary_by_right = {
        item.get("right_clause_ref"): item
        for item in segmentation.get("boundaries", [])
    }
    for clause in segmentation.get("clauses", []):
        clause_id = clause.get("segment_id")
        boundary = boundary_by_right.get(clause_id)
        kind = "MAIN"
        parent_id = None
        if boundary:
            relation = boundary.get("relation")
            kind = "EMBEDDED" if relation == "COMPLEMENT" else "SUBORDINATE"
            parent_id = boundary.get("left_clause_ref")
        start, end = clause.get("start"), clause.get("end")
        if isinstance(start, int) and isinstance(end, int) and end > start:
            graph["clauses"].append({
                "id": _stable("p6c", clause_id),
                "kind": kind,
                "parent_id": _stable("p6c", parent_id) if parent_id else None,
                "source_clause_ref": clause_id,
                "span": _source_span(source, start, end),
            })
    # The engine's tree validator needs parent IDs to reference the emitted
    # clause IDs. Rewrite the parent IDs after all clause IDs are known.
    emitted_clause_ids = {
        item["source_clause_ref"]: item["id"] for item in graph["clauses"]
    }
    for item in graph["clauses"]:
        original_parent = item.get("parent_id")
        if original_parent:
            source_parent = next(
                (key for key, value in emitted_clause_ids.items()
                 if _stable("p6c", key) == original_parent), None
            )
            item["parent_id"] = emitted_clause_ids.get(source_parent) if source_parent else None
        item.pop("source_clause_ref", None)

    relation_map = {
        "COORDINATION_AND": "AND", "COORDINATION_OR": "OR",
        "CONTRAST": "CONTRAST", "COMPLEMENT": "COMPLEMENT",
        "TEMPORAL": "TEMPORAL", "CAUSE": "CAUSAL",
        "CONDITION": "CONDITIONAL",
    }
    for boundary in segmentation.get("boundaries", []):
        relation_type = relation_map.get(boundary.get("relation"))
        if relation_type is None:
            diagnostics.append("UNMAPPED_CLAUSE_BOUNDARY:" + str(boundary.get("relation")))
            continue
        left_roots = clause_roots.get(boundary.get("left_clause_ref"), [])
        right_roots = clause_roots.get(boundary.get("right_clause_ref"), [])
        if not left_roots or not right_roots:
            diagnostics.append("CLAUSE_BOUNDARY_WITHOUT_TWO_PREDICATE_CANDIDATES")
            continue
        start, end = boundary.get("marker_span", [None, None])
        evidence = _source_span(source, start, end)
        for left in left_roots:
            for right in right_roots:
                graph["relations"].append({
                    "type": relation_type, "source": left, "target": right,
                    "evidence": evidence,
                    "feature": ("COORDINATION" if relation_type in {"AND", "OR", "CONTRAST"}
                                else "EMBEDDED_CLAUSE" if relation_type == "COMPLEMENT" else None),
                    "origin": "PHASE5_CLAUSE_SEGMENTATION",
                })
        graph["features"].append(
            "COORDINATION" if relation_type in {"AND", "OR", "CONTRAST"}
            else "EMBEDDED_CLAUSE" if relation_type in {"COMPLEMENT", "RELATIVE"}
            else "SUBORDINATE_CLAUSE"
        )

    for clause_result in operators.get("clauses", []):
        for candidate in clause_result.get("candidates", []):
            operator_type = candidate.get("operator_type")
            if operator_type in (None, "AUXILIARY"):
                continue
            targets = token_nodes.get(candidate.get("scope_target_token_ref"), [])
            operator_token = tokens.get(candidate.get("token_ref"))
            if not targets or operator_token is None:
                diagnostics.append("OPERATOR_SCOPE_TARGET_NOT_IN_SEMANTIC_CANDIDATES")
                continue
            for target_id in dict.fromkeys(targets):
                graph["operators"].append({
                    "type": operator_type,
                    "target_id": target_id,
                    "scope": "LOCAL",
                    "scope_kind": candidate.get("scope_kind"),
                    "value": candidate.get("value"),
                    "span": _token_span(source, operator_token),
                    "origin": "PHASE5_OPERATOR_ANALYSIS",
                })
            graph["features"].append("OPERATOR")

    # Mentions stay distinct from referents. All antecedent links remain
    # alternatives and the composition layer deliberately never resolves them.
    mention_node_ids: dict[str, str] = {}
    for mention in discourse.get("mentions", []):
        token = tokens.get(mention.get("token_ref"))
        if token is None:
            continue
        mention_id = mention.get("mention_id")
        node_id = _stable("p6m", mention_id)
        mention_node_ids[mention_id] = node_id
        add_node(node_id, "MENTION", token, role="MENTION")
    references_by_pronoun: dict[str, list[str]] = {}
    for candidate in discourse.get("reference_candidates", []):
        pronoun = candidate.get("pronoun_mention_ref")
        antecedent = candidate.get("antecedent_mention_ref")
        if pronoun in mention_node_ids and antecedent in mention_node_ids:
            references_by_pronoun.setdefault(pronoun, []).append(mention_node_ids[antecedent])
    for mention in discourse.get("mentions", []):
        if mention.get("mention_type") != "PRONOMINAL":
            continue
        pronoun = mention.get("mention_id")
        if pronoun in mention_node_ids:
            graph["references"].append({
                "mention_id": mention_node_ids[pronoun],
                "antecedent_candidates": list(dict.fromkeys(references_by_pronoun.get(pronoun, []))),
                "uniqueness_evidence": False,
                "origin": "PHASE5_DISCOURSE_ANALYSIS",
            })
            graph["features"].append("DISCOURSE_REFERENCE")

    for discourse_relation in discourse.get("relations", []):
        raw_type = discourse_relation.get("relation")
        relation_type = {
            "TEMPORAL_SEQUENCE": "TEMPORAL", "CONTRAST": "CONTRAST",
            "CAUSE": "CAUSAL", "CONSEQUENCE": "CAUSAL",
        }.get(raw_type)
        if relation_type is None:
            diagnostics.append("UNMAPPED_DISCOURSE_RELATION:" + str(raw_type))
            continue
        left_roots = clause_roots.get(discourse_relation.get("source_clause_ref"), [])
        right_roots = clause_roots.get(discourse_relation.get("target_clause_ref"), [])
        if not left_roots or not right_roots:
            diagnostics.append("DISCOURSE_LINK_WITHOUT_TWO_PREDICATE_CANDIDATES")
            continue
        start, end = discourse_relation.get("marker_span", [None, None])
        evidence = _source_span(source, start, end)
        for left in left_roots:
            for right in right_roots:
                graph["relations"].append({
                    "type": relation_type, "source": left, "target": right,
                    "evidence": evidence, "origin": "PHASE5_DISCOURSE_ANALYSIS",
                })

    if graph["relations"] and any(
        item.get("type") in {"AND", "OR", "CONTRAST"} for item in graph["relations"]
    ):
        graph["features"].append("COORDINATION")
    graph["features"] = sorted(set(graph["features"]))
    if not graph["nodes"]:
        graph["provenance"].append({
            "rule_id": "phase5.no_licensed_core_predicate_candidate",
            "resource_id": phase5.get("pipeline_version", "USG-INTERPRET/0.2.0"),
        })
    return graph, diagnostics


class Phase6IntegratedInterpreter:
    """Compose Phase 5 stage candidates and Phase 6 construction probes."""

    def __init__(self, phase5_service: Phase5InterpretationService | None = None):
        self.phase5_service = phase5_service or Phase5InterpretationService()
        self.resource_manifest_digest = _manifest_digest()

    def interpret(self, source: str, language: str) -> dict:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-empty string")
        if language not in {"en", "ar"}:
            raise ValueError("language must be 'en' or 'ar'")
        phase5 = self.phase5_service.interpret(
            source, language, resource_manifest_digest=self.resource_manifest_digest,
        )
        graph, diagnostics = _phase5_graph(source, phase5)
        template = extract_candidate_graph(source, language)
        # A strict Phase 6 construction probe is a fallback for cases where the
        # existing grammatical stages did not produce any predicate candidates.
        if not any(node.get("role") == "ACTION" for node in graph["nodes"]) and template["status"] == "CANDIDATE_PATTERN_MATCH":
            _merge_template_graph(graph, template["graph"])
            diagnostics.append("PHASE6_CLOSED_TEMPLATE_FALLBACK:" + str(template["template_id"]))
        graph["features"] = sorted(set(graph["features"]))
        if not graph["nodes"]:
            return {
                "pipeline_contract": "USG-INTERPRET/0.3.0",
                "pipeline_version": VERSION,
                "status": "ABSTAIN",
                "capability_state": "CANDIDATE_ONLY",
                "source": phase5["source"],
                "phase5_completion_status": phase5["completion_status"],
                "graph": graph,
                "phase5": phase5,
                "diagnostics": diagnostics + [{
                    "code": "NO_PHASE6_CONSTRUCTION_CANDIDATE",
                    "message": "No registered Phase 5 or Phase 6 candidate construction was licensed.",
                }],
            }
        composition = compose(source, language, graph)
        return {
            "pipeline_contract": "USG-INTERPRET/0.3.0",
            "pipeline_version": VERSION,
            "status": "CANDIDATE_ONLY",
            "capability_state": "CANDIDATE_ONLY",
            "source": phase5["source"],
            "phase5_completion_status": phase5["completion_status"],
            "graph": graph,
            "composition": composition,
            "projection": project_loss_aware(composition),
            "phase5": phase5,
            "diagnostics": diagnostics,
            "capability_boundary": {
                "benchmark_enabled_constructions": [],
                "candidate_only_families": sorted(set(graph["features"])),
                "naturalistic_accuracy_claimed": False,
                "identity_resolution_performed": False,
                "truth_promotion_performed": False,
            },
        }


def interpret_phase6_candidate(source: str, language: str,
                               service: Phase6IntegratedInterpreter | None = None) -> dict:
    """Convenience API with a fresh service; inject a long-lived service in servers."""
    return (service or Phase6IntegratedInterpreter()).interpret(source, language)


def project_preservation_document(composition: dict) -> dict:
    """Losslessly archive a candidate composition as a canonical OPAQUE document.

    This is a preservation projection, not a claim that the candidate graph has
    become a canonical semantic assertion. The complete Phase 6 candidate result
    remains under a namespaced extension and in the OPAQUE expression payload.
    """
    if not isinstance(composition, dict) or composition.get("pipeline_contract") != "USG-INTERPRET/0.3.0":
        raise CompositionError("a Phase 6 candidate composition is required")
    source = composition.get("source", {})
    text = source.get("text")
    language = source.get("language")
    if not isinstance(text, str) or not text or language not in {"en", "ar"}:
        raise CompositionError("Phase 6 composition has no valid source snapshot")
    digest = sha256(text.encode("utf-8")).hexdigest()
    if source.get("sha256") != digest:
        raise CompositionError("Phase 6 source digest does not match exact UTF-8 source")
    suffix = digest[:24]
    source_id = "p6:source:" + suffix
    expression_id = "p6:opaque:" + suffix
    evidence_id = "p6:evidence:" + suffix
    derivation_id = "p6:derivation:" + suffix
    unresolved_id = "p6:unresolved:" + suffix
    span = {"sourceRef": source_id, "start": 0, "end": len(text),
            "offsetUnit": "unicode_code_point"}
    payload = {
        "pipeline_contract": composition["pipeline_contract"],
        "pipeline_version": composition.get("pipeline_version"),
        "status": composition.get("status"),
        "capability_state": "CANDIDATE_ONLY",
        "source_sha256": digest,
        "language": language,
        "graph": deepcopy(composition.get("graph", {})),
        "grammatical": deepcopy(composition.get("grammatical", {})),
        "features": deepcopy(composition.get("features", [])),
        "provenance": deepcopy(composition.get("provenance", [])),
        "safety": {
            "canonical_assertion_emitted": False,
            "identity_resolution_performed": False,
            "truth_promotion_performed": False,
        },
    }
    return {
        "profileId": "USG-SEM/1.0",
        "documentId": "p6:document:" + suffix,
        "sources": [{
            "id": source_id, "text": text, "language": language,
            "sourceType": "USER_INPUT", "trustTier": "QUARANTINE",
            "sensitivity": "INTERNAL", "textHash": digest,
            "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
            "offsetUnit": "unicode_code_point",
        }],
        "primarySourceRef": source_id,
        "definitions": {"concepts": [], "frames": [], "roles": [], "relations": []},
        "referents": [],
        "mentions": [],
        "expressions": [{
            "id": expression_id, "op": "OPAQUE", "sort": "PROP",
            "semanticKind": "EXPRESSION", "operandRefs": [],
            "params": {
                "opaqueType": "USG-INTERPRET/0.3.0-CANDIDATE",
                "reason": "Candidate-only interpretation is preserved without canonical semantic promotion.",
                "candidatePayload": payload,
            },
            "annotations": {"spans": [span], "ruleIds": ["phase6.lossless-preservation/0.1.0"],
                            "basis": "EXPLICIT"},
            "interpretationStatus": "UNRESOLVED",
        }],
        "rootExpressionRefs": [expression_id],
        "assertions": [],
        "evidence": [{
            "id": evidence_id, "sourceRef": source_id, "span": span,
            "quote": text, "alignmentStatus": "EXACT",
            "semanticSupportStatus": "NOT_ESTABLISHED",
            "supportingRuleRefs": [],
        }],
        "contexts": [],
        "expressionRelations": [],
        "unresolvedItems": [{
            "id": unresolved_id, "status": "UNRESOLVED",
            "reason": "Candidate graph remains unresolved and is preserved as OPAQUE data.",
            "surfaceText": text, "scopeRef": expression_id,
            "evidenceRefs": [evidence_id],
        }],
        "derivations": [{
            "id": derivation_id, "method": "COMPOSITION",
            "component": VERSION, "ruleIds": ["phase6.lossless-preservation/0.1.0"],
            "inputRefs": [source_id], "outputRefs": [expression_id],
            "status": "PROPOSED",
            "diagnostics": ["No canonical assertion or referent identity was emitted."],
        }],
        "validation": {
            "structuralStatus": "NOT_CHECKED", "checks": [],
            "validator": "phase6-preservation-projection/0.1.0",
            "contractVersion": "USG-SEM/1.0",
        },
        "mapping": {
            "sourceProfile": "USG-INTERPRET/0.3.0",
            "sourceVersion": "0.3.0", "status": "LOSSLESS",
            "unmappedRefs": [],
            "notes": [
                "Lossless preservation only: full candidate graph and provenance are retained in OPAQUE data.",
                "This document contains no canonical semantic assertion; interpretationStatus remains UNRESOLVED.",
            ],
        },
        "extensions": {"org.wizekin.usg.phase6": payload},
    }


__all__ = [
    "VERSION", "Phase6IntegratedInterpreter", "interpret_phase6_candidate",
    "project_preservation_document",
]
