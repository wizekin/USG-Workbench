"""Versioned native Mention model for USG-SEM/1.0.

A Mention is a textual occurrence, not a Referent. All links are explicit,
typed, opaque references. This package makes no coreference inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

MODEL_VERSION = "0.7.0"


class MentionResolutionStatus(str, Enum):
    LINKED = "LINKED"
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class ReferenceSpace(str, Enum):
    MENTION = "MENTION"
    REFERENT = "REFERENT"
    SOURCE = "SOURCE"


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
class NativeMentionV07:
    """A textual occurrence with independent resolution and explicit links."""
    external_id: str
    surface_text: str
    resolution_status: MentionResolutionStatus
    mention_type: Optional[str] = None
    referent_ref: Optional[TypedReference] = None
    antecedent_mention_ref: Optional[TypedReference] = None
    antecedent_referent_ref: Optional[TypedReference] = None
    source_ref: Optional[TypedReference] = None
    source_span: Optional[Tuple[int, int]] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("mention external_id must be a non-empty opaque ID")
        if not isinstance(self.surface_text, str):
            raise TypeError("surface_text must be a string")
        if not isinstance(self.resolution_status, MentionResolutionStatus):
            raise TypeError("resolution_status must be MentionResolutionStatus")
        if self.mention_type is not None and not isinstance(self.mention_type, str):
            raise TypeError("mention_type must be a string or None")
        if self.referent_ref is not None:
            if (not isinstance(self.referent_ref, TypedReference)
                    or self.referent_ref.space is not ReferenceSpace.REFERENT):
                raise ValueError("referent_ref must be a typed REFERENT reference")
        if self.antecedent_mention_ref is not None:
            if (not isinstance(self.antecedent_mention_ref, TypedReference)
                    or self.antecedent_mention_ref.space is not ReferenceSpace.MENTION):
                raise ValueError("antecedent_mention_ref must be a typed MENTION reference")
        if self.antecedent_referent_ref is not None:
            if (not isinstance(self.antecedent_referent_ref, TypedReference)
                    or self.antecedent_referent_ref.space is not ReferenceSpace.REFERENT):
                raise ValueError("antecedent_referent_ref must be a typed REFERENT reference")
        if self.source_ref is not None:
            if (not isinstance(self.source_ref, TypedReference)
                    or self.source_ref.space is not ReferenceSpace.SOURCE):
                raise ValueError("source_ref must be a typed SOURCE reference")
        if self.source_span is not None:
            if self.source_ref is None:
                raise ValueError("source_span requires an explicit source_ref")
            if (not isinstance(self.source_span, tuple) or len(self.source_span) != 2
                    or any(not isinstance(x, int) or isinstance(x, bool) for x in self.source_span)
                    or self.source_span[0] < 0 or self.source_span[1] < self.source_span[0]):
                raise ValueError("source_span must be a non-negative (start, end) code-point pair")


def same_mention(left: NativeMentionV07, right: NativeMentionV07) -> bool:
    """Occurrence identity is its opaque Mention ID, never surface text."""
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "MentionResolutionStatus", "ReferenceSpace",
    "TypedReference", "NativeMentionV07", "same_mention",
]
