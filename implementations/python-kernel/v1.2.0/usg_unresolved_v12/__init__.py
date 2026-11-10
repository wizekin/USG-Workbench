"""Versioned native UnresolvedItem model for USG-SEM/1.0."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

MODEL_VERSION = "1.2.0"


class UnresolvedStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTING = "CONFLICTING"
    RESOURCE_INTERRUPTED = "RESOURCE_INTERRUPTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class NativeUnresolvedItemV12:
    external_id: str
    status: UnresolvedStatus
    reason: str
    surface_text: Optional[str] = None
    scope_ref: Optional[str] = None
    scope_label: Optional[str] = None
    evidence_refs: Tuple[str, ...] = ()
    candidate_refs: Tuple[str, ...] = ()
    native_status: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("unresolved item external_id must be a non-empty opaque ID")
        if not isinstance(self.status, UnresolvedStatus):
            raise TypeError("status must be UnresolvedStatus")
        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")
        for field, value in (
            ("surface_text", self.surface_text),
            ("scope_ref", self.scope_ref),
            ("scope_label", self.scope_label),
            ("native_status", self.native_status),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field} must be a string or None")
        for field, refs in (("evidence_refs", self.evidence_refs),
                            ("candidate_refs", self.candidate_refs)):
            if not isinstance(refs, tuple):
                raise TypeError(f"{field} must be an ordered tuple")
            if any(not isinstance(ref, str) or not ref for ref in refs):
                raise ValueError(f"{field} must contain non-empty opaque strings")


def same_unresolved_item(left: NativeUnresolvedItemV12,
                         right: NativeUnresolvedItemV12) -> bool:
    return left.external_id == right.external_id


__all__ = ["MODEL_VERSION", "UnresolvedStatus", "NativeUnresolvedItemV12",
           "same_unresolved_item"]
