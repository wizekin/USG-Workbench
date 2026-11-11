"""End-to-end deterministic USG-INTERPRET/0.2.0 application service."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tools.usg_interpretation_v0_1_0.source import ingest_source
from .lexical import (
    LexicalAnalyzer, bundled_lexical_resource_v0_3_0,
    LEXICAL_ANALYSIS_VERSION, MORPHOLOGY_RULESET_VERSION,
)
from .segmentation import segment_document, SEGMENTATION_VERSION
from .operators import OperatorAnalyzer, OPERATOR_ANALYSIS_VERSION
from .syntax import SyntaxAnalyzer, SYNTAX_ANALYSIS_VERSION
from .compose import SemanticComposer, SEMANTIC_COMPOSITION_VERSION, initial_semantic_frame_registry
from .discourse import DiscourseAnalyzer, DISCOURSE_ANALYSIS_VERSION

INTERPRETATION_CONTRACT = "USG-INTERPRET/0.2.0"
EXPRESSION_GRAPH_PROFILE = "USG-INTERPRET-EXPRESSION-GRAPH/0.2.0"
ROOT = Path(__file__).resolve().parents[2]
_OPERATOR_RESOURCE_PATH = ROOT / "resources" / "operators" / "v0.1.0" / "operators-en-ar.json"


def _span(start: int, end: int) -> dict:
    return {"start": start, "end": end, "offsetUnit": "unicode_code_point"}


def _source_id(text: str, language: str) -> str:
    digest = hashlib.sha256((language + "\0" + text).encode("utf-8")).hexdigest()
    return "src:" + digest


def _lexical_json(analysis) -> dict:
    return {
        "status": "COMPLETE" if all(x.status != "UNRESOLVED" for x in analysis.tokens) else "PARTIAL",
        "resource": {
            "resourceId": analysis.resource_id, "version": analysis.resource_version,
            "sha256": analysis.resource_sha256,
        },
        "analyzerVersion": analysis.analyzer_version,
        "tokens": [{
            "tokenRef": item.token.token_id,
            "text": item.token.surface_text,
            "kind": item.token.kind,
            "sourceSpan": _span(item.token.start, item.token.end),
            "status": item.status,
            "candidates": [{
                "lemma": candidate.lemma,
                "partOfSpeech": candidate.part_of_speech,
                "senseRef": candidate.sense_id,
                "conceptRef": candidate.concept_ref,
                "features": dict(candidate.features),
                "derivedByRule": candidate.derived_by_rule,
            } for candidate in item.candidates],
        } for item in analysis.tokens],
    }


def _segmentation_json(segmented) -> dict:
    text = segmented.source.text
    return {
        "version": segmented.segmentation_version,
        "sentences": [{
            "sentenceRef": x.segment_id, "sourceSpan": _span(x.start, x.end),
            "text": text[x.start:x.end],
        } for x in segmented.sentences],
        "clauses": [{
            "clauseRef": x.segment_id, "sentenceRef": x.sentence_ref,
            "sourceSpan": _span(x.start, x.end), "text": text[x.start:x.end],
        } for x in segmented.clauses],
        "boundaries": [{
            "boundaryRef": x.boundary_id, "relation": x.relation,
            "markerText": x.marker_text, "markerSpan": _span(*x.marker_span),
            "leftClauseRef": x.left_clause_ref, "rightClauseRef": x.right_clause_ref,
            "status": "CANDIDATE",
        } for x in segmented.boundaries],
    }


def _operators_json(analysis) -> dict:
    return {
        "status": analysis.status,
        "analyzerVersion": analysis.analyzer_version,
        "recognizedTokenRefs": list(analysis.recognized_token_ids),
        "clauses": [{
            "clauseRef": clause.clause_ref, "status": clause.status,
            "unresolvedTokenRefs": list(clause.unresolved_token_ids),
            "scopeAlternatives": [list(x) for x in clause.scope_alternatives],
            "candidates": [{
                "tokenRef": x.token_ref, "operatorType": x.operator_type,
                "operatorValue": x.value, "scopeTargetKind": x.scope_kind,
                "scopeTargetTokenRef": x.scope_target_token_ref,
                "sourceSpan": _span(*x.source_span),
                "scopeSpan": _span(*x.scope_span),
            } for x in clause.candidates],
        } for clause in analysis.clauses],
    }


def _syntax_json(analysis) -> dict:
    return {
        "status": analysis.status,
        "analyzerVersion": analysis.analyzer_version,
        "clauses": [{
            "clauseRef": clause.clause_ref, "status": clause.status,
            "unresolvedTokenRefs": list(clause.unresolved_token_ids),
            "candidates": [{
                "candidateRef": candidate.candidate_id,
                "constructionRef": candidate.construction_id,
                "roleTokenRefs": dict(candidate.role_token_refs),
                "lexicalSenseRefs": dict(candidate.lexical_sense_refs),
                "sourceSpan": _span(*candidate.source_span),
                "constituents": [{
                    "constituentRef": x.constituent_id, "type": x.constituent_type,
                    "tokenRefs": list(x.token_refs), "sourceSpan": _span(*x.source_span),
                } for x in candidate.constituents],
                "dependencies": [{
                    "headTokenRef": x.head_token_ref,
                    "dependentTokenRef": x.dependent_token_ref,
                    "relation": x.relation,
                } for x in candidate.dependencies],
            } for candidate in clause.candidates],
        } for clause in analysis.clauses],
        "attachments": [{
            "attachmentRef": x.attachment_id,
            "sourceClauseRef": x.source_clause_ref,
            "targetClauseRef": x.target_clause_ref,
            "relation": x.relation,
            "markerText": x.marker_text,
            "markerSpan": _span(*x.marker_span),
            "status": x.status,
        } for x in analysis.attachments],
    }


def _discourse_json(analysis) -> dict:
    return {
        "status": analysis.status,
        "analyzerVersion": analysis.analyzer_version,
        "mentions": [{
            "mentionRef": x.mention_id, "tokenRef": x.token_ref,
            "sentenceRef": x.sentence_ref, "clauseRef": x.clause_ref,
            "mentionType": x.mention_type, "surfaceText": x.surface_text,
            "sourceSpan": _span(*x.source_span),
            "lexicalSenseRefs": list(x.lexical_sense_refs),
            "featuresBySense": {sense: dict(features) for sense, features in x.features_by_sense},
        } for x in analysis.mentions],
        "referenceCandidates": [{
            "candidateRef": x.candidate_id,
            "pronounMentionRef": x.pronoun_mention_ref,
            "antecedentMentionRef": x.antecedent_mention_ref,
            "compatibilityReasons": list(x.compatibility_reasons),
            "sentenceDistance": x.sentence_distance,
            "status": x.status,
        } for x in analysis.reference_candidates],
        "unresolvedPronounMentionRefs": list(analysis.unresolved_pronoun_mention_refs),
        "relations": [{
            "relationRef": x.relation_id,
            "sourceSentenceRef": x.source_sentence_ref,
            "targetSentenceRef": x.target_sentence_ref,
            "sourceClauseRef": x.source_clause_ref,
            "targetClauseRef": x.target_clause_ref,
            "relation": x.relation, "markerText": x.marker_text,
            "markerSpan": _span(*x.marker_span), "status": x.status,
        } for x in analysis.relations],
    }


class InterpretationServiceV02:
    """Run the accepted local pipeline; no model, network, or human review is required."""

    def __init__(self):
        self.lexical_resource = bundled_lexical_resource_v0_3_0()
        self.lexical_analyzer = LexicalAnalyzer(self.lexical_resource)
        self.operator_analyzer = OperatorAnalyzer()
        self.syntax_analyzer = SyntaxAnalyzer()
        self.semantic_composer = SemanticComposer()
        self.discourse_analyzer = DiscourseAnalyzer()
        self.frame_registry = initial_semantic_frame_registry()
        self.operator_resource = json.loads(_OPERATOR_RESOURCE_PATH.read_text(encoding="utf-8"))

    def interpret(self, text: str, language: str) -> dict[str, Any]:
        source = ingest_source(text, language, source_id=_source_id(text, language))
        lexical = self.lexical_analyzer.analyze(source)
        segmented = segment_document(lexical)
        operators = self.operator_analyzer.analyze(lexical, segmented)
        syntax = self.syntax_analyzer.analyze(lexical, segmented, operators)
        composition = self.semantic_composer.compose(lexical, segmented, syntax, operators)
        discourse = self.discourse_analyzer.analyze(lexical, segmented)

        diagnostics = []
        for item in lexical.tokens:
            if item.status == "UNRESOLVED":
                diagnostics.append({
                    "stage": "LEXICAL", "code": "TOKEN_UNRESOLVED",
                    "tokenRef": item.token.token_id,
                    "sourceSpan": _span(item.token.start, item.token.end),
                })
        for clause in syntax.clauses:
            if clause.status not in {"RESOLVED", "AMBIGUOUS"}:
                diagnostics.append({
                    "stage": "SYNTAX", "code": "CLAUSE_" + clause.status,
                    "clauseRef": clause.clause_ref,
                    "unresolvedTokenRefs": list(clause.unresolved_token_ids),
                })
        for clause in operators.clauses:
            if clause.status in {"INCOMPLETE", "INCOMPLETE_RESOURCE_LIMIT"}:
                diagnostics.append({
                    "stage": "OPERATORS", "code": "OPERATOR_" + clause.status,
                    "clauseRef": clause.clause_ref,
                    "unresolvedTokenRefs": list(clause.unresolved_token_ids),
                })
        if discourse.unresolved_pronoun_mention_refs:
            diagnostics.append({
                "stage": "DISCOURSE", "code": "REFERENCE_UNRESOLVED",
                "mentionRefs": list(discourse.unresolved_pronoun_mention_refs),
            })

        if composition.status == "INCOMPLETE_RESOURCE_LIMIT":
            completion = "INCOMPLETE_RESOURCE_LIMIT"
        elif composition.status == "UNSUPPORTED":
            completion = "UNSUPPORTED"
        elif composition.status == "PARTIAL" or discourse.status == "PARTIAL":
            completion = "PARTIAL"
        elif composition.status == "AMBIGUOUS" or discourse.status == "AMBIGUOUS":
            completion = "AMBIGUOUS"
        else:
            completion = "COMPLETE"

        return {
            "contract": INTERPRETATION_CONTRACT,
            "expressionGraphProfile": EXPRESSION_GRAPH_PROFILE,
            "completionStatus": completion,
            "source": {
                "sourceRef": source.source_id, "sha256": source.sha256,
                "language": source.language, "languageProfile": source.language_profile,
                "text": source.text,
            },
            "resourceVersions": {
                "lexicon": {
                    "resourceId": self.lexical_resource.resource_id,
                    "version": self.lexical_resource.version,
                    "sha256": self.lexical_resource.digest(),
                },
                "morphology": MORPHOLOGY_RULESET_VERSION,
                "segmentation": SEGMENTATION_VERSION,
                "operators": {
                    "resourceId": self.operator_resource["resource_id"],
                    "version": self.operator_resource["version"],
                },
                "syntax": SYNTAX_ANALYSIS_VERSION,
                "semanticFrames": {
                    "registryId": self.frame_registry.registry_id,
                    "version": self.frame_registry.version,
                },
                "semanticComposition": SEMANTIC_COMPOSITION_VERSION,
                "discourse": DISCOURSE_ANALYSIS_VERSION,
            },
            "stages": {
                "lexical": _lexical_json(lexical),
                "segmentation": _segmentation_json(segmented),
                "operators": _operators_json(operators),
                "syntax": _syntax_json(syntax),
                "semanticComposition": composition.to_dict(),
                "discourse": _discourse_json(discourse),
            },
            "diagnostics": diagnostics,
        }


__all__ = [
    "INTERPRETATION_CONTRACT", "EXPRESSION_GRAPH_PROFILE",
    "InterpretationServiceV02",
]
