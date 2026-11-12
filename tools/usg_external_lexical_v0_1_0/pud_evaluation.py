"""Independent lexical coverage evaluation of crawled evidence against held-out UD PUD.

Surface-form POS candidates and dictionary lemmas are evaluated separately.
This is lexical evidence coverage, not contextual tagging or semantic correctness.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import unicodedata

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset, parse_conllu
from tools.phase6_external_pud_v0_4.morphology import parse_morph_conllu

POS_TO_UPOS = {
    "noun": "NOUN", "proper noun": "PROPN", "verb": "VERB",
    "adjective": "ADJ", "adverb": "ADV", "pronoun": "PRON",
    "determiner": "DET", "article": "DET", "preposition": "ADP",
    "postposition": "ADP", "conjunction": "CCONJ", "interjection": "INTJ",
    "numeral": "NUM", "number": "NUM", "particle": "PART",
    "auxiliary verb": "AUX", "auxiliary": "AUX", "adposition": "ADP",
}
CONTENT_UPOS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}

SOURCE_TAG_TO_UD_FEATURE = {
    "plural": ("Number", "Plur"),
    "comparative": ("Degree", "Cmp"),
    "superlative": ("Degree", "Sup"),
}


def normalize(form: str, language: str = "en") -> str:
    value = unicodedata.normalize("NFC", form.strip())
    return value.casefold() if language == "en" else value


def load_candidate_evidence(data_dir: str | Path, language: str = "en") -> dict:
    """Read every gzip JSONL shard; reject corrupt JSON and malformed entry containers."""
    root = Path(data_dir)
    physical_shards = sorted(root.rglob("*.jsonl.gz"))
    if not physical_shards:
        raise ValueError(f"no .jsonl.gz lexical shards found under {root}")
    shards = []
    seen_shard_digests: set[str] = set()
    duplicate_shard_count = 0
    for shard in physical_shards:
        digest = hashlib.sha256(shard.read_bytes()).hexdigest()
        if digest in seen_shard_digests:
            duplicate_shard_count += 1
            continue
        seen_shard_digests.add(digest)
        shards.append(shard)
    forms: dict[str, set[str]] = defaultdict(set)
    lemmas: dict[str, set[str]] = defaultdict(set)
    observed_forms: dict[str, set[str]] = defaultdict(set)
    entry_count = 0
    form_tag_counts: Counter[str] = Counter()
    tagged_form_records = 0
    morphology_candidates: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    mapped_morphology_tag_counts: Counter[str] = Counter()
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
                    entries = record.get("entries", [])
                    if entries is None:
                        entries = []
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
                        raw_forms = entry.get("forms", [])
                        if raw_forms is None:
                            raw_forms = []
                        if not isinstance(raw_forms, list):
                            raise ValueError(f"forms is not a list in {shard}:{line_number}")
                        for item in raw_forms:
                            if not isinstance(item, dict):
                                continue
                            form = item.get("form", "")
                            form_key = None
                            if isinstance(form, str) and form.strip():
                                form_key = normalize(form, language)
                                observed_forms[form_key].add(upos)
                                forms[form_key].add(upos)
                            raw_tags = item.get("tags", [])
                            if isinstance(raw_tags, list):
                                tags = {
                                    part.strip().casefold()
                                    for tag in raw_tags if isinstance(tag, str)
                                    for part in tag.split(";") if part.strip()
                                }
                                if tags:
                                    tagged_form_records += 1
                                    form_tag_counts.update(tags)
                                    for tag in tags:
                                        feature = SOURCE_TAG_TO_UD_FEATURE.get(tag)
                                        if feature:
                                            if form_key is not None:
                                                morphology_candidates[form_key].add((upos, feature[0], feature[1]))
                                            mapped_morphology_tag_counts[tag] += 1
        except (OSError, EOFError) as exc:
            raise ValueError(f"unable to read compressed shard {shard}: {exc}") from exc
    return {
        "forms": dict(forms),
        "lemmas": dict(lemmas),
        "observed_forms": dict(observed_forms),
        "entry_count": entry_count,
        "shard_count": len(shards),
        "physical_shard_count": len(physical_shards),
        "duplicate_shard_count": duplicate_shard_count,
        "shard_content_sha256": sorted(seen_shard_digests),
        "form_tag_counts": dict(sorted(form_tag_counts.items())),
        "tagged_form_records": tagged_form_records,
        "morphology_candidates": dict(morphology_candidates),
        "mapped_morphology_tag_counts": dict(sorted(mapped_morphology_tag_counts.items())),
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
        "single_candidate_seen_tokens": 0,
        "multi_candidate_seen_tokens": 0,
        "candidate_label_total": 0,
    }
    by_upos = defaultdict(lambda: {
        "tokens": 0, "seen": 0, "tag_hit": 0,
        "tokens_with_gold_lemma": 0, "gold_lemma_seen": 0,
        "gold_lemma_and_upos_hit": 0,
        "single_candidate_seen_tokens": 0,
        "multi_candidate_seen_tokens": 0,
        "candidate_label_total": 0,
    })
    candidate_count_histogram: Counter[int] = Counter()
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
                candidate_count = len(candidates)
                candidate_count_histogram[candidate_count] += 1
                totals["candidate_label_total"] += candidate_count
                row["candidate_label_total"] += candidate_count
                if candidate_count == 1:
                    totals["single_candidate_seen_tokens"] += 1
                    row["single_candidate_seen_tokens"] += 1
                else:
                    totals["multi_candidate_seen_tokens"] += 1
                    row["multi_candidate_seen_tokens"] += 1
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
        "candidate_ambiguity": {
            "seen_tokens": totals["seen_tokens"],
            "single_candidate_seen_tokens": totals["single_candidate_seen_tokens"],
            "multi_candidate_seen_tokens": totals["multi_candidate_seen_tokens"],
            "candidate_label_count_distribution": {
                str(count): candidate_count_histogram[count]
                for count in sorted(candidate_count_histogram)
            },
            "mean_candidate_labels_when_seen": ratio(
                totals["candidate_label_total"], totals["seen_tokens"]
            ),
            "candidate_precision_measured": False,
            "candidate_precision_reason": (
                "The inventory contains unordered candidate sets; no candidate is selected or ranked "
                "for a token in context, so prediction precision is not defined."
            ),
        },
        "by_upos": {
            tag: {
                **counts,
                "coverage": ratio(counts["seen"], counts["tokens"]),
                "gold_tag_candidate_recall": ratio(counts["tag_hit"], counts["tokens"]),
                "gold_lemma_coverage": ratio(counts["gold_lemma_seen"], counts["tokens_with_gold_lemma"]),
                "gold_lemma_upos_candidate_recall": ratio(
                    counts["gold_lemma_and_upos_hit"], counts["tokens_with_gold_lemma"]
                ),
                "ambiguity_rate_when_seen": ratio(
                    counts["multi_candidate_seen_tokens"], counts["seen"]
                ),
                "mean_candidate_labels_when_seen": ratio(
                    counts["candidate_label_total"], counts["seen"]
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


def evaluate_morphology(sentences: list[dict], inventory: dict[str, set[tuple[str, str, str]]],
                       language: str = "en") -> dict:
    """Compare mapped source-tag candidates with pinned UD FEATS annotations."""
    supported = set(SOURCE_TAG_TO_UD_FEATURE.values())
    totals = Counter()
    by_feature = defaultdict(Counter)
    for sentence in sentences:
        for token in sentence["tokens"]:
            form = normalize(token["form"], language)
            upos = token["upos"]
            gold = {
                (upos, feature, value)
                for feature, value in token.get("feats", ())
                if (feature, value) in supported
            }
            candidates = inventory.get(form, set())
            hits = candidates & gold
            totals["tokens"] += 1
            totals["tokens_with_supported_gold_features"] += int(bool(gold))
            totals["tokens_with_candidate_features"] += int(bool(candidates))
            totals["tokens_with_any_gold_feature_hit"] += int(bool(hits))
            totals["gold_feature_instances"] += len(gold)
            totals["candidate_feature_instances"] += len(candidates)
            totals["matched_feature_instances"] += len(hits)
            for candidate_upos, feature, value in candidates:
                row = by_feature[f"{feature}={value}"]
                row["candidate_instances"] += 1
                if (candidate_upos, feature, value) in gold:
                    row["matched_instances"] += 1
            for _gold_upos, feature, value in gold:
                by_feature[f"{feature}={value}"]["gold_instances"] += 1

    def ratio(n: int, d: int):
        return n / d if d else None

    return {
        "method": "EXACT_SURFACE_UPOS_AND_MAPPED_SOURCE_TAG_VS_PINNED_UD_FEATS",
        "supported_source_tag_mapping": {
            tag: {"feature": feature, "value": value}
            for tag, (feature, value) in sorted(SOURCE_TAG_TO_UD_FEATURE.items())
        },
        "totals": {
            **dict(totals),
            "candidate_pool_precision": ratio(totals["matched_feature_instances"], totals["candidate_feature_instances"]),
            "candidate_recall": ratio(totals["matched_feature_instances"], totals["gold_feature_instances"]),
            "gold_feature_token_recall": ratio(totals["tokens_with_any_gold_feature_hit"], totals["tokens_with_supported_gold_features"]),
        },
        "by_feature": {
            key: {
                **dict(counts),
                "candidate_pool_precision": ratio(counts["matched_instances"], counts["candidate_instances"]),
                "candidate_recall": ratio(counts["matched_instances"], counts["gold_instances"]),
            }
            for key, counts in sorted(by_feature.items())
        },
        "interpretation_boundary": (
            "Candidate-pool precision is the fraction of emitted mapped feature labels matching "
            "the gold token annotation; it is not contextual morphology prediction accuracy. "
            "Only the explicitly mapped source tags and corresponding UD features are evaluated."
        ),
    }


def run(data_dir: str | Path) -> dict:
    evidence = load_candidate_evidence(data_dir, "en")
    spec = DATASETS["en"]
    payload = download_dataset("en")
    sentences = parse_conllu(payload)
    morphology_sentences = parse_morph_conllu(payload)
    if len(sentences) != spec["sentences"] or len(morphology_sentences) != spec["sentences"]:
        raise ValueError(
            f"English PUD expected {spec['sentences']} sentences, got "
            f"{len(sentences)} lexical and {len(morphology_sentences)} morphology sentences"
        )
    result = evaluate(sentences, evidence["forms"], "en", evidence["lemmas"])
    result["morphology_evaluation"] = evaluate_morphology(
        morphology_sentences, evidence["morphology_candidates"], "en"
    )
    result.update({
        "evaluation_type": "EXTERNAL_CRAWL_LEXICAL_GENERALIZATION_PUD",
        "lexical_source": "wizekin/USG-Workbench@usg-external-lexical-data",
        "lexical_source_is_candidate_only": True,
        "lexical_shard_count": evidence["shard_count"],
        "lexical_physical_shard_count": evidence["physical_shard_count"],
        "lexical_duplicate_shard_copies": evidence["duplicate_shard_count"],
        "lexical_shard_content_sha256": evidence["shard_content_sha256"],
        "mapped_dictionary_entry_count": evidence["entry_count"],
        "observed_form_count": len(evidence["observed_forms"]),
        "observed_form_tag_inventory": {
            "tagged_form_records": evidence["tagged_form_records"],
            "tag_counts": evidence["form_tag_counts"],
            "mapped_morphology_tag_counts": evidence["mapped_morphology_tag_counts"],
            "interpretation": (
                "Raw source form tags are reported for morphology-mapping research only; "
                "they are not treated as UD FEATS or as verified morphological predictions."
            ),
        },
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
            "Morphology is evaluated only for the explicitly mapped plural, comparative, and superlative source tags; other tags and UD features are excluded.",
            "Candidate-pool morphology precision is not contextual morphology prediction accuracy.",
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
