"""Evaluate structured candidate outputs against the frozen USG benchmark.

This module is an evaluator only. It does not parse natural language, apply rules,
or generate conclusions. A future inference implementation must first normalize
its structured output into the v1.0.0 candidate-result contract.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = ROOT / "benchmarks/semantic-reasoning/v1.0.0/fixtures.json"
DEFAULT_THRESHOLDS = ROOT / "benchmarks/semantic-reasoning/v1.0.0/thresholds.json"
DEFAULT_FIXTURE_SCHEMA = ROOT / "benchmarks/semantic-reasoning/v1.0.0/fixtures.schema.json"
DEFAULT_RESULT_SCHEMA = ROOT / "benchmarks/semantic-reasoning/v1.0.0/results.schema.json"


def load_json(path: str | Path) -> Any:
    """Load UTF-8 JSON and surface path-aware parse failures."""
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load JSON from {source}: {exc}") from exc


def validate_schema(instance: Any, schema_path: str | Path) -> None:
    """Validate a JSON value using Draft 2020-12 JSON Schema."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - covered by CI dependency
        raise RuntimeError(
            'Install the schema validator with: python -m pip install "jsonschema>=4.18,<5"'
        ) from exc

    schema = load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:20]
        )
        raise ValueError(f"Schema validation failed ({len(errors)} error(s)): {detail}")


def _ratio(numerator: int, denominator: int) -> float | None:
    """Return None for an undefined metric; undefined metrics cannot pass gates."""
    if denominator == 0:
        return None
    return numerator / denominator


def _canonical(value: Any, excluded_fields: set[str]) -> Any:
    """Normalize object key order while preserving semantically meaningful list order."""
    if isinstance(value, Mapping):
        return {
            key: _canonical(item, excluded_fields)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if key not in excluded_fields
        }
    if isinstance(value, list):
        return [_canonical(item, excluded_fields) for item in value]
    if isinstance(value, tuple):
        return [_canonical(item, excluded_fields) for item in value]
    return value


def _same_json(left: Any, right: Any, excluded_fields: set[str]) -> bool:
    return _canonical(left, excluded_fields) == _canonical(right, excluded_fields)


def _indexed(items: Iterable[Mapping[str, Any]], key: str) -> tuple[dict[str, Mapping[str, Any]], set[str]]:
    index: dict[str, Mapping[str, Any]] = {}
    duplicates: set[str] = set()
    for item in items:
        identifier = item.get(key)
        if not isinstance(identifier, str) or not identifier:
            duplicates.add("<missing-or-invalid-id>")
            continue
        if identifier in index:
            duplicates.add(identifier)
        else:
            index[identifier] = item
    return index, duplicates


def _check_exact_subrecords(
    expected_items: list[Mapping[str, Any]],
    actual_items: list[Mapping[str, Any]],
    id_field: str,
    expected_field: str,
    actual_field: str,
) -> tuple[int, int]:
    """Score exact expected subrecords and penalize unrecognized extra check IDs."""
    expected_index, expected_duplicates = _indexed(expected_items, id_field)
    actual_index, actual_duplicates = _indexed(actual_items, id_field)
    extras = set(actual_index) - set(expected_index)
    total = len(expected_items) + len(extras) + len(expected_duplicates) + len(actual_duplicates)
    correct = 0
    if expected_duplicates or actual_duplicates:
        total += 1
    for check_id, expected in expected_index.items():
        actual = actual_index.get(check_id)
        if actual is None:
            continue
        if actual.get(actual_field) == expected.get(expected_field):
            correct += 1
    return correct, total


def _evaluate_derivations(
    expected_specs: list[Mapping[str, Any]],
    actual_specs: list[Mapping[str, Any]],
) -> tuple[int, int]:
    actual_index, duplicates = _indexed(actual_specs, "derivation_id")
    total = len(expected_specs) + len(duplicates)
    correct = 0
    for specification in expected_specs:
        derivation_id = specification.get("derivation_id")
        actual = actual_index.get(derivation_id)
        if actual is None or derivation_id in duplicates:
            continue
        if actual.get("conclusion_id") != specification.get("conclusion_id"):
            continue
        required_fields = specification.get("required_fields", [])
        if any(field not in actual or actual[field] is None for field in required_fields):
            continue
        expected_fields = specification.get("expected_fields", {})
        if any(actual.get(field) != value for field, value in expected_fields.items()):
            continue
        correct += 1
    return correct, total


