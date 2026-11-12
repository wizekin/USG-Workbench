"""Deterministic discovery deduplication, impact classification, and Phase 8 prioritization."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def discovery_key(finding: dict[str, Any]) -> str:
    """Stable identity excludes prose and volatile counts, but includes evidence and scope."""
    identity = {
        "kind": str(finding.get("kind", "unknown")),
        "evidence_refs": sorted(set(str(x) for x in finding.get("evidence_refs", []))),
        "phase_impacts": sorted(set(str(x) for x in finding.get("phase_impacts", []))),
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _prior_discoveries(root: Path, limit: int = 100) -> dict[str, list[dict[str, Any]]]:
    base = root / "evaluations/system-wide/evidence-catalogue"
    if not base.is_dir():
        return {}
    snapshots = sorted((p for p in base.glob("*/catalogue.json") if p.is_file()),
                       key=lambda p: p.parent.name, reverse=True)[:limit]
    indexed: dict[str, list[dict[str, Any]]] = {}
    for path in snapshots:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(report, dict):
            continue
        for item in report.get("discoveries", []):
            if not isinstance(item, dict):
                continue
            key = item.get("discovery_key") or discovery_key(item)
            indexed.setdefault(str(key), []).append({
                "discovery_id": item.get("id"),
                "snapshot_id": path.parent.name,
                "observed_at": report.get("generated_at"),
            })
    return indexed


def deduplicate_discoveries(findings: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Collapse repeated findings within a snapshot and link prior append-only observations."""
    history = _prior_discoveries(root)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        grouped.setdefault(discovery_key(finding), []).append(finding)
    result = []
    for key, items in sorted(grouped.items()):
        primary = dict(items[0])
        prior = history.get(key, [])
        primary["discovery_key"] = key
        primary["duplicate_observation_count"] = len(items) - 1
        primary["previously_observed"] = bool(prior)
        primary["prior_observation_count"] = len(prior)
        primary["prior_observations"] = prior[:10]
        primary["deduplication_status"] = (
            "recurring" if prior else ("duplicate_in_snapshot" if len(items) > 1 else "new"))
        result.append(primary)
    return result


