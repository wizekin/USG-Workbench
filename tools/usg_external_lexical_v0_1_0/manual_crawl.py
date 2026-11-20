"""One-launch, resumable controller for completing the external lexical crawl.

This controller is an adapter over the repository's existing LexicalCrawler.
It deliberately does not reimplement source discovery, parsing, checkpointing,
sharding, or publication. Those remain owned by crawl.py.

A GitHub Actions job has a finite execution window. When that window is nearly
exhausted, this module dispatches the same workflow again. Every continuation
re-reads the authoritative checkpoint from the data branch, so one manual
workflow launch can continue across multiple bounded Actions runs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Callable
from urllib.parse import quote

from .crawl import (
    DEFAULT_DATA_BRANCH,
    DEFAULT_MAX_SHARD_BYTES,
    GITHUB_API,
    GitHubDataPublisher,
    LexicalCrawler,
    _github_api_request,
)

DEFAULT_TARGET_TOTAL = 1_396_111
DEFAULT_BATCH_HEADWORDS = 30_000
DEFAULT_SESSION_RUNTIME_SECONDS = 18_000  # 5 hours; workflow timeout is 5h50m.
DEFAULT_RESERVE_SECONDS = 300             # Leave time for audit and job cleanup.
STORAGE_BUDGET_MIB = 700
STORAGE_BUDGET_BYTES = STORAGE_BUDGET_MIB * 1024 * 1024
WORKFLOW_ID = "usg-external-lexical-complete.yml"
WORKFLOW_REF = "main"


def checkpoint_count(checkpoint: dict[str, Any] | None) -> int:
    """Return the durable source-cursor count, treating absent state as zero."""
    return int((checkpoint or {}).get("processed_headwords", 0) or 0)


def checkpoint_signature(checkpoint: dict[str, Any] | None) -> tuple[Any, ...]:
    """Return fields that prove durable crawl progress beyond timestamp updates."""
    state = checkpoint or {}
    return (
        checkpoint_count(state),
        int(state.get("page_index", 0) or 0),
        int(state.get("entry_index", 0) or 0),
        int(state.get("batch_number", 0) or 0),
        int(state.get("stored_bytes", 0) or 0),
        int(state.get("retried_headwords", 0) or 0),
        int(state.get("recovered_headwords", 0) or 0),
        int(state.get("retry_failed_headwords", 0) or 0),
        int(state.get("retry_dead_letter_headwords", 0) or 0),
        int(state.get("failed_pages", 0) or 0),
        len(state.get("retry_queue", []) or []),
        state.get("status"),
    )


def dispatch_continuation(
    *,
    token: str,
    repository: str,
    workflow_id: str,
    workflow_ref: str,
    target_total: int,
    batch_headwords: int,
) -> None:
    """Queue exactly one continuation through GitHub's workflow_dispatch API."""
    if not token:
        raise ValueError("A GitHub token is required to dispatch a continuation.")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be in owner/name form.")
    endpoint = (
        f"{GITHUB_API}/repos/{repository}/actions/workflows/"
        f"{quote(workflow_id, safe='')}/dispatches"
    )
    _github_api_request(
        "POST",
        endpoint,
        token,
        {
            "ref": workflow_ref,
            "inputs": {
                "target_total": str(target_total),
                "batch_headwords": str(batch_headwords),
                "continue_until_target": "true",
                "continuation": "true",
            },
        },
    )


