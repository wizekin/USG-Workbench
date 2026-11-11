"""Rebuildable local cache for words actually requested by the user.

This database is deliberately separate from USG's canonical semantic-document store.
It contains only demand-fetched lexical material and usage/analysis observations.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


CACHE_SCHEMA_VERSION = 1


def default_cache_path() -> Path:
    override = os.environ.get("USG_LEXICAL_CACHE_PATH")
    if override:
        return Path(override).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "USG" / "cache" / "external-lexical.sqlite3"
    return Path.home() / ".cache" / "usg" / "external-lexical.sqlite3"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LexicalCache:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else default_cache_path()
        if str(self.path) != ":memory:":
            self.path = self.path.expanduser()
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path), timeout=15)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self.connection:
            self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS cache_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cached_records (
                    cache_key TEXT PRIMARY KEY,
                    queried_form TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    analysis_json TEXT,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_cached_records_expiry
                    ON cached_records(expires_at);
                CREATE TABLE IF NOT EXISTS word_activity (
                    word_key TEXT PRIMARY KEY,
                    display_word TEXT NOT NULL,
                    use_count INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_word_activity_popular
                    ON word_activity(use_count DESC, last_seen DESC);
                CREATE TABLE IF NOT EXISTS provider_rate_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    requested_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_provider_rate_window
                    ON provider_rate_events(provider, requested_at);
                CREATE TABLE IF NOT EXISTS provider_state (
                    provider TEXT NOT NULL,
                    state_key TEXT NOT NULL,
                    state_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(provider, state_key)
                );
                CREATE TABLE IF NOT EXISTS analysis_observations (
                    observation_id TEXT PRIMARY KEY,
                    word_key TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    sense_id TEXT,
                    pattern_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    observed_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_analysis_word
                    ON analysis_observations(word_key, observed_at DESC);
            """)
            row = self.connection.execute(
                "SELECT value FROM cache_meta WHERE key='schema_version'"
            ).fetchone()
            if row is None:
                self.connection.execute(
                    "INSERT INTO cache_meta(key, value) VALUES('schema_version', ?)",
                    (str(CACHE_SCHEMA_VERSION),),
                )
            elif int(row["value"]) != CACHE_SCHEMA_VERSION:
                raise RuntimeError(
                    f"Unsupported lexical-cache schema {row['value']}; expected {CACHE_SCHEMA_VERSION}"
                )

    def get_record(self, cache_key: str, *, allow_expired: bool = False) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT * FROM cached_records WHERE cache_key=?", (cache_key,)
        ).fetchone()
        if row is None:
            return None
        expires = datetime.fromisoformat(row["expires_at"])
        if not allow_expired and expires <= utc_now():
            return None
        return {
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "analysis": json.loads(row["analysis_json"]) if row["analysis_json"] else None,
            "fetched_at": row["fetched_at"],
            "expires_at": row["expires_at"],
            "is_stale": expires <= utc_now(),
        }

    def put_record(
        self, cache_key: str, queried_form: str, payload: dict[str, Any],
        analysis: dict[str, Any] | None, *, status: str = "ok", ttl_seconds: int = 2_592_000,
    ) -> None:
        fetched = utc_now()
        expires = fetched + timedelta(seconds=max(1, ttl_seconds))
        with self.connection:
            self.connection.execute("""
                INSERT INTO cached_records(
                    cache_key, queried_form, status, payload_json, analysis_json, fetched_at, expires_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    queried_form=excluded.queried_form,
                    status=excluded.status,
                    payload_json=excluded.payload_json,
                    analysis_json=excluded.analysis_json,
                    fetched_at=excluded.fetched_at,
                    expires_at=excluded.expires_at
            """, (
                cache_key, queried_form, status,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                json.dumps(analysis, ensure_ascii=False, sort_keys=True) if analysis is not None else None,
                fetched.isoformat(), expires.isoformat(),
            ))

    def record_access(self, word_key: str, display_word: str) -> None:
        now = utc_now().isoformat()
        with self.connection:
            self.connection.execute("""
                INSERT INTO word_activity(word_key, display_word, use_count, first_seen, last_seen)
                VALUES(?, ?, 1, ?, ?)
                ON CONFLICT(word_key) DO UPDATE SET
                    display_word=excluded.display_word,
                    use_count=word_activity.use_count + 1,
                    last_seen=excluded.last_seen
            """, (word_key, display_word, now, now))

    def activity(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.connection.execute("""
            SELECT word_key, display_word, use_count, first_seen, last_seen
            FROM word_activity
            ORDER BY use_count DESC, last_seen DESC
            LIMIT ?
        """, (max(1, min(int(limit), 500)),)).fetchall()
        return [dict(row) for row in rows]

    def cached_records(self, limit: int = 10000) -> list[dict[str, Any]]:
        """Read the locally acquired lexical records for incremental graph assembly."""
        rows = self.connection.execute("""
            SELECT cache_key, queried_form, status, payload_json, analysis_json,
                   fetched_at, expires_at
            FROM cached_records
            WHERE status IN ('found', 'found_with_provider_warnings')
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (max(1, min(int(limit), 100000)),)).fetchall()
        now = utc_now()
        return [{
            "cache_key": row["cache_key"],
            "queried_form": row["queried_form"],
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "analysis": json.loads(row["analysis_json"]) if row["analysis_json"] else None,
            "fetched_at": row["fetched_at"],
            "expires_at": row["expires_at"],
            "is_stale": datetime.fromisoformat(row["expires_at"]) <= now,
        } for row in rows]

    def reserve_provider_request(
        self, provider: str, *, maximum: int, window_seconds: int = 3600,
    ) -> None:
        """Persistently enforce a conservative rolling request budget before network IO."""
        now = utc_now()
        cutoff = (now - timedelta(seconds=window_seconds)).isoformat()
        now_text = now.isoformat()
        with self.connection:
            self.connection.execute(
                "DELETE FROM provider_rate_events WHERE provider=? AND requested_at < ?",
                (provider, cutoff),
            )
            count = self.connection.execute(
                "SELECT COUNT(*) AS n FROM provider_rate_events WHERE provider=? AND requested_at >= ?",
                (provider, cutoff),
            ).fetchone()["n"]
            if count >= maximum:
                raise RuntimeError(
                    f"Local safety limit reached for {provider}: {maximum} requests in {window_seconds} seconds"
                )
            self.connection.execute(
                "INSERT INTO provider_rate_events(provider, requested_at) VALUES(?, ?)",
                (provider, now_text),
            )

    def get_state(self, provider: str, state_key: str) -> str | None:
        row = self.connection.execute(
            "SELECT state_value FROM provider_state WHERE provider=? AND state_key=?",
            (provider, state_key),
        ).fetchone()
        return row["state_value"] if row else None

    def set_state(self, provider: str, state_key: str, state_value: str) -> None:
        with self.connection:
            self.connection.execute("""
                INSERT INTO provider_state(provider, state_key, state_value, updated_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(provider, state_key) DO UPDATE SET
                    state_value=excluded.state_value, updated_at=excluded.updated_at
            """, (provider, state_key, state_value, utc_now().isoformat()))

    def save_analysis_observations(self, word_key: str, observations: list[dict[str, Any]]) -> None:
        if not observations:
            return
        with self.connection:
            for observation in observations:
                observation_id = str(observation.get("observation_id", ""))
                if not observation_id:
                    continue
                self.connection.execute("""
                    INSERT OR IGNORE INTO analysis_observations(
                        observation_id, word_key, provider, sense_id, pattern_type, payload_json, observed_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """, (
                    observation_id,
                    word_key,
                    str(observation.get("provider", "unknown")),
                    observation.get("sense_id"),
                    str(observation.get("pattern_type", "unknown")),
                    json.dumps(observation, ensure_ascii=False, sort_keys=True),
                    utc_now().isoformat(),
                ))

    def observations(self, word_key: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute("""
            SELECT payload_json FROM analysis_observations
            WHERE word_key=? ORDER BY observed_at DESC LIMIT ?
        """, (word_key, max(1, min(int(limit), 1000)))).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
