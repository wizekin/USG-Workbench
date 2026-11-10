"""Canonical JSON encoding and content addressing for USG semantic documents."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

CANONICALIZATION_PROFILE = "USG-CANONICAL-JSON/1.0.0"


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented by the canonical JSON profile."""


def canonical_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes without changing semantic array order."""
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError(f"value is not valid canonical JSON: {exc}") from exc
    return encoded.encode("utf-8")


def canonical_hash(value: Any) -> str:
    """SHA-256 digest of the exact canonical UTF-8 JSON representation."""
    return sha256(canonical_bytes(value)).hexdigest()


def parse_canonical(raw: bytes) -> Any:
    """Parse canonical bytes and reject payloads that are not already canonical."""
    if not isinstance(raw, bytes):
        raise CanonicalizationError("canonical payload must be bytes")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanonicalizationError(f"canonical payload is not valid UTF-8 JSON: {exc}") from exc
    if canonical_bytes(value) != raw:
        raise CanonicalizationError("stored JSON bytes do not match the canonicalization profile")
    return value
