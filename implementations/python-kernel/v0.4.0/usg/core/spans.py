"""Spans: zero-based, end-exclusive offsets counted in Unicode code points over
the immutable stored text (spec Part 2 §2.12, Enhancement E-26)."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import InvariantViolation


@dataclass(frozen=True, order=True)
class Span:
    start: int
    end: int

    def __post_init__(self):
        if not (isinstance(self.start, int) and isinstance(self.end, int)):
            raise InvariantViolation("span offsets must be ints", "VC-S10")
        if self.start < 0 or self.end <= self.start:
            raise InvariantViolation(f"invalid span [{self.start},{self.end})", "VC-S10")

    @property
    def length(self) -> int:
        return self.end - self.start

    def within(self, text: str) -> bool:
        return 0 <= self.start < self.end <= len(text)

    def text_of(self, text: str) -> str:
        if not self.within(text):
            raise InvariantViolation(f"span [{self.start},{self.end}) outside text of length {len(text)}", "VC-S10")
        return text[self.start : self.end]

    def overlaps(self, other: "Span") -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: "Span") -> bool:
        return self.start <= other.start and other.end <= self.end

    def as_list(self) -> list[int]:
        return [self.start, self.end]
