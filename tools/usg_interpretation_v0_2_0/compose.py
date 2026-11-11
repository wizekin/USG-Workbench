"""Nested, source-grounded semantic composition over accepted syntax candidates."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
from typing import Any, Literal

from .lexical import LexicalAnalysis, LexicalCandidate
from .segmentation import SegmentedDocument
from .syntax import SyntaxAnalysis, SyntaxCandidate, ClauseSyntaxResult

SEMANTIC_COMPOSITION_VERSION = "semantic-composition/0.2.0"


@dataclass(frozen=True)
class PredicateFrame:
    frame_id: str
    predicate_sense_refs: tuple[str, ...]
    required_roles: tuple[str, ...] = ("AGENT", "PATIENT")
    version: str = "0.1.0"

    def __post_init__(self):
        if not self.frame_id or not self.version or not self.predicate_sense_refs:
            raise ValueError("frame identity, version, and predicate senses are required")
        if len(self.predicate_sense_refs) != len(set(self.predicate_sense_refs)):
            raise ValueError("predicate sense references must be unique")
        if self.required_roles != ("AGENT", "PATIENT"):
            raise ValueError("v0.2 transitive frames require AGENT and PATIENT roles")


@dataclass(frozen=True)
class SemanticFrameRegistry:
    registry_id: str
    version: str
    frames: tuple[PredicateFrame, ...]

    def __post_init__(self):
        if not self.registry_id or not self.version:
            raise ValueError("registry identity and version are required")
        frame_ids = [x.frame_id for x in self.frames]
        senses = [sense for frame in self.frames for sense in frame.predicate_sense_refs]
        if len(frame_ids) != len(set(frame_ids)):
            raise ValueError("frame IDs must be unique")
        if len(senses) != len(set(senses)):
            raise ValueError("each predicate sense must map to one frame")

    def by_sense(self) -> dict[str, PredicateFrame]:
        return {sense: frame for frame in self.frames for sense in frame.predicate_sense_refs}


@dataclass(frozen=True)
class SemanticNode:
    node_id: str
    op: Literal["REF", "PREDICATE", "CLAUSE_GROUP"]
    sort: Literal["ENTITY", "PROPOSITION", "PROPOSITION_SET"]
    operand_refs: tuple[str, ...]
    params: tuple[tuple[str, Any], ...]
    source_span: tuple[int, int]
    derivation_refs: tuple[str, ...]

    def __post_init__(self):
        if not self.node_id or not self.derivation_refs:
            raise ValueError("semantic node identity and derivation provenance are required")
        if self.op == "REF" and self.sort != "ENTITY":
            raise ValueError("REF nodes must have ENTITY sort")
        if self.op == "PREDICATE" and self.sort != "PROPOSITION":
            raise ValueError("PREDICATE nodes must have PROPOSITION sort")
        if self.op == "CLAUSE_GROUP" and self.sort != "PROPOSITION_SET":
            raise ValueError("CLAUSE_GROUP nodes must have PROPOSITION_SET sort")
        if self.source_span[0] < 0 or self.source_span[1] <= self.source_span[0]:
            raise ValueError("semantic node source span must be non-empty")


@dataclass(frozen=True)
class SemanticCandidate:
    candidate_id: str
    root_ref: str
    clause_root_refs: tuple[str, ...]
    nodes: tuple[SemanticNode, ...]
    status: Literal["RESOLVED", "AMBIGUOUS", "PARTIAL"]
    source_span: tuple[int, int]

    def __post_init__(self):
        ids = [x.node_id for x in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("semantic node IDs must be unique")
        known = set(ids)
        if self.root_ref not in known or any(x not in known for x in self.clause_root_refs):
            raise ValueError("semantic roots must reference existing nodes")
        if any(ref not in known for node in self.nodes for ref in node.operand_refs):
            raise ValueError("semantic operands must reference existing nodes")
        if self.source_span[0] < 0 or self.source_span[1] <= self.source_span[0]:
            raise ValueError("candidate source span must be non-empty")

    def to_dict(self) -> dict:
        return {
            "candidateId": self.candidate_id,
            "rootRef": self.root_ref,
            "clauseRootRefs": list(self.clause_root_refs),
            "status": self.status,
            "sourceSpan": {"start": self.source_span[0], "end": self.source_span[1],
                           "offsetUnit": "unicode_code_point"},
            "nodes": [{
                "nodeId": node.node_id, "op": node.op, "sort": node.sort,
                "operandRefs": list(node.operand_refs), "params": dict(node.params),
                "sourceSpan": {"start": node.source_span[0], "end": node.source_span[1],
                               "offsetUnit": "unicode_code_point"},
                "derivationRefs": list(node.derivation_refs),
            } for node in self.nodes],
        }


@dataclass(frozen=True)
class SemanticComposition:
    status: Literal["COMPOSED", "AMBIGUOUS", "PARTIAL", "UNSUPPORTED", "INCOMPLETE_RESOURCE_LIMIT"]
    candidates: tuple[SemanticCandidate, ...]
    unresolved_clause_refs: tuple[str, ...]
    composer_version: str = SEMANTIC_COMPOSITION_VERSION

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "composerVersion": self.composer_version,
            "unresolvedClauseRefs": list(self.unresolved_clause_refs),
            "candidates": [x.to_dict() for x in self.candidates],
        }


def initial_semantic_frame_registry() -> SemanticFrameRegistry:
    return SemanticFrameRegistry("usg-v0.2-transitive-frames", "0.1.0", (
        PredicateFrame("frame:write.transitive", ("en:verb.write", "ar:verb.write")),
        PredicateFrame("frame:read.transitive", ("en:verb.read", "ar:verb.read")),
        PredicateFrame("frame:build.transitive", ("en:verb.build", "ar:verb.build")),
        PredicateFrame("frame:test.transitive", ("en:verb.test",)),
        PredicateFrame("frame:examine.transitive", ("ar:verb.examine",)),
    ))


class SemanticComposer:
    """Compose typed proposition graphs while preserving every licensed alternative."""

    def __init__(self, registry: SemanticFrameRegistry | None = None, max_candidates: int = 64):
        if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        self.registry = registry or initial_semantic_frame_registry()
        self.max_candidates = max_candidates
        self._frames = self.registry.by_sense()

    @staticmethod
    def _stable_id(prefix: str, payload: Any) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), default=str).encode("utf-8")
        return prefix + ":" + sha256(raw).hexdigest()[:20]

    @staticmethod
    def _lexical_choice(lexical: LexicalAnalysis, token_id: str, sense_ref: str) -> tuple[Any, LexicalCandidate]:
        item = next((x for x in lexical.tokens if x.token.token_id == token_id), None)
        if item is None:
            raise ValueError(f"syntax references unknown token {token_id}")
        candidate = next((x for x in item.candidates if x.sense_id == sense_ref), None)
        if candidate is None:
            raise ValueError(f"syntax references unknown lexical sense {sense_ref}")
        return item.token, candidate

    def _candidate_options(
        self, lexical: LexicalAnalysis, result: ClauseSyntaxResult,
    ) -> tuple[tuple[SyntaxCandidate, PredicateFrame], ...]:
        options = []
        for syntax_candidate in result.candidates:
            role_refs = dict(syntax_candidate.role_token_refs)
            sense_refs = dict(syntax_candidate.lexical_sense_refs)
            action_token = role_refs.get("ACTION")
            predicate_sense = sense_refs.get(action_token)
            frame = self._frames.get(predicate_sense)
            if frame is not None:
                # Verify every role/sense pair before a graph can be emitted.
                for role in ("AGENT", "ACTION", "PATIENT"):
                    self._lexical_choice(lexical, role_refs[role], sense_refs[role_refs[role]])
                options.append((syntax_candidate, frame))
        return tuple(options)

    def _compose_candidate(
        self, lexical: LexicalAnalysis,
        selected: tuple[tuple[SyntaxCandidate, PredicateFrame], ...],
        attachments, unresolved_refs: tuple[str, ...],
    ) -> SemanticCandidate:
        nodes = []
        clause_roots = []
        clause_spans = []
        for syntax_candidate, frame in selected:
            role_refs = dict(syntax_candidate.role_token_refs)
            sense_refs = dict(syntax_candidate.lexical_sense_refs)
            ref_nodes = {}
            for role in ("AGENT", "PATIENT"):
                token_id = role_refs[role]
                token, entry = self._lexical_choice(lexical, token_id, sense_refs[token_id])
                ref_id = self._stable_id("ref", [syntax_candidate.candidate_id, role, entry.sense_id])
                params = {
                    "role": role,
                    "surfaceText": token.surface_text,
                    "senseRef": entry.sense_id,
                    "conceptRef": entry.concept_ref,
                    "features": dict(entry.features),
                }
                nodes.append(SemanticNode(
                    ref_id, "REF", "ENTITY", (), tuple(sorted(params.items())),
                    (token.start, token.end), (syntax_candidate.candidate_id, token_id, entry.sense_id),
                ))
                ref_nodes[role] = ref_id
            action_token_id = role_refs["ACTION"]
            action_token, action_entry = self._lexical_choice(
                lexical, action_token_id, sense_refs[action_token_id]
            )
            predicate_id = self._stable_id("pred", [syntax_candidate.candidate_id, frame.frame_id])
            role_bindings = {"AGENT": ref_nodes["AGENT"], "PATIENT": ref_nodes["PATIENT"]}
            predicate_params = {
                "predicateRef": frame.frame_id,
                "predicateSenseRef": action_entry.sense_id,
                "frameVersion": frame.version,
                "roleBindings": role_bindings,
            }
            nodes.append(SemanticNode(
                predicate_id, "PREDICATE", "PROPOSITION",
                (ref_nodes["AGENT"], ref_nodes["PATIENT"]),
                tuple(sorted(predicate_params.items())),
                (action_token.start, action_token.end),
                (syntax_candidate.candidate_id, action_token_id, action_entry.sense_id),
            ))
            clause_roots.append(predicate_id)
            clause_spans.append(syntax_candidate.source_span)

        if len(clause_roots) == 1:
            root_ref = clause_roots[0]
        else:
            root_ref = self._stable_id("group", clause_roots)
            source_span = (min(x[0] for x in clause_spans), max(x[1] for x in clause_spans))
            attachment_payload = [{
                "relation": item.relation,
                "markerText": item.marker_text,
                "markerSpan": list(item.marker_span),
                "sourceClauseRef": item.source_clause_ref,
                "targetClauseRef": item.target_clause_ref,
                "status": item.status,
            } for item in attachments
                if item.source_clause_ref in {x.clause_ref for x, _ in selected}
                and item.target_clause_ref in {x.clause_ref for x, _ in selected}]
            group_params = {"attachmentCandidates": attachment_payload,
                            "unresolvedClauseRefs": list(unresolved_refs)}
            nodes.append(SemanticNode(
                root_ref, "CLAUSE_GROUP", "PROPOSITION_SET", tuple(clause_roots),
                tuple(sorted(group_params.items())), source_span,
                tuple(x.candidate_id for x, _ in selected),
            ))
        candidate_id = self._stable_id("sem", [x.candidate_id for x, _ in selected])
        candidate_status = "PARTIAL" if unresolved_refs else "RESOLVED"
        return SemanticCandidate(
            candidate_id, root_ref, tuple(clause_roots), tuple(nodes), candidate_status,
            (min(x[0] for x in clause_spans), max(x[1] for x in clause_spans)),
        )

    def compose(
        self, lexical: LexicalAnalysis, segmented: SegmentedDocument, syntax: SyntaxAnalysis,
    ) -> SemanticComposition:
        if lexical.source != segmented.source:
            raise ValueError("lexical and segmentation artifacts must share the same source")
        if lexical.source != syntax_source(segmented, syntax):
            raise ValueError("syntax and segmentation artifacts must share the same source")
        options_by_clause = []
        unresolved = []
        ambiguous = False
        resource_limited = False
        for result in syntax.clauses:
            if result.status == "AMBIGUOUS":
                ambiguous = True
            if result.status == "INCOMPLETE_RESOURCE_LIMIT":
                resource_limited = True
            options = self._candidate_options(lexical, result)
            if options:
                options_by_clause.append(options)
            else:
                unresolved.append(result.clause_ref)
        if not options_by_clause:
            if resource_limited:
                status = "INCOMPLETE_RESOURCE_LIMIT"
            elif any(x.status == "INCOMPLETE" for x in syntax.clauses):
                status = "PARTIAL"
            else:
                status = "UNSUPPORTED"
            return SemanticComposition(status, (), tuple(unresolved))

        candidates = []
        overflow = False
        for selected in product(*options_by_clause):
            if len(candidates) >= self.max_candidates:
                overflow = True
                break
            candidates.append(self._compose_candidate(
                lexical, selected, syntax.attachments, tuple(unresolved)
            ))
        if overflow or resource_limited:
            status = "INCOMPLETE_RESOURCE_LIMIT"
        elif unresolved:
            status = "PARTIAL"
        elif ambiguous or len(candidates) > 1:
            status = "AMBIGUOUS"
        else:
            status = "COMPOSED"
        if status == "INCOMPLETE_RESOURCE_LIMIT":
            candidates = [
                SemanticCandidate(x.candidate_id, x.root_ref, x.clause_root_refs,
                                  x.nodes, "PARTIAL", x.source_span)
                for x in candidates
            ]
        elif status == "AMBIGUOUS":
            candidates = [
                SemanticCandidate(x.candidate_id, x.root_ref, x.clause_root_refs,
                                  x.nodes, "AMBIGUOUS", x.source_span)
                for x in candidates
            ]
        return SemanticComposition(status, tuple(candidates), tuple(unresolved))


def syntax_source(segmented: SegmentedDocument, syntax: SyntaxAnalysis):
    """Return the source snapshot only after confirming clause refs are in this segmentation."""
    clause_ids = {x.segment_id for x in segmented.clauses}
    if any(x.clause_ref not in clause_ids for x in syntax.clauses):
        raise ValueError("syntax references a clause outside the supplied segmentation")
    if (syntax.source_ref != segmented.source.source_id
            or syntax.source_sha256 != segmented.source.sha256):
        raise ValueError("syntax artifact source identity/digest does not match segmentation")
    return segmented.source


__all__ = [
    "SEMANTIC_COMPOSITION_VERSION", "PredicateFrame", "SemanticFrameRegistry",
    "SemanticNode", "SemanticCandidate", "SemanticComposition",
    "initial_semantic_frame_registry", "SemanticComposer",
]
