"""Build and store append-only OW-5 campaign reports and artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .validate_protocol import OUTCOMES, POPULATIONS, validate_campaign_report
from .validate_protocol import validate_instance
from .growth_diagnostics import build_execution_accounting, build_stage_attribution

ROOT = Path(__file__).resolve().parents[2]
REPORT_SCHEMA = ROOT / "tools" / "open_world_evaluation" / "schemas" / "campaign-report.schema.json"
GENERATOR_VERSION = "1.0.0"
EVALUATOR_VERSION = "1.0.0"
MAX_RECORDS = 100_000


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"record at {path}:{line_number} must be an object")
            rows.append(row)
            if len(rows) > MAX_RECORDS:
                raise ValueError(f"{path} exceeds {MAX_RECORDS} records")
    return rows


def _read_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _safe_campaign_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{10,100}", value):
        raise ValueError("campaign_id must be 11-101 safe ASCII characters")
    return value


def _failure_signature(record: dict[str, Any], score: dict[str, Any] | None) -> str | None:
    outcome = record.get("outcome")
    target_id = record.get("target", {}).get("component_id", "unknown")
    if score and score.get("structural_status") == "invalid":
        checks = sorted(score.get("failed_checks", []))
        suffix = ",".join(checks) if checks else "unspecified"
        return f"structural_invalid|{target_id}|{suffix}"
    if outcome in {"timeout", "crashed", "infrastructure_error", "invalid_output"}:
        return f"runtime_{outcome}|{target_id}"

    payload = record.get("capture", {}).get("inline_output")
    target_result = payload.get("target_result") if isinstance(payload, dict) else None
    if outcome in {"unsupported", "ambiguous", "partial", "abstained"}:
        stages: list[str] = []
        if isinstance(target_result, dict):
            for diagnostic in target_result.get("diagnostics", []):
                if isinstance(diagnostic, dict):
                    stage = diagnostic.get("stage")
                    code = diagnostic.get("code")
                    if stage or code:
                        stages.append(f"{stage or 'unknown'}:{code or 'unspecified'}")
        suffix = ",".join(sorted(set(stages))[:5]) or "no_diagnostic"
        return f"interpretation_{outcome}|{target_id}|{suffix}"
    return None


def _case_coverage(cases: list[dict[str, Any]]) -> dict[str, Any]:
    population_cases = Counter()
    unclassified = Counter()
    labels: dict[str, Counter[str]] = defaultdict(Counter)
    languages = Counter()
    targets = Counter()
    for case in cases:
        population = case.get("population", "unconstrained_random")
        population_cases[population] += 1
        taxonomy = case.get("taxonomy", {})
        if taxonomy.get("unclassified") is True:
            unclassified[population] += 1
        for label in taxonomy.get("labels", []):
            labels[population][str(label)] += 1
        language = case.get("input", {}).get("language_hint", "unspecified")
        languages[str(language)] += 1
        target = case.get("target", {}).get("component_id", "unknown")
        targets[str(target)] += 1
    return {
        "case_count": len(cases),
        "population_case_counts": dict(sorted(population_cases.items())),
        "unclassified_case_counts": dict(sorted(unclassified.items())),
        "taxonomy_label_counts": {
            pop: dict(sorted(counts.items())) for pop, counts in sorted(labels.items())
        },
        "language_hint_counts": dict(sorted(languages.items())),
        "target_case_counts": dict(sorted(targets.items())),
    }


def build_campaign_report(
    *,
    campaign_id: str,
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    tested_commit_sha: str,
    generation_manifest: dict[str, Any] | None = None,
    artifact_entries: list[dict[str, str]] | None = None,
    minimized_reproducers: list[dict[str, Any]] | None = None,
    adaptive_discovery: dict[str, Any] | None = None,
    coverage_ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    campaign_id = _safe_campaign_id(campaign_id)
    if len(tested_commit_sha) != 40 or any(c not in "0123456789abcdef" for c in tested_commit_sha):
        raise ValueError("tested_commit_sha must be a 40-character lowercase Git SHA")

    for index, case in enumerate(cases):
        errors = validate_instance("scenario", case)
        if errors:
            raise ValueError(f"invalid scenario at index {index}: " + "; ".join(errors))
    for index, record in enumerate(results):
        errors = validate_instance("execution_result", record)
        if errors:
            raise ValueError(f"invalid execution result at index {index}: " + "; ".join(errors))
    score_schema_path = ROOT / "tools" / "open_world_evaluation" / "schemas" / "score-result.schema.json"
    score_schema = json.loads(score_schema_path.read_text(encoding="utf-8"))
    score_validator = Draft202012Validator(score_schema, format_checker=FormatChecker())
    for index, score in enumerate(scores):
        errors = list(score_validator.iter_errors(score))
        if errors:
            raise ValueError(f"invalid score result at index {index}: " + "; ".join(error.message for error in errors))

    case_by_id = {case.get("case_id"): case for case in cases}
    if len(case_by_id) != len(cases):
        raise ValueError("scenario file contains duplicate case_id values")
    result_ids = {record.get("case_id") for record in results}
    unknown_result_ids = result_ids - set(case_by_id)
    if unknown_result_ids:
        raise ValueError("execution results refer to unknown case IDs: " + ", ".join(map(str, unknown_result_ids)))
    commit_values = {
        record.get("target", {}).get("commit_sha")
        for record in results
    }
    if commit_values and commit_values != {tested_commit_sha}:
        raise ValueError("all execution results must pin the same tested_commit_sha")

    score_by_attempt = {score.get("attempt_id"): score for score in scores}
    if len(score_by_attempt) != len(scores):
        raise ValueError("score file contains duplicate attempt_id values")
    attempt_ids = {record.get("attempt_id") for record in results}
    if attempt_ids - set(score_by_attempt):
        # Missing score records remain visible as a known gap but don't invalidate a campaign.
        pass
    extra_scores = set(score_by_attempt) - attempt_ids
    if extra_scores:
        raise ValueError("score records refer to unknown attempts")

    outcome_counts = Counter(record.get("outcome") for record in results)
    outcome_counts = {outcome: int(outcome_counts.get(outcome, 0)) for outcome in OUTCOMES}
    population_rows = []
    population_attempt_counts: dict[str, Counter[str]] = {pop: Counter() for pop in POPULATIONS}
    population_case_counts = Counter(case.get("population") for case in cases)
    for record in results:
        case = case_by_id[record["case_id"]]
        population = case.get("population")
        if population in population_attempt_counts:
            population_attempt_counts[population][record.get("outcome")] += 1

    for population in POPULATIONS:
        counts = {
            outcome: int(population_attempt_counts[population].get(outcome, 0))
            for outcome in OUTCOMES
        }
        population_cases = [case for case in cases if case.get("population") == population]
        population_results = [
            row for row in results
            if case_by_id[row["case_id"]].get("population") == population
        ]
        population_rows.append({
            "population": population,
            "attempted": sum(counts.values()),
            "completed": counts["completed"],
            "outcome_counts": counts,
            "coverage": {
                "scenario_count": int(population_case_counts.get(population, 0)),
                "attempted_case_count": len({
                    row["case_id"] for row in population_results
                }),
                "execution_accounting": build_execution_accounting(population_cases, population_results),
            },
        })

    started_values = [row.get("started_at") for row in results if row.get("started_at")]
    finished_values = [row.get("finished_at") for row in results if row.get("finished_at")]
    created_at = _utc_now()
    started_at = min(started_values) if started_values else created_at
    finished_at = max(finished_values) if finished_values else None

    master_seed = None
    generator_version = GENERATOR_VERSION
    if generation_manifest:
        master_seed = generation_manifest.get("master_seed")
        generator_version = generation_manifest.get("generator_version", GENERATOR_VERSION)
    if not master_seed:
        seeds = {
            case.get("generator", {}).get("master_seed")
            for case in cases if case.get("generator", {}).get("master_seed")
        }
        if len(seeds) == 1:
            master_seed = next(iter(seeds))
        elif seeds:
            master_seed = _sha256("|".join(sorted(seeds)).encode("utf-8"))
        else:
            master_seed = _sha256("\n".join(case.get("case_id", "") for case in cases).encode("utf-8"))
    if not isinstance(master_seed, str) or len(master_seed) < 16:
        master_seed = _sha256(str(master_seed).encode("utf-8"))

    signature_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in results:
        score = score_by_attempt.get(record.get("attempt_id"))
        signature = _failure_signature(record, score)
        if signature:
            signature_groups[signature].append(record)

    minimized_by_case: dict[str, str] = {}
    for item in minimized_reproducers or []:
        minimized_by_case[item.get("original_case_id", "")] = item.get("minimized_case_id", "")

    failure_families = []
    novel_clusters = []
    for signature, rows in sorted(signature_groups.items()):
        case_ids = list(dict.fromkeys(row.get("case_id", "") for row in rows))[:5]
        first_case_id = rows[0].get("case_id", "")
        target_ids = sorted({
            row.get("target", {}).get("component_id", "unknown") for row in rows
        })
        category = signature.split("|", 1)[0]
        failure_families.append({
            "category": category,
            "count": len(rows),
            "first_seen_case_id": first_case_id,
            "example_case_ids": case_ids,
        })
        cluster_id = "OWCL-" + _sha256(signature.encode("utf-8"))[:16].upper()
        novel_clusters.append({
            "cluster_id": cluster_id,
            "case_count": len(rows),
            "reviewed": False,
            "proposed_label": signature,
            "example_case_ids": case_ids,
            "target_ids": target_ids,
            "minimized_reproducer_ids": sorted({
                minimized_by_case[case_id]
                for case_id in case_ids if minimized_by_case.get(case_id)
            }),
        })

    result_record_case_ids = {row.get("case_id") for row in results}
    actual_attempt_case_ids = {
        row.get("case_id") for row in results if row.get("outcome") != "not_executed"
    }
    complete_population_coverage = all(population_case_counts.get(pop, 0) > 0 for pop in POPULATIONS)
    if not actual_attempt_case_ids:
        status = "failed"
    elif len(actual_attempt_case_ids) == len(cases) and complete_population_coverage:
        status = "complete"
    else:
        status = "partial"

    report = {
        "schema_version": "1.0.0",
        "campaign_id": campaign_id,
        "status": status,
        "created_at": created_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "repository": "wizekin/USG-Workbench",
        "tested_commit_sha": tested_commit_sha,
        "protocol_version": "1.0.0",
        "generator_version": str(generator_version),
        "evaluator_version": EVALUATOR_VERSION,
        "master_seed": master_seed,
        "attempted": len(results),
        "completed": outcome_counts["completed"],
        "outcome_counts": outcome_counts,
        "population_results": population_rows,
        "coverage": {
            **_case_coverage(cases),
            "execution_result_count": len(results),
            "execution_accounting": build_execution_accounting(cases, results),
            "stage_attribution": build_stage_attribution(cases, results),
            "scored_attempt_count": len(scores),
            "unexecuted_case_count": len(cases) - len(result_record_case_ids),
            "complete_population_coverage": complete_population_coverage,
            "failure_cluster_count": len(novel_clusters),
            "semantic_scored_attempt_count": sum(
                bool(score.get("semantic_scoring", {}).get("metrics")) for score in scores
            ),
            "adaptive_followup_case_count": int(
                (adaptive_discovery or {}).get("adaptive_followup_case_count", 0)
            ),
            "adaptive_failure_cluster_count": int(
                (adaptive_discovery or {}).get("current_failure_cluster_count", 0)
            ),
            "adaptive_candidate_new_cluster_count": int(
                (adaptive_discovery or {}).get("candidate_new_cluster_count", 0)
            ),
            "adaptive_history_campaign_count": int(
                (adaptive_discovery or {}).get("history_campaign_count", 0)
            ),
            "scope_ledger": {
                "inventory_component_count": int((coverage_ledger or {}).get("inventory_component_count", 0)),
                "registered_target_profile_count": int((coverage_ledger or {}).get("registered_target_profile_count", 0)),
                "entrypoint_exercised_component_count": int((coverage_ledger or {}).get("entrypoint_exercised_component_count", 0)),
                "unclassified_case_count": int((coverage_ledger or {}).get("unclassified_case_count", 0)),
                "not_registered_component_ids": list((coverage_ledger or {}).get("not_registered_component_ids", [])),
                "not_executed_only_component_ids": list((coverage_ledger or {}).get("not_executed_only_component_ids", [])),
                "candidate_new_taxonomy_labels": list((coverage_ledger or {}).get("historical_comparison", {}).get("candidate_new_taxonomy_labels", [])),
                "candidate_new_generator_families": list((coverage_ledger or {}).get("historical_comparison", {}).get("candidate_new_generator_families", [])),
            },
        },
        "failure_families": failure_families,
        "novel_clusters": novel_clusters,
        "limitations": [
            "A finite campaign samples a bounded set of cases and cannot prove unrestricted real-world coverage.",
            "Novel clusters are within-campaign groupings and require historical comparison and human review before being called newly discovered failure families.",
            "Structural validation does not establish semantic correctness or factual truth.",
            "Semantic metrics are reported only when independent case-specific oracle adapters are available.",
            "Naturalistic and controlled-diagnostic populations may be empty; missing populations are reported explicitly and keep campaign status partial.",
            "The registered browser-only JavaScript target is not executed until a real browser automation adapter is available.",
            "Process isolation is best-effort containment, not a hardened sandbox for hostile native code.",
        ],
        "artifacts": artifact_entries or [],
    }
    schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report))
    if errors:
        raise ValueError("campaign report schema errors: " + "; ".join(
            f"{list(error.path)}: {error.message}" for error in errors
        ))
    consistency_errors = validate_campaign_report(report)
    if consistency_errors:
        raise ValueError("campaign report consistency errors: " + "; ".join(consistency_errors))
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# USG Open-World Campaign {report['campaign_id']}",
        "",
        f"**Status:** {report['status'].upper()}",
        f"**Tested commit:** `{report['tested_commit_sha']}`",
        f"**Protocol / generator / evaluator:** {report['protocol_version']} / {report['generator_version']} / {report['evaluator_version']}",
        f"**Master seed:** `{report['master_seed']}`",
        f"**Created:** {report['created_at']}",
        "",
        "## Execution outcomes",
        "",
        "| Outcome | Attempts |",
        "|---|---:|",
    ]
    for outcome in OUTCOMES:
        lines.append(f"| {outcome} | {report['outcome_counts'][outcome]} |")
    lines += [
        "",
        f"**Legacy result records (v1.0 attempted field):** {report['attempted']}  ",
        f"**Actual execution attempts:** {report['coverage']['execution_accounting']['actual_attempt_count']}  ",
        f"**Not-executed target records:** {report['coverage']['execution_accounting']['not_executed_record_count']}  ",
        f"**Scenarios with no result record:** {report['coverage']['execution_accounting']['scenario_count_without_result_record']}  ",
        f"**Scenarios with only not-executed records:** {report['coverage']['execution_accounting']['scenario_count_only_not_executed']}  ",
        f"**Completed outcomes:** {report['completed']}  ",
        f"**Scenarios with no result record (legacy field):** {report['coverage']['unexecuted_case_count']}",
        "",
        "## Population coverage",
        "",
        "| Population | Cases | Result records | Actual attempts | Not executed | Completed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in report["population_results"]:
        lines.append(
            f"| {item['population']} | {item['coverage']['scenario_count']} | "
            f"{item['attempted']} | {item['coverage']['execution_accounting']['actual_attempt_count']} | "
            f"{item['coverage']['execution_accounting']['not_executed_record_count']} | {item['completed']} |"
        )
    lines += [
        "",
        "## Target coverage",
        "",
        "| Target | Cases |",
        "|---|---:|",
    ]
    for target, count in report["coverage"]["target_case_counts"].items():
        lines.append(f"| {target} | {count} |")
    scope = report.get("coverage", {}).get("scope_ledger", {})
    lines += [
        "",
        "## Inventory-backed scope coverage",
        "",
        f"- Inventory components: {scope.get('inventory_component_count', 0)}",
        f"- Components with an exercised entry point: {scope.get('entrypoint_exercised_component_count', 0)}",
        f"- Components not registered as open-world targets: {len(scope.get('not_registered_component_ids', []))}",
        f"- Components with only not-executed attempts: {len(scope.get('not_executed_only_component_ids', []))}",
        f"- Unclassified cases retained: {scope.get('unclassified_case_count', 0)}",
        "",
        "An exercised entry point does not mean every capability or interface in that component was tested.",
        "",
        "## Failure and diagnostic clusters",
        "",
    ]
    if report["novel_clusters"]:
        lines += [
            "| Cluster | Cases | Proposed signature |",
            "|---|---:|---|",
        ]
        for cluster in report["novel_clusters"]:
            lines.append(
                f"| {cluster['cluster_id']} | {cluster['case_count']} | "
                f"{cluster.get('proposed_label', 'unlabelled')} |"
            )
    else:
        lines.append("No clusterable unsupported, partial, invalid, or runtime outcomes were recorded.")
    attribution = report.get("coverage", {}).get("stage_attribution", {})
    lines += [
        "",
        "## First blocking stage and downstream diagnostic impact",
        "",
        attribution.get("causality_warning", "Attribution is heuristic; review individual cases."),
        "",
        f"- Actual attempts analyzed: {attribution.get('analyzed_actual_attempt_count', 0)}",
        f"- Attempts without target-result payload: {attribution.get('records_without_target_result_payload', 0)}",
        f"- Attempts without observed blocking diagnostics: {attribution.get('records_without_observed_blocking_diagnostic', 0)}",
        "",
        "| First blocking stage | Cases | Later-stage blocker co-occurrences |",
        "|---|---:|---:|",
    ]
    first_counts = attribution.get("first_blocking_stage_counts", {})
    later_counts = attribution.get("later_blocking_stage_cooccurrence_counts", {})
    for stage in sorted(set(first_counts) | set(later_counts)):
        lines.append(f"| {stage} | {first_counts.get(stage, 0)} | {later_counts.get(stage, 0)} |")
    lines += [
        "",
        "### Examples",
        "",
    ]
    for stage, case_ids in attribution.get("example_case_ids_by_first_blocking_stage", {}).items():
        lines.append(f"- **{stage}:** " + ", ".join(f"`{case_id}`" for case_id in case_ids))
    adaptive = report.get("coverage", {})
    lines += [
        "",
        "## Adaptive discovery",
        "",
        f"- Follow-up cases generated: {adaptive.get('adaptive_followup_case_count', 0)}",
        f"- Failure clusters compared: {adaptive.get('adaptive_failure_cluster_count', 0)}",
        f"- Candidate-new clusters: {adaptive.get('adaptive_candidate_new_cluster_count', 0)}",
        f"- Prior reports scanned: {adaptive.get('adaptive_history_campaign_count', 0)}",
        "",
        "Candidate-new means not found in the scanned history, not globally novel. Human review remains required.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines += [
        "",
        "## Artifacts",
        "",
    ]
    for artifact in report["artifacts"]:
        lines.append(f"- `{artifact['name']}` — SHA-256 `{artifact['sha256']}`")
    lines += [
        "",
        "This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.",
        "",
    ]
    return "\n".join(lines)


def _exclusive_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _copy_exclusive(source: Path, destination: Path) -> None:
    _exclusive_write(destination, source.read_bytes())


def store_campaign_bundle(
    *,
    campaign_id: str,
    cases_path: Path,
    results_path: Path,
    scores_path: Path,
    output_root: Path,
    tested_commit_sha: str,
    generation_manifest_path: Path | None = None,
    minimized_reproducers_path: Path | None = None,
    adaptive_followups_path: Path | None = None,
    adaptive_discovery_path: Path | None = None,
    coverage_ledger_path: Path | None = None,
) -> Path:
    campaign_id = _safe_campaign_id(campaign_id)
    final_dir = output_root / campaign_id
    if final_dir.exists():
        raise FileExistsError(f"campaign directory already exists; append-only storage refuses overwrite: {final_dir}")
    output_root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{campaign_id}.", dir=output_root))
    try:
        inputs = [
            ("scenario-cases.jsonl", cases_path),
            ("execution-results.jsonl", results_path),
            ("score-results.jsonl", scores_path),
        ]
        if generation_manifest_path is not None:
            inputs.append(("generation-manifest.json", generation_manifest_path))
        if minimized_reproducers_path is not None:
            inputs.append(("minimized-reproducers.jsonl", minimized_reproducers_path))
        if adaptive_followups_path is not None:
            inputs.append(("adaptive-followup-cases.jsonl", adaptive_followups_path))
        if adaptive_discovery_path is not None:
            inputs.append(("adaptive-discovery.json", adaptive_discovery_path))
        if coverage_ledger_path is not None:
            inputs.append(("coverage-ledger.json", coverage_ledger_path))

        artifact_entries = []
        for name, source in inputs:
            data = source.read_bytes()
            _exclusive_write(temp_dir / name, data)
            artifact_entries.append({
                "name": name,
                "uri": name,
                "sha256": _sha256(data),
            })

        cases = _read_jsonl(temp_dir / "scenario-cases.jsonl")
        results = _read_jsonl(temp_dir / "execution-results.jsonl")
        scores = _read_jsonl(temp_dir / "score-results.jsonl")
        manifest = _read_optional_json(temp_dir / "generation-manifest.json") if (temp_dir / "generation-manifest.json").exists() else None
        minimized = _read_jsonl(temp_dir / "minimized-reproducers.jsonl") if (temp_dir / "minimized-reproducers.jsonl").exists() else []
        adaptive = _read_optional_json(temp_dir / "adaptive-discovery.json") if (temp_dir / "adaptive-discovery.json").exists() else None
        coverage_ledger = _read_optional_json(temp_dir / "coverage-ledger.json") if (temp_dir / "coverage-ledger.json").exists() else None

        report = build_campaign_report(
            campaign_id=campaign_id,
            cases=cases,
            results=results,
            scores=scores,
            tested_commit_sha=tested_commit_sha,
            generation_manifest=manifest,
            artifact_entries=artifact_entries,
            minimized_reproducers=minimized,
            adaptive_discovery=adaptive,
            coverage_ledger=coverage_ledger,
        )
        report_bytes = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        markdown_bytes = render_markdown(report).encode("utf-8")
        _exclusive_write(temp_dir / "campaign-report.json", report_bytes)
        _exclusive_write(temp_dir / "campaign-report.md", markdown_bytes)

        bundle_files = sorted(
            path for path in temp_dir.iterdir()
            if path.is_file() and path.name != "bundle-manifest.json"
        )
        bundle_manifest = {
            "manifest_version": "1.0.0",
            "campaign_id": campaign_id,
            "append_only": True,
            "tested_commit_sha": tested_commit_sha,
            "created_at": report["created_at"],
            "files": [
                {
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path.read_bytes()),
                }
                for path in bundle_files
            ],
        }
        _exclusive_write(
            temp_dir / "bundle-manifest.json",
            (json.dumps(bundle_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )

        # Rename publishes the complete directory atomically. It never replaces an existing campaign.
        if final_dir.exists():
            raise FileExistsError(f"campaign directory appeared during write: {final_dir}")
        os.rename(temp_dir, final_dir)
        return final_dir
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and append an immutable campaign report bundle."
    )
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--generation-manifest", type=Path)
    parser.add_argument("--minimized-reproducers", type=Path)
    parser.add_argument("--adaptive-followups", type=Path)
    parser.add_argument("--adaptive-discovery-report", type=Path)
    parser.add_argument("--coverage-ledger", type=Path)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("evaluations/open-world/campaigns"),
    )
    args = parser.parse_args(argv)
    try:
        result = store_campaign_bundle(
            campaign_id=args.campaign_id,
            cases_path=args.cases,
            results_path=args.results,
            scores_path=args.scores,
            output_root=args.output_root,
            tested_commit_sha=args.commit_sha,
            generation_manifest_path=args.generation_manifest,
            minimized_reproducers_path=args.minimized_reproducers,
            adaptive_followups_path=args.adaptive_followups,
            adaptive_discovery_path=args.adaptive_discovery_report,
            coverage_ledger_path=args.coverage_ledger,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(f"Stored append-only campaign: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())