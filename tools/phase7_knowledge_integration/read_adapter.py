"""Read-only, versioned Phase 7 knowledge adapter for Phase 2/4/5/6 consumers."""
from __future__ import annotations
from typing import Any

from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.phase7_knowledge_retrieval import retrieve_candidates

KNOWLEDGE_READ_ADAPTER_VERSION = "usg-knowledge-read-adapter/0.1.0"
_CONSUMER_STATES = {
    "PHASE2": ("ACCEPTED", "VALIDATED_FOR_PROFILE"),
    "PHASE4": ("ACCEPTED", "VALIDATED_FOR_PROFILE"),
    "PHASE5": ("ACCEPTED", "VALIDATED_FOR_PROFILE"),
    "PHASE6": ("CANDIDATE", "UNRESOLVED"),
}


class KnowledgeIntegrationError(ValueError):
    """Unsupported consumer or unsafe integration request."""


class KnowledgeReadAdapter:
    """Expose repository snapshots as read-only evidence to existing services.

    The adapter never mutates knowledge records, lifecycle states, resources,
    interpreter output, or the canonical USG-SEM document store.
    """

    def __init__(self, repository: SQLiteKnowledgeRepository):
        if not isinstance(repository, SQLiteKnowledgeRepository):
            raise TypeError("repository must be an existing SQLiteKnowledgeRepository")
        self.repository = repository

    def query(
        self, consumer: str, query: str, *, language: str | None = None,
        context_filters: dict[str, str] | None = None,
        include_candidate_evidence: bool = False, limit: int = 20,
    ) -> dict[str, Any]:
        consumer = str(consumer).upper()
        if consumer not in _CONSUMER_STATES:
            raise KnowledgeIntegrationError("consumer must be PHASE2, PHASE4, PHASE5, or PHASE6")
        states = set(_CONSUMER_STATES[consumer])
        if include_candidate_evidence and consumer != "PHASE6":
            states.update(("CANDIDATE", "UNRESOLVED"))
        snapshots = self.repository.list_snapshots(limit=500)
        bundles = []
        for metadata in snapshots:
            snapshot = self.repository.get_snapshot(metadata["snapshot_id"])
            if snapshot is not None:
                bundles.append(snapshot.bundle)
        result = retrieve_candidates(
            bundles, query, language=language, context_filters=context_filters,
            include_states=tuple(sorted(states)), limit=limit,
        )
        candidate_only = consumer == "PHASE6"
        return {
            "contract": "USG-KNOWLEDGE-CONSUMER-ADAPTER/0.1.0",
            "adapter_version": KNOWLEDGE_READ_ADAPTER_VERSION,
            "consumer": consumer,
            "repository_version": self.repository.version,
            "snapshot_ids": [item["snapshot_id"] for item in snapshots],
            "candidate_only": candidate_only,
            "promotion_allowed": False,
            "runtime_mutation_performed": False,
            "canonical_document_mutation_performed": False,
            "retrieval": result,
        }

    def for_phase2(self, query: str, **kwargs) -> dict[str, Any]:
        return self.query("PHASE2", query, **kwargs)

    def for_phase4(self, query: str, **kwargs) -> dict[str, Any]:
        return self.query("PHASE4", query, **kwargs)

    def for_phase5(self, query: str, **kwargs) -> dict[str, Any]:
        return self.query("PHASE5", query, **kwargs)

    def for_phase6_candidate(self, query: str, **kwargs) -> dict[str, Any]:
        return self.query("PHASE6", query, **kwargs)


__all__ = ["KNOWLEDGE_READ_ADAPTER_VERSION", "KnowledgeReadAdapter", "KnowledgeIntegrationError"]
