"""SQLite-backed, append-only resource catalogue on a caller-owned canonical connection.

This adapter never opens a database or commits a transaction. The host passes
its existing canonical SQLite connection and owns all transaction boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import sqlite3
from typing import Literal

from tools.usg_interpretation_v0_1_0.resources import ResourceDescriptor, SemanticAssociation

SQLITE_RESOURCE_CATALOGUE_VERSION = "sqlite-semantic-resource-catalogue/0.1.0"


@dataclass(frozen=True)
class AssociationRetrieval:
    association: SemanticAssociation
    activation_score: float
    tier: Literal["ACTIVE", "SECONDARY"]
    total_observations: int
    last_used_at: float


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS usg_resource_catalogue_state (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        registry_id TEXT NOT NULL,
        version INTEGER NOT NULL CHECK (version >= 1)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_resource_descriptor (
        resource_id TEXT PRIMARY KEY,
        resource_type TEXT NOT NULL CHECK (resource_type IN
          ('LEXICON','GRAMMAR','SEMANTIC_FRAME','DISCOURSE','MODEL','OTHER')),
        version TEXT NOT NULL,
        sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
        language TEXT,
        provenance TEXT NOT NULL,
        registered_at REAL NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_semantic_association (
        association_id TEXT PRIMARY KEY,
        source_ref TEXT NOT NULL,
        target_ref TEXT NOT NULL,
        relation TEXT NOT NULL,
        association_kind TEXT NOT NULL CHECK (association_kind IN
          ('CO_OCCURRENCE','FUNCTIONAL','CONTEXTUAL')),
        weight REAL NOT NULL CHECK (weight >= 0 AND weight <= 1),
        observation_count INTEGER NOT NULL CHECK (observation_count >= 0),
        provenance TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status = 'PROVISIONAL'),
        created_at REAL NOT NULL,
        CHECK (source_ref <> target_ref)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS usg_association_usage (
        usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
        association_id TEXT NOT NULL REFERENCES usg_semantic_association(association_id),
        used_at REAL NOT NULL,
        context_ref TEXT
    ) STRICT""",
    "CREATE INDEX IF NOT EXISTS usg_association_by_source ON usg_semantic_association(source_ref, weight DESC)",
    "CREATE INDEX IF NOT EXISTS usg_association_usage_by_id_time ON usg_association_usage(association_id, used_at DESC)",
    """CREATE TRIGGER IF NOT EXISTS usg_resource_no_update BEFORE UPDATE ON usg_resource_descriptor
       BEGIN SELECT RAISE(ABORT, 'resource descriptors are immutable; register a new resource ID/version'); END""",
    """CREATE TRIGGER IF NOT EXISTS usg_resource_no_delete BEFORE DELETE ON usg_resource_descriptor
       BEGIN SELECT RAISE(ABORT, 'resource descriptors are append-only'); END""",
    """CREATE TRIGGER IF NOT EXISTS usg_association_no_update BEFORE UPDATE ON usg_semantic_association
       BEGIN SELECT RAISE(ABORT, 'associations are provisional and immutable'); END""",
    """CREATE TRIGGER IF NOT EXISTS usg_association_no_delete BEFORE DELETE ON usg_semantic_association
       BEGIN SELECT RAISE(ABORT, 'associations are append-only'); END""",
    """CREATE TRIGGER IF NOT EXISTS usg_association_usage_no_update BEFORE UPDATE ON usg_association_usage
       BEGIN SELECT RAISE(ABORT, 'association usage is append-only'); END""",
    """CREATE TRIGGER IF NOT EXISTS usg_association_usage_no_delete BEFORE DELETE ON usg_association_usage
       BEGIN SELECT RAISE(ABORT, 'association usage is append-only'); END""",
)