def _gate_passes(value: float | None, operator: str, threshold: float) -> bool:
    if value is None or not math.isfinite(value):
        return False
    if operator == ">=":
        return value >= threshold
    if operator == "<=":
        return value <= threshold
    raise ValueError(f"Unsupported threshold operator: {operator}")


def evaluate(
    fixtures_payload: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    result_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    """Score a candidate-result bundle and apply the pre-inference gates."""
    errors: list[str] = []
    benchmark_id = fixtures_payload.get("benchmark_id")
    benchmark_version = fixtures_payload.get("benchmark_version")

    if thresholds.get("benchmark_id") != benchmark_id:
        errors.append("threshold benchmark_id does not match the fixture corpus")
    if thresholds.get("benchmark_version") != benchmark_version:
        errors.append("threshold benchmark_version does not match the fixture corpus")
    if result_bundle.get("benchmark_id") != benchmark_id:
        errors.append("result benchmark_id does not match the fixture corpus")
    if result_bundle.get("benchmark_version") != benchmark_version:
        errors.append("result benchmark_version does not match the fixture corpus")

    fixtures = fixtures_payload.get("fixtures", [])
    declared_count = fixtures_payload.get("fixture_count")
    if declared_count != len(fixtures):
        errors.append(
            f"fixture_count declares {declared_count!r} but corpus contains {len(fixtures)}"
        )

    fixture_index, duplicate_fixture_ids = _indexed(fixtures, "id")
    if duplicate_fixture_ids:
        errors.append(f"duplicate fixture IDs: {sorted(duplicate_fixture_ids)}")

    raw_results = result_bundle.get("results", [])
    result_index, duplicate_result_ids = _indexed(raw_results, "fixture_id")
    if duplicate_result_ids:
        errors.append(f"duplicate or invalid result fixture IDs: {sorted(duplicate_result_ids)}")

    missing_results = set(fixture_index) - set(result_index)
    unknown_results = set(result_index) - set(fixture_index)
    if missing_results:
        errors.append(f"missing fixture results: {sorted(missing_results)}")
    if unknown_results:
        errors.append(f"results reference unknown fixtures: {sorted(unknown_results)}")

    excluded = set(thresholds.get("non_semantic_repeat_fields", []))
    true_positives = false_positives = false_negatives = prohibited_emissions = 0
    scope_correct = scope_total = 0
    evidence_correct = evidence_total = 0
    provenance_correct = provenance_total = 0
    preservation_correct = preservation_total = 0
    status_correct = diagnostic_correct = determinism_correct = resource_correct = 0
    status_total = diagnostic_total = determinism_total = resource_total = 0
    category_counts: dict[str, Counter[str]] = {}

    for fixture_id, fixture in fixture_index.items():
        expected = fixture.get("expected", {})
        actual = result_index.get(fixture_id, {})
        expected_conclusions = set(expected.get("conclusions", []))
        actual_conclusions = list(actual.get("conclusions", []))
        actual_unique = set(actual_conclusions)

        tp = len(expected_conclusions & actual_unique)
        fp = len(actual_conclusions) - tp  # includes duplicate and unlisted emissions
        fn = len(expected_conclusions - actual_unique)
        prohibited = set(expected.get("prohibited_conclusions", []))
        prohibited_emissions += sum(1 for item in actual_conclusions if item in prohibited)
        true_positives += tp
        false_positives += fp
        false_negatives += fn

        category = fixture.get("category", "<uncategorized>")
        category_counts.setdefault(category, Counter())
        category_counts[category]["tp"] += tp
        category_counts[category]["expected"] += len(expected_conclusions)

        status_total += 1
        if actual.get("completion_status") == expected.get("completion_status"):
            status_correct += 1

        diagnostic_total += 1
        expected_diagnostics = sorted(expected.get("diagnostics", []))
        actual_diagnostics = sorted(actual.get("diagnostics", []))
        if expected_diagnostics == actual_diagnostics:
            diagnostic_correct += 1

        sc, st = _check_exact_subrecords(
            expected.get("scope_checks", []),
            actual.get("scope_bindings", []),
            "check_id",
            "expected_binding",
            "binding",
        )
        scope_correct += sc
        scope_total += st

        ec, et = _check_exact_subrecords(
            expected.get("evidence_checks", []),
            actual.get("evidence_assessments", []),
            "check_id",
            "expected_assessment",
            "assessment",
        )
        evidence_correct += ec
        evidence_total += et

        pc, pt = _evaluate_derivations(
            expected.get("required_derivations", []),
            actual.get("derivations", []),
        )
        provenance_correct += pc
        provenance_total += pt

        required_preserved = set(expected.get("preserved_item_ids", []))
        observed_preserved = set(actual.get("preserved_item_ids", []))
        preservation_total += len(required_preserved)
        preservation_correct += len(required_preserved & observed_preserved)

        if fixture.get("determinism_required", False):
            determinism_total += 1
            repeat_outputs = actual.get("repeat_outputs", [])
            if (
                isinstance(repeat_outputs, list)
                and len(repeat_outputs) >= 2
                and all(_same_json(repeat_outputs[0], item, excluded) for item in repeat_outputs[1:])
            ):
                determinism_correct += 1

        resource_expected = expected.get("resource_expectations")
        if resource_expected is not None:
            resource_total += 1
            resource_actual = actual.get("resource", {})
            resource_ok = (
                isinstance(resource_actual, Mapping)
                and resource_actual.get("interrupted") == resource_expected.get("expected_interrupted")
                and resource_actual.get("truncated") == resource_expected.get("expected_truncated")
                and resource_actual.get("input_item_count") == resource_expected.get("expected_input_item_count")
                and isinstance(resource_actual.get("preserved_item_count"), int)
                and resource_actual.get("preserved_item_count") >= resource_expected.get("minimum_preserved_items", 0)
                and actual.get("completion_status") == expected.get("completion_status")
                and required_preserved.issubset(observed_preserved)
            )
            if resource_ok:
                resource_correct += 1

    emitted_count = true_positives + false_positives
    expected_count = true_positives + false_negatives
    precision = _ratio(true_positives, emitted_count)
    false_inference_rate = _ratio(false_positives, emitted_count)
    if false_inference_rate is None:
        false_inference_rate = 0.0 if emitted_count == 0 else None

    category_recall = {
        category: _ratio(counts["tp"], counts["expected"])
        for category, counts in sorted(category_counts.items())
        if counts["expected"] > 0
    }
    category_recall_values = [value for value in category_recall.values() if value is not None]
    per_category_minimum = min(category_recall_values) if category_recall_values else None

    metrics = {
        "precision": precision,
        "supported_case_recall": _ratio(true_positives, expected_count),
        "false_inference_rate": false_inference_rate,
        "scope_binding_accuracy": _ratio(scope_correct, scope_total),
        "evidence_assessment_accuracy": _ratio(evidence_correct, evidence_total),
        "provenance_completeness": _ratio(provenance_correct, provenance_total),
        "preservation_accuracy": _ratio(preservation_correct, preservation_total),
        "completion_status_accuracy": _ratio(status_correct, status_total),
        "diagnostic_accuracy": _ratio(diagnostic_correct, diagnostic_total),
        "determinism_accuracy": _ratio(determinism_correct, determinism_total),
        "resource_behavior_accuracy": _ratio(resource_correct, resource_total),
        "per_category_supported_case_recall": per_category_minimum,
    }

    gate_results = []
    for gate in thresholds.get("gates", []):
        metric = gate.get("metric")
        value = metrics.get(metric)
        operator = gate.get("operator")
        required = gate.get("threshold")
        passed = (
            isinstance(required, (int, float))
            and _gate_passes(value, operator, float(required))
        )
        gate_results.append({
            "metric": metric,
            "actual": value,
            "operator": operator,
            "threshold": required,
            "passed": passed,
            "reason": gate.get("reason", ""),
        })

    accepted = not errors and bool(gate_results) and all(item["passed"] for item in gate_results)
    return {
        "benchmark_id": benchmark_id,
        "benchmark_version": benchmark_version,
        "accepted": accepted,
        "metrics": metrics,
        "category_recall": category_recall,
        "counts": {
            "fixtures": len(fixtures),
            "results": len(raw_results),
            "expected_conclusions": expected_count,
            "emitted_conclusions": emitted_count,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "prohibited_emissions": prohibited_emissions,
            "missing_results": len(missing_results),
            "unknown_results": len(unknown_results),
        },
        "gates": gate_results,
        "structural_errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score structured USG benchmark results; this tool does not run inference."
    )
    parser.add_argument("--results", required=True, help="Candidate-result JSON bundle.")
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    parser.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS))
    parser.add_argument("--fixture-schema", default=str(DEFAULT_FIXTURE_SCHEMA))
    parser.add_argument("--result-schema", default=str(DEFAULT_RESULT_SCHEMA))
    args = parser.parse_args(argv)

    try:
        fixtures = load_json(args.fixtures)
        thresholds = load_json(args.thresholds)
        results = load_json(args.results)
        validate_schema(fixtures, args.fixture_schema)
        validate_schema(results, args.result_schema)
        report = evaluate(fixtures, thresholds, results)
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"accepted": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
