"""Held-out lexical morphology candidate generation on English/Arabic UD PUD.

Rules are induced from training folds only. This is a candidate generator
experiment, not a POS tagger or a USG runtime capability.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import unicodedata

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_external_pud_v0_2.crossval import _fold_index, normalize

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-4-pud-morphology.json"
MIN_RULE_SUPPORT = 2


def _features(raw: str) -> tuple[tuple[str, str], ...]:
    if raw in {"", "_"}:
        return ()
    values = []
    for item in raw.split("|"):
        key, sep, value = item.partition("=")
        if sep and key and value:
            values.append((key, value))
    return tuple(sorted(values))


def parse_morph_conllu(payload: bytes) -> list[dict]:
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
            if cols[3] == "_" or cols[2] == "_":
                continue
            tokens.append({
                "id": int(cols[0]), "form": cols[1], "lemma": cols[2],
                "upos": cols[3], "feats": _features(cols[5]),
            })
        if tokens:
            sentences.append({"meta": meta, "tokens": tokens})
    return sentences


def _rule_for(token: dict, language: str) -> tuple | None:
    form = normalize(token["form"], language)
    lemma = normalize(token["lemma"], language)
    if form == lemma or len(form) < 2 or len(lemma) < 2:
        return None

    # A prefix attachment: e.g. Arabic definite article and conjunction+article.
    if form.endswith(lemma):
        prefix = form[:-len(lemma)]
        if prefix:
            return (token["upos"], "prefix", "", prefix, token["feats"])

    # A suffix attachment or suffix alternation.
    if form.startswith(lemma):
        extra = form[len(lemma):]
        if extra:
            # English consonant doubling: run -> running, plan -> planning.
            last = lemma[-1]
            if len(lemma) >= 3 and extra.startswith(last):
                return (token["upos"], "suffix", last, last + extra[1:], token["feats"])
            return (token["upos"], "suffix", "", extra, token["feats"])

    # General suffix replacement after a shared stem: city -> cities, study -> studies.
    common = 0
    while common < min(len(form), len(lemma)) and form[common] == lemma[common]:
        common += 1
    if common >= 2 and common < len(form) and common < len(lemma):
        lemma_suffix, surface_suffix = lemma[common:], form[common:]
        return (token["upos"], "suffix", lemma_suffix, surface_suffix, token["feats"])

    # Internal stem alternations are deliberately not guessed.
    return None


def induce_rules(sentences: list[dict], language: str,
                 min_support: int = MIN_RULE_SUPPORT) -> dict:
    support = Counter()
    examples = defaultdict(set)
    for sentence in sentences:
        for token in sentence["tokens"]:
            rule = _rule_for(token, language)
            if rule is not None:
                support[rule] += 1
                examples[rule].add((normalize(token["lemma"], language),
                                    normalize(token["form"], language)))
    return {
        rule: support[rule]
        for rule in support
        if support[rule] >= min_support
    }


def analyze_token(form: str, language: str, rules: dict) -> set[tuple]:
    value = normalize(form, language)
    candidates = set()
    for (upos, mode, lemma_affix, surface_affix, feats), count in rules.items():
        if mode == "prefix":
            if surface_affix and value.startswith(surface_affix):
                lemma = value[len(surface_affix):]
            else:
                continue
        else:
            if not surface_affix or not value.endswith(surface_affix):
                continue
            stem = value[:-len(surface_affix)]
            lemma = stem + lemma_affix
        if lemma and lemma != value:
            candidates.add((lemma, upos, feats, "MORPHOLOGY_RULE"))
    return candidates


def _exact_candidates(train: list[dict], language: str) -> dict:
    index = defaultdict(set)
    for sentence in train:
        for token in sentence["tokens"]:
            form = normalize(token["form"], language)
            lemma = normalize(token["lemma"], language)
            index[form].add((lemma, token["upos"], token["feats"], "EXACT_FORM"))
    return index


def evaluate_fold(train: list[dict], test: list[dict], language: str) -> dict:
    rules = induce_rules(train, language)
    exact = _exact_candidates(train, language)
    totals = Counter()
    by_upos = defaultdict(Counter)
    rule_usage = Counter()

    for sentence in test:
        for token in sentence["tokens"]:
            form = normalize(token["form"], language)
            gold = (
                normalize(token["lemma"], language),
                token["upos"],
                token["feats"],
            )
            exact_set = exact.get(form, set())
            morph_set = analyze_token(form, language, rules)
            candidates = {
                (lemma, upos, feats)
                for lemma, upos, feats, _source in exact_set | morph_set
            }
            exact_hit = gold in {
                (lemma, upos, feats) for lemma, upos, feats, _source in exact_set
            }
            lemma_pos_hit = (gold[0], gold[1]) in {
                (lemma, upos) for lemma, upos, _feats in candidates
            }
            feature_hit = gold in candidates
            morph_hit = gold in {
                (lemma, upos, feats)
                for lemma, upos, feats, source in morph_set
                if source == "MORPHOLOGY_RULE"
            }
            is_oov = not exact_set

            totals["tokens"] += 1
            totals["exact_form_seen"] += int(bool(exact_set))
            totals["oov_tokens"] += int(is_oov)
            totals["exact_candidate_full_hit"] += int(exact_hit)
            totals["lemma_pos_candidate_hit"] += int(lemma_pos_hit)
            totals["lemma_pos_candidate_miss"] += int(not lemma_pos_hit)
            totals["feature_bundle_candidate_hit"] += int(feature_hit)
            totals["morphology_rescue"] += int(is_oov and morph_hit)
            totals["oov_lemma_pos_hit"] += int(is_oov and lemma_pos_hit)
            totals["ambiguous_candidate_tokens"] += int(len(candidates) > 1)
            totals["candidate_count"] += len(candidates)
            by_upos[token["upos"]]["tokens"] += 1
            by_upos[token["upos"]]["lemma_pos_hit"] += int(lemma_pos_hit)
            by_upos[token["upos"]]["oov"] += int(is_oov)
            by_upos[token["upos"]]["feature_hit"] += int(feature_hit)
            if morph_set:
                rule_usage["tokens_with_morph_candidates"] += 1
                rule_usage["morph_candidates"] += len(morph_set)

    return {
        "totals": dict(totals),
        "by_upos": {k: dict(v) for k, v in sorted(by_upos.items())},
        "rule_inventory_size": len(rules),
        "rule_usage": dict(rule_usage),
    }


def cross_validate(sentences: list[dict], language: str, folds: int = 10) -> dict:
    if folds < 2 or len(sentences) < folds:
        raise ValueError("at least two folds and one sentence per fold are required")
    fold_ids = [_fold_index(s, i, folds) for i, s in enumerate(sentences)]
    aggregate = Counter()
    per_upos = defaultdict(Counter)
    reports = []
    for fold in range(folds):
        train = [s for i, s in enumerate(sentences) if fold_ids[i] != fold]
        test = [s for i, s in enumerate(sentences) if fold_ids[i] == fold]
        result = evaluate_fold(train, test, language)
        aggregate.update(result["totals"])
        for upos, values in result["by_upos"].items():
            per_upos[upos].update(values)
        reports.append({
            "fold": fold, "train_sentences": len(train),
            "test_sentences": len(test), **result,
        })

    def ratio(n, d):
        return n / d if d else None

    t = dict(aggregate)
    t.update({
        "exact_form_coverage": ratio(aggregate["exact_form_seen"], aggregate["tokens"]),
        "oov_rate": ratio(aggregate["oov_tokens"], aggregate["tokens"]),
        "lemma_pos_candidate_recall": ratio(aggregate["lemma_pos_candidate_hit"], aggregate["tokens"]),
        "feature_bundle_candidate_recall": ratio(aggregate["feature_bundle_candidate_hit"], aggregate["tokens"]),
        "morphology_rescue_rate_over_oov": ratio(aggregate["morphology_rescue"], aggregate["oov_tokens"]),
        "ambiguous_candidate_rate": ratio(aggregate["ambiguous_candidate_tokens"], aggregate["tokens"]),
        "mean_candidate_count": ratio(aggregate["candidate_count"], aggregate["tokens"]),
    })
    return {
        "language": language,
        "fold_count": folds,
        "totals": t,
        "by_upos": {
            upos: {
                **dict(values),
                "lemma_pos_recall": ratio(values["lemma_pos_hit"], values["tokens"]),
                "feature_bundle_recall": ratio(values["feature_hit"], values["tokens"]),
            }
            for upos, values in sorted(per_upos.items())
        },
        "folds": reports,
    }


def run() -> dict:
    report = {
        "evaluation_type": "EXTERNAL_PUD_HELDOUT_MORPHOLOGY_CANDIDATE_GENERATION",
        "method": "TRAIN_FOLD_INDUCED_PREFIX_SUFFIX_PARADIGM_RULES",
        "minimum_rule_support": MIN_RULE_SUPPORT,
        "fold_assignment": "SHA256_SENTENCE_ID_HASH",
        "license": "CC BY-SA 3.0",
        "source_data_persisted": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "datasets": {},
    }
    for language, spec in DATASETS.items():
        sentences = parse_morph_conllu(download_dataset(language))
        if len(sentences) != spec["sentences"]:
            raise ValueError(
                f"{language}: expected {spec['sentences']} sentences, got {len(sentences)}"
            )
        result = cross_validate(sentences, language, folds=10)
        result.update({
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "sentences": len(sentences),
            "syntactic_words": sum(len(s["tokens"]) for s in sentences),
        })
        report["datasets"][language] = result
    report["limitations"] = [
        "Rules are induced from training-fold surface/lemma/UPOS/FEATS pairs only.",
        "This is a candidate generator, not contextual POS disambiguation.",
        "UD gold annotations provide evaluation labels but do not establish USG semantic senses.",
        "Prefix/suffix rules do not cover internal stem changes or all non-concatenative Arabic morphology.",
        "Candidate inclusion is not accuracy; ambiguity and OOV must be reported separately.",
        "No rules or derived lexicons are persisted as production resources.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
