"""End-to-end Arabic Stanza parse -> UD graph -> USG nominal candidates.

The parser is evaluated on pre-tokenized Arabic PUD test sentences. Gold UD
graphs are projected through the same USG adapter as a structural reference.
This is not semantic-role adjudication or a construction acceptance benchmark.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json

import stanza

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset, parse_conllu
from collections import defaultdict
from tools.phase6_ud_nominal_candidate_v0_1.adapter import adapt_sentence

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-6-stanza-arabic-nominal-e2e.json"
MODEL_DIR = ROOT / ".cache" / "stanza-arabic-padt"
STANZA_VERSION = "1.11.0"
STANZA_RESOURCES_COMMIT = "142bec5b5ed3069824ec4f843fc3589ab7b1afcc"
STANZA_RESOURCES_URL = (
    "https://raw.githubusercontent.com/stanfordnlp/stanza-resources/"
    + STANZA_RESOURCES_COMMIT
)
BATCH_SIZE = 24


def download_model() -> None:
    """Download the PADT model using a pinned Stanza resource manifest."""
    stanza.download(
        "ar",
        package="padt",
        model_dir=str(MODEL_DIR),
        resources_url=STANZA_RESOURCES_URL,
        resources_version=STANZA_VERSION,
        verbose=False,
    )


def load_pipeline():
    """Load the pretrained Arabic PADT pipeline without implicit downloads."""
    return stanza.Pipeline(
        "ar",
        package="padt",
        processors="tokenize,pos,depparse",
        tokenize_pretokenized=True,
        model_dir=str(MODEL_DIR),
        use_gpu=False,
        download_method=None,
        verbose=False,
    )


def stanza_sentence_to_ud_sentence(
    gold_sentence: dict, parsed_sentence, language: str = "ar"
) -> dict:
    """Attach Stanza's predicted UPOS/arcs to the original gold token sequence.

    PUD's gold word segmentation is deliberately supplied to Stanza. This
    isolates POS/dependency parsing from tokenization and prevents word-index
    drift from being mistaken for dependency errors.
    """
    if language != "ar":
        raise ValueError("this evaluation adapter is Arabic-only")
    gold_tokens = gold_sentence["tokens"]
    predicted_words = list(parsed_sentence.words)
    if len(predicted_words) != len(gold_tokens):
        raise ValueError(
            f"pretokenized word count changed: gold={len(gold_tokens)}, "
            f"predicted={len(predicted_words)}"
        )

    from tools.phase6_ud_nominal_candidate_v0_1.adapter import normalize_surface

    tokens = []
    for index, (gold, predicted) in enumerate(zip(gold_tokens, predicted_words)):
        if normalize_surface(predicted.text, language) != normalize_surface(gold["form"], language):
            raise ValueError(
                f"pretokenized word mismatch at token {index + 1}: "
                f"{gold['form']!r} != {predicted.text!r}"
            )
        head = int(predicted.head)
        head_index = index if head == 0 else head - 1
        if not 0 <= head_index < len(gold_tokens):
            raise ValueError(f"invalid Stanza head index {head} at token {index + 1}")
        relation = predicted.deprel
        upos = predicted.upos
        if not isinstance(relation, str) or not relation or not isinstance(upos, str) or not upos:
            raise ValueError(f"missing Stanza dependency/POS output at token {index + 1}")
        tokens.append({
            "id": gold["id"],
            "form": gold["form"],
            "lemma": predicted.lemma or gold.get("lemma", "_"),
            "upos": upos,
            "deprel": relation,
            "gold_head_index": head_index,
            "is_root": head == 0,
        })
    return {"meta": dict(gold_sentence.get("meta", {})), "tokens": tokens}


def parse_in_batches(nlp, sentences: list[dict], batch_size: int = BATCH_SIZE) -> tuple[list[dict], int]:
    """Parse batches of gold word sequences and return aligned UD-like graphs."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    output, alignment_failures = [], 0
    for start in range(0, len(sentences), batch_size):
        batch = sentences[start:start + batch_size]
        inputs = [[token["form"] for token in sentence["tokens"]] for sentence in batch]
        document = nlp(inputs)
        parsed_sentences = list(document.sentences)
        if len(parsed_sentences) != len(batch):
            raise ValueError(
                f"Stanza returned {len(parsed_sentences)} sentences for batch of {len(batch)}"
            )
        for gold, parsed in zip(batch, parsed_sentences):
            try:
                output.append(stanza_sentence_to_ud_sentence(gold, parsed))
            except ValueError:
                alignment_failures += 1
                output.append({"meta": dict(gold.get("meta", {})), "tokens": []})
    return output, alignment_failures


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
    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = true_positive / len(predicted) if predicted else None
    recall = true_positive / len(gold) if gold else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
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

    common_structural = predicted_structural & gold_structural
    span_exact_edges = sum(
        1 for edge in common_structural
        if pred_full_by_struct[edge] & gold_full_by_struct[edge]
    )
    by_construction = {}
    for construction in sorted({item[1] for item in predicted_full | gold_full}):
        pred = {item for item in predicted_full if item[1] == construction}
        expected = {item for item in gold_full if item[1] == construction}
        by_construction[construction] = _prf(pred, expected)
    return {
        "predicted_candidate_count": len(predicted_full),
        "gold_candidate_count": len(gold_full),
        "structural_edge_metrics_ignoring_spans": _prf(predicted_structural, gold_structural),
        "exact_candidate_and_span_metrics": _prf(predicted_full, gold_full),
        "exact_span_rate_given_structural_match": (
            span_exact_edges / len(common_structural) if common_structural else None
        ),
        "by_construction": by_construction,
    }


