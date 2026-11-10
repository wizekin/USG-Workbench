"""Immutable, revisioned SQLite storage for complete USG-SEM/1.0 documents."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from .canonical import (
    CANONICALIZATION_PROFILE,
    CanonicalizationError,
    canonical_bytes,
    parse_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
MIGRATION_VERSION = 1


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
            "document_id": self.document_id,
            "revision": self.revision,
            "predecessor_revision": self.predecessor_revision,
            "sha256": self.digest,
            "canonicalization_profile": self.canonicalization_profile,
            "created_at": self.created_at,
            "status": self.status,
        }


class CanonicalDocumentStore:
    """SQLite store whose authoritative value is a complete canonical document snapshot.

    Normalized tables are derived indexes only. Revisions are append-only, and
    every write is atomic with its index rows and current-revision pointer.
    """

    def __init__(
        self,
        path: str | Path = ":memory:",
        schema: dict[str, Any] | None = None,
        busy_timeout_ms: int = 5000,
    ):
        self.path = str(path)
        self.schema = schema if schema is not None else json.loads(
            DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(self.schema)
        self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self._lock = threading.RLock()
        self._closed = False
        self._memory = self.path == ":memory:"
        self._connection = sqlite3.connect(
            self.path,
            isolation_level=None,
            check_same_thread=False,
            timeout=busy_timeout_ms / 1000,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        self._connection.execute("PRAGMA synchronous=FULL")
        if not self._memory:
            self._connection.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True

    def __enter__(self) -> "CanonicalDocumentStore":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise GraphStoreError("store is closed")

    def _migrate(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            migration_name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            current_revision INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS document_revisions (
            document_id TEXT NOT NULL,
            revision INTEGER NOT NULL CHECK (revision > 0),
            profile_id TEXT NOT NULL,
            canonicalization_profile TEXT NOT NULL,
            canonical_json BLOB NOT NULL,
            sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
            predecessor_revision INTEGER,
            created_at TEXT NOT NULL,
            PRIMARY KEY (document_id, revision),
            FOREIGN KEY (document_id) REFERENCES documents(document_id),
            FOREIGN KEY (document_id, predecessor_revision)
                REFERENCES document_revisions(document_id, revision)
                DEFERRABLE INITIALLY DEFERRED
        );

        CREATE TABLE IF NOT EXISTS expression_index (
            document_id TEXT NOT NULL,
            revision INTEGER NOT NULL,
            expression_id TEXT NOT NULL,
            expression_sort TEXT,
            semantic_kind TEXT,
            operator TEXT NOT NULL,
            params_json TEXT NOT NULL,
            PRIMARY KEY (document_id, revision, expression_id),
            FOREIGN KEY (document_id, revision)
                REFERENCES document_revisions(document_id, revision) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS assertion_index (
            document_id TEXT NOT NULL,
            revision INTEGER NOT NULL,
            assertion_id TEXT NOT NULL,
            expression_ref TEXT NOT NULL,
            context_ref TEXT,
            context_kind TEXT NOT NULL,
            commitment TEXT NOT NULL,
            epistemic_status TEXT NOT NULL,
            PRIMARY KEY (document_id, revision, assertion_id),
            FOREIGN KEY (document_id, revision)
                REFERENCES document_revisions(document_id, revision) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS evidence_index (
            document_id TEXT NOT NULL,
            revision INTEGER NOT NULL,
            evidence_id TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            span_start INTEGER NOT NULL,
            span_end INTEGER NOT NULL,
            alignment_status TEXT NOT NULL,
            semantic_support_status TEXT NOT NULL,
            PRIMARY KEY (document_id, revision, evidence_id),
            FOREIGN KEY (document_id, revision)
                REFERENCES document_revisions(document_id, revision) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS source_index (
            document_id TEXT NOT NULL,
            revision INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            language TEXT NOT NULL,
            source_type TEXT,
            PRIMARY KEY (document_id, revision, source_id),
            FOREIGN KEY (document_id, revision)
                REFERENCES document_revisions(document_id, revision) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_expression_lookup
            ON expression_index(document_id, revision, operator, expression_sort);
        CREATE INDEX IF NOT EXISTS idx_assertion_lookup
            ON assertion_index(document_id, revision, expression_ref, context_ref);
        CREATE INDEX IF NOT EXISTS idx_evidence_lookup
            ON evidence_index(document_id, revision, source_ref, span_start, span_end);
        CREATE INDEX IF NOT EXISTS idx_source_lookup
            ON source_index(document_id, revision, source_id);

        CREATE TRIGGER IF NOT EXISTS immutable_document_revision_update
        BEFORE UPDATE ON document_revisions
        BEGIN
            SELECT RAISE(ABORT, 'document revisions are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS immutable_document_revision_delete
        BEFORE DELETE ON document_revisions
        BEGIN
            SELECT RAISE(ABORT, 'document revisions are immutable');
        END;
        """
        now = self._now()
        with self._lock:
            safe_now = now.replace("'", "''")
            script = (
                "BEGIN IMMEDIATE;\n"
                + ddl
                + "\nINSERT OR IGNORE INTO schema_migrations(version,migration_name,applied_at) "
                + f"VALUES({MIGRATION_VERSION},'initial-canonical-document-store','{safe_now}');\n"
                + "COMMIT;"
            )
            try:
                self._connection.executescript(script)
            except BaseException:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

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
            raise InvalidDocumentError([f"GROUNDING_VALIDATION_ERROR:{type(exc).__name__}:{exc}"]) from exc
        if grounding.validation_errors:
            raise InvalidDocumentError(
                ["REFERENCE:" + str(item) for item in grounding.validation_errors]
            )

    @staticmethod
    def _index_rows(document: dict[str, Any]) -> dict[str, list[tuple]]:
        document_id = document["documentId"]
        expressions = [
            (
                document_id, 0, item["id"], item.get("sort"), item.get("semanticKind"),
                item["op"], json.dumps(item.get("params", {}), ensure_ascii=False,
                                       sort_keys=True, separators=(",", ":"), allow_nan=False),
            )
            for item in document.get("expressions", [])
        ]
        assertions = []
        for item in document.get("assertions", []):
            context = item.get("evaluationContext", {})
            assertions.append((
                document_id, 0, item["id"], item["expressionRef"],
                context.get("contextRef"), context["kind"], item["commitment"],
                item["epistemicStatus"],
            ))
        evidence = [
            (
                document_id, 0, item["id"], item["sourceRef"],
                item["span"]["start"], item["span"]["end"],
                item["alignmentStatus"], item["semanticSupportStatus"],
            )
            for item in document.get("evidence", [])
        ]
        sources = [
            (
                document_id, 0, item["id"],
                item.get("textHash") or sha256(item["text"].encode("utf-8")).hexdigest(),
                item["language"], item.get("sourceType"),
            )
            for item in document.get("sources", [])
        ]
        return {
            "expression_index": expressions,
            "assertion_index": assertions,
            "evidence_index": evidence,
            "source_index": sources,
        }

    def _write_indexes(self, document: dict[str, Any], revision: int) -> None:
        rows = self._index_rows(document)
        tables = {
            "expression_index": ("document_id,revision,expression_id,expression_sort,semantic_kind,operator,params_json",),
            "assertion_index": ("document_id,revision,assertion_id,expression_ref,context_ref,context_kind,commitment,epistemic_status",),
            "evidence_index": ("document_id,revision,evidence_id,source_ref,span_start,span_end,alignment_status,semantic_support_status",),
            "source_index": ("document_id,revision,source_id,source_hash,language,source_type",),
        }
        for table, (columns,) in tables.items():
            payload = [tuple(revision if index == 1 else value for index, value in enumerate(row)) for row in rows[table]]
            placeholders = ",".join("?" for _ in range(len(payload[0]))) if payload else None
            if payload:
                self._connection.executemany(
                    f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                    payload,
                )

    def put_document(
        self,
        document: dict[str, Any],
        expected_revision: int | None = None,
    ) -> StoredDocument:
        """Create a document or append a revision using compare-and-swap semantics.

        A first write accepts expected_revision=None or 0. An update requires
        the exact current revision. Repeating the current identical snapshot is
        idempotent and returns the existing revision.
        """
        self._ensure_open()
        self._validate_document(document)
        document_id = document["documentId"]
        raw = canonical_bytes(document)
        digest = sha256(raw).hexdigest()
        now = self._now()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                current = self._connection.execute(
                    "SELECT current_revision,created_at FROM documents WHERE document_id=?",
                    (document_id,),
                ).fetchone()
                if current is None:
                    if expected_revision not in (None, 0):
                        raise RevisionConflictError(document_id, 0, expected_revision)
                    revision = 1
                    predecessor = None
                    self._connection.execute(
                        "INSERT INTO documents(document_id,profile_id,current_revision,created_at,updated_at) VALUES(?,?,?,?,?)",
                        (document_id, document["profileId"], 0, now, now),
                    )
                else:
                    current_revision = int(current["current_revision"])
                    existing = self._connection.execute(
                        "SELECT sha256,canonicalization_profile,created_at,predecessor_revision,canonical_json "
                        "FROM document_revisions WHERE document_id=? AND revision=?",
                        (document_id, current_revision),
                    ).fetchone()
                    if existing and existing["sha256"] == digest:
                        existing_document = parse_canonical(bytes(existing["canonical_json"]))
                        self._connection.execute("COMMIT")
                        return StoredDocument(
                            document_id, current_revision, existing["predecessor_revision"],
                            digest, existing["canonicalization_profile"], existing["created_at"],
                            existing_document, "UNCHANGED",
                        )
                    if expected_revision is None or expected_revision != current_revision:
                        raise RevisionConflictError(document_id, current_revision, expected_revision)
                    revision = current_revision + 1
                    predecessor = current_revision

                self._connection.execute(
                    "INSERT INTO document_revisions(document_id,revision,profile_id,canonicalization_profile,canonical_json,sha256,predecessor_revision,created_at) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (
                        document_id, revision, document["profileId"], CANONICALIZATION_PROFILE,
                        sqlite3.Binary(raw), digest, predecessor, now,
                    ),
                )
                self._write_indexes(document, revision)
                self._connection.execute(
                    "UPDATE documents SET current_revision=?,updated_at=? WHERE document_id=?",
                    (revision, now, document_id),
                )
                self._connection.execute("COMMIT")
            except BaseException:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise
        return StoredDocument(
            document_id, revision, predecessor, digest,
            CANONICALIZATION_PROFILE, now, json.loads(raw.decode("utf-8")), "STORED",
        )

    def _read_revision(self, document_id: str, revision: int | None = None) -> sqlite3.Row:
        if revision is None:
            row = self._connection.execute(
                "SELECT r.* FROM documents d JOIN document_revisions r "
                "ON r.document_id=d.document_id AND r.revision=d.current_revision WHERE d.document_id=?",
                (document_id,),
            ).fetchone()
        else:
            row = self._connection.execute(
                "SELECT * FROM document_revisions WHERE document_id=? AND revision=?",
                (document_id, revision),
            ).fetchone()
        if row is None:
            raise DocumentNotFoundError(
                f"document revision not found: {document_id}" +
                (f"@{revision}" if revision is not None else "")
            )
        return row

    def _verify_index_rows(self, document: dict[str, Any], revision: int) -> None:
        expected = self._index_rows(document)
        for table, rows in expected.items():
            expected_rows = {
                tuple(revision if index == 1 else value for index, value in enumerate(row))
                for row in rows
            }
            actual_rows = {
                tuple(row)
                for row in self._connection.execute(
                    f"SELECT * FROM {table} WHERE document_id=? AND revision=?",
                    (document["documentId"], revision),
                ).fetchall()
            }
            if actual_rows != expected_rows:
                raise IntegrityError(f"derived index drift detected in {table}")

    def get_document(self, document_id: str, revision: int | None = None) -> StoredDocument:
        self._ensure_open()
        with self._lock:
            row = self._read_revision(document_id, revision)
            raw = bytes(row["canonical_json"])
            if sha256(raw).hexdigest() != row["sha256"]:
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
            self._verify_index_rows(document, int(row["revision"]))
            return StoredDocument(
                document_id, int(row["revision"]), row["predecessor_revision"],
                row["sha256"], row["canonicalization_profile"], row["created_at"],
                document, "VERIFIED",
            )

    def list_revisions(self, document_id: str) -> list[dict[str, Any]]:
        self._ensure_open()
        with self._lock:
            exists = self._connection.execute(
                "SELECT 1 FROM documents WHERE document_id=?", (document_id,)
            ).fetchone()
            if not exists:
                raise DocumentNotFoundError(f"document not found: {document_id}")
            rows = self._connection.execute(
                "SELECT revision,sha256,predecessor_revision,created_at,canonicalization_profile "
                "FROM document_revisions WHERE document_id=? ORDER BY revision",
                (document_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def rebuild_indexes(self, document_id: str, revision: int | None = None) -> dict[str, int]:
        """Rebuild derived indexes from a verified canonical snapshot."""
        self._ensure_open()
        with self._lock:
            row = self._read_revision(document_id, revision)
            raw = bytes(row["canonical_json"])
            if sha256(raw).hexdigest() != row["sha256"]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch; refusing index rebuild")
            try:
                document = parse_canonical(raw)
            except CanonicalizationError as exc:
                raise IntegrityError(str(exc)) from exc
            self._validate_document(document)
            selected_revision = int(row["revision"])
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                for table in ("expression_index", "assertion_index", "evidence_index", "source_index"):
                    self._connection.execute(
                        f"DELETE FROM {table} WHERE document_id=? AND revision=?",
                        (document_id, selected_revision),
                    )
                self._write_indexes(document, selected_revision)
                self._connection.execute("COMMIT")
            except BaseException:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise
            counts = {}
            for table in ("expression_index", "assertion_index", "evidence_index", "source_index"):
                counts[table] = int(self._connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE document_id=? AND revision=?",
                    (document_id, selected_revision),
                ).fetchone()[0])
            return counts

    def verify_integrity(self, document_id: str, revision: int | None = None) -> dict[str, Any]:
        try:
            stored = self.get_document(document_id, revision)
            return {
                "status": "PASS",
                **stored.metadata(),
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
                "status": "FAIL",
                "document_id": document_id,
                "revision": revision,
                "diagnostics": [f"{type(exc).__name__}:{exc}"],
            }
