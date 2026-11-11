"""Inventory-backed coverage ledger for continuously expanding USG evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "documentation" / "USG-OPEN-WORLD-CAPABILITY-INVENTORY.json"
TARGETS_PATH = ROOT / "tools" / "open_world_evaluation" / "target_profiles.json"
SCHEMA_PATH = ROOT / "tools" / "open_world_evaluation" / "schemas" / "coverage-ledger.schema.json"
OUTCOMES = (
    "completed", "unsupported", "ambiguous", "abstained", "partial",
    "invalid_output", "timeout", "crashed", "infrastructure_error",
    "not_executed",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"record at {path}:{line_number} is not an object")
            rows.append(value)
    return rows


def _load_inventory(path: Path = INVENTORY_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value.get("components"), list):
        raise ValueError("capability inventory must contain a components array")
    ids = [item.get("id") for item in value["components"]]
    if any(not isinstance(item, str) or not item for item in ids):
        raise ValueError("every inventory component must have a non-empty id")
    if len(ids) != len(set(ids)):
        raise ValueError("capability inventory contains duplicate component IDs")
    return value


def _load_targets(path: Path = TARGETS_PATH) -> dict[str, dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    targets = value.get("targets")
    if not isinstance(targets, list):
        raise ValueError("target registry must contain a targets array")
    result = {}
    for item in targets:
        component_id = item.get("component_id")
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("target profile missing component_id")
        if component_id in result:
            raise ValueError(f"duplicate target profile: {component_id}")
        result[component_id] = item
    return result


def _family_hints(case: dict[str, Any]) -> list[str]:
    trace = case.get("generator", {}).get("generation_trace", [])
    families = []
    for item in trace:
        if isinstance(item, str) and item.startswith("family="):
            value = item.split("=", 1)[1].strip()
            if value:
                families.append(value)
    return families


def scan_coverage_history(history_root: Path) -> dict[str, set[str]]:
    """Collect historically observed taxonomy labels, target IDs, and source families."""
    labels: set[str] = set()
    targets: set[str] = set()
    families: set[str] = set()
    for path in sorted(history_root.rglob("coverage-ledger.json")) if history_root.exists() else []:
        try:
            ledger = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        labels.update(ledger.get("observed_taxonomy_labels", []))
        targets.update(ledger.get("target_component_ids", []))
        families.update(ledger.get("observed_generator_families", []))
    return {"labels": labels, "targets": targets, "families": families}


def build_coverage_ledger(
    *,
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    history_root: Path | None = None,
    campaign_id: str | None = None,
    created_at: str | None = None,
    inventory_path: Path = INVENTORY_PATH,
    target_registry_path: Path = TARGETS_PATH,
) -> dict[str, Any]:
    inventory = _load_inventory(inventory_path)
    profiles = _load_targets(target_registry_path)
    inventory_by_id = {item["id"]: item for item in inventory["components"]}

    case_ids = [case.get("case_id") for case in cases]
    if any(not isinstance(value, str) or not value for value in case_ids):
        raise ValueError("all cases must contain case_id")
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate case_id values in coverage input")
    case_by_id = dict(zip(case_ids, cases))

    result_attempts: Counter[str] = Counter()
    outcomes_by_target: dict[str, Counter[str]] = defaultdict(Counter)
    versions_by_target: dict[str, set[str]] = defaultdict(set)
    interfaces_by_target: dict[str, set[str]] = defaultdict(set)
    attempted_case_ids_by_target: dict[str, set[str]] = defaultdict(set)

    for result in results:
        case = case_by_id.get(result.get("case_id"))
        if case is None:
            raise ValueError(f"execution result has unknown case_id: {result.get('case_id')!r}")
        target = result.get("target", {})
        target_id = target.get("component_id") or case.get("target", {}).get("component_id")
        if not isinstance(target_id, str) or not target_id:
            target_id = "unknown"
        result_attempts[target_id] += 1
        outcomes_by_target[target_id][result.get("outcome", "not_executed")] += 1
        attempted_case_ids_by_target[target_id].add(result["case_id"])
        versions_by_target[target_id].add(str(target.get("component_version", "unspecified")))
        interfaces_by_target[target_id].add(str(case.get("target", {}).get("interface", "other")))

    case_counts = Counter(
        str(case.get("target", {}).get("component_id", "unknown"))
        for case in cases
    )
    population_counts = Counter(str(case.get("population", "unknown")) for case in cases)
    language_counts = Counter(str(case.get("input", {}).get("language_hint", "unspecified")) for case in cases)
    taxonomy_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    unclassified_count = 0
    for case in cases:
        taxonomy = case.get("taxonomy", {})
        if taxonomy.get("unclassified") is True:
            unclassified_count += 1
        taxonomy_counts.update(str(label) for label in taxonomy.get("labels", []))
        family_counts.update(_family_hints(case))

    target_ids_observed = set(case_counts) | set(result_attempts)
    unregistered_targets = sorted(target_ids_observed - set(inventory_by_id))
    entrypoint_rows = []
    for component_id, component in sorted(inventory_by_id.items()):
        profile = profiles.get(component_id)
        case_count = int(case_counts.get(component_id, 0))
        attempts = int(result_attempts.get(component_id, 0))
        outcome_counts = {
            outcome: int(outcomes_by_target[component_id].get(outcome, 0))
            for outcome in OUTCOMES
        }
        if profile is None:
            state = "not_registered_in_open_world_target_profiles"
        elif attempts == 0 and case_count == 0:
            state = "registered_but_not_sampled"
        elif attempts == 0:
            state = "sampled_but_not_executed"
        elif attempts > 0 and attempts == outcome_counts["not_executed"]:
            state = "not_executed_only"
        else:
            state = "entrypoint_exercised"

        entrypoint_rows.append({
            "component_id": component_id,
            "name": component.get("name", component_id),
            "inventory_status": component.get("status", "unspecified"),
            "registered_target": profile is not None,
            "targeted_case_count": case_count,
            "attempt_count": attempts,
            "attempted_case_count": len(attempted_case_ids_by_target[component_id]),
            "target_versions": sorted(versions_by_target[component_id]),
            "interfaces": sorted(interfaces_by_target[component_id]),
            "outcome_counts": outcome_counts,
            "entrypoint_coverage_status": state,
            "inventory_capability_count": len(component.get("capabilities", [])),
            "capability_assessment": "not_assessed_by_entrypoint_sampling",
            "uncovered_entry_points": [
                point.get("path") for point in component.get("entry_points", [])
                if point.get("path") != (profile or {}).get("inventory_path")
            ],
        })

    history = scan_coverage_history(history_root) if history_root else {
        "labels": set(), "targets": set(), "families": set()
    }
    observed_labels = set(taxonomy_counts)
    observed_targets = set(target_ids_observed)
    observed_families = set(family_counts)

    ledger = {
        "ledger_version": "1.0.0",
        "created_at": created_at or _utc_now(),
        "campaign_id": campaign_id,
        "inventory_snapshot_commit": inventory.get("snapshot", {}).get("commit"),
        "inventory_version": inventory.get("inventory_version"),
        "case_count": len(cases),
        "execution_result_count": len(results),
        "population_counts": dict(sorted(population_counts.items())),
        "language_hint_counts": dict(sorted(language_counts.items())),
        "unclassified_case_count": unclassified_count,
        "observed_taxonomy_labels": sorted(observed_labels),
        "taxonomy_label_counts": dict(sorted(taxonomy_counts.items())),
        "observed_generator_families": sorted(observed_families),
        "generator_family_counts": dict(sorted(family_counts.items())),
        "target_component_ids": sorted(observed_targets),
        "entrypoint_coverage": entrypoint_rows,
        "registered_target_profile_count": len(profiles),
        "inventory_component_count": len(inventory_by_id),
        "entrypoint_exercised_component_count": sum(
            row["entrypoint_coverage_status"] == "entrypoint_exercised"
            for row in entrypoint_rows
        ),
        "not_registered_component_ids": unregistered_targets,
        "registered_but_not_sampled_component_ids": [
            row["component_id"] for row in entrypoint_rows
            if row["entrypoint_coverage_status"] == "registered_but_not_sampled"
        ],
        "not_executed_only_component_ids": [
            row["component_id"] for row in entrypoint_rows
            if row["entrypoint_coverage_status"] == "not_executed_only"
        ],
        "historical_comparison": {
            "history_taxonomy_label_count": len(history["labels"]),
            "candidate_new_taxonomy_labels": sorted(observed_labels - history["labels"]),
            "history_target_count": len(history["targets"]),
            "candidate_new_targets": sorted(observed_targets - history["targets"]),
            "history_generator_family_count": len(history["families"]),
            "candidate_new_generator_families": sorted(observed_families - history["families"]),
            "classification": "candidate_new_means_not_found_in_scanned_coverage_ledgers_only",
        },
        "interpretation_limits": [
            "An exercised entry point does not imply every listed capability or every listed entry point was tested.",
            "Model-only packages, adapters, structured reasoning services, storage services, and bounded interpreters require distinct target profiles before open-world coverage can be claimed.",
            "Candidate-new taxonomy labels and generator families are observations, not approved taxonomy promotions.",
            "Coverage is measured over the cases supplied to this ledger; it cannot prove unbounded real-world coverage.",
        ],
    }
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(
        schema, format_checker=FormatChecker()
    ).iter_errors(ledger))
    if errors:
        raise ValueError("coverage-ledger schema errors: " + "; ".join(
            f"{list(error.path)}: {error.message}" for error in errors
        ))
    return ledger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an inventory-backed OW coverage ledger.")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, default=Path("evaluations/open-world/campaigns"))
    parser.add_argument("--campaign-id")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("refusing to overwrite an existing coverage ledger")
    try:
        ledger = build_coverage_ledger(
            cases=_read_jsonl(args.cases),
            results=_read_jsonl(args.results),
            history_root=args.history_root,
            campaign_id=args.campaign_id,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "case_count": ledger["case_count"],
        "inventory_component_count": ledger["inventory_component_count"],
        "entrypoint_exercised_component_count": ledger["entrypoint_exercised_component_count"],
        "unclassified_case_count": ledger["unclassified_case_count"],
        "not_registered_component_ids": ledger["not_registered_component_ids"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
