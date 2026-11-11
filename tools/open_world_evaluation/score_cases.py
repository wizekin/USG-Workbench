"""Structural validation and oracle-aware scoring for OW execution records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .validate_protocol import OUTCOMES, validate_instance

ROOT = Path(__file__).resolve().parents[2]
SEM_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
SCORE_SCHEMA_PATH = ROOT / "tools" / "open_world_evaluation" / "schemas" / "score-result.schema.json"
MAX_RECORDS = 100_000


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _walk_span_nodes(value: Any, source_text: str, source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key in ("sourceSpan", "span"):
            span = value.get(key)
            if isinstance(span, dict):
                start, end = span.get("start"), span.get("end")
                if not _is_int(start) or not _is_int(end):
                    errors.append(f"{key} start/end must be integer offsets")
                elif start < 0 or end <= start or end > len(source_text):
                    errors.append(f"{key} [{start}, {end}) is outside the source")
                else:
                    surface = next(
                        (span.get(name) for name in ("surface", "quote", "surfaceText")
                         if isinstance(span.get(name), str)),
                        None,
                    )
                    if surface is not None and source_text[start:end] != surface:
                        errors.append(f"{key} surface does not match source offsets")
                source_ref = span.get("sourceRef")
                if source_ref is not None and source_ref not in source_ids:
                    errors.append(f"{key} references unknown source {source_ref!r}")
        for key, child in value.items():
            if key in {"sourceSpan", "span"}:
                continue
            errors.extend(_walk_span_nodes(child, source_text, source_ids))
    elif isinstance(value, list):
        for child in value:
            errors.extend(_walk_span_nodes(child, source_text, source_ids))
    return errors


def _phase4_checks(case: dict[str, Any], target_result: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    text = case["input"]["text"]
    expected_language = case["input"].get("language_hint", "en")
    if expected_language not in {"en", "ar"}:
        expected_language = "en" if expected_language in {"en-ar", "unknown"} else "ar"

    checks["contract"] = target_result.get("pipeline_contract") == "USG-INTERPRET/0.1.0"
    document = target_result.get("document")
    if not isinstance(document, dict):
        checks.update({
            "document_schema": False,
            "source_preservation": False,
            "source_hash": False,
            "source_spans": False,
            "graph_references": False,
        })
        return checks

    try:
        schema = json.loads(SEM_SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(document))
        checks["document_schema"] = not errors
    except (OSError, json.JSONDecodeError, ValueError):
        checks["document_schema"] = False

    sources = document.get("sources", [])
    matching_sources = [
        source for source in sources
        if isinstance(source, dict) and source.get("text") == text
    ]
    checks["source_preservation"] = bool(matching_sources) and (
        document.get("primarySourceRef") in {source.get("id") for source in sources}
    )
    expected_digest = _sha256(text.encode("utf-8"))
    checks["source_hash"] = any(
        source.get("textHash") == expected_digest for source in matching_sources
    )
    source_ids = {
        source.get("id") for source in sources
        if isinstance(source, dict) and isinstance(source.get("id"), str)
    }
    span_errors = _walk_span_nodes(document, text, source_ids)
    checks["source_spans"] = not span_errors
    expression_ids = {
        item.get("id") for item in document.get("expressions", [])
        if isinstance(item, dict)
    }
    refs_valid = all(
        ref in expression_ids
        for ref in document.get("rootExpressionRefs", [])
    )
    for expression in document.get("expressions", []):
        if isinstance(expression, dict):
            refs_valid = refs_valid and all(
                ref in expression_ids for ref in expression.get("operandRefs", [])
            )
    checks["graph_references"] = bool(refs_valid)
    return checks


def _phase5_checks(case: dict[str, Any], target_result: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    text = case["input"]["text"]
    checks["contract"] = target_result.get("pipeline_contract") == "USG-INTERPRET/0.2.0"
    source = target_result.get("source")
    checks["source_preservation"] = isinstance(source, dict) and source.get("text") == text
    expected_digest = _sha256(text.encode("utf-8"))
    checks["source_hash"] = (
        isinstance(source, dict)
        and source.get("sha256") == expected_digest
        and target_result.get("source_sha256") == expected_digest
    )
    manifest = target_result.get("resource_manifest_digest")
    checks["resource_manifest"] = (
        isinstance(manifest, str) and len(manifest) == 64
        and all(char in "0123456789abcdef" for char in manifest)
    )
    stages = target_result.get("stages")
    checks["stage_completeness"] = isinstance(stages, dict) and all(
        stage in stages for stage in (
            "lexical", "segmentation", "operators", "syntax",
            "semantic_composition", "discourse",
        )
    )
    span_errors: list[str] = []
    token_ids: set[str] = set()
    if checks["stage_completeness"]:
        lexical = stages["lexical"].get("artifact", {})
        tokens = lexical.get("tokens", []) if isinstance(lexical, dict) else []
        for item in tokens:
            token = item.get("token", {}) if isinstance(item, dict) else {}
            token_id = token.get("token_id")
            start, end = token.get("start"), token.get("end")
            surface = token.get("surface_text")
            if isinstance(token_id, str):
                token_ids.add(token_id)
            if not _is_int(start) or not _is_int(end):
                span_errors.append("token offsets must be integers")
            elif start < 0 or end <= start or end > len(text):
                span_errors.append(f"token span [{start}, {end}) is outside source")
            elif isinstance(surface, str) and text[start:end] != surface:
                span_errors.append("token surface does not match source offsets")
        syntax = stages["syntax"].get("artifact", {})
        clauses = syntax.get("clauses", []) if isinstance(syntax, dict) else []
        for clause in clauses:
            for candidate in clause.get("candidates", []):
                for role, token_id in candidate.get("role_token_refs", []):
                    if token_id not in token_ids:
                        span_errors.append(f"role {role} references unknown token {token_id}")
    checks["source_spans_and_token_refs"] = not span_errors
    status = target_result.get("completion_status")
    checks["completion_status_known"] = status in {
        "COMPLETE", "UNSUPPORTED", "AMBIGUOUS", "PARTIAL",
        "INCOMPLETE_RESOURCE_LIMIT",
    }
    checks["no_truth_promotion"] = (
        target_result.get("safety", {}).get("truth_promotion") is False
    )
    return checks


def _phase5_predictions(target_result: dict[str, Any]) -> tuple[str | None, dict[str, str], dict[str, Any]]:
    """Project the single accepted Phase 5 syntax candidate into benchmark fields."""
    stages = target_result.get("stages", {})
    lexical = stages.get("lexical", {}).get("artifact", {})
    syntax = stages.get("syntax", {}).get("artifact", {})
    semantic = stages.get("semantic_composition", {}).get("artifact", {})
    token_by_id = {}
    for item in lexical.get("tokens", []) if isinstance(lexical, dict) else []:
        token = item.get("token", {}) if isinstance(item, dict) else {}
        if isinstance(token.get("token_id"), str):
            token_by_id[token["token_id"]] = token

    syntax_candidates = [
        candidate
        for clause in syntax.get("clauses", []) if isinstance(clause, dict)
        for candidate in clause.get("candidates", []) if isinstance(candidate, dict)
    ] if isinstance(syntax, dict) else []
    semantic_candidates = semantic.get("candidates", []) if isinstance(semantic, dict) else []
    if not (
        target_result.get("completion_status") == "COMPLETE"
        and semantic.get("status") == "COMPOSED"
        and len(semantic_candidates) == 1
        and len(syntax_candidates) == 1
    ):
        return None, {}, {}

    candidate = syntax_candidates[0]
    construction_id = candidate.get("construction_id")
    role_bindings: dict[str, str] = {}
    role_spans: dict[str, Any] = {}
    for row in candidate.get("role_token_refs", []):
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            continue
        role, token_id = row
        token = token_by_id.get(token_id)
        if not isinstance(token, dict):
            continue
        role_bindings[str(role)] = str(token.get("surface_text", ""))
        role_spans[str(role)] = {
            "start": token.get("start"),
            "end": token.get("end"),
            "surface": token.get("surface_text"),
        }
    return construction_id, role_bindings, role_spans


def _diagnostic_oracle_metrics(
    case: dict[str, Any],
    target_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Score only explicit gold expectations in a controlled diagnostic fixture."""
    oracle = case.get("oracle", {})
    expected = oracle.get("expected")
    if not isinstance(expected, dict) or oracle.get("independent") is not True:
        return []
    oracle_id = oracle.get("oracle_id")
    if not isinstance(oracle_id, str) or not oracle_id:
        return []

    def metric(metric_id: str, matched: bool, notes: str) -> dict[str, Any]:
        return {
            "metric_id": metric_id,
            "method": "exact_match",
            "value": 1.0 if matched else 0.0,
            "oracle_id": oracle_id,
            "oracle_independent": True,
            "notes": notes,
        }

    metrics: list[dict[str, Any]] = []
    target_id = case.get("target", {}).get("component_id")
    if target_id == "phase4-bounded-interpreter":
        actual_status = target_result.get("completion_status")
        if expected.get("expected_completion_status") is not None:
            metrics.append(metric(
                "phase4_completion_status_exact",
                actual_status == expected["expected_completion_status"],
                "Exact completion-status comparison against the imported v0.1.0 fixture.",
            ))
        if expected.get("expected_expression_count") is not None:
            document = target_result.get("document", {})
            actual_count = len(document.get("expressions", [])) if isinstance(document, dict) else -1
            metrics.append(metric(
                "phase4_expression_count_exact",
                actual_count == expected["expected_expression_count"],
                "Exact expression count comparison against the imported v0.1.0 fixture.",
            ))
    elif target_id == "phase5-bounded-interpreter":
        predicted_construction, predicted_roles, predicted_spans = _phase5_predictions(target_result)
        if "expected_completion_status" in expected and expected["expected_completion_status"] is not None:
            metrics.append(metric(
                "phase5_completion_status_exact",
                target_result.get("completion_status") == expected["expected_completion_status"],
                "Exact completion-status comparison where the v0.2.1 corpus defines one.",
            ))
        if "expected_construction" in expected:
            metrics.append(metric(
                "phase5_construction_exact",
                predicted_construction == expected["expected_construction"],
                "Exact construction/abstention comparison against the v0.2.1 corpus.",
            ))
        if expected.get("gold_class") == "POSITIVE":
            metrics.append(metric(
                "phase5_role_bindings_exact",
                predicted_roles == expected.get("expected_roles", {}),
                "Exact AGENT/ACTION/PATIENT role-binding comparison.",
            ))
            metrics.append(metric(
                "phase5_role_spans_exact",
                predicted_spans == expected.get("expected_role_spans", {}),
                "Exact Unicode-code-point source-span comparison.",
            ))
        elif expected.get("gold_class") in {"NEGATIVE", "AMBIGUOUS"}:
            metrics.append(metric(
                "phase5_nonpositive_abstention",
                predicted_construction is None,
                "A unique semantic construction must not be emitted for negative/ambiguous target-class fixtures.",
            ))
    return metrics


