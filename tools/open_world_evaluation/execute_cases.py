"""Isolated, allowlisted execution of OW-1 scenario JSONL records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .validate_protocol import validate_instance

ROOT = Path(__file__).resolve().parents[2]
MAX_INLINE_OUTPUT_BYTES = 128 * 1024
MAX_CASES = 100_000


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _commit_sha(explicit: str | None) -> str:
    candidate = explicit or os.environ.get("GITHUB_SHA")
    if not candidate:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        candidate = result.stdout.strip() if result.returncode == 0 else ""
    if len(candidate) != 40 or any(char not in "0123456789abcdef" for char in candidate):
        raise ValueError("a 40-character lowercase tested commit SHA is required")
    return candidate


def _safe_environment(workspace: Path) -> dict[str, str]:
    env: dict[str, str] = {
        "PYTHONPATH": str(ROOT),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "USG_OW_NETWORK_DISABLED": "1",
        "HOME": str(workspace),
        "TMPDIR": str(workspace),
        "TEMP": str(workspace),
        "TMP": str(workspace),
    }
    for key in ("PATH", "SYSTEMROOT", "WINDIR", "LANG", "LC_ALL"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def _outcome_from_payload(payload: dict[str, Any]) -> str:
    outcome = payload.get("outcome")
    allowed = {
        "completed", "unsupported", "ambiguous", "abstained", "partial",
        "invalid_output", "timeout", "crashed", "infrastructure_error",
        "not_executed",
    }
    return outcome if outcome in allowed else "invalid_output"


def _failure_category(outcome: str, target_interface: str) -> str | None:
    if outcome in {"timeout", "crashed", "infrastructure_error"}:
        return "infrastructure"
    if outcome in {"not_executed", "invalid_output"} and target_interface in {
        "browser_ui", "http_api", "cli", "javascript_api"
    }:
        return "api_cli_ui"
    return None


def _make_record(
    case: dict[str, Any],
    commit_sha: str,
    *,
    outcome: str,
    payload: dict[str, Any],
    stdout: bytes,
    stderr: bytes,
    started_at: str,
    finished_at: str,
    duration_ms: float,
    exit_code: int | None,
    timed_out: bool,
    diagnostics: list[str] | None = None,
) -> dict[str, Any]:
    output_bytes = _json_bytes(payload)
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "attempt_id": "OWA-" + uuid.uuid4().hex,
        "case_id": case.get("case_id", "OW-INVALID-CASE"),
        "target": {
            "component_id": case.get("target", {}).get("component_id", "unknown"),
            "component_version": case.get("target", {}).get("component_version", "unknown"),
            "entry_point": case.get("target", {}).get("entry_point", "unknown"),
            "commit_sha": commit_sha,
        },
        "started_at": started_at,
        "finished_at": finished_at,
        "outcome": outcome,
        "execution": {
            "duration_ms": max(0.0, duration_ms),
            "exit_code": exit_code,
            "timed_out": timed_out,
        },
        "capture": {
            "stdout_sha256": _sha256(stdout),
            "stderr_sha256": _sha256(stderr),
            "output_sha256": _sha256(output_bytes),
            "output_media_type": "application/json",
        },
        "validation": {
            "diagnostics": diagnostics or [],
        },
        "scoring": [],
        "artifacts": [],
    }
    if len(output_bytes) <= MAX_INLINE_OUTPUT_BYTES:
        record["capture"]["inline_output"] = payload
    category = _failure_category(outcome, case.get("target", {}).get("interface", "other"))
    if category:
        record["failure_category"] = category
    return record


def _not_executed(
    case: dict[str, Any],
    commit_sha: str,
    reason: str,
    *,
    started_at: str | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    payload = {"outcome": "not_executed", "reason": reason}
    record = _make_record(
        case, commit_sha, outcome="not_executed", payload=payload,
        stdout=b"", stderr=b"", started_at=started_at or now,
        finished_at=now, duration_ms=0.0, exit_code=None,
        timed_out=False, diagnostics=[reason],
    )
    return record


def execute_case(
    case: dict[str, Any],
    *,
    commit_sha: str,
    max_wall_seconds: float = 60.0,
) -> dict[str, Any]:
    """Execute one scenario in a fresh child process using a fixed adapter map."""
    if len(commit_sha) != 40 or any(char not in "0123456789abcdef" for char in commit_sha):
        raise ValueError("commit_sha must be a 40-character lowercase SHA")
    errors = validate_instance("scenario", case)
    if errors:
        return _not_executed(case, commit_sha, "invalid scenario: " + "; ".join(errors))

    requested_bytes = len(case["input"]["text"].encode("utf-8"))
    allowed_bytes = int(case["resource_limits"]["max_input_bytes"])
    if requested_bytes > allowed_bytes:
        return _not_executed(
            case, commit_sha,
            f"input is {requested_bytes} bytes; scenario limit is {allowed_bytes}",
        )

    target_id = case["target"]["component_id"]
    started_at = _utc_now()
    started_clock = time.monotonic()
    requested_wall = float(case["resource_limits"]["wall_time_seconds"])
    wall_seconds = min(requested_wall, float(max_wall_seconds))
    if wall_seconds <= 0:
        return _not_executed(case, commit_sha, "effective wall-time limit must be positive")

    case_json = _json_bytes(case).decode("utf-8")
    try:
        with tempfile.TemporaryDirectory(prefix="usg-ow-case-") as folder:
            workspace = Path(folder)
            child = subprocess.run(
                [sys.executable, "-m", "tools.open_world_evaluation.worker"],
                input=case_json,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=workspace,
                env=_safe_environment(workspace),
                timeout=wall_seconds,
                check=False,
                shell=False,
            )
        stdout = child.stdout.encode("utf-8", errors="replace")
        stderr = child.stderr.encode("utf-8", errors="replace")
        duration_ms = (time.monotonic() - started_clock) * 1000.0
        try:
            payload = json.loads(child.stdout)
            if not isinstance(payload, dict):
                raise ValueError("worker output must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            outcome = "crashed" if child.returncode != 0 else "invalid_output"
            payload = {
                "outcome": outcome,
                "reason": f"worker returned invalid JSON: {exc}",
                "stderr_excerpt": child.stderr[-2000:],
            }
            diagnostics = [payload["reason"]]
        else:
            outcome = _outcome_from_payload(payload)
            diagnostics = []
            if payload.get("reason"):
                diagnostics.append(str(payload["reason"]))
            if child.returncode != 0:
                outcome = "crashed"
                diagnostics.append(f"worker exited with code {child.returncode}")
        record = _make_record(
            case, commit_sha, outcome=outcome, payload=payload,
            stdout=stdout, stderr=stderr, started_at=started_at,
            finished_at=_utc_now(), duration_ms=duration_ms,
            exit_code=child.returncode, timed_out=False,
            diagnostics=diagnostics,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = (time.monotonic() - started_clock) * 1000.0
        raw_stdout = exc.stdout or b""
        raw_stderr = exc.stderr or b""
        if isinstance(raw_stdout, str):
            raw_stdout = raw_stdout.encode("utf-8", errors="replace")
        if isinstance(raw_stderr, str):
            raw_stderr = raw_stderr.encode("utf-8", errors="replace")
        payload = {"outcome": "timeout", "reason": f"case exceeded {wall_seconds:.3f}s wall-time limit"}
        record = _make_record(
            case, commit_sha, outcome="timeout", payload=payload,
            stdout=raw_stdout, stderr=raw_stderr, started_at=started_at,
            finished_at=_utc_now(), duration_ms=duration_ms,
            exit_code=None, timed_out=True, diagnostics=[payload["reason"]],
        )
    except OSError as exc:
        duration_ms = (time.monotonic() - started_clock) * 1000.0
        payload = {
            "outcome": "infrastructure_error",
            "reason": f"could not start isolated worker: {type(exc).__name__}: {exc}",
        }
        record = _make_record(
            case, commit_sha, outcome="infrastructure_error", payload=payload,
            stdout=b"", stderr=str(exc).encode("utf-8"), started_at=started_at,
            finished_at=_utc_now(), duration_ms=duration_ms,
            exit_code=None, timed_out=False, diagnostics=[payload["reason"]],
        )

    validation_errors = validate_instance("execution_result", record)
    if validation_errors:
        raise RuntimeError(
            "OW-3 produced an invalid execution-result record: "
            + "; ".join(validation_errors)
        )
    return record


def load_scenarios(path: Path, *, max_cases: int = MAX_CASES) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"scenario on line {line_number} must be a JSON object")
            cases.append(item)
            if len(cases) > max_cases:
                raise ValueError(f"scenario input exceeds maximum of {max_cases} cases")
    return cases


def execute_file(
    input_path: Path,
    output_path: Path,
    *,
    commit_sha: str,
    max_cases: int = MAX_CASES,
    max_wall_seconds: float = 60.0,
) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite prior execution records: {output_path}")
    cases = load_scenarios(input_path, max_cases=max_cases)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {
        key: 0 for key in (
            "completed", "unsupported", "ambiguous", "abstained", "partial",
            "invalid_output", "timeout", "crashed", "infrastructure_error",
            "not_executed",
        )
    }
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            record = execute_case(
                case, commit_sha=commit_sha, max_wall_seconds=max_wall_seconds
            )
            counts[record["outcome"]] += 1
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
    return {
        "input_cases": len(cases),
        "attempted": sum(counts.values()),
        "outcome_counts": counts,
        "output": str(output_path),
    }


def _positive_float(value: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be numeric") from exc
    if result <= 0 or result > 3600:
        raise argparse.ArgumentTypeError("value must be > 0 and <= 3600")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute OW scenarios in isolated, allowlisted Python workers."
    )
    parser.add_argument("--input", type=Path, required=True, help="scenario JSONL file")
    parser.add_argument("--output", type=Path, required=True, help="new execution-result JSONL file")
    parser.add_argument("--commit-sha", help="exact tested commit (defaults to GITHUB_SHA or git HEAD)")
    parser.add_argument("--max-cases", type=int, default=MAX_CASES)
    parser.add_argument("--max-wall-seconds", type=_positive_float, default=60.0)
    args = parser.parse_args(argv)
    if args.max_cases < 1 or args.max_cases > MAX_CASES:
        parser.error(f"--max-cases must be between 1 and {MAX_CASES}")

    try:
        commit_sha = _commit_sha(args.commit_sha)
        summary = execute_file(
            args.input, args.output, commit_sha=commit_sha,
            max_cases=args.max_cases, max_wall_seconds=args.max_wall_seconds,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
