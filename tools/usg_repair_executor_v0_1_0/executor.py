"""Bounded, deterministic repair-plan executor; never runs plan-supplied commands."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any, Callable

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - reported as a safe rejection by the CLI
    Draft202012Validator = None  # type: ignore[assignment]

CONTRACT = "USG-BOUNDED-REPAIR-PLAN/0.1.0"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-bounded-repair-plan-0.1.0.schema.json"
MAX_PATCHES = 5
MAX_FILE_BYTES = 256_000
MAX_TOTAL_PATCH_BYTES = 64_000
MAX_TOTAL_CHANGED_BYTES = 1_000_000
MAX_TOTAL_RUNTIME_SECONDS = 300
MAX_COMMAND_RUNTIME_SECONDS = 120

VALIDATION_PROFILES: dict[str, tuple[tuple[str, ...], ...]] = {
    "system_evidence_github_actions": (
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_system_evidence_github_actions.py", "-v"),
    ),
    "system_evidence": (
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_system_evidence_*.py", "-v"),
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_phase8_integrated_acceptance.py", "-v"),
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_long_term_plan_sync.py", "-v"),
    ),
    "open_world": (
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_open_world_campaign.py", "-v"),
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_open_world_replay.py", "-v"),
    ),
    "pud": (
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_pud_structural_frequency.py", "-v"),
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_pud_naturalistic_pilot.py", "-v"),
    ),
    "phase4_phase5_smoke": (
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_phase4_benchmark.py", "-v"),
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_phase5_benchmark.py", "-v"),
    ),
    "replay_smoke": (
        ("python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_open_world_replay.py", "-v"),
    ),
}

SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

FORBIDDEN_PATH_PARTS = {
    "implementations", "resources", "lexical", "lexicon", "gold", "semantic-gold",
    "active-runtime", "runtime-semantics", "usg-sem",
    "phase1", "phase2", "phase3", "phase4", "phase5",
}


class RepairRejected(ValueError):
    """A repair plan violates the executor's fixed policy."""


def _redact(value: str, limit: int = 4000) -> str:
    text = value
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[-limit:]


def git_blob_sha1(payload: bytes) -> str:
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


def _schema() -> dict[str, Any]:
    if Draft202012Validator is None:
        raise RepairRejected("jsonschema dependency is unavailable")
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepairRejected(f"repair plan schema unavailable: {type(exc).__name__}") from exc