def score_pair(case: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """Create a score record; semantic correctness requires an independent oracle."""
    case_errors = validate_instance("scenario", case)
    record_errors = validate_instance("execution_result", record)
    identity_checks = {
        "case_id_matches": case.get("case_id") == record.get("case_id"),
        "target_matches": (
            case.get("target", {}).get("component_id")
            == record.get("target", {}).get("component_id")
            and case.get("target", {}).get("component_version")
            == record.get("target", {}).get("component_version")
            and case.get("target", {}).get("entry_point")
            == record.get("target", {}).get("entry_point")
        ),
    }

    payload = record.get("capture", {}).get("inline_output")
    capture = record.get("capture", {})
    digest_check: bool | None = None
    if payload is not None:
        digest_check = _sha256(_canonical_bytes(payload)) == capture.get("output_sha256")

    structural_checks: dict[str, bool | None] = {
        "scenario_protocol_valid": not case_errors,
        "execution_record_valid": not record_errors,
        **identity_checks,
        "output_digest_valid": digest_check,
        "outcome_consistent": (
            isinstance(payload, dict)
            and payload.get("outcome") == record.get("outcome")
        ) if payload is not None else None,
        "contract": None,
        "source_preservation": None,
        "source_hash": None,
        "document_schema": None,
        "resource_manifest": None,
        "stage_completeness": None,
        "source_spans": None,
        "graph_references": None,
        "completion_status_known": None,
        "no_truth_promotion": None,
    }
    target_id = case.get("target", {}).get("component_id")
    target_result = payload.get("target_result") if isinstance(payload, dict) else None
    if isinstance(target_result, dict):
        if target_id == "phase4-bounded-interpreter":
            specialized = _phase4_checks(case, target_result)
            structural_checks.update(specialized)
        elif target_id == "phase5-bounded-interpreter":
            specialized = _phase5_checks(case, target_result)
            structural_checks.update(specialized)
        else:
            structural_checks["contract"] = None
    else:
        structural_checks["contract"] = None

    applicable = [value for value in structural_checks.values() if value is not None]
    failed = [key for key, value in structural_checks.items() if value is False]
    if record_errors or case_errors:
        status = "invalid"
    elif record.get("outcome") == "not_executed":
        status = "not_applicable"
    elif failed:
        status = "invalid"
    elif applicable and all(value is True for value in applicable):
        status = "valid"
    else:
        status = "not_checked"

    oracle = case.get("oracle", {})
    oracle_metrics = (
        _diagnostic_oracle_metrics(case, target_result)
        if isinstance(target_result, dict) else []
    )
    if oracle_metrics:
        oracle_status = "scored"
    elif oracle.get("type") == "none" or oracle.get("independent") is not True:
        oracle_status = "not_scored_no_independent_oracle"
    elif oracle.get("type") == "human_rubric":
        oracle_status = "requires_independent_human_rubric_review"
    else:
        oracle_status = "oracle_declared_but_no_case_specific_adapter"

    return {
        "schema_version": "1.0.0",
        "score_id": "OWS-" + _sha256(
            (case.get("case_id", "") + ":" + record.get("attempt_id", "")).encode("utf-8")
        )[:24].upper(),
        "case_id": case.get("case_id", "unknown"),
        "attempt_id": record.get("attempt_id", "unknown"),
        "population": case.get("population", "unconstrained_random"),
        "target": record.get("target", {}),
        "tested_commit_sha": record.get("target", {}).get("commit_sha"),
        "outcome": record.get("outcome", "not_executed"),
        "structural_status": status,
        "structural_checks": structural_checks,
        "failed_checks": failed,
        "case_validation_errors": case_errors,
        "record_validation_errors": record_errors,
        "semantic_scoring": {
            "status": oracle_status,
            "oracle_type": oracle.get("type", "none"),
            "oracle_id": oracle.get("oracle_id"),
            "independent": oracle.get("independent") is True,
            "metrics": oracle_metrics,
        },
        "limitations": [
            "Structural validity is not semantic correctness, factual truth, or general language understanding.",
            "No semantic score is assigned without an independent case-specific oracle adapter.",
        ],
    }


def load_jsonl(path: Path, *, max_records: int = MAX_RECORDS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"record at {path}:{line_number} must be a JSON object")
            rows.append(row)
            if len(rows) > max_records:
                raise ValueError(f"{path} exceeds maximum {max_records} records")
    return rows


def score_files(
    cases_path: Path,
    results_path: Path,
    scores_path: Path,
    summary_path: Path,
) -> dict[str, Any]:
    if scores_path.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite existing score output or summary")
    cases = load_jsonl(cases_path)
    results = load_jsonl(results_path)
    cases_by_id = {case.get("case_id"): case for case in cases}
    if len(cases_by_id) != len(cases):
        raise ValueError("scenario input contains duplicate case_id values")
    seen: set[str] = set()
    scores: list[dict[str, Any]] = []
    for record in results:
        case_id = record.get("case_id")
        if case_id not in cases_by_id:
            raise ValueError(f"execution result references unknown case_id: {case_id}")
        attempt_id = record.get("attempt_id")
        if attempt_id in seen:
            raise ValueError(f"duplicate execution attempt_id: {attempt_id}")
        seen.add(attempt_id)
        scores.append(score_pair(cases_by_id[case_id], record))

    population_counts: dict[str, Counter[str]] = defaultdict(Counter)
    target_counts: dict[str, Counter[str]] = defaultdict(Counter)
    structural_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for score in scores:
        population_counts[score["population"]][score["outcome"]] += 1
        target_counts[score["target"]["component_id"]][score["outcome"]] += 1
        structural_counts[score["population"]][score["structural_status"]] += 1

    summary = {
        "summary_version": "1.0.0",
        "created_at": _utc_now(),
        "scenario_count": len(cases),
        "result_count": len(results),
        "scored_count": len(scores),
        "unexecuted_scenario_count": len(cases) - len({row["case_id"] for row in results}),
        "outcome_counts": dict(Counter(row["outcome"] for row in scores)),
        "structural_status_counts": dict(Counter(row["structural_status"] for row in scores)),
        "semantic_scored_count": sum(
            bool(row["semantic_scoring"]["metrics"]) for row in scores
        ),
        "semantic_unscored_count": sum(
            not row["semantic_scoring"]["metrics"] for row in scores
        ),
        "by_population": {
            population: {
                "outcomes": dict(outcomes),
                "structural_status": dict(structural_counts[population]),
            }
            for population, outcomes in sorted(population_counts.items())
        },
        "by_target": {
            target: dict(outcomes)
            for target, outcomes in sorted(target_counts.items())
        },
        "known_limitations": [
            "Unexecuted scenarios remain visible in unexecuted_scenario_count.",
            "Structural checks are interface-specific and do not imply semantic correctness.",
            "Semantic scoring remains empty until an independent case-specific oracle adapter is registered.",
        ],
    }

    scores_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with scores_path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in scores:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with summary_path.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate OW execution records and assign oracle-aware structural scores."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = score_files(args.cases, args.results, args.scores, args.summary)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
