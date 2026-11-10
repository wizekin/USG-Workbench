"""Compositional semantic frame mapping for explicitly registered predicates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .lexical import LexicalAnalysis
from .syntax import SyntaxAnalysis

SEMANTIC_COMPOSITION_VERSION = "semantic-composition/0.1.0"


@dataclass(frozen=True)
class PredicateFrame:
    language: str
    lemma: str
    sense_id: str
    predicate_id: str
    argument_roles: tuple[str, ...]

    def __post_init__(self):
        for name in ("language", "lemma", "sense_id", "predicate_id"):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if self.language not in {"en", "ar"}:
            raise ValueError("frame language must be en or ar")
        if not self.argument_roles or len(set(self.argument_roles)) != len(self.argument_roles):
            raise ValueError("argument roles must be non-empty and unique")


@dataclass(frozen=True)
class SemanticFrameRegistry:
    registry_id: str
    version: int
    frames: tuple[PredicateFrame, ...]

    def __post_init__(self):
        if not self.registry_id or isinstance(self.version, bool) or self.version < 1:
            raise ValueError("registry id and positive version are required")
        if not isinstance(self.frames, tuple) or any(not isinstance(x, PredicateFrame) for x in self.frames):
            raise TypeError("frames must be an ordered tuple of PredicateFrame")


@dataclass(frozen=True)
class SemanticNode:
    node_id: str
    op: Literal["REF", "PREDICATE_APP"]
    sort: Literal["TERM", "PROP"]
    operand_refs: tuple[str, ...]
    params: tuple[tuple[str, object], ...]
    token_ids: tuple[str, ...]
    source_span: tuple[int, int]


@dataclass(frozen=True)
class SemanticCandidate:
    candidate_id: str
    status: Literal["RESOLVED", "AMBIGUOUS", "UNRESOLVED", "UNSUPPORTED"]
    frame_id: str | None
    nodes: tuple[SemanticNode, ...]
    root_ref: str | None
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class SemanticComposition:
    status: Literal["COMPOSED", "AMBIGUOUS", "UNRESOLVED", "UNSUPPORTED"]
    candidates: tuple[SemanticCandidate, ...]
    registry_id: str
    registry_version: int
    composer_version: str = SEMANTIC_COMPOSITION_VERSION


class SemanticComposer:
    """Maps supported syntax candidates to explicit role-aware expression DAGs."""

    def __init__(self, registry: SemanticFrameRegistry):
        if not isinstance(registry, SemanticFrameRegistry):
            raise TypeError("registry must be SemanticFrameRegistry")
        self.registry = registry

    def compose(self, lexical: LexicalAnalysis, syntax: SyntaxAnalysis) -> SemanticComposition:
        if syntax.status in {"UNSUPPORTED", "INCOMPLETE"} or not syntax.candidates:
            state = "UNRESOLVED" if syntax.status == "INCOMPLETE" else "UNSUPPORTED"
            return SemanticComposition(state, (), self.registry.registry_id, self.registry.version)
        if syntax.status == "AMBIGUOUS":
            return SemanticComposition("AMBIGUOUS", (), self.registry.registry_id, self.registry.version)
        token_map = {x.token.token_id: x for x in lexical.tokens}
        syntax_candidate = syntax.candidates[0]
        roles = dict(syntax_candidate.roles)
        predicate_id = roles.get("PREDICATE", (None,))[0]
        predicate = token_map.get(predicate_id)
        if predicate is None or predicate.status != "RESOLVED":
            return SemanticComposition("UNRESOLVED", (), self.registry.registry_id, self.registry.version)
        frames = [
            frame for frame in self.registry.frames
            if frame.language == lexical.source.language
            and any(candidate.lemma == frame.lemma and candidate.sense_id == frame.sense_id
                    for candidate in predicate.candidates)
            and len(frame.argument_roles) == len([x for x in roles if x != "PREDICATE"])
        ]
        if not frames:
            candidate = SemanticCandidate("sem:0", "UNSUPPORTED", None, (), None,
                                          ("NO_REGISTERED_SEMANTIC_FRAME",))
            return SemanticComposition("UNSUPPORTED", (candidate,), self.registry.registry_id,
                                       self.registry.version)
        results = []
        for frame_index, frame in enumerate(frames):
            nodes: list[SemanticNode] = []
            role_to_node: dict[str, str] = {}
            for role in frame.argument_roles:
                role_key = role.upper()
                token_ids = roles.get(role_key)
                if not token_ids:
                    break
                token = token_map[token_ids[0]].token
                node_id = f"sem{frame_index}:ref:{role.lower()}"
                role_to_node[role_key] = node_id
                nodes.append(SemanticNode(
                    node_id, "REF", "TERM", (),
                    (("surface", token.surface_text), ("role", role_key)),
                    (token.token_id,), (token.start, token.end),
                ))
            else:
                pred_token = predicate.token
                pred_node_id = f"sem{frame_index}:predicate"
                operand_refs = tuple(role_to_node[x.upper()] for x in frame.argument_roles)
                role_bindings = tuple((role.upper(), role_to_node[role.upper()])
                                      for role in frame.argument_roles)
                nodes.append(SemanticNode(
                    pred_node_id, "PREDICATE_APP", "PROP", operand_refs,
                    (("predicate", frame.predicate_id), ("roleBindings", role_bindings)),
                    tuple(syntax_candidate.token_ids),
                    (syntax_candidate.start, syntax_candidate.end),
                ))
                results.append(SemanticCandidate(
                    f"sem:{frame_index}", "RESOLVED", frame.predicate_id,
                    tuple(nodes), pred_node_id, (),
                ))
        if not results:
            return SemanticComposition("UNRESOLVED", (), self.registry.registry_id, self.registry.version)
        status = "COMPOSED" if len(results) == 1 else "AMBIGUOUS"
        return SemanticComposition(status, tuple(results), self.registry.registry_id,
                                   self.registry.version)


def initial_semantic_frame_registry() -> SemanticFrameRegistry:
    return SemanticFrameRegistry("usg-initial-semantic-frames", 1, (
        PredicateFrame("en", "write", "en:write", "predicate:write", ("SUBJECT", "OBJECT")),
        PredicateFrame("ar", "كتب", "ar:write", "predicate:write", ("SUBJECT", "OBJECT")),
    ))


__all__ = ["SEMANTIC_COMPOSITION_VERSION", "PredicateFrame", "SemanticFrameRegistry",
           "SemanticNode", "SemanticCandidate", "SemanticComposition", "SemanticComposer",
           "initial_semantic_frame_registry"]
