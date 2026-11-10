"""Static validator for the declarative USG Rule Registry v1.0.0.

This module validates registry data only. It never loads or executes rule behavior.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "rules" / "semantic-reasoning" / "v1.0.0"
DEFAULT_REGISTRY = PACKAGE / "registry.json"
DEFAULT_SCHEMA = PACKAGE / "registry.schema.json"
DEFAULT_FIXTURES = ROOT / "benchmarks" / "semantic-reasoning" / "v1.0.0" / "fixtures.json"


class RegistryValidationError(ValueError):
    """Raised when registry data violates the static registry contract."""


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def validate_registry(
    registry: dict[str, Any] | None = None,
    fixtures: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry if registry is not None else _load(DEFAULT_REGISTRY)
    fixtures = fixtures if fixtures is not None else _load(DEFAULT_FIXTURES)
    schema = schema if schema is not None else _load(DEFAULT_SCHEMA)

    errors: list[str] = []
    validator = Draft202012Validator(schema)
    errors.extend(
        f"schema: {error.json_path}: {error.message}"
        for error in sorted(validator.iter_errors(registry), key=lambda item: item.json_path)
    )
    if errors:
        raise RegistryValidationError("; ".join(errors))

    fixture_map = {fixture["id"]: fixture for fixture in fixtures["fixtures"]}
    seen: set[tuple[str, str]] = set()
    registered_versions: dict[tuple[str, str], dict[str, Any]] = {}

    if registry["execution_enabled"] is not False:
        errors.append("registry execution must remain disabled in Step 2.3")

    for rule in registry["rules"]:
        identity = (rule["rule_id"], rule["version"])
        if identity in seen:
            errors.append(f"duplicate rule identity/version: {identity[0]}@{identity[1]}")
        seen.add(identity)
        registered_versions[identity] = rule

        if rule["activation_state"] != "SPECIFIED_NOT_EXECUTABLE":
            errors.append(f"{identity[0]} must remain SPECIFIED_NOT_EXECUTABLE")

        variable_names = {item["name"] for item in rule["variables"]}
        for premise in rule["premises"]:
            for field, variable in premise["match"]["field_bindings"].items():
                if variable not in variable_names:
                    errors.append(
                        f"{identity[0]} premise {premise['premise_id']} binds undeclared variable {variable!r} at {field}"
                    )

        for conclusion in rule["conclusion_templates"]:
            for value in _walk_strings(conclusion["template"]):
                if value.startswith("$") and value[1:] not in variable_names:
                    errors.append(
                        f"{identity[0]} conclusion {conclusion['template_id']} uses undeclared variable {value}"
                    )
            if conclusion["truth_promotion"] is not False:
                errors.append(f"{identity[0]} must not promote truth")

        coverage_types: dict[str, set[str]] = {}
        for coverage in rule["test_coverage"]:
            fixture_id = coverage["fixture_id"]
            if fixture_id not in fixture_map:
                errors.append(f"{identity[0]} references unknown benchmark fixture {fixture_id}")
                continue
            declared_types = set(fixture_map[fixture_id]["case_types"])
            if coverage["expectation"] not in declared_types:
                errors.append(
                    f"{identity[0]} coverage expectation {coverage['expectation']} "
                    f"not declared by fixture {fixture_id}"
                )
            coverage_types.setdefault(coverage["expectation"], set()).add(fixture_id)

        if "positive" not in coverage_types:
            errors.append(f"{identity[0]} requires at least one positive benchmark fixture")
        if not ({"negative", "boundary", "adversarial", "unsupported", "unresolved"} & coverage_types.keys()):
            errors.append(f"{identity[0]} requires negative, boundary, or adversarial benchmark coverage")

        world = rule["assumptions"]["world_assumption"]
        if world == "EXPLICIT_CLOSED_COMPLETE_ONLY":
            if not rule["assumptions"]["closed_domain_policy_required"]:
                errors.append(f"{identity[0]} closed-world rule must require an explicit policy")
            if not rule["assumptions"]["closed_domain_policy_ref"]:
                errors.append(f"{identity[0]} closed-world rule must name its task policy reference")
            required_constraints = {"domain_closed", "domain_complete", "absence_within_domain"}
            actual_constraints = {item["kind"] for item in rule["constraints"]}
            missing = required_constraints - actual_constraints
            if missing:
                errors.append(f"{identity[0]} closed-world rule missing constraints: {sorted(missing)}")
            if rule["scope_context_requirements"]["world_assumption"] != "EXPLICIT_CLOSED_COMPLETE_ONLY":
                errors.append(f"{identity[0]} scope policy must explicitly require a closed complete domain")
        elif rule["assumptions"]["closed_domain_policy_required"]:
            errors.append(f"{identity[0]} declares a closed-domain policy requirement under an OPEN rule")

    for fixture in fixtures["fixtures"]:
        for benchmark_rule in fixture["task"]["reference_policy"]["rules"]:
            identity = (benchmark_rule["id"], benchmark_rule["version"])
            if identity not in registered_versions:
                errors.append(
                    f"benchmark fixture {fixture['id']} references unregistered rule "
                    f"{identity[0]}@{identity[1]}"
                )

    if registry["governance"]["automatic_truth_promotion_forbidden"] is not True:
        errors.append("automatic truth promotion must remain forbidden")
    if registry["governance"]["implicit_closed_world_forbidden"] is not True:
        errors.append("implicit closed-world assumptions must remain forbidden")
    if registry["governance"]["semantic_truncation_forbidden"] is not True:
        errors.append("semantic truncation must remain forbidden")

    if errors:
        raise RegistryValidationError("; ".join(errors))

    return {
        "valid": True,
        "registry_id": registry["registry_id"],
        "registry_version": registry["registry_version"],
        "rule_count": len(registry["rules"]),
        "execution_enabled": False,
        "validated_rule_ids": sorted(rule["rule_id"] for rule in registry["rules"]),
        "benchmark_fixture_count": len(fixture_map),
    }


def main() -> int:
    try:
        report = validate_registry()
    except (OSError, json.JSONDecodeError, RegistryValidationError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
