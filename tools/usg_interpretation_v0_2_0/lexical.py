"""Versioned, provenance-bearing lexical resources and conservative morphology."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import Path
from typing import Literal

from tools.usg_interpretation_v0_1_0.lexical import Token, tokenize
from tools.usg_interpretation_v0_1_0.source import SourceSnapshot

LEXICAL_ANALYSIS_VERSION = "lexical-analysis/0.3.0"
MORPHOLOGY_RULESET_VERSION = "morphology-rules/0.2.0"
_POS = frozenset({"NOUN", "PROPN", "VERB", "ADJ", "ADV", "PRON", "ADP", "DET", "NUM", "OTHER"})


def _nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _lookup(language: str, form: str) -> str:
    return form.casefold() if language == "en" else form


@dataclass(frozen=True)
class LexicalEntry:
    language: Literal["en", "ar"]
    form: str
    lemma: str
    part_of_speech: str
    sense_id: str
    concept_ref: str | None = None
    features: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        if self.language not in {"en", "ar"}:
            raise ValueError("language must be en or ar")
        for name in ("form", "lemma", "part_of_speech", "sense_id"):
            _nonempty(getattr(self, name), name)
        if self.part_of_speech not in _POS:
            raise ValueError("unsupported part of speech")
        if self.concept_ref is not None:
            _nonempty(self.concept_ref, "concept_ref")
        if not isinstance(self.features, tuple) or any(
            not isinstance(x, tuple) or len(x) != 2
            or not all(isinstance(v, str) and v for v in x) for x in self.features
        ):
            raise ValueError("features must be ordered non-empty string pairs")
        if len(dict(self.features)) != len(self.features):
            raise ValueError("feature keys must be unique")


@dataclass(frozen=True)
class MorphologyRule:
    rule_id: str
    language: Literal["en", "ar"]
    position: Literal["prefix", "suffix"]
    affix: str
    target_part_of_speech: str
    features: tuple[tuple[str, str], ...]
    stem_operation: Literal["IDENTITY", "RESTORE_E", "UNDOUBLE_FINAL", "Y_TO_I"] = "IDENTITY"

    def __post_init__(self):
        for name in ("rule_id", "affix", "target_part_of_speech"):
            _nonempty(getattr(self, name), name)
        if self.language not in {"en", "ar"} or self.position not in {"prefix", "suffix"}:
            raise ValueError("unsupported morphology rule language or position")
        if self.target_part_of_speech not in _POS:
            raise ValueError("unsupported target part of speech")
        if self.stem_operation not in {"IDENTITY", "RESTORE_E", "UNDOUBLE_FINAL", "Y_TO_I"}:
            raise ValueError("unsupported morphology stem operation")
        if not isinstance(self.features, tuple) or not self.features:
            raise ValueError("morphology rule features must be a non-empty tuple")
        if any(not isinstance(x, tuple) or len(x) != 2
               or not all(isinstance(v, str) and v for v in x) for x in self.features):
            raise ValueError("morphology rule features must be string pairs")
        if len(dict(self.features)) != len(self.features):
            raise ValueError("morphology rule feature keys must be unique")


@dataclass(frozen=True)
class LexicalResource:
    resource_id: str
    version: str
    provenance: str
    entries: tuple[LexicalEntry, ...]
    morphology_rules: tuple[MorphologyRule, ...]

    def __post_init__(self):
        for name in ("resource_id", "version", "provenance"):
            _nonempty(getattr(self, name), name)
        if re.fullmatch(r"\d+\.\d+\.\d+", self.version) is None:
            raise ValueError("resource version must use semantic version syntax")
        if not isinstance(self.entries, tuple) or any(not isinstance(x, LexicalEntry) for x in self.entries):
            raise TypeError("entries must be a tuple of LexicalEntry")
        if not isinstance(self.morphology_rules, tuple) or any(
            not isinstance(x, MorphologyRule) for x in self.morphology_rules
        ):
            raise TypeError("morphology_rules must be a tuple of MorphologyRule")
        identities = [(x.language, _lookup(x.language, x.form), x.sense_id) for x in self.entries]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate language/form/sense identity")
        rule_ids = [x.rule_id for x in self.morphology_rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("morphology rule IDs must be unique")

    def content(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "version": self.version,
            "provenance": self.provenance,
            "entries": [
                {"language": x.language, "form": x.form, "lemma": x.lemma,
                 "part_of_speech": x.part_of_speech, "sense_id": x.sense_id,
                 "concept_ref": x.concept_ref, "features": dict(x.features)}
                for x in self.entries
            ],
            "morphology_rules": [
                {"rule_id": x.rule_id, "language": x.language, "position": x.position,
                 "affix": x.affix, "target_part_of_speech": x.target_part_of_speech,
                 "features": dict(x.features), "stem_operation": x.stem_operation}
                for x in self.morphology_rules
            ],
        }

    def digest(self) -> str:
        raw = json.dumps(self.content(), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def manifest(self) -> dict:
        return {**self.content(), "sha256": self.digest(),
                "lexical_analyzer_version": LEXICAL_ANALYSIS_VERSION,
                "morphology_ruleset_version": MORPHOLOGY_RULESET_VERSION}


@dataclass(frozen=True)
class LexicalCandidate:
    lemma: str
    part_of_speech: str
    sense_id: str
    concept_ref: str | None
    features: tuple[tuple[str, str], ...]
    derived_by_rule: str | None = None


@dataclass(frozen=True)
class TokenAnalysis:
    token: Token
    status: Literal["RESOLVED", "AMBIGUOUS", "UNRESOLVED", "NOT_APPLICABLE"]
    candidates: tuple[LexicalCandidate, ...]


@dataclass(frozen=True)
class LexicalAnalysis:
    source: SourceSnapshot
    resource_id: str
    resource_version: str
    resource_sha256: str
    analyzer_version: str
    tokens: tuple[TokenAnalysis, ...]

    def __post_init__(self):
        if not isinstance(self.source, SourceSnapshot):
            raise TypeError("source must be a SourceSnapshot")
        if len(self.resource_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.resource_sha256
        ):
            raise ValueError("resource_sha256 must be a lowercase SHA-256 digest")
        previous_end = 0
        for item in self.tokens:
            token = item.token
            if token.end > len(self.source.text) or self.source.text[token.start:token.end] != token.surface_text:
                raise ValueError("token does not align with exact source")
            if token.start < previous_end:
                raise ValueError("tokens must be ordered and non-overlapping")
            previous_end = token.end
            expected = ("NOT_APPLICABLE" if token.kind != "WORD" else
                        "RESOLVED" if len(item.candidates) == 1 else
                        "AMBIGUOUS" if len(item.candidates) > 1 else "UNRESOLVED")
            if item.status != expected:
                raise ValueError("token status does not match candidate count")


class LexicalAnalyzer:
    """Resolve exact forms first, then only registered one-affix morphology rules."""

    def __init__(self, resource: LexicalResource):
        if not isinstance(resource, LexicalResource):
            raise TypeError("resource must be a LexicalResource")
        self.resource = resource
        index = {}
        for entry in resource.entries:
            index.setdefault((entry.language, _lookup(entry.language, entry.form)), []).append(entry)
        self._index = {key: tuple(value) for key, value in index.items()}

    def _candidate(self, entry: LexicalEntry, rule: MorphologyRule | None = None) -> LexicalCandidate:
        features = dict(entry.features)
        if rule is not None:
            features.update(dict(rule.features))
        return LexicalCandidate(
            entry.lemma, entry.part_of_speech, entry.sense_id, entry.concept_ref,
            tuple(sorted(features.items())), rule.rule_id if rule else None,
        )

    def _morphological_candidates(self, language: str, surface: str) -> tuple[LexicalCandidate, ...]:
        found = []
        for rule in self.resource.morphology_rules:
            if rule.language != language:
                continue
            if rule.position == "prefix":
                if not surface.startswith(rule.affix):
                    continue
                stem = surface[len(rule.affix):]
            else:
                normalized = _lookup(language, surface)
                affix = _lookup(language, rule.affix)
                if not normalized.endswith(affix) or len(surface) <= len(rule.affix):
                    continue
                stem = surface[:-len(rule.affix)]
            if not stem:
                continue
            if rule.stem_operation == "RESTORE_E":
                stem += "e"
            elif rule.stem_operation == "Y_TO_I":
                stem += "y"
            elif rule.stem_operation == "UNDOUBLE_FINAL":
                if len(stem) < 2 or stem[-1] != stem[-2]:
                    continue
                stem = stem[:-1]
            entries = self._index.get((language, _lookup(language, stem)), ())
            for entry in entries:
                if entry.part_of_speech == rule.target_part_of_speech:
                    found.append(self._candidate(entry, rule))
        unique = {}
        for item in found:
            key = (item.lemma, item.part_of_speech, item.sense_id, item.features, item.derived_by_rule)
            unique[key] = item
        return tuple(unique.values())

    def analyze(self, source: SourceSnapshot) -> LexicalAnalysis:
        if not isinstance(source, SourceSnapshot):
            raise TypeError("source must be a SourceSnapshot")
        results = []
        for token in tokenize(source):
            if token.kind != "WORD":
                results.append(TokenAnalysis(token, "NOT_APPLICABLE", ()))
                continue
            entries = self._index.get((source.language, _lookup(source.language, token.surface_text)), ())
            if entries:
                candidates = tuple(self._candidate(entry) for entry in entries)
            else:
                candidates = self._morphological_candidates(source.language, token.surface_text)
            status = "RESOLVED" if len(candidates) == 1 else "AMBIGUOUS" if candidates else "UNRESOLVED"
            results.append(TokenAnalysis(token, status, candidates))
        return LexicalAnalysis(
            source, self.resource.resource_id, self.resource.version, self.resource.digest(),
            LEXICAL_ANALYSIS_VERSION, tuple(results),
        )


def load_lexical_resource(path: str | Path) -> LexicalResource:
    """Load the exact JSON resource; schema validation is performed by the caller/CI."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(raw) != {"resource_id", "version", "provenance", "entries", "morphology_rules"}:
        raise ValueError("resource contains missing or unknown top-level fields")
    entries = tuple(LexicalEntry(
        item["language"], item["form"], item["lemma"], item["part_of_speech"],
        item["sense_id"], item.get("concept_ref"),
        tuple(sorted(item.get("features", {}).items())),
    ) for item in raw["entries"])
    rules = tuple(MorphologyRule(
        item["rule_id"], item["language"], item["position"], item["affix"],
        item["target_part_of_speech"], tuple(sorted(item["features"].items())),
        item.get("stem_operation", "IDENTITY"),
    ) for item in raw["morphology_rules"])
    return LexicalResource(raw["resource_id"], raw["version"], raw["provenance"], entries, rules)


