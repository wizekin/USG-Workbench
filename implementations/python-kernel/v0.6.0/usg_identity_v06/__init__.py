"""Versioned native referent-identity model for USG-SEM/1.0.

This package is deliberately independent of the frozen Python kernel v0.5.0.
It models discourse identity metadata without conflating identity scope,
resolution status, concept classification, labels, or context references.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


MODEL_VERSION = "0.6.0"


class IdentityStatus(str, Enum):
    PROVISIONAL = "PROVISIONAL"
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class IdentityScope(str, Enum):
    DOCUMENT = "DOCUMENT"
    WORKSPACE = "WORKSPACE"
    CORPUS = "CORPUS"
    GLOBAL = "GLOBAL"


class ReferenceSpace(str, Enum):
    REFERENT = "REFERENT"
    CONCEPT = "CONCEPT"
    PROVISIONAL = "PROVISIONAL"
    INSTANCE = "INSTANCE"
    NODE = "NODE"
    SOURCE = "SOURCE"


class IntroductionKind(str, Enum):
    WORLD = "WORLD"
    CONTENT_OF = "CONTENT_OF"
    NEGATED = "NEGATED"
    CONDITIONAL = "CONDITIONAL"
    HYPOTHETICAL = "HYPOTHETICAL"


@dataclass(frozen=True, order=True)
class TypedReference:
    """Opaque external ID plus an explicit target space; never parse ID text."""
    space: ReferenceSpace
    external_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.space, ReferenceSpace):
            raise TypeError("reference space must be a ReferenceSpace")
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("reference external_id must be a non-empty string")


@dataclass(frozen=True)
class ReferentIdentity:
    """Identity-resolution axis, independent of identity scope."""
    status: Optional[IdentityStatus] = None
    scope: Optional[IdentityScope] = None
    equivalence_refs: Tuple[TypedReference, ...] = ()
    basis: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status is not None and not isinstance(self.status, IdentityStatus):
            raise TypeError("status must be IdentityStatus or None")
        if self.scope is not None and not isinstance(self.scope, IdentityScope):
            raise TypeError("scope must be IdentityScope or None")
        if not isinstance(self.equivalence_refs, tuple):
            raise TypeError("equivalence_refs must be an ordered tuple")
        for ref in self.equivalence_refs:
            if not isinstance(ref, TypedReference) or ref.space is not ReferenceSpace.REFERENT:
                raise ValueError("equivalence_refs must contain typed REFERENT references")
        if self.basis is not None and not isinstance(self.basis, str):
            raise TypeError("basis must be a string or None")


@dataclass(frozen=True)
class IntroductionContext:
    """Context of referent introduction; separate from identity scope."""
    kind: IntroductionKind = IntroductionKind.WORLD
    context_ref: Optional[TypedReference] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, IntroductionKind):
            raise TypeError("kind must be IntroductionKind")
        if self.kind is IntroductionKind.WORLD:
            if self.context_ref is not None:
                raise ValueError("WORLD introduction must not carry context_ref")
        else:
            if self.context_ref is None:
                raise ValueError(f"{self.kind.value} introduction requires context_ref")
            if self.context_ref.space not in (ReferenceSpace.INSTANCE, ReferenceSpace.NODE):
                raise ValueError("introduction context must target INSTANCE or NODE")


@dataclass(frozen=True)
class NativeReferentV06:
    """Native discourse referent; lexical labels never establish identity."""
    external_id: str
    label: str
    semantic_kind: Optional[str] = None
    concept_refs: Tuple[TypedReference, ...] = ()
    aliases: Tuple[str, ...] = ()
    identity: ReferentIdentity = ReferentIdentity()
    introduced_in: IntroductionContext = IntroductionContext()
    number: Optional[str] = None
    genericity: Optional[str] = None
    source_ref: Optional[TypedReference] = None
    source_span: Optional[Tuple[int, int]] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("referent external_id must be a non-empty opaque ID")
        if not isinstance(self.label, str):
            raise TypeError("label must be a string")
        if not isinstance(self.concept_refs, tuple):
            raise TypeError("concept_refs must be an ordered tuple")
        for ref in self.concept_refs:
            if not isinstance(ref, TypedReference) or ref.space not in (
                ReferenceSpace.CONCEPT, ReferenceSpace.PROVISIONAL
            ):
                raise ValueError("concept_refs must target CONCEPT or PROVISIONAL")
        if not isinstance(self.aliases, tuple) or any(not isinstance(x, str) for x in self.aliases):
            raise TypeError("aliases must be an ordered tuple of strings")
        if not isinstance(self.identity, ReferentIdentity):
            raise TypeError("identity must be ReferentIdentity")
        if not isinstance(self.introduced_in, IntroductionContext):
            raise TypeError("introduced_in must be IntroductionContext")
        if self.source_ref is not None and self.source_ref.space is not ReferenceSpace.SOURCE:
            raise ValueError("source_ref must target SOURCE")
        if self.source_span is not None:
            if (not isinstance(self.source_span, tuple) or len(self.source_span) != 2
                    or any(not isinstance(x, int) or isinstance(x, bool) for x in self.source_span)
                    or self.source_span[0] < 0 or self.source_span[1] < self.source_span[0]):
                raise ValueError("source_span must be a non-negative (start, end) code-point pair")


def same_referent(left: NativeReferentV06, right: NativeReferentV06) -> bool:
    """Identity is the opaque referent ID, never labels, aliases, or concept refs."""
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "IdentityStatus", "IdentityScope", "ReferenceSpace",
    "IntroductionKind", "TypedReference", "ReferentIdentity",
    "IntroductionContext", "NativeReferentV06", "same_referent",
]
