from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..config import Config
from ..core.spans import Span
from ..errors import InvariantViolation


@dataclass(frozen=True)
class Normalized:
    text: str
    offsets: tuple[tuple[int, int], ...]

    def original_span(self, start, end):
        if not 0 <= start < end <= len(self.offsets):
            raise InvariantViolation("normalized span outside text", "SG-SEC-005")
        return Span(self.offsets[start][0], self.offsets[end - 1][1])


def normalize(text: str) -> Normalized:
    """NFC with explicit code-point offsets; original source is always retained."""
    out, offsets = [], []
    for m in re.finditer(r"[^\r\n][\u0300-\u036f\u064b-\u065f]*|\r\n|[\r\n]", text):
        chunk = unicodedata.normalize("NFC", m.group()).replace("\r\n", "\n")
        out.append(chunk)
        offsets.extend([(m.start(), m.end())] * len(chunk))
    return Normalized("".join(out), tuple(offsets))


def tripwires(text):
    patterns = (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", r"(system|developer)\s*prompt",
                r"(disable|skip)\s+(validation|safety|checks)", r"mark\s+.*\s+verified", r"<\|.*?\|>")
    return tuple("INJECTION_CUE" for p in patterns if re.search(p, text, re.I))


def segment(text: str, config: Config | None = None):
    c = config or Config()
    if len(text) > c["max_source_chars"]:
        raise InvariantViolation("source exceeds configured character budget", "SG-SEC-006")
    # Numbers such as 3.5 do not terminate a unit. Oversize units are retained as
    # single unresolved units, never chopped into independently asserted fragments.
    for m in re.finditer(r"[^.!?。！？؟\n]+(?:[.!?。！？؟]+(?=\s|$)|$)|[^\n]+", text):
        a, b = m.span()
        while a < b and text[a].isspace():
            a += 1
        while b > a and text[b - 1].isspace():
            b -= 1
        if a < b:
            yield Span(a, b)
