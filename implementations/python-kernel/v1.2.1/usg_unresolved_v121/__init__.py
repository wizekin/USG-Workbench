"""Corrected native UnresolvedItem model with typed scope and Evidence references."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

MODEL_VERSION = "1.2.1"


class ReferenceSpace(str, Enum):
    EXPRESSION = "EXPRESSION"
    EVIDENCE = "EVIDENCE"


class UnresolvedStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTING = "CONFLICTING"
    RESOURCE_INTERRUPTED = "RESOURCE_INTERRUPTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, order=True)
class TypedReference:
    space: ReferenceSpace
    external_id: str

    def __post_init__(self):
        if not isinstance(self.space, ReferenceSpace):
            raise TypeError("reference space must be ReferenceSpace")
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("reference external_id must be a non-empty opaque string")


@dataclass(frozen=True)
class NativeUnresolvedItemV121:
    external_id: str
    status: UnresolvedStatus
    reason: str
    surface_text: Optional[str] = None
    scope_ref: Optional[TypedReference] = None
    scope_label: Optional[str] = None
    evidence_refs: Tuple[TypedReference, ...] = ()
    candidate_refs: Tuple[str, ...] = ()
    native_status: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("unresolved item external_id must be a non-empty opaque ID")
        if not isinstance(self.status, UnresolvedStatus):
            raise TypeError("status must be UnresolvedStatus")
        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")
        if self.scope_ref is not None and (
            not isinstance(self.scope_ref, TypedReference)
            or self.scope_ref.space is not ReferenceSpace.EXPRESSION
        ):
            raise ValueError("scope_ref must be a typed EXPRESSION reference")
        if not isinstance(self.evidence_refs, tuple) or any(
            not isinstance(ref, TypedReference) or ref.space is not ReferenceSpace.EVIDENCE
            for ref in self.evidence_refs
        ):
            raise ValueError("evidence_refs must be an ordered tuple of typed EVIDENCE references")
        for field, value in (
            ("surface_text", self.surface_text), ("scope_label", self.scope_label),
            ("native_status", self.native_status),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field} must be a string or None")
        if not isinstance(self.candidate_refs, tuple) or any(
            not isinstance(ref, str) or not ref for ref in self.candidate_refs
        ):
            raise ValueError("candidate_refs must be an ordered tuple of non-empty opaque strings")


def same_unresolved_item(left: NativeUnresolvedItemV121,
                         right: NativeUnresolvedItemV121) -> bool:
    return left.external_id == right.external_id


__all__ = ["MODEL_VERSION", "ReferenceSpace", "UnresolvedStatus",
           "TypedReference", "NativeUnresolvedItemV121", "same_unresolved_item"]
