"""Append-only SQLite snapshots of USG-INTERPRET/0.2.0 processing runs."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import sqlite3
from typing import Any

from .integration import canonical_result_bytes, PIPELINE_CONTRACT


class InterpretationRunIntegrityError(RuntimeError):
    pass


class SQLiteInterpretationRunStore:
    """Persist replayable interpretation envelopes on a caller-owned connection."""

    def __init__(self, connection: sqlite3.Connection):
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError("connection must be a caller-owned sqlite3.Connection")
        if not connection.in_transaction:
            raise RuntimeError("interpretation run-store installation requires a caller-owned transaction")
        self.connection = connection
        connection.execute("""CREATE TABLE IF NOT EXISTS usg_interpretation_run (
            run_id TEXT PRIMARY KEY,
            pipeline_contract TEXT NOT NULL,
            pipeline_version TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            source_sha256 TEXT NOT NULL CHECK(length(source_sha256)=64),
            resource_manifest_digest TEXT NOT NULL CHECK(length(resource_manifest_digest)=64),
            result_json BLOB NOT NULL,
            result_sha256 TEXT NOT NULL CHECK(length(result_sha256)=64),
            created_at TEXT NOT NULL
        ) STRICT""")
        connection.execute("""CREATE TRIGGER IF NOT EXISTS usg_interpretation_run_no_update
            BEFORE UPDATE ON usg_interpretation_run
            BEGIN SELECT RAISE(ABORT, 'interpretation runs are immutable'); END""")
        connection.execute("""CREATE TRIGGER IF NOT EXISTS usg_interpretation_run_no_delete
            BEFORE DELETE ON usg_interpretation_run
            BEGIN SELECT RAISE(ABORT, 'interpretation runs are append-only'); END""")

    def put(self, result: dict[str, Any]) -> dict[str, Any]:
        if not self.connection.in_transaction:
            raise RuntimeError("persisting an interpretation run requires a caller-owned transaction")
        if not isinstance(result, dict) or result.get("pipeline_contract") != PIPELINE_CONTRACT:
            raise ValueError("result must be a USG-INTERPRET/0.2.0 envelope")
        required = ("source_ref", "source_sha256", "resource_manifest_digest", "pipeline_version")
        if any(not isinstance(result.get(key), str) or not result[key] for key in required):
            raise ValueError("interpretation envelope is missing required identity or digest fields")
        source = result.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("text"), str):
            raise ValueError("interpretation envelope must preserve its exact source text")
        source_digest = sha256(source["text"].encode("utf-8")).hexdigest()
        if source_digest != result["source_sha256"] or source.get("sha256") != source_digest:
            raise ValueError("source text does not match the interpretation source digest")
        if source.get("source_id") != result["source_ref"]:
            raise ValueError("source identity does not match the interpretation envelope")
        raw = canonical_result_bytes(result)
        digest = sha256(raw).hexdigest()
        run_id = "run:" + digest[:32]
        now = datetime.now(timezone.utc).isoformat()
        existing = self.connection.execute(
            "SELECT result_sha256 FROM usg_interpretation_run WHERE run_id=?", (run_id,)
        ).fetchone()
        if existing is not None:
            if existing[0] != digest:
                raise InterpretationRunIntegrityError("run ID collision with different result digest")
            created = self.connection.execute(
                "SELECT created_at FROM usg_interpretation_run WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            return {"run_id": run_id, "result_sha256": digest, "created_at": created, "status": "UNCHANGED"}
        self.connection.execute(
            """INSERT INTO usg_interpretation_run
               (run_id,pipeline_contract,pipeline_version,source_ref,source_sha256,
                resource_manifest_digest,result_json,result_sha256,created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (run_id, result["pipeline_contract"], result["pipeline_version"],
             result["source_ref"], result["source_sha256"],
             result["resource_manifest_digest"], sqlite3.Binary(raw), digest, now),
        )
        return {"run_id": run_id, "result_sha256": digest, "created_at": now, "status": "STORED"}

    def get(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM usg_interpretation_run WHERE run_id=?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        raw = bytes(row["result_json"])
        digest = sha256(raw).hexdigest()
        if digest != row["result_sha256"]:
            raise InterpretationRunIntegrityError("stored interpretation result digest mismatch")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InterpretationRunIntegrityError("stored interpretation result is invalid JSON") from exc
        if canonical_result_bytes(result) != raw:
            raise InterpretationRunIntegrityError("stored interpretation result is not canonical JSON")
        source = result.get("source")
        source_digest = (
            sha256(source["text"].encode("utf-8")).hexdigest()
            if isinstance(source, dict) and isinstance(source.get("text"), str)
            else None
        )
        if (source_digest != result.get("source_sha256")
                or source.get("sha256") != source_digest
                or source.get("source_id") != result.get("source_ref")):
            raise InterpretationRunIntegrityError("stored interpretation source digest or identity is invalid")
        if (
            result.get("pipeline_contract") != row["pipeline_contract"]
            or result.get("pipeline_version") != row["pipeline_version"]
            or result.get("source_ref") != row["source_ref"]
            or result.get("source_sha256") != row["source_sha256"]
            or result.get("resource_manifest_digest") != row["resource_manifest_digest"]
        ):
            raise InterpretationRunIntegrityError("stored run metadata does not match its result envelope")
        return {
            "run_id": row["run_id"],
            "result_sha256": digest,
            "created_at": row["created_at"],
            "result": result,
        }

    def list(self, limit: int = 50) -> tuple[dict[str, Any], ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be an integer from 1 through 500")
        rows = self.connection.execute(
            "SELECT run_id FROM usg_interpretation_run ORDER BY created_at DESC,run_id LIMIT ?",
            (limit,),
        ).fetchall()
        return tuple({
            "run_id": row[0],
            "created_at": self.connection.execute(
                "SELECT created_at FROM usg_interpretation_run WHERE run_id=?", (row[0],)
            ).fetchone()[0],
        } for row in rows)


__all__ = ["InterpretationRunIntegrityError", "SQLiteInterpretationRunStore"]
