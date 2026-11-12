"""Run the automatic bilingual Phase 6 acceptance factory end to end.

The runner exercises the real integrated interpreter and local API. Its process
exit code reports whether the factory executed correctly; construction failures
are recorded in the report and do not get disguised as a green acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from hashlib import sha256
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

from tools.phase5_interpretation_benchmark_v0_2_0.run import load_and_validate
from tools.phase6_auto_reference_v1_0.evaluate import run as run_step_6_6
from tools.usg_local_api_v1_0_0.application import USGApplication

from .generate import PROFILE_SPECS, build, corpus_sha256, validate

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = ROOT / "benchmarks/phase6-automatic-acceptance-v1.0/corpus.json"
DEFAULT_REPORT = ROOT / "artifacts/phase6-automatic-acceptance-report.json"


def _graph_observation(response: dict[str, Any], expected_source: str) -> dict[str, Any]:
    interpretation = response.get("interpretation", {})
    graph = interpretation.get("graph", {}) if isinstance(interpretation, dict) else {}
    composition = interpretation.get("composition", {}) if isinstance(interpretation, dict) else {}
    composed_graph = composition.get("graph", {}) if isinstance(composition, dict) else {}
    grammatical = composition.get("grammatical", {}) if isinstance(composition, dict) else {}
    if not grammatical:
        grammatical = {"voice": graph.get("voice", "UNKNOWN"),
                       "speech_act": graph.get("speech_act", "UNKNOWN")}
    relations = graph.get("relations", [])
    operators = graph.get("operators", [])
    references = composed_graph.get("references", graph.get("references", []))
    nodes = graph.get("nodes", [])
    spans_valid = True
    source = interpretation.get("source", {}).get("text")
    if not isinstance(source, str):
        source = ""
    composition_source = composition.get("source", {})
    source_integrity = (
        source == expected_source
        and composition_source.get("text") == expected_source
        and composition_source.get("sha256") == sha256(
            expected_source.encode("utf-8")
        ).hexdigest()
    )
    for node in nodes:
        span = node.get("span", {})
        if span:
            start, end = span.get("start"), span.get("end")
            if (type(start) is not int or type(end) is not int or start < 0
                    or end <= start or end > len(source)
                    or source[start:end] != span.get("surface")):
                spans_valid = False
    for edge in relations:
        span = edge.get("evidence", {})
        if span:
            start, end = span.get("start"), span.get("end")
            if (type(start) is not int or type(end) is not int or start < 0
                    or end <= start or end > len(source)
                    or source[start:end] != span.get("surface")):
                spans_valid = False
    for item in graph.get("clauses", []):
        span = item.get("span", {})
        if span:
            start, end = span.get("start"), span.get("end")
            if (type(start) is not int or type(end) is not int or start < 0
                    or end <= start or end > len(source)
                    or source[start:end] != span.get("surface")):
                spans_valid = False
    for item in operators:
        span = item.get("span", {})
        if span:
            start, end = span.get("start"), span.get("end")
            if (type(start) is not int or type(end) is not int or start < 0
                    or end <= start or end > len(source)
                    or source[start:end] != span.get("surface")):
                spans_valid = False
    return {
        "interpretation": interpretation,
        "graph": graph,
        "composition": composition,
        "composed_graph": composed_graph,
        "grammatical": grammatical,
        "relations": relations if isinstance(relations, list) else [],
        "operators": operators if isinstance(operators, list) else [],
        "references": references if isinstance(references, list) else [],
        "nodes": nodes if isinstance(nodes, list) else [],
        "features": set(graph.get("features", [])),
        "relation_types": {item.get("type") for item in relations if isinstance(item, dict)},
        "operator_types": {item.get("type") for item in operators if isinstance(item, dict)},
        "spans_valid": spans_valid,
        "source_integrity": source_integrity,
    }


def _role_span_match(expected: list[dict[str, Any]], observed: dict[str, Any]) -> bool:
    if not expected:
        return True
    actual = Counter(
        (node.get("role"), node.get("span", {}).get("start"),
         node.get("span", {}).get("end"), node.get("span", {}).get("surface"))
        for node in observed["nodes"]
    )
    wanted = Counter(
        (item.get("role"), item.get("start"), item.get("end"), item.get("surface"))
        for item in expected
    )
    return all(actual[key] >= count for key, count in wanted.items())


def _positive_match(case: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, bool, list[str]]:
    expected = case["expected"]
    failures = []
    for relation in expected.get("required_relations", []):
        if relation not in observed["relation_types"]:
            failures.append("missing_relation:" + relation)
    for feature in expected.get("required_features", []):
        if feature not in observed["features"]:
            failures.append("missing_feature:" + feature)
    for operator in expected.get("required_operator_types", []):
        if operator not in observed["operator_types"]:
            failures.append("missing_operator:" + operator)
    required_voice = expected.get("required_voice")
    if required_voice and observed["grammatical"].get("voice") != required_voice:
        failures.append("voice_mismatch:" + required_voice)
    required_act = expected.get("required_speech_act")
    if required_act and observed["grammatical"].get("speech_act") != required_act:
        failures.append("speech_act_mismatch:" + required_act)
    for marker in expected.get("required_markers", []):
        if not any(
            item.get("evidence", {}).get("surface") == marker["surface"]
            and item.get("evidence", {}).get("start") == marker["start"]
            and item.get("evidence", {}).get("end") == marker["end"]
            for item in observed["relations"]
        ):
            failures.append("missing_or_misaligned_marker:" + marker["surface"])
    roles_ok = _role_span_match(expected.get("required_role_spans", []), observed)
    if not roles_ok:
        failures.append("required_role_spans_not_preserved")
    if not observed["source_integrity"]:
        failures.append("source_snapshot_or_digest_mismatch")
    if not observed["spans_valid"]:
        failures.append("invalid_source_grounded_span")
    if expected.get("required_operator_target"):
        if any(not item.get("target_id") for item in observed["operators"]):
            failures.append("operator_target_missing")
    if expected.get("required_scope"):
        if any(item.get("scope") not in {"LOCAL", "CLAUSE", "EMBEDDED", "UNRESOLVED"}
               for item in observed["operators"]):
            failures.append("operator_scope_missing")
    if expected.get("minimum_references", 0) > len(observed["references"]):
        failures.append("reference_candidates_missing")
    if expected.get("minimum_antecedent_candidates", 0) > max(
        [len(item.get("antecedent_candidates", [])) for item in observed["references"]] or [0]
    ):
        failures.append("antecedent_candidates_missing")
    if expected.get("require_unresolved_candidate"):
        if not any(item.get("status") == "UNRESOLVED"
                   and item.get("resolved_antecedent") is None
                   for item in observed["references"]):
            failures.append("unresolved_reference_candidate_not_preserved")
    return not failures, roles_ok, failures


def _negative_match(case: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, list[str]]:
    expected = case["expected"]
    failures = []
    for relation in expected.get("forbidden_relations", []):
        if relation in observed["relation_types"]:
            failures.append("false_relation:" + relation)
    for feature in expected.get("forbidden_features", []):
        if feature in observed["features"]:
            failures.append("false_feature:" + feature)
    for operator in expected.get("forbidden_operator_types", []):
        if operator in observed["operator_types"]:
            failures.append("false_operator:" + operator)
    if expected.get("forbidden_voice") and observed["grammatical"].get("voice") == expected["forbidden_voice"]:
        failures.append("false_voice:" + expected["forbidden_voice"])
    if expected.get("forbidden_speech_act") and observed["grammatical"].get("speech_act") == expected["forbidden_speech_act"]:
        failures.append("false_speech_act:" + expected["forbidden_speech_act"])
    if expected.get("forbidden_references") and observed["references"]:
        failures.append("false_reference_candidate")
    return not failures, failures


def _ambiguous_match(case: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, list[str]]:
    expected = case["expected"]
    failures = []
    if expected.get("ambiguity_alternatives_required"):
        # For coordination/subordination cases, preserving all explicitly
        # generated competing edges is the alternative-preservation criterion.
        required_relations = expected.get("required_relations", [])
        if required_relations:
            for relation in required_relations:
                if relation not in observed["relation_types"]:
                    failures.append("ambiguity_relation_not_preserved:" + relation)
        elif not (
            observed["interpretation"].get("status") == "AMBIGUOUS"
            or observed["graph"].get("alternatives")
            or observed["graph"].get("ambiguity")
            or observed["references"]
        ):
            failures.append("ambiguity_alternatives_not_exposed")
    if expected.get("forbidden_unique_voice"):
        if observed["grammatical"].get("voice") in {"ACTIVE", "PASSIVE", "MIDDLE"}:
            failures.append("ambiguous_voice_forced_unique")
    if expected.get("required_operator_types"):
        missing = set(expected["required_operator_types"]) - observed["operator_types"]
        failures.extend("ambiguous_operator_missing:" + item for item in sorted(missing))
    if expected.get("forbidden_unique_scope"):
        scopes = {item.get("scope") for item in observed["operators"]}
        if scopes and scopes <= {"LOCAL", "CLAUSE", "EMBEDDED"}:
            failures.append("ambiguous_scope_forced_unique")
    if expected.get("minimum_references", 0) > len(observed["references"]):
        failures.append("ambiguous_reference_missing")
    if expected.get("minimum_antecedent_candidates", 0) > max(
        [len(item.get("antecedent_candidates", [])) for item in observed["references"]] or [0]
    ):
        failures.append("ambiguous_antecedents_not_preserved")
    if expected.get("forbidden_unique_resolution"):
        if any(item.get("resolved_antecedent") for item in observed["references"]):
            failures.append("ambiguous_reference_forced_unique")
    return not failures, failures


def _evaluate_corpus(corpus: dict[str, Any], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    predicted = {item["case_id"]: item for item in predictions}
    by_profile: dict[str, dict[str, Any]] = {}
    for key in sorted(corpus["construction_inventory"]):
        lang, profile = key.split("/", 1)
        cases = [item for item in corpus["cases"]
                 if item["language"] == lang and item["profile"] == profile]
        pos = [item for item in cases if item["gold_class"] == "POSITIVE"]
        neg = [item for item in cases if item["gold_class"] == "NEGATIVE"]
        amb = [item for item in cases if item["gold_class"] == "AMBIGUOUS"]
        pos_hits = neg_hits = amb_hits = role_span_hits = 0
        false_unique = 0
        predicted_unique = 0
        diagnostics = []
        for case in cases:
            row = predicted[case["id"]]
            observed = row["observation"]
            if case["gold_class"] == "POSITIVE":
                ok, role_ok, failures = _positive_match(case, observed)
                pos_hits += int(ok)
                role_span_hits += int(role_ok and observed["spans_valid"])
                has_semantic_commitment = bool(
                    observed["relations"] or observed["operators"] or observed["references"]
                    or observed["grammatical"].get("voice") not in {None, "UNKNOWN"}
                    or observed["grammatical"].get("speech_act") not in {None, "UNKNOWN"}
                )
                if not ok and has_semantic_commitment:
                    false_unique += 1
                predicted_unique += int(has_semantic_commitment)
            elif case["gold_class"] == "NEGATIVE":
                ok, failures = _negative_match(case, observed)
                neg_hits += int(ok)
                false_unique += int(not ok)
                predicted_unique += int(not ok)
            else:
                ok, failures = _ambiguous_match(case, observed)
                amb_hits += int(ok)
                false_unique += int(not ok)
            if failures:
                diagnostics.append({"case_id": case["id"], "failures": failures,
                                    "phase6_status": row["phase6_status"],
                                    "diagnostics": row["diagnostics"]})
        precision = pos_hits / (pos_hits + false_unique) if (pos_hits + false_unique) else 0.0
        recall = pos_hits / len(pos) if pos else 0.0
        metrics = {
            "positive_cases": len(pos), "negative_cases": len(neg), "ambiguous_cases": len(amb),
            "positive_detection": pos_hits / len(pos) if pos else 0.0,
            "construction_precision": precision,
            "construction_recall": recall,
            "exact_role_span_accuracy": role_span_hits / len(pos) if pos else 0.0,
            "negative_abstention": neg_hits / len(neg) if neg else 0.0,
            "ambiguity_preservation": amb_hits / len(amb) if amb else 0.0,
            "false_unique_or_invalid_outcomes": false_unique,
        }
        checks = {
            "minimum_20_positive_20_negative_10_ambiguous": len(pos) >= 20 and len(neg) >= 20 and len(amb) >= 10,
            "precision_at_least_0_95": metrics["construction_precision"] >= 0.95,
            "recall_at_least_0_90": metrics["construction_recall"] >= 0.90,
            "exact_role_span_accuracy_1_00": metrics["exact_role_span_accuracy"] == 1.0,
            "negative_abstention_1_00": metrics["negative_abstention"] == 1.0,
            "ambiguity_preservation_1_00": metrics["ambiguity_preservation"] == 1.0,
            "zero_false_unique_outcomes": false_unique == 0,
        }
        by_profile[key] = {
            "step": PROFILE_SPECS_BY_KEY[key]["step"],
            "profile": profile,
            "language": lang,
            "metrics": metrics,
            "checks": checks,
            "passed": all(checks.values()),
            "failure_examples": diagnostics[:12],
        }
    step_results = {}
    for step in ("6.7", "6.8", "6.9", "6.10", "6.11"):
        profiles = [value for value in by_profile.values() if value["step"] == step]
        step_results[step] = {
            "status": "ACCEPTED" if profiles and all(x["passed"] for x in profiles) else "OPEN",
            "language_profiles": {x["language"]: x["passed"] for x in profiles},
            "profile_count": len(profiles),
            "all_profiles_passed": bool(profiles) and all(x["passed"] for x in profiles),
        }
    return {"by_profile": by_profile, "steps_6_7_to_6_11": step_results}


PROFILE_SPECS_BY_KEY = {
    f"{lang}/{profile}": {"step": step}
    for (lang, profile), (step, _family) in PROFILE_SPECS.items()
}


def _check_preservation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_rows = [row for row in rows if row.get("preservation")]
    valid = 0
    failure_examples = []
    for row in candidate_rows:
        check = row["preservation"]
        if check["valid"] and check["payload_matches"] and check["no_assertions"]:
            valid += 1
        elif len(failure_examples) < 10:
            failure_examples.append({"case_id": row["case_id"], "preservation": check})
    ratio = valid / len(candidate_rows) if candidate_rows else 0.0
    return {
        "candidate_results": len(candidate_rows),
        "lossless_opaque_preservation_rate": ratio,
        "zero_canonical_assertion_emission": all(
            row["preservation"]["no_assertions"] for row in candidate_rows
        ),
        "preservation_integrity_passed": bool(candidate_rows) and valid == len(candidate_rows),
        "semantic_assertion_projection_accepted": False,
        "status": "PRESERVATION_ONLY" if candidate_rows and valid == len(candidate_rows) else "OPEN",
        "failure_examples": failure_examples,
        "limitation": "OPAQUE preservation is verified; mapping candidate graphs to canonical semantic assertions is not accepted.",
    }


def _check_integration(seed_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    app = USGApplication(":memory:")
    try:
        checks = {}
        for lang in ("en", "ar"):
            seed = seed_rows[lang][0]
            status, response = app.dispatch("POST", "/v3/phase6/interpret", {
                "source": seed["text"], "language": lang, "persist": True,
            })
            checks[f"{lang}_api"] = status == 200 and isinstance(response.get("interpretation"), dict)
            metadata = response.get("persistence", {}) if isinstance(response, dict) else {}
            run_id = metadata.get("run_id")
            checks[f"{lang}_sqlite_persistence"] = bool(run_id)
            if run_id:
                replay_status, replay = app.dispatch(
                    "POST", f"/v3/phase6/runs/{run_id}/replay", {}
                )
                checks[f"{lang}_deterministic_replay"] = (
                    replay_status == 200 and replay.get("deterministic_match") is True
                )
            else:
                checks[f"{lang}_deterministic_replay"] = False
        return {
            "checks": checks,
            "passed": all(checks.values()),
            "status": "ACCEPTED" if all(checks.values()) else "OPEN",
            "note": "This verifies the shared API path, existing SQLite run persistence, and replay. The repository's CLI and Kernel Lab regressions are additionally run by the acceptance workflow.",
        }
    finally:
        app.close()


def run_acceptance(corpus: dict[str, Any] | None = None) -> dict[str, Any]:
    corpus = corpus or build()
    validate(corpus)
    frozen_seed_corpus = load_and_validate()
    seed_rows = {
        lang: [case for case in frozen_seed_corpus["cases"]
               if case["language"] == lang and case["gold_class"] == "POSITIVE"]
        for lang in ("en", "ar")
    }
    app = USGApplication(":memory:")
    rows = []
    started = perf_counter()
    try:
        for case in corpus["cases"]:
            status, response = app.dispatch("POST", "/v3/phase6/interpret", {
                "source": case["text"], "language": case["language"], "persist": False,
            })
            if status != 200:
                raise RuntimeError(f"integrated interpreter API failed for {case['id']}: {status} {response}")
            observation = _graph_observation(response, case["text"])
            interpretation = observation["interpretation"]
            preservation = None
            projection = response.get("canonical_preservation_projection")
            if projection:
                document = projection.get("document") or {}
                payload = document.get("extensions", {}).get("org.wizekin.usg.phase6", {})
                preservation = {
                    "valid": projection.get("status") == "LOSSLESS_PRESERVATION_ONLY"
                            and projection.get("validation", {}).get("completion_status") == "VALID",
                    "payload_matches": payload.get("graph") == interpretation.get("composition", {}).get("graph"),
                    "no_assertions": document.get("assertions") == []
                                    and projection.get("semantic_assertions_emitted") is False
                                    and document.get("expressions", [{}])[0].get("op") == "OPAQUE",
                }
            rows.append({
                "case_id": case["id"],
                "step": case["step"],
                "language": case["language"],
                "gold_class": case["gold_class"],
                "phase6_status": interpretation.get("status"),
                "diagnostics": [
                    item.get("code", item.get("message", str(item)))
                    if isinstance(item, dict) else str(item)
                    for item in interpretation.get("diagnostics", [])
                ][:12],
                "observation": observation,
                "preservation": preservation,
            })
    finally:
        app.close()
    elapsed_ms = round((perf_counter() - started) * 1000, 3)

    # Step 6.6 remains a separate bounded nominal-reference gate. Its score is
    # not pooled with the new composition/construction benchmark.
    step66 = run_step_6_6()["report"]["evaluation"]
    evaluation = _evaluate_corpus(corpus, rows)
    step12 = _check_preservation(rows)
    step13 = _check_integration(seed_rows)
    step_results = dict(evaluation["steps_6_7_to_6_11"])
    step_results["6.12"] = {
        "status": step12["status"],
        "preservation_integrity_passed": step12["preservation_integrity_passed"],
        "semantic_assertion_projection_accepted": False,
    }
    step_results["6.13"] = {
        "status": step13["status"],
        "checks": step13["checks"],
    }
    all_prior = all(item.get("status") == "ACCEPTED" for item in step_results.values())
    step_results["6.14"] = {
        "status": "ACCEPTED" if all_prior else "OPEN",
        "all_prior_acceptance_gates_passed": all_prior,
        "reason": None if all_prior else "One or more construction or integration gates remain open.",
    }
    return {
        "benchmark_id": corpus["benchmark_id"],
        "benchmark_version": corpus["version"],
        "evaluation_scope": corpus["scope"],
        "license": corpus["license"],
        "corpus_sha256": corpus_sha256(corpus),
        "case_count": len(corpus["cases"]),
        "profile_count": len(corpus["construction_inventory"]),
        "factory_execution_status": "COMPLETED",
        "factory_execution_ms": elapsed_ms,
        "generation_independence": corpus["generation"],
        "step_6_6_bounded_synthetic_gate": {
            "passed": step66["all_synthetic_profile_gates_passed"],
            "profile_count": step66["profile_count"],
            "naturalistic_accuracy_claimed": False,
        },
        "steps": step_results,
        "profile_evaluations": evaluation["by_profile"],
        "step_6_12_projection_boundary": step12,
        "step_6_13_integration": step13,
        "phase6_final_acceptance": "ACCEPTED" if all(
            value.get("status") == "ACCEPTED" for value in step_results.values()
        ) else "OPEN",
        "capability_claim_policy": {
            "candidate_only_results_promoted": False,
            "synthetic_accuracy_claimed_as_naturalistic": False,
            "unsupported_constructions_marked_accepted": False,
            "human_annotations_required": False,
        },
        "case_results": [
            {key: value for key, value in row.items() if key != "observation"}
            for row in rows
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-output", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    corpus = build()
    report = run_acceptance(corpus)
    args.corpus_output.parent.mkdir(parents=True, exist_ok=True)
    args.corpus_output.write_text(
        json.dumps(corpus, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "factory_execution_status": report["factory_execution_status"],
        "case_count": report["case_count"],
        "profile_count": report["profile_count"],
        "phase6_final_acceptance": report["phase6_final_acceptance"],
        "steps": report["steps"],
        "report_path": str(args.output),
        "corpus_path": str(args.corpus_output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    # CI validates that the factory runs and emits evidence. The Phase 6
    # acceptance state is data, not a process failure: OPEN is an honest result.
    return 0 if report["factory_execution_status"] == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
