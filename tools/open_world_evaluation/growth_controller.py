"""Evidence-driven USG growth planner.

This controller aggregates reproducible evaluation evidence and ranks safe next
investigations. It never edits interpreter code, promotes candidate resources,
or changes accepted semantic contracts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .growth_diagnostics import build_stage_attribution

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAX_CAMPAIGNS = 10
MAX_JSONL_RECORDS = 100_000
POLICY_ID = "USG-GROWTH-POLICY/0.1.0"

STAGE_ACTIONS = {
    "lexical": {
        "workstream": "lexical_evidence",
        "action": "Investigate unresolved and ambiguous lexical evidence; add candidate-only source coverage and morphology regressions.",
        "acceptance_gate": "independent_lexical_evaluation",
        "runtime_change_allowed": False,
    },
    "syntax": {
        "workstream": "syntax_constructions",
        "action": "Cluster recurring construction failures and add minimal positive, negative, ambiguous, and boundary fixtures before proposing a rule.",
        "acceptance_gate": "independent_construction_gold",
        "runtime_change_allowed": False,
    },
    "operators": {
        "workstream": "operator_scope",
        "action": "Create explicit scope fixtures for the recurring operator diagnostics and compare alternative scopes against independent gold.",
        "acceptance_gate": "operator_scope_gold",
        "runtime_change_allowed": False,
    },
    "semantic_composition": {
        "workstream": "semantic_composition",
        "action": "Trace the lexical and syntactic inputs to unresolved compositions; define independently reviewed semantic frames and counterexamples.",
        "acceptance_gate": "independent_semantic_gold",
        "runtime_change_allowed": False,
    },
    "discourse": {
        "workstream": "discourse_reference",
        "action": "Build reference-resolution cases with competing antecedents, explicit ambiguity, and discourse-boundary negatives.",
        "acceptance_gate": "independent_discourse_gold",
        "runtime_change_allowed": False,
    },
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must be a JSON object")
            rows.append(value)
            if len(rows) > MAX_JSONL_RECORDS:
                raise ValueError(f"{path} exceeds {MAX_JSONL_RECORDS} records")
    return rows


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _campaigns(root: Path, max_campaigns: int) -> list[Path]:
    base = root / "evaluations" / "open-world" / "campaigns"
    if not base.is_dir():
        return []
    entries: list[tuple[str, Path]] = []
    for directory in base.iterdir():
        if not directory.is_dir():
            continue
        report_path = directory / "campaign-report.json"
        cases_path = directory / "scenario-cases.jsonl"
        results_path = directory / "execution-results.jsonl"
        if not (report_path.is_file() and cases_path.is_file() and results_path.is_file()):
            continue
        try:
            report = _read_json(report_path)
            sort_key = str(report.get("created_at") or "")
        except (OSError, ValueError, json.JSONDecodeError):
            sort_key = ""
        entries.append((sort_key, directory))
    entries.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    return [directory for _, directory in entries[:max_campaigns]]


def _evidence_file(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        return {"path": relative, "status": "missing"}
    return {
        "path": relative,
        "status": "available",
        "sha256": _sha256(path.read_bytes()),
    }


def build_growth_plan(
    root: Path = ROOT,
    *,
    max_campaigns: int = DEFAULT_MAX_CAMPAIGNS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if isinstance(max_campaigns, bool) or not 1 <= max_campaigns <= 100:
        raise ValueError("max_campaigns must be between 1 and 100")

    campaign_summaries: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    diagnostic_counts: dict[str, Counter[str]] = defaultdict(Counter)
    campaign_recurrence: Counter[str] = Counter()
    example_ids: dict[str, list[str]] = defaultdict(list)
    languages: dict[str, set[str]] = defaultdict(set)
    targets: dict[str, set[str]] = defaultdict(set)
    populations: dict[str, set[str]] = defaultdict(set)
    resource_fingerprints: dict[str, set[str]] = defaultdict(set)
    accounting_warnings: list[dict[str, Any]] = []

    for directory in _campaigns(root, max_campaigns):
        report_path = directory / "campaign-report.json"
        cases_path = directory / "scenario-cases.jsonl"
        results_path = directory / "execution-results.jsonl"
        report = _read_json(report_path)
        cases = _read_jsonl(cases_path)
        results = _read_jsonl(results_path)
        attribution = build_stage_attribution(cases, results)
        campaign_id = str(report.get("campaign_id") or directory.name)
        first_counts = attribution.get("first_blocking_stage_counts", {})
        for stage, count in first_counts.items():
            stage_counts[stage] += int(count)
            campaign_recurrence[stage] += 1
        for stage, codes in attribution.get("first_blocking_diagnostic_counts", {}).items():
            for code, count in codes.items():
                diagnostic_counts[stage][code] += int(count)
        for stage, ids in attribution.get("example_case_ids_by_first_blocking_stage", {}).items():
            for case_id in ids:
                if case_id not in example_ids[stage] and len(example_ids[stage]) < 20:
                    example_ids[stage].append(case_id)
        for group in attribution.get("breakdown_by_target_population_language", []):
            stage_group_counts = group.get("first_blocking_stage_counts", {})
            for stage in stage_group_counts:
                languages[stage].add(str(group.get("language", "unspecified")))
                targets[stage].add(str(group.get("target_id", "unknown")))
                populations[stage].add(str(group.get("population", "unknown")))
                fingerprint = str(group.get("resource_fingerprint", "unknown"))
                if fingerprint != "unknown":
                    resource_fingerprints[stage].add(fingerprint)
        if attribution.get("unconfigured_target_record_counts"):
            accounting_warnings.append({
                "campaign_id": campaign_id,
                "kind": "unconfigured_targets",
                "counts": attribution["unconfigured_target_record_counts"],
            })
        if attribution.get("pipeline_version_mismatch_record_counts"):
            accounting_warnings.append({
                "campaign_id": campaign_id,
                "kind": "pipeline_version_mismatch",
                "counts": attribution["pipeline_version_mismatch_record_counts"],
                "identity_counts": attribution.get("pipeline_identity_mismatch_record_counts", {}),
            })
        campaign_summaries.append({
            "campaign_id": campaign_id,
            "created_at": report.get("created_at"),
            "status": report.get("status"),
            "tested_commit_sha": report.get("tested_commit_sha"),
            "scenario_count": len(cases),
            "execution_result_count": len(results),
            "outcome_counts": report.get("outcome_counts", {}),
            "first_blocking_stage_counts": first_counts,
            "first_blocking_diagnostic_counts": attribution.get("first_blocking_diagnostic_counts", {}),
            "case_file_sha256": _sha256(cases_path.read_bytes()),
            "result_file_sha256": _sha256(results_path.read_bytes()),
            "report_file_sha256": _sha256(report_path.read_bytes()),
        })

    actions: list[dict[str, Any]] = []
    for stage, count in stage_counts.items():
        profile = STAGE_ACTIONS.get(stage, {
            "workstream": "diagnostic_registry",
            "action": "Review the unrecognized stage diagnostics and register an explicit target-specific dependency profile before proposing runtime changes.",
            "acceptance_gate": "diagnostic_contract_review",
            "runtime_change_allowed": False,
        })
        recurrence = campaign_recurrence[stage]
        language_set = sorted(languages[stage])
        target_set = sorted(targets[stage])
        population_set = sorted(populations[stage])
        score = count + recurrence * 3 + len(language_set) * 2 + len(target_set)
        actions.append({
            "action_id": "GROWTH-" + stage.upper(),
            "priority_score": score,
            "observed_first_blocker_records": count,
            "campaign_recurrence_count": recurrence,
            "workstream": profile["workstream"],
            "stage": stage,
            "first_blocking_diagnostic_counts": dict(sorted(diagnostic_counts[stage].items())),
            "languages": language_set,
            "targets": target_set,
            "populations": population_set,
            "resource_fingerprints": sorted(resource_fingerprints[stage]),
            "example_case_ids": example_ids[stage],
            "proposed_action": profile["action"],
            "acceptance_gate": profile["acceptance_gate"],
            "runtime_change_allowed": profile["runtime_change_allowed"],
            "requires_independent_evidence": True,
        })
    actions.sort(key=lambda item: (-item["priority_score"], item["stage"]))

    assessment_path = "evaluations/system-wide/2026-11-12/assessment.json"
    matrix_path = "evaluations/system-wide/cross-implementation-matrix-2026-11-12.json"
    assessment = _read_json(root / assessment_path) if (root / assessment_path).is_file() else {}
    matrix = _read_json(root / matrix_path) if (root / matrix_path).is_file() else {}
    lexical = assessment.get("lexical_diagnostics", {})
    open_world = assessment.get("open_world", {})
    cross_gates = matrix.get("cross_implementation_gates", [])
    not_started_gates = [
        item.get("id") for item in cross_gates if item.get("status") != "complete"
    ]
    baseline = {
        "assessment_id": assessment.get("assessment_id"),
        "open_world_naturalistic_cases_at_assessment": open_world.get("populations", {}).get("naturalistic", 0),
        "external_lexical_headwords_at_assessment": lexical.get("crawl_processed_headwords"),
        "external_lexical_exact_surface_coverage": lexical.get("external_pud_exact_surface_coverage"),
        "external_lexical_oov_rate": lexical.get("external_pud_oov_rate"),
        "phase6_step_6_6_status": assessment.get("phase_benchmarks", {}).get("phase6", {}).get("step_6_6"),
        "cross_implementation_gates_not_complete": not_started_gates,
    }
    evidence = [
        _evidence_file(root, assessment_path),
        _evidence_file(root, matrix_path),
        _evidence_file(root, "documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md"),
        _evidence_file(root, "documentation/USG-GROWTH-POLICY-AND-AUTONOMY.md"),
    ]
    return {
        "contract": "USG-EVIDENCE-DRIVEN-GROWTH-PLAN/0.1.0",
        "policy_id": POLICY_ID,
        "generated_at": generated_at or _utc_now(),
        "campaigns_analyzed": len(campaign_summaries),
        "campaigns": campaign_summaries,
        "baseline": baseline,
        "ranked_actions": actions,
        "diagnostic_accounting_warnings": accounting_warnings,
        "evidence_sources": evidence,
        "safety_policy": {
            "runtime_mutations_performed": False,
            "candidate_lexical_data_promoted": False,
            "semantic_contracts_changed": False,
            "automatic_runtime_promotion_allowed": False,
            "all_proposals_require_independent_evidence": True,
        },
        "limitations": [
            "First-blocker counts identify diagnostic starting points, not proven causes.",
            "Repeated failures are weighted by campaign recurrence; this is prioritization, not a semantic-quality score.",
            "Historical baseline figures are not silently replaced by newer measurements.",
            "No naturalistic corpus or independent semantic gold is inferred when absent.",
        ],
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# USG Evidence-Driven Growth Plan",
        "",
        f"Generated: {plan['generated_at']}",
        f"Campaigns analyzed: {plan['campaigns_analyzed']}",
        "",
        "## Baseline warnings",
        "",
        f"- Naturalistic cases in the assessment baseline: {plan['baseline'].get('open_world_naturalistic_cases_at_assessment', 'unknown')}",
        f"- External lexical exact-surface coverage in the assessment baseline: {plan['baseline'].get('external_lexical_exact_surface_coverage', 'unknown')}",
        f"- External lexical OOV rate in the assessment baseline: {plan['baseline'].get('external_lexical_oov_rate', 'unknown')}",
        f"- Phase 6 Step 6.6: {plan['baseline'].get('phase6_step_6_6_status', 'unknown')}",
        "",
        "## Ranked evidence-backed investigations",
        "",
    ]
    if not plan["ranked_actions"]:
        lines.append("No registered first-blocking-stage diagnostics were available in the selected campaigns.")
    for index, action in enumerate(plan["ranked_actions"], 1):
        lines += [
            f"### {index}. {action['stage']} — score {action['priority_score']}",
            "",
            f"- First-blocker records: {action['observed_first_blocker_records']}",
            f"- Campaign recurrence: {action['campaign_recurrence_count']}",
            f"- Diagnostic codes: {json.dumps(action['first_blocking_diagnostic_counts'], ensure_ascii=False, sort_keys=True)}",
            f"- Languages: {', '.join(action['languages']) or 'unknown'}",
            f"- Targets: {', '.join(action['targets']) or 'unknown'}",
            f"- Populations: {', '.join(action['populations']) or 'unknown'}",
            f"- Example cases: {', '.join(action['example_case_ids']) or 'none'}",
            f"- Proposed next action: {action['proposed_action']}",
            f"- Acceptance gate: {action['acceptance_gate']}",
            "- Runtime change allowed by this plan: no",
            "",
        ]
    lines += [
        "## Safety",
        "",
        "- This planner ranks investigations; it does not edit runtime code or resources.",
        "- Lexical resources remain candidate-only until independently evaluated and separately accepted.",
        "- Semantic rule and contract changes require independent gold and explicit acceptance.",
        "- Agreement between implementations is not treated as semantic correctness.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an evidence-driven USG growth plan.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--max-campaigns", type=int, default=DEFAULT_MAX_CAMPAIGNS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)
    plan = build_growth_plan(args.root, max_campaigns=args.max_campaigns)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps({
        "contract": plan["contract"],
        "campaigns_analyzed": plan["campaigns_analyzed"],
        "ranked_action_count": len(plan["ranked_actions"]),
        "top_action": plan["ranked_actions"][0]["action_id"] if plan["ranked_actions"] else None,
        "output": str(args.output),
        "markdown": str(args.markdown),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
