"""Append-only USG knowledge snapshots in the existing canonical SQLite database.

The host owns the SQLite connection and every transaction boundary. This
repository never opens, closes, commits, or rolls back a connection.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any

from tools.phase7_knowledge_contract.validate import validate_bundle

KNOWLEDGE_REPOSITORY_VERSION = "sqlite-usg-knowledge-repository/0.1.0"
ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "specifications" / "usg-knowledge-0.1.0.schema.json"


class KnowledgeRepositoryIntegrityError(RuntimeError):
    """Raised when a stored knowledge snapshot or its indexes fail verification."""


@dataclass(frozen=True)
class KnowledgeSnapshot:
    snapshot_id: str
    bundle_id: str
    bundle_version: int
    digest: str
    created_at: str
    bundle: dict[str, Any]
    status: str = "STORED"

    def metadata(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "bundle_id": self.bundle_id,
            "bundle_version": self.bundle_version,
            "sha256": self.digest,
            "created_at": self.created_at,
            "status": self.status,
        }


def canonical_bundle_bytes(bundle: dict[str, Any]) -> bytes:
    return json.dumps(
        bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS usg_knowledge_repository_state (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        schema_version TEXT NOT NULL,
        repository_version INTEGER NOT NULL CHECK (repository_version >= 1)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_bundle_snapshot (
        snapshot_id TEXT PRIMARY KEY,
        bundle_id TEXT NOT NULL,
        bundle_version INTEGER NOT NULL CHECK (bundle_version >= 1),
        contract TEXT NOT NULL CHECK (contract = 'USG-KNOWLEDGE/0.1.0'),
        namespace TEXT NOT NULL,
        content_sha256 TEXT NOT NULL CHECK (length(content_sha256) = 64),
        canonical_json BLOB NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (bundle_id, bundle_version),
        UNIQUE (bundle_id, content_sha256)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_record_index (
        snapshot_id TEXT NOT NULL,
        record_id TEXT NOT NULL,
        record_kind TEXT NOT NULL,
        record_version INTEGER NOT NULL,
        state TEXT NOT NULL,
        record_json BLOB NOT NULL,
        PRIMARY KEY (snapshot_id, record_id),
        FOREIGN KEY (snapshot_id) REFERENCES usg_knowledge_bundle_snapshot(snapshot_id)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_source_index (
        snapshot_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        source_json BLOB NOT NULL,
        PRIMARY KEY (snapshot_id, source_id),
        FOREIGN KEY (snapshot_id) REFERENCES usg_knowledge_bundle_snapshot(snapshot_id)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_evidence_index (
        snapshot_id TEXT NOT NULL,
        evidence_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        evidence_json BLOB NOT NULL,
        PRIMARY KEY (snapshot_id, evidence_id),
        FOREIGN KEY (snapshot_id) REFERENCES usg_knowledge_bundle_snapshot(snapshot_id)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_context_index (
        snapshot_id TEXT NOT NULL,
        context_id TEXT NOT NULL,
        context_type TEXT NOT NULL,
        context_json BLOB NOT NULL,
        PRIMARY KEY (snapshot_id, context_id),
        FOREIGN KEY (snapshot_id) REFERENCES usg_knowledge_bundle_snapshot(snapshot_id)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_mapping_index (
        snapshot_id TEXT NOT NULL,
        mapping_id TEXT NOT NULL,
        source_record_id TEXT NOT NULL,
        target_record_id TEXT NOT NULL,
        mapping_type TEXT NOT NULL,
        mapping_json BLOB NOT NULL,
        PRIMARY KEY (snapshot_id, mapping_id),
        FOREIGN KEY (snapshot_id) REFERENCES usg_knowledge_bundle_snapshot(snapshot_id)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_knowledge_relation_index (
        snapshot_id TEXT NOT NULL,
        relation_id TEXT NOT NULL,
        subject_record_id TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object_record_id TEXT NOT NULL,
        relation_json BLOB NOT NULL,
        PRIMARY KEY (snapshot_id, relation_id),
        FOREIGN KEY (snapshot_id) REFERENCES usg_knowledge_bundle_snapshot(snapshot_id)
    ) STRICT""",
    "CREATE INDEX IF NOT EXISTS usg_knowledge_record_kind_state ON usg_knowledge_record_index(record_kind, state, record_id)",
    "CREATE INDEX IF NOT EXISTS usg_knowledge_record_lookup ON usg_knowledge_record_index(record_id, record_kind)",
    "CREATE INDEX IF NOT EXISTS usg_knowledge_mapping_endpoints ON usg_knowledge_mapping_index(source_record_id, target_record_id)",
    "CREATE INDEX IF NOT EXISTS usg_knowledge_relation_subject ON usg_knowledge_relation_index(subject_record_id, predicate)",
)


def _append_only_triggers(table: str, label: str) -> tuple[str, str]:
    return (
        f"""CREATE TRIGGER IF NOT EXISTS {table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN SELECT RAISE(ABORT, '{label} are immutable'); END""",
        f"""CREATE TRIGGER IF NOT EXISTS {table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN SELECT RAISE(ABORT, '{label} are append-only'); END""",
    )


