"""Automatic Phase 6 acceptance factory v1.0."""

from .generate import BENCHMARK_ID, build, corpus_sha256, validate
from .evaluate import run_acceptance

__all__ = ["BENCHMARK_ID", "build", "corpus_sha256", "validate", "run_acceptance"]
