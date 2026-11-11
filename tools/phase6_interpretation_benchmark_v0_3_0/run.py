"""Deterministic evaluator for the frozen Phase 6 v0.3.0 gold corpus."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "benchmarks/phase6-interpretation-v0.3.0/corpus.json"
SCHEMA = ROOT / "benchmarks/phase6-interpretation-v0.3.0/corpus.schema.json"


def load_corpus(path=CORPUS):
    corpus = json.loads(Path(path).read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(corpus))
    if errors:
        raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
    ids = set()
    inventory = {(lang, item["construction_id"]) for lang, items in corpus["construction_inventory"].items() for item in items}
    counts = defaultdict(Counter)
    for case in corpus["cases"]:
        if case["id"] in ids:
            raise ValueError(f"duplicate fixture id: {case['id']}")
        ids.add(case["id"])
        key = (case["language"], case["target_construction"])
        if key not in inventory:
            raise ValueError(f"fixture targets unknown construction: {key}")
        counts[key][case["gold_class"]] += 1
        text = case["text"]
        for role, span in case["expected_role_spans"].items():
            if span["end"] > len(text) or text[span["start"]:span["end"]] != span["surface"]:
                raise ValueError(f"invalid source span in {case['id']} / {role}")
            if case["expected_roles"].get(role) != span["surface"]:
                raise ValueError(f"role/span mismatch in {case['id']} / {role}")
        if case["gold_class"] == "POSITIVE":
            if case["gold_construction"] != case["target_construction"] or not case["expected_roles"]:
                raise ValueError(f"positive fixture lacks its target gold graph: {case['id']}")
            if case["expected_completion_status"] != "COMPLETE" or case["ambiguity_reason"] is not None:
                raise ValueError(f"invalid positive status/ambiguity annotation: {case['id']}")
        else:
            if case["gold_construction"] is not None or case["expected_roles"] or case["expected_role_spans"]:
                raise ValueError(f"negative/ambiguous fixture must not invent a unique graph: {case['id']}")
            if case["expected_completion_status"] is not None:
                raise ValueError(f"negative/ambiguous target class must not force a pipeline status: {case['id']}")
            if (case["gold_class"] == "AMBIGUOUS") != (case["ambiguity_reason"] is not None):
                raise ValueError(f"ambiguity reason mismatch: {case['id']}")
    required = corpus["minimums_per_language_and_construction"]
    for key in sorted(inventory):
        for label, minimum in (("POSITIVE", required["positive"]), ("NEGATIVE", required["negative"]), ("AMBIGUOUS", required["ambiguous"])):
            if counts[key][label] < minimum:
                raise ValueError(f"insufficient denominator for {key} / {label}: {counts[key][label]} < {minimum}")
    return corpus


def evaluate(corpus, predictions):
    """Evaluate construction detection/abstention and positive graph accuracy independently."""
    gold = {x["id"]: x for x in corpus["cases"]}
    rows = predictions.get("predictions")
    if not isinstance(rows, list):
        raise ValueError("predictions must contain a predictions array")
    pred = {}
    for row in rows:
        cid = row.get("case_id") if isinstance(row, dict) else None
        if cid not in gold or cid in pred:
            raise ValueError(f"unknown or duplicate prediction case_id: {cid}")
        pred[cid] = row
    report = {}
    inventory = [(lang, c["construction_id"]) for lang, cs in corpus["construction_inventory"].items() for c in cs]
    for lang, construction in sorted(inventory):
        cases = [x for x in corpus["cases"] if x["language"] == lang and x["target_construction"] == construction]
        positive = [x for x in cases if x["gold_class"] == "POSITIVE"]
        negative = [x for x in cases if x["gold_class"] == "NEGATIVE"]
        ambiguous = [x for x in cases if x["gold_class"] == "AMBIGUOUS"]
        if not positive or not negative or not ambiguous:
            raise ValueError(f"empty metric denominator for {lang}/{construction}")
        tp = fp = fn = roles = spans = 0
        neg_abstain = amb_abstain = 0
        for case in cases:
            p = pred.get(case["id"], {})
            selected = p.get("construction_id") == construction
            if case["gold_class"] == "POSITIVE":
                tp += int(selected)
                fn += int(not selected)
                roles += int(selected and p.get("role_bindings", {}) == case["expected_roles"])
                predicted_spans = p.get("role_spans", {})
                valid = predicted_spans == case["expected_role_spans"]
                for span in predicted_spans.values() if isinstance(predicted_spans, dict) else []:
                    if not isinstance(span, dict):
                        valid = False
                    elif span.get("start", -1) < 0 or span.get("end", 0) <= span.get("start", -1) or case["text"][span.get("start", 0):span.get("end", 0)] != span.get("surface"):
                        valid = False
                spans += int(selected and valid)
            elif case["gold_class"] == "NEGATIVE":
                fp += int(selected)
                neg_abstain += int(not selected)
            else:
                fp += int(selected)
                amb_abstain += int(not selected)
        predicted = tp + fp
        report[f"{lang}/{construction}"] = {
            "fixture_count": len(cases), "positive_denominator": len(positive),
            "negative_denominator": len(negative), "ambiguous_denominator": len(ambiguous),
            "precision": tp / predicted if predicted else 0.0,
            "recall": tp / len(positive),
            "role_accuracy": roles / len(positive),
            "source_span_accuracy": spans / len(positive),
            "negative_abstention": neg_abstain / len(negative),
            "ambiguous_abstention": amb_abstain / len(ambiguous),
            "false_unique_constructions": fp,
        }
    return {"benchmark_id": corpus["benchmark_id"], "case_count": len(corpus["cases"]), "by_construction": report}


def quality_gate(report):
    gates = {}
    for key, m in report["by_construction"].items():
        gates[key] = (
            m["precision"] >= 0.95 and m["recall"] >= 0.90
            and m["role_accuracy"] >= 0.95 and m["source_span_accuracy"] >= 0.95
            and m["negative_abstention"] == 1.0 and m["ambiguous_abstention"] == 1.0
            and m["false_unique_constructions"] == 0
        )
    return {"passed": bool(gates) and all(gates.values()), "by_construction": gates}
