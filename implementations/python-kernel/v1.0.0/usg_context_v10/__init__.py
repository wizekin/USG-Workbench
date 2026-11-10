"""Versioned native Context model for USG-SEM/1.0.

Contexts scope semantic content to a world, hypothetical, belief, domain, or
other declared interpretive setting. A context is not a truth judgment and
its links never authorize automatic propagation of assertions.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

MODEL_VERSION = "1.0.0"


class ReferenceSpace(str, Enum):
    CONTEXT = "CONTEXT"
    SOURCE = "SOURCE"
    REFERENT = "REFERENT"


class ContextKind(str, Enum):
    WORLD = "WORLD"
    FICTION = "FICTION"
    HYPOTHETICAL = "HYPOTHETICAL"
    HISTORICAL_BELIEF = "HISTORICAL_BELIEF"
    DOMAIN_MODEL = "DOMAIN_MODEL"
    ATTITUDE = "ATTITUDE"
    CONDITIONAL = "CONDITIONAL"
    NEGATED = "NEGATED"
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
class NativeContextV10:
    """One context node with typed optional links and opaque metadata."""
    external_id: str
    kind: ContextKind
    parent_ref: Optional[TypedReference] = None
    source_ref: Optional[TypedReference] = None
    agent_ref: Optional[TypedReference] = None
    name: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("context external_id must be a non-empty opaque ID")
        if not isinstance(self.kind, ContextKind):
            raise TypeError("kind must be ContextKind")
        expected = (
            ("parent_ref", self.parent_ref, ReferenceSpace.CONTEXT),
            ("source_ref", self.source_ref, ReferenceSpace.SOURCE),
            ("agent_ref", self.agent_ref, ReferenceSpace.REFERENT),
        )
        for field, ref, space in expected:
            if ref is not None:
                if not isinstance(ref, TypedReference):
                    raise TypeError(f"{field} must be TypedReference or None")
                if ref.space is not space:
                    raise ValueError(f"{field} must target {space.value}")
        if self.name is not None and not isinstance(self.name, str):
            raise TypeError("name must be a string or None")
        if self.metadata is not None:
            if not isinstance(self.metadata, Mapping):
                raise TypeError("metadata must be a mapping or None")
            if any(not isinstance(key, str) for key in self.metadata):
                raise ValueError("metadata keys must be strings")
            object.__setattr__(self, "metadata", deepcopy(dict(self.metadata)))


def same_context(left: NativeContextV10, right: NativeContextV10) -> bool:
    """Context identity is its opaque record ID, not its name or kind."""
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "ReferenceSpace", "ContextKind", "TypedReference",
    "NativeContextV10", "same_context",
]
