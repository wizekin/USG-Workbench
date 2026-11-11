"""Explicit operator recognition and conservative scope-candidate analysis."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
import json
from pathlib import Path
from typing import Literal

from .lexical import LexicalAnalysis, bundled_lexical_resource_v0_2_0
from .segmentation import SegmentedDocument

OPERATOR_ANALYSIS_VERSION = "operator-scope-analysis/0.1.0"


@dataclass(frozen=True)
class OperatorLexeme:
    language: Literal["en", "ar"]
    form: str
    operator_type: Literal["NEGATION", "MODALITY", "TENSE", "ASPECT", "QUANTIFIER", "AUXILIARY"]
    value: str
    scope_kind: Literal["PREDICATE", "ARGUMENT"]
    target_pos: Literal["NOUN", "PROPN", "VERB"]
    condition: str | None = None


@dataclass(frozen=True)
class OperatorCandidate:
    clause_ref: str
    token_ref: str
    operator_type: str
    value: str
    scope_kind: str
    scope_target_token_ref: str
    source_span: tuple[int, int]
    scope_span: tuple[int, int]


@dataclass(frozen=True)
class ClauseOperatorResult:
    clause_ref: str
    status: Literal["NONE", "RESOLVED", "AMBIGUOUS", "INCOMPLETE", "INCOMPLETE_RESOURCE_LIMIT"]
    candidates: tuple[OperatorCandidate, ...]
    scope_alternatives: tuple[tuple[str, ...], ...]
    unresolved_token_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class OperatorAnalysis:
    source_ref: str
    source_sha256: str
    clauses: tuple[ClauseOperatorResult, ...]
    recognized_token_ids: tuple[str, ...]
    status: Literal["NONE", "RESOLVED", "AMBIGUOUS", "PARTIAL", "INCOMPLETE_RESOURCE_LIMIT"]
    analyzer_version: str = OPERATOR_ANALYSIS_VERSION


def load_operator_resource(path: str | Path) -> tuple[OperatorLexeme, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(raw) != {"resource_id", "version", "provenance", "operators"}:
        raise ValueError("operator resource contains missing or unknown top-level fields")
    if not raw["resource_id"] or not raw["version"] or not raw["provenance"]:
        raise ValueError("operator resource identity and provenance are required")
    result = tuple(OperatorLexeme(
        item["language"], item["form"], item["operator_type"], item["value"],
        item["scope_kind"], item["target_pos"], item.get("condition"),
    ) for item in raw["operators"])
    identities = [(x.language, x.form.casefold() if x.language == "en" else x.form) for x in result]
    if len(identities) != len(set(identities)):
        raise ValueError("operator language/form pairs must be unique")
    return result


def bundled_operator_resource() -> tuple[OperatorLexeme, ...]:
    path = Path(__file__).resolve().parents[2] / "resources" / "operators" / "v0.1.0" / "operators-en-ar.json"
    return load_operator_resource(path)


class OperatorAnalyzer:
    """Attach registered operators only to the nearest compatible following token."""

    def __init__(self, lexemes: tuple[OperatorLexeme, ...] | None = None, max_scope_operators: int = 4):
        if isinstance(max_scope_operators, bool) or not isinstance(max_scope_operators, int) or max_scope_operators < 1:
            raise ValueError("max_scope_operators must be a positive integer")
        self.lexemes = lexemes or bundled_operator_resource()
        self.max_scope_operators = max_scope_operators
        self._index = {
            (x.language, x.form.casefold() if x.language == "en" else x.form): x
            for x in self.lexemes
        }

    @staticmethod
    def _candidate_pos(item, pos: str) -> bool:
        return any(candidate.part_of_speech == pos for candidate in item.candidates)

    @staticmethod
    def _condition_matches(item, condition: str | None) -> bool:
        if condition is None:
            return True
        if condition == "VERBFORM_PARTICIPLE":
            return any(dict(candidate.features).get("VerbForm") == "Participle"
                       for candidate in item.candidates)
        return False

    def _analyze_clause(self, lexical: LexicalAnalysis, clause):
        clause_tokens = [x for x in lexical.tokens
                         if x.token.kind == "WORD"
                         and clause.start <= x.token.start and x.token.end <= clause.end]
        candidates = []
        unresolved = []
        recognized = []
        for index, item in enumerate(clause_tokens):
            token = item.token
            key = (lexical.source.language,
                   token.surface_text.casefold() if lexical.source.language == "en" else token.surface_text)
            lexeme = self._index.get(key)
            if lexeme is None:
                continue
            recognized.append(token.token_id)
            target = None
            for following in clause_tokens[index + 1:]:
                if self._candidate_pos(following, lexeme.target_pos) and self._condition_matches(following, lexeme.condition):
                    target = following
                    break
            if target is None:
                unresolved.append(token.token_id)
                continue
            candidates.append(OperatorCandidate(
                clause.segment_id, token.token_id, lexeme.operator_type, lexeme.value,
                lexeme.scope_kind, target.token.token_id,
                (token.start, token.end), (target.token.start, target.token.end),
            ))
        semantic = [x for x in candidates if x.operator_type != "AUXILIARY"]
        if unresolved:
            status = "INCOMPLETE"
            alternatives = ()
        elif len(semantic) > self.max_scope_operators:
            status = "INCOMPLETE_RESOURCE_LIMIT"
            alternatives = ()
        elif len(semantic) > 1:
            status = "AMBIGUOUS"
            alternatives = tuple(tuple(x.token_ref for x in order)
                                 for order in permutations(semantic))
        elif semantic:
            status = "RESOLVED"
            alternatives = ((semantic[0].token_ref,),)
        elif candidates:
            status = "RESOLVED"
            alternatives = ((),)
        else:
            status = "NONE"
            alternatives = ((),)
        return ClauseOperatorResult(
            clause.segment_id, status, tuple(candidates), alternatives, tuple(unresolved)
        ), tuple(recognized)

    def analyze(self, lexical: LexicalAnalysis, segmented: SegmentedDocument) -> OperatorAnalysis:
        if lexical.source != segmented.source:
            raise ValueError("operator analysis inputs must share the exact source snapshot")
        results = []
        recognized = []
        for clause in segmented.clauses:
            result, token_ids = self._analyze_clause(lexical, clause)
            results.append(result)
            recognized.extend(token_ids)
        statuses = {x.status for x in results}
        if "INCOMPLETE_RESOURCE_LIMIT" in statuses:
            overall = "INCOMPLETE_RESOURCE_LIMIT"
        elif "INCOMPLETE" in statuses:
            overall = "PARTIAL"
        elif "AMBIGUOUS" in statuses:
            overall = "AMBIGUOUS"
        elif "RESOLVED" in statuses:
            overall = "RESOLVED"
        else:
            overall = "NONE"
        return OperatorAnalysis(
            lexical.source.source_id, lexical.source.sha256, tuple(results),
            tuple(recognized), overall,
        )


__all__ = [
    "OPERATOR_ANALYSIS_VERSION", "OperatorLexeme", "OperatorCandidate",
    "ClauseOperatorResult", "OperatorAnalysis", "load_operator_resource",
    "bundled_operator_resource", "bundled_lexical_resource_v0_2_0",
    "OperatorAnalyzer",
]
