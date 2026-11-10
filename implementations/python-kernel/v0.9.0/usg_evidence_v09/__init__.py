"""Versioned native Evidence model for USG-SEM/1.0.

Evidence records preserve source-grounded spans and quotes alongside two
independent assessments: textual alignment and semantic support. Exact source
alignment is not entailment, corroboration, or proof of truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

MODEL_VERSION = "0.9.0"


class ReferenceSpace(str, Enum):
    EVIDENCE = "EVIDENCE"
    SOURCE = "SOURCE"


class AlignmentStatus(str, Enum):
    EXACT = "EXACT"
    MISMATCH = "MISMATCH"
    UNVERIFIED = "UNVERIFIED"


class SemanticSupportStatus(str, Enum):
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    PROPOSED = "PROPOSED"
    RULE_SUPPORTED = "RULE_SUPPORTED"
    CORROBORATED = "CORROBORATED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, order=True)
class TypedReference:
    """Opaque external ID plus explicit target space; never parse ID text."""
    space: ReferenceSpace
    external_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.space, ReferenceSpace):
            raise TypeError("reference space must be a ReferenceSpace")
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("reference external_id must be a non-empty string")


@dataclass(frozen=True)
class EvidenceSpan:
    """Zero-based, end-exclusive Unicode code-point source span."""
    source_ref: TypedReference
    start: int
    end: int
    offset_unit: str = "unicode_code_point"

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, TypedReference) or self.source_ref.space is not ReferenceSpace.SOURCE:
            raise ValueError("span source_ref must be a typed SOURCE reference")
        if isinstance(self.start, bool) or not isinstance(self.start, int) or self.start < 0:
            raise ValueError("span start must be a non-negative integer")
        if isinstance(self.end, bool) or not isinstance(self.end, int) or self.end <= self.start:
            raise ValueError("span end must be an integer greater than start")
        if self.offset_unit != "unicode_code_point":
            raise ValueError("offset_unit must be unicode_code_point")


@dataclass(frozen=True)
class NativeEvidenceV09:
    """A source-grounded evidence record, not a truth or entailment judgment."""
    external_id: str
    source_ref: TypedReference
    span: EvidenceSpan
    quote: str
    alignment_status: AlignmentStatus
    semantic_support_status: SemanticSupportStatus
    supporting_rule_refs: Tuple[str, ...] = ()
    native_verification_meaning: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("evidence external_id must be a non-empty opaque ID")
        if not isinstance(self.source_ref, TypedReference) or self.source_ref.space is not ReferenceSpace.SOURCE:
            raise ValueError("source_ref must be a typed SOURCE reference")
        if not isinstance(self.span, EvidenceSpan):
            raise TypeError("span must be EvidenceSpan")
        if self.span.source_ref != self.source_ref:
            raise ValueError("evidence source_ref and span source_ref must match")
        if not isinstance(self.quote, str):
            raise TypeError("quote must be a string")
        if not isinstance(self.alignment_status, AlignmentStatus):
            raise TypeError("alignment_status must be AlignmentStatus")
        if not isinstance(self.semantic_support_status, SemanticSupportStatus):
            raise TypeError("semantic_support_status must be SemanticSupportStatus")
        if not isinstance(self.supporting_rule_refs, tuple):
            raise TypeError("supporting_rule_refs must be an ordered tuple")
        for ref in self.supporting_rule_refs:
            if not isinstance(ref, str) or not ref:
                raise ValueError("supporting rule references must be non-empty opaque strings")
        if self.native_verification_meaning is not None and not isinstance(self.native_verification_meaning, str):
            raise TypeError("native_verification_meaning must be a string or None")


def same_evidence(left: NativeEvidenceV09, right: NativeEvidenceV09) -> bool:
    """Evidence identity is its opaque record ID, not quote or source equality."""
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "ReferenceSpace", "AlignmentStatus",
    "SemanticSupportStatus", "TypedReference", "EvidenceSpan",
    "NativeEvidenceV09", "same_evidence",
]
