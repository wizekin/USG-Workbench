"""Graph-first automatic Phase 6 acceptance corpus generator.

The oracle is assembled from frozen Phase 5 semantic cases before new text is
realized. It never calls the Phase 6 interpreter or reads Phase 6 candidate
outputs while generating references.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tools.phase5_interpretation_benchmark_v0_2_0.run import load_and_validate

ROOT = Path(__file__).resolve().parents[2]
SEED = 67111426
BENCHMARK_ID = "usg-phase6-automatic-acceptance/1.0.0"
LANGUAGES = ("en", "ar")
PROFILE_SPECS = {
    ("en", "step_6_7_coordination"): ("6.7", "coordination"),
    ("ar", "step_6_7_coordination"): ("6.7", "coordination"),
    ("en", "step_6_8_embedded_clauses"): ("6.8", "embedded_clauses"),
    ("ar", "step_6_8_embedded_clauses"): ("6.8", "embedded_clauses"),
    ("en", "step_6_9_voice_speech_act"): ("6.9", "voice_speech_act"),
    ("ar", "step_6_9_voice_speech_act"): ("6.9", "voice_speech_act"),
    ("en", "step_6_10_operator_scope"): ("6.10", "operator_scope"),
    ("ar", "step_6_10_operator_scope"): ("6.10", "operator_scope"),
    ("en", "step_6_11_discourse_reference"): ("6.11", "discourse_reference"),
    ("ar", "step_6_11_discourse_reference"): ("6.11", "discourse_reference"),
}

EN_BASE = {"writes": "write", "reads": "read", "builds": "build", "tests": "test"}
EN_PARTICIPLE = {"writes": "written", "reads": "read", "builds": "built", "tests": "tested"}
AR_PRESENT = {"كتب": "يكتب", "قرأ": "يقرأ", "فحص": "يفحص", "بنى": "يبني"}
AR_PASSIVE = {"كتب": "كُتِبَ", "قرأ": "قُرِئَ", "فحص": "فُحِصَ", "بنى": "بُنِيَ"}


def _trim_clause(text: str) -> str:
    return text.strip().rstrip(" .!?؟")


def _span(text: str, surface: str, start_at: int = 0) -> dict[str, Any]:
    start = text.find(surface, start_at)
    if start < 0:
        raise ValueError(f"reference surface {surface!r} is not present in {text!r}")
    return {"start": start, "end": start + len(surface), "surface": surface}


def _seed_rows() -> dict[str, list[dict[str, Any]]]:
    corpus = load_and_validate()
    rows = {
        lang: [
            case for case in corpus["cases"]
            if case["language"] == lang and case["gold_class"] == "POSITIVE"
        ]
        for lang in LANGUAGES
    }
    for lang, items in rows.items():
        if len(items) < 20:
            raise ValueError(f"Phase 5 frozen corpus needs 20 positive seed clauses for {lang}")
    return rows


def _role_spans(text: str, seed: dict[str, Any], offset: int = 0) -> list[dict[str, Any]]:
    values = []
    for role, surface in sorted(seed["expected_roles"].items()):
        local = _span(text, surface)
        values.append({
            "role": role, "surface": surface,
            "start": local["start"] + offset,
            "end": local["end"] + offset,
            "clause_id": None,
        })
    return values


def _case(case_id: str, lang: str, step: str, profile: str, gold_class: str,
          text: str, reference_graph: dict[str, Any], expected: dict[str, Any],
          *, source_seed_ids: list[str]) -> dict[str, Any]:
    spans = []
    for node in reference_graph.get("nodes", []):
        span = node.get("source_span")
        if span:
            spans.append({"node_id": node["id"], **span})
        for item in node.get("source_spans", []):
            spans.append({"node_id": node["id"], **item})
    return {
        "id": case_id,
        "language": lang,
        "step": step,
        "profile": profile,
        "gold_class": gold_class,
        "text": text,
        "reference_graph": reference_graph,
        "expected": expected,
        "expected_node_spans": spans,
        "source_seed_case_ids": source_seed_ids,
        "generator": {
            "id": "usg.phase6.graph-first-acceptance/1.0.0",
            "seed": SEED,
            "reference_created_before_realization": True,
        },
    }


def _two_clause_case(lang: str, step: str, profile: str, kind: str,
                     clauses: list[dict[str, Any]], marker1: str,
                     marker2: str | None = None) -> dict[str, Any]:
    # Construct the oracle graph before realizing the sentence.
    graph: dict[str, Any] = {
        "nodes": [
            {"id": f"predicate-{i+1}", "kind": "EVENT",
             "semantic_roles": dict(c["expected_roles"])}
            for i, c in enumerate(clauses)
        ],
        "relations": [],
        "ambiguity": None,
    }
    relation = "AND" if step == "6.7" else "CAUSAL"
    graph["relations"].append({"type": relation, "source": "predicate-1", "target": "predicate-2"})
    if marker2:
        graph["relations"].append({"type": "OR" if step == "6.7" else "TEMPORAL",
                                   "source": "predicate-2", "target": "predicate-3"})
        graph["ambiguity"] = "MULTIPLE_COORDINATION_OR_ATTACHMENT_READINGS"
    left = _trim_clause(clauses[0]["text"])
    middle = _trim_clause(clauses[1]["text"])
    right = _trim_clause(clauses[2]["text"]) if marker2 and len(clauses) > 2 else None
    if lang == "en":
        text = f"{left} {marker1} {middle}"
        if marker2 and right:
            text += f" {marker2} {right}"
    else:
        text = f"{left} {marker1} {middle}"
        if marker2 and right:
            text += f" {marker2} {right}"
    offsets = [0, len(left) + len(marker1) + 2]
    if marker2 and right:
        offsets.append(offsets[1] + len(middle) + len(marker2) + 2)
    for index, clause in enumerate(clauses[:len(offsets)]):
        role_spans = _role_spans(text[offsets[index]:], clause, 0)
        for item in role_spans:
            item["start"] += offsets[index]
            item["end"] += offsets[index]
            item["clause_id"] = f"clause-{index+1}"
            graph["nodes"][index]["source_spans"] = graph["nodes"][index].get("source_spans", []) + [item]
    marker_start = len(left) + 1
    expected = {
        "required_relations": [relation] + (["OR" if step == "6.7" else "TEMPORAL"] if marker2 else []),
        "required_features": ["COORDINATION" if step == "6.7" else "SUBORDINATE_CLAUSE"],
        "required_markers": [
            {"surface": marker1, "start": marker_start, "end": marker_start + len(marker1)}
        ],
        "required_role_spans": [
            span for node in graph["nodes"] for span in node.get("source_spans", [])
        ],
        "ambiguity_alternatives_required": bool(marker2),
    }
    return _case(
        f"{lang}.{profile}.{kind}.{clauses[0]['id']}",
        lang, step, profile, kind, text, graph, expected,
        source_seed_ids=[c["id"] for c in clauses],
    )


def _generate_coordination(lang: str, seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    conjunction = "and" if lang == "en" else "و"
    for i in range(20):
        a, b = seeds[i], seeds[(i + 7) % 20]
        out.append(_two_clause_case(
            lang, "6.7", "coordination", "POSITIVE", [a, b], conjunction
        ))
    for i in range(20):
        seed = seeds[i]
        text = _trim_clause(seed["text"])
        graph = {"nodes": [], "relations": [], "ambiguity": None}
        out.append(_case(
            f"{lang}.coordination.NEGATIVE.{i+1:02d}", lang, "6.7", "coordination",
            "NEGATIVE", text, graph,
            {"forbidden_relations": ["AND", "OR", "CONTRAST"],
             "forbidden_features": ["COORDINATION"]},
            source_seed_ids=[seed["id"]],
        ))
    disjunction = "or" if lang == "en" else "أو"
    for i in range(10):
        a, b, c = seeds[i], seeds[(i + 6) % 20], seeds[(i + 13) % 20]
        out.append(_two_clause_case(
            lang, "6.7", "coordination", "AMBIGUOUS", [a, b, c],
            conjunction, disjunction,
        ))
    return out


def _generate_subordination(lang: str, seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    causal = "because" if lang == "en" else "لأن"
    temporal = "when" if lang == "en" else "عندما"
    for i in range(20):
        a, b = seeds[i], seeds[(i + 9) % 20]
        out.append(_two_clause_case(
            lang, "6.8", "embedded_clauses", "POSITIVE", [a, b], causal
        ))
    for i in range(20):
        a, b = seeds[i], seeds[(i + 9) % 20]
        text = _trim_clause(a["text"]) + ". " + _trim_clause(b["text"])
        out.append(_case(
            f"{lang}.embedded_clauses.NEGATIVE.{i+1:02d}", lang, "6.8",
            "embedded_clauses", "NEGATIVE", text,
            {"nodes": [], "relations": [], "ambiguity": None},
            {"forbidden_relations": ["COMPLEMENT", "RELATIVE", "TEMPORAL", "CAUSAL", "CONDITIONAL"],
             "forbidden_features": ["EMBEDDED_CLAUSE", "SUBORDINATE_CLAUSE"]},
            source_seed_ids=[a["id"], b["id"]],
        ))
    for i in range(10):
        a, b, c = seeds[i], seeds[(i + 5) % 20], seeds[(i + 12) % 20]
        out.append(_two_clause_case(
            lang, "6.8", "embedded_clauses", "AMBIGUOUS", [a, b, c],
            causal, temporal,
        ))
    return out


def _generate_voice(lang: str, seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for i in range(20):
        seed = seeds[i]
        roles = seed["expected_roles"]
        if lang == "en":
            action = roles["ACTION"]
            participle = EN_PARTICIPLE.get(action)
            if not participle:
                raise ValueError(f"no passive realization for English predicate {action!r}")
            text = f"Was the {roles['PATIENT']} {participle}?"
        else:
            action = roles["ACTION"]
            passive = AR_PASSIVE.get(action)
            if not passive:
                raise ValueError(f"no passive realization for Arabic predicate {action!r}")
            text = f"هل {passive} {roles['PATIENT']}؟"
        graph = {
            "nodes": [{"id": "patient", "kind": "ENTITY", "role": "PATIENT",
                       "semantic_value": roles["PATIENT"]}],
            "relations": [],
            "voice": "PASSIVE", "speech_act": "QUESTION", "ambiguity": None,
        }
        out.append(_case(
            f"{lang}.voice_speech_act.POSITIVE.{i+1:02d}", lang, "6.9",
            "voice_speech_act", "POSITIVE", text, graph,
            {"required_voice": "PASSIVE", "required_speech_act": "QUESTION",
             "required_features": ["VOICE", "SPEECH_ACT"]},
            source_seed_ids=[seed["id"]],
        ))
    for i in range(20):
        seed = seeds[i]
        text = _trim_clause(seed["text"])
        out.append(_case(
            f"{lang}.voice_speech_act.NEGATIVE.{i+1:02d}", lang, "6.9",
            "voice_speech_act", "NEGATIVE", text,
            {"nodes": [], "relations": [], "voice": "ACTIVE",
             "speech_act": "ASSERTION", "ambiguity": None},
            {"forbidden_voice": "PASSIVE", "forbidden_speech_act": "QUESTION",
             "forbidden_features": ["VOICE"]},
            source_seed_ids=[seed["id"]],
        ))
    for i in range(10):
        seed = seeds[i]
        roles = seed["expected_roles"]
        if lang == "en":
            action = EN_PARTICIPLE[roles["ACTION"]]
            text = f"The {roles['PATIENT']} was {action}."
        else:
            # Unvowelled past-tense forms can leave active/passive morphology
            # underdetermined in ordinary MSA orthography.
            text = f"{roles['ACTION']} {roles['AGENT']} {roles['PATIENT']}"
        graph = {
            "nodes": [{"id": "voice-1", "kind": "EVENT_OR_PROPERTY"}],
            "relations": [],
            "voice_alternatives": ["PASSIVE", "ADJECTIVAL_OR_UNSPECIFIED"],
            "ambiguity": "VOICE_OR_PARTICIPIAL_STATUS_UNDERSPECIFIED",
        }
        out.append(_case(
            f"{lang}.voice_speech_act.AMBIGUOUS.{i+1:02d}", lang, "6.9",
            "voice_speech_act", "AMBIGUOUS", text, graph,
            {"ambiguity_alternatives_required": True, "forbidden_unique_voice": True},
            source_seed_ids=[seed["id"]],
        ))
    return out


def _generate_operators(lang: str, seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for i in range(20):
        seed = seeds[i]
        roles = seed["expected_roles"]
        if lang == "en":
            predicate = EN_BASE[roles["ACTION"]]
            text = f"{roles['AGENT']} may not {predicate}"
        else:
            predicate = AR_PRESENT[roles["ACTION"]]
            text = f"قد لا {predicate} {roles['AGENT']}"
        graph = {
            "nodes": [{"id": "event", "kind": "EVENT"}],
            "operators": [
                {"type": "MODALITY", "target": "event"},
                {"type": "NEGATION", "target": "event"},
            ],
            "ambiguity": None,
        }
        out.append(_case(
            f"{lang}.operator_scope.POSITIVE.{i+1:02d}", lang, "6.10",
            "operator_scope", "POSITIVE", text, graph,
            {"required_operator_types": ["MODALITY", "NEGATION"],
             "required_operator_target": True,
             "required_scope": True},
            source_seed_ids=[seed["id"]],
        ))
    for i in range(20):
        seed = seeds[i]
        text = _trim_clause(seed["text"])
        out.append(_case(
            f"{lang}.operator_scope.NEGATIVE.{i+1:02d}", lang, "6.10",
            "operator_scope", "NEGATIVE", text,
            {"nodes": [], "operators": [], "ambiguity": None},
            {"forbidden_operator_types": ["MODALITY", "NEGATION", "QUANTIFIER", "CONDITION"]},
            source_seed_ids=[seed["id"]],
        ))
    for i in range(10):
        seed = seeds[i]
        roles = seed["expected_roles"]
        if lang == "en":
            predicate = EN_BASE[roles["ACTION"]]
            text = f"{roles['AGENT']} must not {predicate}"
        else:
            predicate = AR_PRESENT[roles["ACTION"]]
            text = f"ربما لا {predicate} {roles['AGENT']}"
        graph = {
            "nodes": [{"id": "event", "kind": "EVENT"}],
            "operators": [
                {"type": "MODALITY", "target": "event", "scope": "UNRESOLVED"},
                {"type": "NEGATION", "target": "event", "scope": "UNRESOLVED"},
            ],
            "scope_alternatives": ["MODALITY_OVER_NEGATION", "NEGATION_OVER_MODALITY"],
            "ambiguity": "NESTED_OPERATOR_SCOPE_AMBIGUITY",
        }
        out.append(_case(
            f"{lang}.operator_scope.AMBIGUOUS.{i+1:02d}", lang, "6.10",
            "operator_scope", "AMBIGUOUS", text, graph,
            {"required_operator_types": ["MODALITY", "NEGATION"],
             "ambiguity_alternatives_required": True, "forbidden_unique_scope": True},
            source_seed_ids=[seed["id"]],
        ))
    return out


def _generate_discourse(lang: str, seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    en_pronoun = {"Ada": "She", "Mira": "She", "Lina": "She", "Noah": "He", "Omar": "He"}
    for i in range(20):
        seed = seeds[i]
        agent = seed["expected_roles"]["AGENT"]
        if lang == "en":
            pronoun = en_pronoun.get(agent, "They")
            text = f"{_trim_clause(seed['text'])}. {pronoun} reads."
        else:
            text = f"{_trim_clause(seed['text'])}. هو قرأ."
        graph = {
            "mentions": [
                {"id": "antecedent", "kind": "ENTITY_MENTION"},
                {"id": "pronoun", "kind": "PRONOMINAL_MENTION"},
            ],
            "references": [{"mention": "pronoun", "antecedent_candidates": ["antecedent"],
                            "expected_resolution": "antecedent"}],
            "ambiguity": None,
        }
        out.append(_case(
            f"{lang}.discourse_reference.POSITIVE.{i+1:02d}", lang, "6.11",
            "discourse_reference", "POSITIVE", text, graph,
            {"minimum_references": 1, "minimum_antecedent_candidates": 1,
             "require_unresolved_candidate": True},
            source_seed_ids=[seed["id"]],
        ))
    for i in range(20):
        seed = seeds[i]
        text = _trim_clause(seed["text"])
        out.append(_case(
            f"{lang}.discourse_reference.NEGATIVE.{i+1:02d}", lang, "6.11",
            "discourse_reference", "NEGATIVE", text,
            {"mentions": [], "references": [], "ambiguity": None},
            {"forbidden_references": True},
            source_seed_ids=[seed["id"]],
        ))
    for i in range(10):
        a, b = seeds[i], seeds[(i + 8) % 20]
        first, second = a["expected_roles"]["AGENT"], b["expected_roles"]["AGENT"]
        if lang == "en":
            text = f"{_trim_clause(a['text'])}. {_trim_clause(b['text'])}. They read."
        else:
            text = f"{_trim_clause(a['text'])}. {_trim_clause(b['text'])}. هما قرأا."
        graph = {
            "mentions": [
                {"id": "antecedent-1", "kind": "ENTITY_MENTION"},
                {"id": "antecedent-2", "kind": "ENTITY_MENTION"},
                {"id": "pronoun", "kind": "PRONOMINAL_MENTION"},
            ],
            "references": [{"mention": "pronoun",
                            "antecedent_candidates": ["antecedent-1", "antecedent-2"],
                            "expected_resolution": None}],
            "ambiguity": "MULTIPLE_POSSIBLE_ANTECEDENTS",
        }
        out.append(_case(
            f"{lang}.discourse_reference.AMBIGUOUS.{i+1:02d}", lang, "6.11",
            "discourse_reference", "AMBIGUOUS", text, graph,
            {"minimum_references": 1, "minimum_antecedent_candidates": 2,
             "forbidden_unique_resolution": True},
            source_seed_ids=[a["id"], b["id"]],
        ))
    return out


def build() -> dict[str, Any]:
    seeds = _seed_rows()
    cases: list[dict[str, Any]] = []
    for lang in LANGUAGES:
        cases.extend(_generate_coordination(lang, seeds[lang]))
        cases.extend(_generate_subordination(lang, seeds[lang]))
        cases.extend(_generate_voice(lang, seeds[lang]))
        cases.extend(_generate_operators(lang, seeds[lang]))
        cases.extend(_generate_discourse(lang, seeds[lang]))
    corpus = {
        "benchmark_id": BENCHMARK_ID,
        "version": "1.0.0",
        "contract": "USG-INTERPRET/0.3.0",
        "license": "CC0-1.0",
        "scope": "AUTOMATIC_GRAPH_FIRST_SYNTHETIC_ACCEPTANCE_FOR_PHASE6_STEPS_6_7_TO_6_14",
        "languages": ["en", "ar"],
        "generation": {
            "generator": "usg.phase6.graph-first-acceptance/1.0.0",
            "seed": SEED,
            "reference_graph_created_before_text_realization": True,
            "source_seed_corpus": "usg-interpretation-v0.2.1-balanced-foundation",
            "uses_human_annotations_for_new_cases": False,
            "uses_model_labels": False,
            "uses_phase6_candidate_predictions": False,
            "reads_phase6_development_fixtures": False,
            "uses_external_corpus": False,
            "uses_candidate_lexicon": False,
            "note": "The frozen Phase 5 accepted corpus supplies lexical/role seeds; each new multi-clause or transformed case receives a newly composed reference graph before realization. This is controlled synthetic evidence, not human gold or naturalistic accuracy.",
        },
        "construction_inventory": {
            f"{lang}/{profile}": {"positive": 20, "negative": 20, "ambiguous": 10}
            for lang, profile in PROFILE_SPECS
        },
        "cases": cases,
        "integration_checks": [
            {"step": "6.12", "id": "canonical-preservation-and-semantic-projection-boundary"},
            {"step": "6.13", "id": "api-sqlite-persistence-deterministic-replay"},
            {"step": "6.14", "id": "unified-per-profile-exit-evaluator"},
        ],
    }
    validate(corpus)
    return corpus


def validate(corpus: dict[str, Any]) -> None:
    if corpus.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError("unexpected Phase 6 acceptance benchmark ID")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or len(cases) != 500:
        raise ValueError("Phase 6 acceptance corpus must contain exactly 500 cases")
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate Phase 6 acceptance case ID")
    if corpus["generation"]["uses_human_annotations_for_new_cases"]:
        raise ValueError("new cases must not depend on human annotations")
    if corpus["generation"]["uses_model_labels"] or corpus["generation"]["uses_phase6_candidate_predictions"]:
        raise ValueError("reference generation must be independent of model/runtime predictions")
    actual: dict[str, dict[str, int]] = {}
    for case in cases:
        key = f"{case['language']}/{case['profile']}"
        actual.setdefault(key, {"positive": 0, "negative": 0, "ambiguous": 0})
        bucket = case["gold_class"].lower()
        if bucket not in actual[key]:
            raise ValueError(f"invalid gold class: {case['id']}")
        actual[key][bucket] += 1
        text = case["text"]
        if not isinstance(text, str) or not text:
            raise ValueError(f"empty source text: {case['id']}")
        for span in case.get("expected_node_spans", []):
            start, end = span.get("start"), span.get("end")
            if type(start) is not int or type(end) is not int or start < 0 or end <= start or end > len(text):
                raise ValueError(f"invalid expected span: {case['id']}")
            if text[start:end] != span.get("surface"):
                raise ValueError(f"source span mismatch: {case['id']}")
        for span in case.get("expected", {}).get("required_markers", []):
            if text[span["start"]:span["end"]] != span["surface"]:
                raise ValueError(f"marker span mismatch: {case['id']}")
        for span in case.get("expected", {}).get("required_role_spans", []):
            if (span["start"] < 0 or span["end"] <= span["start"]
                    or span["end"] > len(text)
                    or text[span["start"]:span["end"]] != span["surface"]):
                raise ValueError(f"role span mismatch: {case['id']}")
    if actual != corpus["construction_inventory"]:
        raise ValueError("construction inventory and case counts differ")
    for key, counts in actual.items():
        if counts != {"positive": 20, "negative": 20, "ambiguous": 10}:
            raise ValueError(f"profile {key} does not meet 20/20/10 minimums")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def corpus_sha256(corpus: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(corpus)).hexdigest()



def main() -> int:
    corpus = build()
    output = ROOT / "benchmarks/phase6-automatic-acceptance-v1.0/corpus.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(corpus, ensure_ascii=False, sort_keys=True, indent=2) + "\\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "benchmark_id": BENCHMARK_ID,
        "case_count": len(corpus["cases"]),
        "profile_count": len(corpus["construction_inventory"]),
        "corpus_sha256": corpus_sha256(corpus),
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
