"""Generate a read-only Phase 6 continuation tracker snapshot.

The manifest remains authoritative. GitHub lookups only observe pull-request and
check-run activity; they never change tracker status or semantic capability.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "evaluations" / "phase6-continuation" / "tracker.json"
DEFAULT_SCHEMA = ROOT / "specifications" / "phase6-continuation-tracker-1.0.schema.json"
API_ROOT = "https://api.github.com"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def validate_manifest(data: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate tracker structure and, when available, its published JSON Schema."""
    if data.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported Phase 6 tracker schema_version")
    if data.get("tracker_id") != "USG-PHASE-6-CONTINUATION-TRACKER":
        raise ValueError("Unexpected tracker_id")
    phase_status = data.get("phase_status")
    if not isinstance(phase_status, dict) or phase_status.get("phase7_blocking") is not False:
        raise ValueError("Phase 6 continuation must be explicitly non-blocking for Phase 7")
    items = data.get("work_items")
    if not isinstance(items, list) or not items:
        raise ValueError("work_items must be a non-empty array")
    ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Every work item must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.startswith("P6-CONT-"):
            raise ValueError("Every work item must have a stable P6-CONT identifier")
        if item_id in ids:
            raise ValueError(f"Duplicate work item id: {item_id}")
        ids.add(item_id)
        if item.get("pr_search_marker") != item_id:
            raise ValueError(f"{item_id} must use its ID as the PR search marker")
        if item.get("phase7_blocking") is not False:
            raise ValueError(f"{item_id} must not block Phase 7")
        if item.get("status") not in {
            "backlog", "candidate_only", "in_progress",
            "merged_pending_acceptance", "accepted", "blocked", "deferred"
        }:
            raise ValueError(f"{item_id} has an unsupported status")
    if schema_path is not None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError as exc:
            raise RuntimeError("jsonschema is required for schema validation") from exc
        schema = load_json(schema_path)
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(data)


def api_get(url: str, token: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "usg-phase6-continuation-tracker",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"GitHub API request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub API returned a non-object response")
    return payload


def discover_pull_requests(repository: str, marker: str, token: str) -> list[dict[str, Any]]:
    query = f"repo:{repository} is:pr {marker}"
    search_url = f"{API_ROOT}/search/issues?{urlencode({'q': query, 'per_page': 20})}"
    results = api_get(search_url, token).get("items", [])
    observations: list[dict[str, Any]] = []
    for item in results:
        if "pull_request" not in item:
            continue
        number = item.get("number")
        if not isinstance(number, int):
            continue
        pr = api_get(f"{API_ROOT}/repos/{repository}/pulls/{number}", token)
        head = pr.get("head") or {}
        sha = head.get("sha")
        check_summary: dict[str, Any] = {
            "available": False, "total": 0, "queued": 0, "in_progress": 0,
            "success": 0, "failure": 0, "cancelled_or_skipped": 0
        }
        if isinstance(sha, str) and sha:
            try:
                checks = api_get(
                    f"{API_ROOT}/repos/{repository}/commits/{sha}/check-runs?per_page=100",
                    token,
                ).get("check_runs", [])
                check_summary["available"] = True
                check_summary["total"] = len(checks)
                for check in checks:
                    status = check.get("status")
                    conclusion = check.get("conclusion")
                    if status != "completed":
                        check_summary["in_progress"] += 1
                    elif conclusion == "success":
                        check_summary["success"] += 1
                    elif conclusion in {"failure", "timed_out", "action_required", "startup_failure"}:
                        check_summary["failure"] += 1
                    elif conclusion in {"cancelled", "skipped", "neutral"}:
                        check_summary["cancelled_or_skipped"] += 1
                    else:
                        check_summary["queued"] += 1
            except Exception as exc:  # Check access can vary by repository permissions.
                check_summary["error"] = str(exc)
        observations.append({
            "number": number,
            "title": pr.get("title") or item.get("title"),
            "url": pr.get("html_url") or item.get("html_url"),
            "state": pr.get("state"),
            "merged": bool(pr.get("merged")),
            "merge_commit_sha": pr.get("merge_commit_sha"),
            "head_branch": head.get("ref"),
            "head_sha": sha,
            "updated_at": pr.get("updated_at") or item.get("updated_at"),
            "checks": check_summary,
        })
    return observations


