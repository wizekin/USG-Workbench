"""Conservative clause-level syntax candidates for English and MSA Arabic."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
from typing import Literal

from .lexical import LexicalAnalysis
from .segmentation import SegmentedDocument, ClauseSegment

SYNTAX_ANALYSIS_VERSION = "syntax-analysis/0.2.0"

_PATTERNS = {
    "en": (
        ("en.simple_transitive.svo", ({"NOUN", "PROPN"}, {"VERB"}, {"NOUN", "PROPN"}), ("AGENT", "ACTION", "PATIENT")),
    ),
    "ar": (
        ("ar.simple_transitive.vso", ({"VERB"}, {"NOUN", "PROPN"}, {"NOUN", "PROPN"}), ("ACTION", "AGENT", "PATIENT")),
        ("ar.simple_transitive.svo", ({"NOUN", "PROPN"}, {"VERB"}, {"NOUN", "PROPN"}), ("AGENT", "ACTION", "PATIENT")),
    ),
}


@dataclass(frozen=True)
class ConstituentNode:
    constituent_id: str
    constituent_type: Literal["CLAUSE", "NP", "VP"]
    token_refs: tuple[str, ...]
    source_span: tuple[int, int]


@dataclass(frozen=True)
class DependencyEdge:
    head_token_ref: str
    dependent_token_ref: str
    relation: Literal["NSUBJ", "OBJ"]


@dataclass(frozen=True)
class SyntaxCandidate:
    candidate_id: str
    construction_id: str
    clause_ref: str
    role_token_refs: tuple[tuple[str, str], ...]
    lexical_sense_refs: tuple[tuple[str, str], ...]
    constituents: tuple[ConstituentNode, ...]
    dependencies: tuple[DependencyEdge, ...]
    source_span: tuple[int, int]


@dataclass(frozen=True)
class ClauseSyntaxResult:
    clause_ref: str
    status: Literal["RESOLVED", "AMBIGUOUS", "INCOMPLETE", "UNSUPPORTED", "INCOMPLETE_RESOURCE_LIMIT"]
    candidates: tuple[SyntaxCandidate, ...]
    unresolved_token_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClauseAttachment:
    attachment_id: str
    source_clause_ref: str
    target_clause_ref: str
    relation: str
    marker_text: str
    marker_span: tuple[int, int]
    status: Literal["CANDIDATE"] = "CANDIDATE"


@dataclass(frozen=True)
class SyntaxAnalysis:
    clauses: tuple[ClauseSyntaxResult, ...]
    attachments: tuple[ClauseAttachment, ...]
    status: Literal["COMPLETE", "AMBIGUOUS", "PARTIAL", "UNSUPPORTED", "INCOMPLETE_RESOURCE_LIMIT"]
    analyzer_version: str = SYNTAX_ANALYSIS_VERSION


class SyntaxAnalyzer:
    """Build explicit role, constituent, dependency, and attachment candidates."""

    def __init__(self, max_candidates: int = 64):
        if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        self.max_candidates = max_candidates

    @staticmethod
    def _candidate_id(clause_ref: str, construction: str, choices: tuple[tuple[str, str], ...]) -> str:
        raw = json.dumps([clause_ref, construction, choices], ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
        return "syn:" + sha256(raw).hexdigest()[:20]

    @staticmethod
    def _constituents(candidate_id, clause_ref, items, role_order):
        by_role = {role: item for role, item in zip(role_order, items)}
        agent = by_role["AGENT"].token
        action = by_role["ACTION"].token
        patient = by_role["PATIENT"].token
        all_refs = tuple(item.token.token_id for item in items)
        return (
            ConstituentNode(candidate_id + ":clause", "CLAUSE", all_refs,
                            (items[0].token.start, items[-1].token.end)),
            ConstituentNode(candidate_id + ":np-agent", "NP", (agent.token_id,),
                            (agent.start, agent.end)),
            ConstituentNode(candidate_id + ":vp", "VP", (action.token_id, patient.token_id),
                            (action.start, patient.end)),
            ConstituentNode(candidate_id + ":np-patient", "NP", (patient.token_id,),
                            (patient.start, patient.end)),
        )

    def _analyze_clause(self, lexical: LexicalAnalysis, clause: ClauseSegment) -> ClauseSyntaxResult:
        items = [item for item in lexical.tokens
                 if item.token.kind == "WORD"
                 and clause.start <= item.token.start and item.token.end <= clause.end]
        if not items:
            return ClauseSyntaxResult(clause.segment_id, "UNSUPPORTED", ())
        unresolved = tuple(x.token.token_id for x in items if x.status == "UNRESOLVED")
        if unresolved:
            return ClauseSyntaxResult(clause.segment_id, "INCOMPLETE", (), unresolved)
        if len(items) != 3:
            return ClauseSyntaxResult(clause.segment_id, "UNSUPPORTED", ())

        candidates = []
        overflow = False
        for construction_id, allowed_pos, role_order in _PATTERNS[lexical.source.language]:
            choices = []
            for item, allowed in zip(items, allowed_pos):
                eligible = [candidate for candidate in item.candidates
                            if candidate.part_of_speech in allowed]
                if not eligible:
                    choices = []
                    break
                choices.append(eligible)
            if not choices:
                continue
            for combination in product(*choices):
                if len(candidates) >= self.max_candidates:
                    overflow = True
                    break
                role_refs = tuple((role, item.token.token_id)
                                  for role, item in zip(role_order, items))
                sense_refs = tuple((item.token.token_id, candidate.sense_id)
                                   for item, candidate in zip(items, combination))
                candidate_id = self._candidate_id(clause.segment_id, construction_id, sense_refs)
                by_role = {role: item for role, item in zip(role_order, items)}
                action_token = by_role["ACTION"].token
                agent_token = by_role["AGENT"].token
                patient_token = by_role["PATIENT"].token
                constituents = self._constituents(candidate_id, clause.segment_id, items, role_order)
                dependencies = (
                    DependencyEdge(action_token.token_id, agent_token.token_id, "NSUBJ"),
                    DependencyEdge(action_token.token_id, patient_token.token_id, "OBJ"),
                )
                candidates.append(SyntaxCandidate(
                    candidate_id, construction_id, clause.segment_id,
                    role_refs, sense_refs, constituents, dependencies,
                    (items[0].token.start, items[-1].token.end),
                ))
            if overflow:
                break
        if overflow:
            return ClauseSyntaxResult(clause.segment_id, "INCOMPLETE_RESOURCE_LIMIT", tuple(candidates))
        if not candidates:
            return ClauseSyntaxResult(clause.segment_id, "UNSUPPORTED", ())
        status = "RESOLVED" if len(candidates) == 1 else "AMBIGUOUS"
        return ClauseSyntaxResult(clause.segment_id, status, tuple(candidates))

    def analyze(self, lexical: LexicalAnalysis, segmented: SegmentedDocument) -> SyntaxAnalysis:
        if not isinstance(lexical, LexicalAnalysis) or not isinstance(segmented, SegmentedDocument):
            raise TypeError("lexical and segmented inputs must be versioned analysis artifacts")
        if lexical.source != segmented.source:
            raise ValueError("lexical and segmentation artifacts must share the exact source snapshot")
        results = tuple(self._analyze_clause(lexical, clause) for clause in segmented.clauses)
        attachments = tuple(ClauseAttachment(
            boundary.boundary_id, boundary.left_clause_ref, boundary.right_clause_ref,
            boundary.relation, boundary.marker_text, boundary.marker_span,
        ) for boundary in segmented.boundaries)
        statuses = {x.status for x in results}
        if not results:
            overall = "UNSUPPORTED"
        elif "INCOMPLETE_RESOURCE_LIMIT" in statuses:
            overall = "INCOMPLETE_RESOURCE_LIMIT"
        elif "AMBIGUOUS" in statuses:
            overall = "AMBIGUOUS"
        elif "INCOMPLETE" in statuses:
            overall = "PARTIAL"
        elif "UNSUPPORTED" in statuses:
            overall = "PARTIAL" if "RESOLVED" in statuses else "UNSUPPORTED"
        else:
            overall = "COMPLETE"
        return SyntaxAnalysis(results, attachments, overall)


__all__ = [
    "SYNTAX_ANALYSIS_VERSION", "ConstituentNode", "DependencyEdge",
    "SyntaxCandidate", "ClauseSyntaxResult", "ClauseAttachment",
    "SyntaxAnalysis", "SyntaxAnalyzer",
]
