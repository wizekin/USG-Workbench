"""Advisory contextual POS candidate ranking; never overwrites lexical evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .lexical import LexicalAnalysis, LexicalCandidate
from .segmentation import SegmentedDocument


CONTEXTUAL_LEXICAL_VERSION = "contextual-lexical-ranking/0.1.0"


@dataclass(frozen=True)
class RankedLexicalCandidate:
    candidate: LexicalCandidate
    score: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ContextualTokenResult:
    token: object
    status: Literal["SELECTED", "AMBIGUOUS", "UNCHANGED", "UNRESOLVED", "NOT_APPLICABLE"]
    candidates: tuple[RankedLexicalCandidate, ...]
    selected_candidate: LexicalCandidate | None


@dataclass(frozen=True)
class ContextualLexicalAnalysis:
    source_ref: str
    source_sha256: str
    resource_id: str
    resource_version: str
    analyzer_version: str
    tokens: tuple[ContextualTokenResult, ...]


class ContextualLexicalRanker:
    """Rank existing POS candidates using conservative adjacent-token evidence.

    This component is advisory: it never creates lexical candidates, changes
    the source, or resolves two senses that receive equal contextual evidence.
    Downstream syntax/semantic stages do not consume these rankings yet.
    """

    def __init__(self, minimum_score_margin: int = 1):
        if isinstance(minimum_score_margin, bool) or not isinstance(minimum_score_margin, int):
            raise TypeError("minimum_score_margin must be an integer")
        if minimum_score_margin < 1:
            raise ValueError("minimum_score_margin must be positive")
        self.minimum_score_margin = minimum_score_margin

    @staticmethod
    def _pos(item) -> set[str]:
        return {candidate.part_of_speech for candidate in item.candidates}

    @staticmethod
    def _score(candidate: LexicalCandidate, left_pos: set[str], right_pos: set[str]):
        score = 0
        evidence = []
        pos = candidate.part_of_speech
        if pos == "NOUN":
            if "DET" in left_pos:
                score += 2
                evidence.append("LEFT_DETERMINER_SUPPORTS_NOUN")
            if "ADJ" in left_pos:
                score += 1
                evidence.append("LEFT_ADJECTIVE_SUPPORTS_NOUN")
            if "VERB" in right_pos:
                score += 1
                evidence.append("RIGHT_VERB_SUPPORTS_SUBJECT_NOUN")
        elif pos == "VERB":
            if left_pos.intersection({"PRON", "PROPN", "NOUN"}):
                score += 2
                evidence.append("LEFT_NOMINAL_SUPPORTS_VERB")
            if right_pos.intersection({"NOUN", "PROPN", "PRON"}):
                score += 2
                evidence.append("RIGHT_NOMINAL_SUPPORTS_TRANSITIVE_VERB")
        return score, tuple(evidence)

    def analyze(
        self, lexical: LexicalAnalysis, segmented: SegmentedDocument
    ) -> ContextualLexicalAnalysis:
        if not isinstance(lexical, LexicalAnalysis):
            raise TypeError("lexical must be a LexicalAnalysis artifact")
        if not isinstance(segmented, SegmentedDocument):
            raise TypeError("segmented must be a SegmentedDocument artifact")
        if lexical.source != segmented.source:
            raise ValueError("lexical and segmentation inputs must share the exact source")
        previous_word = {}
        next_word = {}
        for clause in segmented.clauses:
            word_positions = [
                index for index, item in enumerate(lexical.tokens)
                if item.token.kind == "WORD"
                and clause.start <= item.token.start
                and item.token.end <= clause.end
            ]
            for offset, index in enumerate(word_positions):
                if offset:
                    previous_word[index] = word_positions[offset - 1]
                if offset + 1 < len(word_positions):
                    next_word[index] = word_positions[offset + 1]

        results = []
        for index, item in enumerate(lexical.tokens):
            if item.token.kind != "WORD":
                results.append(ContextualTokenResult(
                    item.token, "NOT_APPLICABLE", (), None
                ))
                continue
            if not item.candidates:
                results.append(ContextualTokenResult(
                    item.token, "UNRESOLVED", (), None
                ))
                continue
            if len(item.candidates) == 1:
                candidate = item.candidates[0]
                results.append(ContextualTokenResult(
                    item.token, "UNCHANGED",
                    (RankedLexicalCandidate(candidate, 0, ()),), None
                ))
                continue

            left_pos = self._pos(lexical.tokens[previous_word[index]]) if index in previous_word else set()
            right_pos = self._pos(lexical.tokens[next_word[index]]) if index in next_word else set()
            ranked = []
            for candidate in item.candidates:
                score, evidence = self._score(candidate, left_pos, right_pos)
                ranked.append(RankedLexicalCandidate(candidate, score, evidence))
            ranked.sort(key=lambda value: (-value.score, value.candidate.sense_id,
                                           value.candidate.lemma, value.candidate.part_of_speech))
            top_score = ranked[0].score
            second_score = ranked[1].score if len(ranked) > 1 else 0
            if top_score > 0 and top_score - second_score >= self.minimum_score_margin:
                status = "SELECTED"
                selected = ranked[0].candidate
            else:
                status = "AMBIGUOUS"
                selected = None
            results.append(ContextualTokenResult(
                item.token, status, tuple(ranked), selected
            ))

        return ContextualLexicalAnalysis(
            lexical.source.source_id, lexical.source.sha256,
            lexical.resource_id, lexical.resource_version,
            CONTEXTUAL_LEXICAL_VERSION, tuple(results),
        )


__all__ = [
    "CONTEXTUAL_LEXICAL_VERSION", "RankedLexicalCandidate",
    "ContextualTokenResult", "ContextualLexicalAnalysis",
    "ContextualLexicalRanker",
]
