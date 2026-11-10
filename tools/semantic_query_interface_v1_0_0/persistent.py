"""Revision-pinned query execution over the canonical SQLite document store.

The stored canonical snapshot is the only query input. Results are wrapped with
its exact immutable revision and digest so callers can reproduce the operation.
"""
from __future__ import annotations

from typing import Any

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.semantic_query_interface_v1_0_0 import QueryInterface


class PersistentQueryService:
    """Run the existing deterministic query pipeline against a stored revision.

    This service deliberately does not add a second query engine or write query
    results back into canonical documents. Storage and query errors propagate;
    no partial-success envelope is returned.
    """

    def __init__(
        self,
        store: CanonicalDocumentStore,
        query_interface: QueryInterface | None = None,
    ) -> None:
        self.store = store
        self.query_interface = query_interface or QueryInterface()

    def run(
        self,
        document_id: str,
        query: dict[str, Any],
        revision: int | None = None,
    ) -> dict[str, Any]:
        """Execute a query against the current or explicitly selected revision."""
        stored = self.store.get_document(document_id, revision=revision)
        result = self.query_interface.run(stored.document, query)

        # The query engine hashes the same canonical JSON representation used by
        # the store. Refuse to return a result if those identities ever diverge.
        if result.get("document_id") != stored.document_id:
            raise RuntimeError("persistent query document identity mismatch")
        if result.get("document_sha256") != stored.digest:
            raise RuntimeError("persistent query snapshot digest mismatch")

        return {
            "profile_id": "USG-PERSISTENT-QUERY/1.0.0",
            "document_id": stored.document_id,
            "document_revision": stored.revision,
            "document_sha256": stored.digest,
            "canonicalization_profile": stored.canonicalization_profile,
            "storage_status": stored.status,
            "query_result": result,
            "safety": {
                "canonical_document_mutated": False,
                "query_result_persisted_as_semantic_truth": False,
                "revision_pinned": True,
            },
        }


def run_persistent_query(
    store: CanonicalDocumentStore,
    document_id: str,
    query: dict[str, Any],
    revision: int | None = None,
    query_interface: QueryInterface | None = None,
) -> dict[str, Any]:
    """Convenience entry point for a single revision-pinned query."""
    return PersistentQueryService(store, query_interface).run(
        document_id, query, revision=revision
    )
