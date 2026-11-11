"""Versioned, lossless SQLite persistence for USG-SEM/1.0 documents."""

from .store import (
    CanonicalDocumentStore,
    RESOURCE_CATALOGUE_ROLE,
    DocumentNotFoundError,
    GraphStoreError,
    IntegrityError,
    InvalidDocumentError,
    RevisionConflictError,
    StoredDocument,
)

__all__ = [
    "CanonicalDocumentStore",
    "RESOURCE_CATALOGUE_ROLE",
    "DocumentNotFoundError",
    "GraphStoreError",
    "IntegrityError",
    "InvalidDocumentError",
    "RevisionConflictError",
    "StoredDocument",
]