def bundled_lexical_resource() -> LexicalResource:
    return load_lexical_resource(Path(__file__).resolve().parents[2] / "resources" / "lexical" / "v0.1.0" / "en-ar-foundation-lexicon.json")


def bundled_lexical_resource_v0_2_0() -> LexicalResource:
    return load_lexical_resource(Path(__file__).resolve().parents[2] / "resources" / "lexical" / "v0.2.0" / "en-ar-operator-lexicon.json")


def bundled_lexical_resource_v0_3_0() -> LexicalResource:
    return load_lexical_resource(Path(__file__).resolve().parents[2] / "resources" / "lexical" / "v0.3.0" / "en-ar-discourse-lexicon.json")


def compose_lexical_resources(
    resources: tuple[LexicalResource, ...], version: str | None = None
) -> LexicalResource:
    """Compose versioned lexical resources without silently hiding conflicts.

    Exact duplicate entries/rules are retained once. If two resources assign
    different records to the same lexical identity or rule ID, composition
    fails explicitly instead of selecting an arbitrary winner.
    """
    if not isinstance(resources, tuple) or not resources:
        raise ValueError("resources must be a non-empty tuple")
    if any(not isinstance(item, LexicalResource) for item in resources):
        raise TypeError("all resources must be LexicalResource instances")

    entries_by_identity = {}
    rules_by_id = {}
    for resource in resources:
        for entry in resource.entries:
            key = (entry.language, _lookup(entry.language, entry.form), entry.sense_id)
            previous = entries_by_identity.get(key)
            if previous is not None and previous != entry:
                raise ValueError(f"conflicting lexical entry for {key!r}")
            entries_by_identity[key] = entry
        for rule in resource.morphology_rules:
            previous = rules_by_id.get(rule.rule_id)
            if previous is not None and previous != rule:
                raise ValueError(f"conflicting morphology rule {rule.rule_id!r}")
            rules_by_id[rule.rule_id] = rule

    if version is None:
        version = ".".join(map(str, max(
            tuple(int(part) for part in item.version.split("."))
            for item in resources
        )))
    return LexicalResource(
        "usg-en-ar-composite-lexicon",
        version,
        "Deterministic composition of: " + ", ".join(
            f"{item.resource_id}@{item.version}#{item.digest()}" for item in resources
        ),
        tuple(entries_by_identity[key] for key in sorted(entries_by_identity)),
        tuple(rules_by_id[key] for key in sorted(rules_by_id)),
    )


