"""Sentence-internal clause segmentation with exact source spans and explicit links."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tools.usg_interpretation_v0_1_0.source import SourceSnapshot
from .lexical import LexicalAnalysis

SEGMENTATION_VERSION = "document-clause-segmentation/0.2.0"
_SENTENCE_END = frozenset(".!?؟。")
_CLOSERS = frozenset("\"'”’»)]}")
_EN_MARKERS = {
    "and": "COORDINATION_AND", "or": "COORDINATION_OR", "but": "CONTRAST",
    "because": "CAUSE", "if": "CONDITION", "when": "TEMPORAL",
    "that": "COMPLEMENT", "then": "TEMPORAL",
}
_AR_MARKERS = {
    "ثم": "TEMPORAL", "إذا": "CONDITION", "لأن": "CAUSE", "أن": "COMPLEMENT",
    "و": "COORDINATION_AND", "أو": "COORDINATION_OR", "لكن": "CONTRAST",
}


@dataclass(frozen=True)
class SentenceSegment:
    segment_id: str
    start: int
    end: int


@dataclass(frozen=True)
class ClauseSegment:
    segment_id: str
    sentence_ref: str
    start: int
    end: int


@dataclass(frozen=True)
class ClauseBoundary:
    boundary_id: str
    relation: str
    marker_text: str
    marker_span: tuple[int, int]
    left_clause_ref: str
    right_clause_ref: str


@dataclass(frozen=True)
class SegmentedDocument:
    source: SourceSnapshot
    sentences: tuple[SentenceSegment, ...]
    clauses: tuple[ClauseSegment, ...]
    boundaries: tuple[ClauseBoundary, ...]
    segmentation_version: str = SEGMENTATION_VERSION

    def __post_init__(self):
        if not isinstance(self.source, SourceSnapshot):
            raise TypeError("source must be a SourceSnapshot")
        sentence_ids = {x.segment_id for x in self.sentences}
        clause_ids = {x.segment_id for x in self.clauses}
        for item in (*self.sentences, *self.clauses):
            if item.start < 0 or item.end <= item.start or item.end > len(self.source.text):
                raise ValueError("segment span is outside the exact source")
            if self.source.text[item.start:item.end].strip() == "":
                raise ValueError("empty source segments are not allowed")
        for item in self.clauses:
            if item.sentence_ref not in sentence_ids:
                raise ValueError("clause references an unknown sentence")
        for item in self.boundaries:
            if (item.left_clause_ref not in clause_ids or item.right_clause_ref not in clause_ids
                    or item.left_clause_ref == item.right_clause_ref):
                raise ValueError("clause boundary references are invalid")
            start, end = item.marker_span
            if start < 0 or end <= start or end > len(self.source.text):
                raise ValueError("boundary marker span is invalid")
            if self.source.text[start:end] != item.marker_text:
                raise ValueError("boundary marker does not match exact source")


def _trim(text: str, start: int, end: int) -> tuple[int, int] | None:
    while start < end and (text[start].isspace() or text[start] == ","):
        start += 1
    while end > start and (text[end - 1].isspace() or text[end - 1] == ","):
        end -= 1
    return (start, end) if start < end else None


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    cursor = 0
    index = 0
    while index < len(text):
        if text[index] in _SENTENCE_END:
            end = index + 1
            while end < len(text) and text[end] in _SENTENCE_END:
                end += 1
            while end < len(text) and text[end] in _CLOSERS:
                end += 1
            if end == len(text) or text[end].isspace():
                span = _trim(text, cursor, end)
                if span:
                    spans.append(span)
                cursor = end
                index = end
                continue
        index += 1
    span = _trim(text, cursor, len(text))
    if span:
        spans.append(span)
    return spans


def _has_verb(tokens, start: int, end: int) -> bool:
    return any(
        start <= item.token.start and item.token.end <= end
        and any(candidate.part_of_speech == "VERB" for candidate in item.candidates)
        for item in tokens if item.token.kind == "WORD"
    )


def segment_document(lexical: LexicalAnalysis) -> SegmentedDocument:
    """Segment sentences and only explicit clause boundaries with verb evidence.

    Conjunctions/subordinators are treated as boundary candidates only when
    both sides contain a lexically supported verb. This is conservative
    segmentation, not a full dependency parser.
    """
    if not isinstance(lexical, LexicalAnalysis):
        raise TypeError("lexical must be a LexicalAnalysis")
    source = lexical.source
    sentences = []
    clauses = []
    boundaries = []
    marker_map = _EN_MARKERS if source.language == "en" else _AR_MARKERS

    for s_index, (s_start, s_end) in enumerate(_sentence_spans(source.text)):
        sentence_id = f"s{s_index}"
        sentences.append(SentenceSegment(sentence_id, s_start, s_end))
        candidates = []
        for item in lexical.tokens:
            token = item.token
            if token.start < s_start or token.end > s_end:
                continue
            if token.kind == "PUNCTUATION" and token.surface_text in {";", "؛"}:
                if _trim(source.text, s_start, token.start) and _trim(source.text, token.end, s_end):
                    candidates.append((token.start, token.end, token.surface_text, "CLAUSE_SEQUENCE"))
            elif token.kind == "WORD":
                key = token.surface_text.casefold() if source.language == "en" else token.surface_text
                relation = marker_map.get(key)
                if relation is None:
                    continue
                if (_has_verb(lexical.tokens, s_start, token.start)
                        and _has_verb(lexical.tokens, token.end, s_end)):
                    candidates.append((token.start, token.end, token.surface_text, relation))
        candidates.sort(key=lambda x: (x[0], x[1]))
        accepted = []
        last_end = s_start
        for candidate in candidates:
            if candidate[0] <= last_end:
                continue
            if not _trim(source.text, last_end, candidate[0]):
                continue
            if not _trim(source.text, candidate[1], s_end):
                continue
            accepted.append(candidate)
            last_end = candidate[1]

        cursor = s_start
        local_clause_ids = []
        local_boundaries = []
        for c_index, (marker_start, marker_end, marker_text, relation) in enumerate(accepted):
            span = _trim(source.text, cursor, marker_start)
            if span:
                clause_id = f"{sentence_id}.c{len(local_clause_ids)}"
                clauses.append(ClauseSegment(clause_id, sentence_id, *span))
                local_clause_ids.append(clause_id)
            cursor = marker_end
            local_boundaries.append((relation, marker_text, (marker_start, marker_end)))
        span = _trim(source.text, cursor, s_end)
        if span:
            clause_id = f"{sentence_id}.c{len(local_clause_ids)}"
            clauses.append(ClauseSegment(clause_id, sentence_id, *span))
            local_clause_ids.append(clause_id)
        for b_index, (relation, marker_text, marker_span) in enumerate(local_boundaries):
            if b_index + 1 >= len(local_clause_ids):
                continue
            boundaries.append(ClauseBoundary(
                f"{sentence_id}.b{b_index}", relation, marker_text, marker_span,
                local_clause_ids[b_index], local_clause_ids[b_index + 1],
            ))

    return SegmentedDocument(source, tuple(sentences), tuple(clauses), tuple(boundaries))


__all__ = [
    "SEGMENTATION_VERSION", "SentenceSegment", "ClauseSegment", "ClauseBoundary",
    "SegmentedDocument", "segment_document",
]
