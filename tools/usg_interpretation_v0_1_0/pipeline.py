"""Bounded end-to-end interpreter and USG-SEM/1.0 document projection."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any
from uuid import uuid4

from .source import ingest_source, segment_source
from .lexical import LexicalAnalyzer, LexicalEntry, LexicalResource
from .syntax import GrammarAnalyzer, initial_grammar_registry
from .compose import SemanticComposer, initial_semantic_frame_registry
from .mentions import MentionAnalyzer
from .discourse import DiscourseAnalyzer, initial_discourse_registry
from .assertion_evidence import project_assertions_and_evidence

PIPELINE_VERSION = "usg-interpretation/0.1.0"


def demo_lexical_resource() -> LexicalResource:
    """Tiny transparent demonstration lexicon, not a production language model."""
    entries = (
        LexicalEntry("en", "Ada", "Ada", "PROPN", "en:ada"),
        LexicalEntry("en", "writes", "write", "VERB", "en:write"),
        LexicalEntry("en", "code", "code", "NOUN", "en:code"),
        LexicalEntry("ar", "كتب", "كتب", "VERB", "ar:write"),
        LexicalEntry("ar", "الطالب", "طالب", "NOUN", "ar:student"),
        LexicalEntry("ar", "الدرس", "درس", "NOUN", "ar:lesson"),
    )
    return LexicalResource("usg-demo-lexicon", 1, entries)


class InterpretationService:
    """Offline deterministic pipeline; resource injection replaces demo lexicon."""

    def __init__(self, lexical_resource: LexicalResource | None = None):
        self.lexical_analyzer = LexicalAnalyzer(lexical_resource or demo_lexical_resource())
        self.grammar_analyzer = GrammarAnalyzer(initial_grammar_registry())
        self.semantic_composer = SemanticComposer(initial_semantic_frame_registry())
        self.mention_analyzer = MentionAnalyzer()
        self.discourse_analyzer = DiscourseAnalyzer(initial_discourse_registry())

    def interpret(self, text: str, language: str) -> dict[str, Any]:
        source = ingest_source(text, language)
        segmented = segment_source(source)
        lexical = self.lexical_analyzer.analyze(source)
        mentions = self.mention_analyzer.analyze(lexical)
        discourse = self.discourse_analyzer.analyze(segmented, lexical)

        syntax = None
        composition = None
        unresolved_items = []
        if not segmented.sentences:
            completion = "PARTIAL" if text else "UNSUPPORTED"
            unresolved_items.append({
                "id": "unresolved:empty-source", "status": "UNRESOLVED",
                "reason": "NO_NON_WHITESPACE_SENTENCE_SPAN",
                "surfaceText": text,
            })
        elif len(segmented.sentences) != 1:
            completion = "UNSUPPORTED"
            for sentence in segmented.sentences:
                unresolved_items.append({
                    "id": f"unresolved:{sentence.segment_id}",
                    "status": "UNSUPPORTED",
                    "reason": "MULTI_SENTENCE_COMPOSITION_NOT_ENABLED",
                    "surfaceText": text[sentence.start:sentence.end],
                })
        else:
            syntax = self.grammar_analyzer.analyze(lexical)
            composition = self.semantic_composer.compose(lexical, syntax)
            if syntax.status == "INCOMPLETE":
                completion = "PARTIAL"
                for token_id in syntax.unresolved_token_ids:
                    item = next(x for x in lexical.tokens if x.token.token_id == token_id)
                    unresolved_items.append({
                        "id": f"unresolved:{token_id}", "status": "UNRESOLVED",
                        "reason": "LEXICAL_ANALYSIS_UNRESOLVED",
                        "surfaceText": item.token.surface_text,
                    })
            elif syntax.status == "UNSUPPORTED":
                completion = "UNSUPPORTED"
                unresolved_items.append({
                    "id": "unresolved:syntax", "status": "UNSUPPORTED",
                    "reason": "NO_REGISTERED_GRAMMAR_PATTERN",
                    "surfaceText": text,
                })
            elif composition.status == "UNSUPPORTED":
                completion = "UNSUPPORTED"
                unresolved_items.append({
                    "id": "unresolved:semantic-frame", "status": "UNSUPPORTED",
                    "reason": "NO_REGISTERED_SEMANTIC_FRAME",
                    "surfaceText": text,
                })
            elif composition.status != "COMPOSED":
                completion = "AMBIGUOUS" if composition.status == "AMBIGUOUS" else "PARTIAL"
                unresolved_items.append({
                    "id": "unresolved:composition", "status": "AMBIGUOUS",
                    "reason": "SEMANTIC_COMPOSITION_NOT_UNIQUE",
                    "surfaceText": text,
                })
            else:
                completion = "COMPLETE"

        document = self._document(source, lexical, mentions, discourse,
                                  composition, unresolved_items)
        diagnostics = []
        if syntax is not None:
            diagnostics.append({"stage": "syntax", "status": syntax.status})
        if composition is not None:
            diagnostics.append({"stage": "semantic_composition", "status": composition.status})
        return {
            "pipeline_contract": "USG-INTERPRET/0.1.0",
            "pipeline_version": PIPELINE_VERSION,
            "language_profile": source.language_profile,
            "completion_status": completion,
            "source_ref": source.source_id,
            "stages": [
                {"stage": "source_ingestion", "status": "COMPLETE", "version": "source-ingestion/0.1.0"},
                {"stage": "segmentation", "status": "COMPLETE", "version": segmented.segmentation_version},
                {"stage": "lexical", "status": "COMPLETE", "version": lexical.analyzer_version,
                 "resource_id": lexical.resource_id, "resource_version": lexical.resource_version},
                {"stage": "syntax", "status": syntax.status if syntax else "NOT_RUN",
                 "version": syntax.analyzer_version if syntax else "syntax-analysis/0.1.0"},
                {"stage": "semantic_composition",
                 "status": composition.status if composition else "NOT_RUN",
                 "version": composition.composer_version if composition else "semantic-composition/0.1.0"},
                {"stage": "mentions", "status": "COMPLETE", "version": mentions.analyzer_version},
                {"stage": "discourse", "status": "COMPLETE", "version": discourse.analyzer_version},
            ],
            "diagnostics": diagnostics,
            "alternatives": [],
            "resource_limits": {"interrupted": False, "budget": None},
            "document": document,
        }

    @staticmethod
    def _document(source, lexical, mentions, discourse, composition, unresolved_items):
        expressions = []
        referents = []
        assertions = []
        evidence = []
        roots = []
        if composition is not None and composition.status == "COMPOSED":
            candidate = composition.candidates[0]
            for node in candidate.nodes:
                params = dict(node.params)
                if node.op == "REF":
                    referent_id = "referent:" + node.node_id
                    referents.append({
                        "id": referent_id, "label": str(params.get("surface", "")),
                        "sourceRef": source.source_id,
                        "sourceSpan": {
                            "sourceRef": source.source_id,
                            "start": node.source_span[0], "end": node.source_span[1],
                            "offsetUnit": "unicode_code_point",
                        },
                    })
                    params["referentRef"] = referent_id
                elif "roleBindings" in params:
                    params["roleBindings"] = dict(params["roleBindings"])
                expressions.append({
                    "id": node.node_id, "op": node.op, "sort": node.sort,
                    "operandRefs": list(node.operand_refs), "params": params,
                    "interpretationStatus": "RESOLVED",
                })
            roots = [candidate.root_ref]
            projected = project_assertions_and_evidence(source, composition)
            assertions = list(projected.assertions)
            evidence = list(projected.evidence)
            # USG-SEM/1.0 span objects carry their own sourceRef.
            for item in evidence:
                item["span"]["sourceRef"] = source.source_id

        mention_records = [{
            "id": item.mention_id,
            "surfaceText": item.surface_text,
            "mentionType": item.mention_type,
            "resolutionStatus": "UNRESOLVED",
            "referentRef": None,
            "sourceSpan": {
                "sourceRef": source.source_id, "start": item.start, "end": item.end,
                "offsetUnit": "unicode_code_point",
            },
        } for item in mentions.mentions]
        source_record = {
            "id": source.source_id, "text": source.text, "language": source.language,
            "sourceType": "USER_INPUT", "trustTier": "UNKNOWN", "sensitivity": "UNKNOWN",
            "textHash": source.sha256, "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
            "offsetUnit": "unicode_code_point",
        }
        doc_id = "doc:" + uuid4().hex
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": doc_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "sources": [source_record],
            "primarySourceRef": source.source_id,
            "definitions": {
                "grammarVersion": "usg-initial-grammar/1",
                "concepts": [], "frames": [], "roles": [], "relations": [],
            },
            "referents": referents,
            "mentions": mention_records,
            "expressions": expressions,
            "rootExpressionRefs": roots,
            "assertions": assertions,
            "evidence": evidence,
            "contexts": [],
            "expressionRelations": [],
            "unresolvedItems": unresolved_items,
            "derivations": [],
            "validation": {
                "structuralStatus": "PASS", "checks": [],
                "validator": "USG-SEM/1.0 schema and canonical SQLite store",
                "contractVersion": "USG-SEM/1.0",
            },
            "mapping": {
                "sourceProfile": "USG-INTERPRET/0.1.0", "sourceVersion": "0.1.0",
                "status": "PARTIAL" if unresolved_items else "LOSSLESS",
                "unmappedRefs": [x["id"] for x in unresolved_items],
                "notes": ["Interpretation does not establish objective truth."],
            },
            "extensions": {
                "usgInterpretation": {
                    "pipelineContract": "USG-INTERPRET/0.1.0",
                    "languageProfile": source.language_profile,
                    "discourseCandidates": [
                        {"relation": x.relation, "markerId": x.marker_id,
                         "sourceSentenceRef": x.source_sentence_ref,
                         "targetSentenceRef": x.target_sentence_ref, "status": x.status}
                        for x in discourse.links
                    ],
                }
            },
        }


__all__ = ["PIPELINE_VERSION", "demo_lexical_resource", "InterpretationService"]