class SQLiteKnowledgeRepository:
    """Append-only knowledge snapshot repository on a caller-owned connection."""

    def __init__(self, connection: sqlite3.Connection):
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError("connection must be a caller-owned sqlite3.Connection")
        if not connection.in_transaction:
            raise RuntimeError("knowledge repository installation requires a caller-owned transaction")
        self.connection = connection
        for statement in _SCHEMA:
            connection.execute(statement)
        connection.execute(
            "INSERT OR IGNORE INTO usg_knowledge_repository_state(singleton,schema_version,repository_version) VALUES(1,?,1)",
            (KNOWLEDGE_REPOSITORY_VERSION,),
        )
        row = connection.execute(
            "SELECT schema_version FROM usg_knowledge_repository_state WHERE singleton=1"
        ).fetchone()
        if row is None or row[0] != KNOWLEDGE_REPOSITORY_VERSION:
            raise ValueError("knowledge repository schema version mismatch; apply an explicit migration")
        for table, label in (
            ("usg_knowledge_bundle_snapshot", "knowledge snapshots"),
            ("usg_knowledge_record_index", "knowledge record indexes"),
            ("usg_knowledge_source_index", "knowledge source indexes"),
            ("usg_knowledge_evidence_index", "knowledge evidence indexes"),
            ("usg_knowledge_context_index", "knowledge context indexes"),
            ("usg_knowledge_mapping_index", "knowledge mapping indexes"),
            ("usg_knowledge_relation_index", "knowledge relation indexes"),
        ):
            for statement in _append_only_triggers(table, label):
                connection.execute(statement)

    def _require_transaction(self) -> None:
        if not self.connection.in_transaction:
            raise RuntimeError("knowledge repository writes require a caller-owned SQLite transaction")

    @property
    def version(self) -> int:
        row = self.connection.execute(
            "SELECT repository_version FROM usg_knowledge_repository_state WHERE singleton=1"
        ).fetchone()
        return int(row[0])

    @property
    def connection_identity(self) -> int:
        """Diagnostic identity token; the repository retains the exact supplied connection."""
        return id(self.connection)

    def put_bundle(self, bundle: dict[str, Any]) -> KnowledgeSnapshot:
        self._require_transaction()
        errors = validate_bundle(bundle)
        if errors:
            raise ValueError("knowledge bundle validation failed: " + "; ".join(errors))
        raw = canonical_bundle_bytes(bundle)
        digest = sha256(raw).hexdigest()
        existing = self.connection.execute(
            """SELECT snapshot_id,bundle_id,bundle_version,content_sha256,created_at
               FROM usg_knowledge_bundle_snapshot
               WHERE bundle_id=? AND content_sha256=?""",
            (bundle["bundle_id"], digest),
        ).fetchone()
        if existing is not None:
            return KnowledgeSnapshot(
                existing["snapshot_id"], existing["bundle_id"], existing["bundle_version"],
                existing["content_sha256"], existing["created_at"], bundle, "UNCHANGED",
            )

        latest = self.connection.execute(
            "SELECT COALESCE(MAX(bundle_version),0) FROM usg_knowledge_bundle_snapshot WHERE bundle_id=?",
            (bundle["bundle_id"],),
        ).fetchone()[0]
        bundle_version = int(latest) + 1
        snapshot_id = "knowledge:" + digest[:32]
        from datetime import datetime, timezone
        created_at = datetime.now(timezone.utc).isoformat()

        self.connection.execute(
            """INSERT INTO usg_knowledge_bundle_snapshot
               (snapshot_id,bundle_id,bundle_version,contract,namespace,content_sha256,canonical_json,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (snapshot_id, bundle["bundle_id"], bundle_version, bundle["contract"],
             bundle["namespace"], digest, sqlite3.Binary(raw), created_at),
        )
        for item in bundle["records"]:
            self.connection.execute(
                """INSERT INTO usg_knowledge_record_index
                   (snapshot_id,record_id,record_kind,record_version,state,record_json)
                   VALUES(?,?,?,?,?,?)""",
                (snapshot_id, item["id"], item["kind"], item["version"], item["state"],
                 sqlite3.Binary(canonical_bundle_bytes(item))),
            )
        for item in bundle["sources"]:
            self.connection.execute(
                "INSERT INTO usg_knowledge_source_index(snapshot_id,source_id,source_json) VALUES(?,?,?)",
                (snapshot_id, item["id"], sqlite3.Binary(canonical_bundle_bytes(item))),
            )
        for item in bundle["evidence"]:
            self.connection.execute(
                "INSERT INTO usg_knowledge_evidence_index(snapshot_id,evidence_id,source_id,evidence_json) VALUES(?,?,?,?)",
                (snapshot_id, item["id"], item["source_id"], sqlite3.Binary(canonical_bundle_bytes(item))),
            )
        for item in bundle["contexts"]:
            self.connection.execute(
                "INSERT INTO usg_knowledge_context_index(snapshot_id,context_id,context_type,context_json) VALUES(?,?,?,?)",
                (snapshot_id, item["id"], item["context_type"], sqlite3.Binary(canonical_bundle_bytes(item))),
            )
        for item in bundle["mappings"]:
            self.connection.execute(
                """INSERT INTO usg_knowledge_mapping_index
                   (snapshot_id,mapping_id,source_record_id,target_record_id,mapping_type,mapping_json)
                   VALUES(?,?,?,?,?,?)""",
                (snapshot_id, item["id"], item["source_record_id"], item["target_record_id"],
                 item["mapping_type"], sqlite3.Binary(canonical_bundle_bytes(item))),
            )
        for item in bundle["relations"]:
            self.connection.execute(
                """INSERT INTO usg_knowledge_relation_index
                   (snapshot_id,relation_id,subject_record_id,predicate,object_record_id,relation_json)
                   VALUES(?,?,?,?,?,?)""",
                (snapshot_id, item["id"], item["subject_record_id"], item["predicate"],
                 item["object_record_id"], sqlite3.Binary(canonical_bundle_bytes(item))),
            )
        self.connection.execute(
            "UPDATE usg_knowledge_repository_state SET repository_version=repository_version+1 WHERE singleton=1"
        )
        return KnowledgeSnapshot(snapshot_id, bundle["bundle_id"], bundle_version, digest, created_at, bundle)

    def get_snapshot(self, snapshot_id: str) -> KnowledgeSnapshot | None:
        row = self.connection.execute(
            """SELECT snapshot_id,bundle_id,bundle_version,content_sha256,canonical_json,created_at
               FROM usg_knowledge_bundle_snapshot WHERE snapshot_id=?""",
            (snapshot_id,),
        ).fetchone()
        if row is None:
            return None
        raw = bytes(row["canonical_json"])
        if sha256(raw).hexdigest() != row["content_sha256"]:
            raise KnowledgeRepositoryIntegrityError("stored knowledge bundle digest mismatch")
        try:
            bundle = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KnowledgeRepositoryIntegrityError("stored knowledge bundle is invalid JSON") from exc
        if canonical_bundle_bytes(bundle) != raw:
            raise KnowledgeRepositoryIntegrityError("stored knowledge bundle is not canonical JSON")
        errors = validate_bundle(bundle)
        if errors:
            raise KnowledgeRepositoryIntegrityError("stored knowledge bundle no longer validates: " + "; ".join(errors))
        expected = {
            "record": len(bundle["records"]), "source": len(bundle["sources"]),
            "evidence": len(bundle["evidence"]), "context": len(bundle["contexts"]),
            "mapping": len(bundle["mappings"]), "relation": len(bundle["relations"]),
        }
        tables = {
            "record": "usg_knowledge_record_index", "source": "usg_knowledge_source_index",
            "evidence": "usg_knowledge_evidence_index", "context": "usg_knowledge_context_index",
            "mapping": "usg_knowledge_mapping_index", "relation": "usg_knowledge_relation_index",
        }
        for kind, table in tables.items():
            actual = self.connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE snapshot_id=?", (snapshot_id,)
            ).fetchone()[0]
            if actual != expected[kind]:
                raise KnowledgeRepositoryIntegrityError(f"{kind} index count mismatch")
        return KnowledgeSnapshot(
            row["snapshot_id"], row["bundle_id"], row["bundle_version"],
            row["content_sha256"], row["created_at"], bundle, "VERIFIED",
        )

    def get_latest(self, bundle_id: str) -> KnowledgeSnapshot | None:
        row = self.connection.execute(
            """SELECT snapshot_id FROM usg_knowledge_bundle_snapshot
               WHERE bundle_id=? ORDER BY bundle_version DESC LIMIT 1""",
            (bundle_id,),
        ).fetchone()
        return self.get_snapshot(row["snapshot_id"]) if row else None

    def list_snapshots(self, bundle_id: str | None = None, limit: int = 50) -> tuple[dict[str, Any], ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be an integer from 1 through 500")
        if bundle_id is None:
            rows = self.connection.execute(
                """SELECT snapshot_id,bundle_id,bundle_version,content_sha256,created_at
                   FROM usg_knowledge_bundle_snapshot
                   ORDER BY created_at DESC,snapshot_id LIMIT ?""", (limit,)
            ).fetchall()
        else:
            rows = self.connection.execute(
                """SELECT snapshot_id,bundle_id,bundle_version,content_sha256,created_at
                   FROM usg_knowledge_bundle_snapshot WHERE bundle_id=?
                   ORDER BY bundle_version DESC LIMIT ?""", (bundle_id, limit)
            ).fetchall()
        return tuple({
            "snapshot_id": row["snapshot_id"], "bundle_id": row["bundle_id"],
            "bundle_version": row["bundle_version"], "sha256": row["content_sha256"],
            "created_at": row["created_at"],
        } for row in rows)


__all__ = [
    "KNOWLEDGE_REPOSITORY_VERSION", "KnowledgeRepositoryIntegrityError",
    "KnowledgeSnapshot", "SQLiteKnowledgeRepository", "canonical_bundle_bytes",
]
