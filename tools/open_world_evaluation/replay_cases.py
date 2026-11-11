"""Pinned, append-only replay of previously recorded OW scenarios."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

from .execute_cases import execute_case
from .validate_protocol import validate_instance

ROOT = Path(__file__).resolve().parents[2]
STABILITY_PROFILES_PATH = ROOT / "tools" / "open_world_evaluation" / "replay_stability_profiles.json"
REPLAY_VERSION = "1.0.0"
MAX_REPLAY_RECORDS = 500


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_sha(value: str) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(
        char in "0123456789abcdef" for char in value
    )


def load_stability_profiles(path: Path = STABILITY_PROFILES_PATH) -> dict[str, Any]:
    profiles = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profiles, dict) or not isinstance(profiles.get("profiles"), dict):
        raise ValueError("replay stability profiles must contain a profiles object")
    for target_id, profile in profiles["profiles"].items():
        paths = profile.get("volatile_json_paths")
        if not isinstance(paths, list) or any(
            not isinstance(item, str) or not item or item.startswith(".") or item.endswith(".")
            for item in paths
        ):
            raise ValueError(f"{target_id} has invalid volatile_json_paths")
    return profiles


def current_checkout_sha(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("cannot determine the checked-out Git commit")
    value = result.stdout.strip()
    if not _valid_sha(value):
        raise RuntimeError("checked-out Git HEAD is not a valid lowercase commit SHA")
    return value


def _target_result(record: dict[str, Any]) -> dict[str, Any] | None:
    payload = record.get("capture", {}).get("inline_output")
    if not isinstance(payload, dict):
        return None
    value = payload.get("target_result")
    return value if isinstance(value, dict) else None


def _remove_path(value: dict[str, Any], path: str) -> None:
    parts = path.split(".")
    current: Any = value
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return
        current = current[part]
    if isinstance(current, dict):
        current.pop(parts[-1], None)


def _normalize_source_id_references(value: dict[str, Any]) -> None:
    source_ids: set[str] = set()
    if isinstance(value.get("source_ref"), str):
        source_ids.add(value["source_ref"])
    source = value.get("source")
    if isinstance(source, dict) and isinstance(source.get("source_id"), str):
        source_ids.add(source["source_id"])
    document = value.get("document")
    if isinstance(document, dict):
        if isinstance(document.get("primarySourceRef"), str):
            source_ids.add(document["primarySourceRef"])
        sources = document.get("sources", [])
        if isinstance(sources, list):
            for item in sources:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    source_ids.add(item["id"])
    if not source_ids:
        return

    def normalize(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: normalize(child) for key, child in item.items()}
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, str) and item in source_ids:
            return "__USG_REPLAY_SOURCE_ID__"
        return item

    normalized = normalize(value)
    value.clear()
    value.update(normalized)


def stable_target_result_projection(
    record: dict[str, Any],
    target_id: str,
    *,
    profiles: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return the normalized target-result projection and observed pipeline version."""
    profiles = profiles or load_stability_profiles()
    profile = profiles["profiles"].get(target_id)
    target_result = _target_result(record)
    if profile is None or target_result is None:
        return None, None
    observed_version = target_result.get("pipeline_version")
    observed_contract = target_result.get("pipeline_contract")
    if observed_version != profile["pipeline_version"]:
        return None, str(observed_version) if observed_version is not None else None
    if observed_contract != profile["pipeline_contract"]:
        return None, str(observed_version)
    stable = copy.deepcopy(target_result)
    if profile.get("normalize_source_id_references", False):
        _normalize_source_id_references(stable)
    for path in profile["volatile_json_paths"]:
        _remove_path(stable, path)
    return stable, str(observed_version)


