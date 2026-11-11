"""Independent POS-candidate coverage evaluation of crawled lexical evidence against UD PUD.

The lexical candidate inventory comes only from the separately crawled dictionary
shards; gold UPOS labels come only from pinned, held-out UD PUD annotations.
This measures candidate coverage, not contextual tagging or semantic correctness.
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


def load_candidate_inventory(data_dir: str | Path, language: str = "en") -> dict[str, set[str]]:
    """Read every gzip JSONL shard under a snapshot directory; fail closed on corruption."""
    root = Path(data_dir)
    shards = sorted(root.rglob("*.jsonl.gz"))
    if not shards:
        raise ValueError(f"no .jsonl.gz lexical shards found under {root}")
    inventory: dict[str, set[str]] = defaultdict(set)
    for shard in shards:
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
                for entry in record.get("entries", []) or []:
                    if not isinstance(entry, dict):
                        continue
                    raw_pos = str(entry.get("part_of_speech") or "").strip().casefold()
                    upos = POS_TO_UPOS.get(raw_pos)
                    if not upos:
                        continue
                    forms = [entry.get("lemma", "")]
                    forms.extend(
                        item.get("form", "") for item in (entry.get("forms", []) or [])
                        if isinstance(item, dict)
                    )
                    for form in forms:
                        if isinstance(form, str) and form.strip():
                            inventory[normalize(form, language)].add(upos)
    return dict(inventory)


def evaluate(sentences: list[dict], inventory: dict[str, set[str]], language: str) -> dict:
    totals = {"tokens": 0, "seen_tokens": 0, "oov_tokens": 0,
              "gold_tag_in_candidates": 0, "ambiguous_seen_tokens": 0,
              "content_tokens": 0, "content_seen_tokens": 0,
              "content_gold_tag_in_candidates": 0}
    by_upos = defaultdict(lambda: {"tokens": 0, "seen": 0, "tag_hit": 0})
    for sentence in sentences:
        for token in sentence["tokens"]:
            form = normalize(token["form"], language)
            gold = token["upos"]
            candidates = inventory.get(form, set())
            totals["tokens"] += 1
            by_upos[gold]["tokens"] += 1
            if candidates:
                totals["seen_tokens"] += 1
                by_upos[gold]["seen"] += 1
                if len(candidates) > 1:
                    totals["ambiguous_seen_tokens"] += 1
                if gold in candidates:
                    totals["gold_tag_in_candidates"] += 1
                    by_upos[gold]["tag_hit"] += 1
            else:
                totals["oov_tokens"] += 1
            if gold in CONTENT_UPOS:
                totals["content_tokens"] += 1
                if candidates:
                    totals["content_seen_tokens"] += 1
                if gold in candidates:
                    totals["content_gold_tag_in_candidates"] += 1

    def ratio(n: int, d: int):
        return n / d if d else None

    return {
        "language": language,
        "method": "EXTERNAL_CRAWL_LEXICON_EXACT_FORM_UPOS_CANDIDATE_MATCH",
        "totals": {
            **totals,
            "token_coverage": ratio(totals["seen_tokens"], totals["tokens"]),
            "oov_rate": ratio(totals["oov_tokens"], totals["tokens"]),
            "gold_tag_candidate_recall_all_tokens": ratio(totals["gold_tag_in_candidates"], totals["tokens"]),
            "gold_tag_hit_rate_when_seen": ratio(totals["gold_tag_in_candidates"], totals["seen_tokens"]),
            "ambiguity_rate_when_seen": ratio(totals["ambiguous_seen_tokens"], totals["seen_tokens"]),
            "content_token_coverage": ratio(totals["content_seen_tokens"], totals["content_tokens"]),
            "content_gold_tag_candidate_recall": ratio(totals["content_gold_tag_in_candidates"], totals["content_tokens"]),
        },
        "by_upos": {
            tag: {**counts, "coverage": ratio(counts["seen"], counts["tokens"]),
                  "gold_tag_candidate_recall": ratio(counts["tag_hit"], counts["tokens"])}
            for tag, counts in sorted(by_upos.items())
        },
        "lexicon_form_count": len(inventory),
        "interpretation_boundary": (
            "Dictionary-derived POS candidates are compared with independent PUD gold tags. "
            "A candidate hit is not a correct disambiguation; no precision, contextual tagging, "
            "sense accuracy, morphology accuracy, or semantic capability is measured."
        ),
    }


def run(data_dir: str | Path) -> dict:
    inventory = load_candidate_inventory(data_dir, "en")
    spec = DATASETS["en"]
    sentences = parse_conllu(download_dataset("en"))
    if len(sentences) != spec["sentences"]:
        raise ValueError(f"English PUD expected {spec['sentences']} sentences, got {len(sentences)}")
    result = evaluate(sentences, inventory, "en")
    result.update({
        "evaluation_type": "EXTERNAL_CRAWL_LEXICAL_GENERALIZATION_PUD",
        "lexical_source": "wizekin/USG-Workbench@usg-external-lexical-data",
        "lexical_source_is_candidate_only": True,
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
            "Exact surface matching does not use context or infer unseen inflections.",
            "PUD is one English domain snapshot and does not establish broad language coverage.",
            "UPOS mapping is a conservative label normalization, not a trained POS tagger.",
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
