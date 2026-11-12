"""Versioned external lexical retrieval and incremental analysis subsystem."""

__version__ = "0.1.0"

from .adapter import (
    ADAPTER_CONTRACT,
    CandidatePackageError,
    adapt_candidate_package,
    validate_candidate_package,
)
from .service import ExternalLexicalService

__all__ = [
    "ExternalLexicalService",
    "ADAPTER_CONTRACT",
    "CandidatePackageError",
    "adapt_candidate_package",
    "validate_candidate_package",
    "__version__",
]
