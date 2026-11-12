"""Evaluate the Step 6.6 candidate recognizer against the automatic oracle corpus."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from tools.phase6_auto_reference_v1_0.generate import build, validate
from tools.phase6_nominal_candidate_v0_4_1 import analyzer

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/phase6-step-6.6-automatic-reference-report.json"


def _score(corpus: dict, lexicon: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="usg-phase6-auto-reference-") as tmp:
        lex_path = Path(tmp) / "reference-lexicon.json"
        lex_path.write_text(json.dumps(lexicon, ensure_ascii=False), encoding="utf-8")
        original = analyzer.LEXICON
        analyzer.LEXICON = lex_path
        try:
            report = {}
            failed = []
            for key in sorted(corpus["construction_inventory"]):
                rows = [c for c in corpus["cases"] if f"{c['language']}/{c['target_construction']}" == key]
                pos = [c for c in rows if c["gold_class"] == "POSITIVE"]
                neg = [c for c in rows if c["gold_class"] == "NEGATIVE"]
                amb = [c for c in rows if c["gold_class"] == "AMBIGUOUS"]
                exact = role = span = relation = negative_abstain = ambiguity_preserved = 0
                false_unique = 0
                for case in rows:
                    prediction = analyzer.analyze(case["text"], case["language"])
                    cls = case["gold_class"]
                    ok = False
                    if cls == "POSITIVE":
                        ok = (
                            prediction.get("status") == "CANDIDATE"
                            and prediction.get("construction_id") == case["target_construction"]
                        )
                        exact += int(ok)
                        role += int(ok and prediction.get("role_bindings") == case["expected_role_bindings"])
                        span += int(ok and prediction.get("role_spans") == case["expected_role_spans"])
                        relation += int(ok and prediction.get("semantic_relation_candidate") == case["expected_relation_type"])
                    elif cls == "NEGATIVE":
                        ok = prediction.get("status") == "ABSTAIN" and prediction.get("construction_id") is None
                        negative_abstain += int(ok)
                    else:
                        expected = case["expected_status"]
                        if expected == "CANDIDATE_UNSPECIFIED":
                            ok = (
                                prediction.get("status") == "CANDIDATE"
                                and prediction.get("construction_id") == case["target_construction"]
                                and prediction.get("semantic_relation_candidate") == "GENITIVE_UNSPECIFIED"
                                and prediction.get("role_bindings") == case["expected_role_bindings"]
                                and prediction.get("role_spans") == case["expected_role_spans"]
                            )
                        elif expected == "AMBIGUOUS":
                            ok = prediction.get("status") == "AMBIGUOUS" and len(prediction.get("alternatives", [])) >= 2
                        else:
                            ok = prediction.get("status") in {"ABSTAIN", "AMBIGUOUS"} and prediction.get("construction_id") is None
                        ambiguity_preserved += int(ok)
                        false_unique += int(not ok)
                    if not ok:
                        failed.append(case["id"])
                npos, nneg, namb = len(pos), len(neg), len(amb)
                report[key] = {
                    "positive": npos,
                    "negative": nneg,
                    "ambiguous": namb,
                    "positive_detection": exact / npos if npos else 0.0,
                    "exact_role_accuracy": role / npos if npos else 0.0,
                    "exact_span_accuracy": span / npos if npos else 0.0,
                    "relation_accuracy": relation / npos if npos else 0.0,
                    "negative_abstention": negative_abstain / nneg if nneg else 0.0,
                    "ambiguity_preservation": ambiguity_preserved / namb if namb else 0.0,
                    "false_unique_ambiguities": false_unique,
                }
        finally:
            analyzer.LEXICON = original

    gates = {
        key: all(report[key][metric] >= 0.95 for metric in (
            "positive_detection", "exact_role_accuracy", "exact_span_accuracy", "relation_accuracy"
        )) and report[key]["negative_abstention"] == 1.0
        and report[key]["ambiguity_preservation"] == 1.0
        and report[key]["false_unique_ambiguities"] == 0
        for key in report
    }
    return {
        "evaluation_scope": "CONTROLLED_SYNTHETIC_SEMANTIC_REFERENCE_ONLY",
        "case_count": sum(sum(v.values()) for v in corpus["construction_inventory"].values()),
        "profile_count": len(report),
        "by_profile": report,
        "all_synthetic_profile_gates_passed": bool(gates) and all(gates.values()),
        "profile_gates": gates,
        "naturalistic_semantic_accuracy_claimed": False,
        "human_annotations_used": False,
        "model_labels_used": False,
        "benchmark_enabled_constructions": [],
        "runtime_capability_state": "CANDIDATE_ONLY",
        "failed_case_ids": failed,
    }


def run() -> dict:
    corpus, lexicon = build()
    validate(corpus, lexicon)
    corpus_bytes = (json.dumps(corpus, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    lexicon_bytes = (json.dumps(lexicon, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    evaluation = _score(corpus, lexicon)
    result = {
        "benchmark_id": corpus["benchmark_id"],
        "benchmark_version": corpus["version"],
        "license": "CC0-1.0",
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "reference_lexicon_sha256": hashlib.sha256(lexicon_bytes).hexdigest(),
        "evaluation": evaluation,
    }
    return {"corpus": corpus, "lexicon": lexicon, "report": result}


def main() -> None:
    result = run()
    root = ROOT / "benchmarks/phase6-auto-reference-v1.0"
    root.mkdir(parents=True, exist_ok=True)
    (root / "corpus.json").write_text(json.dumps(result["corpus"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (root / "reference-lexicon.json").write_text(json.dumps(result["lexicon"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result["report"], ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["report"], ensure_ascii=False, indent=2))
    if not result["report"]["evaluation"]["all_synthetic_profile_gates_passed"]:
        raise SystemExit("automatic synthetic-reference gate failed")


if __name__ == "__main__":
    main()
