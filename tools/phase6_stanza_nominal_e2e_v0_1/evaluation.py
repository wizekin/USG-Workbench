"""Evaluate a research-only Stanza Arabic parser on Arabic PUD.

The PADT-trained parser is used only as an isolated diagnostic. Its source
training corpus has non-commercial licensing; this module is not a product
dependency and must not be bundled for commercial use without rights review.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_ud_nominal_candidate_v0_1.adapter import (
    adapt_sentence, parse_ud_conllu,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-6-stanza-arabic-nominal-e2e.json"
MODEL_DIR = ROOT / ".stanza-resources"
RESOURCES_VERSION = "1.15.0"
PACKAGES = {
    "tokenize": "padt_nocharlm",
    "pos": "padt_nocharlm",
    "depparse": "padt_nocharlm",
}


def stanza_sentence_to_ud(stanza_sentence, text: str) -> dict:
    tokens = []
    for index, word in enumerate(stanza_sentence.words):
        head = int(word.head or 0)
        head_index = index if head == 0 else head - 1
        tokens.append({
            "id": index + 1,
            "form": word.text,
            "lemma": word.lemma or word.text,
            "upos": word.upos or "X",
            "deprel": word.deprel or "dep",
            "gold_head_index": head_index,
            "is_root": head == 0,
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
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    precision = tp / len(predicted) if predicted else None
    recall = tp / len(gold) if gold else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "true_positive": tp, "false_positive": fp, "false_negative": fn,
        "precision": precision, "recall": recall, "f1": f1,
    }


def evaluate_candidate_sets(predicted: list[dict], gold: list[dict]) -> dict:
    if len(predicted) != len(gold):
        raise ValueError("predicted and gold sentence counts differ")
    predicted_full, gold_full = set(), set()
    predicted_structural, gold_structural = set(), set()
    pred_full_by_struct, gold_full_by_struct = defaultdict(set), defaultdict(set)
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
    common = predicted_structural & gold_structural
    span_exact = sum(
        bool(pred_full_by_struct[edge] & gold_full_by_struct[edge])
        for edge in common
    )
    return {
        "predicted_candidate_hypotheses": len(predicted_full),
        "gold_candidate_hypotheses": len(gold_full),
        "structural_edge_metrics": structural,
        "exact_candidate_and_span_metrics": exact,
        "exact_span_rate_given_structural_match": span_exact / len(common) if common else None,
    }


def evaluate_parser_outputs(predicted_sentences: list[dict], gold_sentences: list[dict]) -> dict:
    totals = Counter()
    by_upos = defaultdict(Counter)
    token_count_mismatches = 0
    for predicted, gold in zip(predicted_sentences, gold_sentences):
        if len(predicted["tokens"]) != len(gold["tokens"]):
            token_count_mismatches += 1
            continue
        for pred_token, gold_token in zip(predicted["tokens"], gold["tokens"]):
            totals["tokens"] += 1
            pos_hit = pred_token["upos"] == gold_token["upos"]
            head_hit = pred_token["gold_head_index"] == gold_token["gold_head_index"]
            totals["upos_hits"] += int(pos_hit)
            totals["uas_hits"] += int(head_hit)
            if gold_token["is_root"]:
                totals["root_tokens"] += 1
                totals["root_hits"] += int(head_hit)
            if gold_token["upos"] in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}:
                totals["content_tokens"] += 1
                totals["content_upos_hits"] += int(pos_hit)
                totals["content_uas_hits"] += int(head_hit)
            by_upos[gold_token["upos"]]["tokens"] += 1
            by_upos[gold_token["upos"]]["upos_hits"] += int(pos_hit)
            by_upos[gold_token["upos"]]["uas_hits"] += int(head_hit)

    def ratio(n, d):
        return n / d if d else None

    result = dict(totals)
    result.update({
        "upos_accuracy": ratio(totals["upos_hits"], totals["tokens"]),
        "uas": ratio(totals["uas_hits"], totals["tokens"]),
        "content_upos_accuracy": ratio(totals["content_upos_hits"], totals["content_tokens"]),
        "content_uas": ratio(totals["content_uas_hits"], totals["content_tokens"]),
        "root_attachment_accuracy": ratio(totals["root_hits"], totals["root_tokens"]),
        "token_count_mismatched_sentences": token_count_mismatches,
    })
    return {
        "totals": result,
        "by_upos": {
            upos: {
                **dict(values),
                "upos_accuracy": ratio(values["upos_hits"], values["tokens"]),
                "uas": ratio(values["uas_hits"], values["tokens"]),
            }
            for upos, values in sorted(by_upos.items())
        },
    }


def run() -> dict:
    import stanza

    spec = DATASETS["ar"]
    gold_sentences = parse_ud_conllu(download_dataset("ar"))
    if len(gold_sentences) != spec["sentences"]:
        raise ValueError(f"Arabic PUD expected {spec['sentences']} sentences, got {len(gold_sentences)}")

    stanza.download(
        lang="ar",
        model_dir=str(MODEL_DIR),
        package=PACKAGES,
        processors="tokenize,pos,depparse",
        resources_version=RESOURCES_VERSION,
        verbose=False,
    )
    nlp = stanza.Pipeline(
        lang="ar",
        dir=str(MODEL_DIR),
        package=PACKAGES,
        processors="tokenize,pos,depparse",
        tokenize_pretokenized=True,
        use_gpu=False,
        resources_version=RESOURCES_VERSION,
        verbose=False,
    )
    pretokenized = [[token["form"] for token in sentence["tokens"]] for sentence in gold_sentences]
    doc = nlp(pretokenized)
    if len(doc.sentences) != len(gold_sentences):
        raise ValueError("Stanza sentence count differs from pre-tokenized Arabic PUD input")

    predicted_graphs, predicted_adapted, gold_adapted = [], [], []
    predicted_status = Counter()
    predicted_alignment_failures = 0
    for index, (stanza_sentence, gold) in enumerate(zip(doc.sentences, gold_sentences)):
        predicted = stanza_sentence_to_ud(stanza_sentence, gold.get("meta", {}).get("text", ""))
        predicted_graphs.append(predicted)
        adapted = adapt_sentence(predicted, "ar")
        predicted_adapted.append(adapted)
        gold_adapted.append(adapt_sentence(gold, "ar"))
        predicted_status[adapted["status"]] += 1
        predicted_alignment_failures += adapted["span_alignment_failures"]

    parser_metrics = evaluate_parser_outputs(predicted_graphs, gold_sentences)
    candidate_metrics = evaluate_candidate_sets(predicted_adapted, gold_adapted)
    report = {
        "evaluation_type": "STANZA_ARABIC_PUD_PARSER_TO_USG_NOMINAL_CANDIDATES",
        "stanza_version": stanza.__version__,
        "model": "Arabic PADT no-charlm POS + dependency parser",
        "resources_version": RESOURCES_VERSION,
        "model_package_license": "Apache-2.0",
        "training_treebank": "UD_Arabic-PADT",
        "training_treebank_license": "CC BY-NC-SA 3.0",
        "commercial_use_status": "RESEARCH_ONLY_NOT_FOR_COMMERCIAL_INTEGRATION_WITHOUT_RIGHTS_CLEARANCE",
        "source": {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "license": "CC BY-SA 3.0",
            "sentences": len(gold_sentences),
        },
        "input_tokenization": "PUD_GOLD_PRETOKENIZED_WORDS",
        "parser_metrics": parser_metrics,
        "predicted_sentence_status": dict(predicted_status),
        "predicted_span_alignment_failures": predicted_alignment_failures,
        "nominal_candidate_metrics": candidate_metrics,
        "model_bundled": False,
        "source_data_persisted": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "limitations": [
            "The parser is trained on Arabic-PADT, not Arabic-PUD; no PUD fine-tuning is performed.",
            "The training treebank has a non-commercial license; this is a research diagnostic only.",
            "Gold PUD tokenization is supplied, so this does not evaluate raw-text tokenization or MWT segmentation.",
            "The candidate reference is a UD syntactic projection, not human-adjudicated USG semantic-role gold.",
            "All generated USG outputs remain candidate-only; unmarked nmod ambiguity is retained.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
