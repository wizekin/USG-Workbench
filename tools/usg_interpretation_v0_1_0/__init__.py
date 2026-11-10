"""Versioned source ingestion, segmentation, and lexical analysis primitives."""
from .source import (
    LANGUAGE_PROFILES, SourceSnapshot, TextSegment, SegmentedSource,
    ingest_source, segment_source,
)
from .lexical import (
    LEXICAL_ANALYSIS_VERSION, Token, LexicalEntry, LexicalResource,
    LexicalCandidate, TokenAnalysis, LexicalAnalysis, tokenize, LexicalAnalyzer,
)

from .syntax import (
    SYNTAX_ANALYSIS_VERSION, GrammarPattern, GrammarRegistry,
    SyntaxCandidate, SyntaxAnalysis, GrammarAnalyzer, initial_grammar_registry,
)

__all__ = [
    "LANGUAGE_PROFILES", "SourceSnapshot", "TextSegment", "SegmentedSource",
    "ingest_source", "segment_source", "LEXICAL_ANALYSIS_VERSION", "Token",
    "LexicalEntry", "LexicalResource", "LexicalCandidate", "TokenAnalysis",
    "LexicalAnalysis", "tokenize", "LexicalAnalyzer", "SYNTAX_ANALYSIS_VERSION",
    "GrammarPattern", "GrammarRegistry", "SyntaxCandidate", "SyntaxAnalysis",
    "GrammarAnalyzer", "initial_grammar_registry",
]