def run_session(
    crawler: Any,
    *,
    target_total: int,
    batch_headwords: int = DEFAULT_BATCH_HEADWORDS,
    session_runtime_seconds: int = DEFAULT_SESSION_RUNTIME_SECONDS,
    reserve_seconds: int = DEFAULT_RESERVE_SECONDS,
    max_shard_bytes: int = DEFAULT_MAX_SHARD_BYTES,
    run_id: str = "manual",
    continue_chain: bool = False,
    continuation_dispatcher: Callable[..., None] | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Run actual crawler batches until target, safety stop, or session budget.

    The crawler is duck-typed only to permit deterministic offline unit tests.
    Production uses tools.usg_external_lexical_v0_1_0.crawl.LexicalCrawler.
    """
    if target_total < 0:
        raise ValueError("target_total cannot be negative.")
    if not 1 <= batch_headwords <= DEFAULT_BATCH_HEADWORDS:
        raise ValueError(f"batch_headwords must be between 1 and {DEFAULT_BATCH_HEADWORDS}.")
    if session_runtime_seconds <= reserve_seconds:
        raise ValueError("The session runtime must be greater than the reserve.")
    if session_runtime_seconds > DEFAULT_SESSION_RUNTIME_SECONDS:
        raise ValueError(
            f"session_runtime_seconds cannot exceed {DEFAULT_SESSION_RUNTIME_SECONDS}."
        )

    started = monotonic()
    initial_checkpoint = crawler.load_checkpoint() or {}
    expected_total = int(initial_checkpoint.get("expected_headwords", 0) or 0)
    target = target_total or expected_total or DEFAULT_TARGET_TOTAL
    if expected_total and target > expected_total:
        raise ValueError(
            f"Requested target {target:,} exceeds source snapshot size {expected_total:,}."
        )

    initial_count = checkpoint_count(initial_checkpoint)
    batches: list[dict[str, Any]] = []
    current_checkpoint = initial_checkpoint

    def report(status: str, **extra: Any) -> dict[str, Any]:
        final_count = checkpoint_count(current_checkpoint)
        return {
            "status": status,
            "target_total": target,
            "initial_processed_headwords": initial_count,
            "final_processed_headwords": final_count,
            "session_processed_headwords": max(0, final_count - initial_count),
            "remaining_headwords": max(0, target - final_count),
            "stored_bytes": int(current_checkpoint.get("stored_bytes", 0) or 0),
            "storage_budget_bytes": STORAGE_BUDGET_BYTES,
            "storage_budget_mib": STORAGE_BUDGET_MIB,
            "snapshot_id": current_checkpoint.get("source_snapshot_id"),
            "batch_count": len(batches),
            "batches": batches,
            "elapsed_seconds": round(monotonic() - started, 2),
            **extra,
        }

    while True:
        current_checkpoint = crawler.load_checkpoint() or current_checkpoint
        current_count = checkpoint_count(current_checkpoint)
        stored_bytes = int(current_checkpoint.get("stored_bytes", 0) or 0)
        durable_status = current_checkpoint.get("status")

        if current_count >= target:
            return report("target_reached")
        if durable_status == "storage_limit_reached" or stored_bytes >= STORAGE_BUDGET_BYTES:
            return report("storage_limit_reached")
        if durable_status == "complete":
            return report(
                "source_complete_below_target",
                message="The pinned source snapshot is complete but its durable count is below the requested target.",
            )

        remaining_session = session_runtime_seconds - (monotonic() - started)
        if remaining_session <= reserve_seconds:
            break

        before = checkpoint_signature(current_checkpoint)
        next_batch = len(batches) + 1
        run_batch_id = f"{run_id}-part-{next_batch:04d}"
        requested_headwords = min(batch_headwords, target - current_count)
        result = crawler.run_batch(
            max_runtime_seconds=max(1, int(remaining_session - reserve_seconds)),
            max_headwords=requested_headwords,
            max_shard_bytes=max_shard_bytes,
            run_id=run_batch_id,
        )
        current_checkpoint = crawler.load_checkpoint() or current_checkpoint
        after = checkpoint_signature(current_checkpoint)

        batch = result.get("batch", {}) if isinstance(result, dict) else {}
        batches.append({
            "status": result.get("status") if isinstance(result, dict) else "invalid_result",
            "stop_reason": result.get("stop_reason") if isinstance(result, dict) else None,
            "headwords": int(batch.get("headwords", 0) or 0),
            "entries": int(batch.get("entries", 0) or 0),
            "senses": int(batch.get("senses", 0) or 0),
            "compressed_bytes": int(batch.get("compressed_bytes", 0) or 0),
            "shard_path": batch.get("shard_path"),
            "commit_sha": result.get("commit_sha") if isinstance(result, dict) else None,
        })

        status = result.get("status") if isinstance(result, dict) else None
        stop_reason = result.get("stop_reason") if isinstance(result, dict) else None
        if status == "storage_limit_reached":
            return report("storage_limit_reached", last_result=result)
        if status == "shard_size_limit":
            return report("shard_size_limit", last_result=result)
        if status == "up_to_date":
            return report(
                "source_up_to_date_below_target",
                message="The source reports no newer snapshot, but the requested count has not been reached.",
                last_result=result,
            )
        if status not in {"in_progress", "complete"}:
            return report("crawler_error", last_result=result)

        current_count = checkpoint_count(current_checkpoint)
        stored_bytes = int(current_checkpoint.get("stored_bytes", 0) or 0)
        if stored_bytes > STORAGE_BUDGET_BYTES:
            return report("storage_budget_exceeded", last_result=result)
        if current_count >= target:
            return report("target_reached")
        if current_checkpoint.get("status") == "complete":
            return report(
                "source_complete_below_target",
                message="The crawler exhausted the pinned snapshot before reaching the requested count.",
            )

        # A page error or rate limit must not create an immediate endless
        # dispatch loop. Its exact checkpoint remains durable and can be resumed
        # by a later manual launch after the upstream issue clears.
        if stop_reason in {"source_rate_limited", "browse_page_error"}:
            return report("paused_for_source_retry", stop_reason=stop_reason)

        if after == before:
            return report(
                "no_durable_progress",
                message="The crawler returned without changing the durable cursor, counters, or storage.",
                last_result=result,
            )

    if not continue_chain:
        return report("session_budget_reached", continuation_dispatched=False)

    if continuation_dispatcher is None:
        return report(
            "continuation_dispatch_unavailable",
            message="The session ended before the target and no continuation dispatcher was configured.",
        )

    continuation_dispatcher(target_total=target, batch_headwords=batch_headwords)
    return report("continuation_dispatched", continuation_dispatched=True)


def _append_step_summary(result: dict[str, Any]) -> None:
    """Append a human-readable summary to the active GitHub Actions job."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as stream:
        stream.write("# USG external lexical completion launcher\n\n")
        stream.write(f"- Status: **{result.get('status')}**\n")
        stream.write(f"- Target: {int(result.get('target_total', 0)):,}\n")
        stream.write(f"- Initial processed: {int(result.get('initial_processed_headwords', 0)):,}\n")
        stream.write(f"- Final processed: {int(result.get('final_processed_headwords', 0)):,}\n")
        stream.write(f"- Remaining: {int(result.get('remaining_headwords', 0)):,}\n")
        stream.write(
            f"- Stored compressed data: {int(result.get('stored_bytes', 0)):,} / "
            f"{STORAGE_BUDGET_BYTES:,} bytes (700 MiB)\n"
        )
        stream.write(f"- Batches in this Actions run: {int(result.get('batch_count', 0))}\n")
        stream.write(f"- Elapsed seconds: {result.get('elapsed_seconds', 0)}\n")
        if result.get("continuation_dispatched"):
            stream.write("- Continuation: queued through workflow_dispatch\n")
        if result.get("message"):
            stream.write(f"- Note: {result['message']}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Continue the USG external lexical crawl to a cumulative headword target."
    )
    parser.add_argument("--target-total", type=int, default=DEFAULT_TARGET_TOTAL,
                        help="Cumulative checkpoint target; use 0 to use the source snapshot headword count.")
    parser.add_argument("--batch-headwords", type=int, default=DEFAULT_BATCH_HEADWORDS)
    parser.add_argument("--max-session-runtime-seconds", type=int, default=DEFAULT_SESSION_RUNTIME_SECONDS)
    parser.add_argument("--reserve-seconds", type=int, default=DEFAULT_RESERVE_SECONDS)
    parser.add_argument("--max-shard-bytes", type=int, default=DEFAULT_MAX_SHARD_BYTES)
    parser.add_argument("--continue-chain", action="store_true",
                        help="Automatically dispatch another Actions run when this runner's time budget is nearly exhausted.")
    parser.add_argument("--workflow-id", default=WORKFLOW_ID)
    parser.add_argument("--workflow-ref", default=WORKFLOW_REF)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "manual"))
    parser.add_argument("--data-repository", default=os.environ.get("GITHUB_REPOSITORY", "wizekin/USG-Workbench"))
    parser.add_argument("--data-branch", default=os.environ.get("USG_LEXICAL_DATA_BRANCH", DEFAULT_DATA_BRANCH))
    args = parser.parse_args(argv)

    if args.data_repository != "wizekin/USG-Workbench":
        parser.error(
            "The existing LexicalCrawler checkpoint reader is bound to wizekin/USG-Workbench; "
            "use that repository for the durable data branch."
        )

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN or GH_TOKEN is required.")

    publisher = GitHubDataPublisher(args.data_repository, token, args.data_branch)
    crawler = LexicalCrawler(
        publisher=publisher,
        data_branch=args.data_branch,
        delay_seconds=0.35,
        storage_budget_bytes=STORAGE_BUDGET_BYTES,
    )

    def continue_workflow(*, target_total: int, batch_headwords: int) -> None:
        dispatch_continuation(
            token=token,
            repository=args.data_repository,
            workflow_id=args.workflow_id,
            workflow_ref=args.workflow_ref,
            target_total=target_total,
            batch_headwords=batch_headwords,
        )

    try:
        result = run_session(
            crawler,
            target_total=args.target_total,
            batch_headwords=args.batch_headwords,
            session_runtime_seconds=args.max_session_runtime_seconds,
            reserve_seconds=args.reserve_seconds,
            max_shard_bytes=args.max_shard_bytes,
            run_id=args.run_id,
            continue_chain=args.continue_chain,
            continuation_dispatcher=continue_workflow if args.continue_chain else None,
        )
    except Exception as exc:
        print(f"Manual lexical launcher failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    _append_step_summary(result)

    if result["status"] in {"target_reached", "continuation_dispatched"}:
        return 0
    if result["status"] == "session_budget_reached" and not args.continue_chain:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
