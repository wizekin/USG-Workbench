"""Source-grounded mention extraction and non-committal referent candidates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .lexical import LexicalAnalysis

REFERENCE_ANALYSIS_VERSION = "mention-reference/0.1.0"
_NOMINAL = frozenset({"NOUN", "PROPN", "PRON"})


@dataclass(frozen=True)
class Mention:
    mention_id: str
    token_id: str
    surface_text: str
    start: int
    end: int
    mention_type: Literal["NOMINAL", "PROPER", "PRONOUN"]
    lexical_senses: tuple[str, ...]

    def __post_init__(self):
        if not self.mention_id or not self.token_id or not self.surface_text:
            raise ValueError("mention identifiers and surface are required")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("mention span must be non-empty and ordered")


@dataclass(frozen=True)
class ReferentCandidate:
    antecedent_mention_id: str
    anaphor_mention_id: str
    basis: str
    status: Literal["CANDIDATE"] = "CANDIDATE"


@dataclass(frozen=True)
class MentionAnalysis:
    mentions: tuple[Mention, ...]
    referent_candidates: tuple[ReferentCandidate, ...]
    unresolved_mention_ids: tuple[str, ...]
    analyzer_version: str = REFERENCE_ANALYSIS_VERSION


class MentionAnalyzer:
    """Extract nominal mentions; exact repeated forms create candidates only."""

    def analyze(self, lexical: LexicalAnalysis) -> MentionAnalysis:
        mentions = []
        for item in lexical.tokens:
            if item.status != "RESOLVED":
                continue
            nominal = [candidate for candidate in item.candidates
                       if candidate.part_of_speech.upper() in _NOMINAL]
            if not nominal:
                continue
            token = item.token
            pos = {x.part_of_speech.upper() for x in nominal}
            kind = "PRONOUN" if "PRON" in pos else "PROPER" if "PROPN" in pos else "NOMINAL"
            mentions.append(Mention(
                f"mention:{token.token_id}", token.token_id, token.surface_text,
                token.start, token.end, kind,
                tuple(x.sense_id for x in nominal),
            ))
        candidates = []
        for index, mention in enumerate(mentions):
            # Only exact surface repetition is a weak retrieval cue. It is
            # deliberately not promoted to identity or a resolved referent.
            for prior in mentions[:index]:
                if prior.surface_text == mention.surface_text:
                    candidates.append(ReferentCandidate(
                        prior.mention_id, mention.mention_id, "EXACT_SURFACE_REPEAT"
                    ))
        return MentionAnalysis(
            tuple(mentions), tuple(candidates),
            tuple(x.mention_id for x in mentions),
        )


__all__ = ["REFERENCE_ANALYSIS_VERSION", "Mention", "ReferentCandidate",
           "MentionAnalysis", "MentionAnalyzer"]
