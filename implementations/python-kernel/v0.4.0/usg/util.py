"""Small shared utilities: injectable clock, hashing, canonical JSON."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Protocol


class Clock(Protocol):
    def now(self) -> float:  # epoch seconds
        ...


class SystemClock:
    def now(self) -> float:
        return time.time()


class FakeClock:
    """Deterministic clock for tests and for replaying scheduled behaviour."""

    def __init__(self, start: float = 1_000_000.0):
        self._t = float(start)

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> float:
        self._t += float(seconds)
        return self._t

    def set(self, t: float) -> None:
        self._t = float(t)


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes | str) -> bytes:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).digest()


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8 friendly.

    Used for hashing audit entries and certificates. Floats are rejected for
    hashed structures that must be canonical (use strings or integers)."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def estimate_tokens(text: str) -> int:
    """Cheap, deliberately pessimistic token estimate (~1 token per 3.5 chars)."""

    if not text:
        return 0
    return max(1, int(len(text) / 3.5) + 1)
