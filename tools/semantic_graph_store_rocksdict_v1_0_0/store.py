"""RocksDB-backed evaluation adapter for the USG-SEM/1.0 canonical store.

Canonical snapshots are authoritative. Every revision, index row, and current
pointer is committed in one RocksDB WriteBatch. A portable OS file lock
serializes compare-and-swap writers across processes.
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
from typing import Any, Iterator
from urllib.parse import quote

from jsonschema import Draft202012Validator, FormatChecker
from rocksdict import Options, Rdict, WriteBatch

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_graph_store_v1_0_0.canonical import (
    CANONICALIZATION_PROFILE,
    CanonicalizationError,
    canonical_bytes,
    parse_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
INDEX_FAMILIES = ("expression", "assertion", "evidence", "source")


class GraphStoreError(RuntimeError):
    pass


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
            "document_id": self.document_id,
            "revision": self.revision,
            "predecessor_revision": self.predecessor_revision,
            "sha256": self.digest,
            "canonicalization_profile": self.canonicalization_profile,
            "created_at": self.created_at,
            "status": self.status,
        }


def _encode_id(value: str) -> str:
    return quote(value, safe="")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _decode_json(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"))


class CanonicalDocumentStore:
    """RocksDB canonical store using byte-only keys/values and atomic batches."""

    def __init__(self, path: str | Path, schema: dict[str, Any] | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.schema = schema if schema is not None else json.loads(
            DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(self.schema)
        self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self._lock = threading.RLock()
        self._closed = False
        options = Options(raw_mode=True)
        options.create_if_missing(True)
        self._db = Rdict(str(self.path), options)
        self._lock_path = self.path.with_name(self.path.name + ".usg-writer.lock")

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._db.flush_wal(True)
                self._db.close()
                self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _ensure_open(self):
        if self._closed:
            raise GraphStoreError("store is closed")

    @contextmanager
    def _writer_lock(self):
        """Cross-process exclusive lock; OS releases it automatically after process death."""
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

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _doc_prefix(document_id: str) -> bytes:
        return b"D/" + _encode_id(document_id).encode("ascii") + b"/"

    @classmethod
    def _current_key(cls, document_id: str) -> bytes:
        return cls._doc_prefix(document_id) + b"current"

    @classmethod
    def _revision_prefix(cls, document_id: str) -> bytes:
        return cls._doc_prefix(document_id) + b"revision/"

    @classmethod
    def _revision_key(cls, document_id: str, revision: int) -> bytes:
        return cls._revision_prefix(document_id) + f"{revision:020d}".encode("ascii")

    @classmethod
    def _snapshot_key(cls, document_id: str, revision: int) -> bytes:
        return cls._doc_prefix(document_id) + b"snapshot/" + f"{revision:020d}".encode("ascii")

    @classmethod
    def _index_prefix(cls, family: str, document_id: str, revision: int) -> bytes:
        return (
            b"I/" + family.encode("ascii") + b"/" + _encode_id(document_id).encode("ascii")
            + b"/" + f"{revision:020d}".encode("ascii") + b"/"
        )

    @classmethod
    def _index_key(cls, family: str, document_id: str, revision: int, record_id: str) -> bytes:
        # Hashing only the record component keeps physical keys bounded while
        # the full record ID remains in the value and is verified on reads.
        suffix = sha256(record_id.encode("utf-8")).hexdigest().encode("ascii")
        return cls._index_prefix(family, document_id, revision) + suffix

    @staticmethod
    def _get(view, key: bytes) -> bytes | None:
        try:
            value = view.get(key)
        except AttributeError:
            try:
                value = view[key]
            except KeyError:
                return None
        return bytes(value) if value is not None else None

    @staticmethod
    def _items_from(view, prefix: bytes) -> Iterator[tuple[bytes, bytes]]:
        iterator = view.items(from_key=prefix)
        try:
            for key, value in iterator:
                key = bytes(key)
                if not key.startswith(prefix):
                    break
                yield key, bytes(value)
        finally:
            del iterator

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
    def _index_rows(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        rows: dict[str, list[dict[str, Any]]] = {
            "expression": [], "assertion": [], "evidence": [], "source": []
        }
        for item in document.get("expressions", []):
            rows["expression"].append({
                "id": item["id"], "sort": item.get("sort"),
                "semanticKind": item.get("semanticKind"), "op": item["op"],
                "params": item.get("params", {}),
            })
        for item in document.get("assertions", []):
            context = item.get("evaluationContext", {})
            rows["assertion"].append({
                "id": item["id"], "expressionRef": item["expressionRef"],
                "contextRef": context.get("contextRef"), "contextKind": context["kind"],
                "commitment": item["commitment"], "epistemicStatus": item["epistemicStatus"],
            })
        for item in document.get("evidence", []):
            rows["evidence"].append({
                "id": item["id"], "sourceRef": item["sourceRef"],
                "span": item["span"], "alignmentStatus": item["alignmentStatus"],
                "semanticSupportStatus": item["semanticSupportStatus"],
            })
        for item in document.get("sources", []):
            rows["source"].append({
                "id": item["id"],
                "sourceHash": item.get("textHash") or sha256(item["text"].encode("utf-8")).hexdigest(),
                "language": item["language"], "sourceType": item.get("sourceType"),
            })
        return rows

    def put_document(self, document: dict[str, Any], expected_revision: int | None = None) -> StoredDocument:
        self._ensure_open()
        self._validate_document(document)
        document_id = document["documentId"]
        raw = canonical_bytes(document)
        digest = sha256(raw).hexdigest()
        now = self._now()
        with self._lock, self._writer_lock():
            current_raw = self._get(self._db, self._current_key(document_id))
            current = _decode_json(current_raw) if current_raw else None
            if current is None:
                if expected_revision not in (None, 0):
                    raise RevisionConflictError(document_id, 0, expected_revision)
                revision, predecessor = 1, None
                created_at = now
            else:
                current_revision = int(current["revision"])
                existing = self.get_document(document_id, current_revision)
                if existing.digest == digest:
                    return StoredDocument(
                        document_id, existing.revision, existing.predecessor_revision,
                        digest, existing.canonicalization_profile, existing.created_at,
                        existing.document, "UNCHANGED",
                    )
                if expected_revision is None or expected_revision != current_revision:
                    raise RevisionConflictError(document_id, current_revision, expected_revision)
                revision, predecessor = current_revision + 1, current_revision
                created_at = current["created_at"]

            revision_meta = {
                "document_id": document_id, "revision": revision,
                "predecessor_revision": predecessor, "profile_id": document["profileId"],
                "canonicalization_profile": CANONICALIZATION_PROFILE,
                "sha256": digest, "created_at": now,
            }
            current_meta = {
                "document_id": document_id, "profile_id": document["profileId"],
                "revision": revision, "created_at": created_at, "updated_at": now,
            }
            batch = WriteBatch(raw_mode=True)
            batch.put(self._revision_key(document_id, revision), _json_bytes(revision_meta))
            batch.put(self._snapshot_key(document_id, revision), raw)
            for family, items in self._index_rows(document).items():
                for item in items:
                    batch.put(
                        self._index_key(family, document_id, revision, item["id"]),
                        _json_bytes(item),
                    )
            batch.put(self._current_key(document_id), _json_bytes(current_meta))
            self._db.write(batch)
            # WriteBatch is atomic; synchronously flush its WAL record for durability.
            self._db.flush_wal(True)
            return StoredDocument(
                document_id, revision, predecessor, digest, CANONICALIZATION_PROFILE,
                now, parse_canonical(raw), "STORED",
            )

    def _read_revision(self, view, document_id: str, revision: int | None = None):
        if revision is None:
            current_raw = self._get(view, self._current_key(document_id))
            if current_raw is None:
                raise DocumentNotFoundError(f"document not found: {document_id}")
            revision = int(_decode_json(current_raw)["revision"])
        meta_raw = self._get(view, self._revision_key(document_id, revision))
        snapshot_raw = self._get(view, self._snapshot_key(document_id, revision))
        if meta_raw is None or snapshot_raw is None:
            raise DocumentNotFoundError(f"document revision not found: {document_id}@{revision}")
        return _decode_json(meta_raw), snapshot_raw

    def _verify_indexes(self, view, document: dict[str, Any], revision: int) -> None:
        expected = self._index_rows(document)
        for family, items in expected.items():
            prefix = self._index_prefix(family, document["documentId"], revision)
            actual = {
                key: value for key, value in self._items_from(view, prefix)
            }
            wanted = {
                self._index_key(family, document["documentId"], revision, item["id"]):
                    _json_bytes(item)
                for item in items
            }
            if actual != wanted:
                raise IntegrityError(f"derived index drift detected in {family}_index")

    def get_document(self, document_id: str, revision: int | None = None) -> StoredDocument:
        self._ensure_open()
        snapshot = self._db.snapshot()
        try:
            meta, raw = self._read_revision(snapshot, document_id, revision)
            digest = sha256(raw).hexdigest()
            if digest != meta["sha256"]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch")
            if meta["canonicalization_profile"] != CANONICALIZATION_PROFILE:
                raise IntegrityError("unsupported canonicalization profile")
            try:
                document = parse_canonical(raw)
            except CanonicalizationError as exc:
                raise IntegrityError(str(exc)) from exc
            self._validate_document(document)
            if document.get("documentId") != document_id or document.get("profileId") != meta["profile_id"]:
                raise IntegrityError("snapshot identity/profile does not match revision metadata")
            self._verify_indexes(snapshot, document, int(meta["revision"]))
            return StoredDocument(
                document_id, int(meta["revision"]), meta["predecessor_revision"],
                digest, meta["canonicalization_profile"], meta["created_at"], document, "VERIFIED",
            )
        finally:
            del snapshot

    def list_revisions(self, document_id: str) -> list[dict[str, Any]]:
        self._ensure_open()
        prefix = self._revision_prefix(document_id)
        snapshot = self._db.snapshot()
        try:
            rows = [_decode_json(value) for _, value in self._items_from(snapshot, prefix)]
            if not rows:
                raise DocumentNotFoundError(f"document not found: {document_id}")
            return [{
                "revision": item["revision"], "sha256": item["sha256"],
                "predecessor_revision": item["predecessor_revision"],
                "created_at": item["created_at"],
                "canonicalization_profile": item["canonicalization_profile"],
            } for item in sorted(rows, key=lambda item: item["revision"])]
        finally:
            del snapshot

    def rebuild_indexes(self, document_id: str, revision: int | None = None) -> dict[str, int]:
        self._ensure_open()
        with self._lock, self._writer_lock():
            meta, raw = self._read_revision(self._db, document_id, revision)
            if sha256(raw).hexdigest() != meta["sha256"]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch; refusing index rebuild")
            document = parse_canonical(raw)
            self._validate_document(document)
            if document.get("documentId") != document_id or document.get("profileId") != meta["profile_id"]:
                raise IntegrityError("snapshot identity/profile does not match revision metadata")
            selected = int(meta["revision"])
            batch = WriteBatch(raw_mode=True)
            counts = {}
            for family, items in self._index_rows(document).items():
                prefix = self._index_prefix(family, document_id, selected)
                for key, _ in self._items_from(self._db, prefix):
                    batch.delete(key)
                for item in items:
                    batch.put(self._index_key(family, document_id, selected, item["id"]), _json_bytes(item))
                counts[family + "_index"] = len(items)
            self._db.write(batch)
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
