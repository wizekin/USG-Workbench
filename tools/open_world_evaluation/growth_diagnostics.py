"""System-wide execution accounting and dependency-aware blocker attribution."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STAGE_GRAPH_PATH = ROOT / "tools" / "open_world_evaluation" / "stage_dependency_graph.json"
BLOCKING_MARKERS = (
    "UNRESOLVED", "INCOMPLETE", "UNSUPPORTED", "INVALID",
    "ERROR", "FAILED", "AMBIGUOUS", "MISSING", "PARTIAL",
)
STAGE_ALIASES = {
    "tokenisation": "tokenization", "lexical_analysis": "lexical",
    "lexicon": "lexical", "morphological": "morphology",
    "semantic": "semantic_composition", "semanticcomposition": "semantic_composition",
    "operator": "operators", "reference": "discourse", "coreference": "discourse",
}


def _stage_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return STAGE_ALIASES.get(normalized, normalized)


def load_stage_dependency_graph(path: Path = STAGE_GRAPH_PATH) -> dict[str, Any]:
    """Load and validate the acyclic stage-dependency profiles."""
    graph = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(graph, dict) or not isinstance(graph.get("profiles"), dict):
        raise ValueError("stage dependency graph must contain a profiles object")
    for target_id, profile in graph["profiles"].items():
        stages = profile.get("stages")
        if not isinstance(stages, dict) or not stages:
            raise ValueError(f"{target_id} must declare non-empty stages")
        for stage, spec in stages.items():
            dependencies = spec.get("depends_on")
            if not isinstance(dependencies, list) or any(dep not in stages for dep in dependencies):
                raise ValueError(f"{target_id}.{stage} has an unknown dependency")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(stage: str) -> None:
            if stage in visiting:
                raise ValueError(f"{target_id} stage graph contains a cycle at {stage}")
            if stage in visited:
                return
            visiting.add(stage)
            for dependency in stages[stage]["depends_on"]:
                visit(dependency)
            visiting.remove(stage)
            visited.add(stage)

        for stage in stages:
            visit(stage)
    return graph


def _ancestor_map(stages: dict[str, Any]) -> dict[str, set[str]]:
    ancestors: dict[str, set[str]] = {}

    def resolve(stage: str) -> set[str]:
        if stage in ancestors:
            return ancestors[stage]
        found: set[str] = set()
        for dependency in stages[stage]["depends_on"]:
            found.add(dependency)
            found.update(resolve(dependency))
        ancestors[stage] = found
        return found

    for stage in stages:
        resolve(stage)
    return ancestors


def _case_population(case: dict[str, Any]) -> str:
    return str(case.get("population", "unknown"))


def _target_id(case: dict[str, Any]) -> str:
    return str(case.get("target", {}).get("component_id", "unknown"))


def _language(case: dict[str, Any]) -> str:
    return str(case.get("input", {}).get("language_hint", "unspecified"))


def build_execution_accounting(cases: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    """Return reconcilable scenario, result-record, and actual-attempt counts."""
    case_by_id = {case.get("case_id"): case for case in cases}
    records_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    targets: dict[str, dict[str, Any]] = {}

    for result in results:
        case_id = str(result.get("case_id", ""))
        records_by_case[case_id].append(result)
        case = case_by_id.get(case_id)
        target = str(result.get("target", {}).get("component_id") or (
            _target_id(case) if case else "unknown"
        ))
        row = targets.setdefault(target, {
            "result_record_count": 0, "actual_attempt_count": 0,
            "not_executed_record_count": 0, "scenario_ids": set(),
            "actual_attempt_scenario_ids": set(), "only_not_executed_scenario_ids": set(),
        })
        row["result_record_count"] += 1
        row["scenario_ids"].add(case_id)
        if result.get("outcome") == "not_executed":
            row["not_executed_record_count"] += 1
        else:
            row["actual_attempt_count"] += 1
            row["actual_attempt_scenario_ids"].add(case_id)

    scenario_with_result = scenario_with_actual = scenario_only_not_executed = 0
    scenarios_without_result = multiple_result_scenarios = 0
    for case in cases:
        case_id = str(case.get("case_id", ""))
        rows = records_by_case.get(case_id, [])
        if not rows:
            scenarios_without_result += 1
            continue
        scenario_with_result += 1
        if len(rows) > 1:
            multiple_result_scenarios += 1
        if any(row.get("outcome") != "not_executed" for row in rows):
            scenario_with_actual += 1
        else:
            scenario_only_not_executed += 1
            target = targets.get(_target_id(case))
            if target is not None:
                target["only_not_executed_scenario_ids"].add(case_id)

    target_rows = []
    for target in sorted(targets):
        row = targets[target]
        target_rows.append({
            "target_id": target,
            "scenario_count_with_result": len(row["scenario_ids"]),
            "scenario_count_with_actual_attempt": len(row["actual_attempt_scenario_ids"]),
            "scenario_count_only_not_executed": len(row["only_not_executed_scenario_ids"]),
            "result_record_count": row["result_record_count"],
            "actual_attempt_count": row["actual_attempt_count"],
            "not_executed_record_count": row["not_executed_record_count"],
        })

    result_record_count = len(results)
    not_executed_count = sum(row.get("outcome") == "not_executed" for row in results)
    return {
        "accounting_version": "1.0.0",
        "legacy_attempted_field_definition": "execution_result_record_count_including_not_executed",
        "scenario_count": len(cases),
        "result_record_count": result_record_count,
        "actual_attempt_count": result_record_count - not_executed_count,
        "not_executed_record_count": not_executed_count,
        "scenario_count_with_result_record": scenario_with_result,
        "scenario_count_with_actual_attempt": scenario_with_actual,
        "scenario_count_only_not_executed": scenario_only_not_executed,
        "scenario_count_without_result_record": scenarios_without_result,
        "scenario_count_with_multiple_result_records": multiple_result_scenarios,
        "target_accounting": target_rows,
    }


def _target_result(record: dict[str, Any]) -> dict[str, Any] | None:
    payload = record.get("capture", {}).get("inline_output")
    if not isinstance(payload, dict):
        return None
    value = payload.get("target_result")
    if isinstance(value, dict):
        return value
    if isinstance(payload.get("stages"), (dict, list)) or isinstance(payload.get("diagnostics"), list):
        return payload
    return None


def _is_blocking(diagnostic: dict[str, Any]) -> bool:
    if isinstance(diagnostic.get("blocking"), bool):
        return diagnostic["blocking"]
    severity = str(diagnostic.get("severity", "")).lower()
    if severity in {"info", "informational", "warning", "warn"}:
        return False
    if severity in {"error", "fatal", "blocking"}:
        return True
    code = str(diagnostic.get("code", "")).upper()
    status = str(diagnostic.get("status", "")).upper()
    return any(marker in code or marker in status for marker in BLOCKING_MARKERS)


def _collect_stage_diagnostics(target_result: dict[str, Any]) -> dict[str, set[str]]:
    by_stage: dict[str, set[str]] = defaultdict(set)
    diagnostics = target_result.get("diagnostics", [])
    if isinstance(diagnostics, list):
        for diagnostic in diagnostics:
            if not isinstance(diagnostic, dict) or not _is_blocking(diagnostic):
                continue
            stage = _stage_name(diagnostic.get("stage"))
            if stage:
                by_stage[stage].add(str(diagnostic.get("code") or diagnostic.get("status") or "UNSPECIFIED"))

    stages = target_result.get("stages", {})
    if isinstance(stages, dict):
        iterable = stages.items()
    elif isinstance(stages, list):
        iterable = ((item.get("stage"), item) for item in stages if isinstance(item, dict))
    else:
        iterable = ()
    for raw_stage, stage_data in iterable:
        stage = _stage_name(raw_stage)
        if not stage or not isinstance(stage_data, dict):
            continue
        nested = stage_data.get("diagnostics", [])
        if isinstance(nested, list):
            for diagnostic in nested:
                if isinstance(diagnostic, dict) and _is_blocking(diagnostic):
                    by_stage[stage].add(str(diagnostic.get("code") or diagnostic.get("status") or "UNSPECIFIED"))
        status = str(stage_data.get("status") or stage_data.get("completion_status") or "").upper()
        if any(marker in status for marker in BLOCKING_MARKERS):
            by_stage[stage].add("STAGE_STATUS_" + status)
    return by_stage


def build_stage_attribution(
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    *,
    max_examples: int = 8,
    graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attribute blockers using target-specific DAG ancestry, not a global sequence.

    A stage is a first blocker when none of its declared ancestors is also
    blocked. Multiple parallel first blockers are retained. Later blockers
    are dependency-related co-occurrences, not proof of causal responsibility.
    """
    graph = graph or load_stage_dependency_graph()
    case_by_id = {case.get("case_id"): case for case in cases}
    first_counts: Counter[str] = Counter()
    downstream_counts: Counter[str] = Counter()
    group_counts: dict[tuple[str, str, str, str], Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)
    analyzed = without_payload = without_blocker = not_executed = 0
    unmapped: Counter[str] = Counter()
    unconfigured_targets: Counter[str] = Counter()
    multiple_first_blocker_records = 0
    records_with_blockers = 0

    for record in results:
        if record.get("outcome") == "not_executed":
            not_executed += 1
            continue
        analyzed += 1
        case = case_by_id.get(record.get("case_id"), {})
        target_id = str(record.get("target", {}).get("component_id") or _target_id(case))
        target_result = _target_result(record)
        if target_result is None:
            without_payload += 1
            without_blocker += 1
            continue
        blockers = _collect_stage_diagnostics(target_result)
        if not blockers:
            without_blocker += 1
            continue
        records_with_blockers += 1
        profile = graph["profiles"].get(target_id)
        if profile is None:
            unconfigured_targets[target_id] += 1
            for stage in blockers:
                unmapped[stage] += 1
            continue

        stages = profile["stages"]
        ancestors = _ancestor_map(stages)
        known = set(blockers).intersection(stages)
        for stage in sorted(set(blockers) - set(stages)):
            unmapped[stage] += 1
        if not known:
            continue

        first = sorted(
            stage for stage in known
            if not (ancestors[stage] & known)
        )
        later = sorted(known - set(first))
        if len(first) > 1:
            multiple_first_blocker_records += 1
        key = (target_id, _case_population(case), _language(case), profile["pipeline_version"])
        case_id = str(record.get("case_id", ""))
        for stage in first:
            first_counts[stage] += 1
            group_counts[key][stage] += 1
            if len(examples[stage]) < max_examples and case_id not in examples[stage]:
                examples[stage].append(case_id)
        for stage in later:
            downstream_counts[stage] += 1

    groups = [{
        "target_id": target,
        "population": population,
        "language": language,
        "pipeline_version": pipeline_version,
        "first_blocking_stage_counts": dict(sorted(counts.items())),
    } for (target, population, language, pipeline_version), counts in sorted(group_counts.items())]
    return {
        "attribution_version": "2.0.0",
        "stage_dependency_graph_version": graph.get("graph_version", "unknown"),
        "attribution_basis": "target_specific_dependency_dag_ancestry",
        "causality_warning": (
            "A first blocker is an observed diagnostic with no other blocked declared ancestor. "
            "Parallel first blockers are retained. Dependency-related later blockers are co-occurrences, "
            "not proof that an upstream failure caused them."
        ),
        "analyzed_actual_attempt_count": analyzed,
        "not_executed_record_count_excluded": not_executed,
        "records_without_target_result_payload": without_payload,
        "records_without_observed_blocking_diagnostic": without_blocker,
        "records_with_blocking_diagnostics": records_with_blockers,
        "records_with_multiple_parallel_first_blockers": multiple_first_blocker_records,
        "unconfigured_target_record_counts": dict(sorted(unconfigured_targets.items())),
        "unmapped_blocking_stage_counts": dict(sorted(unmapped.items())),
        "first_blocking_stage_counts": dict(sorted(first_counts.items())),
        "dependency_related_later_stage_counts": dict(sorted(downstream_counts.items())),
        "example_case_ids_by_first_blocking_stage": dict(sorted(examples.items())),
        "breakdown_by_target_population_language": groups,
        "profiles": {
            target: {
                "pipeline_contract": profile["pipeline_contract"],
                "pipeline_version": profile["pipeline_version"],
                "stages": profile["stages"],
            }
            for target, profile in sorted(graph["profiles"].items())
        },
    }
