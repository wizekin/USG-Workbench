"""LanceDB evaluation adapter: versioned canonical snapshots + rebuildable retrieval sidecar.

This is an evaluation prototype. LanceDB table versions provide snapshot history,
but there is no cross-table transaction or unique constraint enforcing USG's
per-document compare-and-swap revision rule under concurrent writers.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import threading
from typing import Any

import lancedb
from jsonschema import Draft202012Validator, FormatChecker

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_graph_store_v1_0_0.canonical import (
    CANONICALIZATION_PROFILE, CanonicalizationError, canonical_bytes, parse_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
CANONICAL_TABLE = "canonical_revisions"
RETRIEVAL_TABLE = "retrieval_records"


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


def _quote(value: str) -> str:
    return value.replace("'", "''")


class CanonicalDocumentStore:
    """Append-only canonical revision table with a rebuildable retrieval sidecar."""

    def __init__(self, path: str | Path, schema: dict[str, Any] | None = None):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.schema = schema if schema is not None else json.loads(
            DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(self.schema)
        self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self._db = lancedb.connect(self.path)
        self._lock = threading.RLock()
        self._closed = False
        self._lock_path = Path(self.path).with_name(Path(self.path).name + ".usg-writer.lock")
        self._table = self._open_or_create_canonical_table()

    @contextmanager
    def _writer_lock(self):
        """Serialize adapter writers across processes on the same local filesystem."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self._lock_path, "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                if handle.read(1) == b"":
                    handle.seek(0)
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    def _open_or_create_canonical_table(self):
        names = self._db.table_names()
        if CANONICAL_TABLE in names:
            return self._db.open_table(CANONICAL_TABLE)
        # Create a typed empty table; first put_document uses add().
        import pyarrow as pa
        schema = pa.schema([
            pa.field("document_id", pa.string()),
            pa.field("revision", pa.int64()),
            pa.field("predecessor_revision", pa.int64()),
            pa.field("profile_id", pa.string()),
            pa.field("canonicalization_profile", pa.string()),
            pa.field("canonical_json", pa.large_string()),
            pa.field("sha256", pa.string()),
            pa.field("created_at", pa.string()),
        ])
        return self._db.create_table(CANONICAL_TABLE, schema=schema)

    def close(self):
        # LanceDB connections are lightweight and have no required close call.
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
        if diagnostics:
            raise InvalidDocumentError(diagnostics)
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

    def _rows_for_document(self, document_id: str) -> list[dict[str, Any]]:
        # Refresh the table handle to observe commits made by another adapter instance.
        self._table = self._db.open_table(CANONICAL_TABLE)
        filter_expr = f"document_id = '{_quote(document_id)}'"
        return self._table.search().where(filter_expr).to_arrow().to_pylist()

    def put_document(self, document: dict[str, Any], expected_revision: int | None = None):
        self._ensure_open()
        self._validate_document(document)
        did = document["documentId"]
        raw = canonical_bytes(document)
        digest = sha256(raw).hexdigest()
        now = self._now()
        with self._lock, self._writer_lock():
            # Reopen the table handle after acquiring the cross-process lock so
            # the CAS check sees the newest committed manifest.
            self._table = self._db.open_table(CANONICAL_TABLE)
            rows = self._rows_for_document(did)
            if rows:
                rows.sort(key=lambda x: x["revision"])
                revisions = [int(x["revision"]) for x in rows]
                if len(revisions) != len(set(revisions)):
                    raise IntegrityError("duplicate document revision rows detected")
                current = rows[-1]
                current_revision = int(current["revision"])
                current_raw = current["canonical_json"].encode("utf-8")
                if sha256(current_raw).hexdigest() != current["sha256"]:
                    raise IntegrityError("current canonical snapshot SHA-256 mismatch")
                if current["sha256"] == digest:
                    return StoredDocument(
                        did, current_revision, current["predecessor_revision"], digest,
                        current["canonicalization_profile"], current["created_at"],
                        parse_canonical(current_raw), "UNCHANGED",
                    )
                if expected_revision is None or expected_revision != current_revision:
                    raise RevisionConflictError(did, current_revision, expected_revision)
                revision, predecessor = current_revision + 1, current_revision
                created_at = current["created_at"]
            else:
                if expected_revision not in (None, 0):
                    raise RevisionConflictError(did, 0, expected_revision)
                revision, predecessor, created_at = 1, None, now

            # One append is atomic as a Lance table transaction. LanceDB has no
            # per-document unique conditional key, so the local OS lock makes
            # this adapter's read/check/append sequence a serialized CAS on
            # the same local filesystem. Direct table writers bypassing this
            # adapter are outside that guarantee.
            self._table.add([{
                "document_id": did, "revision": revision,
                "predecessor_revision": predecessor, "profile_id": document["profileId"],
                "canonicalization_profile": CANONICALIZATION_PROFILE,
                "canonical_json": raw.decode("utf-8"), "sha256": digest, "created_at": now,
            }])
            return StoredDocument(
                did, revision, predecessor, digest, CANONICALIZATION_PROFILE,
                now, parse_canonical(raw), "STORED",
            )

    def get_document(self, document_id: str, revision: int | None = None):
        self._ensure_open()
        rows = self._rows_for_document(document_id)
        all_revisions = [int(x["revision"]) for x in rows]
        if len(all_revisions) != len(set(all_revisions)):
            raise IntegrityError("duplicate document revision rows detected")
        if revision is not None:
            rows = [x for x in rows if int(x["revision"]) == revision]
        if not rows:
            raise DocumentNotFoundError(f"document revision not found: {document_id}")
        rows.sort(key=lambda x: x["revision"])
        row = rows[-1]
        raw = row["canonical_json"].encode("utf-8")
        digest = sha256(raw).hexdigest()
        if digest != row["sha256"]:
            raise IntegrityError("canonical snapshot SHA-256 mismatch")
        if row["canonicalization_profile"] != CANONICALIZATION_PROFILE:
            raise IntegrityError("unsupported canonicalization profile")
        try:
            document = parse_canonical(raw)
        except CanonicalizationError as exc:
            raise IntegrityError(str(exc)) from exc
        self._validate_document(document)
        if document.get("documentId") != document_id or document.get("profileId") != row["profile_id"]:
            raise IntegrityError("snapshot identity/profile does not match revision metadata")
        return StoredDocument(
            document_id, int(row["revision"]), row["predecessor_revision"], digest,
            row["canonicalization_profile"], row["created_at"], document, "VERIFIED",
        )

    def list_revisions(self, document_id: str):
        rows = self._rows_for_document(document_id)
        if not rows:
            raise DocumentNotFoundError(f"document not found: {document_id}")
        rows.sort(key=lambda x: x["revision"])
        revisions = [int(x["revision"]) for x in rows]
        if len(revisions) != len(set(revisions)):
            raise IntegrityError("duplicate document revision rows detected")
        return [{
            "revision": int(x["revision"]), "sha256": x["sha256"],
            "predecessor_revision": x["predecessor_revision"],
            "created_at": x["created_at"],
            "canonicalization_profile": x["canonicalization_profile"],
        } for x in rows]

    def rebuild_indexes(self, document_id: str, revision: int | None = None):
        # LanceDB's retrieval table is a separate, rebuildable sidecar; the
        # canonical table itself has no normalized per-record indexes.
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
        """Build or replace the optional text/vector retrieval sidecar."""
        self._ensure_open()
        if RETRIEVAL_TABLE in self._db.table_names():
            self._db.drop_table(RETRIEVAL_TABLE)
        if records:
            self._db.create_table(RETRIEVAL_TABLE, data=records)
        return len(records)

    def search_vectors(self, vector: list[float], limit: int = 10):
        if RETRIEVAL_TABLE not in self._db.table_names():
            return []
        return (
            self._db.open_table(RETRIEVAL_TABLE)
            .search(vector).limit(limit).to_arrow().to_pylist()
        )

    def search_text(self, query: str, limit: int = 10):
        if RETRIEVAL_TABLE not in self._db.table_names():
            return []
        return (
            self._db.open_table(RETRIEVAL_TABLE)
            .search(query, query_type="fts").limit(limit).to_arrow().to_pylist()
        )
