"""Append-only, hash-chained audit log (SG-FND-006, SG-SEC-009).

Entry hash = SHA-256( prev_hash || canonical_json(entry) ). Triggers in the
schema forbid UPDATE/DELETE; ``verify_chain`` detects any out-of-band tamper.
A model component may be *logged* but can never be the actor of a decision event.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable

from ..core.values import Component
from ..errors import PolicyDenied
from ..util import Clock, canonical_json, sha256_hex

GENESIS = "0" * 64
MAX_DETAIL = 500

# Events that record a *decision*. Models may never be the actor of these.
DECISION_EVENTS = frozenset(
    {
        "PROMOTED", "REJECTED", "DEPRECATED", "VERIFIED", "STATUS_CHANGED", "MERGED",
        "EQUIVALENCE_ACTIVATED", "EQUIVALENCE_REVOKED", "RULE_RELEASED", "RULE_ACTIVATED",
        "TIER_CHANGED", "ID_TOMBSTONED", "ROLLED_BACK", "CONSTANT_CALIBRATED", "SEAL_INSTALLED",
        "PATTERN_ACTIVATED", "PATTERN_SUSPENDED", "FRAME_ACTIVATED",
    }
)
_MODEL_ACTORS = frozenset({Component.MODEL_GATEWAY, Component.BIG_MODEL_GATEWAY})


def _entry_payload(at: float, actor: str, event: str, ref: str, detail: str) -> str:
    return canonical_json({"at_ms": int(round(at * 1000)), "actor": actor, "event": event, "ref": ref, "detail": detail})


def append_audit(conn: sqlite3.Connection, clock: Clock, actor: Component, event: str, ref: str, detail: str = "") -> int:
    if actor in _MODEL_ACTORS and event in DECISION_EVENTS:
        raise PolicyDenied(f"{actor.value} may not be the actor of decision event {event}", "SG-FND-004")
    detail = (detail or "")[:MAX_DETAIL]
    row = conn.execute("SELECT entry_hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
    prev = row[0] if row else GENESIS
    at = float(clock.now())
    entry_hash = sha256_hex(prev + _entry_payload(at, actor.value, event, ref, detail))
    cur = conn.execute(
        "INSERT INTO audit_log(at,actor,event,ref,detail,prev_hash,entry_hash) VALUES(?,?,?,?,?,?,?)",
        (at, actor.value, event, ref, detail, prev, entry_hash),
    )
    return int(cur.lastrowid)


def verify_chain(rows: Iterable[sqlite3.Row]) -> tuple[bool, int | None]:
    """Return (ok, first_bad_seq)."""
    prev = GENESIS
    for r in rows:
        expect = sha256_hex(prev + _entry_payload(r["at"], r["actor"], r["event"], r["ref"], r["detail"]))
        if r["prev_hash"] != prev or r["entry_hash"] != expect:
            return False, int(r["seq"])
        prev = r["entry_hash"]
    return True, None
