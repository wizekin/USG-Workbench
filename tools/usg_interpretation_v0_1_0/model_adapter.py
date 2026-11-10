"""Optional model candidate adapter with deterministic source-grounding validation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Literal

from .source import SourceSnapshot

MODEL_ADAPTER_VERSION = "model-candidate-adapter/0.1.0"


@dataclass(frozen=True)
class ModelCandidate:
    candidate_id: str
    start: int
    end: int
    surface_text: str
    lemma: str | None
    part_of_speech: str | None
    sense_id: str | None
    rank: int
    rationale_code: str

    def __post_init__(self):
        if not self.candidate_id or not self.surface_text or not self.rationale_code:
            raise ValueError("candidate identity, surface, and rationale code are required")
        if isinstance(self.start, bool) or not isinstance(self.start, int) or self.start < 0:
            raise ValueError("candidate start must be a non-negative integer")
        if isinstance(self.end, bool) or not isinstance(self.end, int) or self.end <= self.start:
            raise ValueError("candidate end must be greater than start")
        if isinstance(self.rank, bool) or not isinstance(self.rank, int) or self.rank < 1:
            raise ValueError("candidate rank must be a positive integer")


@dataclass(frozen=True)
class ModelProposalBatch:
    source_sha256: str
    language: str
    model_id: str
    model_version: str
    configuration_digest: str
    prompt_digest: str
    candidates: tuple[ModelCandidate, ...]

    def __post_init__(self):
        for name in ("source_sha256", "model_id", "model_version",
                     "configuration_digest", "prompt_digest"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        if self.language not in {"en", "ar"}:
            raise ValueError("model proposal language must be en or ar")
        if not isinstance(self.candidates, tuple) or any(not isinstance(x, ModelCandidate) for x in self.candidates):
            raise TypeError("candidates must be an ordered tuple of ModelCandidate")


@dataclass(frozen=True)
class ValidatedModelCandidate:
    candidate: ModelCandidate
    model_id: str
    model_version: str
    configuration_digest: str
    prompt_digest: str
    grounding_status: Literal["EXACT_SOURCE_SPAN"]


@dataclass(frozen=True)
class ModelValidationResult:
    status: Literal["ACCEPTED_CANDIDATES", "REJECTED_BATCH"]
    candidates: tuple[ValidatedModelCandidate, ...]
    diagnostics: tuple[str, ...]
    adapter_version: str = MODEL_ADAPTER_VERSION


class CandidateGenerator(Protocol):
    """Optional adapter protocol; implementations may wrap local/offline models."""
    def generate(self, source: SourceSnapshot) -> ModelProposalBatch: ...


def validate_model_proposals(source: SourceSnapshot,
                             batch: ModelProposalBatch) -> ModelValidationResult:
    """Reject the entire batch on source/profile mismatch or ungrounded spans."""
    if batch.source_sha256 != source.sha256:
        return ModelValidationResult("REJECTED_BATCH", (), ("SOURCE_HASH_MISMATCH",))
    if batch.language != source.language:
        return ModelValidationResult("REJECTED_BATCH", (), ("LANGUAGE_PROFILE_MISMATCH",))
    validated = []
    seen_ids = set()
    for candidate in batch.candidates:
        if candidate.candidate_id in seen_ids:
            return ModelValidationResult("REJECTED_BATCH", (), ("DUPLICATE_CANDIDATE_ID",))
        seen_ids.add(candidate.candidate_id)
        if candidate.end > len(source.text):
            return ModelValidationResult("REJECTED_BATCH", (), ("SPAN_OUT_OF_RANGE",))
        if source.text[candidate.start:candidate.end] != candidate.surface_text:
            return ModelValidationResult("REJECTED_BATCH", (), ("SPAN_SURFACE_MISMATCH",))
        validated.append(ValidatedModelCandidate(
            candidate, batch.model_id, batch.model_version,
            batch.configuration_digest, batch.prompt_digest, "EXACT_SOURCE_SPAN",
        ))
    return ModelValidationResult("ACCEPTED_CANDIDATES", tuple(validated), ())


class ModelAssistedAnalyzer:
    """Thin optional wrapper; callers may omit it and use deterministic stages."""
    def __init__(self, generator: CandidateGenerator):
        if not callable(getattr(generator, "generate", None)):
            raise TypeError("generator must implement generate(source)")
        self.generator = generator

    def analyze(self, source: SourceSnapshot) -> ModelValidationResult:
        proposal = self.generator.generate(source)
        if not isinstance(proposal, ModelProposalBatch):
            return ModelValidationResult("REJECTED_BATCH", (), ("INVALID_PROPOSAL_BATCH_TYPE",))
        return validate_model_proposals(source, proposal)


__all__ = ["MODEL_ADAPTER_VERSION", "ModelCandidate", "ModelProposalBatch",
           "ValidatedModelCandidate", "ModelValidationResult", "CandidateGenerator",
           "validate_model_proposals", "ModelAssistedAnalyzer"]
