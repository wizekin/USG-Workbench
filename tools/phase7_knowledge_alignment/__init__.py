"""Candidate-only bilingual sense-to-concept alignment proposal builder."""
from .proposals import (
    AlignmentProposalError, build_bilingual_alignment_bundle,
    ingest_bilingual_alignment_bundle,
)
__all__ = [
    "AlignmentProposalError", "build_bilingual_alignment_bundle",
    "ingest_bilingual_alignment_bundle",
]