def stable_target_result_digest(
    record: dict[str, Any],
    target_id: str,
    *,
    profiles: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    stable, version = stable_target_result_projection(record, target_id, profiles=profiles)
    if stable is None:
        return None, version
    return _sha256(_canonical_bytes(stable)), version


def _differing_json_paths(left: Any, right: Any, *, limit: int = 32) -> list[str]:
    differences: list[str] = []

    def visit(a: Any, b: Any, path: str) -> None:
        if len(differences) >= limit:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(set(a) | set(b)):
                child = f"{path}.{key}" if path else str(key)
                if key not in a or key not in b:
                    differences.append(child)
                else:
                    visit(a[key], b[key], child)
                if len(differences) >= limit:
                    return
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                differences.append(path + ".[length]")
            for index, (item_a, item_b) in enumerate(zip(a, b)):
                visit(item_a, item_b, f"{path}[{index}]")
                if len(differences) >= limit:
                    return
        elif a != b:
            differences.append(path or "$")

    visit(left, right, "")
    return differences


def compare_replay(
    original: dict[str, Any],
    replayed: dict[str, Any],
    *,
    profiles: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target_id = str(original.get("target", {}).get("component_id", "unknown"))
    original_projection, original_version = stable_target_result_projection(
        original, target_id, profiles=profiles
    )
    replay_projection, replay_version = stable_target_result_projection(
        replayed, target_id, profiles=profiles
    )
    original_digest = (
        _sha256(_canonical_bytes(original_projection))
        if original_projection is not None else None
    )
    replay_digest = (
        _sha256(_canonical_bytes(replay_projection))
        if replay_projection is not None else None
    )
    outcome_matches = original.get("outcome") == replayed.get("outcome")
    comparable = original_digest is not None and replay_digest is not None
    target_result_matches = original_digest == replay_digest if comparable else None
    differing_paths = (
        _differing_json_paths(original_projection, replay_projection)
        if comparable and not target_result_matches else []
    )

    if not outcome_matches:
        status = "outcome_mismatch"
    elif not comparable:
        status = "not_comparable"
    elif not target_result_matches:
        status = "target_result_mismatch"
    else:
        status = "exact_match"

    return {
        "case_id": original.get("case_id"),
        "target_id": target_id,
        "tested_commit_sha": original.get("target", {}).get("commit_sha"),
        "input_sha256": None,
        "original_attempt_id": original.get("attempt_id"),
        "replay_attempt_id": replayed.get("attempt_id"),
        "original_outcome": original.get("outcome"),
        "replay_outcome": replayed.get("outcome"),
        "outcome_matches": outcome_matches,
        "original_target_result_sha256": original_digest,
        "replay_target_result_sha256": replay_digest,
        "target_result_matches": target_result_matches,
        "differing_json_paths": differing_paths,
        "original_pipeline_version": original_version,
        "replay_pipeline_version": replay_version,
        "status": status,
    }


def replay_records(
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    *,
    commit_sha: str,
    max_cases: int = 25,
    selected_case_ids: set[str] | None = None,
    max_wall_seconds: float = 60.0,
    executor: Callable[..., dict[str, Any]] | None = None,
    profiles: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not _valid_sha(commit_sha):
        raise ValueError("commit_sha must be a 40-character lowercase SHA")
    if not 1 <= max_cases <= MAX_REPLAY_RECORDS:
        raise ValueError(f"max_cases must be 1..{MAX_REPLAY_RECORDS}")
    if max_wall_seconds <= 0:
        raise ValueError("max_wall_seconds must be positive")

    executor = executor or execute_case
    profiles = profiles or load_stability_profiles()
    case_by_id = {case.get("case_id"): case for case in cases}
    if len(case_by_id) != len(cases):
        raise ValueError("scenario input contains duplicate case IDs")
    if selected_case_ids:
        missing = selected_case_ids - set(case_by_id)
        if missing:
            raise ValueError("selected case IDs are missing: " + ", ".join(sorted(missing)))

    eligible = []
    skipped_not_executed = 0
    for original in results:
        case_id = original.get("case_id")
        if selected_case_ids and case_id not in selected_case_ids:
            continue
        if original.get("outcome") == "not_executed":
            skipped_not_executed += 1
            continue
        if original.get("target", {}).get("commit_sha") != commit_sha:
            raise ValueError(
                f"original result for {case_id} is pinned to a different commit"
            )
        case = case_by_id.get(case_id)
        if case is None:
            raise ValueError(f"original result references missing case {case_id}")
        if case.get("target", {}).get("component_id") != original.get("target", {}).get("component_id"):
            raise ValueError(f"case/result target mismatch for {case_id}")
        eligible.append((case, original))

    selected = eligible[:max_cases]
    entries = []
    for case, original in selected:
        replayed = executor(
            case, commit_sha=commit_sha, max_wall_seconds=max_wall_seconds
        )
        entry = compare_replay(original, replayed, profiles=profiles)
        entry["input_sha256"] = case.get("input", {}).get("utf8_sha256")
        entries.append(entry)

    counts = {
        "exact_match": sum(item["status"] == "exact_match" for item in entries),
        "outcome_mismatch": sum(item["status"] == "outcome_mismatch" for item in entries),
        "target_result_mismatch": sum(item["status"] == "target_result_mismatch" for item in entries),
        "not_comparable": sum(item["status"] == "not_comparable" for item in entries),
    }
    mismatch_count = counts["outcome_mismatch"] + counts["target_result_mismatch"]
    if not entries:
        status = "no_cases"
    elif mismatch_count:
        status = "differences_found"
    elif counts["not_comparable"]:
        status = "partial"
    else:
        status = "complete"

    return {
        "schema_version": "1.0.0",
        "replay_version": REPLAY_VERSION,
        "created_at": _utc_now(),
        "repository": "wizekin/USG-Workbench",
        "tested_commit_sha": commit_sha,
        "replay_policy_version": str(profiles.get("policy_version", "unknown")),
        "status": status,
        "selected_case_count": len({case["case_id"] for case, _ in selected}),
        "selected_result_record_count": len(eligible),
        "replayed_record_count": len(entries),
        "skipped_not_executed_record_count": skipped_not_executed,
        "not_replayed_due_to_budget_count": max(0, len(eligible) - len(selected)),
        "counts": counts,
        "entries": entries,
        "limitations": [
            "Replay requires the current checkout to equal the pinned tested commit; it never labels a different checkout as the original commit.",
            "Only target-result fields outside the explicit target stability profile's volatile paths are compared.",
            "A matching replay establishes repeatability for these pinned cases and resources, not semantic correctness.",
            "Targets without a stability profile or with a pipeline-version mismatch are reported as not comparable.",
        ],
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(item)
    return rows


def replay_files(
    cases_path: Path,
    results_path: Path,
    output_path: Path,
    *,
    commit_sha: str,
    max_cases: int = 25,
    selected_case_ids: set[str] | None = None,
    max_wall_seconds: float = 60.0,
    root: Path = ROOT,
) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite replay report: {output_path}")
    checked_out = current_checkout_sha(root)
    if checked_out != commit_sha:
        raise ValueError(
            f"checkout commit {checked_out} does not match requested replay commit {commit_sha}; "
            "checkout the exact commit before replay"
        )
    cases = _read_jsonl(cases_path)
    results = _read_jsonl(results_path)
    for index, case in enumerate(cases):
        errors = validate_instance("scenario", case)
        if errors:
            raise ValueError(f"invalid scenario {index}: " + "; ".join(errors))
    for index, record in enumerate(results):
        errors = validate_instance("execution_result", record)
        if errors:
            raise ValueError(f"invalid execution result {index}: " + "; ".join(errors))

    report = replay_records(
        cases, results, commit_sha=commit_sha, max_cases=max_cases,
        selected_case_ids=selected_case_ids, max_wall_seconds=max_wall_seconds,
    )
    schema_path = ROOT / "tools" / "open_world_evaluation" / "schemas" / "replay-report.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report))
    if errors:
        raise ValueError("replay report schema errors: " + "; ".join(error.message for error in errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay recorded USG Open-World cases at the exact pinned commit."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--max-cases", type=int, default=25)
    parser.add_argument("--max-wall-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)
    try:
        report = replay_files(
            args.cases, args.results, args.output,
            commit_sha=args.commit_sha,
            max_cases=args.max_cases,
            selected_case_ids=set(args.case_id) if args.case_id else None,
            max_wall_seconds=args.max_wall_seconds,
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": report["status"],
        "tested_commit_sha": report["tested_commit_sha"],
        "replayed_record_count": report["replayed_record_count"],
        "counts": report["counts"],
        "mismatches": [
            {"case_id": item["case_id"], "status": item["status"],
             "differing_json_paths": item.get("differing_json_paths", [])}
            for item in report["entries"] if item["status"] in {"outcome_mismatch", "target_result_mismatch"}
        ],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "differences_found" else 0


if __name__ == "__main__":
    raise SystemExit(main())
