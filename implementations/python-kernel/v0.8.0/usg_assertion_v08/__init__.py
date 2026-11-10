"""Versioned native Assertion model for USG-SEM/1.0.

An Assertion is a claim record about expression content. It is not the
expression itself, and its epistemic/lifecycle metadata does not establish
objective truth. References are opaque and explicitly typed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

MODEL_VERSION = "0.8.0"


class ReferenceSpace(str, Enum):
    ASSERTION = "ASSERTION"
    EXPRESSION = "EXPRESSION"
    SOURCE = "SOURCE"
    REFERENT = "REFERENT"
    EVIDENCE = "EVIDENCE"
    CONTEXT = "CONTEXT"
    DEFINITION = "DEFINITION"
    ALTERNATIVE_GROUP = "ALTERNATIVE_GROUP"


class AssertionOrigin(str, Enum):
    SOURCE_TEXT = "SOURCE_TEXT"
    GRAMMATICAL = "GRAMMATICAL"
    BACKGROUND_INFERENCE = "BACKGROUND_INFERENCE"
    IMPORTED_RESOURCE = "IMPORTED_RESOURCE"
    CURATED = "CURATED"
    UNKNOWN = "UNKNOWN"


class EpistemicStatus(str, Enum):
    SOURCE_ASSERTED = "SOURCE_ASSERTED"
    INFERRED = "INFERRED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class CommitmentKind(str, Enum):
    AUTHOR = "AUTHOR"
    ATTRIBUTED = "ATTRIBUTED"
    NONE = "NONE"


class EvaluationContextKind(str, Enum):
    WORLD = "WORLD"
    FICTION = "FICTION"
    HYPOTHETICAL = "HYPOTHETICAL"
    HISTORICAL_BELIEF = "HISTORICAL_BELIEF"
    DOMAIN_MODEL = "DOMAIN_MODEL"
    UNKNOWN = "UNKNOWN"


class LifecycleStage(str, Enum):
    DISCOVERED = "DISCOVERED"
    STRUCTURED = "STRUCTURED"
    FORMALLY_VALIDATED = "FORMALLY_VALIDATED"
    AUTOMATICALLY_EVALUATED = "AUTOMATICALLY_EVALUATED"
    CORROBORATED = "CORROBORATED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    DEPRECATED = "DEPRECATED"


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
class EvaluationContext:
    """Contextual frame for evaluating a claim, not a truth judgment."""
    kind: EvaluationContextKind
    context_ref: Optional[TypedReference] = None
    name: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EvaluationContextKind):
            raise TypeError("kind must be EvaluationContextKind")
        if self.context_ref is not None:
            if (not isinstance(self.context_ref, TypedReference)
                    or self.context_ref.space is not ReferenceSpace.CONTEXT):
                raise ValueError("context_ref must be a typed CONTEXT reference")
        if self.name is not None and not isinstance(self.name, str):
            raise TypeError("name must be a string or None")


@dataclass(frozen=True)
class NativeAssertionV08:
    """A claim about an expression, with independent provenance/status axes."""
    external_id: str
    expression_ref: TypedReference
    origin: AssertionOrigin
    epistemic_status: EpistemicStatus
    commitment: CommitmentKind
    evaluation_context: EvaluationContext
    lifecycle_stage: LifecycleStage
    attributed_to_ref: Optional[TypedReference] = None
    source_ref: Optional[TypedReference] = None
    evidence_refs: Tuple[TypedReference, ...] = ()
    definition_ref: Optional[TypedReference] = None
    alternative_group_ref: Optional[TypedReference] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("assertion external_id must be a non-empty opaque ID")
        required = (
            ("expression_ref", self.expression_ref, ReferenceSpace.EXPRESSION),
        )
        for field_name, ref, expected in required:
            if not isinstance(ref, TypedReference) or ref.space is not expected:
                raise ValueError(f"{field_name} must target {expected.value}")
        enum_fields = (
            ("origin", self.origin, AssertionOrigin),
            ("epistemic_status", self.epistemic_status, EpistemicStatus),
            ("commitment", self.commitment, CommitmentKind),
            ("lifecycle_stage", self.lifecycle_stage, LifecycleStage),
        )
        for field_name, value, expected in enum_fields:
            if not isinstance(value, expected):
                raise TypeError(f"{field_name} must be {expected.__name__}")
        if not isinstance(self.evaluation_context, EvaluationContext):
            raise TypeError("evaluation_context must be EvaluationContext")
        optional_refs = (
            ("attributed_to_ref", self.attributed_to_ref, ReferenceSpace.REFERENT),
            ("source_ref", self.source_ref, ReferenceSpace.SOURCE),
            ("definition_ref", self.definition_ref, ReferenceSpace.DEFINITION),
            ("alternative_group_ref", self.alternative_group_ref, ReferenceSpace.ALTERNATIVE_GROUP),
        )
        for field_name, ref, expected in optional_refs:
            if ref is not None and (
                not isinstance(ref, TypedReference) or ref.space is not expected
            ):
                raise ValueError(f"{field_name} must be a typed {expected.value} reference")
        if not isinstance(self.evidence_refs, tuple):
            raise TypeError("evidence_refs must be an ordered tuple")
        for ref in self.evidence_refs:
            if not isinstance(ref, TypedReference) or ref.space is not ReferenceSpace.EVIDENCE:
                raise ValueError("evidence_refs must contain typed EVIDENCE references")


def same_assertion(left: NativeAssertionV08, right: NativeAssertionV08) -> bool:
    """Assertion identity is its opaque record ID, never its expression or claim."""
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "ReferenceSpace", "AssertionOrigin", "EpistemicStatus",
    "CommitmentKind", "EvaluationContextKind", "LifecycleStage",
    "TypedReference", "EvaluationContext", "NativeAssertionV08",
    "same_assertion",
]
