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
from tools.phase6_spacy_nominal_e2e_v0_1.evaluation import evaluate_candidate_sets
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
