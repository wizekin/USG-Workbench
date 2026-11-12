"""Integrated Phase 6 bridge benchmark over the frozen Phase 5 bilingual corpus.

This reports bridge preservation only. It does not turn Phase 5 gold coverage into
new Phase 6 naturalistic accuracy evidence for Steps 6.7-6.11.
"""
from __future__ import annotations

import json
from pathlib import Path
from hashlib import sha256
from tools.phase5_interpretation_benchmark_v0_2_0.run import load_and_validate, CORPUS
from .interpret import Phase6IntegratedInterpreter

ROOT = Path(__file__).resolve().parents[2]


def run_integrated_benchmark() -> dict:
    corpus = load_and_validate(CORPUS)
    service = Phase6IntegratedInterpreter()
    rows = []
    tp = fp = fn = positive = negative = ambiguous = neg_abstain = amb_abstain = 0
    roles_ok = spans_ok = 0
    for case in corpus["cases"]:
        result = service.interpret(case["text"], case["language"])
        phase5 = result.get("phase5", {})
        stages = phase5.get("stages", {})
        syntax = stages.get("syntax", {}).get("artifact", {})
        semantic = stages.get("semantic_composition", {}).get("artifact", {})
        operators = stages.get("operators", {}).get("artifact", {})
        syntax_candidates = [
            candidate for clause in syntax.get("clauses", [])
            for candidate in clause.get("candidates", [])
        ]
        has_scoped_operator = any(
            candidate.get("operator_type") != "AUXILIARY"
            for clause in operators.get("clauses", [])
            for candidate in clause.get("candidates", [])
        )
        unique_candidate = (
            phase5.get("completion_status") == "COMPLETE"
            and semantic.get("status") == "COMPOSED"
            and not has_scoped_operator
            and len(syntax_candidates) == 1
        )
        predicted_construction = (
            syntax_candidates[0].get("construction_id") if unique_candidate else None
        )
        candidate_id = syntax_candidates[0].get("candidate_id") if unique_candidate else None
        phase6_nodes = result.get("graph", {}).get("nodes", [])
        predicted_roles = {}
        predicted_spans = {}
        if candidate_id:
            for node in phase6_nodes:
                if node.get("candidate_id") != candidate_id:
                    continue
                role = node.get("role")
                if role in {"AGENT", "ACTION", "PATIENT"}:
                    predicted_roles[role] = node["span"]["surface"]
                    predicted_spans[role] = {
                        "start": node["span"]["start"],
                        "end": node["span"]["end"],
                        "surface": node["span"]["surface"],
                    }
        if candidate_id and set(predicted_roles) != {"AGENT", "ACTION", "PATIENT"}:
            raise AssertionError("Phase 6 graph lost a role for " + case["id"])
        gold_positive = case["gold_class"] == "POSITIVE"
        if gold_positive:
            positive += 1
            exact_construction = predicted_construction == case["expected_construction"]
            exact_roles = predicted_roles == case["expected_roles"]
            exact_spans = predicted_spans == case["expected_role_spans"]
            if exact_construction:
                tp += 1
            else:
                fn += 1
            roles_ok += int(exact_roles)
            spans_ok += int(exact_spans)
        else:
            if case["gold_class"] == "NEGATIVE":
                negative += 1
                neg_abstain += int(predicted_construction is None)
            else:
                ambiguous += 1
                amb_abstain += int(predicted_construction is None)
            if predicted_construction is not None:
                fp += 1
        rows.append({
            "case_id": case["id"], "language": case["language"],
            "gold_class": case["gold_class"],
            "predicted_construction": predicted_construction,
            "phase6_status": result["status"],
            "exact_roles": (predicted_roles == case["expected_roles"]) if gold_positive else None,
            "exact_spans": (predicted_spans == case["expected_role_spans"]) if gold_positive else None,
        })
    predicted_positive = tp + fp
    metrics = {
        "case_count": len(rows), "positive_count": positive,
        "negative_count": negative, "ambiguous_count": ambiguous,
        "construction_precision": tp / predicted_positive if predicted_positive else 0.0,
        "construction_recall": tp / positive if positive else 0.0,
        "exact_role_accuracy": roles_ok / positive if positive else 0.0,
        "exact_source_span_accuracy": spans_ok / positive if positive else 0.0,
        "negative_abstention_rate": neg_abstain / negative if negative else 0.0,
        "ambiguous_abstention_rate": amb_abstain / ambiguous if ambiguous else 0.0,
        "false_unique_constructions": fp,
    }
    checks = {
        "positive_construction_precision_at_least_0_95": metrics["construction_precision"] >= 0.95,
        "positive_construction_recall_at_least_0_90": metrics["construction_recall"] >= 0.90,
        "exact_role_bindings": metrics["exact_role_accuracy"] == 1.0,
        "exact_valid_source_spans": metrics["exact_source_span_accuracy"] == 1.0,
        "negative_abstention": metrics["negative_abstention_rate"] == 1.0,
        "ambiguous_abstention": metrics["ambiguous_abstention_rate"] == 1.0,
        "zero_false_unique_constructions": metrics["false_unique_constructions"] == 0,
    }
    raw = json.dumps(corpus, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "benchmark_id": "USG-PHASE6-INTEGRATED-BRIDGE-REGRESSION",
        "benchmark_version": "0.1.0",
        "evaluation_scope": "FROZEN_PHASE5_CORPUS_TO_PHASE6_GRAPH_BRIDGE",
        "source_corpus_id": corpus["benchmark_id"],
        "source_corpus_sha256": sha256(raw).hexdigest(),
        "case_count": len(rows), "metrics": metrics, "checks": checks,
        "passed": all(checks.values()),
        "phase6_candidate_only": True,
        "new_phase6_naturalistic_accuracy_claimed": False,
        "rows": rows,
    }


def main() -> int:
    report = run_integrated_benchmark()
    output = ROOT / "benchmarks" / "phase6-integrated-bridge-v0.1.0" / "latest-report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"},
                     ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
