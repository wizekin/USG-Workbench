"""Independent lexical coverage evaluation of crawled evidence against held-out UD PUD.

Surface-form POS candidates and dictionary lemmas are evaluated separately.
This is lexical evidence coverage, not contextual tagging or semantic correctness.
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path
import unicodedata

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset, parse_conllu

POS_TO_UPOS = {
    "noun": "NOUN", "proper noun": "PROPN", "verb": "VERB",
    "adjective": "ADJ", "adverb": "ADV", "pronoun": "PRON",
    "determiner": "DET", "article": "DET", "preposition": "ADP",
    "postposition": "ADP", "conjunction": "CCONJ", "interjection": "INTJ",
    "numeral": "NUM", "number": "NUM", "particle": "PART",
    "auxiliary verb": "AUX", "auxiliary": "AUX", "adposition": "ADP",
}
CONTENT_UPOS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}


def normalize(form: str, language: str = "en") -> str:
    value = unicodedata.normalize("NFC", form.strip())
    return value.casefold() if language == "en" else value


def load_candidate_evidence(data_dir: str | Path, language: str = "en") -> dict:
    """Read every gzip JSONL shard; reject corrupt JSON and malformed entry containers."""
    root = Path(data_dir)
    shards = sorted(root.rglob("*.jsonl.gz"))
    if not shards:
        raise ValueError(f"no .jsonl.gz lexical shards found under {root}")
    forms: dict[str, set[str]] = defaultdict(set)
    lemmas: dict[str, set[str]] = defaultdict(set)
    observed_forms: dict[str, set[str]] = defaultdict(set)
    entry_count = 0
    for shard in shards:
        try:
            with gzip.open(shard, "rt", encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid JSON in {shard}:{line_number}") from exc
                    if not isinstance(record, dict):
                        raise ValueError(f"non-object record in {shard}:{line_number}")
                    entries = record.get("entries", []) or []
                    if not isinstance(entries, list):
                        raise ValueError(f"entries is not a list in {shard}:{line_number}")
                    for entry in entries:
                        if not isinstance(entry, dict):
                            raise ValueError(f"entry is not an object in {shard}:{line_number}")
                        raw_pos = str(entry.get("part_of_speech") or "").strip().casefold()
                        upos = POS_TO_UPOS.get(raw_pos)
                        if not upos:
                            continue
                        entry_count += 1
                        lemma = entry.get("lemma", "")
                        if isinstance(lemma, str) and lemma.strip():
                            key = normalize(lemma, language)
                            lemmas[key].add(upos)
                            forms[key].add(upos)
                        raw_forms = entry.get("forms", []) or []
                        if not isinstance(raw_forms, list):
                            raise ValueError(f"forms is not a list in {shard}:{line_number}")
                        for item in raw_forms:
                            if not isinstance(item, dict):
                                continue
                            form = item.get("form", "")
                            if isinstance(form, str) and form.strip():
                                key = normalize(form, language)
                                observed_forms[key].add(upos)
                                forms[key].add(upos)
        except (OSError, EOFError) as exc:
            raise ValueError(f"unable to read compressed shard {shard}: {exc}") from exc
    return {
        "forms": dict(forms),
        "lemmas": dict(lemmas),
        "observed_forms": dict(observed_forms),
        "entry_count": entry_count,
        "shard_count": len(shards),
    }


def load_candidate_inventory(data_dir: str | Path, language: str = "en") -> dict[str, set[str]]:
    """Backward-compatible surface-form-to-UPOS candidate index."""
    return load_candidate_evidence(data_dir, language)["forms"]


def evaluate(
    sentences: list[dict],
    inventory: dict[str, set[str]],
    language: str,
    lemma_inventory: dict[str, set[str]] | None = None,
) -> dict:
    totals = {
        "tokens": 0, "seen_tokens": 0, "oov_tokens": 0,
        "gold_tag_in_candidates": 0, "ambiguous_seen_tokens": 0,
        "content_tokens": 0, "content_seen_tokens": 0,
        "content_gold_tag_in_candidates": 0,
        "tokens_with_gold_lemma": 0, "gold_lemma_seen": 0,
        "gold_lemma_and_upos_hit": 0,
    }
    by_upos = defaultdict(lambda: {
        "tokens": 0, "seen": 0, "tag_hit": 0,
        "tokens_with_gold_lemma": 0, "gold_lemma_seen": 0,
        "gold_lemma_and_upos_hit": 0,
    })
    for sentence in sentences:
        for token in sentence["tokens"]:
            form = normalize(token["form"], language)
            gold = token["upos"]
            candidates = inventory.get(form, set())
            totals["tokens"] += 1
            row = by_upos[gold]
            row["tokens"] += 1
            if candidates:
                totals["seen_tokens"] += 1
                row["seen"] += 1
                if len(candidates) > 1:
                    totals["ambiguous_seen_tokens"] += 1
                if gold in candidates:
                    totals["gold_tag_in_candidates"] += 1
                    row["tag_hit"] += 1
            else:
                totals["oov_tokens"] += 1
            if gold in CONTENT_UPOS:
                totals["content_tokens"] += 1
                if candidates:
                    totals["content_seen_tokens"] += 1
                if gold in candidates:
                    totals["content_gold_tag_in_candidates"] += 1

            gold_lemma = token.get("lemma")
            if lemma_inventory is not None and isinstance(gold_lemma, str) and gold_lemma.strip():
                lemma_key = normalize(gold_lemma, language)
                lemma_candidates = lemma_inventory.get(lemma_key, set())
                totals["tokens_with_gold_lemma"] += 1
                row["tokens_with_gold_lemma"] += 1
                if lemma_candidates:
                    totals["gold_lemma_seen"] += 1
                    row["gold_lemma_seen"] += 1
                if gold in lemma_candidates:
                    totals["gold_lemma_and_upos_hit"] += 1
                    row["gold_lemma_and_upos_hit"] += 1

    def ratio(n: int, d: int):
        return n / d if d else None

    total_metrics = {
        **totals,
        "token_coverage": ratio(totals["seen_tokens"], totals["tokens"]),
        "oov_rate": ratio(totals["oov_tokens"], totals["tokens"]),
        "gold_tag_candidate_recall_all_tokens": ratio(totals["gold_tag_in_candidates"], totals["tokens"]),
        "gold_tag_hit_rate_when_seen": ratio(totals["gold_tag_in_candidates"], totals["seen_tokens"]),
        "ambiguity_rate_when_seen": ratio(totals["ambiguous_seen_tokens"], totals["seen_tokens"]),
        "content_token_coverage": ratio(totals["content_seen_tokens"], totals["content_tokens"]),
        "content_gold_tag_candidate_recall": ratio(totals["content_gold_tag_in_candidates"], totals["content_tokens"]),
        "gold_lemma_coverage": ratio(totals["gold_lemma_seen"], totals["tokens_with_gold_lemma"]),
        "gold_lemma_upos_candidate_recall": ratio(totals["gold_lemma_and_upos_hit"], totals["tokens_with_gold_lemma"]),
    }
    return {
        "language": language,
        "method": "EXTERNAL_CRAWL_EXACT_SURFACE_AND_LEMMA_CANDIDATE_MATCH",
        "totals": total_metrics,
        "by_upos": {
            tag: {
                **counts,
                "coverage": ratio(counts["seen"], counts["tokens"]),
                "gold_tag_candidate_recall": ratio(counts["tag_hit"], counts["tokens"]),
                "gold_lemma_coverage": ratio(counts["gold_lemma_seen"], counts["tokens_with_gold_lemma"]),
                "gold_lemma_upos_candidate_recall": ratio(
                    counts["gold_lemma_and_upos_hit"], counts["tokens_with_gold_lemma"]
                ),
            }
            for tag, counts in sorted(by_upos.items())
        },
        "lexicon_form_count": len(inventory),
        "lexicon_lemma_count": len(lemma_inventory) if lemma_inventory is not None else None,
        "interpretation_boundary": (
            "Dictionary-derived surface and lemma candidates are compared with independent PUD gold annotations. "
            "Candidate coverage is not contextual POS disambiguation. Lemma coverage is exact normalized matching, "
            "not lemmatizer accuracy. Morphological feature accuracy, precision, sense accuracy, and semantic "
            "capability are not measured."
        ),
    }


def run(data_dir: str | Path) -> dict:
    evidence = load_candidate_evidence(data_dir, "en")
    spec = DATASETS["en"]
    sentences = parse_conllu(download_dataset("en"))
    if len(sentences) != spec["sentences"]:
        raise ValueError(f"English PUD expected {spec['sentences']} sentences, got {len(sentences)}")
    result = evaluate(sentences, evidence["forms"], "en", evidence["lemmas"])
    result.update({
        "evaluation_type": "EXTERNAL_CRAWL_LEXICAL_GENERALIZATION_PUD",
        "lexical_source": "wizekin/USG-Workbench@usg-external-lexical-data",
        "lexical_source_is_candidate_only": True,
        "lexical_shard_count": evidence["shard_count"],
        "mapped_dictionary_entry_count": evidence["entry_count"],
        "observed_form_count": len(evidence["observed_forms"]),
        "pud_repository": f"UniversalDependencies/{spec['repo']}",
        "pud_commit": spec["commit"],
        "pud_file": spec["file"],
        "pud_git_blob_sha1": spec["blob_sha"],
        "pud_license": "CC BY-SA 3.0",
        "pud_sentences": len(sentences),
        "source_text_persisted": False,
        "runtime_promotion_allowed": False,
        "limitations": [
            "The crawler is partial; its current inventory is not a complete dictionary.",
            "Exact surface and lemma matching do not use sentence context or infer unseen inflections.",
            "PUD is one English domain snapshot and does not establish broad language coverage.",
            "UPOS mapping is a conservative label normalization, not a trained POS tagger.",
            "Morphological feature accuracy and precision are not measured.",
            "Results do not authorize promotion into the active USG lexicon or interpreter.",
        ],
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="directory containing downloaded lexical shards")
    parser.add_argument("--output", default="artifacts/external-lexical-pud-evaluation.json")
    args = parser.parse_args()
    report = run(args.data_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