def classify_impacts(finding: dict[str, Any], phases: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe phase impact without changing a phase's recorded status."""
    by_id = {str(item.get("id")): item for item in phases}
    impacts = []
    for phase_id in sorted(set(finding.get("phase_impacts", []))):
        phase = by_id.get(str(phase_id), {})
        status = str(phase.get("status", "unknown"))
        if status == "bounded_exit_accepted_continuation_open":
            disposition = "accepted_baseline_with_open_continuation"
        elif status.startswith("accepted"):
            disposition = "accepted_scope_amendment_review"
        elif status in {"in_progress", "definition_in_progress"}:
            disposition = "active_phase_dependency_review"
        else:
            disposition = "phase_status_unclassified"
        impacts.append({"phase_id": phase_id, "phase_status": status, "disposition": disposition})
    details = finding.get("details") if isinstance(finding.get("details"), dict) else {}
    migration_required = bool(details.get("normative_contract_change") or details.get("canonical_invariant_change"))
    return {
        "impacts": impacts,
        "cross_cutting": len(impacts) > 1,
        "migration_review_required": migration_required,
        "phase_status_mutation_allowed": False,
    }


_BACKLOG_RULES = (
    (("growth_planner_recommendation",), ("SYS-15",)),
    (("latest_open_world_campaign_has_no_naturalistic_population", "open_world_campaign_evidence_missing"),
     ("SYS-03", "SYS-01", "SYS-02")),
    (("latest_github_workflow_run_failed", "github_actions_status_collection_incomplete",
      "github_actions_artifact_index_incomplete"), ("SYS-16",)),
    (("external_lexical",), ("SYS-05", "SYS-06", "SYS-17")),
    (("semantic", "construction", "syntax", "operator", "discourse"), ("SYS-08", "SYS-09", "SYS-17")),
)


def related_backlog_items(findings: list[dict[str, Any]], root: Path) -> dict[str, list[str]]:
    """Link observations to existing backlog IDs only; never create or close backlog work."""
    backlog = root / "documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md"
    if not backlog.is_file():
        return {str(item.get("id")): [] for item in findings}
    text = backlog.read_text(encoding="utf-8")
    known = set(re.findall(r"\bSYS-\d{2}\b", text))
    links = {}
    for item in findings:
        kind = str(item.get("kind", "")).lower()
        proposed: set[str] = set()
        for markers, ids in _BACKLOG_RULES:
            if any(marker in kind for marker in markers):
                proposed.update(ids)
        links[str(item.get("id"))] = sorted(proposed & known)
    return links


def integrated_priorities(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create an explainable cross-source queue while preserving each source's own metrics."""
    severity_order = {"high": 0, "medium": 1, "low": 2, "informational": 3}
    output = []
    for item in findings:
        details = item.get("details") if isinstance(item.get("details"), dict) else {}
        reasons = [f"severity:{item.get('severity', 'unknown')}"]
        if item.get("previously_observed"):
            reasons.append(f"recurs_in_{item.get('prior_observation_count', 0)}_prior_snapshot(s)")
        if item.get("duplicate_observation_count"):
            reasons.append(f"duplicate_{item['duplicate_observation_count']}_times_in_snapshot")
        if details.get("campaign_recurrence_count") is not None:
            reasons.append(f"campaign_recurrence:{details['campaign_recurrence_count']}")
        if details.get("priority_score") is not None:
            reasons.append("growth_planner_score_retained_as_source_metric")
        output.append({
            "discovery_id": item.get("id"),
            "discovery_key": item.get("discovery_key"),
            "kind": item.get("kind"),
            "severity": item.get("severity"),
            "priority_band": item.get("severity", "unknown"),
            "priority_reasons": reasons,
            "phase_impacts": item.get("phase_impacts", []),
            "route": item.get("route"),
            "source_metrics": {
                key: details[key] for key in (
                    "priority_score", "observed_first_blocker_records",
                    "campaign_recurrence_count", "acceptance_gate",
                    "pud_evaluation_status", "inventory_status"
                ) if key in details
            },
            "review_required": True,
            "runtime_change_allowed": False,
        })
    output.sort(key=lambda item: (severity_order.get(item["severity"], 4),
                                 not bool(item["priority_reasons"]), item["discovery_id"] or ""))
    for rank, item in enumerate(output, 1):
        item["rank"] = rank
    return output


def build_review_proposals(findings: list[dict[str, Any]], phases: list[dict[str, Any]],
                           limit: int = 100) -> list[dict[str, Any]]:
    """Turn observations into stable, review-only proposal records; never implement them."""
    phase_by_id = {str(item.get("id")): item for item in phases}
    proposals = []
    for finding in findings:
        route = str(finding.get("route", "evidence_quality_review"))
        impact = finding.get("impact_classification") or {}
        if impact.get("migration_review_required"):
            proposal_type = "versioned_contract_migration_review"
            next_action = "Prepare a versioned migration, compatibility adapter, and affected regression plan for explicit review."
        elif route == "existing_phase_continuation":
            proposal_type = "existing_continuation_update"
            next_action = "Update the owning continuation with this evidence; preserve its existing acceptance boundary."
        elif route == "existing_phase_amendment_proposal":
            proposal_type = "accepted_phase_amendment"
            next_action = "Draft a scope-specific amendment proposal; retain the prior acceptance record unchanged."
        elif route == "cross_cutting_workstream_review":
            proposal_type = "cross_cutting_workstream"
            next_action = "Compare affected phases and dependencies before defining a shared workstream."
        elif route == "new_phase_candidate":
            proposal_type = "future_phase_candidate"
            next_action = "Check all existing continuations and amendments before proposing a new phase."
        elif route == "evidence_quality_review":
            proposal_type = "evidence_quality_remediation"
            next_action = "Resolve or explicitly document the evidence-quality gap, then refresh the affected snapshot."
        else:
            proposal_type = "evidence_collection_or_registry_maintenance"
            next_action = "Repair collection or registry coverage and rerun the evidence collector."
        key = str(finding.get("discovery_key") or discovery_key(finding))
        proposal_id = "P8-PROP-" + hashlib.sha256((proposal_type + ":" + key).encode("utf-8")).hexdigest()[:16]
        impacted = []
        for phase_id in sorted(set(str(x) for x in finding.get("phase_impacts", []))):
            phase = phase_by_id.get(phase_id, {})
            impacted.append({
                "phase_id": phase_id,
                "phase_name": phase.get("name"),
                "recorded_status": phase.get("status", "unknown"),
                "open_work": phase.get("open_work"),
            })
        proposals.append({
            "proposal_id": proposal_id,
            "source_discovery_id": finding.get("id"),
            "source_discovery_key": key,
            "proposal_type": proposal_type,
            "route": route,
            "title": str(finding.get("summary") or finding.get("kind") or "Evidence-backed follow-up"),
            "priority_band": finding.get("severity", "unknown"),
            "impacted_phases": impacted,
            "evidence_refs": list(finding.get("evidence_refs", [])),
            "related_backlog_items": list(finding.get("related_backlog_items", [])),
            "proposed_next_action": next_action,
            "acceptance_requirements": [
                "Declare positive, negative, ambiguous, and boundary regressions where behavior changes.",
                "Preserve source rights, population, version, and candidate/runtime boundaries.",
                "Run relevant regression and independent evaluation gates.",
                "Record exact commit, resource digests, and evidence population."
            ],
            "review_status": "draft_requires_review",
            "implementation_status": "not_implemented",
            "phase_status_mutation_allowed": False,
            "canonical_contract_mutation_allowed": False,
            "runtime_promotion_allowed": False,
        })
    proposals.sort(key=lambda item: (
        {"high": 0, "medium": 1, "low": 2, "informational": 3}.get(item["priority_band"], 4),
        item["proposal_id"]))
    return proposals[:max(0, limit)]
