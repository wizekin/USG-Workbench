"""Source-grounded multi-sentence mention, reference, and discourse candidates."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Literal

from .lexical import LexicalAnalysis
from .segmentation import SegmentedDocument

DISCOURSE_ANALYSIS_VERSION = "discourse-analysis/0.2.0"
_NOMINAL_POS = frozenset({"NOUN", "PROPN"})
_MENTION_POS = _NOMINAL_POS | {"PRON"}
_EN_RELATIONS = {
    "then": "TEMPORAL_SEQUENCE", "however": "CONTRAST",
    "therefore": "CONSEQUENCE", "because": "CAUSE",
}
_AR_RELATIONS = {
    "ثم": "TEMPORAL_SEQUENCE", "لكن": "CONTRAST",
    "لذلك": "CONSEQUENCE", "لأن": "CAUSE",
}


def _stable_id(prefix: str, value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), default=str).encode("utf-8")
    return prefix + ":" + sha256(raw).hexdigest()[:20]


@dataclass(frozen=True)
class Mention:
    mention_id: str
    token_ref: str
    sentence_ref: str
    clause_ref: str
    mention_type: Literal["NOMINAL", "PROPER", "PRONOMINAL"]
    surface_text: str
    source_span: tuple[int, int]
    lexical_sense_refs: tuple[str, ...]
    features_by_sense: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]


@dataclass(frozen=True)
class ReferenceCandidate:
    candidate_id: str
    pronoun_mention_ref: str
    antecedent_mention_ref: str
    compatibility_reasons: tuple[str, ...]
    sentence_distance: int
    status: Literal["CANDIDATE"] = "CANDIDATE"


@dataclass(frozen=True)
class DiscourseRelation:
    relation_id: str
    source_sentence_ref: str
    target_sentence_ref: str
    source_clause_ref: str
    target_clause_ref: str
    relation: str
    marker_text: str
    marker_span: tuple[int, int]
    status: Literal["CANDIDATE"] = "CANDIDATE"


@dataclass(frozen=True)
class DiscourseAnalysis:
    source_ref: str
    source_sha256: str
    mentions: tuple[Mention, ...]
    reference_candidates: tuple[ReferenceCandidate, ...]
    unresolved_pronoun_mention_refs: tuple[str, ...]
    relations: tuple[DiscourseRelation, ...]
    status: Literal["NO_REFERENCES", "CANDIDATES_AVAILABLE", "AMBIGUOUS", "PARTIAL", "INCOMPLETE_RESOURCE_LIMIT"]
    analyzer_version: str = DISCOURSE_ANALYSIS_VERSION


class DiscourseAnalyzer:
    """Generate mention and antecedent candidates without resolving identity."""

    def __init__(self, max_antecedents: int = 20, max_candidates_per_pronoun: int = 64):
        for name, value in (("max_antecedents", max_antecedents),
                            ("max_candidates_per_pronoun", max_candidates_per_pronoun)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        self.max_antecedents = max_antecedents
        self.max_candidates_per_pronoun = max_candidates_per_pronoun

    @staticmethod
    def _compatible(pronoun_features, antecedent_features):
        reasons = []
        for key in ("Number", "Gender", "Person"):
            p_value = pronoun_features.get(key)
            a_value = antecedent_features.get(key)
            if p_value and a_value and p_value != a_value:
                return None
            if key == "Gender" and p_value and not a_value:
                return None
            if p_value and a_value:
                reasons.append(key.upper() + "_MATCH")
        return tuple(reasons) or ("NO_CONTRADICTION_IN_REGISTERED_FEATURES",)

    def analyze(self, lexical: LexicalAnalysis, segmented: SegmentedDocument) -> DiscourseAnalysis:
        if lexical.source != segmented.source:
            raise ValueError("discourse analysis inputs must share the exact source snapshot")
        source = lexical.source
        sentence_for = {}
        clause_for = {}
        sentence_index = {item.segment_id: index for index, item in enumerate(segmented.sentences)}
        for item in lexical.tokens:
            token = item.token
            sentence = next((x for x in segmented.sentences
                             if x.start <= token.start and token.end <= x.end), None)
            clause = next((x for x in segmented.clauses
                           if x.start <= token.start and token.end <= x.end), None)
            if sentence is not None:
                sentence_for[token.token_id] = sentence.segment_id
            if clause is not None:
                clause_for[token.token_id] = clause.segment_id

        mentions = []
        pronoun_ids = set()
        for item in lexical.tokens:
            token = item.token
            if token.kind != "WORD" or token.token_id not in sentence_for or token.token_id not in clause_for:
                continue
            candidates = [x for x in item.candidates if x.part_of_speech in _MENTION_POS]
            if not candidates:
                continue
            pos_set = {x.part_of_speech for x in candidates}
            mention_type = ("PRONOMINAL" if "PRON" in pos_set else
                            "PROPER" if "PROPN" in pos_set else "NOMINAL")
            senses = tuple(x.sense_id for x in candidates)
            features = tuple((x.sense_id, tuple(sorted(x.features))) for x in candidates)
            mention_id = _stable_id("mention", [source.source_id, token.token_id, senses])
            mentions.append(Mention(
                mention_id, token.token_id, sentence_for[token.token_id],
                clause_for[token.token_id], mention_type, token.surface_text,
                (token.start, token.end), senses, features,
            ))
            if mention_type == "PRONOMINAL":
                pronoun_ids.add(mention_id)

        mention_index = {x.mention_id: x for x in mentions}
        refs = []
        unresolved = []
        resource_limited = False
        for pronoun in (x for x in mentions if x.mention_type == "PRONOMINAL"):
            p_index = sentence_index[pronoun.sentence_ref]
            antecedents = [
                x for x in mentions
                if x.mention_type != "PRONOMINAL"
                and (sentence_index[x.sentence_ref] < p_index
                     or (x.sentence_ref == pronoun.sentence_ref and x.source_span[1] < pronoun.source_span[0]))
            ]
            antecedents = antecedents[-self.max_antecedents:]
            local = []
            for antecedent in antecedents:
                compatible_reasons = []
                for _, p_features in pronoun.features_by_sense:
                    p_map = dict(p_features)
                    for _, a_features in antecedent.features_by_sense:
                        reasons = self._compatible(p_map, dict(a_features))
                        if reasons is not None:
                            compatible_reasons.extend(reasons)
                if compatible_reasons:
                    reasons = tuple(sorted(set(compatible_reasons)))
                    local.append(ReferenceCandidate(
                        _stable_id("refcand", [pronoun.mention_id, antecedent.mention_id, reasons]),
                        pronoun.mention_id, antecedent.mention_id, reasons,
                        p_index - sentence_index[antecedent.sentence_ref],
                    ))
            if len(local) > self.max_candidates_per_pronoun:
                resource_limited = True
                local = local[-self.max_candidates_per_pronoun:]
            refs.extend(local)
            if not local:
                unresolved.append(pronoun.mention_id)

        relations = []
        marker_map = _EN_RELATIONS if source.language == "en" else _AR_RELATIONS
        for index in range(1, len(segmented.sentences)):
            previous = segmented.sentences[index - 1]
            current = segmented.sentences[index]
            first_word = next((x.token for x in lexical.tokens
                               if x.token.kind == "WORD"
                               and current.start <= x.token.start and x.token.end <= current.end), None)
            if first_word is None:
                continue
            key = first_word.surface_text.casefold() if source.language == "en" else first_word.surface_text
            relation = marker_map.get(key)
            if relation is None:
                continue
            previous_clauses = [x for x in segmented.clauses if x.sentence_ref == previous.segment_id]
            current_clauses = [x for x in segmented.clauses if x.sentence_ref == current.segment_id]
            if not previous_clauses or not current_clauses:
                continue
            relations.append(DiscourseRelation(
                _stable_id("discourse", [previous.segment_id, current.segment_id, relation, first_word.start]),
                previous.segment_id, current.segment_id,
                previous_clauses[-1].segment_id, current_clauses[0].segment_id,
                relation, first_word.surface_text, (first_word.start, first_word.end),
            ))

        ambiguous = any(
            sum(1 for candidate in refs if candidate.pronoun_mention_ref == mention_id) > 1
            for mention_id in pronoun_ids
        )
        if resource_limited:
            status = "INCOMPLETE_RESOURCE_LIMIT"
        elif unresolved:
            status = "PARTIAL"
        elif ambiguous:
            status = "AMBIGUOUS"
        elif refs:
            status = "CANDIDATES_AVAILABLE"
        else:
            status = "NO_REFERENCES"
        return DiscourseAnalysis(
            source.source_id, source.sha256, tuple(mentions), tuple(refs),
            tuple(unresolved), tuple(relations), status,
        )


__all__ = [
    "DISCOURSE_ANALYSIS_VERSION", "Mention", "ReferenceCandidate",
    "DiscourseRelation", "DiscourseAnalysis", "DiscourseAnalyzer",
]