def run() -> dict:
    spec = DATASETS["ar"]
    payload = download_dataset("ar")
    gold_sentences = parse_conllu(payload)
    if len(gold_sentences) != spec["sentences"]:
        raise ValueError(
            f"expected {spec['sentences']} Arabic PUD sentences, got {len(gold_sentences)}"
        )

    download_model()
    nlp = load_pipeline()
    predicted_graphs, token_alignment_failures = parse_in_batches(nlp, gold_sentences)

    predicted_adapted = [adapt_sentence(graph, "ar") for graph in predicted_graphs]
    gold_adapted = [adapt_sentence(sentence, "ar") for sentence in gold_sentences]
    predicted_status = Counter(item["status"] for item in predicted_adapted)
    predicted_span_failures = sum(item["span_alignment_failures"] for item in predicted_adapted)
    metrics = evaluate_candidate_sets(predicted_adapted, gold_adapted)

    report = {
        "evaluation_type": "STANZA_TO_USG_NOMINAL_CANDIDATE_END_TO_END_ARABIC_PUD",
        "stanza_version": stanza.__version__,
        "model": "Arabic UD-PADT package=padt",
        "model_training_treebank": "UniversalDependencies/UD_Arabic-PADT",
        "model_license": "Apache-2.0 (Stanza model distribution)",
        "source": {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "license": spec["license"],
            "sentences": len(gold_sentences),
        },
        "tokenization": "PUD_GOLD_PRETOKENIZED_WORDS_PRESERVED",
        "gold_reference": "UD_PUD_GOLD_DEPENDENCY_GRAPH_PROJECTED_THROUGH_SAME_USG_ADAPTER",
        "predicted_input": "PRETRAINED_STANZA_ARABIC_PADT_POS_AND_DEPENDENCIES",
        "batch_size": BATCH_SIZE,
        "token_alignment_failure_sentences": token_alignment_failures,
        "predicted_sentence_status": dict(predicted_status),
        "predicted_span_alignment_failures": predicted_span_failures,
        "metrics": metrics,
        "source_data_persisted": False,
        "model_bundled": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "limitations": [
            "Gold references are UD syntactic structures projected through the same USG adapter, not human-adjudicated semantic-role gold.",
            "The Stanza Arabic PADT model is evaluated on Arabic PUD; shared source or training-data overlap cannot be ruled out.",
            "PUD gold tokenization is supplied to the parser, so tokenization and raw-text segmentation are not evaluated.",
            "Only the dependency/POS graph is predicted; lexical semantics and semantic-role interpretation are not independently adjudicated.",
            "A token alignment failure causes that sentence's predicted graph to abstain rather than score misaligned token IDs.",
            "All outputs remain candidate-only; this experiment cannot satisfy Step 6.6 semantic acceptance.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
