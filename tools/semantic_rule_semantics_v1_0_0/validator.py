"""Static cross-validator for USG Rule Semantics v1.0.0.

This package validates specifications and references. It does not match or execute rules.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SEMANTICS_DIR = ROOT / "rules" / "semantic-reasoning" / "semantics" / "v1.0.0"
DEFAULT_CONTRACT = SEMANTICS_DIR / "contract.json"
DEFAULT_SCHEMA = SEMANTICS_DIR / "contract.schema.json"
DEFAULT_REGISTRY = ROOT / "rules" / "semantic-reasoning" / "v1.0.0" / "registry.json"
DEFAULT_REGISTRY_SCHEMA = ROOT / "rules" / "semantic-reasoning" / "v1.0.0" / "registry.schema.json"


class SemanticsValidationError(ValueError):
    """Raised when rule semantics are incomplete or inconsistent."""


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def validate_semantics(
    contract: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    registry_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract if contract is not None else _load(DEFAULT_CONTRACT)
    registry = registry if registry is not None else _load(DEFAULT_REGISTRY)
    schema = schema if schema is not None else _load(DEFAULT_SCHEMA)
    registry_schema = registry_schema if registry_schema is not None else _load(DEFAULT_REGISTRY_SCHEMA)

    errors: list[str] = []
    errors.extend(
        f"contract schema: {error.json_path}: {error.message}"
        for error in sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda item: item.json_path)
    )
    if errors:
        raise SemanticsValidationError("; ".join(errors))

    if registry["execution_enabled"] is not False or contract["execution_enabled"] is not False:
        errors.append("rule execution must remain disabled through Step 2.4")
    if contract["rule_model_version"] != registry["rule_model_version"]:
        errors.append("rule model version does not match the registry")
    if contract["registry_id"] != registry["registry_id"] or contract["registry_version"] != registry["registry_version"]:
        errors.append("registry identity/version does not match the semantics contract")
    if contract["usg_profile"] != registry["usg_profile"]:
        errors.append("USG profile does not match the registry")

    declared_kinds = set(registry_schema["$defs"]["constraint"]["properties"]["kind"]["enum"])
    defined_kinds = {item["kind"] for item in contract["constraint_semantics"]}
    if declared_kinds != defined_kinds:
        errors.append(
            f"constraint semantics coverage mismatch: missing={sorted(declared_kinds - defined_kinds)}, "
            f"extra={sorted(defined_kinds - declared_kinds)}"
        )

    catalog = {item["code"] for item in contract["diagnostic_catalog"]}
    if len(catalog) != len(contract["diagnostic_catalog"]):
        errors.append("diagnostic catalogue contains duplicate codes")
    if len({item["kind"] for item in contract["constraint_semantics"]}) != len(contract["constraint_semantics"]):
        errors.append("constraint semantics contains duplicate kinds")
    if len({item["code"] for item in contract["outcomes"]}) != len(contract["outcomes"]):
        errors.append("applicability outcomes contain duplicate codes")
    scope_axes = {item["axis"] for item in contract["scope_policies"]}
    expected_scope_axes = {"typed_identity", "context", "attribution", "polarity", "modality", "quantifier", "temporal", "roles", "definition_grounding"}
    if scope_axes != expected_scope_axes:
        errors.append(f"scope policy coverage mismatch: missing={sorted(expected_scope_axes - scope_axes)}, extra={sorted(scope_axes - expected_scope_axes)}")
    catalog_diagnostics = set()
    for item in contract["constraint_semantics"]:
        catalog_diagnostics.update(item["failure_diagnostics"])
    missing_constraint_diagnostics = catalog_diagnostics - catalog
    if missing_constraint_diagnostics:
        errors.append(f"constraint diagnostics missing from catalogue: {sorted(missing_constraint_diagnostics)}")
    used_diagnostics = set()
    for rule in registry["rules"]:
        used_diagnostics.update(rule["diagnostics"])
        used_diagnostics.update(item["failure_diagnostic"] for item in rule["constraints"])
        used_diagnostics.update(item["diagnostic"] for item in rule["non_applicability"])
        if rule["activation_state"] != "SPECIFIED_NOT_EXECUTABLE":
            errors.append(f"{rule['rule_id']} must remain SPECIFIED_NOT_EXECUTABLE")
        if rule["execution_semantics"]["matching"] != "EXACT_TYPED_MATCH_NO_COERCION":
            errors.append(f"{rule['rule_id']} must use exact typed matching without coercion")
        for premise in rule["premises"]:
            for token in premise["match"]["fixed_fields"].values():
                if token == "RULE_ELIGIBLE_ASSERTION" and token not in {
                    item["token"] for item in contract["assertion_eligibility_policies"]
                }:
                    errors.append(f"{rule['rule_id']} uses an undefined assertion eligibility token")

    missing_diagnostics = used_diagnostics - catalog
    if missing_diagnostics:
        errors.append(f"registry diagnostics missing from contract catalogue: {sorted(missing_diagnostics)}")

    outcomes = {item["code"]: item for item in contract["outcomes"]}
    if set(outcomes) != set(contract["failure_precedence"]):
        errors.append("failure precedence must include every applicability outcome exactly once")
    if outcomes["APPLICABLE"]["may_create_conclusion_candidate"] is not True:
        errors.append("only APPLICABLE may create a conclusion candidate")
    for code, outcome in outcomes.items():
        if code != "APPLICABLE" and outcome["may_create_conclusion_candidate"]:
            errors.append(f"{code} must not create a conclusion candidate")

    policies = {item["token"]: item for item in contract["assertion_eligibility_policies"]}
    if "RULE_ELIGIBLE_ASSERTION" not in policies:
        errors.append("RULE_ELIGIBLE_ASSERTION must resolve to an explicit eligibility policy")
    else:
        policy = policies["RULE_ELIGIBLE_ASSERTION"]
        if policy["allowed_epistemic_statuses"] != ["SOURCE_ASSERTED"]:
            errors.append("initial rule eligibility must remain SOURCE_ASSERTED-only")
        if policy["unknown_origin_outcome"] != "UNKNOWN":
            errors.append("unknown assertion origin must remain UNKNOWN")
        commitments = {item["commitment"]: item for item in policy["commitment_rules"]}
        if set(commitments) != {"AUTHOR", "ATTRIBUTED", "NONE"} or not commitments["ATTRIBUTED"]["require_attributed_to_ref"]:
            errors.append("commitment and attributed referent requirements must be explicit")
        if policy["inferred_premise_chaining_allowed"] or policy["verified_status_auto_promotion"]:
            errors.append("inferred chaining and verified-status auto-promotion must remain disabled")

    if contract["open_world_policy"]["default"] != "OPEN" or contract["open_world_policy"]["absence_means_negation"]:
        errors.append("open-world default and absence-not-negation invariant must remain fixed")
    if contract["conflict_policy"]["winner_selection"] != "FORBIDDEN":
        errors.append("conflict winner selection must remain forbidden")
    if contract["resource_policy"]["semantic_truncation"] or contract["resource_policy"]["drop_unprocessed_input"]:
        errors.append("resource interruption must preserve semantic content without truncation")

    if errors:
        raise SemanticsValidationError("; ".join(errors))

    return {
        "valid": True,
        "semantics_id": contract["semantics_id"],
        "semantics_version": contract["semantics_version"],
        "rule_count": len(registry["rules"]),
        "constraint_kind_count": len(defined_kinds),
        "diagnostic_count": len(catalog),
        "execution_enabled": False,
        "outcome_codes": list(contract["failure_precedence"]),
    }


def main() -> int:
    try:
        report = validate_semantics()
    except (OSError, json.JSONDecodeError, SemanticsValidationError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
