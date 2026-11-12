"""Append-only SQLite persistence for Phase 6 candidate-composition runs.

Uses a caller-owned SQLite connection and never creates a second database owner.
These records are processing artifacts, not canonical USG-SEM/1.0 documents.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json
import sqlite3


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class Phase6RunIntegrityError(RuntimeError):
    pass


class SQLitePhase6CandidateRunStore:
    def __init__(self, connection):
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError("connection must be a caller-owned sqlite3.Connection")
        if not connection.in_transaction:
            raise RuntimeError("Phase 6 run-store installation requires a caller-owned transaction")
        self.connection = connection
        connection.execute("""CREATE TABLE IF NOT EXISTS usg_phase6_candidate_run (
            run_id TEXT PRIMARY KEY,
            pipeline_contract TEXT NOT NULL,
            source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
            input_json BLOB NOT NULL,
            result_json BLOB NOT NULL,
            result_sha256 TEXT NOT NULL CHECK(length(result_sha256)=64),
            resource_manifest_digest TEXT NOT NULL CHECK(length(resource_manifest_digest)=64),
            created_at TEXT NOT NULL
        ) STRICT""")
        connection.execute("""CREATE TRIGGER IF NOT EXISTS usg_phase6_candidate_run_no_update
            BEFORE UPDATE ON usg_phase6_candidate_run
            BEGIN SELECT RAISE(ABORT, 'Phase 6 candidate runs are immutable'); END""")
        connection.execute("""CREATE TRIGGER IF NOT EXISTS usg_phase6_candidate_run_no_delete
            BEFORE DELETE ON usg_phase6_candidate_run
            BEGIN SELECT RAISE(ABORT, 'Phase 6 candidate runs are append-only'); END""")

    def put(self, source, language, graph, result, resource_manifest_digest):
        if not self.connection.in_transaction:
            raise RuntimeError("persisting a Phase 6 run requires a caller-owned transaction")
        if not isinstance(source, str) or not source:
            raise ValueError("source must be non-empty text")
        if language not in {"en", "ar"}:
            raise ValueError("language must be en or ar")
        if not isinstance(graph, dict) or not isinstance(result, dict):
            raise ValueError("graph and result must be objects")
        if not isinstance(resource_manifest_digest, str) or len(resource_manifest_digest) != 64:
            raise ValueError("resource manifest digest must be a SHA-256 hex digest")
        source_digest = sha256(source.encode("utf-8")).hexdigest()
        inputs = {"source": source, "language": language, "graph": graph}
        input_raw = canonical_bytes(inputs)
        result_raw = canonical_bytes(result)
        result_digest = sha256(result_raw).hexdigest()
        run_id = "phase6-run:" + sha256(input_raw + b"\0" + result_raw).hexdigest()[:32]
        existing = self.connection.execute(
            "SELECT result_sha256 FROM usg_phase6_candidate_run WHERE run_id=?", (run_id,)
        ).fetchone()
        if existing:
            if existing[0] != result_digest:
                raise Phase6RunIntegrityError("run ID collision with a different result digest")
            created = self.connection.execute(
                "SELECT created_at FROM usg_phase6_candidate_run WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            return {"run_id": run_id, "result_sha256": result_digest, "created_at": created, "status": "UNCHANGED"}
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """INSERT INTO usg_phase6_candidate_run
            (run_id,pipeline_contract,source_sha256,input_json,result_json,result_sha256,resource_manifest_digest,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (run_id, result.get("pipeline_contract", "USG-INTERPRET/0.3.0"), source_digest,
             sqlite3.Binary(input_raw), sqlite3.Binary(result_raw), result_digest,
             resource_manifest_digest, now),
        )
        return {"run_id": run_id, "result_sha256": result_digest, "created_at": now, "status": "STORED"}

    def get(self, run_id):
        row = self.connection.execute(
            "SELECT * FROM usg_phase6_candidate_run WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        input_raw, result_raw = bytes(row["input_json"]), bytes(row["result_json"])
        if sha256(result_raw).hexdigest() != row["result_sha256"]:
            raise Phase6RunIntegrityError("stored Phase 6 result digest mismatch")
        if sha256(json.loads(input_raw.decode("utf-8"))["source"].encode("utf-8")).hexdigest() != row["source_sha256"]:
            raise Phase6RunIntegrityError("stored Phase 6 source digest mismatch")
        inputs, result = json.loads(input_raw.decode("utf-8")), json.loads(result_raw.decode("utf-8"))
        if canonical_bytes(inputs) != input_raw or canonical_bytes(result) != result_raw:
            raise Phase6RunIntegrityError("stored Phase 6 run is not canonical JSON")
        return {"run_id": row["run_id"], "result_sha256": row["result_sha256"],
                "created_at": row["created_at"], "resource_manifest_digest": row["resource_manifest_digest"],
                "input": inputs, "result": result}

    def list(self, limit=50):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be an integer from 1 to 500")
        rows = self.connection.execute(
            "SELECT run_id,result_sha256,created_at FROM usg_phase6_candidate_run ORDER BY created_at DESC,run_id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return tuple(dict(row) for row in rows)
