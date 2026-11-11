"""Validate the OW-0 machine-readable repository inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = Path("documentation/USG-OPEN-WORLD-CAPABILITY-INVENTORY.json")

COMPONENT_STATUSES = {
    "historical_baseline",
    "model_only",
    "implemented_regression_tested",
    "bounded_benchmark_enabled",
    "partial_candidate_only",
}
CAPABILITY_STATES = {
    "implemented_regression_tested",
    "bounded",
    "bounded_benchmark_enabled",
    "model_contract_only",
    "partial_candidate",
    "not_canonical",
}


def _exists(root: Path, relative_path: Any) -> bool:
    return (
        isinstance(relative_path, str)
        and bool(relative_path)
        and (root / relative_path).exists()
    )


def validate_inventory(root: Path = ROOT) -> list[str]:
    """Return all inventory validation errors; an empty list means valid."""
    inventory_file = root / INVENTORY_PATH
    if not inventory_file.is_file():
        return [f"missing inventory file: {INVENTORY_PATH.as_posix()}"]

    try:
        data = json.loads(inventory_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read inventory JSON: {exc}"]

    errors: list[str] = []
    if data.get("inventory_version") != "1.0.0":
        errors.append("inventory_version must be 1.0.0")

    snapshot = data.get("snapshot")
    if not isinstance(snapshot, dict):
        errors.append("snapshot must be an object")
    else:
        for key in ("repository", "branch", "commit", "captured_at"):
            if not isinstance(snapshot.get(key), str) or not snapshot[key]:
                errors.append(f"snapshot.{key} must be a non-empty string")
        for key in (
            "tracked_tree_entries",
            "tracked_files",
            "workflow_files",
            "root_python_test_files",
            "javascript_workbench_test_files",
        ):
            value = snapshot.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"snapshot.{key} must be a non-negative integer")

    components = data.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty array")
        components = []

    component_ids: set[str] = set()
    for index, component in enumerate(components):
        prefix = f"components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue

        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif component_id in component_ids:
            errors.append(f"duplicate component id: {component_id}")
        else:
            component_ids.add(component_id)

        if component.get("status") not in COMPONENT_STATUSES:
            errors.append(f"{prefix}.status is not a recognized inventory status")

        if not _exists(root, component.get("path")):
            errors.append(f"{prefix}.path does not exist: {component.get('path')!r}")

        entry_points = component.get("entry_points")
        if not isinstance(entry_points, list) or not entry_points:
            errors.append(f"{prefix}.entry_points must be a non-empty array")
        else:
            for entry_index, entry in enumerate(entry_points):
                if not isinstance(entry, dict) or not _exists(root, entry.get("path")):
                    errors.append(
                        f"{prefix}.entry_points[{entry_index}].path does not exist"
                    )

        capabilities = component.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            errors.append(f"{prefix}.capabilities must be a non-empty array")
        else:
            for cap_index, capability in enumerate(capabilities):
                if not isinstance(capability, dict):
                    errors.append(f"{prefix}.capabilities[{cap_index}] must be an object")
                    continue
                if capability.get("state") not in CAPABILITY_STATES:
                    errors.append(
                        f"{prefix}.capabilities[{cap_index}].state is not recognized"
                    )

        evidence = component.get("evidence_paths")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence_paths must be a non-empty array")
        else:
            for evidence_path in evidence:
                if not _exists(root, evidence_path):
                    errors.append(
                        f"{prefix}.evidence path does not exist: {evidence_path!r}"
                    )

    for section in ("contracts", "benchmark_sets"):
        rows = data.get(section)
        if not isinstance(rows, list) or not rows:
            errors.append(f"{section} must be a non-empty array")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not _exists(root, row.get("path")):
                errors.append(f"{section}[{index}].path does not exist")

    resource_sets = data.get("resource_sets")
    if not isinstance(resource_sets, list) or not resource_sets:
        errors.append("resource_sets must be a non-empty array")
    else:
        for relative_path in resource_sets:
            if not _exists(root, relative_path):
                errors.append(f"resource path does not exist: {relative_path!r}")

    known_gaps = data.get("known_gaps")
    if not isinstance(known_gaps, list) or len(known_gaps) < 3:
        errors.append("known_gaps must explicitly record missing OW infrastructure")

    conclusions = data.get("inventory_conclusions")
    if not isinstance(conclusions, list) or not conclusions:
        errors.append("inventory_conclusions must be a non-empty array")

    return errors


def main() -> int:
    errors = validate_inventory()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"OW-0 inventory validation failed with {len(errors)} error(s).")
        return 1
    inventory = json.loads((ROOT / INVENTORY_PATH).read_text(encoding="utf-8"))
    print(
        "OW-0 inventory valid: "
        f"{len(inventory['components'])} components, "
        f"{len(inventory['contracts'])} contracts, "
        f"{len(inventory['resource_sets'])} resource families, "
        f"{len(inventory['benchmark_sets'])} controlled benchmark sets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
