"""Versioned native Definitions catalogue model for USG-SEM/1.0."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Tuple

MODEL_VERSION = "1.4.0"


class SemanticKind(str, Enum):
    ENTITY = "ENTITY"
    EVENT = "EVENT"
    PROCESS = "PROCESS"
    STATE = "STATE"
    PROPERTY = "PROPERTY"
    VALUE = "VALUE"
    QUANTITY = "QUANTITY"
    RELATION = "RELATION"
    ROLE = "ROLE"
    FRAME = "FRAME"
    PROPOSITION = "PROPOSITION"
    CONSTRAINT = "CONSTRAINT"
    TIME = "TIME"
    FUNCTION = "FUNCTION"
    EXPRESSION = "EXPRESSION"


def _opaque_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty opaque string")


def _metadata(value: Optional[Mapping[str, Any]], field: str):
    if value is None:
        return
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a mapping or None")
    if any(not isinstance(key, str) for key in value):
        raise ValueError(f"{field} keys must be strings")


@dataclass(frozen=True)
class ConceptDefinitionV14:
    external_id: str
    label: str
    semantic_kind: SemanticKind
    version: int
    definition: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    canonical_extras: Optional[Mapping[str, Any]] = None

    def __post_init__(self):
        _opaque_id(self.external_id, "concept external_id")
        if not isinstance(self.label, str):
            raise TypeError("concept label must be a string")
        if not isinstance(self.semantic_kind, SemanticKind):
            raise TypeError("semantic_kind must be SemanticKind")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise ValueError("concept version must be a positive integer")
        for field, value in (("definition", self.definition), ("lifecycle_stage", self.lifecycle_stage)):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field} must be a string or None")
        _metadata(self.canonical_extras, "canonical_extras")
        if self.canonical_extras is not None:
            object.__setattr__(self, "canonical_extras", deepcopy(dict(self.canonical_extras)))


@dataclass(frozen=True)
class FrameDefinitionV14:
    external_id: str
    label: str
    version: int
    roles: Tuple[str, ...]
    semantic_kind: Optional[SemanticKind] = None
    canonical_extras: Optional[Mapping[str, Any]] = None

    def __post_init__(self):
        _opaque_id(self.external_id, "frame external_id")
        if not isinstance(self.label, str):
            raise TypeError("frame label must be a string")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise ValueError("frame version must be a positive integer")
        if not isinstance(self.roles, tuple) or any(not isinstance(x, str) or not x for x in self.roles):
            raise ValueError("frame roles must be an ordered tuple of non-empty strings")
        if self.semantic_kind is not None and not isinstance(self.semantic_kind, SemanticKind):
            raise TypeError("semantic_kind must be SemanticKind or None")
        _metadata(self.canonical_extras, "canonical_extras")
        if self.canonical_extras is not None:
            object.__setattr__(self, "canonical_extras", deepcopy(dict(self.canonical_extras)))


@dataclass(frozen=True)
class RoleDefinitionV14:
    external_id: str
    label: str
    constraints: Optional[Mapping[str, Any]] = None
    canonical_extras: Optional[Mapping[str, Any]] = None

    def __post_init__(self):
        _opaque_id(self.external_id, "role external_id")
        if not isinstance(self.label, str):
            raise TypeError("role label must be a string")
        _metadata(self.constraints, "constraints")
        _metadata(self.canonical_extras, "canonical_extras")
        if self.constraints is not None:
            object.__setattr__(self, "constraints", deepcopy(dict(self.constraints)))
        if self.canonical_extras is not None:
            object.__setattr__(self, "canonical_extras", deepcopy(dict(self.canonical_extras)))


@dataclass(frozen=True)
class RelationDefinitionV14:
    external_id: str
    label: str
    properties: Optional[Mapping[str, Any]] = None
    canonical_extras: Optional[Mapping[str, Any]] = None

    def __post_init__(self):
        _opaque_id(self.external_id, "relation external_id")
        if not isinstance(self.label, str):
            raise TypeError("relation label must be a string")
        _metadata(self.properties, "properties")
        _metadata(self.canonical_extras, "canonical_extras")
        if self.properties is not None:
            object.__setattr__(self, "properties", deepcopy(dict(self.properties)))
        if self.canonical_extras is not None:
            object.__setattr__(self, "canonical_extras", deepcopy(dict(self.canonical_extras)))


@dataclass(frozen=True)
class DefinitionsCatalogueV14:
    concepts: Tuple[ConceptDefinitionV14, ...]
    frames: Tuple[FrameDefinitionV14, ...]
    roles: Tuple[RoleDefinitionV14, ...]
    relations: Tuple[RelationDefinitionV14, ...]
    grammar_version: Optional[str] = None
    ontology_release: Optional[str] = None

    def __post_init__(self):
        for field, values, cls in (
            ("concepts", self.concepts, ConceptDefinitionV14),
            ("frames", self.frames, FrameDefinitionV14),
            ("roles", self.roles, RoleDefinitionV14),
            ("relations", self.relations, RelationDefinitionV14),
        ):
            if not isinstance(values, tuple) or any(not isinstance(x, cls) for x in values):
                raise TypeError(f"{field} must be an ordered tuple of {cls.__name__}")
        for field, value in (("grammar_version", self.grammar_version),
                             ("ontology_release", self.ontology_release)):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field} must be a string or None")


def same_definition(left: Any, right: Any) -> bool:
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "SemanticKind", "ConceptDefinitionV14",
    "FrameDefinitionV14", "RoleDefinitionV14", "RelationDefinitionV14",
    "DefinitionsCatalogueV14", "same_definition",
]
