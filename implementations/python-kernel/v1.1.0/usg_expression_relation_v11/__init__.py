"""Versioned native ExpressionRelation model for USG-SEM/1.0."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Tuple

MODEL_VERSION = "1.1.0"


class ReferenceSpace(str, Enum):
    EXPRESSION = "EXPRESSION"
    EVIDENCE = "EVIDENCE"


class RelationType(str, Enum):
    CAUSE = "CAUSE"
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"
    ATTACKS = "ATTACKS"
    RELATED_TO = "RELATED_TO"
    PRECEDES = "PRECEDES"
    OVERLAPS = "OVERLAPS"
    COREFERS = "COREFERS"
    OTHER = "OTHER"


class VerificationStatus(str, Enum):
    NOT_INDEPENDENTLY_VERIFIED = "NOT_INDEPENDENTLY_VERIFIED"
    RULE_SUPPORTED = "RULE_SUPPORTED"
    CORROBORATED = "CORROBORATED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, order=True)
class TypedReference:
    space: ReferenceSpace
    external_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.space, ReferenceSpace):
            raise TypeError("reference space must be a ReferenceSpace")
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("reference external_id must be a non-empty string")


@dataclass(frozen=True)
class NativeExpressionRelationV11:
    external_id: str
    relation_type: RelationType
    source_expression_ref: TypedReference
    target_expression_ref: TypedReference
    verification_status: VerificationStatus
    evidence_refs: Tuple[TypedReference, ...] = ()
    attribution: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("relation external_id must be a non-empty opaque ID")
        if not isinstance(self.relation_type, RelationType):
            raise TypeError("relation_type must be RelationType")
        if not isinstance(self.verification_status, VerificationStatus):
            raise TypeError("verification_status must be VerificationStatus")
        for field, ref in (
            ("source_expression_ref", self.source_expression_ref),
            ("target_expression_ref", self.target_expression_ref),
        ):
            if not isinstance(ref, TypedReference) or ref.space is not ReferenceSpace.EXPRESSION:
                raise ValueError(f"{field} must be a typed EXPRESSION reference")
        if not isinstance(self.evidence_refs, tuple):
            raise TypeError("evidence_refs must be an ordered tuple")
        for ref in self.evidence_refs:
            if not isinstance(ref, TypedReference) or ref.space is not ReferenceSpace.EVIDENCE:
                raise ValueError("evidence_refs must contain typed EVIDENCE references")
        if self.attribution is not None:
            if not isinstance(self.attribution, Mapping):
                raise TypeError("attribution must be a mapping or None")
            if any(not isinstance(key, str) for key in self.attribution):
                raise ValueError("attribution keys must be strings")
            object.__setattr__(self, "attribution", deepcopy(dict(self.attribution)))


def same_expression_relation(left: NativeExpressionRelationV11,
                             right: NativeExpressionRelationV11) -> bool:
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "ReferenceSpace", "RelationType", "VerificationStatus",
    "TypedReference", "NativeExpressionRelationV11", "same_expression_relation",
]
