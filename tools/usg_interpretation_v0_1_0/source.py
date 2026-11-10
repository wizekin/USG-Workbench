"""Immutable source snapshots and conservative, span-preserving segmentation.

Offsets are Python Unicode code-point offsets, zero-based and end-exclusive.
The source string is never normalized or rewritten.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Literal
from uuid import uuid4

PIPELINE_CONTRACT = "USG-INTERPRET/0.1.0"
SEGMENTATION_VERSION = "source-segmentation/0.1.0"
LANGUAGE_PROFILES = {
    "en": "en-standard-written/0.1.0",
    "ar": "ar-msa-written/0.1.0",
}
_SENTENCE_END = frozenset(".!?؟。")
_CLAUSE_END = frozenset(";؛；")
_CLOSERS = frozenset("\"'”’»)]}")


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: str
    text: str
    language: str
    language_profile: str
    sha256: str
    pipeline_contract: str = PIPELINE_CONTRACT

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.text, str):
            raise TypeError("source text must be a string")
        if self.language not in LANGUAGE_PROFILES:
            raise ValueError("language must be one of the declared profiles: en, ar")
        if self.language_profile != LANGUAGE_PROFILES[self.language]:
            raise ValueError("language_profile does not match the declared language")
        expected = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        if self.sha256 != expected:
            raise ValueError("source sha256 does not match the exact UTF-8 source text")


@dataclass(frozen=True)
class TextSegment:
    segment_id: str
    kind: Literal["paragraph", "sentence", "clause"]
    start: int
    end: int
    parent_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.segment_id, str) or not self.segment_id:
            raise ValueError("segment_id must be non-empty")
        if self.kind not in {"paragraph", "sentence", "clause"}:
            raise ValueError("unsupported segment kind")
        if (isinstance(self.start, bool) or not isinstance(self.start, int)
                or isinstance(self.end, bool) or not isinstance(self.end, int)
                or self.start < 0 or self.end < self.start):
            raise ValueError("segment offsets must be non-negative ordered integers")


@dataclass(frozen=True)
class SegmentedSource:
    source: SourceSnapshot
    paragraphs: tuple[TextSegment, ...]
    sentences: tuple[TextSegment, ...]
    clauses: tuple[TextSegment, ...]
    segmentation_version: str = SEGMENTATION_VERSION

    def __post_init__(self) -> None:
        for group in (self.paragraphs, self.sentences, self.clauses):
            if not isinstance(group, tuple) or any(not isinstance(x, TextSegment) for x in group):
                raise TypeError("segments must be ordered tuples of TextSegment")
            for item in group:
                if item.end > len(self.source.text):
                    raise ValueError("segment end exceeds source length")
                if item.start == item.end:
                    raise ValueError("empty segments are not emitted")
        paragraph_ids = {x.segment_id for x in self.paragraphs}
        sentence_ids = {x.segment_id for x in self.sentences}
        if any(x.parent_id not in paragraph_ids for x in self.sentences):
            raise ValueError("every sentence must reference an existing paragraph")
        if any(x.parent_id not in sentence_ids for x in self.clauses):
            raise ValueError("every clause must reference an existing sentence")


def ingest_source(text: str, language: str, *, source_id: str | None = None) -> SourceSnapshot:
    """Capture exact source bytes and declared language without normalization."""
    if not isinstance(text, str):
        raise TypeError("source text must be a string")
    if language not in LANGUAGE_PROFILES:
        raise ValueError("language must be 'en' or 'ar'")
    return SourceSnapshot(
        source_id=source_id or "src:" + uuid4().hex,
        text=text,
        language=language,
        language_profile=LANGUAGE_PROFILES[language],
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _trim_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if start < end else None


def _paragraph_spans(text: str) -> list[tuple[int, int]]:
    # Blank lines delimit paragraphs. CRLF is consumed as one line break;
    # single newlines remain inside a paragraph.
    spans: list[tuple[int, int]] = []
    cursor = 0
    for match in re.finditer(r"(?:\r\n|\r|\n)[ \t]*(?:(?:\r\n|\r|\n)[ \t]*)+", text):
        span = _trim_span(text, cursor, match.start())
        if span:
            spans.append(span)
        cursor = match.end()
    span = _trim_span(text, cursor, len(text))
    if span:
        spans.append(span)
    return spans


def _sentence_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = start
    index = start
    while index < end:
        if text[index] in _SENTENCE_END:
            boundary = index + 1
            while boundary < end and text[boundary] in _SENTENCE_END:
                boundary += 1
            while boundary < end and text[boundary] in _CLOSERS:
                boundary += 1
            if boundary == end or text[boundary].isspace():
                span = _trim_span(text, cursor, boundary)
                if span:
                    spans.append(span)
                cursor = boundary
                index = boundary
                continue
        index += 1
    span = _trim_span(text, cursor, end)
    if span:
        spans.append(span)
    return spans


def _clause_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    # Conservative segmentation: only explicit semicolon-family separators
    # split clause candidates. Commas and conjunctions are not guessed.
    spans: list[tuple[int, int]] = []
    cursor = start
    for index in range(start, end):
        if text[index] in _CLAUSE_END:
            span = _trim_span(text, cursor, index + 1)
            if span:
                spans.append(span)
            cursor = index + 1
    span = _trim_span(text, cursor, end)
    if span:
        spans.append(span)
    return spans


def segment_source(source: SourceSnapshot) -> SegmentedSource:
    """Produce nested paragraph/sentence/clause spans over the exact snapshot.

    This stage performs boundary segmentation only. It does not claim that a
    sentence boundary is a syntactic clause boundary or that segmentation
    establishes grammatical or semantic correctness.
    """
    if not isinstance(source, SourceSnapshot):
        raise TypeError("source must be a SourceSnapshot")

    paragraphs: list[TextSegment] = []
    sentences: list[TextSegment] = []
    clauses: list[TextSegment] = []
    for p_index, (p_start, p_end) in enumerate(_paragraph_spans(source.text)):
        p_id = f"p{p_index}"
        paragraphs.append(TextSegment(p_id, "paragraph", p_start, p_end, None))
        for s_index, (s_start, s_end) in enumerate(_sentence_spans(source.text, p_start, p_end)):
            s_id = f"{p_id}.s{s_index}"
            sentences.append(TextSegment(s_id, "sentence", s_start, s_end, p_id))
            for c_index, (c_start, c_end) in enumerate(_clause_spans(source.text, s_start, s_end)):
                clauses.append(TextSegment(f"{s_id}.c{c_index}", "clause",
                                           c_start, c_end, s_id))
    return SegmentedSource(source, tuple(paragraphs), tuple(sentences), tuple(clauses))
