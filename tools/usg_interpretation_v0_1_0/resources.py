"""Versioned semantic resource manifest and provisional association registry."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Literal

RESOURCE_REGISTRY_VERSION = "semantic-resource-registry/0.1.0"


@dataclass(frozen=True)
class ResourceDescriptor:
    resource_id: str
    resource_type: Literal["LEXICON", "GRAMMAR", "SEMANTIC_FRAME", "DISCOURSE", "MODEL", "OTHER"]
    version: str
    sha256: str
    language: str | None
    provenance: str

    def __post_init__(self):
        if not all((self.resource_id, self.version, self.sha256, self.provenance)):
            raise ValueError("resource identity, version, digest, and provenance are required")
        if self.resource_type not in {"LEXICON", "GRAMMAR", "SEMANTIC_FRAME", "DISCOURSE", "MODEL", "OTHER"}:
            raise ValueError("unsupported resource type")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256.lower()):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")


@dataclass(frozen=True)
class SemanticAssociation:
    association_id: str
    source_ref: str
    target_ref: str
    relation: str
    association_kind: Literal["CO_OCCURRENCE", "FUNCTIONAL", "CONTEXTUAL"]
    weight: float
    observation_count: int
    provenance: str
    status: Literal["PROVISIONAL"] = "PROVISIONAL"

    def __post_init__(self):
        if not all((self.association_id, self.source_ref, self.target_ref,
                    self.relation, self.provenance)):
            raise ValueError("association identity, endpoints, relation, and provenance are required")
        if self.source_ref == self.target_ref:
            raise ValueError("self-associations are not accepted in this version")
        if self.association_kind not in {"CO_OCCURRENCE", "FUNCTIONAL", "CONTEXTUAL"}:
            raise ValueError("unsupported association kind")
        if isinstance(self.weight, bool) or not isinstance(self.weight, (int, float)) or not 0 <= self.weight <= 1:
            raise ValueError("association weight must be between 0 and 1")
        if isinstance(self.observation_count, bool) or not isinstance(self.observation_count, int) or self.observation_count < 0:
            raise ValueError("observation_count must be a non-negative integer")
        if self.status != "PROVISIONAL":
            raise ValueError("associations cannot be promoted to definitions or identities")


@dataclass(frozen=True)
class SemanticResourceRegistry:
    registry_id: str
    version: int
    resources: tuple[ResourceDescriptor, ...] = ()
    associations: tuple[SemanticAssociation, ...] = ()

    def __post_init__(self):
        if not self.registry_id or isinstance(self.version, bool) or self.version < 1:
            raise ValueError("registry id and positive version are required")
        resource_ids = [x.resource_id for x in self.resources]
        association_ids = [x.association_id for x in self.associations]
        if len(resource_ids) != len(set(resource_ids)):
            raise ValueError("resource IDs must be unique")
        if len(association_ids) != len(set(association_ids)):
            raise ValueError("association IDs must be unique")

    def with_resource(self, descriptor: ResourceDescriptor) -> "SemanticResourceRegistry":
        if any(x.resource_id == descriptor.resource_id for x in self.resources):
            raise ValueError("resource ID already registered; publish a new version under a new ID")
        return SemanticResourceRegistry(self.registry_id, self.version + 1,
                                        self.resources + (descriptor,), self.associations)

    def with_association(self, association: SemanticAssociation) -> "SemanticResourceRegistry":
        if any(x.association_id == association.association_id for x in self.associations):
            raise ValueError("association ID already registered")
        return SemanticResourceRegistry(self.registry_id, self.version + 1,
                                        self.resources, self.associations + (association,))

    def active_associations(self, source_ref: str) -> tuple[SemanticAssociation, ...]:
        selected = [x for x in self.associations if x.source_ref == source_ref]
        return tuple(sorted(selected, key=lambda x: (x.weight, x.observation_count, x.association_id),
                            reverse=True))

    def manifest(self) -> dict:
        return {
            "registry_id": self.registry_id,
            "version": self.version,
            "contract": RESOURCE_REGISTRY_VERSION,
            "resources": [
                {"resource_id": x.resource_id, "resource_type": x.resource_type,
                 "version": x.version, "sha256": x.sha256, "language": x.language,
                 "provenance": x.provenance} for x in self.resources
            ],
            "associations": [
                {"association_id": x.association_id, "source_ref": x.source_ref,
                 "target_ref": x.target_ref, "relation": x.relation,
                 "association_kind": x.association_kind, "weight": x.weight,
                 "observation_count": x.observation_count, "provenance": x.provenance,
                 "status": x.status} for x in self.associations
            ],
        }

    def digest(self) -> str:
        encoded = json.dumps(self.manifest(), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        return sha256(encoded).hexdigest()


__all__ = ["RESOURCE_REGISTRY_VERSION", "ResourceDescriptor",
           "SemanticAssociation", "SemanticResourceRegistry"]
