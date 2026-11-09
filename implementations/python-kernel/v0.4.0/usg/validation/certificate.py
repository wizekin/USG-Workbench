"""Candidates and derivation certificates (spec Part 5 §5.8).

The AI submits a machine-checkable DERIVATION, never an explanation. A
certificate lists, step by step, which source span / referent / frame / role
each element came from and which registered rule justified it:

  SOURCE_SPAN -> LEXICAL_SENSE -> SEMANTIC_FRAME -> ROLE_ASSIGNMENT -> ASSERTION

Producers can be a MODEL, the RULE_ENGINE or an IMPORT - never a human (this
implementation has no human review). Retention: FULL for candidates; COMPACT
(hash + rule ids + spans) for low-risk accepted records, which can be rebuilt
by replay when the derivation is deterministic (E-54).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .. import GRAMMAR_VERSION, ONTOLOGY_RELEASE, RULESET_RELEASE
from ..core.records import Source
from ..core.spans import Span
from ..core.values import Basis, Origin, Outcome
from ..errors import InvariantViolation
from ..grammar.node import Node
from ..grammar.serialize import node_from_json, node_to_json
from ..util import canonical_json, sha256_hex


class StepType(str, Enum):
    REFERENT_CREATION = "REFERENT_CREATION"
    COREFERENCE = "COREFERENCE"
    LEXICAL_SENSE = "LEXICAL_SENSE"
    FRAME_SELECTION = "FRAME_SELECTION"
    ROLE_ASSIGNMENT = "ROLE_ASSIGNMENT"
    OPERATOR_ATTACHMENT = "OPERATOR_ATTACHMENT"
    FIGURATIVE_MAPPING = "FIGURATIVE_MAPPING"
    CANONICALIZATION = "CANONICALIZATION"
    INFERENCE = "INFERENCE"


PRODUCER_KINDS = ("MODEL", "RULE_ENGINE", "IMPORT")  # deliberately no HUMAN
RETENTION = ("FULL", "COMPACT")


@dataclass(frozen=True)
class CertStep:
    step_id: str
    step_type: StepType
    rule_id: str
    basis: Basis = Basis.GRAMMATICAL
    spans: tuple[tuple[int, int], ...] = ()
    inputs: tuple[tuple[str, str], ...] = ()  # e.g. ("frame","GIVE"), ("role","AGENT#0"), ("referent","W:t1:1")
    output: str = ""
    premises: tuple[str, ...] = ()  # INFERENCE: ids of the premises
    alternatives_considered: tuple[str, ...] = ()
    rule_version: int = 1

    def has_input(self, key: str, value: str) -> bool:
        return (key, value) in self.inputs

    def to_json(self) -> dict[str, Any]:
        return {"id": self.step_id, "type": self.step_type.value, "rule": self.rule_id, "rule_version": self.rule_version,
                "basis": self.basis.value, "spans": [list(s) for s in self.spans], "inputs": [list(i) for i in self.inputs],
                "output": self.output, "premises": list(self.premises), "alternatives": list(self.alternatives_considered)}

    @staticmethod
    def from_json(d: Mapping[str, Any]) -> "CertStep":
        return CertStep(d["id"], StepType(d["type"]), d["rule"], Basis(d["basis"]), tuple(tuple(s) for s in d["spans"]),
                        tuple(tuple(i) for i in d["inputs"]), d.get("output", ""), tuple(d.get("premises", ())),
                        tuple(d.get("alternatives", ())), d.get("rule_version", 1))


@dataclass(frozen=True)
class DerivationCertificate:
    source_hash: str
    producer_kind: str = "MODEL"
    model_id: str | None = None
    prompt_hash: str | None = None
    schema_version: str = "1"
    steps: tuple[CertStep, ...] = ()
    unresolved: tuple[str, ...] = ()
    outcome: Outcome = Outcome.RESOLVED
    retention: str = "FULL"
    parent: str | None = None  # hash of the previous version when this is a repair retry
    grammar_version: str = GRAMMAR_VERSION
    ontology_release: str = ONTOLOGY_RELEASE
    ruleset_release: str = RULESET_RELEASE

    def to_json(self) -> dict[str, Any]:
        return {"source_hash": self.source_hash, "producer": {"kind": self.producer_kind, "model_id": self.model_id,
                                                              "prompt_hash": self.prompt_hash, "schema": self.schema_version},
                "steps": [s.to_json() for s in self.steps], "unresolved": list(self.unresolved),
                "outcome": self.outcome.value, "retention": self.retention, "parent": self.parent,
                "grammar_version": self.grammar_version, "ontology_release": self.ontology_release,
                "ruleset_release": self.ruleset_release}

    @staticmethod
    def from_json(d: Mapping[str, Any]) -> "DerivationCertificate":
        p = d["producer"]
        return DerivationCertificate(
            d["source_hash"], p["kind"], p.get("model_id"), p.get("prompt_hash"), p.get("schema", "1"),
            tuple(CertStep.from_json(s) for s in d["steps"]), tuple(d.get("unresolved", ())), Outcome(d["outcome"]),
            d.get("retention", "FULL"), d.get("parent"), d["grammar_version"], d["ontology_release"], d["ruleset_release"])

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.to_json()))

    def compact(self) -> dict[str, Any]:
        """COMPACT retention: hash, rule ids and spans. The full certificate can be regenerated by replay (E-54)."""
        return {"hash": self.content_hash(), "rules": sorted({s.rule_id for s in self.steps}),
                "spans": sorted({tuple(sp) for s in self.steps for sp in s.spans}), "outcome": self.outcome.value}

    def step(self, step_id: str) -> CertStep | None:
        return next((s for s in self.steps if s.step_id == step_id), None)

    def steps_of(self, t: StepType) -> list[CertStep]:
        return [s for s in self.steps if s.step_type is t]


@dataclass(frozen=True)
class Candidate:
    """One interpreted unit awaiting validation: the expression plus how it was derived."""

    source: Source
    unit_span: Span
    expression: Node
    certificate: DerivationCertificate
    declared_origin: Origin = Origin.SOURCE_TEXT

    @property
    def unit_text(self) -> str:
        return self.source.span_text(self.unit_span)

    def content_hash(self) -> str:
        from ..grammar.serialize import full_hash
        return sha256_hex(f"{full_hash(self.expression)}|{self.certificate.content_hash()}|{self.unit_span.start}:{self.unit_span.end}")

    def to_json(self) -> dict[str, Any]:
        return {"unit_span": self.unit_span.as_list(), "expression": node_to_json(self.expression),
                "certificate": self.certificate.to_json(), "declared_origin": self.declared_origin.value}

    @staticmethod
    def from_json(source: Source, d: Mapping[str, Any]) -> "Candidate":
        try:
            return Candidate(source, Span(*d["unit_span"]), node_from_json(d["expression"]),
                             DerivationCertificate.from_json(d["certificate"]), Origin(d.get("declared_origin", "SOURCE_TEXT")))
        except InvariantViolation:
            raise
        except (KeyError, ValueError, TypeError) as e:
            raise InvariantViolation(f"malformed candidate: {e}", "VC-S01") from e