def bundled_lexical_resource_v0_4_0() -> LexicalResource:
    """Return the Phase 5 composite lexicon, preserving component provenance."""
    root = Path(__file__).resolve().parents[2] / "resources" / "lexical"
    discourse = load_lexical_resource(root / "v0.3.0" / "en-ar-discourse-lexicon.json")
    starter = load_lexical_resource(root / "v0.4.0" / "en-core-starter-lexicon.json")
    return compose_lexical_resources((discourse, starter))


def bundled_lexical_resource_v0_5_0() -> LexicalResource:
    """Return the Phase 5 composite lexicon with explicit stem transformations."""
    root = Path(__file__).resolve().parents[2] / "resources" / "lexical"
    discourse = load_lexical_resource(root / "v0.3.0" / "en-ar-discourse-lexicon.json")
    starter = load_lexical_resource(root / "v0.5.0" / "en-core-starter-lexicon.json")
    return compose_lexical_resources((discourse, starter), version="0.5.0")


__all__ = [
    "LEXICAL_ANALYSIS_VERSION", "MORPHOLOGY_RULESET_VERSION", "LexicalEntry",
    "MorphologyRule", "LexicalResource", "LexicalCandidate", "TokenAnalysis",
    "LexicalAnalysis", "LexicalAnalyzer", "load_lexical_resource",
    "bundled_lexical_resource", "bundled_lexical_resource_v0_2_0",
    "bundled_lexical_resource_v0_3_0", "compose_lexical_resources",
    "bundled_lexical_resource_v0_4_0", "bundled_lexical_resource_v0_5_0",
]
