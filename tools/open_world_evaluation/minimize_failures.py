"""Bounded delta-debug minimizer for reproducible OW failure cases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from .execute_cases import execute_case
from .score_cases import score_pair


def delta_debug_text(
    text: str,
    preserves_failure: Callable[[str], bool],
    *,
    max_attempts: int = 32,
) -> tuple[str, int]:
    """Delete token chunks while preserving a caller-defined failure signature."""
    if max_attempts < 0:
        raise ValueError("max_attempts must be non-negative")
    tokens = text.split()
    if len(tokens) < 2 or max_attempts == 0:
        return text, 0

    attempts = 0
    granularity = 2
    while len(tokens) >= 2 and attempts < max_attempts:
        chunk_size = (len(tokens) + granularity - 1) // granularity
        reduced = False
        for start in range(0, len(tokens), chunk_size):
            if attempts >= max_attempts:
                break
            candidate_tokens = tokens[:start] + tokens[start + chunk_size:]
            if not candidate_tokens:
                continue
            candidate = " ".join(candidate_tokens)
            attempts += 1
            if preserves_failure(candidate):
                tokens = candidate_tokens
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if not reduced:
            if granularity >= len(tokens):
                break
            granularity = min(len(tokens), granularity * 2)
    return " ".join(tokens), attempts


def failure_signature(score: dict[str, Any]) -> tuple[str, ...] | None:
    outcome = score.get("outcome")
    if score.get("structural_status") == "invalid":
        return ("structural_invalid", *sorted(score.get("failed_checks", [])))
    if outcome in {"timeout", "crashed", "invalid_output"}:
        return (str(outcome),)
    return None


def minimize_failure_case(
    case: dict[str, Any],
    original_score: dict[str, Any],
    *,
    commit_sha: str,
    max_attempts: int = 24,
    max_wall_seconds: float = 15.0,
) -> dict[str, Any] | None:
    """Re-execute candidate reductions and retain only the same stable failure."""
    signature = failure_signature(original_score)
    if signature is None:
        return None

    cache: dict[str, bool] = {}

    def preserves(candidate_text: str) -> bool:
        if candidate_text in cache:
            return cache[candidate_text]
        candidate = json.loads(json.dumps(case, ensure_ascii=False))
        candidate["input"]["text"] = candidate_text
        candidate["input"]["utf8_sha256"] = hashlib.sha256(candidate_text.encode("utf-8")).hexdigest()
        record = execute_case(
            candidate, commit_sha=commit_sha, max_wall_seconds=max_wall_seconds
        )
        candidate_score = score_pair(candidate, record)
        keep = failure_signature(candidate_score) == signature
        cache[candidate_text] = keep
        return keep

    minimized_text, attempts = delta_debug_text(
        case["input"]["text"], preserves, max_attempts=max_attempts
    )
    if minimized_text == case["input"]["text"]:
        return None

    minimized_case = json.loads(json.dumps(case, ensure_ascii=False))
    minimized_hash = hashlib.sha256(minimized_text.encode("utf-8")).hexdigest()
    minimized_case["case_id"] = "OW-MIN-" + hashlib.sha256(
        (case["case_id"] + ":" + minimized_hash).encode("utf-8")
    ).hexdigest()[:24].upper()
    minimized_case["input"]["text"] = minimized_text
    minimized_case["input"]["utf8_sha256"] = minimized_hash
    generator = minimized_case.get("generator", {})
    generator.setdefault("generation_trace", []).append(
        f"minimized_from={case['case_id']}"
    )
    generator.setdefault("mutation_ops", []).append("bounded_delta_debug_minimization")
    record = execute_case(
        minimized_case, commit_sha=commit_sha, max_wall_seconds=max_wall_seconds
    )
    score = score_pair(minimized_case, record)
    if failure_signature(score) != signature:
        return None
    return {
        "original_case_id": case["case_id"],
        "minimized_case_id": minimized_case["case_id"],
        "attempts": attempts,
        "original_text_sha256": case["input"]["utf8_sha256"],
        "minimized_text_sha256": minimized_hash,
        "original_text": case["input"]["text"],
        "minimized_text": minimized_text,
        "failure_signature": list(signature),
        "case": minimized_case,
        "execution_result": record,
        "score_result": score,
    }


def minimize_files(
    cases_path: Path,
    results_path: Path,
    scores_path: Path,
    output_path: Path,
    *,
    commit_sha: str,
    max_cases: int = 5,
    max_attempts: int = 24,
) -> int:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite minimized reproducer file: {output_path}")
    def read(path: Path) -> list[dict[str, Any]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    cases = read(cases_path)
    results = read(results_path)
    scores = read(scores_path)
    by_case = {item["case_id"]: item for item in cases}
    by_attempt = {item["attempt_id"]: item for item in scores}
    count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        for record in results:
            if count >= max_cases:
                break
            score = by_attempt.get(record.get("attempt_id"))
            case = by_case.get(record.get("case_id"))
            if not score or not case or failure_signature(score) is None:
                continue
            minimized = minimize_failure_case(
                case, score, commit_sha=commit_sha, max_attempts=max_attempts,
            )
            if minimized is not None:
                stream.write(json.dumps(minimized, ensure_ascii=False, sort_keys=True) + "\n")
                stream.flush()
                count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Minimize a bounded number of OW structural/runtime failures.")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--max-cases", type=int, default=5)
    parser.add_argument("--max-attempts", type=int, default=24)
    args = parser.parse_args(argv)
    if not 1 <= args.max_cases <= 100 or not 0 <= args.max_attempts <= 128:
        parser.error("--max-cases must be 1..100 and --max-attempts 0..128")
    try:
        count = minimize_files(
            args.cases, args.results, args.scores, args.output,
            commit_sha=args.commit_sha, max_cases=args.max_cases,
            max_attempts=args.max_attempts,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(f"Minimized reproducer cases written: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
