"""Versioned SQLite-backed catalogue for inspectable USG semantic resources."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any

RESOURCE_CATALOGUE_VERSION = "USG-RESOURCE-CATALOGUE/0.1.0"
RESOURCE_CLASSES = frozenset({
    "LEXICAL_REALIZATION",
    "GRAMMAR_PATTERN",
    "SEMANTIC_FRAME",
    "DISCOURSE_RESOURCE",
    "PROVISIONAL_ASSOCIATION",
})
_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")


class ResourceCatalogueError(RuntimeError):
    """Base class for deterministic resource-catalogue failures."""


class InvalidResourceError(ResourceCatalogueError):
    pass


class ResourceNotFoundError(ResourceCatalogueError):
    pass


class ResourceVersionConflictError(ResourceCatalogueError):
    pass


class ResourceActivationConflictError(ResourceCatalogueError):
    pass


class ResourceIntegrityError(ResourceCatalogueError):
    pass


@dataclass(frozen=True)
class ResourceSnapshot:
    resource_id: str
    version: str
    resource_class: str
    provenance: dict[str, Any]
    content: dict[str, Any]
    digest: str
    created_at: str
    active: bool
    write_status: str = "STORED"


@dataclass(frozen=True)
class ResourceRetrieval:
    snapshot: ResourceSnapshot
    usage_count: int
    last_used_at: str | None
    activation_score: float
    rank: int


@dataclass(frozen=True)
class AssociationCandidate:
    association_id: str
    resource_id: str
    resource_version: str
    source_ref: str
    relation: str
    target_ref: str
    attributes: dict[str, Any]
    status: str
    identity_resolution: bool
    activation_score: float
    active_resource: bool


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InvalidResourceError(f"resource is not canonical JSON: {exc}") from exc


def _version_key(value: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(value)
    if match is None:
        raise InvalidResourceError("version must be a stable MAJOR.MINOR.PATCH version")
    return tuple(int(part) for part in match.groups())


def _utc_timestamp(value: datetime | str | None = None) -> str:
    if value is None:
        parsed = datetime.now(timezone.utc)
    elif isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidResourceError("timestamp must be an ISO-8601 datetime") from exc
    else:
        raise InvalidResourceError("timestamp must be an ISO-8601 datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidResourceError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _validate_resource(
    resource_id: str,
    version: str,
    resource_class: str,
    provenance: dict[str, Any],
    content: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(resource_id, str) or not _ID_RE.fullmatch(resource_id):
        raise InvalidResourceError("resource_id must be a non-empty stable identifier")
    if not isinstance(version, str):
        raise InvalidResourceError("version must be a stable MAJOR.MINOR.PATCH version")
    _version_key(version)
    if not isinstance(resource_class, str) or resource_class not in RESOURCE_CLASSES:
        raise InvalidResourceError("resource_class is not a supported resource class")
    if not isinstance(provenance, dict) or not provenance:
        raise InvalidResourceError("provenance must be a non-empty object")
    if not isinstance(content, dict):
        raise InvalidResourceError("resource content must be an object")
    if resource_class == "PROVISIONAL_ASSOCIATION":
        associations = content.get("associations")
        if not isinstance(associations, list):
            raise InvalidResourceError("provisional association content requires an associations array")
        seen = set()
        for item in associations:
            if not isinstance(item, dict):
                raise InvalidResourceError("each association must be an object")
            required = ("association_id", "source_ref", "relation", "target_ref")
            if any(not isinstance(item.get(key), str) or not item[key].strip() for key in required):
                raise InvalidResourceError("each association requires non-empty association_id, source_ref, relation, and target_ref")
            if item["association_id"] in seen:
                raise InvalidResourceError("association_id values must be unique within a resource")
            seen.add(item["association_id"])
    envelope = {
        "catalogue_contract": RESOURCE_CATALOGUE_VERSION,
        "resource_id": resource_id,
        "version": version,
        "resource_class": resource_class,
        "provenance": provenance,
        "content": content,
    }
    _canonical_bytes(envelope)
    return envelope


class SQLiteResourceCatalogue:
    """Append-only resource snapshots and rebuildable retrieval metadata in SQLite.

    Pass the same database path used by CanonicalDocumentStore to keep resource
    records in the canonical SQLite database file. This class owns a separate
    SQLite connection; resource snapshots never alter canonical USG-SEM rows.
    """

    def __init__(self, path: str | Path = ":memory:", busy_timeout_ms: int = 5000):
        if isinstance(busy_timeout_ms, bool) or not isinstance(busy_timeout_ms, int) or busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be a non-negative integer")
        self.path = str(path)
        self._lock = threading.RLock()
        self._closed = False
        self._connection = sqlite3.connect(
            self.path, isolation_level=None, check_same_thread=False,
            timeout=busy_timeout_ms / 1000,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
        self._connection.execute("PRAGMA synchronous=FULL")
        if self.path != ":memory:":
            self._connection.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True

    def __enter__(self) -> "SQLiteResourceCatalogue":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise ResourceCatalogueError("resource catalogue is closed")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _migrate(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS resource_catalogue_migrations (
            version INTEGER PRIMARY KEY,
            migration_name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS semantic_resource_snapshots (
            resource_id TEXT NOT NULL,
            version TEXT NOT NULL,
            resource_class TEXT NOT NULL,
            canonical_json BLOB NOT NULL,
            sha256 TEXT NOT NULL CHECK(length(sha256)=64),
            created_at TEXT NOT NULL,
            PRIMARY KEY(resource_id, version)
        );
        CREATE TABLE IF NOT EXISTS semantic_resource_heads (
            resource_id TEXT PRIMARY KEY,
            resource_class TEXT NOT NULL,
            active_version TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(resource_id, active_version)
                REFERENCES semantic_resource_snapshots(resource_id, version)
        );
        CREATE TABLE IF NOT EXISTS semantic_resource_usage_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id TEXT NOT NULL,
            version TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            FOREIGN KEY(resource_id, version)
                REFERENCES semantic_resource_snapshots(resource_id, version)
        );
        CREATE INDEX IF NOT EXISTS idx_resource_class
            ON semantic_resource_snapshots(resource_class, resource_id, version);
        CREATE INDEX IF NOT EXISTS idx_resource_usage
            ON semantic_resource_usage_events(resource_id, version, occurred_at);
        """
        now = self._now().replace("'", "''")
        script = (
            "BEGIN IMMEDIATE;\n" + ddl
            + "\nINSERT OR IGNORE INTO resource_catalogue_migrations(version,migration_name,applied_at) "
            + f"VALUES(1,'initial-resource-catalogue','{now}');\nCOMMIT;"
        )
        with self._lock:
            try:
                self._connection.executescript(script)
            except BaseException:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def _active_version(self, resource_id: str) -> str | None:
        row = self._connection.execute(
            "SELECT active_version FROM semantic_resource_heads WHERE resource_id=?",
            (resource_id,),
        ).fetchone()
        return str(row["active_version"]) if row else None

    def put_resource(
        self,
        resource_id: str,
        version: str,
        resource_class: str,
        content: dict[str, Any],
        provenance: dict[str, Any],
        *,
        activate: bool = False,
        expected_active_version: str | None = None,
    ) -> ResourceSnapshot:
        """Insert an immutable snapshot; identical retries are idempotent.

        A new version is secondary by default. Activation is an explicit,
        compare-and-swap operation and never rewrites the stored snapshot.
        """
        self._ensure_open()
        envelope = _validate_resource(resource_id, version, resource_class, provenance, content)
        raw = _canonical_bytes(envelope)
        digest = sha256(raw).hexdigest()
        now = self._now()
        write_status = "STORED"
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                existing = self._connection.execute(
                    "SELECT sha256 FROM semantic_resource_snapshots WHERE resource_id=? AND version=?",
                    (resource_id, version),
                ).fetchone()
                if existing:
                    if existing["sha256"] != digest:
                        raise ResourceVersionConflictError(
                            f"resource version is immutable: {resource_id}@{version}"
                        )
                    write_status = "UNCHANGED"
                else:
                    self._connection.execute(
                        "INSERT INTO semantic_resource_snapshots(resource_id,version,resource_class,canonical_json,sha256,created_at) "
                        "VALUES(?,?,?,?,?,?)",
                        (resource_id, version, resource_class, sqlite3.Binary(raw), digest, now),
                    )
                if activate:
                    current = self._active_version(resource_id)
                    if current != expected_active_version:
                        raise ResourceActivationConflictError(
                            f"active version conflict for {resource_id}: current={current}, expected={expected_active_version}"
                        )
                    head = self._connection.execute(
                        "SELECT resource_class FROM semantic_resource_heads WHERE resource_id=?",
                        (resource_id,),
                    ).fetchone()
                    if head and head["resource_class"] != resource_class:
                        raise ResourceCatalogueError("resource class cannot change between versions")
                    self._connection.execute(
                        "INSERT INTO semantic_resource_heads(resource_id,resource_class,active_version,updated_at) "
                        "VALUES(?,?,?,?) ON CONFLICT(resource_id) DO UPDATE SET "
                        "active_version=excluded.active_version, updated_at=excluded.updated_at",
                        (resource_id, resource_class, version, now),
                    )
                self._connection.execute("COMMIT")
            except BaseException:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise
        snapshot = self.get_resource(resource_id, version)
        return ResourceSnapshot(
            snapshot.resource_id, snapshot.version, snapshot.resource_class,
            snapshot.provenance, snapshot.content, snapshot.digest,
            snapshot.created_at, snapshot.active, write_status,
        )

    def set_active_version(
        self,
        resource_id: str,
        version: str,
        *,
        expected_active_version: str | None,
    ) -> None:
        """Switch the active pointer using compare-and-swap; snapshots stay immutable."""
        self._ensure_open()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    "SELECT resource_class FROM semantic_resource_snapshots WHERE resource_id=? AND version=?",
                    (resource_id, version),
                ).fetchone()
                if row is None:
                    raise ResourceNotFoundError(f"resource snapshot not found: {resource_id}@{version}")
                current = self._active_version(resource_id)
                if current != expected_active_version:
                    raise ResourceActivationConflictError(
                        f"active version conflict for {resource_id}: current={current}, expected={expected_active_version}"
                    )
                head = self._connection.execute(
                    "SELECT resource_class FROM semantic_resource_heads WHERE resource_id=?",
                    (resource_id,),
                ).fetchone()
                if head and head["resource_class"] != row["resource_class"]:
                    raise ResourceCatalogueError("resource class cannot change between versions")
                self._connection.execute(
                    "INSERT INTO semantic_resource_heads(resource_id,resource_class,active_version,updated_at) "
                    "VALUES(?,?,?,?) ON CONFLICT(resource_id) DO UPDATE SET "
                    "active_version=excluded.active_version, updated_at=excluded.updated_at",
                    (resource_id, row["resource_class"], version, self._now()),
                )
                self._connection.execute("COMMIT")
            except BaseException:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def _snapshot_from_row(self, row: sqlite3.Row) -> ResourceSnapshot:
        raw = bytes(row["canonical_json"])
        digest = sha256(raw).hexdigest()
        if digest != row["sha256"]:
            raise ResourceIntegrityError(
                f"resource digest mismatch: {row['resource_id']}@{row['version']}"
            )
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ResourceIntegrityError("stored resource is not valid UTF-8 JSON") from exc
        if _canonical_bytes(envelope) != raw:
            raise ResourceIntegrityError("stored resource is not canonical JSON")
        if not isinstance(envelope, dict):
            raise ResourceIntegrityError("stored resource envelope must be an object")
        if envelope.get("catalogue_contract") != RESOURCE_CATALOGUE_VERSION:
            raise ResourceIntegrityError("stored resource catalogue contract is unsupported")
        if (envelope.get("resource_id") != row["resource_id"]
                or envelope.get("version") != row["version"]
                or envelope.get("resource_class") != row["resource_class"]):
            raise ResourceIntegrityError("stored resource identity does not match its catalogue row")
        active = self._active_version(row["resource_id"]) == row["version"]
        return ResourceSnapshot(
            row["resource_id"], row["version"], row["resource_class"],
            envelope["provenance"], envelope["content"], digest,
            row["created_at"], active,
        )

    def get_resource(self, resource_id: str, version: str | None = None) -> ResourceSnapshot:
        self._ensure_open()
        selected = version if version is not None else self._active_version(resource_id)
        if selected is None:
            raise ResourceNotFoundError(f"no active resource version: {resource_id}")
        row = self._connection.execute(
            "SELECT * FROM semantic_resource_snapshots WHERE resource_id=? AND version=?",
            (resource_id, selected),
        ).fetchone()
        if row is None:
            raise ResourceNotFoundError(f"resource snapshot not found: {resource_id}@{selected}")
        return self._snapshot_from_row(row)

    def list_resources(self, resource_class: str | None = None) -> tuple[ResourceSnapshot, ...]:
        self._ensure_open()
        if resource_class is not None and resource_class not in RESOURCE_CLASSES:
            raise InvalidResourceError("resource_class is not a supported resource class")
        if resource_class is None:
            rows = self._connection.execute(
                "SELECT * FROM semantic_resource_snapshots"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT * FROM semantic_resource_snapshots WHERE resource_class=?",
                (resource_class,),
            ).fetchall()
        snapshots = [self._snapshot_from_row(row) for row in rows]
        snapshots.sort(key=lambda item: (
            item.resource_class, item.resource_id, tuple(-part for part in _version_key(item.version))
        ))
        return tuple(snapshots)

    def record_usage(
        self,
        resource_id: str,
        version: str,
        occurred_at: datetime | str | None = None,
    ) -> None:
        self._ensure_open()
        timestamp = _utc_timestamp(occurred_at)
        with self._lock:
            exists = self._connection.execute(
                "SELECT 1 FROM semantic_resource_snapshots WHERE resource_id=? AND version=?",
                (resource_id, version),
            ).fetchone()
            if exists is None:
                raise ResourceNotFoundError(f"resource snapshot not found: {resource_id}@{version}")
            self._connection.execute(
                "INSERT INTO semantic_resource_usage_events(resource_id,version,occurred_at) VALUES(?,?,?)",
                (resource_id, version, timestamp),
            )

    def _usage(self, resource_id: str, version: str) -> tuple[int, str | None]:
        row = self._connection.execute(
            "SELECT COUNT(*) AS usage_count, MAX(occurred_at) AS last_used_at "
            "FROM semantic_resource_usage_events WHERE resource_id=? AND version=?",
            (resource_id, version),
        ).fetchone()
        return int(row["usage_count"]), row["last_used_at"]

    def retrieve(
        self,
        resource_class: str,
        *,
        include_secondary: bool = True,
        active_first: bool = True,
        now: datetime | str | None = None,
        half_life_seconds: float = 30 * 24 * 60 * 60,
    ) -> tuple[ResourceRetrieval, ...]:
        """Return deterministic active/secondary resources with decayed usage ranking.

        activation_score is retrieval metadata only; it is not probability,
        truth, semantic confidence, identity, or entailment.
        """
        if resource_class not in RESOURCE_CLASSES:
            raise InvalidResourceError("resource_class is not a supported resource class")
        if isinstance(half_life_seconds, bool) or not isinstance(half_life_seconds, (int, float)) or not math.isfinite(half_life_seconds) or half_life_seconds <= 0:
            raise InvalidResourceError("half_life_seconds must be a positive finite number")
        now_dt = datetime.fromisoformat(_utc_timestamp(now))
        snapshots = self.list_resources(resource_class)
        candidates = []
        for snapshot in snapshots:
            if not include_secondary and not snapshot.active:
                continue
            count, last_used = self._usage(snapshot.resource_id, snapshot.version)
            score = 0.0
            if count and last_used:
                last_dt = datetime.fromisoformat(last_used)
                age = max(0.0, (now_dt - last_dt).total_seconds())
                score = count * math.exp(-math.log(2.0) * age / float(half_life_seconds))
            candidates.append((snapshot, count, last_used, score))
        candidates.sort(key=lambda item: (
            0 if (active_first and item[0].active) else 1,
            -item[3], item[0].resource_id,
            tuple(-part for part in _version_key(item[0].version)),
        ))
        return tuple(
            ResourceRetrieval(snapshot, count, last_used, score, index + 1)
            for index, (snapshot, count, last_used, score) in enumerate(candidates)
        )

    def retrieve_associations(
        self,
        *,
        source_ref: str | None = None,
        relation: str | None = None,
        target_ref: str | None = None,
        include_secondary: bool = True,
        now: datetime | str | None = None,
        half_life_seconds: float = 30 * 24 * 60 * 60,
    ) -> tuple[AssociationCandidate, ...]:
        """Retrieve provisional links by exact fields without resolving identity."""
        resources = self.retrieve(
            "PROVISIONAL_ASSOCIATION", include_secondary=include_secondary,
            active_first=True, now=now, half_life_seconds=half_life_seconds,
        )
        found = []
        for item in resources:
            for association in item.snapshot.content["associations"]:
                if source_ref is not None and association["source_ref"] != source_ref:
                    continue
                if relation is not None and association["relation"] != relation:
                    continue
                if target_ref is not None and association["target_ref"] != target_ref:
                    continue
                found.append(AssociationCandidate(
                    association["association_id"], item.snapshot.resource_id,
                    item.snapshot.version, association["source_ref"],
                    association["relation"], association["target_ref"],
                    {key: value for key, value in association.items()
                     if key not in {"association_id", "source_ref", "relation", "target_ref"}},
                    "PROVISIONAL", False, item.activation_score,
                    item.snapshot.active,
                ))
        found.sort(key=lambda item: (
            0 if item.active_resource else 1, -item.activation_score,
            item.resource_id, item.resource_version, item.association_id,
        ))
        return tuple(found)

    def verify_integrity(self) -> dict[str, Any]:
        """Verify every immutable snapshot and active pointer without mutating data."""
        self._ensure_open()
        checked = 0
        diagnostics = []
        rows = self._connection.execute(
            "SELECT * FROM semantic_resource_snapshots ORDER BY resource_id,version"
        ).fetchall()
        for row in rows:
            try:
                self._snapshot_from_row(row)
                checked += 1
            except ResourceCatalogueError as exc:
                diagnostics.append(str(exc))
        heads = self._connection.execute(
            "SELECT h.resource_id,h.active_version,s.resource_class AS snapshot_class,h.resource_class AS head_class "
            "FROM semantic_resource_heads h LEFT JOIN semantic_resource_snapshots s "
            "ON s.resource_id=h.resource_id AND s.version=h.active_version"
        ).fetchall()
        for head in heads:
            if head["snapshot_class"] is None:
                diagnostics.append(f"ACTIVE_SNAPSHOT_MISSING:{head['resource_id']}@{head['active_version']}")
            elif head["snapshot_class"] != head["head_class"]:
                diagnostics.append(f"ACTIVE_CLASS_MISMATCH:{head['resource_id']}")
        return {
            "status": "PASS" if not diagnostics else "FAIL",
            "resource_snapshots_checked": checked,
            "active_resources": len(heads),
            "diagnostics": diagnostics,
        }


__all__ = [
    "RESOURCE_CATALOGUE_VERSION", "RESOURCE_CLASSES",
    "ResourceCatalogueError", "InvalidResourceError", "ResourceNotFoundError",
    "ResourceVersionConflictError", "ResourceActivationConflictError",
    "ResourceIntegrityError", "ResourceSnapshot", "ResourceRetrieval",
    "AssociationCandidate", "SQLiteResourceCatalogue",
]