def build_report(
    manifest: dict[str, Any],
    repository: str,
    token: str | None = None,
    offline: bool = False,
    source_commit: str | None = None,
) -> dict[str, Any]:
    validate_manifest(manifest)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    items: list[dict[str, Any]] = []
    for source_item in manifest["work_items"]:
        item = dict(source_item)
        item["github_observation"] = {
            "status": "manifest_only",
            "pull_requests": [],
        }
        if not offline and token:
            try:
                prs = discover_pull_requests(repository, item["pr_search_marker"], token)
                item["github_observation"] = {
                    "status": "matched" if prs else "no_matching_pr",
                    "pull_requests": prs,
                }
            except Exception as exc:
                item["github_observation"] = {
                    "status": "lookup_error",
                    "pull_requests": [],
                    "error": str(exc),
                }
        items.append(item)
    errors = sum(item["github_observation"]["status"] == "lookup_error" for item in items)
    return {
        "report_version": "1.0.0",
        "tracker_id": manifest["tracker_id"],
        "generated_at_utc": now,
        "repository": repository,
        "source_commit": source_commit,
        "monitoring_mode": "offline" if offline else ("github_api" if token else "manifest_only"),
        "report_status": "partial" if errors else "complete",
        "bounded_phase6_exit": manifest["phase_status"]["bounded_exit"],
        "runtime_capability_claim": manifest["phase_status"]["runtime_capability_claim"],
        "naturalistic_accuracy": manifest["phase_status"]["naturalistic_accuracy"],
        "phase7_blocking": False,
        "work_item_count": len(items),
        "github_lookup_errors": errors,
        "work_items": items,
        "guardrails": manifest["guardrails"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Phase 6 Continuation Tracker — Automated Snapshot",
        "",
        f"- Generated (UTC): {report['generated_at_utc']}",
        f"- Repository: `{report['repository']}`",
        f"- Source commit: `{report.get('source_commit') or 'not supplied'}`",
        f"- Monitoring mode: **{report['monitoring_mode']}**",
        f"- Report status: **{report['report_status']}**",
        f"- Bounded Phase 6 exit: **{report['bounded_phase6_exit']}**",
        f"- Runtime capability claim: **{report['runtime_capability_claim']}**",
        f"- Naturalistic accuracy: **{report['naturalistic_accuracy']}**",
        "- Phase 7 blocking: **No**",
        "",
        "| ID | Status in manifest | GitHub observation | Pull requests |",
        "|---|---|---|---:|",
    ]
    for item in report["work_items"]:
        obs = item["github_observation"]
        lines.append(
            f"| {item['id']} | {item['status']} | {obs['status']} | {len(obs['pull_requests'])} |"
        )
    lines.extend(["", "## Workstream details", ""])
    for item in report["work_items"]:
        obs = item["github_observation"]
        lines.extend([
            f"### {item['id']} — {item['title']}",
            "",
            f"- Phase step: {item['phase_step']}",
            f"- Priority: {item['priority']}",
            f"- Manifest status: **{item['status']}**",
            f"- Phase 7 blocking: **No**",
            f"- Objective: {item['objective']}",
            f"- Acceptance gate: {item['acceptance_gate']}",
            f"- GitHub lookup: **{obs['status']}**",
        ])
        if obs.get("error"):
            lines.append(f"- Lookup error: {obs['error']}")
        for pr in obs["pull_requests"]:
            checks = pr["checks"]
            lines.append(
                f"- PR [#{pr['number']} — {pr['title']}]({pr['url']}): "
                f"state={pr['state']}, merged={pr['merged']}, "
                f"checks={checks['success']} success / {checks['failure']} failure / "
                f"{checks['in_progress']} in progress of {checks['total']}"
            )
        if not obs["pull_requests"]:
            lines.append("- No matching PR was found for this workstream marker.")
        lines.append("")
    lines.extend(["## Guardrails", ""])
    lines.extend(f"- {rule}" for rule in report["guardrails"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "wizekin/USG-Workbench"))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "phase6-continuation-tracker")
    parser.add_argument("--offline", action="store_true", help="Do not query the GitHub API.")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    validate_manifest(manifest, args.schema)
    token = None if args.offline else (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    report = build_report(
        manifest,
        args.repository,
        token=token,
        offline=args.offline,
        source_commit=os.environ.get("GITHUB_SHA"),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "phase6-continuation-tracker-report.json"
    markdown_path = args.output_dir / "phase6-continuation-tracker-report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    markdown_path.write_text(markdown, encoding="utf-8")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(markdown)
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    print(f"Report status: {report['report_status']}; Phase 7 blocking: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
