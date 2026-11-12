"""Rights-aware Phase 7 source adapters."""
from .adapters import (
    KnowledgeSourceAdapterError, adapt_canonical_document,
    adapt_lexical_candidate_package, ingest_canonical_document,
    ingest_lexical_candidate_package,
)
__all__ = [
    "KnowledgeSourceAdapterError", "adapt_canonical_document",
    "adapt_lexical_candidate_package", "ingest_canonical_document",
    "ingest_lexical_candidate_package",
]
