"""Shared application service for Phase 7 knowledge inspection."""
from __future__ import annotations
from typing import Any
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from tools.phase7_knowledge_integration import KnowledgeReadAdapter
from tools.phase7_knowledge_relations import reconcile_relations

KNOWLEDGE_INSPECTION_VERSION = "usg-knowledge-inspection/0.1.0"


class KnowledgeInspectionService:
    """Read-only inspection facade shared by the local API, CLI, and Kernel Lab."""

    def __init__(self, repository: SQLiteKnowledgeRepository):
        if not isinstance(repository, SQLiteKnowledgeRepository):
            raise TypeError("repository must be an existing SQLiteKnowledgeRepository")
        self.repository = repository
        self.read_adapter = KnowledgeReadAdapter(repository)

    def list_bundles(self, limit: int = 100) -> dict[str, Any]:
        snapshots = self.repository.list_snapshots(limit=limit)
        return {
            "contract": "USG-KNOWLEDGE-INSPECTION/0.1.0",
            "service_version": KNOWLEDGE_INSPECTION_VERSION,
            "count": len(snapshots), "bundles": list(snapshots),
        }

    def query(self, query: str, *, consumer: str = "PHASE2", language: str | None = None,
              context_filters: dict[str, str] | None = None,
              include_candidate_evidence: bool = False, limit: int = 20) -> dict[str, Any]:
        return self.read_adapter.query(
            consumer, query, language=language, context_filters=context_filters,
            include_candidate_evidence=include_candidate_evidence, limit=limit,
        )

    def inspect_record(self, record_id: str) -> dict[str, Any] | None:
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be non-empty")
        for metadata in self.repository.list_snapshots(limit=500):
            snapshot = self.repository.get_snapshot(metadata["snapshot_id"])
            if snapshot is None:
                continue
            bundle = snapshot.bundle
            record = next((item for item in bundle["records"] if item["id"] == record_id), None)
            if record is None:
                continue
            source_map = {item["id"]: item for item in bundle["sources"]}
            evidence_map = {item["id"]: item for item in bundle["evidence"]}
            context_map = {item["id"]: item for item in bundle["contexts"]}
            evidence = [evidence_map[item] for item in record.get("evidence_ids", []) if item in evidence_map]
            source_ids = sorted(set(record.get("source_ids", [])) | {item["source_id"] for item in evidence})
            return {
                "contract": "USG-KNOWLEDGE-RECORD-INSPECTION/0.1.0",
                "record": record, "bundle": snapshot.metadata(),
                "sources": [source_map[item] for item in source_ids if item in source_map],
                "evidence": evidence,
                "contexts": [context_map[item] for item in record.get("context_ids", []) if item in context_map],
                "mappings": [item for item in bundle["mappings"]
                             if item["source_record_id"] == record_id or item["target_record_id"] == record_id],
                "relations": [item for item in bundle["relations"]
                              if item["subject_record_id"] == record_id or item["object_record_id"] == record_id],
                "truth_adjudicated": False, "promotion_performed": False,
            }
        return None

    def list_conflicts(self) -> dict[str, Any]:
        conflicts = []
        for metadata in self.repository.list_snapshots(limit=500):
            snapshot = self.repository.get_snapshot(metadata["snapshot_id"])
            if snapshot is None or not snapshot.bundle.get("relations"):
                continue
            report = reconcile_relations(snapshot.bundle)
            for claim in report["claims"]:
                if claim["disposition"] == "CONFLICT":
                    conflicts.append({"bundle": snapshot.metadata(), **claim})
        conflicts.sort(key=lambda item: (item["bundle"]["bundle_id"], item["subject_record_id"],
                                         item["predicate"], item["object_record_id"]))
        return {
            "contract": "USG-KNOWLEDGE-CONFLICT-LEDGER/0.1.0",
            "service_version": KNOWLEDGE_INSPECTION_VERSION,
            "count": len(conflicts), "conflicts": conflicts,
            "winner_selected": False, "truth_adjudicated": False,
        }


__all__ = ["KNOWLEDGE_INSPECTION_VERSION", "KnowledgeInspectionService"]
