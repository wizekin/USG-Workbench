"""Versioned native Derivation model for USG-SEM/1.0."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple
from enum import Enum

MODEL_VERSION = "1.3.0"


class DerivationMethod(str, Enum):
    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    MODEL_PROPOSAL = "MODEL_PROPOSAL"
    IMPORT = "IMPORT"
    INFERENCE = "INFERENCE"
    COMPOSITION = "COMPOSITION"
    UNKNOWN = "UNKNOWN"


class DerivationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DerivationModelInfo:
    provider: Optional[str] = None
    name: Optional[str] = None
    revision: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None

    def __post_init__(self) -> None:
        for field, value in (("provider", self.provider), ("name", self.name),
                             ("revision", self.revision)):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{field} must be a string or None")
        if self.metadata is not None:
            if not isinstance(self.metadata, Mapping):
                raise TypeError("model metadata must be a mapping or None")
            if any(not isinstance(key, str) for key in self.metadata):
                raise ValueError("model metadata keys must be strings")
            object.__setattr__(self, "metadata", deepcopy(dict(self.metadata)))


@dataclass(frozen=True)
class NativeDerivationV13:
    external_id: str
    method: DerivationMethod
    input_refs: Tuple[str, ...]
    output_refs: Tuple[str, ...]
    status: DerivationStatus
    component: Optional[str] = None
    rule_ids: Tuple[str, ...] = ()
    model: Optional[DerivationModelInfo] = None
    timestamp: Optional[str] = None
    diagnostics: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.external_id, str) or not self.external_id:
            raise ValueError("derivation external_id must be a non-empty opaque ID")
        if not isinstance(self.method, DerivationMethod):
            raise TypeError("method must be DerivationMethod")
        if not isinstance(self.status, DerivationStatus):
            raise TypeError("status must be DerivationStatus")
        for field, refs in (("input_refs", self.input_refs),
                            ("output_refs", self.output_refs),
                            ("rule_ids", self.rule_ids)):
            if not isinstance(refs, tuple):
                raise TypeError(f"{field} must be an ordered tuple")
            if any(not isinstance(ref, str) or not ref for ref in refs):
                raise ValueError(f"{field} must contain non-empty opaque strings")
        if self.component is not None and not isinstance(self.component, str):
            raise TypeError("component must be a string or None")
        if self.model is not None and not isinstance(self.model, DerivationModelInfo):
            raise TypeError("model must be DerivationModelInfo or None")
        if self.timestamp is not None and not isinstance(self.timestamp, str):
            raise TypeError("timestamp must be a string or None")
        if not isinstance(self.diagnostics, tuple) or any(
            not isinstance(item, str) for item in self.diagnostics
        ):
            raise TypeError("diagnostics must be an ordered tuple of strings")


def same_derivation(left: NativeDerivationV13, right: NativeDerivationV13) -> bool:
    return left.external_id == right.external_id


__all__ = [
    "MODEL_VERSION", "DerivationMethod", "DerivationStatus",
    "DerivationModelInfo", "NativeDerivationV13", "same_derivation",
]
