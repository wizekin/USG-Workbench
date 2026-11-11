"""Integrated, deterministic orchestration of accepted Phase 5 interpretation stages."""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from tools.usg_interpretation_v0_1_0.source import ingest_source
from .lexical import LexicalAnalyzer, bundled_lexical_resource_v0_4_0
from .segmentation import segment_document
from .syntax import SyntaxAnalyzer
from .compose import SemanticComposer
from .operators import OperatorAnalyzer
from .discourse import DiscourseAnalyzer
from .catalogue import bundled_resource_descriptors

PHASE5_INTEGRATION_VERSION = "phase5-interpretation-integration/0.1.0"
PIPELINE_CONTRACT = "USG-INTERPRET/0.2.0"


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {item.name: _jsonable(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported interpretation artifact value: {type(value).__name__}")


def canonical_result_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class Phase5InterpretationService:
    """Run the existing v0.2 stages without inventing a USG-SEM document adapter."""

    def __init__(
        self,
        *,
        max_syntax_candidates: int = 64,
        max_semantic_candidates: int = 64,
        max_scope_operators: int = 4,
        max_antecedents: int = 20,
        max_reference_candidates: int = 64,
    ):
        self.lexical_resource = bundled_lexical_resource_v0_4_0()
        self.lexical_analyzer = LexicalAnalyzer(self.lexical_resource)
        self.syntax_analyzer = SyntaxAnalyzer(max_candidates=max_syntax_candidates)
        self.semantic_composer = SemanticComposer(max_candidates=max_semantic_candidates)
        self.operator_analyzer = OperatorAnalyzer(max_scope_operators=max_scope_operators)
        self.discourse_analyzer = DiscourseAnalyzer(
            max_antecedents=max_antecedents,
            max_candidates_per_pronoun=max_reference_candidates,
        )
        self.resource_limits = {
            "syntax_max_candidates": max_syntax_candidates,
            "semantic_max_candidates": max_semantic_candidates,
            "operator_max_scope_operators": max_scope_operators,
            "discourse_max_antecedents": max_antecedents,
            "discourse_max_candidates_per_pronoun": max_reference_candidates,
            "interrupted": False,
        }

    def interpret(
        self,
        text: str,
        language: str,
        *,
        resource_manifest_digest: str,
    ) -> dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        if language not in {"en", "ar"}:
            raise ValueError("language must be 'en' or 'ar'")
        if (not isinstance(resource_manifest_digest, str)
                or len(resource_manifest_digest) != 64
                or any(char not in "0123456789abcdef" for char in resource_manifest_digest)):
            raise ValueError("resource_manifest_digest must be a lowercase SHA-256 digest")

        source_seed = sha256((language + "\0" + text).encode("utf-8")).hexdigest()
        source = ingest_source(text, language, source_id="src:" + source_seed[:24])
        lexical = self.lexical_analyzer.analyze(source)
        segmented = segment_document(lexical)
        operators = self.operator_analyzer.analyze(lexical, segmented)
        syntax = self.syntax_analyzer.analyze(lexical, segmented, operators)
        composition = self.semantic_composer.compose(
            lexical, segmented, syntax, operators
        )
        discourse = self.discourse_analyzer.analyze(lexical, segmented)

        lexical_ambiguous = [
            item for item in lexical.tokens if item.status == "AMBIGUOUS"
        ]
        lexical_unresolved = [
            item for item in lexical.tokens if item.status == "UNRESOLVED"
        ]
        diagnostics = []
        for item in lexical_ambiguous:
            diagnostics.append({
                "code": "LEXICAL_AMBIGUOUS_TOKEN",
                "stage": "lexical",
                "token_ref": item.token.token_id,
                "source_span": [item.token.start, item.token.end],
            })
        for item in lexical_unresolved:
            diagnostics.append({
                "code": "LEXICAL_UNRESOLVED_TOKEN",
                "stage": "lexical",
                "token_ref": item.token.token_id,
                "source_span": [item.token.start, item.token.end],
            })
        for item in syntax.clauses:
            if item.status not in {"RESOLVED"}:
                diagnostics.append({
                    "code": "SYNTAX_" + item.status,
                    "stage": "syntax",
                    "clause_ref": item.clause_ref,
                    "unresolved_token_ids": list(item.unresolved_token_ids),
                })
        for item in operators.clauses:
            if item.status in {"AMBIGUOUS", "INCOMPLETE", "INCOMPLETE_RESOURCE_LIMIT"}:
                diagnostics.append({
                    "code": "OPERATOR_" + item.status,
                    "stage": "operators",
                    "clause_ref": item.clause_ref,
                    "unresolved_token_ids": list(item.unresolved_token_ids),
                })
        for clause_ref in composition.unresolved_clause_refs:
            diagnostics.append({
                "code": "SEMANTIC_CLAUSE_UNRESOLVED",
                "stage": "semantic_composition",
                "clause_ref": clause_ref,
            })
        for mention_ref in discourse.unresolved_pronoun_mention_refs:
            diagnostics.append({
                "code": "DISCOURSE_ANTECEDENT_UNRESOLVED",
                "stage": "discourse",
                "mention_ref": mention_ref,
            })

        interrogative_force = text.rstrip().endswith(("?", "؟"))
        if interrogative_force:
            diagnostics.append({
                "code": "UNSUPPORTED_INTERROGATIVE_FORCE",
                "stage": "syntax",
                "source_span": [len(text.rstrip()) - 1, len(text.rstrip())],
            })

        stage_statuses = {
            syntax.status, operators.status, composition.status, discourse.status,
        }
        if "INCOMPLETE_RESOURCE_LIMIT" in stage_statuses:
            completion = "INCOMPLETE_RESOURCE_LIMIT"
        elif interrogative_force or "UNSUPPORTED" in stage_statuses:
            completion = "UNSUPPORTED"
        elif ("AMBIGUOUS" in stage_statuses or lexical_ambiguous):
            completion = "AMBIGUOUS"
        elif (
            "PARTIAL" in stage_statuses or "INCOMPLETE" in stage_statuses
            or lexical_unresolved or discourse.unresolved_pronoun_mention_refs
        ):
            completion = "PARTIAL"
        else:
            completion = "COMPLETE"

        resource_versions = [{
            "resource_id": item.resource_id,
            "resource_type": item.resource_type,
            "version": item.version,
            "sha256": item.sha256,
            "language": item.language,
        } for item in bundled_resource_descriptors()]
        source_record = {
            "source_id": source.source_id,
            "text": source.text,
            "language": source.language,
            "language_profile": source.language_profile,
            "sha256": source.sha256,
            "offset_unit": "unicode_code_point",
        }
        stage_records = {
            "lexical": {
                "version": lexical.analyzer_version,
                "resource_id": lexical.resource_id,
                "resource_version": lexical.resource_version,
                "resource_sha256": lexical.resource_sha256,
                "resource_sha256_kind": "canonical_composite_resource_content",
                "resource_provenance": self.lexical_resource.provenance,
                "status": "AMBIGUOUS" if lexical_ambiguous else "PARTIAL" if lexical_unresolved else "COMPLETE",
                "artifact": _jsonable(lexical),
            },
            "segmentation": {
                "version": segmented.segmentation_version,
                "status": "COMPLETE",
                "artifact": _jsonable(segmented),
            },
            "operators": {
                "version": operators.analyzer_version,
                "status": operators.status,
                "artifact": _jsonable(operators),
            },
            "syntax": {
                "version": syntax.analyzer_version,
                "status": syntax.status,
                "artifact": _jsonable(syntax),
            },
            "semantic_composition": {
                "version": composition.composer_version,
                "status": composition.status,
                "artifact": composition.to_dict(),
            },
            "discourse": {
                "version": discourse.analyzer_version,
                "status": discourse.status,
                "artifact": _jsonable(discourse),
            },
        }
        result = {
            "pipeline_contract": PIPELINE_CONTRACT,
            "pipeline_version": PHASE5_INTEGRATION_VERSION,
            "language_profile": source.language_profile,
            "completion_status": completion,
            "source": source_record,
            "source_ref": source.source_id,
            "source_sha256": source.sha256,
            "resource_manifest_digest": resource_manifest_digest,
            "resource_versions": resource_versions,
            "stages": stage_records,
            "document_composition": composition.to_dict(),
            "diagnostics": diagnostics,
            "alternatives": {
                "semantic_candidates": [
                    item.to_dict() for item in composition.candidates
                ],
                "discourse_reference_candidates": _jsonable(discourse.reference_candidates),
            },
            "resource_limits": dict(self.resource_limits),
            "safety": {
                "usg_sem_document_emitted": False,
                "truth_promotion": False,
                "identity_resolution": False,
                "association_promotion": False,
            },
        }
        return result


__all__ = [
    "PHASE5_INTEGRATION_VERSION", "PIPELINE_CONTRACT",
    "Phase5InterpretationService", "canonical_result_bytes",
]
