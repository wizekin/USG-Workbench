"""Ten-fold lexical POS-candidate coverage audit on external UD PUD.

Each fold's lexical candidates are learned from the other nine folds only.
This measures exact-form POS candidate coverage, not USG semantics or parsing.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import json
import unicodedata

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset, parse_conllu

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-6-pud-pos-crossval.json"
CONTENT_UPOS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}


def normalize(form: str, language: str) -> str:
    value = unicodedata.normalize("NFC", form)
    return value.casefold() if language == "en" else value


def _fold_index(sentence: dict, index: int, folds: int) -> int:
    sent_id = sentence.get("meta", {}).get("sent_id")
    if not sent_id:
        return index % folds
    digest = sha256(sent_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % folds


def cross_validate(sentences: list[dict], language: str, folds: int = 10) -> dict:
    if folds < 2 or len(sentences) < folds:
        raise ValueError("at least two folds and one sentence per fold are required")
    fold_ids = [_fold_index(sentence, index, folds)
                for index, sentence in enumerate(sentences)]
    totals = {
        "tokens": 0, "seen_tokens": 0, "oov_tokens": 0,
        "gold_tag_in_candidates": 0, "ambiguous_seen_tokens": 0,
        "content_tokens": 0, "content_seen_tokens": 0,
        "content_gold_tag_in_candidates": 0,
    }
    by_upos = defaultdict(lambda: {"tokens": 0, "seen": 0, "tag_hit": 0})
    fold_reports = []

    for fold in range(folds):
        train = [s for i, s in enumerate(sentences) if fold_ids[i] != fold]
        test = [s for i, s in enumerate(sentences) if fold_ids[i] == fold]
        lexicon = defaultdict(set)
        for sentence in train:
            for token in sentence["tokens"]:
                lexicon[normalize(token["form"], language)].add(token["upos"])

        fold_total = {"fold": fold, "train_sentences": len(train),
                      "test_sentences": len(test), "tokens": 0,
                      "seen_tokens": 0, "tag_hits": 0, "oov_tokens": 0}
        for sentence in test:
            for token in sentence["tokens"]:
                form = normalize(token["form"], language)
                candidates = lexicon.get(form, set())
                upos = token["upos"]
                totals["tokens"] += 1
                fold_total["tokens"] += 1
                by_upos[upos]["tokens"] += 1
                if candidates:
                    totals["seen_tokens"] += 1
                    fold_total["seen_tokens"] += 1
                    by_upos[upos]["seen"] += 1
                    if len(candidates) > 1:
                        totals["ambiguous_seen_tokens"] += 1
                    if upos in candidates:
                        totals["gold_tag_in_candidates"] += 1
                        fold_total["tag_hits"] += 1
                        by_upos[upos]["tag_hit"] += 1
                else:
                    totals["oov_tokens"] += 1
                    fold_total["oov_tokens"] += 1
                if upos in CONTENT_UPOS:
                    totals["content_tokens"] += 1
                    if candidates:
                        totals["content_seen_tokens"] += 1
                    if upos in candidates:
                        totals["content_gold_tag_in_candidates"] += 1
        fold_reports.append(fold_total)

    def ratio(n: int, d: int):
        return n / d if d else None

    return {
        "language": language,
        "method": "DETERMINISTIC_SENTENCE_ID_HASH_10_FOLD_CROSS_VALIDATION",
        "fold_count": folds,
        "totals": {
            **totals,
            "token_coverage": ratio(totals["seen_tokens"], totals["tokens"]),
            "tag_candidate_recall_over_all_tokens": ratio(
                totals["gold_tag_in_candidates"], totals["tokens"]),
            "tag_candidate_hit_rate_when_seen": ratio(
                totals["gold_tag_in_candidates"], totals["seen_tokens"]),
            "ambiguous_candidate_rate_when_seen": ratio(
                totals["ambiguous_seen_tokens"], totals["seen_tokens"]),
            "content_token_coverage": ratio(
                totals["content_seen_tokens"], totals["content_tokens"]),
            "content_tag_candidate_recall": ratio(
                totals["content_gold_tag_in_candidates"], totals["content_tokens"]),
        },
        "by_upos": {
            upos: {
                **counts,
                "coverage": ratio(counts["seen"], counts["tokens"]),
                "tag_candidate_recall": ratio(counts["tag_hit"], counts["tokens"]),
            }
            for upos, counts in sorted(by_upos.items())
        },
        "folds": fold_reports,
        "interpretation_boundary": (
            "This is lexical POS-candidate coverage only. It does not evaluate "
            "syntactic attachment, semantic roles, construction precision, or USG capability."
        ),
    }


def run() -> dict:
    report = {
        "evaluation_type": "EXTERNAL_PUD_CROSS_VALIDATED_POS_LEXICON_COVERAGE",
        "license": "CC BY-SA 3.0",
        "source_data_persisted": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "runtime_capability_state": "CANDIDATE_ONLY",
        "datasets": {},
    }
    for language, spec in DATASETS.items():
        sentences = parse_conllu(download_dataset(language))
        if len(sentences) != spec["sentences"]:
            raise ValueError(f"{language}: expected {spec['sentences']} sentences, got {len(sentences)}")
        result = cross_validate(sentences, language, folds=10)
        result["repository"] = f"UniversalDependencies/{spec['repo']}"
        result["commit"] = spec["commit"]
        result["file"] = spec["file"]
        result["git_blob_sha1"] = spec["blob_sha"]
        result["sentences"] = len(sentences)
        report["datasets"][language] = result

    report["limitations"] = [
        "Surface forms and UPOS tags are taken from the PUD training folds; test sentences are held out by sentence.",
        "The dictionary is an exact-form candidate set, not a contextual POS tagger.",
        "A tag being present in the candidate set is not a correct disambiguation.",
        "The audit does not create or validate USG semantic-role senses.",
        "PUD is a news/wiki test treebank and does not establish broad language coverage.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
