"""Synchronize the USG long-term plan with authoritative repository evidence.

This tool does not edit the strategic plan, phase roadmaps, backlog, or runtime.
It generates a deterministic status/impact report for review and PR publication.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = Path("config/usg-long-term-development-plan-0.1.0.json")
DEFAULT_SCHEMA = Path("specifications/usg-long-term-development-plan-0.1.0.schema.json")
DEFAULT_REGISTRY = Path("config/usg-system-evidence-source-registry-0.1.0.json")
DEFAULT_BACKLOG = Path("documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md")
DEFAULT_CONTINUATION = Path("evaluations/phase6-continuation/tracker.json")
DEFAULT_ACCEPTANCE_DIR = Path("evaluations/system-wide/evidence-catalogue")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_plan(plan: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(plan),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:12]
        )
        raise ValueError(f"long-term plan schema validation failed: {details}")
    phase_ids = [item["phase_id"] for item in plan["phases"]]
    if len(phase_ids) != len(set(phase_ids)):
        raise ValueError("phase IDs in the long-term plan must be unique")
    work_item_ids = [
        item["id"]
        for phase in plan["phases"]
        for item in phase["work_items"]
    ]
    if len(work_item_ids) != len(set(work_item_ids)):
        raise ValueError("work item IDs in the long-term plan must be unique")


def parse_backlog_statuses(markdown: str) -> dict[str, str]:
    """Read only the explicit implementation-status table, not the work queue."""
    statuses: dict[str, str] = {}
    for line in markdown.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"SYS-\d{2}", cells[0]):
            continue
        bold = re.match(r"^\*\*(.+?)\*\*", cells[1])
        if bold:
            statuses[cells[0]] = bold.group(1).strip()
    return statuses


def parse_continuation_statuses(tracker: dict[str, Any]) -> dict[str, str]:
    items = tracker.get("work_items", [])
    if not isinstance(items, list):
        raise ValueError("Phase 6 continuation tracker work_items must be an array")
    result: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        result[str(item["id"])] = str(item.get("status", "not_reported"))
    return result


def collect_phase8_acceptance(root: Path) -> dict[str, Any]:
    directory = root / DEFAULT_ACCEPTANCE_DIR
    artifacts = sorted(directory.glob("*/phase8-integrated-acceptance.json"))
    if not artifacts:
        return {
            "status": "not_verified",
            "phase_accepted": False,
            "artifact": None,
            "reason": "No published Phase 8 integrated-acceptance artifact was found.",
        }
    artifact_path = artifacts[-1]
    try:
        artifact = read_json(artifact_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return {
            "status": "unreadable",
            "phase_accepted": False,
            "artifact": artifact_path.relative_to(root).as_posix(),
            "reason": str(error),
        }
    decision = artifact.get("acceptance_decision", {})
    source_sha = decision.get("source_commit_sha")
    validated_sha = decision.get("validated_commit_sha")
    accepted = (
        artifact.get("status") == "accepted"
        and artifact.get("phase_accepted") is True
        and bool(source_sha)
        and source_sha == validated_sha
        and bool(decision.get("workflow_run_id"))
        and bool(decision.get("workflow_run_attempt"))
    )
    return {
        "status": "accepted" if accepted else artifact.get("status", "invalid"),
        "phase_accepted": accepted,
        "artifact": artifact_path.relative_to(root).as_posix(),
        "source_commit_sha": source_sha,
        "validated_commit_sha": validated_sha,
        "workflow_run_id": decision.get("workflow_run_id"),
        "workflow_run_attempt": decision.get("workflow_run_attempt"),
        "decision_id": decision.get("decision_id"),
        "reason": (
            "Published artifact records an accepted exact-head Phase 8 decision."
            if accepted
            else "Latest artifact does not prove accepted exact-head Phase 8 formal acceptance."
        ),
    }


def fingerprint_sources(root: Path, paths: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    ignored = {".git", ".venv", "node_modules", "__pycache__"}
    for relative in paths:
        path = root / relative
        if path.is_file():
            result.append({
                "path": relative,
                "exists": True,
                "sha256": sha256_file(path),
                "file_count": 1,
            })
        elif path.is_dir():
            files = sorted(
                item for item in path.rglob("*")
                if item.is_file() and not any(part in ignored for part in item.parts)
            )
            digest = hashlib.sha256()
            for item in files:
                rel = item.relative_to(root).as_posix()
                digest.update(rel.encode("utf-8"))
                digest.update(b"\0")
                digest.update(sha256_file(item).encode("ascii"))
                digest.update(b"\n")
            result.append({
                "path": relative,
                "exists": True,
                "sha256": digest.hexdigest(),
                "file_count": len(files),
            })
        else:
            result.append({
                "path": relative,
                "exists": False,
                "sha256": None,
                "file_count": 0,
            })
    return result


def load_changed_paths(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    values = [
        line.strip().replace("\\", "/")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return sorted(set(values))


def matching_workstreams(plan: dict[str, Any], changed_paths: list[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for rule in plan.get("path_trigger_rules", []):
        patterns = rule.get("patterns", [])
        matched = sorted({
            path for path in changed_paths
            if any(fnmatch.fnmatch(path, pattern) for pattern in patterns)
        })
        if matched:
            matches.append({
                "phase_id": rule["phase_id"],
                "matched_paths": matched,
                "rationale": rule.get("rationale", ""),
            })
    return matches


def build_report(
    root: Path,
    plan: dict[str, Any],
    registry: dict[str, Any],
    backlog_statuses: dict[str, str],
    continuation_statuses: dict[str, str],
    changed_paths: list[str],
    commit_sha: str,
    event_name: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    phase_registry = {
        str(item["id"]): {
            "name": item.get("name"),
            "status": item.get("status"),
            "roadmap": item.get("roadmap"),
            "acceptance": item.get("acceptance"),
            "open_work": item.get("open_work"),
        }
        for item in registry.get("phases", [])
    }
    phase_snapshots = []
    for phase in plan["phases"]:
        phase_id = phase["phase_id"]
        phase_snapshots.append({
            "phase_id": phase_id,
            "title": phase["title"],
            "planned_status": phase["status"],
            "authoritative_registry_status": phase_registry.get(phase_id, {}).get("status"),
            "linked_backlog": [
                {"id": item_id, "status": backlog_statuses.get(item_id, "not_reported")}
                for item_id in phase.get("linked_backlog_ids", [])
            ],
            "linked_phase6_continuations": [
                {"id": item_id, "status": continuation_statuses.get(item_id, "not_reported")}
                for item_id in phase.get("linked_continuation_ids", [])
            ],
            "dependencies": phase.get("depends_on", []),
        })

    source_paths = [item["path"] for item in plan.get("sources_of_truth", [])]
    fingerprints = fingerprint_sources(root, source_paths)
    phase8_acceptance = collect_phase8_acceptance(root)
    impacted = matching_workstreams(plan, changed_paths)
    return {
        "contract": "USG-LONG-TERM-PLAN-SYNC/0.1.0",
        "plan_contract": plan["contract"],
        "plan_version": plan["version"],
        "repository": plan["repository"],
        "generated_at": generated_at,
        "commit_sha": commit_sha or "not_supplied",
        "event_name": event_name or "manual",
        "change_observation": {
            "changed_path_count": len(changed_paths),
            "changed_paths": changed_paths,
            "impacted_workstreams": impacted,
            "requires_plan_review": bool(impacted),
            "interpretation": (
                "Changed paths identify workstreams that should be re-evaluated; they do not prove task completion or semantic capability."
            ),
        },
        "phase8_formal_acceptance": phase8_acceptance,
        "phase_snapshots": phase_snapshots,
        "backlog_statuses": [
            {"id": item_id, "reported_status": status}
            for item_id, status in sorted(backlog_statuses.items())
        ],
        "phase6_continuation_statuses": [
            {"id": item_id, "reported_status": status}
            for item_id, status in sorted(continuation_statuses.items())
        ],
        "source_fingerprints": fingerprints,
        "maintenance_actions": [
            "Refresh impacted workstream dependencies and source links before starting affected tasks."
            if impacted else
            "No changed paths matched the registered future workstream; review periodic source/status drift."
        ] + ([
            "Phase 8 formal acceptance remains unverified or blocked; resolve it before starting Phase 9."
        ] if not phase8_acceptance.get("phase_accepted") else [
            "Phase 8 exact-head formal acceptance is present; Phase 9 remains planned until explicitly started."
        ]),
        "governance": {
            "strategic_plan_modified": False,
            "source_of_truth_files_modified": False,
            "future_phase_implementation_started": False,
            "semantic_runtime_mutation_allowed": False,
            "candidate_promotion_allowed": False,
            "normative_contract_mutation_allowed": False,
            "phase_acceptance_inferred_from_merge": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    q = chr(96)
    lines = [
        "# USG Long-Term Development Plan — Synchronization Report",
        "",
        f"- **Generated:** {report['generated_at']}",
        f"- **Commit:** {q}{report['commit_sha']}{q}",
        f"- **Trigger:** {q}{report['event_name']}{q}",
        f"- **Phase 8 formal acceptance:** **{report['phase8_formal_acceptance']['status']}**",
        f"- **Changed paths:** {report['change_observation']['changed_path_count']}",
        "",
        "## Phase status snapshot",
        "",
        "| Phase | Planned state | Registry state | Linked work evidence |",
        "|---|---|---|---|",
    ]
    for item in report["phase_snapshots"]:
        linked = [
            f"{entry['id']}: {entry['status']}"
            for entry in item["linked_backlog"]
        ] + [
            f"{entry['id']}: {entry['status']}"
            for entry in item["linked_phase6_continuations"]
        ]
        lines.append(
            f"| {item['phase_id']} — {item['title']} | {item['planned_status']} | "
            f"{item['authoritative_registry_status'] or 'not registered'} | "
            f"{'; '.join(linked) if linked else '—'} |"
        )
    lines += ["", "## Workstreams affected by this change", ""]
    impacted = report["change_observation"]["impacted_workstreams"]
    if impacted:
        for item in impacted:
            lines.append(f"### {item['phase_id']}")
            lines.append(item["rationale"])
            lines.append("")
            lines.extend(f"- {q}{path}{q}" for path in item["matched_paths"])
            lines.append("")
    else:
        lines.append("No changed paths matched the registered workstream triggers.")
        lines.append("")
    lines += [
        "## Phase 8 acceptance evidence",
        "",
        report["phase8_formal_acceptance"].get("reason", "No status detail is available."),
        "",
    ]
    if report["phase8_formal_acceptance"].get("artifact"):
        lines.append(f"Artifact: {q}{report['phase8_formal_acceptance']['artifact']}{q}")
        lines.append("")
    lines += [
        "## Source fingerprints",
        "",
        "| Source | Present | Files | SHA-256 |",
        "|---|---:|---:|---|",
    ]
    for item in report["source_fingerprints"]:
        lines.append(
            f"| {q}{item['path']}{q} | {str(item['exists']).lower()} | "
            f"{item['file_count']} | {q}{item['sha256'] or '—'}{q} |"
        )
    lines += ["", "## Required maintenance actions", ""]
    lines.extend(f"- {action}" for action in report["maintenance_actions"])
    lines += [
        "",
        "## Governance boundary",
        "",
        "This synchronizer reports source changes and authoritative status. It does not edit the strategic plan, accept a phase from a merged PR, promote resources, or start future implementation.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--backlog", type=Path, default=DEFAULT_BACKLOG)
    parser.add_argument("--continuation-tracker", type=Path, default=DEFAULT_CONTINUATION)
    parser.add_argument("--changed-paths-file", type=Path)
    parser.add_argument("--commit-sha", default="")
    parser.add_argument("--event-name", default="manual")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    plan = read_json(root / args.plan)
    schema = read_json(root / args.schema)
    validate_plan(plan, schema)
    registry = read_json(root / args.registry)
    backlog_statuses = parse_backlog_statuses((root / args.backlog).read_text(encoding="utf-8"))
    continuation_statuses = parse_continuation_statuses(read_json(root / args.continuation_tracker))
    changed_paths = load_changed_paths(
        (root / args.changed_paths_file) if args.changed_paths_file else None
    )
    report = build_report(
        root, plan, registry, backlog_statuses, continuation_statuses,
        changed_paths, args.commit_sha, args.event_name,
    )
    output_json = root / args.output_json
    output_markdown = root / args.output_markdown
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "phase8_status": report["phase8_formal_acceptance"]["status"],
        "changed_path_count": report["change_observation"]["changed_path_count"],
        "impacted_phase_ids": [item["phase_id"] for item in report["change_observation"]["impacted_workstreams"]],
        "outputs": [str(args.output_json), str(args.output_markdown)],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
