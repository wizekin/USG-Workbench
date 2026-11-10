"""Small, explicit grammar-pattern matcher; syntax is not semantic truth."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .lexical import LexicalAnalysis, TokenAnalysis

SYNTAX_ANALYSIS_VERSION = "syntax-analysis/0.1.0"
NOMINAL = frozenset({"NOUN", "PROPN", "PRON"})
VERBAL = frozenset({"VERB"})


@dataclass(frozen=True)
class GrammarPattern:
    pattern_id: str
    language: str
    slots: tuple[tuple[str, frozenset[str]], ...]
    roles: tuple[tuple[str, int], ...]

    def __post_init__(self):
        if not self.pattern_id or self.language not in {"en", "ar"}:
            raise ValueError("pattern id and supported language are required")
        if not self.slots or not self.roles:
            raise ValueError("patterns require slots and grammatical roles")
        if any(not kinds for _, kinds in self.slots):
            raise ValueError("every grammar slot needs at least one POS category")
        if any(index < 0 or index >= len(self.slots) for _, index in self.roles):
            raise ValueError("role slot index is outside pattern")


@dataclass(frozen=True)
class GrammarRegistry:
    registry_id: str
    version: int
    patterns: tuple[GrammarPattern, ...]

    def __post_init__(self):
        if not self.registry_id or isinstance(self.version, bool) or self.version < 1:
            raise ValueError("registry id and positive version are required")
        if not isinstance(self.patterns, tuple) or any(not isinstance(x, GrammarPattern) for x in self.patterns):
            raise TypeError("patterns must be an ordered tuple of GrammarPattern")
        ids = [x.pattern_id for x in self.patterns]
        if len(ids) != len(set(ids)):
            raise ValueError("grammar pattern ids must be unique")


@dataclass(frozen=True)
class SyntaxCandidate:
    candidate_id: str
    pattern_id: str
    language: str
    token_ids: tuple[str, ...]
    roles: tuple[tuple[str, tuple[str, ...]], ...]
    start: int
    end: int


@dataclass(frozen=True)
class SyntaxAnalysis:
    status: Literal["PARSED", "AMBIGUOUS", "UNSUPPORTED", "INCOMPLETE"]
    candidates: tuple[SyntaxCandidate, ...]
    unresolved_token_ids: tuple[str, ...]
    analyzer_version: str = SYNTAX_ANALYSIS_VERSION


def _pos(item: TokenAnalysis) -> frozenset[str]:
    return frozenset(x.part_of_speech.upper() for x in item.candidates)


class GrammarAnalyzer:
    """Matches only registered POS patterns; it never invents parse trees."""

    def __init__(self, registry: GrammarRegistry):
        if not isinstance(registry, GrammarRegistry):
            raise TypeError("registry must be GrammarRegistry")
        self.registry = registry

    def analyze(self, lexical: LexicalAnalysis) -> SyntaxAnalysis:
        if not isinstance(lexical, LexicalAnalysis):
            raise TypeError("lexical must be LexicalAnalysis")
        words = [x for x in lexical.tokens if x.token.kind == "WORD"]
        unresolved = tuple(x.token.token_id for x in words if x.status != "RESOLVED")
        if not words:
            return SyntaxAnalysis("UNSUPPORTED", (), unresolved)
        if unresolved:
            return SyntaxAnalysis("INCOMPLETE", (), unresolved)
        matches: list[SyntaxCandidate] = []
        for pattern in self.registry.patterns:
            if pattern.language != lexical.source.language or len(pattern.slots) != len(words):
                continue
            if not all(_pos(item).intersection(allowed) for item, (_, allowed)
                       in zip(words, pattern.slots)):
                continue
            role_bindings = tuple(
                (role, (words[index].token.token_id,))
                for role, index in pattern.roles
            )
            matches.append(SyntaxCandidate(
                candidate_id=f"syn:{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                language=pattern.language,
                token_ids=tuple(x.token.token_id for x in words),
                roles=role_bindings,
                start=words[0].token.start,
                end=words[-1].token.end,
            ))
        if not matches:
            return SyntaxAnalysis("UNSUPPORTED", (), ())
        return SyntaxAnalysis("PARSED" if len(matches) == 1 else "AMBIGUOUS",
                              tuple(matches), ())


def initial_grammar_registry() -> GrammarRegistry:
    """A tiny fixture-grade registry; expand only with benchmark-backed patterns."""
    return GrammarRegistry("usg-initial-grammar", 1, (
        GrammarPattern("en.svo.v1", "en", (
            ("subject", NOMINAL), ("predicate", VERBAL), ("object", NOMINAL),
        ), (("SUBJECT", 0), ("PREDICATE", 1), ("OBJECT", 2))),
        GrammarPattern("ar.svo.v1", "ar", (
            ("subject", NOMINAL), ("predicate", VERBAL), ("object", NOMINAL),
        ), (("SUBJECT", 0), ("PREDICATE", 1), ("OBJECT", 2))),
        GrammarPattern("ar.vso.v1", "ar", (
            ("predicate", VERBAL), ("subject", NOMINAL), ("object", NOMINAL),
        ), (("PREDICATE", 0), ("SUBJECT", 1), ("OBJECT", 2))),
    ))


__all__ = ["SYNTAX_ANALYSIS_VERSION", "GrammarPattern", "GrammarRegistry",
           "SyntaxCandidate", "SyntaxAnalysis", "GrammarAnalyzer",
           "initial_grammar_registry"]
