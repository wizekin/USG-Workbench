"""Deterministic HMM POS-tagging diagnostic on external UD PUD.

This is an isolated research baseline, not part of the USG runtime.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import math

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset, parse_conllu
from tools.phase6_external_pud_v0_2.crossval import CONTENT_UPOS, _fold_index, normalize

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-6-pud-contextual-pos.json"
START = "<START>"
ALPHA = 0.1


def train_hmm(sentences: list[dict], language: str, alpha: float = ALPHA) -> dict:
    word_tags = defaultdict(Counter)
    tag_counts = Counter()
    transitions = defaultdict(Counter)
    start_counts = Counter()
    tags = set()
    sentence_count = 0
    for sentence in sentences:
        previous = START
        sentence_count += 1
        for token in sentence["tokens"]:
            form = normalize(token["form"], language)
            tag = token["upos"]
            word_tags[form][tag] += 1
            tag_counts[tag] += 1
            transitions[previous][tag] += 1
            if previous == START:
                start_counts[tag] += 1
            tags.add(tag)
            previous = tag
    return {
        "word_tags": {k: dict(v) for k, v in word_tags.items()},
        "tag_counts": dict(tag_counts),
        "transitions": {k: dict(v) for k, v in transitions.items()},
        "start_counts": dict(start_counts),
        "tags": sorted(tags),
        "vocabulary_size": len(word_tags),
        "sentence_count": sentence_count,
        "alpha": alpha,
    }


def _transition_log(previous: str, tag: str, model: dict) -> float:
    alpha = model["alpha"]
    counts = model["transitions"].get(previous, {})
    denominator = sum(counts.values()) + alpha * len(model["tags"])
    return math.log((counts.get(tag, 0) + alpha) / denominator)


def _emission_log(form: str, tag: str, model: dict) -> float:
    alpha = model["alpha"]
    counts = model["word_tags"].get(form, {})
    denominator = model["tag_counts"][tag] + alpha * (model["vocabulary_size"] + 1)
    return math.log((counts.get(tag, 0) + alpha) / denominator)


def viterbi(forms: list[str], language: str, model: dict) -> list[str]:
    if not forms:
        return []
    tags = model["tags"]
    normalized = [normalize(form, language) for form in forms]
    scores = {}
    backpointers = []
    for tag in tags:
        start = _transition_log(START, tag, model)
        scores[tag] = start + _emission_log(normalized[0], tag, model)
    for form in normalized[1:]:
        next_scores, back = {}, {}
        for tag in tags:
            best_previous, best_score = None, float("-inf")
            emission = _emission_log(form, tag, model)
            for previous in tags:
                score = scores[previous] + _transition_log(previous, tag, model) + emission
                if score > best_score:
                    best_previous, best_score = previous, score
            next_scores[tag] = best_score
            back[tag] = best_previous
        scores = next_scores
        backpointers.append(back)
    current = max(tags, key=lambda tag: scores[tag])
    output = [current]
    for back in reversed(backpointers):
        current = back[current]
        output.append(current)
    output.reverse()
    return output


def _majority_tag(form: str, model: dict) -> str:
    counts = model["word_tags"].get(form)
    if counts:
        return min(counts, key=lambda tag: (-counts[tag], tag))
    totals = model["tag_counts"]
    return min(totals, key=lambda tag: (-totals[tag], tag))


def evaluate_fold(train: list[dict], test: list[dict], language: str) -> dict:
    model = train_hmm(train, language)
    totals = {
        "tokens": 0, "unigram_correct": 0, "hmm_correct": 0,
        "seen_tokens": 0, "oov_tokens": 0,
        "seen_hmm_correct": 0, "oov_hmm_correct": 0,
        "content_tokens": 0, "content_unigram_correct": 0,
        "content_hmm_correct": 0,
        "sentences": 0, "unigram_sentence_exact": 0, "hmm_sentence_exact": 0,
    }
    for sentence in test:
        tokens = sentence["tokens"]
        forms = [t["form"] for t in tokens]
        gold = [t["upos"] for t in tokens]
        norm = [normalize(x, language) for x in forms]
        unigram = [_majority_tag(x, model) for x in norm]
        predicted = viterbi(forms, language, model)
        totals["sentences"] += 1
        totals["unigram_sentence_exact"] += int(unigram == gold)
        totals["hmm_sentence_exact"] += int(predicted == gold)
        for form, expected, base, tag in zip(norm, gold, unigram, predicted):
            totals["tokens"] += 1
            totals["unigram_correct"] += int(base == expected)
            totals["hmm_correct"] += int(tag == expected)
            if form in model["word_tags"]:
                totals["seen_tokens"] += 1
                totals["seen_hmm_correct"] += int(tag == expected)
            else:
                totals["oov_tokens"] += 1
                totals["oov_hmm_correct"] += int(tag == expected)
            if expected in CONTENT_UPOS:
                totals["content_tokens"] += 1
                totals["content_unigram_correct"] += int(base == expected)
                totals["content_hmm_correct"] += int(tag == expected)
    return totals


def cross_validate(sentences: list[dict], language: str, folds: int = 10) -> dict:
    if folds < 2 or len(sentences) < folds:
        raise ValueError("at least two folds and one sentence per fold are required")
    fold_ids = [_fold_index(s, i, folds) for i, s in enumerate(sentences)]
    aggregate = Counter()
    fold_reports = []
    for fold in range(folds):
        train = [s for i, s in enumerate(sentences) if fold_ids[i] != fold]
        test = [s for i, s in enumerate(sentences) if fold_ids[i] == fold]
        result = evaluate_fold(train, test, language)
        aggregate.update(result)
        fold_reports.append({"fold": fold, "train_sentences": len(train),
                             "test_sentences": len(test), **result})

    def ratio(n, d):
        return n / d if d else None

    t = dict(aggregate)
    t.update({
        "unigram_accuracy": ratio(aggregate["unigram_correct"], aggregate["tokens"]),
        "hmm_accuracy": ratio(aggregate["hmm_correct"], aggregate["tokens"]),
        "hmm_accuracy_seen": ratio(aggregate["seen_hmm_correct"], aggregate["seen_tokens"]),
        "hmm_accuracy_oov": ratio(aggregate["oov_hmm_correct"], aggregate["oov_tokens"]),
        "unigram_content_accuracy": ratio(aggregate["content_unigram_correct"], aggregate["content_tokens"]),
        "hmm_content_accuracy": ratio(aggregate["content_hmm_correct"], aggregate["content_tokens"]),
        "unigram_sentence_exact_accuracy": ratio(aggregate["unigram_sentence_exact"], aggregate["sentences"]),
        "hmm_sentence_exact_accuracy": ratio(aggregate["hmm_sentence_exact"], aggregate["sentences"]),
    })
    return {"language": language, "fold_count": folds, "totals": t, "folds": fold_reports}


def run() -> dict:
    report = {
        "evaluation_type": "EXTERNAL_PUD_10_FOLD_HMM_POS_DIAGNOSTIC",
        "method": "DETERMINISTIC_FIRST_ORDER_HMM_WITH_ADD_ALPHA_SMOOTHING",
        "alpha": ALPHA,
        "license": "CC BY-SA 3.0",
        "source_data_persisted": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "datasets": {},
    }
    for language, spec in DATASETS.items():
        sentences = parse_conllu(download_dataset(language))
        if len(sentences) != spec["sentences"]:
            raise ValueError(f"{language}: expected {spec['sentences']} sentences, got {len(sentences)}")
        result = cross_validate(sentences, language, folds=10)
        result.update({
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "sentences": len(sentences),
        })
        report["datasets"][language] = result
    report["limitations"] = [
        "This HMM is a standalone diagnostic, not an implementation of USG lexical semantics.",
        "Training and testing use ten sentence-ID-hash folds from PUD; results are corpus-specific.",
        "Exact-form emissions do not provide productive morphology or unseen-word understanding.",
        "No syntactic dependency or semantic-role labels are predicted.",
        "No result in this experiment enables a USG construction.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
