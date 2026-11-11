"""Dependency-driven nominal candidate extraction from UD CoNLL-U.

This module consumes an existing dependency graph and converts selected
syntactic relations into source-grounded USG nominal candidate structures.
It does not perform parsing and does not claim semantic adjudication.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_external_pud_v0_5.camel_msa import normalize_arabic
from tools.phase6_external_pud_v0_8.spacy_dependencies import parse_dependency_conllu

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-6-ud-nominal-candidates.json"

EN_TEMPORAL = {
    "today", "yesterday", "tomorrow", "now", "later", "soon", "recently",
    "currently", "early", "late", "then", "afterward", "beforehand",
}
AR_TEMPORAL = {
    "اليوم", "امس", "غدا", "الان", "لاحقا", "حاليا", "مبكرا",
    "متاخرا", "ثم", "قبلا",
}


def normalize_surface(value: str, language: str) -> str:
    return value.casefold() if language == "en" else normalize_arabic(value)


def align_token_spans(text: str, tokens: list[dict], language: str) -> tuple[dict, list[int]]:
    normalized_chars = []
    original_starts = []
    original_ends = []
    for index, char in enumerate(text):
        normalized = normalize_surface(char, language)
        for output_char in normalized:
            normalized_chars.append(output_char)
            original_starts.append(index)
            original_ends.append(index + 1)
    normalized_text = "".join(normalized_chars)
    cursor = 0
    spans, failed = {}, []
    for index, token in enumerate(tokens):
        target = normalize_surface(token["form"], language)
        if not target:
            failed.append(index)
            continue
        found = normalized_text.find(target, cursor)
        if found < 0:
            failed.append(index)
            continue
        last = found + len(target) - 1
        start = original_starts[found]
        end = original_ends[last]
        spans[index] = {
            "start": start,
            "end": end,
            "surface": text[start:end],
            "token_id": token["id"],
        }
        cursor = last + 1
    return spans, failed


def _phrase_span(spans: dict, indexes: list[int]) -> dict | None:
    available = [spans[index] for index in indexes if index in spans]
    if len(available) != len(indexes) or not available:
        return None
    start = min(item["start"] for item in available)
    end = max(item["end"] for item in available)
    return {"start": start, "end": end}


def _candidate(text: str, construction: str, rule: str, relation_type: str,
               roles: dict[str, int | list[int]], spans: dict, tokens: list[dict],
               dependent_index: int, marker_indexes: list[int] | None = None,
               semantic_status: str | None = None) -> dict | None:
    role_spans = {}
    role_bindings = {}
    for role, indexes in roles.items():
        indexes = indexes if isinstance(indexes, list) else [indexes]
        phrase = _phrase_span(spans, indexes)
        if phrase is None:
            return None
        role_spans[role] = phrase
        role_bindings[role] = text[phrase["start"]:phrase["end"]]
    marker_indexes = marker_indexes or []
    marker_spans = []
    for index in marker_indexes:
        if index not in spans:
            return None
        marker_spans.append(spans[index])
    head_index = roles.get("HEAD")
    if head_index is None:
        head_index = roles.get("POSSESSED")
    if head_index is None:
        head_index = roles.get("GENITIVE_HEAD")
    if isinstance(head_index, list):
        head_index = head_index[0]
    head_token = tokens[head_index] if isinstance(head_index, int) else None
    dep = tokens[dependent_index]
    return {
        "status": "CANDIDATE",
        "candidate_only": True,
        "construction_id": construction,
        "relation_type": relation_type,
        "semantic_status": semantic_status,
        "role_bindings": role_bindings,
        "role_spans": role_spans,
        "grammatical_markers": marker_spans,
        "predicate_span": None,
        "derivation": {
            "rule_id": rule,
            "source": "UD_DEPENDENCY_GRAPH",
            "dependency_relation": dep["deprel"],
            "head_token_id": head_token["id"] if head_token else None,
            "dependent_token_id": dep["id"],
        },
    }


def adapt_sentence(sentence: dict, language: str) -> dict:
    text = sentence.get("meta", {}).get("text", "")
    tokens = sentence["tokens"]
    if not text:
        return {
            "status": "ABSTAIN",
            "candidates": [],
            "reason": "SOURCE_TEXT_MISSING",
            "span_alignment_failures": len(tokens),
        }
    spans, failed = align_token_spans(text, tokens, language)
    children = defaultdict(list)
    for index, token in enumerate(tokens):
        head = token.get("gold_head_index")
        if head is not None and head != index:
            children[head].append(index)

    candidates = []
    for dependent_index, token in enumerate(tokens):
        relation = token["deprel"]
        head_index = token.get("gold_head_index")
        if head_index is None or head_index == dependent_index:
            continue
        head = tokens[head_index]
        head_pos = head["upos"]
        dep_pos = token["upos"]

        if relation == "amod" and head_pos in {"NOUN", "PROPN"} and dep_pos == "ADJ":
            candidate = _candidate(
                text, "nominal.attribute_modifier", "ud.amod.attribute.v1",
                "ATTRIBUTE_MODIFIER",
                {"HEAD": head_index, "ATTRIBUTE": dependent_index},
                spans, tokens, dependent_index,
            )
            if candidate:
                candidates.append(candidate)
            continue

        if relation.startswith("compound") and head_pos in {"NOUN", "PROPN"} and dep_pos in {"NOUN", "PROPN"}:
            candidate = _candidate(
                text, "nominal.compound_modifier", "ud.compound.head_modifier.v1",
                "NOUN_COMPOUND",
                {"HEAD": head_index, "COMPOUND_MODIFIER": dependent_index},
                spans, tokens, dependent_index,
            )
            if candidate:
                candidates.append(candidate)
            continue

        if relation == "nmod:poss" and head_pos in {"NOUN", "PROPN"} and dep_pos in {"NOUN", "PROPN", "PRON"}:
            candidate = _candidate(
                text, "nominal.possession", "ud.nmod_poss.possession.v1",
                "POSSESSION",
                {"POSSESSED": head_index, "POSSESSOR": dependent_index},
                spans, tokens, dependent_index,
            )
            if candidate:
                candidates.append(candidate)
            continue

        if relation == "nmod" and head_pos in {"NOUN", "PROPN"} and dep_pos in {"NOUN", "PROPN", "PRON"}:
            markers = [
                child for child in children.get(dependent_index, [])
                if tokens[child]["deprel"] == "case"
            ]
            marker_text = " ".join(tokens[index]["form"] for index in markers)
            marker_norm = normalize_surface(marker_text, language).strip()
            if marker_norm == "of":
                candidate = _candidate(
                    text, "nominal.genitive_relation", "ud.nmod.case_of.genitive.v1",
                    "GENITIVE_UNSPECIFIED",
                    {"GENITIVE_HEAD": head_index, "GENITIVE_DEPENDENT": dependent_index},
                    spans, tokens, dependent_index, marker_indexes=markers,
                    semantic_status="UNSPECIFIED",
                )
                if candidate:
                    candidates.append(candidate)
            elif markers:
                candidate = _candidate(
                    text, "nominal.prepositional_modifier", "ud.nmod.case.prepositional.v1",
                    "PREPOSITIONAL_NOMINAL_MODIFIER",
                    {"HEAD": head_index, "MODIFIER": [*markers, dependent_index]},
                    spans, tokens, dependent_index, marker_indexes=markers,
                    semantic_status="UNSPECIFIED",
                )
                if candidate:
                    candidates.append(candidate)
            else:
                genitive = _candidate(
                    text, "nominal.genitive_relation", "ud.nmod.unmarked.genitive_candidate.v1",
                    "GENITIVE_UNSPECIFIED",
                    {"GENITIVE_HEAD": head_index, "GENITIVE_DEPENDENT": dependent_index},
                    spans, tokens, dependent_index, semantic_status="UNSPECIFIED",
                )
                nominal = _candidate(
                    text, "nominal.nominal_modifier_unspecified", "ud.nmod.unmarked.nominal_candidate.v1",
                    "NOMINAL_MODIFIER_UNSPECIFIED",
                    {"HEAD": head_index, "MODIFIER": dependent_index},
                    spans, tokens, dependent_index, semantic_status="UNSPECIFIED",
                )
                alternatives = [item for item in (genitive, nominal) if item]
                if alternatives:
                    candidates.append({
                        "status": "AMBIGUOUS",
                        "candidate_only": True,
                        "construction_id": None,
                        "alternatives": alternatives,
                        "derivation": {
                            "source": "UD_DEPENDENCY_GRAPH",
                            "dependency_relation": relation,
                            "head_token_id": head["id"],
                            "dependent_token_id": token["id"],
                            "reason": "UNMARKED_NMOD_DOES_NOT_IDENTIFY_POSSESSION_OR_GENITIVE_SEMANTICS",
                        },
                    })
            continue

        if relation == "advmod" and dep_pos == "ADV":
            temporal = EN_TEMPORAL if language == "en" else AR_TEMPORAL
            if normalize_surface(token["form"], language) in temporal:
                candidate = _candidate(
                    text, "modifier.temporal_adverbial", "ud.advmod.temporal_lexicon.v1",
                    "TEMPORAL_MODIFIER",
                    {"MODIFIED": head_index, "TIME": dependent_index},
                    spans, tokens, dependent_index,
                )
                if candidate:
                    candidates.append(candidate)

    status = "AMBIGUOUS" if any(item["status"] == "AMBIGUOUS" for item in candidates) else (
        "CANDIDATE" if candidates else "ABSTAIN"
    )
    return {
        "status": status,
        "candidate_only": True,
        "source_text": text,
        "candidates": candidates,
        "span_alignment_failures": len(failed),
        "unaligned_token_ids": [tokens[index]["id"] for index in failed],
        "source": "GOLD_UD_DEPENDENCY_TREEBANK",
    }


def run() -> dict:
    report = {
        "evaluation_type": "UD_GOLD_DEPENDENCY_TO_USG_NOMINAL_CANDIDATE_ADAPTER",
        "source_data_persisted": False,
        "runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "languages": {},
    }
    for language, spec in DATASETS.items():
        sentences = parse_dependency_conllu(download_dataset(language))
        totals = Counter()
        by_construction = Counter()
        by_status = Counter()
        alignment_failures = 0
        for sentence in sentences:
            adapted = adapt_sentence(sentence, language)
            totals["sentences"] += 1
            totals["tokens"] += len(sentence["tokens"])
            totals["candidates"] += len(adapted["candidates"])
            totals["span_alignment_failures"] += adapted["span_alignment_failures"]
            alignment_failures += adapted["span_alignment_failures"]
            by_status[adapted["status"]] += 1
            for candidate in adapted["candidates"]:
                if candidate["status"] == "AMBIGUOUS":
                    by_status["AMBIGUOUS_CANDIDATE"] += 1
                    for alternative in candidate["alternatives"]:
                        by_construction[alternative["construction_id"]] += 1
                else:
                    by_status["CANDIDATE"] += 1
                    by_construction[candidate["construction_id"]] += 1
        report["languages"][language] = {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "license": "CC BY-SA 3.0",
            "sentences": len(sentences),
            "totals": dict(totals),
            "by_status": dict(by_status),
            "by_construction": dict(by_construction),
            "span_alignment_success_rate": (
                1 - alignment_failures / totals["tokens"] if totals["tokens"] else None
            ),
        }
    report["limitations"] = [
        "The adapter consumes gold UD dependencies; this measures graph-to-USG transformation, not end-to-end parsing.",
        "UD dependency labels are syntactic evidence, not human-adjudicated USG semantic-role gold.",
        "Unmarked nmod relations remain ambiguous; no possession is inferred.",
        "Genitive semantics remain explicitly unspecified unless a more specific licensed construction exists.",
        "Temporal adverbs use a small versioned lexical list and abstain outside it.",
        "All outputs remain CANDIDATE or AMBIGUOUS; no construction is enabled.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
