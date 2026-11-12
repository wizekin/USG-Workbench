"""Repository-wide evidence/resource catalogue. Read-only; no runtime promotion."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker
from .discovery import (build_review_proposals, classify_impacts, deduplicate_discoveries, integrated_priorities, related_backlog_items)
from .freshness import evidence_quality_diagnostics

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config/usg-system-evidence-source-registry-0.1.0.json"
REGISTRY_SCHEMA = ROOT / "specifications/usg-system-evidence-source-registry-0.1.0.schema.json"
REPORT_SCHEMA = ROOT / "specifications/usg-system-evidence-catalogue-0.1.0.schema.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value

def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def matches(root: Path, patterns: list[str]) -> list[Path]:
    found: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and not any(x in {".git", "node_modules", ".venv", "__pycache__"} for x in path.parts):
                found.add(path)
    return sorted(found, key=lambda p: p.relative_to(root).as_posix())

def validate_registry(registry: dict[str, Any]) -> None:
    schema = json.loads(REGISTRY_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(registry),
                    key=lambda e: list(e.absolute_path))
    if errors:
        raise ValueError("source registry validation failed: " + "; ".join(e.message for e in errors[:8]))
    family_ids = [x["id"] for x in registry["source_families"]]
    phase_ids = [x["id"] for x in registry["phases"]]
    if len(family_ids) != len(set(family_ids)) or len(phase_ids) != len(set(phase_ids)):
        raise ValueError("source family and phase IDs must be unique")
    known = set(phase_ids)
    for family in registry["source_families"]:
        if set(family["consumers"]) - known:
            raise ValueError(f"{family['id']} references an unknown phase")

def inventory_sources(root: Path, registry: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for family in registry["source_families"]:
        files = []
        for path in matches(root, family["patterns"]):
            files.append({"path": path.relative_to(root).as_posix(),
                          "sha256": digest(path), "size_bytes": path.stat().st_size})
        result.append({
            "id": family["id"], "title": family["title"], "category": family["category"],
            "description": family["description"], "use_mode": family["use_mode"],
            "evidence_class": family["evidence_class"], "consumers": family["consumers"],
            "refresh": family["refresh"], "guardrails": family["guardrails"],
            "matched_file_count": len(files), "status": "available" if files else "missing",
            "files": files,
        })
    return result

def read_campaigns(root: Path, limit: int) -> list[dict[str, Any]]:
    base = root / "evaluations/open-world/campaigns"
    if not base.is_dir():
        return []
    items = []
    for report_path in base.glob("*/campaign-report.json"):
        report = read_json(report_path)
        if report is None:
            continue
        items.append((str(report.get("created_at") or ""), report_path.parent, report))
    items.sort(key=lambda x: (x[0], x[1].name), reverse=True)
    output = []
    for created, directory, report in items[:limit]:
        coverage = report.get("coverage") if isinstance(report.get("coverage"), dict) else {}
        populations = coverage.get("population_case_counts", {})
        attribution = coverage.get("stage_attribution", {})
        accounting = coverage.get("execution_accounting")
        bundle_manifest = read_json(directory / "bundle-manifest.json")
        output.append({
            "campaign_id": report.get("campaign_id", directory.name),
            "created_at": created or None, "status": report.get("status", "not_reported"),
            "tested_commit_sha": report.get("tested_commit_sha"),
            "scenario_count": coverage.get("case_count", report.get("case_count")),
            "population_case_counts": populations,
            "target_case_counts": coverage.get("target_case_counts", {}),
            "outcome_counts": report.get("outcome_counts", {}),
            "execution_accounting": accounting if isinstance(accounting, dict) else {
                "status": "not_recorded_in_report_version"},
            "campaign_report_sha256": digest(report_path),
            "bundle_manifest": bundle_manifest,
            "artifact_hashes": (
                {item["name"]: item["sha256"] for item in bundle_manifest.get("files", [])
                 if isinstance(item, dict) and item.get("name") and item.get("sha256")}
                if bundle_manifest and isinstance(bundle_manifest.get("files"), list) else {}
            ),
            "first_blocking_stage_counts": attribution.get("first_blocking_stage_counts", {})
                if isinstance(attribution, dict) else {},
            "naturalistic_case_count": int(populations.get("naturalistic", 0) or 0),
            "report_path": (directory / "campaign-report.json").relative_to(root).as_posix(),
        })
    return output

def external_lexical(manifest_path: Path | None, checkpoint_path: Path | None,
                     pud_path: Path | None, pud_error_path: Path | None,
                     shard_inventory_path: Path | None, branch_commit: str | None) -> dict[str, Any]:
    manifest, checkpoint = read_json(manifest_path), read_json(checkpoint_path)
    pud, pud_error = read_json(pud_path), read_json(pud_error_path)
    shard_inventory = read_json(shard_inventory_path)
    if manifest is None:
        return {"status": "unavailable", "manifest_available": False,
                "checkpoint_available": checkpoint is not None, "external_branch_commit": branch_commit,
                "pud_evaluation": {"status": "not_run_without_manifest",
                                   "error": pud_error.get("error") if pud_error else None},
            "shard_inventory": shard_inventory if shard_inventory is not None else {
                "status": "not_collected", "file_count": 0, "total_size_bytes": 0, "files": []}}
    processed, expected = int(manifest.get("processed_headwords", 0) or 0), int(manifest.get("expected_headwords", 0) or 0)
    batches = int(manifest.get("batch_count", 0) or 0)
    percent = 100 * processed / expected if expected else None
    shards = int(pud.get("lexical_shard_count", -1)) if pud else -1
    totals = pud.get("totals", {}) if pud else {}
    morphology = pud.get("morphology_evaluation", {}).get("totals", {}) if pud else {}
    last = manifest.get("last_batch", {})
    budget = int(manifest.get("storage_budget_bytes", 0) or 0)
    shard_count = int(shard_inventory.get("file_count", 0) or 0) if shard_inventory else None
    shard_inventory_match = bool(shard_inventory is not None and shard_count == batches)
    pud_fresh = bool(pud is not None and shards == batches and shard_inventory_match)
    return {
        "status": manifest.get("status", "unknown"), "manifest_available": True,
        "checkpoint_available": checkpoint is not None, "external_branch_commit": branch_commit,
        "source": {"repository": manifest.get("source_repository"), "commit": manifest.get("source_commit"),
                   "snapshot_id": manifest.get("source_snapshot_id")},
        "progress": {
            "processed_headwords": processed, "expected_headwords": expected,
            "headword_completion_percent": round(percent, 4) if percent is not None else None,
            "processed_entries": manifest.get("processed_entries"), "processed_senses": manifest.get("processed_senses"),
            "batch_count": batches, "stored_bytes": manifest.get("stored_bytes"),
            "storage_budget_bytes": budget,
            "storage_budget_percent": round(100 * int(manifest.get("stored_bytes", 0) or 0) / budget, 4) if budget else None,
            "failed_headwords": manifest.get("failed_headwords"), "pending_retries": manifest.get("pending_retries"),
            "retried_headwords": manifest.get("retried_headwords"), "recovered_headwords": manifest.get("recovered_headwords"),
            "retry_failed_headwords": manifest.get("retry_failed_headwords"),
            "retry_dead_letter_headwords": manifest.get("retry_dead_letter_headwords"),
            "updated_at": manifest.get("updated_at"),
            "checkpoint_cursor": {"page_index": checkpoint.get("page_index") if checkpoint else None,
                                  "entry_index": checkpoint.get("entry_index") if checkpoint else None,
                                  "cycle_number": checkpoint.get("cycle_number") if checkpoint else None},
            "last_batch": {"headwords": last.get("headwords"), "entries": last.get("entries"),
                           "senses": last.get("senses"), "stop_reason": last.get("stop_reason")},
        },
        "shard_inventory": {
            "status": ("matches_manifest" if shard_inventory_match else
                       ("count_mismatch" if shard_inventory is not None else "not_collected")),
            "file_count": shard_count,
            "manifest_batch_count": batches,
            "total_size_bytes": shard_inventory.get("total_size_bytes") if shard_inventory else None,
            "files": shard_inventory.get("files", []) if shard_inventory else [],
            "inventory_sha256": digest(shard_inventory_path) if shard_inventory_path and shard_inventory_path.is_file() else None,
        },
        "pud_evaluation": {
            "generated_at": (pud.get("generated_at") or pud.get("evaluated_at") or pud.get("created_at")) if pud else None,
            "status": "fresh_for_current_shard_count" if pud_fresh else (
                "stale_shard_count_mismatch" if pud else "not_available"),
            "evaluated_shard_count": shards if pud else None, "current_manifest_batch_count": batches,
            "pud_repository": pud.get("pud_repository") if pud else None,
            "pud_commit": pud.get("pud_commit") if pud else None, "pud_sentences": pud.get("pud_sentences") if pud else None,
            "lexicon_form_count": pud.get("lexicon_form_count") if pud else None,
            "lexicon_lemma_count": pud.get("lexicon_lemma_count") if pud else None,
            "mapped_dictionary_entry_count": pud.get("mapped_dictionary_entry_count") if pud else None,
            "exact_surface_token_coverage": totals.get("token_coverage"), "oov_rate": totals.get("oov_rate"),
            "gold_upos_candidate_recall": totals.get("gold_tag_candidate_recall_all_tokens"),
            "gold_lemma_coverage": totals.get("gold_lemma_coverage"),
            "gold_lemma_upos_candidate_recall": totals.get("gold_lemma_upos_candidate_recall"),
            "morphology_candidate_pool_precision": morphology.get("candidate_pool_precision"),
            "morphology_candidate_recall": morphology.get("candidate_recall"),
            "candidate_precision_measured": totals.get("candidate_precision_measured", False),
            "rights_and_runtime_boundary": {
                "candidate_only": pud.get("lexical_source_is_candidate_only", True) if pud else True,
                "runtime_promotion_allowed": pud.get("runtime_promotion_allowed", False) if pud else False,
                "source_text_persisted": pud.get("source_text_persisted", False) if pud else False},
            "error": pud_error.get("error") if pud_error else None,
        },
        "manifest_sha256": digest(manifest_path) if manifest_path and manifest_path.is_file() else None,
        "checkpoint_sha256": digest(checkpoint_path) if checkpoint_path and checkpoint_path.is_file() else None,
    }

def workflow_evidence(path: Path | None) -> dict[str, Any]:
    payload = read_json(path)
    if payload is None:
        return {"status": "not_collected", "workflow_count": 0, "latest_run_count": 0,
                "status_counts": {}, "workflows": [], "collection_errors": [],
                "artifact_collection_errors": [],
                "interpretation_boundary": "Live workflow status was not collected; workflow configuration is not evidence of execution or success."}
    if payload.get("contract") != "USG-GITHUB-ACTIONS-EVIDENCE/0.1.0":
        return {"status": "collection_error", "workflow_count": 0, "latest_run_count": 0,
                "status_counts": {}, "workflows": [], "collection_errors": [
                    {"error": "unsupported or missing USG-GITHUB-ACTIONS-EVIDENCE contract"}],
                "artifact_collection_errors": [],
                "interpretation_boundary": "Malformed workflow evidence is not counted as a pass."}
    return {"status": "collected", "workflow_count": int(payload.get("workflow_count", 0) or 0),
            "latest_run_count": int(payload.get("latest_run_count", 0) or 0),
            "status_counts": payload.get("status_counts", {}),
            "workflows": payload.get("workflows", []),
            "collection_errors": payload.get("collection_errors", []),
            "artifact_collection_errors": payload.get("artifact_collection_errors", []),
            "interpretation_boundary": payload.get("interpretation_boundary", "Workflow status is operational evidence, not semantic correctness.")}

def route_for_phases(phase_impacts: list[str], phases: list[dict[str, Any]]) -> str:
    by_id = {item["id"]: item for item in phases}
    if "P6" in phase_impacts and by_id.get("P6", {}).get("status") == "bounded_exit_accepted_continuation_open":
        return "existing_phase_continuation"
    if any(by_id.get(pid, {}).get("status", "").startswith("accepted") for pid in phase_impacts):
        return "existing_phase_amendment_proposal"
    return "cross_cutting_workstream_review" if len(phase_impacts) > 1 else "new_phase_candidate"

def make_finding(kind: str, summary: str, refs: list[str], impacts: list[str],
                 phases: list[dict[str, Any]], severity: str = "medium",
                 route: str | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    token = hashlib.sha256((kind + "\0" + "\0".join(refs) + "\0" + summary).encode()).hexdigest()[:16]
    return {"id": "SYS-EVID-" + token, "kind": kind, "severity": severity, "summary": summary,
            "evidence_refs": refs, "phase_impacts": impacts,
            "route": route or route_for_phases(impacts, phases),
            "review_status": "observed_requires_review", "runtime_change_allowed": False,
            "details": details or {}}

def discover(phases: list[dict[str, Any]], external: dict[str, Any],
             campaigns: list[dict[str, Any]], growth: dict[str, Any] | None,
             sources: list[dict[str, Any]], workflows: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    if external.get("manifest_available"):
        progress = external.get("progress", {})
        pct = progress.get("headword_completion_percent")
        if pct is not None and pct < 100:
            findings.append(make_finding(
                "external_lexical_acquisition_incomplete",
                f"The pinned external lexical source snapshot is {pct:.2f}% processed; retrieved records remain candidate evidence.",
                ["external_lexical.manifest_sha256", "external_lexical.progress"],
                ["P5", "P6", "P7", "P8"], phases, "informational", "existing_external_lexical_workstream",
                {"processed_headwords": progress.get("processed_headwords"),
                 "expected_headwords": progress.get("expected_headwords"),
                 "processed_senses": progress.get("processed_senses"),
                 "batch_count": progress.get("batch_count")}))
        pud_status = external.get("pud_evaluation", {}).get("status")
        if pud_status != "fresh_for_current_shard_count":
            findings.append(make_finding(
                "external_lexical_evaluation_not_current",
                "The English PUD lexical/morphology evaluation is missing or does not cover all current shards; refresh it before using coverage metrics to steer lexical development.",
                ["external_lexical.manifest_sha256", "external_lexical.pud_evaluation"],
                ["P5", "P6", "P7", "P8"], phases, "high", "existing_evaluation_refresh",
                {"pud_evaluation_status": pud_status}))
    else:
        findings.append(make_finding(
            "external_lexical_manifest_unavailable",
            "The external lexical branch manifest was not collected. Its absence is not an empty inventory or zero progress.",
            ["external_lexical.manifest"], ["P8"], phases, "high", "evidence_collection"))
    if external.get("manifest_available") and external.get("shard_inventory", {}).get("status") != "matches_manifest":
        inventory_status = external.get("shard_inventory", {}).get("status")
        findings.append(make_finding(
            "external_lexical_shard_inventory_mismatch" if inventory_status == "count_mismatch" else "external_lexical_shard_inventory_unavailable",
            "The physical external lexical shard inventory is missing or does not reconcile with the cumulative crawl manifest; investigate before treating crawl totals or PUD metrics as current.",
            ["external_lexical.manifest_sha256", "external_lexical.shard_inventory"],
            ["P5", "P6", "P7", "P8"], phases, "high", "existing_external_lexical_workstream",
            {"manifest_batch_count": external.get("progress", {}).get("batch_count"),
             "physical_shard_count": external.get("shard_inventory", {}).get("file_count"),
             "inventory_status": inventory_status}))
    failed_conclusions = {"failure", "timed_out", "action_required", "startup_failure"}
    if workflows.get("status") == "collected":
        phase_impact_rules = [
            ("phase1", ["P1"]), ("phase2", ["P2"]), ("phase3", ["P3"]),
            ("phase4", ["P4"]), ("phase5", ["P5"]), ("phase6", ["P6"]),
            ("phase7", ["P7"]), ("phase8", ["P8"]),
        ]
        for workflow in workflows.get("workflows", []):
            latest_run = workflow.get("latest_run") or {}
            conclusion = latest_run.get("conclusion")
            path = str(workflow.get("path") or "").lower()
            if conclusion not in failed_conclusions:
                continue
            impacts = next((values for marker, values in phase_impact_rules if marker in path), None)
            if impacts is None and "external-lexical" in path:
                impacts = ["P5", "P6", "P7", "P8"]
            elif impacts is None and ("open-world" in path or "pud" in path):
                impacts = ["P4", "P5", "P6", "P8"]
            elif impacts is None and "growth" in path:
                impacts = ["P5", "P6", "P7", "P8"]
            elif impacts is None and "system-evidence" in path:
                impacts = ["P8"]
            if impacts is None:
                impacts = ["P8"]
            findings.append(make_finding(
                "latest_github_workflow_run_failed",
                f"The latest recorded run for workflow '{workflow.get('name')}' concluded {conclusion}.",
                [str(latest_run.get("html_url") or workflow.get("html_url") or workflow.get("path"))],
                impacts, phases, "high" if conclusion == "failure" else "medium",
                "existing_workflow_or_phase_continuation",
                {"workflow_path": workflow.get("path"), "workflow_id": workflow.get("workflow_id"),
                 "run_id": latest_run.get("run_id"), "run_sha": latest_run.get("head_sha"),
                 "event": latest_run.get("event"), "conclusion": conclusion}))
        if workflows.get("collection_errors"):
            findings.append(make_finding(
                "github_actions_status_collection_incomplete",
                f"Live GitHub Actions status collection could not resolve {len(workflows['collection_errors'])} workflow(s); unavailable statuses are not passes.",
                ["workflow_evidence.collection_errors"], ["P8"], phases, "medium", "evidence_collection",
                {"collection_error_count": len(workflows["collection_errors"])}))
        if workflows.get("artifact_collection_errors"):
            findings.append(make_finding(
                "github_actions_artifact_index_incomplete",
                f"Artifact metadata could not be collected for {len(workflows['artifact_collection_errors'])} latest workflow run(s); workflow status is still recorded separately.",
                ["workflow_evidence.artifact_collection_errors"], ["P8"], phases, "low", "evidence_collection",
                {"artifact_collection_error_count": len(workflows["artifact_collection_errors"])}))
    else:
        findings.append(make_finding(
            "github_actions_status_not_collected",
            "Live latest-run status for repository workflows is unavailable in this catalogue snapshot.",
            ["workflow_evidence"], ["P8"], phases, "medium", "evidence_collection",
            {"collection_status": workflows.get("status")}))
    if campaigns:
        latest = campaigns[0]
        if latest.get("naturalistic_case_count", 0) == 0:
            findings.append(make_finding(
                "latest_open_world_campaign_has_no_naturalistic_population",
                "The latest stored Open-World campaign contains no naturalistic cases; keep its randomized and diagnostic results separate from the PUD input-only pilot.",
                [latest["report_path"]], ["P4", "P5", "P6", "P8"], phases, "medium",
                "existing_naturalistic_evaluation_workstream",
                {"campaign_id": latest.get("campaign_id"),
                 "population_case_counts": latest.get("population_case_counts", {})}))
    else:
        findings.append(make_finding(
            "open_world_campaign_evidence_missing",
            "No immutable Open-World campaign reports were found in the current repository snapshot.",
            ["evaluations/open-world/campaigns"], ["P8"], phases, "high", "evidence_collection"))
    if not growth:
        findings.append(make_finding(
            "growth_plan_not_collected",
            "A fresh evidence-driven growth plan was not available in this catalogue snapshot; preserve the planner error/unavailable state and do not infer an empty priority queue.",
            ["growth_plan"], ["P5", "P6", "P7", "P8"], phases, "medium", "evidence_collection"))
    if growth:
        impact_map = {
            "lexical": ["P5", "P6", "P7", "P8"], "morphology": ["P5", "P6", "P8"],
            "syntax": ["P4", "P5", "P6", "P8"], "operators": ["P5", "P6", "P8"],
            "semantic_composition": ["P4", "P5", "P6", "P7", "P8"], "discourse": ["P5", "P6", "P8"]}
        for action in growth.get("ranked_actions", [])[:10]:
            stage = str(action.get("stage", "unknown"))
            findings.append(make_finding(
                "growth_planner_recommendation",
                str(action.get("proposed_action") or action.get("action") or f"Investigate repeated first blockers in {stage}."),
                ["growth_plan.ranked_actions", *action.get("example_case_ids", [])[:5]],
                impact_map.get(stage, ["P8"]), phases, "medium", details={
                    "stage": stage, "priority_score": action.get("priority_score"),
                    "acceptance_gate": action.get("acceptance_gate"),
                    "observed_first_blocker_records": action.get("observed_first_blocker_records"),
                    "campaign_recurrence_count": action.get("campaign_recurrence_count")}))
    missing = [item["id"] for item in sources if item["status"] == "missing"]
    if missing:
        findings.append(make_finding(
            "registered_evidence_sources_missing",
            "One or more curated source families did not resolve to files in this repository snapshot.",
            [f"source_family:{x}" for x in missing], ["P8"], phases, "low", "registry_maintenance",
            {"missing_source_family_ids": missing}))
    return findings

def collect_catalogue(root: Path = ROOT, *, registry_path: Path = REGISTRY_PATH,
                      external_manifest_path: Path | None = None,
                      external_checkpoint_path: Path | None = None,
                      pud_evaluation_path: Path | None = None, pud_error_path: Path | None = None,
                      external_shard_inventory_path: Path | None = None,
                      workflow_runs_path: Path | None = None,
                      growth_plan_path: Path | None = None, external_branch_commit: str | None = None,
                      repository_name: str = "wizekin/USG-Workbench", branch: str = "main",
                      commit_sha: str = "unknown", tree_sha: str | None = None,
                      max_campaigns: int = 20, generated_at: str | None = None) -> dict[str, Any]:
    root = Path(root)
    registry = read_json(Path(registry_path))
    if registry is None:
        raise ValueError("source registry is required")
    validate_registry(registry)
    if isinstance(max_campaigns, bool) or not 1 <= max_campaigns <= 100:
        raise ValueError("max_campaigns must be between 1 and 100")
    phases = registry["phases"]
    sources = inventory_sources(root, registry)
    campaigns = read_campaigns(root, max_campaigns)
    external = external_lexical(external_manifest_path, external_checkpoint_path,
                                pud_evaluation_path, pud_error_path,
                                external_shard_inventory_path, external_branch_commit)
    growth = read_json(growth_plan_path)
    workflows = workflow_evidence(workflow_runs_path)
    diagnostic_items = evidence_quality_diagnostics(
        external, campaigns, growth, generated_at or utc_now())
    diagnostic_findings = []
    for item in diagnostic_items:
        detail = {key: value for key, value in item.items()
                  if key not in {"kind", "severity", "summary", "evidence_refs"}}
        diagnostic_findings.append(make_finding(
            item["kind"], item["summary"], item["evidence_refs"], ["P8"], phases,
            item["severity"], "evidence_quality_review", detail))
    findings = deduplicate_discoveries(
        discover(phases, external, campaigns, growth, sources, workflows) + diagnostic_findings, root)
    backlog_links = related_backlog_items(findings, root)
    for finding in findings:
        finding["related_backlog_items"] = backlog_links.get(str(finding.get("id")), [])
        finding["impact_classification"] = classify_impacts(finding, phases)
    priorities = integrated_priorities(findings)
    review_proposals = build_review_proposals(findings, phases)
    latest = campaigns[0] if campaigns else None
    selected_naturalistic = sum(item.get("naturalistic_case_count", 0) for item in campaigns)
    report = {
        "contract": "USG-SYSTEM-EVIDENCE-CATALOGUE/0.1.0",
        "generated_at": generated_at or utc_now(),
        "repository": {"name": repository_name, "branch": branch, "commit_sha": commit_sha, "tree_sha": tree_sha},
        "phase_status": phases,
        "source_registry": {"contract": registry["contract"], "version": registry["version"],
                            "source_family_count": len(registry["source_families"]), "phase_count": len(phases)},
        "source_families": sources,
        "resource_consumption_map": {
            "contract": "USG-PHASE-RESOURCE-CONSUMPTION-MAP/0.1.0",
            "path": "config/usg-phase-resource-consumption-map-0.1.0.json",
            "note": "Declared resource-consumer relationships; not proof that all listed assets are already imported at runtime."},
        "asset_summary": {
            "source_family_count": len(sources),
            "available_source_family_count": sum(x["status"] == "available" for x in sources),
            "missing_source_family_count": sum(x["status"] == "missing" for x in sources),
            "indexed_file_count": sum(x["matched_file_count"] for x in sources),
            "unique_indexed_path_count": len({f["path"] for x in sources for f in x["files"]})},
        "open_world": {
            "campaign_count": len(campaigns), "campaigns": campaigns, "latest_campaign": latest,
            "population_summary": {"latest_campaign_population_case_counts":
                latest.get("population_case_counts", {}) if latest else {},
                "naturalistic_case_count_across_selected_campaigns": selected_naturalistic,
                "aggregation_note": "Sum across immutable report populations, not a unique corpus count."},
            "interpretation_boundary": "Execution, structural validity, and semantic correctness are separate; randomized, controlled-diagnostic, and naturalistic populations are not pooled."},
        "external_lexical": external,
        "workflow_evidence": workflows,
        "growth_plan": {
            "status": "available" if growth else "not_collected",
            "contract": growth.get("contract") if growth else None,
            "generated_at": growth.get("generated_at") if growth else None,
            "campaigns_analyzed": growth.get("campaigns_analyzed", 0) if growth else 0,
            "ranked_actions": growth.get("ranked_actions", []) if growth else [],
            "baseline": growth.get("baseline") if growth else None,
            "campaigns": growth.get("campaigns", []) if growth else [],
            "evidence_sources": growth.get("evidence_sources", []) if growth else [],
            "diagnostic_accounting_warnings": growth.get("diagnostic_accounting_warnings", []) if growth else [],
            "safety_policy": growth.get("safety_policy", {
                "runtime_mutations_performed": False, "candidate_lexical_data_promoted": False,
                "semantic_contracts_changed": False}) if growth else {
                "runtime_mutations_performed": False, "candidate_lexical_data_promoted": False,
                "semantic_contracts_changed": False}},
        "discoveries": findings,
        "evidence_quality_diagnostics": diagnostic_items,
        "integrated_priorities": priorities,
        "review_proposals": review_proposals,
        "discovery_management": {"deduplication": "stable_kind_evidence_scope_fingerprint",
                                "historical_snapshot_limit": 100,
                                "backlog_linking": "existing_ids_only",
                                "phase_impact_classification": "descriptive_only"},
        "governance": {
            "runtime_mutations_performed": False, "candidate_resources_promoted": False,
            "phase_statuses_changed": False, "canonical_contracts_changed": False,
            "amendments_require_review": True,
            "phase_router_policy": "Route into an existing continuation first; accepted phases receive explicit amendment proposals; uncovered cross-cutting gaps may become future phase candidates."},
        "limitations": [
            "Path inventory does not prove that each runtime imports each listed resource.",
            "Pattern-based discovery can miss new source types until the registry is updated.",
            "Latest stored campaign is not necessarily the latest live workflow run until its report is published to main.",
            "Missing report or metric is not interpreted as zero.",
            "Growth planner first blockers are diagnostic starting points, not proven causes.",
            "No global semantic accuracy, intelligence, or AGI score is produced.",
            "Candidate lexical and semantic resources are not promoted by this tool."]}
    schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report),
                    key=lambda e: list(e.absolute_path))
    if errors:
        raise ValueError("catalogue schema validation failed: " + "; ".join(e.message for e in errors[:10]))
    return report

def render_markdown(report: dict[str, Any]) -> str:
    phases, sources, ow = report["phase_status"], report["source_families"], report["open_world"]
    ext, progress, pud = report["external_lexical"], report["external_lexical"].get("progress", {}), report["external_lexical"].get("pud_evaluation", {})
    lines = [
        "# USG System-Wide Evidence and Resource Catalogue", "",
        f"Generated: {report['generated_at']}",
        f"Repository commit: {report['repository']['commit_sha']}", "",
        "## Purpose", "",
        "This catalogue consolidates phase records, contracts, runtime components, adapters, resources, benchmarks, Open-World campaigns, external lexical acquisition, and growth-planning recommendations. It is a development-planning input, not a semantic accuracy score.", "",
        "## Development phases", "",
        "| Phase | Status | Boundary / open work |", "|---|---|---|"]
    for phase in phases:
        lines.append(f"| {phase['id']} — {phase['name']} | {phase['status']} | {phase['open_work']} |")
    lines += ["", "## Source-family inventory", "", "| Source family | Files | Use mode | Consumers |",
              "|---|---:|---|---|"]
    for item in sources:
        lines.append(f"| {item['title']} | {item['matched_file_count']} | {item['use_mode']} | {', '.join(item['consumers'])} |")
    lines += ["", f"Unique indexed paths: {report['asset_summary']['unique_indexed_path_count']}.",
              "", "## Open-World evidence", "", f"Stored campaigns collected: {ow['campaign_count']}. "]
    if ow["latest_campaign"]:
        item = ow["latest_campaign"]
        lines += [f"- Latest stored campaign: {item['campaign_id']} ({item['created_at']}); status: {item['status']}.",
                  f"- Tested commit: {item.get('tested_commit_sha')}.",
                  f"- Population counts: {json.dumps(item.get('population_case_counts', {}), sort_keys=True)}.",
                  f"- Execution accounting: {json.dumps(item.get('execution_accounting', {}), sort_keys=True)}.",
                  f"- Naturalistic cases in latest campaign: {item.get('naturalistic_case_count', 0)}."]
    else:
        lines.append("- No immutable campaign report was found in the current checkout.")
    lines += ["", "Open-World outcomes are not a single accuracy denominator. See population, target, and execution accounting separately.",
              "", "## External lexical acquisition", ""]
    if ext.get("manifest_available"):
        lines += [f"- Status: {ext.get('status')}; snapshot: {ext.get('source', {}).get('snapshot_id')}.",
                  f"- Physical shards: {ext.get('shard_inventory', {}).get('file_count')} / {ext.get('shard_inventory', {}).get('manifest_batch_count')} ({ext.get('shard_inventory', {}).get('status')}); total compressed bytes: {ext.get('shard_inventory', {}).get('total_size_bytes')}.",
                  f"- Processed headwords: {progress.get('processed_headwords')} / {progress.get('expected_headwords')} ({progress.get('headword_completion_percent')}%).",
                  f"- Entries / senses: {progress.get('processed_entries')} / {progress.get('processed_senses')}.",
                  f"- Batches: {progress.get('batch_count')}; stored bytes: {progress.get('stored_bytes')} / {progress.get('storage_budget_bytes')}.",
                  f"- Retry recovery: {progress.get('recovered_headwords')} recovered; {progress.get('pending_retries')} pending; {progress.get('retry_dead_letter_headwords')} dead-lettered.",
                  f"- PUD report: {pud.get('status')} (shards {pud.get('evaluated_shard_count')} / {pud.get('current_manifest_batch_count')})."]
        if pud.get("status") == "fresh_for_current_shard_count":
            lines += [f"- Exact surface coverage: {pud.get('exact_surface_token_coverage')}; OOV rate: {pud.get('oov_rate')}.",
                      f"- UPOS candidate recall: {pud.get('gold_upos_candidate_recall')}; lemma coverage: {pud.get('gold_lemma_coverage')}.",
                      f"- Morphology candidate-pool precision/recall: {pud.get('morphology_candidate_pool_precision')} / {pud.get('morphology_candidate_recall')}."]
        else:
            lines.append("- Historical PUD metrics are not considered current until recalculated against the current shard count.")
    else:
        lines.append("- Manifest unavailable; absence is not treated as zero progress.")
    lines += ["", "External records remain candidate evidence. Exact coverage is not contextual POS prediction, morphology prediction, sense accuracy, or semantic correctness.",
              "", "## GitHub Actions execution status", ""]
    workflow_summary = report["workflow_evidence"]
    lines.append(f"Workflow definitions collected: {workflow_summary['workflow_count']}; with a latest non-PR run: {workflow_summary['latest_run_count']}.")
    lines.append(f"Latest run status counts: {json.dumps(workflow_summary['status_counts'], sort_keys=True)}.")
    failed_runs = [item for item in workflow_summary["workflows"]
                   if (item.get("latest_run") or {}).get("conclusion") in {"failure", "timed_out", "action_required", "startup_failure"}]
    for item in failed_runs[:20]:
        latest_run = item.get("latest_run") or {}
        lines.append(f"- {item.get('name')} ({item.get('path')}): {latest_run.get('conclusion')} — {latest_run.get('html_url')}.")
    if workflow_summary.get("collection_errors"):
        lines.append(f"- Workflow status collection errors: {len(workflow_summary['collection_errors'])}.")
    if workflow_summary.get("artifact_collection_errors"):
        lines.append(f"- Workflow artifact metadata collection errors: {len(workflow_summary['artifact_collection_errors'])}.")
    if workflow_summary["status"] == "not_collected":
        lines.append("- Live workflow statuses were not collected in this snapshot.")
    lines += ["", workflow_summary["interpretation_boundary"], "", "## Growth planner", ""]
    growth = report["growth_plan"]
    if growth["status"] == "available":
        lines.append(f"Plan generated: {growth.get('generated_at')}; campaigns analyzed: {growth.get('campaigns_analyzed')}.")
        for n, action in enumerate(growth["ranked_actions"][:10], 1):
            lines.append(f"{n}. {action.get('stage')}: {action.get('proposed_action') or action.get('action')} (gate: {action.get('acceptance_gate')}).")
    else:
        lines.append("Growth plan not collected.")
    lines += ["", "## New observations and phase routing", "",
              "| Observation | Severity | Phase impacts | Route |", "|---|---|---|---|"]
    for item in report["discoveries"]:
        lines.append(f"| {item['summary']} | {item['severity']} | {', '.join(item['phase_impacts'])} | {item['route']} |")
    lines += ["", "## Integrated discovery priorities", "",
              "| Rank | Discovery | Priority band | Reasons | Existing backlog links |",
              "|---:|---|---|---|---|"]
    for item in report.get("integrated_priorities", []):
        finding = next((x for x in report["discoveries"] if x.get("id") == item.get("discovery_id")), {})
        lines.append(f"| {item['rank']} | {item.get('kind')} | {item.get('priority_band')} | {', '.join(item.get('priority_reasons', []))} | {', '.join(finding.get('related_backlog_items', []))} |")
    lines += ["", "Prioritization preserves source-specific growth metrics; it does not calculate a combined intelligence or semantic-quality score.",
              "", "## Review-only phase proposals", "",
              "| Proposal | Type | Priority | Route | Review status |",
              "|---|---|---|---|---|"]
    for proposal in report.get("review_proposals", []):
        lines.append(f"| {proposal['proposal_id']} — {proposal['title']} | {proposal['proposal_type']} | {proposal['priority_band']} | {proposal['route']} | {proposal['review_status']} |")
    lines += ["", "All observations require review. Existing continuations are preferred; accepted phase changes are amendment proposals; contract changes require explicit versioned migrations. The collector makes no runtime or phase-status changes.", "",
              "## Safety", "",
              "- No candidate resource promotion or canonical-contract mutation.",
              "- Missing results are not zero; skipped targets are not passes.",
              "- Naturalistic, randomized, controlled-diagnostic, and synthetic evidence remain separate.",
              "- No overall intelligence or semantic accuracy score is calculated.", ""]
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--external-manifest", type=Path)
    parser.add_argument("--external-checkpoint", type=Path)
    parser.add_argument("--external-branch-commit")
    parser.add_argument("--pud-evaluation", type=Path)
    parser.add_argument("--pud-error", type=Path)
    parser.add_argument("--external-shard-inventory", type=Path)
    parser.add_argument("--workflow-runs", type=Path)
    parser.add_argument("--growth-plan", type=Path)
    parser.add_argument("--max-campaigns", type=int, default=20)
    parser.add_argument("--repository", default="wizekin/USG-Workbench")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit-sha", default="unknown")
    parser.add_argument("--tree-sha")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args(argv)
    report = collect_catalogue(
        args.root, registry_path=args.registry, external_manifest_path=args.external_manifest,
        external_checkpoint_path=args.external_checkpoint, external_branch_commit=args.external_branch_commit,
        pud_evaluation_path=args.pud_evaluation, pud_error_path=args.pud_error,
        external_shard_inventory_path=args.external_shard_inventory,
        workflow_runs_path=args.workflow_runs,
        growth_plan_path=args.growth_plan, repository_name=args.repository, branch=args.branch,
        commit_sha=args.commit_sha, tree_sha=args.tree_sha, max_campaigns=args.max_campaigns)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"contract": report["contract"], "source_families": report["asset_summary"]["source_family_count"],
                      "indexed_paths": report["asset_summary"]["unique_indexed_path_count"],
                      "campaigns": report["open_world"]["campaign_count"], "discoveries": len(report["discoveries"]),
                      "external_status": report["external_lexical"]["status"], "output": str(args.output)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
