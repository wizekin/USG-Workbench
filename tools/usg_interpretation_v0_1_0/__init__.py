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

from .compose import (
    SEMANTIC_COMPOSITION_VERSION, PredicateFrame, SemanticFrameRegistry,
    SemanticNode, SemanticCandidate, SemanticComposition, SemanticComposer,
    initial_semantic_frame_registry,
)

from .mentions import (
    REFERENCE_ANALYSIS_VERSION, Mention, ReferentCandidate,
    MentionAnalysis, MentionAnalyzer,
)

from .discourse import (
    DISCOURSE_ANALYSIS_VERSION, DiscourseMarker, DiscourseRegistry,
    DiscourseLink, DiscourseAnalysis, DiscourseAnalyzer, initial_discourse_registry,
)

from .assertion_evidence import (
    ASSERTION_EVIDENCE_ADAPTER_VERSION, AssertionEvidenceProjection,
    project_assertions_and_evidence,
)

from .resources import (
    RESOURCE_REGISTRY_VERSION, ResourceDescriptor, SemanticAssociation,
    SemanticResourceRegistry,
)

__all__ = [
    "LANGUAGE_PROFILES", "SourceSnapshot", "TextSegment", "SegmentedSource",
    "ingest_source", "segment_source", "LEXICAL_ANALYSIS_VERSION", "Token",
    "LexicalEntry", "LexicalResource", "LexicalCandidate", "TokenAnalysis",
    "LexicalAnalysis", "tokenize", "LexicalAnalyzer", "SYNTAX_ANALYSIS_VERSION",
    "GrammarPattern", "GrammarRegistry", "SyntaxCandidate", "SyntaxAnalysis",
    "GrammarAnalyzer", "initial_grammar_registry", "SEMANTIC_COMPOSITION_VERSION",
    "PredicateFrame", "SemanticFrameRegistry", "SemanticNode", "SemanticCandidate",
    "SemanticComposition", "SemanticComposer", "initial_semantic_frame_registry", "REFERENCE_ANALYSIS_VERSION", "Mention",
    "ReferentCandidate", "MentionAnalysis", "MentionAnalyzer", "DISCOURSE_ANALYSIS_VERSION",
    "DiscourseMarker", "DiscourseRegistry", "DiscourseLink", "DiscourseAnalysis",
    "DiscourseAnalyzer", "initial_discourse_registry",
    "ASSERTION_EVIDENCE_ADAPTER_VERSION", "AssertionEvidenceProjection",
    "project_assertions_and_evidence", "RESOURCE_REGISTRY_VERSION",
    "ResourceDescriptor", "SemanticAssociation", "SemanticResourceRegistry",
]
