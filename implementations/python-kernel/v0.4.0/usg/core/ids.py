"""Typed identifiers (spec Part 2 §2.4).

A bare integer is never an ID: it is always (space, number). IDs are
meaning-free, immutable and never reused. Workspace handles (``W:n``) are
task-local and are *never* persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..errors import InvariantViolation


class IdSpace(str, Enum):
    CONCEPT = "CONCEPT"
    FRAME = "FRAME"
    ROLE = "ROLE"
    RELATION = "RELATION"
    REFERENT = "REFERENT"
    INSTANCE = "INSTANCE"
    ASSERTION = "ASSERTION"
    EVIDENCE = "EVIDENCE"
    SOURCE = "SOURCE"
    CERTIFICATE = "CERTIFICATE"
    DEFINITION = "DEFINITION"
    MAPPING = "MAPPING"
    ENTRY = "ENTRY"
    SENSE = "SENSE"
    DOMAIN = "DOMAIN"
    CANDIDATE = "CANDIDATE"
    NODE = "NODE"
    PROVISIONAL = "P"  # provisional concepts/frames: never in trusted records (I-07)


@dataclass(frozen=True, order=True)
class Ref:
    """A persistent reference. ``Ref(IdSpace.CONCEPT, 12)`` prints as ``CONCEPT:12``."""

    space: IdSpace
    n: int

    def __post_init__(self):
        if not isinstance(self.space, IdSpace):
            raise InvariantViolation(f"invalid id space {self.space!r}", "I-01")
        if not isinstance(self.n, int) or isinstance(self.n, bool) or self.n <= 0:
            raise InvariantViolation(f"id number must be a positive int (0 is invalid), got {self.n!r}", "I-01")

    def __str__(self) -> str:
        return f"{self.space.value}:{self.n}"

    @property
    def is_provisional(self) -> bool:
        return self.space is IdSpace.PROVISIONAL

    @staticmethod
    def parse(text: str) -> "Ref":
        try:
            sp, num = text.split(":", 1)
            return Ref(IdSpace(sp), int(num))
        except (ValueError, KeyError) as e:
            raise InvariantViolation(f"cannot parse reference {text!r}", "I-01") from e


@dataclass(frozen=True, order=True)
class WHandle:
    """Task-local workspace handle ``W:n`` — never persisted (spec §2.4.1 item 9)."""

    task: str
    n: int

    def __str__(self) -> str:
        return f"W:{self.task}:{self.n}"


def ref(space: IdSpace, n: int) -> Ref:
    return Ref(space, n)
