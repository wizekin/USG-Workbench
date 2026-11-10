"""Deterministic evaluator for the frozen USG-INTERPRET/0.1.0 corpus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.usg_interpretation_v0_1_0 import InterpretationService
from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore


def evaluate(fixtures: dict) -> dict:
    service = InterpretationService()
    rows = []
    status_matches = source_matches = evidence_aligned = schema_valid = 0
    truth_policy_violations = 0
    unresolved_total = unsupported_total = 0
    with CanonicalDocumentStore(":memory:") as store:
        for case in fixtures["cases"]:
            result = service.interpret(case["text"], case["language"])
            document = result["document"]
            status_ok = result["completion_status"] == case["expected_completion_status"]
            source_ok = document["sources"][0]["text"] == case["text"]
            evidence_ok = all(
                item["alignmentStatus"] == "EXACT"
                and item["quote"] == case["text"][item["span"]["start"]:item["span"]["end"]]
                for item in document["evidence"]
            )
            schema_ok = True
            try:
                store.put_document(document)
            except Exception as exc:
                schema_ok = False
                schema_error = f"{type(exc).__name__}:{exc}"
            else:
                schema_error = None
            policy_ok = all(
                item["commitment"] == "NONE"
                and item["epistemicStatus"] == "UNKNOWN"
                and item["lifecycleStage"] == "DISCOVERED"
                for item in document["assertions"]
            ) and all(item["semanticSupportStatus"] == "NOT_ESTABLISHED"
                     for item in document["evidence"])
            if not policy_ok:
                truth_policy_violations += 1
            status_matches += int(status_ok)
            source_matches += int(source_ok)
            evidence_aligned += int(evidence_ok)
            schema_valid += int(schema_ok)
            unresolved_total += len(document["unresolvedItems"])
            unsupported_total += int(result["completion_status"] == "UNSUPPORTED")
            rows.append({
                "case_id": case["id"],
                "expected_status": case["expected_completion_status"],
                "actual_status": result["completion_status"],
                "status_match": status_ok,
                "source_preserved": source_ok,
                "evidence_exact": evidence_ok,
                "canonical_document_valid": schema_ok,
                "schema_error": schema_error,
                "expression_count": len(document["expressions"]),
                "expected_expression_count": case["expected_expression_count"],
                "truth_policy_valid": policy_ok,
                "unresolved_item_count": len(document["unresolvedItems"]),
            })
    total = len(rows)
    return {
        "benchmark_id": fixtures["benchmark_id"],
        "benchmark_version": fixtures["version"],
        "pipeline_contract": fixtures["contract"],
        "case_count": total,
        "metrics": {
            "completion_status_accuracy": status_matches / total if total else 0.0,
            "source_preservation_rate": source_matches / total if total else 0.0,
            "exact_evidence_alignment_rate": evidence_aligned / total if total else 0.0,
            "canonical_document_validation_rate": schema_valid / total if total else 0.0,
            "truth_policy_violation_count": truth_policy_violations,
            "unresolved_item_count": unresolved_total,
            "unsupported_case_count": unsupported_total,
        },
        "acceptance": {
            "status_accuracy_at_least_1": status_matches == total,
            "source_preservation_at_least_1": source_matches == total,
            "evidence_alignment_at_least_1": evidence_aligned == total,
            "canonical_validation_at_least_1": schema_valid == total,
            "zero_truth_policy_violations": truth_policy_violations == 0,
        },
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=ROOT / "benchmarks/phase4-interpretation/v0.1.0/fixtures.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    report = evaluate(fixtures)
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if all(report["acceptance"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
