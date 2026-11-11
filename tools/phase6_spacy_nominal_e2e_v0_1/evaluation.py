"""End-to-end English spaCy parse -> UD-normalized graph -> USG candidates.

Gold PUD dependencies are used only as a structural reference. The model is
not fine-tuned on PUD and the candidate adapter remains candidate-only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

import spacy
from spacy.tokens import Doc

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_ud_nominal_candidate_v0_1.adapter import (
    adapt_sentence, parse_ud_conllu,
)
from tools.phase6_external_pud_v0_8.spacy_dependencies import (
    convert_heads_to_ud_conventions,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-6-spacy-nominal-e2e.json"


def spacy_parse_to_ud_sentence(forms: list[str], lemmas: list[str], upos: list[str],
                               heads: list[int], deprels: list[str], text: str) -> dict:
    converted_heads = convert_heads_to_ud_conventions(heads, deprels)
    tokens = []
    for index, (form, lemma, tag, relation) in enumerate(zip(forms, lemmas, upos, deprels)):
        relation = relation.lower()
        if relation in {"prep", "agent"}:
            ud_relation = "case"
        elif relation in {"pobj", "pcomp"}:
            governor = converted_heads[index]
            ud_relation = "nmod" if upos[governor] in {"NOUN", "PROPN"} else "obl"
        elif relation == "poss":
            ud_relation = "nmod:poss"
        elif relation == "dobj":
            ud_relation = "obj"
        elif relation == "nsubjpass":
            ud_relation = "nsubj:pass"
        elif relation == "auxpass":
            ud_relation = "aux:pass"
        elif relation == "npadvmod" and tag == "ADV":
            ud_relation = "advmod"
        elif relation == "prt":
            ud_relation = "compound:prt"
        elif relation == "root":
            ud_relation = "root"
        else:
            ud_relation = relation
        tokens.append({
            "id": index + 1,
            "form": form,
            "lemma": lemma,
            "upos": tag,
            "deprel": ud_relation,
            "gold_head_index": converted_heads[index],
            "is_root": converted_heads[index] == index,
        })
    return {"meta": {"text": text}, "tokens": tokens}


def _flatten_candidates(adapted: dict) -> list[dict]:
    flattened = []
    for candidate in adapted["candidates"]:
        if candidate["status"] == "AMBIGUOUS":
            flattened.extend(candidate["alternatives"])
        else:
            flattened.append(candidate)
    return flattened


def _signature(candidate: dict, sentence_index: int) -> tuple:
    derivation = candidate["derivation"]
    roles = tuple(sorted(
        (role, span["start"], span["end"])
        for role, span in candidate["role_spans"].items()
    ))
    markers = tuple(sorted(
        (span["start"], span["end"])
        for span in candidate["grammatical_markers"]
    ))
    return (
        sentence_index,
        candidate["construction_id"],
        derivation["head_token_id"],
        derivation["dependent_token_id"],
        roles,
        markers,
    )


def _structural_signature(candidate: dict, sentence_index: int) -> tuple:
    derivation = candidate["derivation"]
    return (
        sentence_index,
        candidate["construction_id"],
        derivation["head_token_id"],
        derivation["dependent_token_id"],
    )


def _prf(predicted: set, gold: set) -> dict:
    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = true_positive / len(predicted) if predicted else None
    recall = true_positive / len(gold) if gold else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def evaluate_candidate_sets(predicted: list[dict], gold: list[dict]) -> dict:
    if len(predicted) != len(gold):
        raise ValueError("predicted and gold sentence counts differ")
    predicted_full, gold_full = set(), set()
    predicted_structural, gold_structural = set(), set()
    pred_full_by_struct = defaultdict(set)
    gold_full_by_struct = defaultdict(set)
    for sentence_index, (pred_sentence, gold_sentence) in enumerate(zip(predicted, gold)):
        for item in _flatten_candidates(pred_sentence):
            full = _signature(item, sentence_index)
            structural = _structural_signature(item, sentence_index)
            predicted_full.add(full)
            predicted_structural.add(structural)
            pred_full_by_struct[structural].add(full)
        for item in _flatten_candidates(gold_sentence):
            full = _signature(item, sentence_index)
            structural = _structural_signature(item, sentence_index)
            gold_full.add(full)
            gold_structural.add(structural)
            gold_full_by_struct[structural].add(full)

    structural = _prf(predicted_structural, gold_structural)
    exact = _prf(predicted_full, gold_full)
    common_structural = predicted_structural & gold_structural
    span_exact_edges = sum(
        1 for edge in common_structural
        if pred_full_by_struct[edge] & gold_full_by_struct[edge]
    )

    by_construction = {}
    all_constructions = sorted({item[1] for item in predicted_full | gold_full})
    for construction in all_constructions:
        pred = {item for item in predicted_full if item[1] == construction}
        expected = {item for item in gold_full if item[1] == construction}
        by_construction[construction] = _prf(pred, expected)

    return {
        "predicted_candidate_count": len(predicted_full),
        "gold_candidate_count": len(gold_full),
        "structural_edge_metrics_ignoring_spans": structural,
        "exact_candidate_and_span_metrics": exact,
        "exact_span_rate_given_structural_match": (
            span_exact_edges / len(common_structural) if common_structural else None
        ),
        "by_construction": by_construction,
    }

def run() -> dict:
    spec = DATASETS["en"]
    sentences = parse_ud_conllu(download_dataset("en"))
    if len(sentences) != spec["sentences"]:
        raise ValueError(f"expected {spec['sentences']} English PUD sentences, got {len(sentences)}")
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    docs = [
        Doc(nlp.vocab, words=[token["form"] for token in sentence["tokens"]])
        for sentence in sentences
    ]

    predicted_adapted = []
    gold_adapted = []
    predicted_sentence_status = Counter()
    predicted_alignment_failures = 0
    for sentence, doc in zip(sentences, nlp.pipe(docs, batch_size=128)):
        predicted_graph = spacy_parse_to_ud_sentence(
            [token.text for token in doc],
            [token.lemma_ for token in doc],
            [token.pos_ for token in doc],
            [token.head.i for token in doc],
            [token.dep_ for token in doc],
            sentence.get("meta", {}).get("text", ""),
        )
        predicted = adapt_sentence(predicted_graph, "en")
        gold = adapt_sentence(sentence, "en")
        predicted_adapted.append(predicted)
        gold_adapted.append(gold)
        predicted_sentence_status[predicted["status"]] += 1
        predicted_alignment_failures += predicted["span_alignment_failures"]

    metrics = evaluate_candidate_sets(predicted_adapted, gold_adapted)
    report = {
        "evaluation_type": "SPACY_TO_USG_NOMINAL_CANDIDATE_END_TO_END_ENGLISH_PUD",
        "spacy_version": spacy.__version__,
        "model": "en_core_web_sm==3.8.0",
        "model_license": "MIT",
        "source": {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "license": "CC BY-SA 3.0",
            "sentences": len(sentences),
        },
        "tokenization": "PUD_GOLD_PRETOKENIZED_WORDS_PRESERVED",
        "gold_reference": "UD_PUD_GOLD_DEPENDENCY_GRAPH_PROJECTED_THROUGH_SAME_USG_ADAPTER",
        "predicted_input": "PRETRAINED_SPACY_DEPENDENCIES_WITH_PARTIAL_UD_HEAD_CONVERSION",
        "predicted_sentence_status": dict(predicted_sentence_status),
        "predicted_span_alignment_failures": predicted_alignment_failures,
        "metrics": metrics,
        "source_data_persisted": False,
        "model_bundled": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "limitations": [
            "The reference structures are UD syntax projected into USG candidate types, not human-adjudicated semantic-role gold.",
            "The spaCy-to-UD conversion is partial and covers common preposition/coordination conventions plus selected relation-label mappings.",
            "The pretrained model is evaluated without PUD fine-tuning; training-data overlap with PUD is not claimed to be impossible.",
            "The evaluation measures parser-plus-adapter structural extraction, not semantic correctness or broad-domain generalization.",
            "All predicted outputs remain candidate-only; ambiguous unmarked nmod alternatives are preserved.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
