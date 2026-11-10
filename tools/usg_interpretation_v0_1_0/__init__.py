"""Versioned source ingestion and conservative segmentation primitives."""
from .source import (
    LANGUAGE_PROFILES,
    SourceSnapshot,
    TextSegment,
    SegmentedSource,
    ingest_source,
    segment_source,
)

__all__ = [
    "LANGUAGE_PROFILES", "SourceSnapshot", "TextSegment", "SegmentedSource",
    "ingest_source", "segment_source",
]
