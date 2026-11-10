"""DuckDB-backed evaluation adapter for the USG-SEM/1.0 canonical store."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import threading
from typing import Any

import duckdb
from jsonschema import Draft202012Validator, FormatChecker

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_graph_store_v1_0_0.canonical import (
    CANONICALIZATION_PROFILE, CanonicalizationError, canonical_bytes, parse_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"


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
            "document_id": self.document_id, "revision": self.revision,
            "predecessor_revision": self.predecessor_revision, "sha256": self.digest,
            "canonicalization_profile": self.canonicalization_profile,
            "created_at": self.created_at, "status": self.status,
        }


class CanonicalDocumentStore:
    """DuckDB SQL tables with complete canonical snapshots as the authority."""

    def __init__(self, path: str | Path, schema: dict[str, Any] | None = None, read_only: bool = False):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.schema = schema if schema is not None else json.loads(
            DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(self.schema)
        self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self._lock = threading.RLock()
        self._closed = False
        self._connection = duckdb.connect(self.path, read_only=read_only)
        if not read_only:
            self._migrate()

    def close(self):
        with self._lock:
            if not self._closed:
                self._connection.close()
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
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _migrate(self):
        ddl = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            migration_name VARCHAR NOT NULL,
            applied_at VARCHAR NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            document_id VARCHAR PRIMARY KEY,
            profile_id VARCHAR NOT NULL,
            current_revision BIGINT NOT NULL,
            created_at VARCHAR NOT NULL,
            updated_at VARCHAR NOT NULL
        );
        CREATE TABLE IF NOT EXISTS document_revisions (
            document_id VARCHAR NOT NULL,
            revision BIGINT NOT NULL,
            profile_id VARCHAR NOT NULL,
            canonicalization_profile VARCHAR NOT NULL,
            canonical_json BLOB NOT NULL,
            sha256 VARCHAR NOT NULL,
            predecessor_revision BIGINT,
            created_at VARCHAR NOT NULL,
            PRIMARY KEY (document_id, revision)
        );
        CREATE TABLE IF NOT EXISTS expression_index (
            document_id VARCHAR NOT NULL, revision BIGINT NOT NULL,
            expression_id VARCHAR NOT NULL, expression_sort VARCHAR,
            semantic_kind VARCHAR, operator VARCHAR NOT NULL, params_json VARCHAR NOT NULL,
            PRIMARY KEY (document_id, revision, expression_id)
        );
        CREATE TABLE IF NOT EXISTS assertion_index (
            document_id VARCHAR NOT NULL, revision BIGINT NOT NULL,
            assertion_id VARCHAR NOT NULL, expression_ref VARCHAR NOT NULL,
            context_ref VARCHAR, context_kind VARCHAR NOT NULL,
            commitment VARCHAR NOT NULL, epistemic_status VARCHAR NOT NULL,
            PRIMARY KEY (document_id, revision, assertion_id)
        );
        CREATE TABLE IF NOT EXISTS evidence_index (
            document_id VARCHAR NOT NULL, revision BIGINT NOT NULL,
            evidence_id VARCHAR NOT NULL, source_ref VARCHAR NOT NULL,
            span_start BIGINT NOT NULL, span_end BIGINT NOT NULL,
            alignment_status VARCHAR NOT NULL, semantic_support_status VARCHAR NOT NULL,
            PRIMARY KEY (document_id, revision, evidence_id)
        );
        CREATE TABLE IF NOT EXISTS source_index (
            document_id VARCHAR NOT NULL, revision BIGINT NOT NULL,
            source_id VARCHAR NOT NULL, source_hash VARCHAR NOT NULL,
            language VARCHAR NOT NULL, source_type VARCHAR,
            PRIMARY KEY (document_id, revision, source_id)
        );
        CREATE INDEX IF NOT EXISTS idx_expression_document ON expression_index(document_id);
        CREATE INDEX IF NOT EXISTS idx_assertion_document ON assertion_index(document_id);
        CREATE INDEX IF NOT EXISTS idx_evidence_document ON evidence_index(document_id);
        CREATE INDEX IF NOT EXISTS idx_source_document ON source_index(document_id);
        """
        with self._lock:
            self._connection.execute("BEGIN TRANSACTION")
            try:
                self._connection.execute(ddl)
                self._connection.execute(
                    "INSERT INTO schema_migrations VALUES (1, ?, ?) ON CONFLICT DO NOTHING",
                    ["initial-canonical-document-store", self._now()],
                )
                self._connection.execute("COMMIT")
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise

    def _validate_document(self, document: dict[str, Any]):
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
                actual = sha256(source["text"].encode("utf-8")).hexdigest()
                if declared_hash.lower() != actual:
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

    @staticmethod
    def _index_rows(document: dict[str, Any]) -> dict[str, list[tuple]]:
        did = document["documentId"]
        expressions = [
            (did, 0, x["id"], x.get("sort"), x.get("semanticKind"), x["op"],
             json.dumps(x.get("params", {}), ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), allow_nan=False))
            for x in document.get("expressions", [])
        ]
        assertions = []
        for x in document.get("assertions", []):
            context = x.get("evaluationContext", {})
            assertions.append((
                did, 0, x["id"], x["expressionRef"], context.get("contextRef"),
                context["kind"], x["commitment"], x["epistemicStatus"],
            ))
        evidence = [
            (did, 0, x["id"], x["sourceRef"], x["span"]["start"], x["span"]["end"],
             x["alignmentStatus"], x["semanticSupportStatus"])
            for x in document.get("evidence", [])
        ]
        sources = [
            (did, 0, x["id"], x.get("textHash") or sha256(x["text"].encode("utf-8")).hexdigest(),
             x["language"], x.get("sourceType"))
            for x in document.get("sources", [])
        ]
        return {
            "expression_index": expressions, "assertion_index": assertions,
            "evidence_index": evidence, "source_index": sources,
        }

    def _write_indexes(self, document: dict[str, Any], revision: int):
        tables = {
            "expression_index": "document_id,revision,expression_id,expression_sort,semantic_kind,operator,params_json",
            "assertion_index": "document_id,revision,assertion_id,expression_ref,context_ref,context_kind,commitment,epistemic_status",
            "evidence_index": "document_id,revision,evidence_id,source_ref,span_start,span_end,alignment_status,semantic_support_status",
            "source_index": "document_id,revision,source_id,source_hash,language,source_type",
        }
        for table, rows in self._index_rows(document).items():
            if rows:
                payload = [tuple(revision if i == 1 else value for i, value in enumerate(row)) for row in rows]
                placeholders = ",".join("?" for _ in payload[0])
                self._connection.executemany(
                    f"INSERT INTO {table} ({tables[table]}) VALUES ({placeholders})", payload
                )

    def put_document(self, document: dict[str, Any], expected_revision: int | None = None) -> StoredDocument:
        self._ensure_open()
        self._validate_document(document)
        did = document["documentId"]
        raw = canonical_bytes(document)
        digest = sha256(raw).hexdigest()
        now = self._now()
        with self._lock:
            self._connection.execute("BEGIN TRANSACTION")
            try:
                current = self._connection.execute(
                    "SELECT current_revision, created_at FROM documents WHERE document_id=?", [did]
                ).fetchone()
                if current is None:
                    if expected_revision not in (None, 0):
                        raise RevisionConflictError(did, 0, expected_revision)
                    revision, predecessor, created = 1, None, now
                    self._connection.execute(
                        "INSERT INTO documents VALUES (?, ?, 0, ?, ?)",
                        [did, document["profileId"], now, now],
                    )
                else:
                    current_revision = int(current[0])
                    existing = self._connection.execute(
                        "SELECT canonical_json, sha256, canonicalization_profile, "
                        "predecessor_revision, created_at FROM document_revisions "
                        "WHERE document_id=? AND revision=?", [did, current_revision]
                    ).fetchone()
                    if existing is None:
                        raise IntegrityError("current revision metadata or snapshot is missing")
                    current_raw = bytes(existing[0])
                    if sha256(current_raw).hexdigest() != existing[1]:
                        raise IntegrityError("current canonical snapshot SHA-256 mismatch")
                    if existing[1] == digest:
                        unchanged = parse_canonical(current_raw)
                        self._connection.execute("COMMIT")
                        return StoredDocument(
                            did, current_revision, existing[3], digest, existing[2],
                            existing[4], unchanged, "UNCHANGED",
                        )
                    if expected_revision is None or expected_revision != current_revision:
                        raise RevisionConflictError(did, current_revision, expected_revision)
                    revision, predecessor, created = current_revision + 1, current_revision, current[1]

                self._connection.execute(
                    "INSERT INTO document_revisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [did, revision, document["profileId"], CANONICALIZATION_PROFILE,
                     raw, digest, predecessor, now],
                )
                self._write_indexes(document, revision)
                self._connection.execute(
                    "UPDATE documents SET current_revision=?, updated_at=? WHERE document_id=?",
                    [revision, now, did],
                )
                self._connection.execute("COMMIT")
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise
        return StoredDocument(
            did, revision, predecessor, digest, CANONICALIZATION_PROFILE,
            now, parse_canonical(raw), "STORED",
        )

    def _read_revision(self, did: str, revision: int | None = None):
        if revision is None:
            row = self._connection.execute(
                "SELECT r.revision, r.profile_id, r.canonicalization_profile, r.canonical_json, "
                "r.sha256, r.predecessor_revision, r.created_at FROM documents d "
                "JOIN document_revisions r ON r.document_id=d.document_id "
                "AND r.revision=d.current_revision WHERE d.document_id=?", [did]
            ).fetchone()
        else:
            row = self._connection.execute(
                "SELECT revision, profile_id, canonicalization_profile, canonical_json, "
                "sha256, predecessor_revision, created_at FROM document_revisions "
                "WHERE document_id=? AND revision=?", [did, revision]
            ).fetchone()
        if row is None:
            raise DocumentNotFoundError(
                f"document revision not found: {did}" + (f"@{revision}" if revision else "")
            )
        return row

    def _verify_index_rows(self, document: dict[str, Any], revision: int):
        for table, expected in self._index_rows(document).items():
            expected_rows = {
                tuple(revision if i == 1 else value for i, value in enumerate(row))
                for row in expected
            }
            actual_rows = {
                tuple(row) for row in self._connection.execute(
                    f"SELECT * FROM {table} WHERE document_id=? AND revision=?",
                    [document["documentId"], revision]
                ).fetchall()
            }
            if actual_rows != expected_rows:
                raise IntegrityError(f"derived index drift detected in {table}")

    def get_document(self, document_id: str, revision: int | None = None) -> StoredDocument:
        self._ensure_open()
        with self._lock:
            row = self._read_revision(document_id, revision)
            raw = bytes(row[3])
            if sha256(raw).hexdigest() != row[4]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch")
            if row[2] != CANONICALIZATION_PROFILE:
                raise IntegrityError("unsupported canonicalization profile")
            try:
                document = parse_canonical(raw)
            except CanonicalizationError as exc:
                raise IntegrityError(str(exc)) from exc
            self._validate_document(document)
            if document.get("documentId") != document_id or document.get("profileId") != row[1]:
                raise IntegrityError("snapshot identity/profile does not match revision metadata")
            self._verify_index_rows(document, int(row[0]))
            return StoredDocument(
                document_id, int(row[0]), row[5], row[4], row[2], row[6], document, "VERIFIED"
            )

    def list_revisions(self, document_id: str) -> list[dict[str, Any]]:
        self._ensure_open()
        with self._lock:
            rows = self._connection.execute(
                "SELECT revision, sha256, predecessor_revision, created_at, canonicalization_profile "
                "FROM document_revisions WHERE document_id=? ORDER BY revision", [document_id]
            ).fetchall()
            if not rows:
                raise DocumentNotFoundError(f"document not found: {document_id}")
            return [{
                "revision": x[0], "sha256": x[1], "predecessor_revision": x[2],
                "created_at": x[3], "canonicalization_profile": x[4],
            } for x in rows]

    def rebuild_indexes(self, document_id: str, revision: int | None = None) -> dict[str, int]:
        self._ensure_open()
        with self._lock:
            row = self._read_revision(document_id, revision)
            raw = bytes(row[3])
            if sha256(raw).hexdigest() != row[4]:
                raise IntegrityError("canonical snapshot SHA-256 mismatch; refusing index rebuild")
            document = parse_canonical(raw)
            self._validate_document(document)
            if document.get("documentId") != document_id or document.get("profileId") != row[1]:
                raise IntegrityError("snapshot identity/profile does not match revision metadata")
            selected = int(row[0])
            self._connection.execute("BEGIN TRANSACTION")
            try:
                for table in ("expression_index", "assertion_index", "evidence_index", "source_index"):
                    self._connection.execute(
                        f"DELETE FROM {table} WHERE document_id=? AND revision=?",
                        [document_id, selected],
                    )
                self._write_indexes(document, selected)
                self._connection.execute("COMMIT")
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise
            return {
                table: int(self._connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE document_id=? AND revision=?",
                    [document_id, selected]
                ).fetchone()[0])
                for table in ("expression_index", "assertion_index", "evidence_index", "source_index")
            }

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
