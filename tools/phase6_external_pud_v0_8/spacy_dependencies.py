"""Evaluate spaCy English dependency-head predictions on pinned English PUD.

Only unlabeled attachment is scored because spaCy's ClearNLP-derived relation
labels are not identical to the UD relation inventory used by PUD.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json

from spacy.tokens import Doc

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-4-spacy-english-dependencies.json"
CONTENT_UPOS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}


def parse_dependency_conllu(payload: bytes) -> list[dict]:
    source = payload.decode("utf-8")
    sentences = []
    for block in source.strip().split("\n\n"):
        meta, tokens = {}, []
        for line in block.splitlines():
            if line.startswith("# "):
                key, sep, value = line[2:].partition(" = ")
                if sep:
                    meta[key] = value
                continue
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) != 10 or not cols[0].isdigit():
                continue
            if cols[3] == "_" or not cols[6].isdigit() or cols[7] == "_":
                continue
            tokens.append({
                "id": int(cols[0]),
                "form": cols[1],
                "lemma": cols[2],
                "upos": cols[3],
                "head_id": int(cols[6]),
                "deprel": cols[7],
            })
        if not tokens:
            continue
        id_to_index = {token["id"]: index for index, token in enumerate(tokens)}
        for index, token in enumerate(tokens):
            head_id = token.pop("head_id")
            token["is_root"] = head_id == 0
            token["gold_head_index"] = index if head_id == 0 else id_to_index.get(head_id)
        sentences.append({"meta": meta, "tokens": tokens})
    return sentences


def evaluate_predictions(sentences: list[dict], predictions: list[list[dict]]) -> dict:
    totals = Counter()
    by_upos = defaultdict(Counter)
    by_deprel = defaultdict(Counter)
    for sentence, predicted_tokens in zip(sentences, predictions):
        if len(sentence["tokens"]) != len(predicted_tokens):
            raise ValueError("spaCy output token count differs from pre-tokenized PUD input")
        for gold, predicted in zip(sentence["tokens"], predicted_tokens):
            gold_head = gold["gold_head_index"]
            if gold_head is None:
                totals["unscorable_tokens"] += 1
                continue
            correct = int(predicted["head_index"] == gold_head)
            upos = gold["upos"].upper()
            deprel = gold["deprel"]
            totals["tokens"] += 1
            totals["uas_hits"] += correct
            if gold.get("is_root", False):
                totals["root_tokens"] += 1
                totals["root_hits"] += correct
            if upos != "PUNCT":
                totals["nonpunct_tokens"] += 1
                totals["nonpunct_uas_hits"] += correct
            if upos in CONTENT_UPOS:
                totals["content_tokens"] += 1
                totals["content_uas_hits"] += correct
            by_upos[upos]["tokens"] += 1
            by_upos[upos]["uas_hits"] += correct
            by_deprel[deprel]["tokens"] += 1
            by_deprel[deprel]["uas_hits"] += correct

    def ratio(n, d):
        return n / d if d else None

    totals_out = dict(totals)
    totals_out.update({
        "uas": ratio(totals["uas_hits"], totals["tokens"]),
        "nonpunct_uas": ratio(totals["nonpunct_uas_hits"], totals["nonpunct_tokens"]),
        "content_uas": ratio(totals["content_uas_hits"], totals["content_tokens"]),
        "root_attachment_accuracy": ratio(totals["root_hits"], totals["root_tokens"]),
    })
    return {
        "totals": totals_out,
        "by_upos": {
            upos: {
                **dict(values),
                "uas": ratio(values["uas_hits"], values["tokens"]),
            }
            for upos, values in sorted(by_upos.items())
        },
        "by_gold_deprel": {
            relation: {
                **dict(values),
                "uas": ratio(values["uas_hits"], values["tokens"]),
            }
            for relation, values in sorted(by_deprel.items())
        },
    }


def run() -> dict:
    import spacy

    spec = DATASETS["en"]
    sentences = parse_dependency_conllu(download_dataset("en"))
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
            {"head_index": token.head.i, "deprel": token.dep_}
            for token in doc
        ])
    report = {
        "evaluation_type": "EXTERNAL_SPACY_ENGLISH_PUD_UNLABELED_DEPENDENCY_EVALUATION",
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
        "scoring": "UNLABELED_ATTACHMENT_UAS_ONLY",
        "dependency_label_comparison": (
            "NOT_SCORED: spaCy ClearNLP-derived labels are not the UD relation inventory"
        ),
        "source_data_persisted": False,
        "model_bundled": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "results": evaluate_predictions(sentences, predictions),
        "limitations": [
            "UAS compares head indices only and does not validate dependency relation labels.",
            "The model's published training sources include OntoNotes 5; training-data overlap with PUD is not claimed to be impossible.",
            "The model is evaluated without PUD fine-tuning.",
            "Dependency syntax is not equivalent to USG semantic roles or semantic relations.",
            "No LAS, semantic-role F1, or USG construction accuracy is claimed.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
