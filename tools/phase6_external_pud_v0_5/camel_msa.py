"""Optional CAMeL Tools MSA analyzer evaluation on the pinned Arabic PUD treebank.

CAMeL Tools and its morphology database are installed only in this optional
evaluation environment; neither is bundled into the USG runtime or repository.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import unicodedata

from tools.phase6_external_pud_v0_1.run import DATASETS, download_dataset
from tools.phase6_external_pud_v0_4.morphology import parse_morph_conllu

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6-4-camel-msa-pud.json"


def normalize_arabic(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    output = []
    for char in value:
        if char == "\u0640" or unicodedata.category(char) == "Mn":
            continue
        output.append({
            "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
            "ى": "ي", "ة": "ه",
        }.get(char, char))
    return "".join(output)


def extract_candidates(analyses: list[dict]) -> set[tuple[str, str]]:
    candidates = set()
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        lemma = analysis.get("lex")
        upos = analysis.get("ud")
        if not isinstance(lemma, str) or not lemma:
            continue
        if not isinstance(upos, str) or not upos or upos == "_":
            continue
        candidates.add((normalize_arabic(lemma), upos.upper()))
    return candidates


def evaluate(sentences: list[dict], analyzer) -> dict:
    totals = Counter()
    by_upos = {}
    for sentence in sentences:
        for token in sentence["tokens"]:
            form = token["form"]
            gold_lemma = normalize_arabic(token["lemma"])
            gold_upos = token["upos"].upper()
            analyses = analyzer.analyze(form)
            candidates = extract_candidates(analyses)
            has_analysis = bool(candidates)
            lemma_hit = any(lemma == gold_lemma for lemma, _upos in candidates)
            upos_hit = any(upos == gold_upos for _lemma, upos in candidates)
            lemma_pos_hit = (gold_lemma, gold_upos) in candidates

            totals["tokens"] += 1
            totals["tokens_with_analysis"] += int(has_analysis)
            totals["no_analysis_tokens"] += int(not has_analysis)
            totals["lemma_candidate_hit"] += int(lemma_hit)
            totals["upos_candidate_hit"] += int(upos_hit)
            totals["lemma_pos_candidate_hit"] += int(lemma_pos_hit)
            totals["ambiguous_tokens"] += int(len(candidates) > 1)
            totals["candidate_count"] += len(candidates)

            if any(
                ch.isalpha() and "ARABIC" in unicodedata.name(ch, "")
                for ch in form
            ):
                totals["arabic_script_tokens"] += 1
                totals["arabic_script_with_analysis"] += int(has_analysis)
                totals["arabic_script_lemma_hit"] += int(lemma_hit)
                totals["arabic_script_upos_hit"] += int(upos_hit)
                totals["arabic_script_lemma_pos_hit"] += int(lemma_pos_hit)

            row = by_upos.setdefault(gold_upos, Counter())
            row["tokens"] += 1
            row["with_analysis"] += int(has_analysis)
            row["lemma_hit"] += int(lemma_hit)
            row["upos_hit"] += int(upos_hit)
            row["lemma_pos_hit"] += int(lemma_pos_hit)
            row["ambiguous"] += int(len(candidates) > 1)

    def ratio(n, d):
        return n / d if d else None

    result = dict(totals)
    result.update({
        "analysis_coverage": ratio(totals["tokens_with_analysis"], totals["tokens"]),
        "lemma_candidate_recall": ratio(totals["lemma_candidate_hit"], totals["tokens"]),
        "upos_candidate_recall": ratio(totals["upos_candidate_hit"], totals["tokens"]),
        "lemma_pos_candidate_recall": ratio(totals["lemma_pos_candidate_hit"], totals["tokens"]),
        "ambiguous_candidate_rate": ratio(totals["ambiguous_tokens"], totals["tokens"]),
        "mean_candidate_count": ratio(totals["candidate_count"], totals["tokens"]),
        "arabic_script_analysis_coverage": ratio(
            totals["arabic_script_with_analysis"], totals["arabic_script_tokens"]),
        "arabic_script_lemma_recall": ratio(
            totals["arabic_script_lemma_hit"], totals["arabic_script_tokens"]),
        "arabic_script_upos_recall": ratio(
            totals["arabic_script_upos_hit"], totals["arabic_script_tokens"]),
        "arabic_script_lemma_pos_recall": ratio(
            totals["arabic_script_lemma_pos_hit"], totals["arabic_script_tokens"]),
    })
    result["by_upos"] = {
        upos: {
            **dict(values),
            "analysis_coverage": ratio(values["with_analysis"], values["tokens"]),
            "lemma_recall": ratio(values["lemma_hit"], values["tokens"]),
            "upos_recall": ratio(values["upos_hit"], values["tokens"]),
            "lemma_pos_recall": ratio(values["lemma_pos_hit"], values["tokens"]),
        }
        for upos, values in sorted(by_upos.items())
    }
    return result


def run() -> dict:
    try:
        from camel_tools.morphology.analyzer import Analyzer
        from camel_tools.morphology.database import MorphologyDB
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional CAMeL Tools environment and morphology-db-msa-r13"
        ) from exc

    db = MorphologyDB.builtin_db("calima-msa-r13", flags="a")
    analyzer = Analyzer(db, backoff="NONE", cache_size=100000)
    spec = DATASETS["ar"]
    sentences = parse_morph_conllu(download_dataset("ar"))
    if len(sentences) != spec["sentences"]:
        raise ValueError(
            f"Arabic PUD expected {spec['sentences']} sentences, got {len(sentences)}"
        )
    report = {
        "evaluation_type": "EXTERNAL_CAMEL_TOOLS_MSA_MORPHOLOGY_CANDIDATE_EVALUATION",
        "toolkit": "camel-tools==1.6.0",
        "database": "calima-msa-r13",
        "database_license": "GPL-2.0",
        "backoff": "NONE",
        "database_bundled": False,
        "toolkit_bundled": False,
        "usg_runtime_integration": False,
        "semantic_acceptance_credit": False,
        "construction_promotion_allowed": False,
        "source": {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"],
            "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"],
            "license": "CC BY-SA 3.0",
            "sentences": len(sentences),
        },
        "metrics": evaluate(sentences, analyzer),
        "limitations": [
            "This is an external morphology candidate analysis, not contextual disambiguation.",
            "The CALIMA database may return multiple analyses; candidate inclusion is not accuracy.",
            "No guarantee is made that the analyzer training data is disjoint from PUD.",
            "PUD is an MSA-oriented treebank and does not evaluate Egyptian Arabic dialect coverage.",
            "The morphology database is GPL-2.0 and is installed only in the ephemeral CI environment.",
            "No CAMeL code or database is copied into the USG repository or runtime distribution.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