def validate_plan(plan: dict[str, Any]) -> None:
    schema = _schema()
    errors = sorted(Draft202012Validator(schema).iter_errors(plan), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        where = "/".join(str(part) for part in first.path) or "$"
        raise RepairRejected(f"plan schema rejected {where}: {first.message}")
    if plan.get("contract") != CONTRACT:
        raise RepairRejected("unsupported repair-plan contract")
    if len(plan.get("patches", [])) > MAX_PATCHES:
        raise RepairRejected("patch count exceeds the fixed limit")


def _allowed_path(scope: str, relative: str) -> bool:
    filename = relative.rsplit("/", 1)[-1]
    if scope == "ci":
        return relative.startswith(".github/workflows/") or (
            relative.startswith("tests/test_")
            and relative.endswith(".py")
            and filename.startswith((
                "test_system_evidence_", "test_open_world_", "test_pud_",
                "test_usg_repair_executor", "test_phase8_", "test_long_term_plan_sync",
            ))
        )
    if scope == "reporting":
        return relative.startswith((
            "tools/system_evidence/",
            "tools/open_world_evaluation/",
            "documentation/",
            "evaluations/system-wide/",
        ))
    if scope == "packaging":
        return relative.startswith("tools/open_world_evaluation/") or (
            relative.startswith("evaluations/open-world/campaigns/")
            and relative.endswith("/bundle-manifest.json")
        )
    if scope == "regression_fixture":
        return relative.startswith((
            "tests/fixtures/diagnostics/",
            "tests/fixtures/regressions/",
        ))
    return False


def _resolve_existing_file(root: Path, relative: str, scope: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or "\0" in relative:
        raise RepairRejected("patch path must be a non-empty POSIX relative path")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise RepairRejected("absolute, dot, and parent-traversal paths are forbidden")
    if any(part.lower() in FORBIDDEN_PATH_PARTS for part in pure.parts):
        raise RepairRejected("patch targets a protected runtime, resource, lexical, gold, or Phase 1-5 path")
    if not _allowed_path(scope, relative):
        raise RepairRejected(f"path is outside the allowlist for scope {scope}")
    cursor = root
    for part in pure.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RepairRejected("symlink paths are forbidden")
    try:
        resolved = cursor.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise RepairRejected("patch target escapes the repository or does not exist") from exc
    if not resolved.is_file():
        raise RepairRejected("patch target must be an existing regular file")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise RepairRejected("patch target exceeds the per-file size limit")
    return resolved


def _is_ancestor(root: Path, base_commit: str, current_commit: str) -> bool:
    if base_commit == current_commit:
        return True
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_commit, current_commit],
            cwd=root, capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _prepare_patches(plan: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    total_patch_bytes = 0
    total_changed_bytes = 0
    for item in plan["patches"]:
        relative = item["path"]
        if relative in seen_paths:
            raise RepairRejected("a plan may patch each file only once")
        seen_paths.add(relative)
        target = _resolve_existing_file(root, relative, item["scope"])
        original = target.read_bytes()
        actual_sha = git_blob_sha1(original)
        if actual_sha != item["expected_git_blob_sha1"]:
            raise RepairRejected(f"stale target blob for {relative}")
        try:
            text = original.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RepairRejected(f"patch target is not UTF-8 text: {relative}") from exc
        for edit in item["edits"]:
            before = edit["match_text"]
            after = edit["replacement_text"]
            expected = edit["expected_occurrences"]
            if before == after:
                raise RepairRejected(f"no-op patch is forbidden: {relative}")
            if text.count(before) != expected:
                raise RepairRejected(
                    f"expected {expected} exact match(es), found {text.count(before)}: {relative}"
                )
            if any(pattern.search(after) for pattern in SECRET_PATTERNS):
                raise RepairRejected(f"replacement appears to contain a secret: {relative}")
            if item["scope"] == "regression_fixture" and re.search(
                r'"(?:gold_label|semantic_gold|semantic_role_gold|semantic_relation_gold|expected_semantic)"\s*:',
                after,
            ):
                raise RepairRejected("regression-fixture patches may not edit semantic gold labels")
            text = text.replace(before, after, expected)
            total_patch_bytes += len(before.encode("utf-8")) + len(after.encode("utf-8"))
            if total_patch_bytes > MAX_TOTAL_PATCH_BYTES:
                raise RepairRejected("repair plan exceeds the total patch-text budget")
        updated = text.encode("utf-8")
        if len(updated) > MAX_FILE_BYTES:
            raise RepairRejected(f"patched file exceeds the per-file size limit: {relative}")
        total_changed_bytes += len(updated)
        if total_changed_bytes > MAX_TOTAL_CHANGED_BYTES:
            raise RepairRejected("repair plan exceeds the total changed-byte budget")
        prepared.append({
            "path": relative,
            "target": target,
            "original": original,
            "updated": updated,
            "before_sha256": hashlib.sha256(original).hexdigest(),
            "after_sha256": hashlib.sha256(updated).hexdigest(),
            "edit_count": len(item["edits"]),
        })
    return prepared


def _validation_environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        upper = key.upper()
        if any(marker in upper for marker in ("TOKEN", "PASSWORD", "SECRET", "API_KEY", "PRIVATE_KEY")):
            env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _run_validation_profile(
    profile: str,
    root: Path,
    command_runner: Callable[..., Any] = subprocess.run,
) -> tuple[list[dict[str, Any]], bool]:
    commands = VALIDATION_PROFILES.get(profile)
    if commands is None:
        raise RepairRejected("validation profile is not registered")
    deadline = time.monotonic() + MAX_TOTAL_RUNTIME_SECONDS
    results: list[dict[str, Any]] = []
    env = _validation_environment()
    for command in commands:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            results.append({"command_id": " ".join(command), "status": "timeout", "returncode": None})
            return results, False
        timeout = max(1, min(MAX_COMMAND_RUNTIME_SECONDS, int(remaining)))
        started = time.monotonic()
        try:
            completed = command_runner(
                list(command), cwd=root, capture_output=True, text=True,
                timeout=timeout, check=False, env=env,
            )
            returncode = int(completed.returncode)
            stdout = _redact(str(getattr(completed, "stdout", "")))
            stderr = _redact(str(getattr(completed, "stderr", "")))
            status = "passed" if returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            returncode, stdout, stderr, status = None, "", "registered validation timed out", "timeout"
        except Exception as exc:  # the fixed runner may fail, but never changes the allowlist
            returncode, stdout, stderr, status = None, "", f"{type(exc).__name__}: {_redact(str(exc), 500)}", "runner_error"
        results.append({
            "command_id": " ".join(command),
            "status": status,
            "returncode": returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": stdout,
            "stderr_tail": stderr,
        })
        if status != "passed":
            return results, False
    return results, True


def _write_result(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execute_plan(
    plan: dict[str, Any],
    root: Path,
    current_commit: str,
    *,
    apply: bool = False,
    result_path: Path | None = None,
    ancestor_checker: Callable[[Path, str, str], bool] = _is_ancestor,
    command_runner: Callable[..., Any] = subprocess.run,
) -> tuple[dict[str, Any], int]:
    report: dict[str, Any] = {
        "contract": "USG-BOUNDED-REPAIR-RESULT/0.1.0",
        "repair_id": plan.get("repair_id"),
        "base_commit": plan.get("base_commit"),
        "current_commit": current_commit,
        "status": "rejected",
        "patches": [],
        "tests": [],
        "rollback_note": plan.get("rollback_note"),
        "runtime_semantics_changed": False,
        "candidate_resources_promoted": False,
        "gold_labels_changed": False,
    }
    prepared: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    try:
        validate_plan(plan)
        if not ancestor_checker(root, plan["base_commit"], current_commit):
            raise RepairRejected("plan base commit is not an ancestor of the checked-out commit")
        prepared = _prepare_patches(plan, root)
        report["patches"] = [
            {"path": item["path"], "before_sha256": item["before_sha256"], "after_sha256": item["after_sha256"], "edit_count": item["edit_count"]}
            for item in prepared
        ]
        report["validation_profile"] = plan["validation_profile"]
        report["evidence"] = plan["evidence"]
        if not apply:
            report["status"] = "validated_dry_run"
            _write_result(result_path, report)
            return report, 0

        try:
            for item in prepared:
                item["target"].write_bytes(item["updated"])
                applied.append(item)
        except Exception:
            for item in reversed(applied):
                item["target"].write_bytes(item["original"])
            raise

        tests, passed = _run_validation_profile(plan["validation_profile"], root, command_runner)
        report["tests"] = tests
        if not passed:
            for item in reversed(applied):
                item["target"].write_bytes(item["original"])
            report["status"] = "rolled_back_test_failure"
            _write_result(result_path, report)
            return report, 1

        report["status"] = "applied_validated"
        _write_result(result_path, report)
        return report, 0
    except RepairRejected as exc:
        report["status"] = "rejected"
        report["error"] = _redact(str(exc), 1000)
        _write_result(result_path, report)
        return report, 2
    except Exception as exc:
        for item in reversed(applied):
            try:
                item["target"].write_bytes(item["original"])
            except OSError:
                pass
        report["status"] = "rolled_back_executor_error" if applied else "rejected"
        report["error"] = f"{type(exc).__name__}: {_redact(str(exc), 1000)}"
        _write_result(result_path, report)
        return report, 2


def _load_plan(path: Path, root: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise RepairRejected("plan symlinks are forbidden")
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to((root / "automation" / "repair-plans").resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise RepairRejected("plan must be an existing file under automation/repair-plans") from exc
    if resolved.stat().st_size > 128_000:
        raise RepairRejected("plan symlink or size limit rejected")
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepairRejected(f"plan JSON is invalid: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise RepairRejected("plan root must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--current-commit", default="")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="apply the validated patch set and run its registered tests")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    try:
        plan = _load_plan(args.plan, root)
        current = args.current_commit.strip()
        if not current:
            current = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
                timeout=10, check=True,
            ).stdout.strip()
        report, code = execute_plan(
            plan, root, current, apply=args.apply, result_path=args.result,
        )
    except RepairRejected as exc:
        report = {
            "contract": "USG-BOUNDED-REPAIR-RESULT/0.1.0",
            "status": "rejected",
            "error": _redact(str(exc), 1000),
            "runtime_semantics_changed": False,
            "candidate_resources_promoted": False,
            "gold_labels_changed": False,
        }
        _write_result(args.result, report)
        code = 2
    print(json.dumps({
        "repair_id": report.get("repair_id"),
        "status": report.get("status"),
        "patch_count": len(report.get("patches", [])),
        "validation_profile": report.get("validation_profile"),
        "test_count": len(report.get("tests", [])),
        "runtime_semantics_changed": False,
        "candidate_resources_promoted": False,
        "gold_labels_changed": False,
        "result_path": str(args.result),
    }, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
