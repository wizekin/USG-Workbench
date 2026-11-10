"""Explicit discourse-marker detection with source-grounded candidate links."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .source import SegmentedSource
from .lexical import LexicalAnalysis

DISCOURSE_ANALYSIS_VERSION = "discourse-analysis/0.1.0"


@dataclass(frozen=True)
class DiscourseMarker:
    language: str
    surface: str
    relation: Literal["CONTRAST", "CONDITION", "CAUSE", "TEMPORAL", "ATTRIBUTION"]
    marker_id: str

    def __post_init__(self):
        if self.language not in {"en", "ar"} or not self.surface or not self.marker_id:
            raise ValueError("marker language, surface, and ID are required")


@dataclass(frozen=True)
class DiscourseRegistry:
    registry_id: str
    version: int
    markers: tuple[DiscourseMarker, ...]

    def __post_init__(self):
        if not self.registry_id or isinstance(self.version, bool) or self.version < 1:
            raise ValueError("registry id and positive version are required")
        if not isinstance(self.markers, tuple) or any(not isinstance(x, DiscourseMarker) for x in self.markers):
            raise TypeError("markers must be an ordered tuple of DiscourseMarker")


@dataclass(frozen=True)
class DiscourseLink:
    link_id: str
    relation: str
    marker_id: str
    marker_text: str
    marker_span: tuple[int, int]
    source_sentence_ref: str
    target_sentence_ref: str | None
    status: Literal["MARKER_DETECTED", "UNRESOLVED"]


@dataclass(frozen=True)
class DiscourseAnalysis:
    links: tuple[DiscourseLink, ...]
    analyzer_version: str = DISCOURSE_ANALYSIS_VERSION


class DiscourseAnalyzer:
    """Detect registered connective forms; never infer missing discourse links."""

    def __init__(self, registry: DiscourseRegistry):
        self.registry = registry

    def analyze(self, segmented: SegmentedSource, lexical: LexicalAnalysis) -> DiscourseAnalysis:
        if segmented.source != lexical.source:
            raise ValueError("segmentation and lexical analysis must reference the same source")
        sentence_for_token = {}
        for sentence in segmented.sentences:
            for item in lexical.tokens:
                if sentence.start <= item.token.start and item.token.end <= sentence.end:
                    sentence_for_token[item.token.token_id] = sentence
        markers = {(x.language, x.surface.casefold() if x.language == "en" else x.surface): x
                   for x in self.registry.markers}
        links = []
        for item in lexical.tokens:
            if item.token.kind != "WORD":
                continue
            key = (lexical.source.language,
                   item.token.surface_text.casefold() if lexical.source.language == "en"
                   else item.token.surface_text)
            marker = markers.get(key)
            if marker is None:
                continue
            sentence = sentence_for_token.get(item.token.token_id)
            if sentence is None:
                continue
            index = next(i for i, x in enumerate(segmented.sentences)
                         if x.segment_id == sentence.segment_id)
            target = segmented.sentences[index - 1] if index > 0 else None
            links.append(DiscourseLink(
                f"disc:{item.token.token_id}", marker.relation, marker.marker_id,
                item.token.surface_text, (item.token.start, item.token.end),
                target.segment_id if target else sentence.segment_id,
                sentence.segment_id if target else None,
                "MARKER_DETECTED" if target else "UNRESOLVED",
            ))
        return DiscourseAnalysis(tuple(links))


def initial_discourse_registry() -> DiscourseRegistry:
    return DiscourseRegistry("usg-initial-discourse-markers", 1, (
        DiscourseMarker("en", "however", "CONTRAST", "en:however"),
        DiscourseMarker("en", "but", "CONTRAST", "en:but"),
        DiscourseMarker("en", "if", "CONDITION", "en:if"),
        DiscourseMarker("en", "because", "CAUSE", "en:because"),
        DiscourseMarker("en", "then", "TEMPORAL", "en:then"),
        DiscourseMarker("en", "said", "ATTRIBUTION", "en:said"),
        DiscourseMarker("ar", "لكن", "CONTRAST", "ar:but"),
        DiscourseMarker("ar", "إذا", "CONDITION", "ar:if"),
        DiscourseMarker("ar", "لأن", "CAUSE", "ar:because"),
        DiscourseMarker("ar", "ثم", "TEMPORAL", "ar:then"),
        DiscourseMarker("ar", "قال", "ATTRIBUTION", "ar:said"),
    ))


__all__ = ["DISCOURSE_ANALYSIS_VERSION", "DiscourseMarker", "DiscourseRegistry",
           "DiscourseLink", "DiscourseAnalysis", "DiscourseAnalyzer",
           "initial_discourse_registry"]
