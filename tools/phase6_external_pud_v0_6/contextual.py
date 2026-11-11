"""Contextual MSA POS/analysis selection using a lightweight structured perceptron.

CAMeL MLE supplies morphology candidate sets and an out-of-context baseline.
A fold-trained averaged structured perceptron uses sentence context to predict
UPOS, then selects only among licensed CAMeL candidates. This is an isolated
benchmark experiment, not a USG runtime component.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import unicodedata

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_external_pud_v0_2.crossval import _fold_index
from tools.phase6_external_pud_v0_4.morphology import parse_morph_conllu
from tools.phase6_external_pud_v0_5.camel_msa import normalize_arabic

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-4-contextual-morphology.json"
START = "__START__"
EPOCHS = 3


def _bucket(value: int) -> str:
    if value == 0:
        return "0"
    if value == 1:
        return "1"
    if value <= 3:
        return "2-3"
    if value <= 7:
        return "4-7"
    return "8+"


def token_features(tokens: list[dict], analyses: list[list[dict]], index: int,
                   mle_top: dict | None = None) -> tuple[str, ...]:
    token = tokens[index]
    word = normalize_arabic(token["form"])
    previous = normalize_arabic(tokens[index - 1]["form"]) if index else "__BOS__"
    previous2 = normalize_arabic(tokens[index - 2]["form"]) if index > 1 else "__BOS2__"
    following = normalize_arabic(tokens[index + 1]["form"]) if index + 1 < len(tokens) else "__EOS__"
    following2 = normalize_arabic(tokens[index + 2]["form"]) if index + 2 < len(tokens) else "__EOS2__"
    feats = {"BIAS", f"W={word}", f"W-1={previous}", f"W-2={previous2}",
             f"W+1={following}", f"W+2={following2}"}
    for size in range(1, 5):
        if len(word) >= size:
            feats.add(f"P{size}={word[:size]}")
            feats.add(f"S{size}={word[-size:]}")
    feats.add(f"PREV_BIGRAM={previous}|{word}")
    feats.add(f"NEXT_BIGRAM={word}|{following}")
    feats.add(f"PREV_SUFFIX2={previous[-2:]}")
    feats.add(f"NEXT_PREFIX2={following[:2]}")
    feats.add(f"LEN={_bucket(len(word))}")
    feats.add(f"IS_ARABIC={int(any('ARABIC' in unicodedata.name(c, '') and c.isalpha() for c in word))}")
    feats.add(f"IS_DIGIT={int(word.isdigit())}")
    feats.add(f"HAS_DIGIT={int(any(c.isdigit() for c in word))}")
    feats.add(f"IS_PUNCT={int(bool(word) and all(unicodedata.category(c).startswith('P') for c in word))}")
    feats.add(f"HAS_HYPHEN={int('-' in word or 'ـ' in word)}")

    candidates = analyses[index]
    feats.add(f"CAMEL_COUNT={_bucket(len(candidates))}")
    for candidate in candidates:
        analysis = candidate["analysis"]
        for key in ("ud", "pos", "gen", "num", "cas", "stt", "asp", "mod",
                    "vox", "per", "prc0", "prc1", "prc2", "prc3", "enc0"):
            value = analysis.get(key)
            if value not in (None, "", "_"):
                feats.add(f"CAMEL_{key.upper()}={value}")
    if candidates:
        top = candidates[0]["analysis"]
        top_lemma = top.get("lex")
        if isinstance(top_lemma, str) and top_lemma:
            feats.add(f"CAMEL_TOP_LEMMA={normalize_arabic(top_lemma)}")
        for key in ("ud", "pos", "gen", "num", "cas", "stt", "asp", "mod"):
            value = top.get(key)
            if value not in (None, "", "_"):
                feats.add(f"CAMEL_TOP_{key.upper()}={value}")
    if mle_top:
        top_lemma = mle_top.get("lex")
        if isinstance(top_lemma, str) and top_lemma:
            feats.add(f"MLE_TOP_LEMMA={normalize_arabic(top_lemma)}")
        top_upos = mle_top.get("ud")
        if isinstance(top_upos, str) and top_upos:
            feats.add(f"MLE_TOP_UD={top_upos}")
    return tuple(sorted(feats))


def prepare_sentences(sentences: list[dict], disambiguator, analyzer) -> list[dict]:
    prepared = []
    for sentence in sentences:
        tokens = sentence["tokens"]
        forms = [token["form"] for token in tokens]
        disambiguated = disambiguator.disambiguate(forms)
        analyses = []
        mle_top1 = []
        for item, form in zip(disambiguated, forms):
            top = item.analyses[0].analysis if item.analyses else None
            mle_top1.append(top)
            rows = []
            for analysis in analyzer.analyze(form):
                if not isinstance(analysis, dict):
                    continue
                rows.append({
                    "analysis": analysis,
                    "pos_lex_logprob": analysis.get("pos_lex_logprob"),
                    "lex_logprob": analysis.get("lex_logprob"),
                })
            analyses.append(rows)
        features = [
            token_features(tokens, analyses, i, mle_top1[i])
            for i in range(len(tokens))
        ]
        prepared.append({
            "meta": sentence.get("meta", {}),
            "tokens": tokens,
            "analyses": analyses,
            "mle_top1": mle_top1,
            "features": features,
            "gold": [token["upos"] for token in tokens],
        })
    return prepared


class AveragedStructuredPerceptron:
    def __init__(self, epochs: int = EPOCHS):
        self.epochs = epochs
        self.weights = defaultdict(float)
        self.totals = defaultdict(float)
        self.timestamps = defaultdict(int)
        self.step = 0
        self.tags = []

    def _score(self, tag: str, features: tuple[str, ...], previous: str) -> float:
        weights = self.weights
        score = weights[(tag, f"TRANS={previous}")]
        for feature in features:
            score += weights[(tag, feature)]
        return score

    def predict(self, sequence: list[tuple[str, ...]]) -> list[str]:
        if not sequence:
            return []
        tags = self.tags
        weights = self.weights
        # Compute emissions once per token/tag; only transitions vary in Viterbi.
        emissions = [
            {
                tag: sum(weights[(tag, feature)] for feature in features)
                for tag in tags
            }
            for features in sequence
        ]
        scores = {
            tag: emissions[0][tag] + weights[(tag, f"TRANS={START}")]
            for tag in tags
        }
        backpointers = []
        for position in range(1, len(sequence)):
            next_scores = {}
            back = {}
            for tag in tags:
                best_previous = tags[0]
                best_score = float("-inf")
                transition_base = f"TRANS="
                for previous in tags:
                    score = (
                        scores[previous]
                        + weights[(tag, transition_base + previous)]
                        + emissions[position][tag]
                    )
                    if score > best_score:
                        best_score = score
                        best_previous = previous
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

    def _update(self, key: tuple[str, str], amount: float) -> None:
        self.totals[key] += (self.step - self.timestamps[key]) * self.weights[key]
        self.timestamps[key] = self.step
        self.weights[key] += amount

    def fit(self, samples: list[dict]) -> "AveragedStructuredPerceptron":
        self.tags = sorted({tag for sample in samples for tag in sample["gold"]})
        for _epoch in range(self.epochs):
            for sample in samples:
                self.step += 1
                features = sample["features"]
                gold = sample["gold"]
                predicted = self.predict(features)
                if predicted == gold:
                    continue
                previous_gold = START
                previous_predicted = START
                for position, (feature_set, gold_tag, predicted_tag) in enumerate(
                    zip(features, gold, predicted)
                ):
                    for feature in feature_set:
                        self._update((gold_tag, feature), 1.0)
                        self._update((predicted_tag, feature), -1.0)
                    self._update((gold_tag, f"TRANS={previous_gold}"), 1.0)
                    self._update((predicted_tag, f"TRANS={previous_predicted}"), -1.0)
                    previous_gold = gold_tag
                    previous_predicted = predicted_tag
        averaged = {}
        denominator = max(self.step, 1)
        for key, weight in self.weights.items():
            total = self.totals[key] + (self.step - self.timestamps[key]) * weight
            averaged[key] = total / denominator
        self.weights = defaultdict(float, averaged)
        return self


def _candidate_score(candidate: dict) -> tuple:
    pos_score = candidate.get("pos_lex_logprob")
    lex_score = candidate.get("lex_logprob")
    try:
        pos_score = float(pos_score)
    except (TypeError, ValueError):
        pos_score = float("-inf")
    try:
        lex_score = float(lex_score)
    except (TypeError, ValueError):
        lex_score = float("-inf")
    lex = candidate["analysis"].get("lex", "")
    return (pos_score, lex_score, str(lex))


def _best_for_upos(candidates: list[dict], upos: str) -> dict | None:
    matching = [
        candidate for candidate in candidates
        if str(candidate["analysis"].get("ud", "")).upper() == upos.upper()
    ]
    return max(matching, key=_candidate_score) if matching else None


def evaluate_fold(train: list[dict], test: list[dict], epochs: int = EPOCHS) -> dict:
    model = AveragedStructuredPerceptron(epochs=epochs).fit(train)
    totals = defaultdict(int)
    by_upos = defaultdict(lambda: defaultdict(int))
    for sample in test:
        predicted = model.predict(sample["features"])
        for position, (token, candidates, gold, guess) in enumerate(zip(
            sample["tokens"], sample["analyses"], sample["gold"], predicted
        )):
            gold_lemma = normalize_arabic(token["lemma"])
            gold_upos = gold.upper()
            rows = {
                (normalize_arabic(str(c["analysis"].get("lex", ""))),
                 str(c["analysis"].get("ud", "")).upper())
                for c in candidates
            }
            candidate_hit = (gold_lemma, gold_upos) in rows
            mle_top = sample["mle_top1"][position]
            mle_correct = bool(
                mle_top
                and normalize_arabic(str(mle_top.get("lex", ""))) == gold_lemma
                and str(mle_top.get("ud", "")).upper() == gold_upos
            )
            selected = _best_for_upos(candidates, guess)
            selected_correct = bool(
                selected
                and normalize_arabic(str(selected["analysis"].get("lex", ""))) == gold_lemma
                and str(selected["analysis"].get("ud", "")).upper() == gold_upos
            )
            totals["tokens"] += 1
            totals["candidate_upper_bound_hits"] += int(candidate_hit)
            totals["mle_top1_hits"] += int(mle_correct)
            totals["crf_pos_hits"] += int(guess.upper() == gold_upos)
            totals["crf_selected_hits"] += int(selected_correct)
            totals["crf_selected_tokens"] += int(selected is not None)
            totals["crf_abstentions"] += int(selected is None)
            totals["ambiguous_candidate_tokens"] += int(len(rows) > 1)
            row = by_upos[gold_upos]
            row["tokens"] += 1
            row["mle_top1_hits"] += int(mle_correct)
            row["crf_pos_hits"] += int(guess.upper() == gold_upos)
            row["crf_selected_hits"] += int(selected_correct)
            row["candidate_upper_bound_hits"] += int(candidate_hit)

    def ratio(n, d):
        return n / d if d else None

    t = dict(totals)
    t.update({
        "candidate_upper_bound_recall": ratio(totals["candidate_upper_bound_hits"], totals["tokens"]),
        "mle_top1_lemma_pos_accuracy": ratio(totals["mle_top1_hits"], totals["tokens"]),
        "crf_pos_accuracy": ratio(totals["crf_pos_hits"], totals["tokens"]),
        "crf_selected_lemma_pos_accuracy": ratio(totals["crf_selected_hits"], totals["tokens"]),
        "crf_selected_accuracy_when_not_abstaining": ratio(
            totals["crf_selected_hits"], totals["crf_selected_tokens"]),
        "crf_selection_coverage": ratio(totals["crf_selected_tokens"], totals["tokens"]),
        "crf_abstention_rate": ratio(totals["crf_abstentions"], totals["tokens"]),
        "candidate_ambiguity_rate": ratio(totals["ambiguous_candidate_tokens"], totals["tokens"]),
    })
    return {
        "totals": t,
        "by_upos": {
            upos: {
                **dict(values),
                "mle_top1_accuracy": ratio(values["mle_top1_hits"], values["tokens"]),
                "crf_pos_accuracy": ratio(values["crf_pos_hits"], values["tokens"]),
                "crf_selected_lemma_pos_accuracy": ratio(values["crf_selected_hits"], values["tokens"]),
                "candidate_upper_bound_recall": ratio(values["candidate_upper_bound_hits"], values["tokens"]),
            }
            for upos, values in sorted(by_upos.items())
        },
    }


def cross_validate(prepared: list[dict], folds: int = 10, epochs: int = EPOCHS) -> dict:
    fold_ids = [_fold_index(sample, i, folds) for i, sample in enumerate(prepared)]
    aggregate = defaultdict(int)
    per_upos = defaultdict(lambda: defaultdict(int))
    fold_reports = []
    for fold in range(folds):
        train = [s for i, s in enumerate(prepared) if fold_ids[i] != fold]
        test = [s for i, s in enumerate(prepared) if fold_ids[i] == fold]
        result = evaluate_fold(train, test, epochs=epochs)
        aggregate.update(result["totals"])
        for upos, values in result["by_upos"].items():
            per_upos[upos].update(values)
        fold_reports.append({
            "fold": fold, "train_sentences": len(train),
            "test_sentences": len(test), **result,
        })

    def ratio(n, d):
        return n / d if d else None

    totals = dict(aggregate)
    totals.update({
        "candidate_upper_bound_recall": ratio(aggregate["candidate_upper_bound_hits"], aggregate["tokens"]),
        "mle_top1_lemma_pos_accuracy": ratio(aggregate["mle_top1_hits"], aggregate["tokens"]),
        "crf_pos_accuracy": ratio(aggregate["crf_pos_hits"], aggregate["tokens"]),
        "crf_selected_lemma_pos_accuracy": ratio(aggregate["crf_selected_hits"], aggregate["tokens"]),
        "crf_selected_accuracy_when_not_abstaining": ratio(
            aggregate["crf_selected_hits"], aggregate["crf_selected_tokens"]),
        "crf_selection_coverage": ratio(aggregate["crf_selected_tokens"], aggregate["tokens"]),
        "crf_abstention_rate": ratio(aggregate["crf_abstentions"], aggregate["tokens"]),
        "candidate_ambiguity_rate": ratio(aggregate["ambiguous_candidate_tokens"], aggregate["tokens"]),
    })
    return {
        "fold_count": folds, "epochs": epochs, "totals": totals,
        "by_upos": {
            upos: {
                **dict(values),
                "mle_top1_accuracy": ratio(values["mle_top1_hits"], values["tokens"]),
                "crf_pos_accuracy": ratio(values["crf_pos_hits"], values["tokens"]),
                "crf_selected_lemma_pos_accuracy": ratio(values["crf_selected_hits"], values["tokens"]),
                "candidate_upper_bound_recall": ratio(values["candidate_upper_bound_hits"], values["tokens"]),
            }
            for upos, values in sorted(per_upos.items())
        },
        "folds": fold_reports,
    }


def run() -> dict:
    from camel_tools.disambig.mle import MLEDisambiguator
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.morphology.database import MorphologyDB

    db = MorphologyDB.builtin_db("calima-msa-r13", flags="a")
    analyzer = Analyzer(db, backoff="NONE", cache_size=100000)
    mle = MLEDisambiguator.pretrained(
        "calima-msa-r13", analyzer=analyzer, top=1, cache_size=100000
    )
    spec = DATASETS["ar"]
    sentences = parse_morph_conllu(download_dataset("ar"))
    if len(sentences) != spec["sentences"]:
        raise ValueError(f"expected {spec['sentences']} Arabic PUD sentences, got {len(sentences)}")
    prepared = prepare_sentences(sentences, mle, analyzer)
    result = cross_validate(prepared, folds=10, epochs=EPOCHS)
    report = {
        "evaluation_type": "EXTERNAL_PUD_CONTEXTUAL_MORPHOLOGY_CANDIDATE_DISAMBIGUATION",
        "method": "TEN_FOLD_AVERAGED_STRUCTURED_PERCEPTRON_WITH_CAMEL_MLE_CANDIDATES",
        "epochs": EPOCHS,
        "fold_assignment": "SHA256_SENTENCE_ID_HASH",
        "toolkit": "camel-tools==1.6.0",
        "morphology_database": "calima-msa-r13",
        "mle_model": "calima-msa-r13",
        "database_and_mle_data_license": "GPL-2.0",
        "source": {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "license": "CC BY-SA 3.0",
            "sentences": len(sentences),
        },
        "toolkit_and_model_bundled": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "results": result,
        "limitations": [
            "The structured perceptron is trained on nine PUD folds and tested on the held-out fold.",
            "CAMeL candidate analyses and MLE scores come from an external pretrained resource; overlap with PUD training data is unknown.",
            "The contextual model predicts UPOS and selects only among existing CAMeL analyses; it cannot recover a missing gold lemma.",
            "The MLE top-1 baseline is word-based/out-of-context; the perceptron is the contextual comparison.",
            "The candidate upper bound is calculated from the full Analyzer output, not the MLE top-1 result.",
            "This experiment does not evaluate semantic roles, dependencies, or USG construction interpretation.",
            "The GPL-2.0 morphology and MLE data are installed only in the ephemeral CI runner.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
