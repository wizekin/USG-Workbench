"""Evidence freshness and cross-source consistency diagnostics for Phase 8."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


FRESHNESS_LIMIT_HOURS = {
    "external_lexical_manifest": 72,
    "external_lexical_pud_evaluation": 30 * 24,
    "growth_plan": 48,
}


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_diagnostic(source: str, value: Any, observed_at: datetime,
                    maximum_hours: int) -> dict[str, Any] | None:
    if value is None:
        return None
    timestamp = _timestamp(value)
    if timestamp is None:
        return {
            "kind": "evidence_timestamp_invalid",
            "severity": "medium",
            "source": source,
            "observed_timestamp": value,
            "summary": f"{source} has a timestamp that cannot be interpreted; freshness is unknown.",
            "evidence_refs": [source],
        }
    age_hours = round((observed_at - timestamp).total_seconds() / 3600, 2)
    if age_hours < 0:
        return {
            "kind": "evidence_timestamp_in_future",
            "severity": "high",
            "source": source,
            "observed_timestamp": value,
            "age_hours": age_hours,
            "summary": f"{source} timestamp is later than the catalogue observation time.",
            "evidence_refs": [source],
        }
    if age_hours > maximum_hours:
        return {
            "kind": "evidence_source_stale",
            "severity": "medium",
            "source": source,
            "observed_timestamp": value,
            "age_hours": age_hours,
            "maximum_age_hours": maximum_hours,
            "summary": f"{source} is {age_hours} hours old; its configured freshness window is {maximum_hours} hours.",
            "evidence_refs": [source],
        }
    return None


def evidence_quality_diagnostics(external: dict[str, Any], campaigns: list[dict[str, Any]],
                                 growth: dict[str, Any] | None,
                                 observed_at: str) -> list[dict[str, Any]]:
    """Return actionable diagnostics; unknown timestamps are not silently treated as fresh."""
    now = _timestamp(observed_at)
    if now is None:
        raise ValueError("observed_at must be an ISO-8601 timestamp")
    findings: list[dict[str, Any]] = []

    manifest = external.get("manifest") if isinstance(external.get("manifest"), dict) else {}
    progress = external.get("progress") if isinstance(external.get("progress"), dict) else {}
    pud = external.get("pud_evaluation") if isinstance(external.get("pud_evaluation"), dict) else {}

    candidates = [
        ("external_lexical_manifest", progress.get("updated_at"),
         FRESHNESS_LIMIT_HOURS["external_lexical_manifest"]),
        ("external_lexical_pud_evaluation",
         pud.get("generated_at") or pud.get("evaluated_at") or pud.get("created_at"),
         FRESHNESS_LIMIT_HOURS["external_lexical_pud_evaluation"]),
        ("growth_plan", growth.get("generated_at") if growth else None,
         FRESHNESS_LIMIT_HOURS["growth_plan"]),
    ]
    for source, timestamp, limit in candidates:
        diagnostic = _age_diagnostic(source, timestamp, now, limit)
        if diagnostic:
            findings.append(diagnostic)

    processed, expected = progress.get("processed_headwords"), progress.get("expected_headwords")
    if isinstance(processed, int) and isinstance(expected, int) and processed > expected:
        findings.append({
            "kind": "external_lexical_progress_contradiction", "severity": "high",
            "summary": "External lexical processed headwords exceed the declared expected headword population.",
            "evidence_refs": ["external_lexical.progress.processed_headwords",
                              "external_lexical.progress.expected_headwords"],
            "processed_headwords": processed, "expected_headwords": expected,
        })

    manifest_batches = progress.get("batch_count")
    physical_shards = external.get("shard_inventory", {}).get("file_count")
    if isinstance(manifest_batches, int) and isinstance(physical_shards, int) and manifest_batches != physical_shards:
        findings.append({
            "kind": "external_lexical_shard_count_contradiction", "severity": "high",
            "summary": "External lexical manifest batch count disagrees with the physical shard inventory.",
            "evidence_refs": ["external_lexical.progress.batch_count",
                              "external_lexical.shard_inventory.file_count"],
            "manifest_batch_count": manifest_batches, "physical_shard_count": physical_shards,
        })
    evaluated_shards = pud.get("evaluated_shard_count")
    if isinstance(manifest_batches, int) and isinstance(evaluated_shards, int) and manifest_batches != evaluated_shards:
        findings.append({
            "kind": "external_lexical_pud_shard_contradiction", "severity": "high",
            "summary": "The PUD evaluation shard count disagrees with the current external lexical manifest.",
            "evidence_refs": ["external_lexical.pud_evaluation.evaluated_shard_count",
                              "external_lexical.progress.batch_count"],
            "evaluated_shard_count": evaluated_shards, "manifest_batch_count": manifest_batches,
        })

    for campaign in campaigns:
        populations = campaign.get("population_case_counts")
        scenario_count = campaign.get("scenario_count")
        if isinstance(populations, dict) and isinstance(scenario_count, int):
            numeric = [value for value in populations.values() if isinstance(value, int) and not isinstance(value, bool)]
            if len(numeric) == len(populations) and sum(numeric) != scenario_count:
                findings.append({
                    "kind": "campaign_population_count_contradiction", "severity": "high",
                    "summary": f"Campaign {campaign.get('campaign_id')} population counts do not sum to its declared scenario count.",
                    "evidence_refs": [str(campaign.get("report_path") or "open_world.campaign")],
                    "campaign_id": campaign.get("campaign_id"),
                    "scenario_count": scenario_count, "population_case_count_sum": sum(numeric),
                })
        accounting = campaign.get("execution_accounting")
        if isinstance(accounting, dict):
            attempted = accounting.get("actual_attempt_count")
            not_executed = accounting.get("not_executed_record_count")
            if isinstance(attempted, int) and isinstance(not_executed, int) and isinstance(scenario_count, int):
                if attempted + not_executed != scenario_count:
                    findings.append({
                        "kind": "campaign_execution_accounting_contradiction", "severity": "high",
                        "summary": f"Campaign {campaign.get('campaign_id')} execution accounting does not reconcile with its scenario count.",
                        "evidence_refs": [str(campaign.get("report_path") or "open_world.campaign")],
                        "campaign_id": campaign.get("campaign_id"), "scenario_count": scenario_count,
                        "actual_attempt_count": attempted, "not_executed_record_count": not_executed,
                    })
    return findings
