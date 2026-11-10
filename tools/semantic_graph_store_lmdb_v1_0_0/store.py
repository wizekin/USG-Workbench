"""Immutable, revisioned LMDB storage for complete USG-SEM/1.0 documents.

Canonical snapshots are authoritative. All named-database indexes are rebuildable
projections committed atomically with the snapshot and revision pointer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import threading
from typing import Any, Callable

import lmdb
from jsonschema import Draft202012Validator, FormatChecker

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_graph_store_v1_0_0.canonical import (
    CANONICALIZATION_PROFILE, CanonicalizationError, canonical_bytes, parse_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
INDEX_FAMILIES = ("expression_index", "assertion_index", "evidence_index", "source_index")


class GraphStoreError(RuntimeError):
    """Base class for deterministic graph-store failures."""


class InvalidDocumentError(GraphStoreError):
    def __init__(self, diagnostics: list[str]):
        self.diagnostics = tuple(diagnostics)
        super().__init__("document validation failed: " + "; ".join(diagnostics))


class DocumentNotFoundError(GraphStoreError):
    pass


class RevisionConflictError(GraphStoreError):
    def __init__(self, document_id: str, current_revision: int, expected_revision: int | None):
        self.document_id = document_id
        self.current_revision = current_revision
        self.expected_revision = expected_revision
        super().__init__(
            f"revision conflict for {document_id}: current={current_revision}, "
            f"expected={expected_revision}"
        )


class IntegrityError(GraphStoreError):
    pass


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

    def metadata(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id, "revision": self.revision,
            "predecessor_revision": self.predecessor_revision, "sha256": self.digest,
            "canonicalization_profile": self.canonicalization_profile,
            "created_at": self.created_at, "status": self.status,
        }


class CanonicalDocumentStore:
    """LMDB implementation of the Phase 3 canonical graph-store contract.

    LMDB permits many concurrent readers and serializes write transactions. A
    single LMDB transaction spans all named databases, so snapshots, immutable
    revision metadata, indexes, and the current pointer commit atomically.
    """

    def __init__(
        self,
        path: str | Path,
        schema: dict[str, Any] | None = None,
        map_size: int = 1 << 40,
        max_readers: int = 256,
        lock: bool = True,
    ):
        if path is None:
            raise ValueError("LMDB requires a filesystem directory; use a temporary directory for tests")
        self.path = str(path)
        self.schema = schema if schema is not None else json.loads(
            DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(self.schema)
        self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self._lock = threading.RLock()
        self._closed = False
        self._temporary = None
        Path(self.path).mkdir(parents=True, exist_ok=True)
        self._env = lmdb.open(
            self.path, subdir=True, create=True, map_size=map_size, max_dbs=8,
            max_readers=max_readers, lock=lock, sync=True, metasync=True,
            writemap=False, map_async=False, readahead=True, meminit=True,
        )
        self._db = {
            name: self._env.open_db(name.encode("ascii"), create=True)
            for name in (
                "documents", "revisions", "snapshots", "expression_index",
                "assertion_index", "evidence_index", "source_index", "migrations",
            )
        }
        self._initialize()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._env.close()
                self._closed = True
                if self._temporary is not None:
                    self._temporary.cleanup()

    def __enter__(self) -> "CanonicalDocumentStore":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise GraphStoreError("store is closed")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _key(*parts: Any) -> bytes:
        # Hash keys avoid LMDB's finite key-size limit for long document/record IDs.
        return sha256(canonical_bytes(list(parts))).digest()

    @staticmethod
    def _revision_key(document_id: str, revision: int) -> bytes:
        return CanonicalDocumentStore._key(document_id) + int(revision).to_bytes(8, "big")

    @staticmethod
    def _index_prefix(document_id: str, revision: int) -> bytes:
        return CanonicalDocumentStore._revision_key(document_id, revision)

    @staticmethod
    def _index_key(document_id: str, revision: int, record_id: str) -> bytes:
        return (
            CanonicalDocumentStore._index_prefix(document_id, revision)
            + sha256(record_id.encode("utf-8")).digest()
        )

    @staticmethod
    def _encode(value: Any) -> bytes:
        return canonical_bytes(value)

    @staticmethod
    def _decode(raw: bytes | None) -> Any:
        if raw is None:
            return None
        try:
            return parse_canonical(bytes(raw))
        except CanonicalizationError as exc:
            raise IntegrityError(f"stored metadata is not canonical: {exc}") from exc

    def _initialize(self) -> None:
        migration_key = b"schema-v1"
        with self._write_txn() as txn:
            if txn.get(migration_key, db=self._db["migrations"]) is None:
                txn.put(
                    migration_key,
                    self._encode({
                        "version": 1,
                        "name": "initial-lmdb-canonical-document-store",
                        "applied_at": self._now(),
                    }),
                    db=self._db["migrations"],
                    overwrite=False,
                )

    def _write_txn(self):
        """Return a transaction; LMDB coordinates writers across processes."""
        self._ensure_open()
        return self._env.begin(write=True)

    def _validate_document(self, document: dict[str, Any]) -> None:
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
            declared_hash = source.get("textHash")
            if declared_hash is not None:
                actual_hash = sha256(source["text"].encode("utf-8")).hexdigest()
                if declared_hash.lower() != actual_hash:
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
            raise InvalidDocumentError(
                ["REFERENCE:" + str(item) for item in grounding.validation_errors]
            )

    @staticmethod
    def _index_rows(document: dict[str, Any]) -> dict[str, list[list[Any]]]:
        document_id = document["documentId"]
        expressions = [
            [document_id, 0, item["id"], item.get("sort"), item.get("semanticKind"),
             item["op"], json.dumps(item.get("params", {}), ensure_ascii=False,
                                    sort_keys=True, separators=(",", ":"), allow_nan=False)]
            for item in document.get("expressions", [])
        ]
        assertions = []
        for item in document.get("assertions", []):
            context = item.get("evaluationContext", {})
            assertions.append([
                document_id, 0, item["id"], item["expressionRef"], context.get("contextRef"),
                context["kind"], item["commitment"], item["epistemicStatus"],
            ])
        evidence = [
            [document_id, 0, item["id"], item["sourceRef"], item["span"]["start"],
             item["span"]["end"], item["alignmentStatus"], item["semanticSupportStatus"]]
            for item in document.get("evidence", [])
        ]
        sources = [
            [document_id, 0, item["id"],
             item.get("textHash") or sha256(item["text"].encode("utf-8")).hexdigest(),
             item["language"], item.get("sourceType")]
            for item in document.get("sources", [])
        ]
        return {
            "expression_index": expressions, "assertion_index": assertions,
            "evidence_index": evidence, "source_index": sources,
        }

    def _write_indexes(self, txn, document: dict[str, Any], revision: int) -> None:
        rows = self._index_rows(document)
        for family, family_rows in rows.items():
            db = self._db[family]
            for row in family_rows:
                row[1] = revision
                key = self._index_key(document["documentId"], revision, row[2])
                value = self._encode(row)
                existing = txn.get(key, db=db)
                if existing is not None and bytes(existing) != value:
                    raise IntegrityError(f"index key collision or conflicting row in {family}")
                txn.put(key, value, db=db, overwrite=True)

    def _get_revision(self, txn, document_id: str, revision: int | None = None):
        doc_key = self._key(document_id)
        doc_meta = self._decode(txn.get(doc_key, db=self._db["documents"]))
        if doc_meta is None:
            raise DocumentNotFoundError(f"document not found: {document_id}")
        selected = int(doc_meta["current_revision"] if revision is None else revision)
        revision_key = self._revision_key(document_id, selected)
        metadata = self._decode(txn.get(revision_key, db=self._db["revisions"]))
        raw = txn.get(revision_key, db=self._db["snapshots"])
        if metadata is None or raw is None:
            raise DocumentNotFoundError(f"document revision not found: {document_id}@{selected}")
        return metadata, bytes(raw), selected

    def put_document(
        self, document: dict[str, Any], expected_revision: int | None = None,
    ) -> StoredDocument:
        """Create or append a revision using atomic compare-and-swap semantics."""
        self._ensure_open()
        self._validate_document(document)
        document_id = document["documentId"]
        raw = canonical_bytes(document)
        digest = sha256(raw).hexdigest()
        now = self._now()
        with self._lock:
            with self._write_txn() as txn:
                doc_key = self._key(document_id)
                current = self._decode(txn.get(doc_key, db=self._db["documents"]))
                if current is None:
                    if expected_revision not in (None, 0):
                        raise RevisionConflictError(document_id, 0, expected_revision)
                    revision, predecessor = 1, None
                    created_at = now
                else:
                    current_revision = int(current["current_revision"])
                    rev_key = self._revision_key(document_id, current_revision)
                    metadata = self._decode(txn.get(rev_key, db=self._db["revisions"]))
                    existing_raw = txn.get(rev_key, db=self._db["snapshots"])
                    if metadata is None or existing_raw is None:
                        raise IntegrityError("current revision metadata or snapshot is missing")
                    if metadata["sha256"] == digest:
                        existing_raw = bytes(existing_raw)
                        if sha256(existing_raw).hexdigest() != metadata["sha256"]:
                            raise IntegrityError("current canonical snapshot SHA-256 mismatch")
                        existing_doc = parse_canonical(existing_raw)
                        return StoredDocument(
                            document_id, current_revision, metadata.get("predecessor_revision"),
                            digest, metadata["canonicalization_profile"], metadata["created_at"],
                            existing_doc, "UNCHANGED",
                        )
                    if expected_revision is None or expected_revision != current_revision:
                        raise RevisionConflictError(document_id, current_revision, expected_revision)
                    revision, predecessor = current_revision + 1, current_revision
                    created_at = current["created_at"]

                revision_key = self._revision_key(document_id, revision)
                revision_metadata = {
                    "document_id": document_id, "revision": revision,
                    "profile_id": document["profileId"],
                    "canonicalization_profile": CANONICALIZATION_PROFILE,
                    "sha256": digest, "predecessor_revision": predecessor,
                    "created_at": now,
                }
                if current is None:
                    txn.put(doc_key, self._encode({
                        "document_id": document_id, "profile_id": document["profileId"],
                        "current_revision": 0, "created_at": now, "updated_at": now,
                    }), db=self._db["documents"], overwrite=False)
                txn.put(revision_key, self._encode(revision_metadata), db=self._db["revisions"], overwrite=False)
                txn.put(revision_key, raw, db=self._db["snapshots"], overwrite=False)
                self._write_indexes(txn, document, revision)
                txn.put(doc_key, self._encode({
                    "document_id": document_id, "profile_id": document["profileId"],
                    "current_revision": revision, "created_at": created_at, "updated_at": now,
                }), db=self._db["documents"], overwrite=True)

        return StoredDocument(
            document_id, revision, predecessor, digest, CANONICALIZATION_PROFILE,
            now, json.loads(raw.decode("utf-8")), "STORED",
        )

    def _verify_index_rows(self, txn, document: dict[str, Any], revision: int) -> None:
        expected = self._index_rows(document)
        prefix = self._index_prefix(document["documentId"], revision)
        for family, rows in expected.items():
            db = self._db[family]
            expected_values = {}
            for row in rows:
                row[1] = revision
                expected_values[self._index_key(document["documentId"], revision, row[2])] = self._encode(row)
            actual_values = {}
            with txn.cursor(db=db) as cursor:
                if cursor.set_range(prefix):
                    while cursor.key().startswith(prefix):
                        actual_values[bytes(cursor.key())] = bytes(cursor.value())
                        if not cursor.next():
                            break
            if actual_values != expected_values:
                raise IntegrityError(f"derived index drift detected in {family}")

    def get_document(self, document_id: str, revision: int | None = None) -> StoredDocument:
        self._ensure_open()
        with self._env.begin() as txn:
            metadata, raw, selected = self._get_revision(txn, document_id, revision)
            if sha256(raw).hexdigest() != metadata["sha256"]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch")
            if metadata["canonicalization_profile"] != CANONICALIZATION_PROFILE:
                raise IntegrityError("unsupported canonicalization profile")
            try:
                document = parse_canonical(raw)
            except CanonicalizationError as exc:
                raise IntegrityError(str(exc)) from exc
            self._validate_document(document)
            if document.get("documentId") != document_id or document.get("profileId") != metadata["profile_id"]:
                raise IntegrityError("snapshot identity/profile does not match revision metadata")
            self._verify_index_rows(txn, document, selected)
            return StoredDocument(
                document_id, selected, metadata.get("predecessor_revision"),
                metadata["sha256"], metadata["canonicalization_profile"],
                metadata["created_at"], document, "VERIFIED",
            )

    def list_revisions(self, document_id: str) -> list[dict[str, Any]]:
        self._ensure_open()
        with self._env.begin() as txn:
            if txn.get(self._key(document_id), db=self._db["documents"]) is None:
                raise DocumentNotFoundError(f"document not found: {document_id}")
            revisions = []
            prefix = self._key(document_id)
            with txn.cursor(db=self._db["revisions"]) as cursor:
                if cursor.set_range(prefix):
                    while cursor.key().startswith(prefix):
                        item = self._decode(cursor.value())
                        revisions.append({
                            "revision": item["revision"], "sha256": item["sha256"],
                            "predecessor_revision": item.get("predecessor_revision"),
                            "created_at": item["created_at"],
                            "canonicalization_profile": item["canonicalization_profile"],
                        })
                        if not cursor.next():
                            break
            return sorted(revisions, key=lambda item: item["revision"])

    def rebuild_indexes(self, document_id: str, revision: int | None = None) -> dict[str, int]:
        """Rebuild derived index records from a verified authoritative snapshot."""
        self._ensure_open()
        with self._lock:
            with self._env.begin() as read_txn:
                metadata, raw, selected = self._get_revision(read_txn, document_id, revision)
            if sha256(raw).hexdigest() != metadata["sha256"]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch; refusing index rebuild")
            document = parse_canonical(raw)
            self._validate_document(document)
            if document.get("documentId") != document_id or document.get("profileId") != metadata["profile_id"]:
                raise IntegrityError("snapshot identity/profile does not match revision metadata")
            with self._write_txn() as txn:
                prefix = self._index_prefix(document_id, selected)
                for family in INDEX_FAMILIES:
                    db = self._db[family]
                    stale = []
                    with txn.cursor(db=db) as cursor:
                        if cursor.set_range(prefix):
                            while cursor.key().startswith(prefix):
                                stale.append(bytes(cursor.key()))
                                if not cursor.next():
                                    break
                    for key in stale:
                        txn.delete(key, db=db)
                self._write_indexes(txn, document, selected)
            counts = {}
            with self._env.begin() as txn:
                for family in INDEX_FAMILIES:
                    count = 0
                    prefix = self._index_prefix(document_id, selected)
                    with txn.cursor(db=self._db[family]) as cursor:
                        if cursor.set_range(prefix):
                            while cursor.key().startswith(prefix):
                                count += 1
                                if not cursor.next():
                                    break
                    counts[family] = count
            return counts

    def verify_integrity(self, document_id: str, revision: int | None = None) -> dict[str, Any]:
        try:
            stored = self.get_document(document_id, revision)
            return {
                **stored.metadata(), "status": "PASS", "document_status": stored.status,
                "record_counts": {
                    "sources": len(stored.document.get("sources", [])),
                    "expressions": len(stored.document.get("expressions", [])),
                    "assertions": len(stored.document.get("assertions", [])),
                    "evidence": len(stored.document.get("evidence", [])),
                },
                "diagnostics": [],
            }
        except GraphStoreError as exc:
            return {
                "status": "FAIL", "document_id": document_id, "revision": revision,
                "diagnostics": [f"{type(exc).__name__}:{exc}"],
            }

    def storage_stats(self) -> dict[str, Any]:
        """Return LMDB environment/page statistics without implying semantic counts."""
        self._ensure_open()
        with self._env.begin() as txn:
            return {
                "map_size_bytes": self._env.info()["map_size"],
                "last_page_number": self._env.info()["last_pgno"],
                "last_transaction_id": self._env.info()["last_txnid"],
                "databases": {
                    name: txn.stat(db=db) for name, db in self._db.items()
                },
            }
