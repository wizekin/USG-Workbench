"""Gold-corpus validator and deterministic evaluator for USG-INTERPRET/0.2.0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from collections import Counter, defaultdict

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "benchmarks/phase5-interpretation/v0.2.0/corpus.json"
SCHEMA = ROOT / "benchmarks/phase5-interpretation/v0.2.0/corpus.schema.json"


def load_and_validate(path: Path = CORPUS) -> dict:
    corpus = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(corpus), key=lambda e: list(e.path))
    if errors:
        raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
    seen = set()
    for case in corpus["cases"]:
        if case["id"] in seen:
            raise ValueError(f"duplicate case id: {case['id']}")
        seen.add(case["id"])
        text = case["text"]
        for role, span in case["expected_role_spans"].items():
            if span["end"] > len(text) or text[span["start"]:span["end"]] != span["surface"]:
                raise ValueError(f"invalid gold span in {case['id']} role {role}")
            if case["expected_roles"].get(role) != span["surface"]:
                raise ValueError(f"gold role/span mismatch in {case['id']} role {role}")
        if case["gold_class"] == "POSITIVE":
            if case["expected_completion_status"] != "COMPLETE" or not case["expected_construction"]:
                raise ValueError(f"positive case lacks a gold construction: {case['id']}")
            if set(case["expected_roles"]) != {"AGENT", "ACTION", "PATIENT"}:
                raise ValueError(f"positive case must annotate AGENT/ACTION/PATIENT: {case['id']}")
        elif case["expected_roles"] or case["expected_role_spans"] or case["expected_construction"] is not None:
            raise ValueError(f"negative/ambiguous case must not invent a unique role graph: {case['id']}")
        if case["gold_class"] == "NEGATIVE" and case["expected_completion_status"] != "UNSUPPORTED":
            raise ValueError(f"negative case must expect UNSUPPORTED: {case['id']}")
        if case["gold_class"] == "AMBIGUOUS" and case["expected_completion_status"] != "AMBIGUOUS":
            raise ValueError(f"ambiguous case must expect AMBIGUOUS: {case['id']}")
    return corpus


def corpus_summary(corpus: dict) -> dict:
    counts = defaultdict(Counter)
    for case in corpus["cases"]:
        counts[case["language"]][case["gold_class"]] += 1
    return {
        "benchmark_id": corpus["benchmark_id"],
        "contract": corpus["contract"],
        "case_count": len(corpus["cases"]),
        "by_language": {
            lang: {kind: counts[lang][kind] for kind in ("POSITIVE", "NEGATIVE", "AMBIGUOUS")}
            for lang in sorted(counts)
        },
        "minimum_fixture_gate": {
            lang: all(counts[lang][kind] >= required for kind, required in
                      (("POSITIVE", 20), ("NEGATIVE", 20), ("AMBIGUOUS", 10)))
            for lang in sorted(counts)
        },
    }


def evaluate(corpus: dict, predictions: dict) -> dict:
    gold_by_id = {case["id"]: case for case in corpus["cases"]}
    pred_rows = predictions.get("predictions")
    if not isinstance(pred_rows, list):
        raise ValueError("predictions must contain a predictions array")
    pred_by_id = {}
    for row in pred_rows:
        if not isinstance(row, dict) or row.get("case_id") not in gold_by_id:
            raise ValueError("prediction has an unknown or missing case_id")
        if row["case_id"] in pred_by_id:
            raise ValueError(f"duplicate prediction for {row['case_id']}")
        pred_by_id[row["case_id"]] = row

    by_language = {}
    case_rows = []
    for lang in sorted({x["language"] for x in corpus["cases"]}):
        gold = [x for x in corpus["cases"] if x["language"] == lang]
        tp = fp = fn = status_ok = roles_ok = spans_ok = positive_total = 0
        for case in gold:
            pred = pred_by_id.get(case["id"], {})
            predicted_status = pred.get("completion_status")
            predicted_construction = pred.get("construction_id")
            gold_construction = case["expected_construction"]
            gold_positive = case["gold_class"] == "POSITIVE"
            predicted_positive = predicted_construction is not None
            if gold_positive:
                positive_total += 1
            if predicted_positive and gold_positive and predicted_construction == gold_construction:
                tp += 1
            elif predicted_positive:
                fp += 1
            if gold_positive and not (predicted_positive and predicted_construction == gold_construction):
                fn += 1
            status_match = predicted_status == case["expected_completion_status"]
            status_ok += int(status_match)
            role_match = pred.get("role_bindings", {}) == case["expected_roles"]
            if gold_positive:\n                roles_ok += int(role_match)
            predicted_spans = pred.get("role_spans", {})
            span_match = predicted_spans == case["expected_role_spans"]
            spans_valid = True
            for role_spans in predicted_spans.values() if isinstance(predicted_spans, dict) else []:
                items = role_spans if isinstance(role_spans, list) else [role_spans]
                for span in items:
                    if not isinstance(span, dict):
                        spans_valid = False
                        continue
                    start, end, surface = span.get("start"), span.get("end"), span.get("surface")
                    if (not isinstance(start, int) or isinstance(start, bool)
                            or not isinstance(end, int) or isinstance(end, bool)
                            or not isinstance(surface, str) or start < 0 or end <= start
                            or end > len(case["text"]) or case["text"][start:end] != surface):
                        spans_valid = False
            if gold_positive:\n                spans_ok += int(span_match and spans_valid)
            case_rows.append({
                "case_id": case["id"], "language": lang,
                "gold_class": case["gold_class"],
                "status_match": status_match,
                "construction_match": (predicted_construction == gold_construction),
                "role_bindings_match": role_match,
                "role_spans_match_and_valid": span_match and spans_valid,
                "prediction_present": case["id"] in pred_by_id,
            })
        predicted_positive_count = tp + fp
        by_language[lang] = {
            "case_count": len(gold),
            "positive_gold_count": positive_total,
            "construction_true_positive": tp,
            "construction_false_positive": fp,
            "construction_false_negative": fn,
            "construction_precision": tp / predicted_positive_count if predicted_positive_count else 0.0,
            "construction_recall": tp / positive_total if positive_total else 0.0,
            "completion_status_accuracy": status_ok / len(gold) if gold else 0.0,
            "role_binding_exact_accuracy": roles_ok / positive_total if positive_total else 0.0,
            "role_span_exact_and_valid_accuracy": spans_ok / positive_total if positive_total else 0.0,
            "missing_predictions": sum(1 for x in gold if x["id"] not in pred_by_id),
        }
    return {
        "benchmark_id": corpus["benchmark_id"],
        "contract": corpus["contract"],
        "evaluation_status": "EVALUATED",
        "by_language": by_language,
        "cases": case_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    corpus = load_and_validate(args.corpus)
    report = corpus_summary(corpus)
    if args.predictions:
        predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
        report["evaluation"] = evaluate(corpus, predictions)
    else:
        report["evaluation_status"] = "NOT_EVALUATED_NO_PREDICTIONS_SUPPLIED"
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    gates = report["minimum_fixture_gate"]
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
