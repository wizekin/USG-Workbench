"""Read-only snapshot of the latest GitHub Actions run for every repository workflow."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path
from typing import Any, Callable

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"

def _get_json(url: str, token: str, opener: Callable = urlopen) -> dict[str, Any]:
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "USG-System-Evidence-Catalogue/0.1.0",
    })
    with opener(request, timeout=30) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"GitHub API returned a non-object response for {url}")
    return value

def collect_workflow_runs(repository: str, token: str, opener: Callable = urlopen,
                          workers: int = 8) -> dict[str, Any]:
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise ValueError("repository must be owner/name")
    if not token:
        raise ValueError("GitHub token is required")
    base = f"{API_ROOT}/repos/{repository}"
    index = _get_json(f"{base}/actions/workflows?per_page=100", token, opener)
    workflows = index.get("workflows")
    if not isinstance(workflows, list):
        raise ValueError("GitHub workflow listing did not return a workflows array")

    def fetch_one(workflow: dict[str, Any]) -> dict[str, Any]:
        workflow_id = workflow.get("id")
        row = {
            "workflow_id": workflow_id,
            "name": workflow.get("name"),
            "path": workflow.get("path"),
            "state": workflow.get("state"),
            "html_url": workflow.get("html_url"),
        }
        if workflow.get("state") == "disabled_manually" or workflow.get("state") == "disabled_inactivity":
            return {**row, "latest_run": None, "status": "disabled"}
        try:
            data = _get_json(
                f"{base}/actions/workflows/{workflow_id}/runs?per_page=1&exclude_pull_requests=true",
                token, opener)
            runs = data.get("workflow_runs", [])
            if not runs:
                return {**row, "latest_run": None, "status": "no_runs"}
            run = runs[0]
            latest = {
                "run_id": run.get("id"),
                "run_number": run.get("run_number"),
                "run_attempt": run.get("run_attempt"),
                "event": run.get("event"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "created_at": run.get("created_at"),
                "updated_at": run.get("updated_at"),
                "head_sha": run.get("head_sha"),
                "head_branch": run.get("head_branch"),
                "head_commit_message": run.get("head_commit", {}).get("message")
                    if isinstance(run.get("head_commit"), dict) else None,
                "html_url": run.get("html_url"),
            }
            return {**row, "latest_run": latest, "status": run.get("conclusion") or run.get("status") or "unknown"}
        except Exception as exc:
            return {**row, "latest_run": None, "status": "collection_error",
                    "collection_error": f"{type(exc).__name__}: {exc}"}

    ordered = sorted(workflows, key=lambda item: (str(item.get("path", "")), int(item.get("id", 0))))
    with ThreadPoolExecutor(max_workers=max(1, min(int(workers), 16))) as pool:
        results = list(pool.map(fetch_one, ordered))
    counts: dict[str, int] = {}
    for item in results:
        status = str(item.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    errors = [{"workflow_id": item.get("workflow_id"), "path": item.get("path"),
               "error": item.get("collection_error")}
              for item in results if item.get("status") == "collection_error"]
    return {
        "contract": "USG-GITHUB-ACTIONS-EVIDENCE/0.1.0",
        "repository": repository,
        "workflow_count": len(results),
        "latest_run_count": sum(item.get("latest_run") is not None for item in results),
        "status_counts": dict(sorted(counts.items())),
        "workflows": results,
        "collection_errors": errors,
        "interpretation_boundary": "This snapshot reports the latest non-PR run exposed for each workflow. Workflow presence is not run success; skipped, disabled, no-run, and collection-error statuses remain distinct. Results do not establish semantic correctness.",
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", ""))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    report = collect_workflow_runs(args.repository, args.token, workers=args.workers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"contract": report["contract"], "workflow_count": report["workflow_count"],
                      "latest_run_count": report["latest_run_count"], "status_counts": report["status_counts"],
                      "collection_errors": len(report["collection_errors"]), "output": str(args.output)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