class SQLiteResourceCatalogue:
    """Append-only resource and provisional-association catalogue.

    The connection must be the same SQLite connection used by the host's
    canonical store. This class never opens, closes, commits, or rolls back it.
    """

    def __init__(self, connection: sqlite3.Connection, registry_id: str = "usg-v0.2-resource-catalogue"):
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError("connection must be a caller-owned sqlite3.Connection")
        if not registry_id or not isinstance(registry_id, str):
            raise ValueError("registry_id must be non-empty")
        if not connection.in_transaction:
            raise RuntimeError("catalogue installation requires a caller-owned SQLite transaction")
        self.connection = connection
        for statement in _SCHEMA:
            connection.execute(statement)
        connection.execute(
            "INSERT OR IGNORE INTO usg_resource_catalogue_state(singleton,registry_id,version) VALUES(1,?,1)",
            (registry_id,),
        )
        row = connection.execute(
            "SELECT registry_id FROM usg_resource_catalogue_state WHERE singleton=1"
        ).fetchone()
        if row is None or row[0] != registry_id:
            raise ValueError("the supplied SQLite database already belongs to a different resource catalogue")

    def _require_transaction(self) -> None:
        if not self.connection.in_transaction:
            raise RuntimeError("write operations require a caller-owned SQLite transaction")

    def _increment_version(self) -> None:
        self.connection.execute(
            "UPDATE usg_resource_catalogue_state SET version=version+1 WHERE singleton=1"
        )

    @property
    def version(self) -> int:
        row = self.connection.execute(
            "SELECT version FROM usg_resource_catalogue_state WHERE singleton=1"
        ).fetchone()
        return int(row[0])

    def register_resource(self, descriptor: ResourceDescriptor, registered_at: float) -> None:
        self._require_transaction()
        if not isinstance(descriptor, ResourceDescriptor):
            raise TypeError("descriptor must be a ResourceDescriptor")
        try:
            self.connection.execute(
                """INSERT INTO usg_resource_descriptor
                   (resource_id,resource_type,version,sha256,language,provenance,registered_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (descriptor.resource_id, descriptor.resource_type, descriptor.version,
                 descriptor.sha256.lower(), descriptor.language, descriptor.provenance,
                 float(registered_at)),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"resource already registered or invalid: {descriptor.resource_id}") from exc
        self._increment_version()

    def register_association(self, association: SemanticAssociation, created_at: float) -> None:
        self._require_transaction()
        if not isinstance(association, SemanticAssociation):
            raise TypeError("association must be a SemanticAssociation")
        if association.status != "PROVISIONAL":
            raise ValueError("only provisional associations can be registered")
        try:
            self.connection.execute(
                """INSERT INTO usg_semantic_association
                   (association_id,source_ref,target_ref,relation,association_kind,weight,
                    observation_count,provenance,status,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (association.association_id, association.source_ref, association.target_ref,
                 association.relation, association.association_kind, float(association.weight),
                 association.observation_count, association.provenance, "PROVISIONAL",
                 float(created_at)),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"association already registered or invalid: {association.association_id}") from exc
        self._increment_version()

    def record_use(self, association_id: str, used_at: float, context_ref: str | None = None) -> None:
        self._require_transaction()
        exists = self.connection.execute(
            "SELECT 1 FROM usg_semantic_association WHERE association_id=?", (association_id,)
        ).fetchone()
        if exists is None:
            raise KeyError(f"unknown association: {association_id}")
        self.connection.execute(
            "INSERT INTO usg_association_usage(association_id,used_at,context_ref) VALUES(?,?,?)",
            (association_id, float(used_at), context_ref),
        )

    def manifest(self) -> dict:
        state = self.connection.execute(
            "SELECT registry_id,version FROM usg_resource_catalogue_state WHERE singleton=1"
        ).fetchone()
        resources = self.connection.execute(
            """SELECT resource_id,resource_type,version,sha256,language,provenance
               FROM usg_resource_descriptor ORDER BY resource_id"""
        ).fetchall()
        associations = self.connection.execute(
            """SELECT association_id,source_ref,target_ref,relation,association_kind,weight,
                      observation_count,provenance,status
               FROM usg_semantic_association ORDER BY association_id"""
        ).fetchall()
        return {
            "registry_id": state[0],
            "version": int(state[1]),
            "contract": SQLITE_RESOURCE_CATALOGUE_VERSION,
            "resources": [
                {"resource_id": x[0], "resource_type": x[1], "version": x[2],
                 "sha256": x[3], "language": x[4], "provenance": x[5]}
                for x in resources
            ],
            "associations": [
                {"association_id": x[0], "source_ref": x[1], "target_ref": x[2],
                 "relation": x[3], "association_kind": x[4], "weight": float(x[5]),
                 "observation_count": int(x[6]), "provenance": x[7], "status": x[8]}
                for x in associations
            ],
        }

    def digest(self) -> str:
        encoded = json.dumps(self.manifest(), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        return sha256(encoded).hexdigest()

    def retrieve_associations(
        self, source_ref: str, *, now: float, active_limit: int = 10,
        secondary_limit: int = 20, half_life_seconds: float = 30 * 24 * 3600,
    ) -> tuple[AssociationRetrieval, ...]:
        for name, value in (("active_limit", active_limit), ("secondary_limit", secondary_limit)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if half_life_seconds <= 0:
            raise ValueError("half_life_seconds must be positive")
        rows = self.connection.execute(
            """SELECT a.association_id,a.source_ref,a.target_ref,a.relation,a.association_kind,
                      a.weight,a.observation_count,a.provenance,a.status,a.created_at,
                      COUNT(u.usage_id),MAX(u.used_at)
               FROM usg_semantic_association AS a
               LEFT JOIN usg_association_usage AS u ON u.association_id=a.association_id
               WHERE a.source_ref=? AND a.status='PROVISIONAL'
               GROUP BY a.association_id""",
            (source_ref,),
        ).fetchall()
        ranked = []
        for row in rows:
            usage_count = int(row[10])
            total_observations = int(row[6]) + usage_count
            last_used = float(row[11]) if row[11] is not None else float(row[9])
            age = max(0.0, float(now) - last_used)
            decay = math.exp(-math.log(2.0) * age / float(half_life_seconds))
            score = float(row[5]) * (1.0 + math.log1p(total_observations)) * decay
            association = SemanticAssociation(
                row[0], row[1], row[2], row[3], row[4], float(row[5]),
                int(row[6]), row[7], row[8],
            )
            ranked.append((score, total_observations, association, last_used))
        ranked.sort(key=lambda x: (-x[0], -x[2].weight, -x[1], x[2].association_id))
        result = []
        for index, (score, count, association, last_used) in enumerate(ranked):
            if index < active_limit:
                tier = "ACTIVE"
            elif index < active_limit + secondary_limit:
                tier = "SECONDARY"
            else:
                break
            result.append(AssociationRetrieval(association, score, tier, count, last_used))
        return tuple(result)


def verify_resource_file(descriptor: ResourceDescriptor, path: str | Path) -> bool:
    """Verify a registered descriptor against the exact bytes of a resource file."""
    digest = sha256(Path(path).read_bytes()).hexdigest()
    return digest == descriptor.sha256.lower()


def bundled_resource_descriptors() -> tuple[ResourceDescriptor, ...]:
    """Build reproducible descriptors for the currently bundled v0.2 resource set."""
    root = Path(__file__).resolve().parents[2]
    specifications = (
        ("usg-en-ar-foundation-lexicon", "LEXICON", "0.1.0",
         "resources/lexical/v0.1.0/en-ar-foundation-lexicon.json", "en+ar"),
        ("usg-en-ar-operator-lexicon", "LEXICON", "0.2.0",
         "resources/lexical/v0.2.0/en-ar-operator-lexicon.json", "en+ar"),
        ("usg-en-ar-discourse-lexicon", "LEXICON", "0.3.0",
         "resources/lexical/v0.3.0/en-ar-discourse-lexicon.json", "en+ar"),
        ("usg-en-ar-scope-operators", "GRAMMAR", "0.1.0",
         "resources/operators/v0.1.0/operators-en-ar.json", "en+ar"),
        ("usg-v0.2-syntax", "GRAMMAR", "0.2.0",
         "tools/usg_interpretation_v0_2_0/syntax.py", "en+ar"),
        ("usg-v0.2-segmentation", "GRAMMAR", "0.2.0",
         "tools/usg_interpretation_v0_2_0/segmentation.py", "en+ar"),
        ("usg-v0.2-discourse", "DISCOURSE", "0.2.0",
         "tools/usg_interpretation_v0_2_0/discourse.py", "en+ar"),
        ("usg-v0.2-expression-graph-schema", "OTHER", "0.2.0",
         "specifications/usg-interpret-expression-graph-0.2.0.schema.json", None),
    )
    result = []
    for resource_id, resource_type, version, relative, language in specifications:
        path = root / relative
        raw = path.read_bytes()
        if relative.endswith(".json") and "resources/" in relative:
            data = json.loads(raw.decode("utf-8"))
            provenance = data["provenance"]
        else:
            provenance = "Project-authored, versioned implementation/schema; digest covers exact repository bytes."
        result.append(ResourceDescriptor(
            resource_id, resource_type, version, sha256(raw).hexdigest(),
            language, provenance,
        ))
    from .compose import initial_semantic_frame_registry
    frame_manifest = initial_semantic_frame_registry()
    frame_payload = {
        "registry_id": frame_manifest.registry_id,
        "version": frame_manifest.version,
        "frames": [
            {"frame_id": x.frame_id, "predicate_sense_refs": list(x.predicate_sense_refs),
             "required_roles": list(x.required_roles), "version": x.version}
            for x in frame_manifest.frames
        ],
    }
    encoded = json.dumps(frame_payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    result.append(ResourceDescriptor(
        "usg-v0.2-transitive-frames", "SEMANTIC_FRAME", "0.1.0",
        sha256(encoded).hexdigest(), "en+ar",
        "Project-authored transitive predicate frame registry; digest covers canonical frame manifest.",
    ))
    return tuple(result)


__all__ = [
    "SQLITE_RESOURCE_CATALOGUE_VERSION", "AssociationRetrieval",
    "SQLiteResourceCatalogue", "verify_resource_file", "bundled_resource_descriptors",
]
