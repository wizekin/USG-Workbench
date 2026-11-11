"""Historical failure comparison and bounded adaptive robustness-case generation."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .minimize_failures import failure_signature
from .score_cases import load_jsonl
from .validate_protocol import validate_instance

GENERATOR_ID = "usg-open-world-adaptive-discovery"
GENERATOR_VERSION = "1.0.0"
MAX_HISTORY_REPORTS = 100_000
MAX_FOLLOWUPS = 500


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cluster_signature(case: dict[str, Any], score: dict[str, Any]) -> tuple[str, ...] | None:
    base = failure_signature(score)
    if base is None:
        return None
    target = case.get("target", {}).get("component_id", "unknown")
    if base[0] == "structural_invalid":
        return ("structural_invalid", target, *base[1:])
    return (f"runtime_{base[0]}", target)


def cluster_id(signature: tuple[str, ...]) -> tuple[str, str]:
    label = "|".join(signature)
    return "OWCL-" + sha256(label.encode("utf-8"))[:16].upper(), label


def scan_history(root: Path, exclude_campaign_id: str | None = None) -> dict[str, Any]:
    paths = sorted(root.rglob("campaign-report.json")) if root.exists() else []
    if len(paths) > MAX_HISTORY_REPORTS:
        raise ValueError(f"history exceeds {MAX_HISTORY_REPORTS} report files")
    known: dict[str, dict[str, Any]] = {}
    campaigns: list[str] = []
    for path in paths:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cid = report.get("campaign_id")
        if not isinstance(cid, str) or cid == exclude_campaign_id:
            continue
        campaigns.append(cid)
        for cluster in report.get("novel_clusters", []):
            key = cluster.get("cluster_id")
            if isinstance(key, str):
                known.setdefault(key, {
                    "first_seen_campaign_id": cid,
                    "proposed_label": cluster.get("proposed_label"),
                })
    return {
        "campaign_ids": campaigns,
        "history_campaign_count": len(campaigns),
        "known": known,
    }


def whitespace_variants(text: str) -> list[tuple[str, str]]:
    if not text:
        return []
    candidates: list[tuple[str, str]] = []
    if " " in text:
        candidates.extend([
            ("repeated_internal_whitespace", text.replace(" ", "  ")),
            ("nonbreaking_space", text.replace(" ", "\u00a0", 1)),
            ("line_break_internal_whitespace", text.replace(" ", "\n", 1)),
            ("tab_internal_whitespace", text.replace(" ", "\t", 1)),
        ])
    candidates.extend([
        ("leading_trailing_whitespace", " " + text + " "),
        ("leading_line_break", "\n" + text),
        ("trailing_tab", text + "\t"),
    ])
    seen = {text}
    result = []
    for operation, candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append((operation, candidate))
    return result


def make_followup(
    base: dict[str, Any], text: str, operation: str, signature: tuple[str, ...],
    campaign_id: str, created_at: str,
) -> dict[str, Any]:
    origin = base["case_id"]
    master = base.get("generator", {}).get("master_seed")
    if not isinstance(master, str) or len(master) < 16:
        master = sha256(f"{campaign_id}:{origin}".encode())
    digest = sha256(text.encode("utf-8"))
    identity = sha256(f"{campaign_id}:{origin}:{operation}:{digest}".encode())
    case_id = "OW-ADAPT-" + identity[:24].upper()
    cid, label = cluster_id(signature)
    taxonomy = base.get("taxonomy", {})
    labels = list(taxonomy.get("labels", []))
    for tag in ("adaptive_followup", "adaptive_whitespace_robustness", cid):
        if tag not in labels:
            labels.append(tag)
    return {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "population": "unconstrained_random",
        "created_at": created_at,
        "generator": {
            "id": GENERATOR_ID,
            "version": GENERATOR_VERSION,
            "seed_mode": "derived",
            "master_seed": master,
            "case_seed": sha256(f"{master}:{identity}".encode()),
            "generation_trace": [
                f"adaptive_from_campaign={campaign_id}",
                f"origin_case_id={origin}",
                f"failure_cluster_id={cid}",
                f"failure_signature={label}",
            ],
            "mutation_ops": [operation],
        },
        "source": {
            "kind": "synthetic",
            "source_id": f"{GENERATOR_ID}/{GENERATOR_VERSION}",
            "transformations": [operation],
        },
        "input": {
            "text": text,
            "utf8_sha256": digest,
            "language_hint": base.get("input", {}).get("language_hint", "unspecified"),
            "prior_turns": base.get("input", {}).get("prior_turns", []),
        },
        "target": dict(base["target"]),
        "taxonomy": {
            "labels": labels,
            "unclassified": taxonomy.get("unclassified", True),
        },
        "oracle": {"type": "none", "independent": False},
        "resource_limits": dict(base["resource_limits"]),
    }


def build_adaptive_discovery(
    *, campaign_id: str, cases: list[dict[str, Any]],
    results: list[dict[str, Any]], scores: list[dict[str, Any]],
    history_root: Path, max_cases: int = 150,
    variants_per_case: int = 3, created_at: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 0 <= max_cases <= MAX_FOLLOWUPS:
        raise ValueError(f"max_cases must be between 0 and {MAX_FOLLOWUPS}")
    if not 0 <= variants_per_case <= 6:
        raise ValueError("variants_per_case must be between 0 and 6")
    timestamp = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    cases_by_id = {case.get("case_id"): case for case in cases}
    if len(cases_by_id) != len(cases):
        raise ValueError("duplicate scenario case IDs")
    scores_by_attempt = {score.get("attempt_id"): score for score in scores}
    if len(scores_by_attempt) != len(scores):
        raise ValueError("duplicate score attempt IDs")
    history = scan_history(history_root, exclude_campaign_id=campaign_id)
    groups: dict[str, list[tuple[dict[str, Any], tuple[str, ...]]]] = defaultdict(list)
    skipped_diagnostics = skipped_unscored = 0

    for record in results:
        case = cases_by_id.get(record.get("case_id"))
        score = scores_by_attempt.get(record.get("attempt_id"))
        if case is None or score is None:
            skipped_unscored += 1
            continue
        if case.get("population") != "unconstrained_random":
            skipped_diagnostics += 1
            continue
        signature = cluster_signature(case, score)
        if signature is not None:
            cid, _ = cluster_id(signature)
            groups[cid].append((case, signature))

    followups: list[dict[str, Any]] = []
    clusters = []
    for cid, rows in sorted(groups.items()):
        signature = rows[0][1]
        previous = history["known"].get(cid)
        origin_ids = list(dict.fromkeys(row[0]["case_id"] for row in rows))
        clusters.append({
            "cluster_id": cid,
            "proposed_label": "|".join(signature),
            "case_count": len(rows),
            "example_case_ids": origin_ids[:10],
            "target_ids": sorted({row[0]["target"]["component_id"] for row in rows}),
            "historically_observed": previous is not None,
            "first_seen_campaign_id": previous.get("first_seen_campaign_id") if previous else None,
            "discovery_status": "previously_observed" if previous else "not_found_in_scanned_history",
        })
        for case, row_signature in rows:
            if len(followups) >= max_cases:
                break
            for operation, variant in whitespace_variants(case["input"]["text"])[:variants_per_case]:
                if len(followups) >= max_cases:
                    break
                candidate = make_followup(
                    case, variant, operation, row_signature, campaign_id, timestamp
                )
                errors = validate_instance("scenario", candidate)
                if errors:
                    raise ValueError(candidate["case_id"] + ": " + "; ".join(errors))
                followups.append(candidate)

    report = {
        "discovery_version": "1.0.0",
        "campaign_id": campaign_id,
        "created_at": timestamp,
        "history_campaign_count": len(history["campaign_ids"]),
        "history_campaign_ids": history["campaign_ids"],
        "current_failure_cluster_count": len(clusters),
        "historically_observed_cluster_count": sum(x["historically_observed"] for x in clusters),
        "candidate_new_cluster_count": sum(not x["historically_observed"] for x in clusters),
        "adaptive_followup_case_count": len(followups),
        "followup_policy": "Only structural-invalid and runtime failure signatures receive whitespace/format-only follow-ups.",
        "skipped_controlled_diagnostics": skipped_diagnostics,
        "skipped_missing_case_or_score": skipped_unscored,
        "clusters": clusters,
        "limitations": [
            "Not found in scanned history is a candidate-new cluster, not proof of global novelty.",
            "Historical comparison covers only readable campaign reports under the supplied history root.",
            "Formatting variants are robustness probes, not gold-equivalent paraphrases.",
            "Unsupported, ambiguous, partial, and not-executed outcomes are not automatically treated as defects.",
            "Hidden evaluation samples are not implemented; public reports must not contain hidden seeds or supposedly secret cases.",
        ],
    }
    return followups, report


def write_outputs(
    cases: list[dict[str, Any]], report: dict[str, Any],
    cases_path: Path, report_path: Path,
) -> None:
    if cases_path.exists() or report_path.exists():
        raise FileExistsError("refusing to overwrite adaptive discovery outputs")
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with cases_path.open("x", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            stream.write(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n")
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare failure clusters and generate bounded adaptive follow-ups.")
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, default=Path("evaluations/open-world/campaigns"))
    parser.add_argument("--output-cases", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--max-cases", type=int, default=150)
    parser.add_argument("--variants-per-case", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        followups, report = build_adaptive_discovery(
            campaign_id=args.campaign_id,
            cases=load_jsonl(args.cases),
            results=load_jsonl(args.results),
            scores=load_jsonl(args.scores),
            history_root=args.history_root,
            max_cases=args.max_cases,
            variants_per_case=args.variants_per_case,
        )
        write_outputs(followups, report, args.output_cases, args.output_report)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "campaign_id": args.campaign_id,
        "adaptive_followup_case_count": len(followups),
        "current_failure_cluster_count": len(report["clusters"]),
        "candidate_new_cluster_count": report["candidate_new_cluster_count"],
        "history_campaign_count": report["history_campaign_count"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
