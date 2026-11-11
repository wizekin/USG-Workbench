"""Evaluate the optional spaCy English pipeline on pinned English PUD.

The model is used only in an isolated benchmark; it is not a USG runtime
dependency or a source of semantic-role annotations.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import unicodedata

from spacy.tokens import Doc

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_external_pud_v0_4.morphology import parse_morph_conllu

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-4-spacy-english-pud.json"


def normalize_english(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def evaluate_predictions(sentences: list[dict], predictions: list[list[dict]]) -> dict:
    totals = Counter()
    by_upos = defaultdict(Counter)
    for sentence, predicted_tokens in zip(sentences, predictions):
        if len(sentence["tokens"]) != len(predicted_tokens):
            raise ValueError("spaCy output token count differs from pre-tokenized PUD input")
        for gold, predicted in zip(sentence["tokens"], predicted_tokens):
            gold_lemma = normalize_english(gold["lemma"])
            predicted_lemma = normalize_english(predicted.get("lemma", ""))
            gold_upos = gold["upos"].upper()
            predicted_upos = str(predicted.get("upos", "")).upper()
            lemma_hit = bool(predicted_lemma) and predicted_lemma == gold_lemma
            pos_hit = predicted_upos == gold_upos
            joint_hit = lemma_hit and pos_hit
            totals["tokens"] += 1
            totals["lemma_hits"] += int(lemma_hit)
            totals["upos_hits"] += int(pos_hit)
            totals["lemma_upos_hits"] += int(joint_hit)
            if gold_upos in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}:
                totals["content_tokens"] += 1
                totals["content_lemma_hits"] += int(lemma_hit)
                totals["content_upos_hits"] += int(pos_hit)
                totals["content_lemma_upos_hits"] += int(joint_hit)
            if gold_upos != "PUNCT":
                totals["nonpunct_tokens"] += 1
                totals["nonpunct_lemma_upos_hits"] += int(joint_hit)
            row = by_upos[gold_upos]
            row["tokens"] += 1
            row["lemma_hits"] += int(lemma_hit)
            row["upos_hits"] += int(pos_hit)
            row["lemma_upos_hits"] += int(joint_hit)

    def ratio(n, d):
        return n / d if d else None

    totals_out = dict(totals)
    totals_out.update({
        "lemma_accuracy": ratio(totals["lemma_hits"], totals["tokens"]),
        "upos_accuracy": ratio(totals["upos_hits"], totals["tokens"]),
        "lemma_upos_joint_accuracy": ratio(totals["lemma_upos_hits"], totals["tokens"]),
        "content_lemma_accuracy": ratio(totals["content_lemma_hits"], totals["content_tokens"]),
        "content_upos_accuracy": ratio(totals["content_upos_hits"], totals["content_tokens"]),
        "content_lemma_upos_joint_accuracy": ratio(
            totals["content_lemma_upos_hits"], totals["content_tokens"]),
        "nonpunct_lemma_upos_joint_accuracy": ratio(
            totals["nonpunct_lemma_upos_hits"], totals["nonpunct_tokens"]),
    })
    return {
        "totals": totals_out,
        "by_upos": {
            upos: {
                **dict(values),
                "lemma_accuracy": ratio(values["lemma_hits"], values["tokens"]),
                "upos_accuracy": ratio(values["upos_hits"], values["tokens"]),
                "lemma_upos_joint_accuracy": ratio(values["lemma_upos_hits"], values["tokens"]),
            }
            for upos, values in sorted(by_upos.items())
        },
    }


def run() -> dict:
    import spacy

    spec = DATASETS["en"]
    sentences = parse_morph_conllu(download_dataset("en"))
    if len(sentences) != spec["sentences"]:
        raise ValueError(
            f"English PUD expected {spec['sentences']} sentences, got {len(sentences)}"
        )
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    docs = [
        Doc(nlp.vocab, words=[token["form"] for token in sentence["tokens"]])
        for sentence in sentences
    ]
    predictions = []
    for doc in nlp.pipe(docs, batch_size=128):
        predictions.append([
            {"lemma": token.lemma_, "upos": token.pos_}
            for token in doc
        ])
    report = {
        "evaluation_type": "EXTERNAL_SPACY_ENGLISH_PUD_LEMMA_UPOS_EVALUATION",
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
        "source_data_persisted": False,
        "model_bundled": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "results": evaluate_predictions(sentences, predictions),
        "limitations": [
            "The pretrained spaCy model is evaluated as-is; no PUD fine-tuning is performed.",
            "The model's published training sources include OntoNotes 5; training-data overlap with PUD is not claimed to be impossible.",
            "The model returns one lemma and UPOS per token, so candidate ambiguity is not represented.",
            "This is English-only and does not evaluate USG semantic roles or constructions.",
            "A model score on PUD does not establish broad-domain or conversational English performance.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
