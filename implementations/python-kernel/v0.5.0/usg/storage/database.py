"""SQLite access with the disciplines the specification requires:

* WAL journal, foreign keys on, busy timeout (Part 11 §11.3.2).
* ONE writer connection guarded by a lock; ``BEGIN IMMEDIATE`` per write
  transaction; ``synchronous=FULL`` for authoritative (REGISTRY/PROMOTION) commits.
* Sole-writer discipline (SG-GOV-008): a ``WriteTxn`` is opened for one or more
  ``WriterRole``s and refuses to modify tables owned by other roles.
* Read access through ``ReadTxn``, which can only run SELECT statements.

This is a discipline guard against bugs and against model-produced output
reaching the wrong store; it is not a security boundary against code that
already runs in the process.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from ..errors import PolicyDenied, StorageError
from ..util import Clock, SystemClock
from . import schema
from .audit import append_audit
from .schema import WriterRole
from ..core.values import Component

_WRITE_RE = re.compile(
    r"^\s*(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|REPLACE\s+INTO|UPDATE(?:\s+OR\s+\w+)?|DELETE\s+FROM)\s+[\"`\[]?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
_READ_RE = re.compile(r"^\s*(SELECT|EXPLAIN)\b", re.IGNORECASE)
_WITH_RE = re.compile(r"^\s*WITH\b", re.IGNORECASE)
_MUTATING_KW = re.compile(r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|CREATE|ATTACH)\b", re.IGNORECASE)
_SAVEPOINT_RE = re.compile(r"^\s*(SAVEPOINT|RELEASE|ROLLBACK\s+TO)\b", re.IGNORECASE)


def _is_read(sql: str) -> bool:
    if _READ_RE.match(sql):
        return True
    return bool(_WITH_RE.match(sql)) and not _MUTATING_KW.search(sql)


class ReadTxn:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        if not _is_read(sql):
            raise PolicyDenied("read transactions can only run SELECT statements", "SG-GOV-008")
        return self._conn.execute(sql, tuple(params)).fetchall()

    def one(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql: str, params: Sequence[Any] = (), default: Any = None) -> Any:
        row = self.one(sql, params)
        return row[0] if row is not None else default


class WriteTxn(ReadTxn):
    def __init__(self, conn: sqlite3.Connection, roles: frozenset[WriterRole], clock: Clock):
        super().__init__(conn)
        self.roles = roles
        self.clock = clock

    # -- permissions -------------------------------------------------------
    def require_role(self, role: WriterRole) -> None:
        if role not in self.roles:
            raise PolicyDenied(f"operation requires writer role {role.value}", "SG-GOV-008")

    def _check_write(self, sql: str) -> None:
        if _is_read(sql) or _SAVEPOINT_RE.match(sql):
            return
        m = _WRITE_RE.match(sql)
        if not m:
            raise PolicyDenied("statement type not permitted in a write transaction", "SG-GOV-008")
        table = m.group(1)
        owners = schema.TABLE_OWNERS.get(table)
        if owners is None:
            raise StorageError(f"table {table!r} has no registered owner")
        if not (owners & self.roles):
            raise PolicyDenied(
                f"roles {sorted(r.value for r in self.roles)} may not write table {table!r} "
                f"(owners: {sorted(r.value for r in owners)})",
                "SG-GOV-008",
            )

    # -- execution ---------------------------------------------------------
    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        self._check_write(sql)
        return self._conn.execute(sql, tuple(params))

    def executemany(self, sql: str, seq: Sequence[Sequence[Any]]) -> sqlite3.Cursor:
        self._check_write(sql)
        return self._conn.executemany(sql, seq)

    def audit(self, actor: Component, event: str, ref: str, detail: str = "") -> int:
        """Append to the hash-chained audit log inside this transaction."""
        return append_audit(self._conn, self.clock, actor, event, ref, detail)


class Database:
    def __init__(self, path: str = ":memory:", clock: Clock | None = None, busy_timeout_ms: int = 5000):
        self.path = path
        self.clock: Clock = clock or SystemClock()
        self._memory = path == ":memory:"
        self._busy = busy_timeout_ms
        self._lock = threading.RLock()
        self._readers: dict[int, sqlite3.Connection] = {}
        self._reader_lock = threading.Lock()
        self._writer = self._connect()
        if not self._memory:
            self._writer.execute("PRAGMA journal_mode=WAL")
        self._closed = False

    # -- connections -------------------------------------------------------
    def _connect(self, readonly: bool = False) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False, timeout=self._busy / 1000)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(f"PRAGMA busy_timeout={int(self._busy)}")
        conn.execute("PRAGMA synchronous=NORMAL")
        if readonly:
            conn.execute("PRAGMA query_only=ON")
        return conn

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            for c in self._readers.values():
                try:
                    c.close()
                except sqlite3.Error:
                    pass
            self._readers.clear()
            self._writer.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- migrations --------------------------------------------------------
    def migrate(self) -> list[int]:
        """Apply pending migrations atomically. Idempotent. Returns versions applied."""
        applied: list[int] = []
        with self._lock:
            c = self._writer
            has = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migration'").fetchone()
            done = {r[0] for r in c.execute("SELECT version FROM schema_migration")} if has else set()
            for version, name, ddl in sorted(schema.MIGRATIONS):
                if version in done:
                    continue
                safe_name = name.replace("'", "''")
                script = (
                    "BEGIN IMMEDIATE;\n" + ddl + f"\nINSERT INTO schema_migration(version,name,applied_at) "
                    f"VALUES({int(version)},'{safe_name}',{float(self.clock.now())!r});\nCOMMIT;"
                )
                try:
                    c.executescript(script)
                except sqlite3.Error:
                    if c.in_transaction:
                        c.execute("ROLLBACK")
                    raise
                applied.append(version)
        return applied

    def schema_version(self) -> int:
        with self.read() as r:
            try:
                return int(r.scalar("SELECT COALESCE(MAX(version),0) FROM schema_migration", default=0))
            except sqlite3.OperationalError:
                return 0

    # -- transactions ------------------------------------------------------
    @contextmanager
    def write(self, *roles: WriterRole) -> Iterator[WriteTxn]:
        if not roles:
            raise PolicyDenied("a write transaction needs at least one writer role", "SG-GOV-008")
        role_set = frozenset(roles)
        authoritative = bool(role_set & {WriterRole.REGISTRY, WriterRole.PROMOTION})
        with self._lock:
            c = self._writer
            if authoritative and not self._memory:
                c.execute("PRAGMA synchronous=FULL")
            c.execute("BEGIN IMMEDIATE")
            try:
                yield WriteTxn(c, role_set, self.clock)
            except BaseException:
                if c.in_transaction:
                    c.execute("ROLLBACK")
                raise
            else:
                c.execute("COMMIT")
            finally:
                if authoritative and not self._memory:
                    c.execute("PRAGMA synchronous=NORMAL")

    @contextmanager
    def read(self) -> Iterator[ReadTxn]:
        if self._memory:
            with self._lock:  # the only connection is shared
                yield ReadTxn(self._writer)
            return
        tid = threading.get_ident()
        with self._reader_lock:
            conn = self._readers.get(tid)
            if conn is None:
                conn = self._connect(readonly=True)
                self._readers[tid] = conn
        yield ReadTxn(conn)

    # -- maintenance -------------------------------------------------------
    def journal_mode(self) -> str:
        with self._lock:
            return str(self._writer.execute("PRAGMA journal_mode").fetchone()[0]).lower()

    def integrity_check(self) -> bool:
        with self._lock:
            return self._writer.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    def checkpoint(self) -> None:
        if not self._memory:
            with self._lock:
                self._writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def raw_unsafe_connection(self) -> sqlite3.Connection:
        """For tests that must tamper with storage to prove tamper detection."""
        return self._writer
