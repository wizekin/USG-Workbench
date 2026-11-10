"""Qdrant local-mode candidate adapter for USG canonical snapshot evaluation.

This is an evaluation adapter, not a production canonical-store recommendation.
Qdrant is a vector database. Canonical snapshots are stored as immutable payloads
with a neutral placeholder vector in a separate collection; real retrieval vectors
live in another collection. Qdrant local mode is single-process exclusive.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import threading
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from jsonschema import Draft202012Validator, FormatChecker
from qdrant_client import QdrantClient, models

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_graph_store_v1_0_0.canonical import (
    CANONICALIZATION_PROFILE, CanonicalizationError, canonical_bytes, parse_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
CANONICAL_COLLECTION = "usg_canonical_revisions"
RETRIEVAL_COLLECTION = "usg_retrieval_records"


class GraphStoreError(RuntimeError): pass
class DocumentNotFoundError(GraphStoreError): pass
class IntegrityError(GraphStoreError): pass


class InvalidDocumentError(GraphStoreError):
    def __init__(self, diagnostics: list[str]):
        self.diagnostics = tuple(diagnostics)
        super().__init__("document validation failed: " + "; ".join(diagnostics))


class RevisionConflictError(GraphStoreError):
    def __init__(self, document_id: str, current_revision: int, expected_revision: int | None):
        self.document_id = document_id
        self.current_revision = current_revision
        self.expected_revision = expected_revision
        super().__init__(
            f"revision conflict for {document_id}: current={current_revision}, "
            f"expected={expected_revision}"
        )


@dataclass(frozen=True)
class StoredDocument:
    document_id: str
    revision: int
    predecessor_revision: int | None
    digest: str
    canonicalization_profile: str
    created_at: str
    document: dict[str, Any]
    status: str = "STORED"

    def metadata(self):
        return {
            "document_id": self.document_id, "revision": self.revision,
            "predecessor_revision": self.predecessor_revision, "sha256": self.digest,
            "canonicalization_profile": self.canonicalization_profile,
            "created_at": self.created_at, "status": self.status,
        }


class CanonicalDocumentStore:
    """Persistent local Qdrant snapshot/payload and vector-retrieval evaluation adapter."""

    def __init__(
        self, path: str | Path, schema: dict[str, Any] | None = None,
        retrieval_vector_size: int = 4,
    ):
        if retrieval_vector_size < 1:
            raise ValueError("retrieval_vector_size must be positive")
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.schema = schema if schema is not None else json.loads(
            DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(self.schema)
        self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self._retrieval_vector_size = retrieval_vector_size
        self._lock = threading.RLock()
        self._closed = False
        # Qdrant local mode intentionally locks the storage directory to one
        # client/process. Use Qdrant server mode for multiple processes/clients.
        self._client = QdrantClient(path=self.path)
        self._ensure_collection(
            CANONICAL_COLLECTION, 1, models.Distance.DOT
        )
        self._ensure_collection(
            RETRIEVAL_COLLECTION, retrieval_vector_size, models.Distance.COSINE
        )

    def _ensure_collection(self, name, size, distance):
        if not self._client.collection_exists(name):
            self._client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(size=size, distance=distance),
            )

    def close(self):
        if not self._closed:
            self._client.close()
            self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _ensure_open(self):
        if self._closed:
            raise GraphStoreError("store is closed")

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _point_id(document_id: str, revision: int) -> str:
        return str(uuid5(NAMESPACE_URL, f"usg-sem-1.0:{document_id}:{revision}"))

    def _validate_document(self, document):
        if not isinstance(document, dict):
            raise InvalidDocumentError(["DOCUMENT_NOT_OBJECT"])
        errors = sorted(
            self._validator.iter_errors(document),
            key=lambda item: (list(item.absolute_path), item.message),
        )
        diagnostics = [
            "SCHEMA:" + "/".join(str(part) for part in error.absolute_path) + ":" + error.message
            for error in errors
        ]
        for source in document.get("sources", []):
            declared = source.get("textHash")
            if declared is not None:
                actual = sha256(source["text"].encode("utf-8")).hexdigest()
                if declared.lower() != actual:
                    diagnostics.append(f"SOURCE_HASH_MISMATCH:{source['id']}")
        if diagnostics:
            raise InvalidDocumentError(diagnostics)
        try:
            grounding = GroundingIndex(document, self.schema)
        except Exception as exc:
            raise InvalidDocumentError(
                [f"GROUNDING_VALIDATION_ERROR:{type(exc).__name__}:{exc}"]
            ) from exc
        if grounding.validation_errors:
            raise InvalidDocumentError(["REFERENCE:" + str(x) for x in grounding.validation_errors])

    def _scroll_document(self, document_id: str) -> list[Any]:
        self._ensure_open()
        scroll_filter = models.Filter(
            must=[models.FieldCondition(
                key="document_id", match=models.MatchValue(value=document_id)
            )]
        )
        records = []
        offset = None
        while True:
            points, offset = self._client.scroll(
                collection_name=CANONICAL_COLLECTION,
                scroll_filter=scroll_filter, limit=256, offset=offset,
                with_payload=True, with_vectors=False,
            )
            records.extend(points)
            if offset is None:
                break
        return records

    def _decode_record(self, point):
        payload = point.payload or {}
        raw = payload["canonical_json"].encode("utf-8")
        digest = sha256(raw).hexdigest()
        if digest != payload["sha256"]:
            raise IntegrityError("canonical snapshot SHA-256 mismatch")
        if payload["canonicalization_profile"] != CANONICALIZATION_PROFILE:
            raise IntegrityError("unsupported canonicalization profile")
        try:
            document = parse_canonical(raw)
        except CanonicalizationError as exc:
            raise IntegrityError(str(exc)) from exc
        if document.get("documentId") != payload["document_id"] or document.get("profileId") != payload["profile_id"]:
            raise IntegrityError("snapshot identity/profile does not match revision metadata")
        self._validate_document(document)
        return StoredDocument(
            payload["document_id"], int(payload["revision"]),
            payload.get("predecessor_revision"), digest,
            payload["canonicalization_profile"], payload["created_at"],
            document, "VERIFIED",
        )

    def put_document(self, document: dict[str, Any], expected_revision: int | None = None):
        self._ensure_open()
        self._validate_document(document)
        did = document["documentId"]
        raw = canonical_bytes(document)
        digest = sha256(raw).hexdigest()
        now = self._now()
        with self._lock:
            rows = self._scroll_document(did)
            rows.sort(key=lambda point: int((point.payload or {})["revision"]))
            revisions = [int((point.payload or {})["revision"]) for point in rows]
            if len(revisions) != len(set(revisions)):
                raise IntegrityError("duplicate document revision points detected")
            if rows:
                current = self._decode_record(rows[-1])
                if current.digest == digest:
                    return StoredDocument(
                        did, current.revision, current.predecessor_revision, digest,
                        current.canonicalization_profile, current.created_at,
                        current.document, "UNCHANGED",
                    )
                if expected_revision is None or expected_revision != current.revision:
                    raise RevisionConflictError(did, current.revision, expected_revision)
                revision, predecessor = current.revision + 1, current.revision
            else:
                if expected_revision not in (None, 0):
                    raise RevisionConflictError(did, 0, expected_revision)
                revision, predecessor = 1, None

            payload = {
                "document_id": did, "revision": revision,
                "predecessor_revision": predecessor, "profile_id": document["profileId"],
                "canonicalization_profile": CANONICALIZATION_PROFILE,
                "canonical_json": raw.decode("utf-8"), "sha256": digest, "created_at": now,
            }
            # The one-point upsert is waited to completion. The application lock
            # protects competing threads in this local process. There is no
            # database-native multi-operation CAS transaction.
            self._client.upsert(
                collection_name=CANONICAL_COLLECTION,
                wait=True,
                points=[models.PointStruct(
                    id=self._point_id(did, revision), vector=[1.0], payload=payload
                )],
            )
            return StoredDocument(
                did, revision, predecessor, digest, CANONICALIZATION_PROFILE,
                now, parse_canonical(raw), "STORED",
            )

    def get_document(self, document_id: str, revision: int | None = None):
        rows = self._scroll_document(document_id)
        revisions = [int((point.payload or {})["revision"]) for point in rows]
        if len(revisions) != len(set(revisions)):
            raise IntegrityError("duplicate document revision points detected")
        if revision is not None:
            rows = [point for point in rows if int((point.payload or {})["revision"]) == revision]
        if not rows:
            raise DocumentNotFoundError(f"document revision not found: {document_id}")
        rows.sort(key=lambda point: int((point.payload or {})["revision"]))
        return self._decode_record(rows[-1])

    def list_revisions(self, document_id: str):
        rows = self._scroll_document(document_id)
        if not rows:
            raise DocumentNotFoundError(f"document not found: {document_id}")
        rows.sort(key=lambda point: int((point.payload or {})["revision"]))
        revisions = [int((point.payload or {})["revision"]) for point in rows]
        if len(revisions) != len(set(revisions)):
            raise IntegrityError("duplicate document revision points detected")
        return [{
            "revision": int((point.payload or {})["revision"]),
            "sha256": (point.payload or {})["sha256"],
            "predecessor_revision": (point.payload or {}).get("predecessor_revision"),
            "created_at": (point.payload or {})["created_at"],
            "canonicalization_profile": (point.payload or {})["canonicalization_profile"],
        } for point in rows]

    def rebuild_indexes(self, document_id: str, revision: int | None = None):
        stored = self.get_document(document_id, revision)
        return {
            "canonical_revisions": 1,
            "expressions_available_for_retrieval": len(stored.document.get("expressions", [])),
            "assertions_available_for_retrieval": len(stored.document.get("assertions", [])),
            "evidence_available_for_retrieval": len(stored.document.get("evidence", [])),
            "sources_available_for_retrieval": len(stored.document.get("sources", [])),
        }

    def verify_integrity(self, document_id: str, revision: int | None = None):
        try:
            stored = self.get_document(document_id, revision)
            return {
                **stored.metadata(), "status": "PASS", "document_status": stored.status,
                "record_counts": {
                    "sources": len(stored.document.get("sources", [])),
                    "expressions": len(stored.document.get("expressions", [])),
                    "assertions": len(stored.document.get("assertions", [])),
                    "evidence": len(stored.document.get("evidence", [])),
                }, "diagnostics": [],
            }
        except GraphStoreError as exc:
            return {
                "status": "FAIL", "document_id": document_id, "revision": revision,
                "diagnostics": [f"{type(exc).__name__}:{exc}"],
            }

    def replace_retrieval_records(self, records: list[dict[str, Any]]):
        self._ensure_open()
        for item in records:
            if len(item["vector"]) != self._retrieval_vector_size:
                raise ValueError("retrieval vector has incorrect dimensionality")
        if self._client.collection_exists(RETRIEVAL_COLLECTION):
            self._client.delete_collection(RETRIEVAL_COLLECTION)
        self._client.create_collection(
            collection_name=RETRIEVAL_COLLECTION,
            vectors_config=models.VectorParams(
                size=self._retrieval_vector_size, distance=models.Distance.COSINE
            ),
        )
        if records:
            self._client.upsert(
                collection_name=RETRIEVAL_COLLECTION, wait=True,
                points=[
                    models.PointStruct(
                        id=item["record_id"], vector=item["vector"],
                        payload={k: v for k, v in item.items() if k not in ("record_id", "vector")},
                    )
                    for item in records
                ],
            )
        return len(records)

    def search_vectors(self, vector: list[float], limit: int = 10):
        self._ensure_open()
        if len(vector) != self._retrieval_vector_size:
            raise ValueError("query vector has incorrect dimensionality")
        return [
            {"record_id": str(point.id), **(point.payload or {}), "score": point.score}
            for point in self._client.query_points(
                collection_name=RETRIEVAL_COLLECTION,
                query=vector, limit=limit, with_payload=True,
            ).points
        ]
