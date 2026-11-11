"""Validate OW-1 Open-World Evaluation protocol schemas and records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "tools" / "open_world_evaluation" / "schemas"
SCHEMA_FILES = {
    "source": "source-provenance.schema.json",
    "scenario": "scenario.schema.json",
    "execution_result": "execution-result.schema.json",
    "campaign_report": "campaign-report.schema.json",
}
OUTCOMES = (
    "completed", "unsupported", "ambiguous", "abstained", "partial",
    "invalid_output", "timeout", "crashed", "infrastructure_error",
    "not_executed",
)
POPULATIONS = (
    "unconstrained_random", "naturalistic", "controlled_diagnostic",
)
LICENSED_SOURCE_KINDS = {
    "open_license_dataset", "public_domain", "public_documentation",
}


def load_schemas() -> dict[str, dict[str, Any]]:
    schemas = {
        key: json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        for key, filename in SCHEMA_FILES.items()
    }
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    return schemas


def _schema_errors(kind: str, instance: dict[str, Any]) -> list[str]:
    schema = json.loads(
        (SCHEMA_DIR / SCHEMA_FILES[kind]).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    return [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in errors
    ]


def _source_policy_errors(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("kind") in LICENSED_SOURCE_KINDS:
        for field in ("source_url", "retrieved_at", "license_status",
                      "redistribution_allowed", "privacy_review_status"):
            if field not in source:
                errors.append(f"naturalistic source is missing {field}")
        if source.get("license_status") != "approved":
            errors.append("public source license_status must be approved")
        if source.get("redistribution_allowed") is not True:
            errors.append("public source must explicitly permit redistribution")
        if source.get("privacy_review_status") != "approved":
            errors.append("public source must pass privacy review")
    return errors


def validate_instance(kind: str, instance: dict[str, Any]) -> list[str]:
    if kind not in SCHEMA_FILES:
        raise ValueError(f"unknown protocol record kind: {kind}")
    errors = _schema_errors(kind, instance)
    if errors:
        return errors

    if kind == "source":
        errors.extend(_source_policy_errors(instance))
    elif kind == "scenario":
        errors.extend(_source_policy_errors(instance["source"]))
        if instance["population"] == "naturalistic":
            if instance["source"].get("kind") not in LICENSED_SOURCE_KINDS:
                errors.append("naturalistic population requires a public/licensed source kind")
        if instance["population"] == "controlled_diagnostic":
            oracle = instance["oracle"]
            if oracle["type"] == "none" or oracle["independent"] is not True:
                errors.append("controlled diagnostic cases require an independent non-empty oracle")
        actual_digest = hashlib.sha256(
            instance["input"]["text"].encode("utf-8")
        ).hexdigest()
        if instance["input"]["utf8_sha256"] != actual_digest:
            errors.append("input.utf8_sha256 does not match the exact UTF-8 input text")

    return errors


def validate_campaign_report(instance: dict[str, Any]) -> list[str]:
    errors = validate_instance("campaign_report", instance)
    if errors:
        return errors

    outcomes = instance["outcome_counts"]
    total = sum(outcomes.values())
    if total != instance["attempted"]:
        errors.append(
            f"attempted ({instance['attempted']}) does not equal outcome total ({total})"
        )
    if instance["completed"] != outcomes["completed"]:
        errors.append("campaign completed does not equal outcome_counts.completed")

    population_rows = instance["population_results"]
    seen = [row["population"] for row in population_rows]
    if len(set(seen)) != len(seen) or set(seen) != set(POPULATIONS):
        errors.append("population_results must contain each population exactly once")

    population_total = 0
    population_outcomes = {key: 0 for key in OUTCOMES}
    for row in population_rows:
        row_total = sum(row["outcome_counts"].values())
        if row_total != row["attempted"]:
            errors.append(
                f"{row['population']} attempted does not equal its outcome total"
            )
        if row["completed"] != row["outcome_counts"]["completed"]:
            errors.append(
                f"{row['population']} completed does not equal its completed outcome count"
            )
        population_total += row["attempted"]
        for key in OUTCOMES:
            population_outcomes[key] += row["outcome_counts"][key]

    if population_total != instance["attempted"]:
        errors.append("population attempts do not reconcile with campaign attempted")
    if population_outcomes != outcomes:
        errors.append("population outcome totals do not reconcile with campaign outcome_counts")
    if instance["status"] == "complete" and (
        instance["finished_at"] is None or instance["attempted"] == 0
    ):
        errors.append("complete campaign requires a finish time and at least one attempt")

    return errors


def main() -> int:
    try:
        schemas = load_schemas()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"OW-1 protocol validation failed: {exc}")
        return 1
    print(
        "OW-1 protocol schemas valid: "
        + ", ".join(f"{key}={schema.get('title', key)}" for key, schema in schemas.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
