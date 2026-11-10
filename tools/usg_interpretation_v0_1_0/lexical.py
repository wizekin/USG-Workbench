"""Versioned lexical and morphology candidates over exact source spans.

No lemma, part of speech, sense, or concept is invented for unknown words.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import unicodedata

from .source import SourceSnapshot

LEXICAL_ANALYSIS_VERSION = "lexical-analysis/0.1.0"


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")


@dataclass(frozen=True)
class Token:
    token_id: str
    surface_text: str
    start: int
    end: int
    kind: Literal["WORD", "NUMBER", "PUNCTUATION", "SYMBOL", "OTHER"]

    def __post_init__(self) -> None:
        _nonempty(self.token_id, "token_id")
        if not isinstance(self.surface_text, str) or not self.surface_text:
            raise ValueError("surface_text must be non-empty")
        if (isinstance(self.start, bool) or not isinstance(self.start, int)
                or isinstance(self.end, bool) or not isinstance(self.end, int)
                or self.start < 0 or self.end <= self.start):
            raise ValueError("token offsets must be zero-based, end-exclusive integers")
        if self.kind not in {"WORD", "NUMBER", "PUNCTUATION", "SYMBOL", "OTHER"}:
            raise ValueError("unsupported token kind")


@dataclass(frozen=True)
class LexicalEntry:
    language: str
    form: str
    lemma: str
    part_of_speech: str
    sense_id: str
    morphology: tuple[tuple[str, str], ...] = ()
    concept_ref: str | None = None

    def __post_init__(self) -> None:
        if self.language not in {"en", "ar"}:
            raise ValueError("lexical entry language must be en or ar")
        for field, value in (
            ("form", self.form), ("lemma", self.lemma),
            ("part_of_speech", self.part_of_speech), ("sense_id", self.sense_id),
        ):
            _nonempty(value, field)
        if not isinstance(self.morphology, tuple):
            raise TypeError("morphology must be an ordered tuple of key/value pairs")
        if any(not isinstance(pair, tuple) or len(pair) != 2
               or not all(isinstance(part, str) and part for part in pair)
               for pair in self.morphology):
            raise ValueError("morphology entries must be non-empty string pairs")
        if self.concept_ref is not None:
            _nonempty(self.concept_ref, "concept_ref")


@dataclass(frozen=True)
class LexicalResource:
    resource_id: str
    version: int
    entries: tuple[LexicalEntry, ...]

    def __post_init__(self) -> None:
        _nonempty(self.resource_id, "resource_id")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise ValueError("resource version must be a positive integer")
        if not isinstance(self.entries, tuple) or any(not isinstance(x, LexicalEntry) for x in self.entries):
            raise TypeError("entries must be an ordered tuple of LexicalEntry")
        identities = [(x.language, _lookup_form(x.language, x.form), x.lemma,
                       x.part_of_speech, x.sense_id) for x in self.entries]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate lexical entry identity")


@dataclass(frozen=True)
class LexicalCandidate:
    lemma: str
    part_of_speech: str
    sense_id: str
    morphology: tuple[tuple[str, str], ...]
    concept_ref: str | None


@dataclass(frozen=True)
class TokenAnalysis:
    token: Token
    status: Literal["RESOLVED", "AMBIGUOUS", "UNRESOLVED", "NOT_APPLICABLE"]
    candidates: tuple[LexicalCandidate, ...]


@dataclass(frozen=True)
class LexicalAnalysis:
    source: SourceSnapshot
    resource_id: str
    resource_version: int
    analyzer_version: str
    tokens: tuple[TokenAnalysis, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tokens, tuple) or any(not isinstance(x, TokenAnalysis) for x in self.tokens):
            raise TypeError("tokens must be an ordered tuple of TokenAnalysis")
        previous_end = 0
        for item in self.tokens:
            token = item.token
            if token.end > len(self.source.text):
                raise ValueError("token span exceeds source length")
            if self.source.text[token.start:token.end] != token.surface_text:
                raise ValueError("token surface does not match its exact source span")
            if token.start < previous_end:
                raise ValueError("tokens must be ordered and non-overlapping")
            previous_end = token.end
            expected = (
                "NOT_APPLICABLE" if token.kind != "WORD" else
                "RESOLVED" if len(item.candidates) == 1 else
                "AMBIGUOUS" if len(item.candidates) > 1 else "UNRESOLVED"
            )
            if item.status != expected:
                raise ValueError("token lexical status does not match candidate count and kind")


def _lookup_form(language: str, form: str) -> str:
    return form.casefold() if language == "en" else form


def _category(char: str) -> str:
    return unicodedata.category(char)


def _is_letter_or_mark(char: str) -> bool:
    return _category(char)[0] in {"L", "M"}


def _is_number(char: str) -> bool:
    return _category(char)[0] == "N"


def tokenize(source: SourceSnapshot) -> tuple[Token, ...]:
    """Tokenize Unicode text while retaining exact surface strings and offsets.

    Apostrophes are retained inside alphabetic tokens when surrounded by
    letters. Hyphens, clitics, and language-specific morphological segmentation
    are deliberately not inferred in this version.
    """
    if not isinstance(source, SourceSnapshot):
        raise TypeError("source must be a SourceSnapshot")
    text = source.text
    tokens: list[Token] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        start = index
        if _is_letter_or_mark(char):
            index += 1
            while index < len(text):
                current = text[index]
                if _is_letter_or_mark(current):
                    index += 1
                    continue
                if (current in {"'", "’"} and index + 1 < len(text)
                        and _is_letter_or_mark(text[index + 1])
                        and _category(text[index - 1])[0] == "L"):
                    index += 1
                    continue
                break
            kind = "WORD"
        elif _is_number(char):
            index += 1
            while index < len(text) and _is_number(text[index]):
                index += 1
            kind = "NUMBER"
        else:
            index += 1
            category = _category(char)[0]
            kind = "PUNCTUATION" if category == "P" else "SYMBOL" if category == "S" else "OTHER"
        tokens.append(Token(
            token_id=f"t{len(tokens)}",
            surface_text=text[start:index],
            start=start,
            end=index,
            kind=kind,
        ))
    return tuple(tokens)


class LexicalAnalyzer:
    """Resolve tokens only against an explicitly supplied, versioned resource."""

    def __init__(self, resource: LexicalResource):
        if not isinstance(resource, LexicalResource):
            raise TypeError("resource must be a LexicalResource")
        self.resource = resource
        index: dict[tuple[str, str], list[LexicalEntry]] = {}
        for entry in resource.entries:
            key = (entry.language, _lookup_form(entry.language, entry.form))
            index.setdefault(key, []).append(entry)
        self._index = {key: tuple(value) for key, value in index.items()}

    def analyze(self, source: SourceSnapshot) -> LexicalAnalysis:
        if not isinstance(source, SourceSnapshot):
            raise TypeError("source must be a SourceSnapshot")
        token_results: list[TokenAnalysis] = []
        for token in tokenize(source):
            if token.kind != "WORD":
                token_results.append(TokenAnalysis(token, "NOT_APPLICABLE", ()))
                continue
            key = (source.language, _lookup_form(source.language, token.surface_text))
            entries = self._index.get(key, ())
            candidates = tuple(
                LexicalCandidate(
                    lemma=entry.lemma,
                    part_of_speech=entry.part_of_speech,
                    sense_id=entry.sense_id,
                    morphology=entry.morphology,
                    concept_ref=entry.concept_ref,
                )
                for entry in entries
            )
            status = "RESOLVED" if len(candidates) == 1 else "AMBIGUOUS" if candidates else "UNRESOLVED"
            token_results.append(TokenAnalysis(token, status, candidates))
        return LexicalAnalysis(
            source=source,
            resource_id=self.resource.resource_id,
            resource_version=self.resource.version,
            analyzer_version=LEXICAL_ANALYSIS_VERSION,
            tokens=tuple(token_results),
        )


__all__ = [
    "LEXICAL_ANALYSIS_VERSION", "Token", "LexicalEntry", "LexicalResource",
    "LexicalCandidate", "TokenAnalysis", "LexicalAnalysis", "tokenize",
    "LexicalAnalyzer",
]
