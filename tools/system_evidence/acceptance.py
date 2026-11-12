"""Integrated structural/governance acceptance gate for the Phase 8 evidence control plane."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path("config/phase-resource-manifests/phase8-system-evidence-integration.json")
MANIFEST_SCHEMA_PATH = Path("specifications/usg-phase-resource-manifest-0.1.0.schema.json")
RESOURCE_MAP_PATH = Path("config/usg-phase-resource-consumption-map-0.1.0.json")
RESOURCE_MAP_SCHEMA_PATH = Path("specifications/usg-phase-resource-consumption-map-0.1.0.schema.json")


def evaluate_phase8_acceptance(report: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """Evaluate whether Phase 8 is structurally ready for human acceptance review.

    This gate can never mark Phase 8 accepted or mutate canonical/runtime state.
    """
    root = Path(root)
    checks: list[dict[str, Any]] = []

    def check(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "passed": bool(passed), "detail": detail})

    try:
        resource_map = json.loads((root / RESOURCE_MAP_PATH).read_text(encoding="utf-8"))
        resource_map_schema = json.loads((root / RESOURCE_MAP_SCHEMA_PATH).read_text(encoding="utf-8"))
        Draft202012Validator(resource_map_schema, format_checker=FormatChecker()).validate(resource_map)
        check("P8-MAP", resource_map.get("contract") == "USG-PHASE-RESOURCE-CONSUMPTION-MAP/0.1.0",
              "Phase resource-consumption map parses and validates against its versioned schema.")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        resource_map = {}
        check("P8-MAP", False, f"Phase resource-consumption map validation failed: {error}")

    try:
        manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
        manifest_schema = json.loads((root / MANIFEST_SCHEMA_PATH).read_text(encoding="utf-8"))
        Draft202012Validator(manifest_schema, format_checker=FormatChecker()).validate(manifest)
        check("P8-MANIFEST", manifest.get("phase_id") == "P8",
              "Phase 8 resource manifest parses and validates against its versioned schema.")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        manifest = {}
        check("P8-MANIFEST", False, f"Phase 8 resource manifest validation failed: {error}")

    phase_ids = {str(item.get("id")) for item in report.get("phase_status", [])}
    check("P8-PHASE-COVERAGE", {f"P{i}" for i in range(1, 9)} <= phase_ids,
          "Catalogue includes phase status records for Phases 1–8.")

    phase8 = next((item for item in resource_map.get("phases", [])
                   if item.get("phase_id") == "P8"), {})
    available_families = {item.get("id") for item in report.get("source_families", [])}
    required_families = set(phase8.get("required_sources", []))
    missing_required = sorted(required_families - available_families)
    check("P8-RESOURCE-COVERAGE", not missing_required,
          "All required Phase 8 source families are represented in the catalogue."
          if not missing_required else f"Missing required source families: {missing_required}")

    required_sections = (
        "source_registry", "resource_consumption_map", "asset_summary", "open_world",
        "external_lexical", "workflow_evidence", "growth_plan", "discoveries",
        "evidence_quality_diagnostics", "integrated_priorities", "review_proposals", "governance",
    )
    missing_sections = [key for key in required_sections if key not in report]
    check("P8-INTEGRATED-CATALOGUE", not missing_sections,
          "Catalogue contains every required evidence, diagnostics, routing, and planning section."
          if not missing_sections else f"Missing catalogue sections: {missing_sections}")

    discoveries = report.get("discoveries", [])
    priorities = report.get("integrated_priorities", [])
    proposals = report.get("review_proposals", [])
    check("P8-DISCOVERY-COVERAGE", len(priorities) == len(discoveries),
          "Every deduplicated discovery appears in the integrated priority queue.")
    check("P8-PROPOSAL-COVERAGE", len(proposals) == len(discoveries),
          "Every discovery has a corresponding review-only proposal record.")
    unsafe_findings = [item.get("id") for item in discoveries
                       if item.get("runtime_change_allowed") is not False
                       or item.get("review_status") != "observed_requires_review"]
    check("P8-DISCOVERY-GOVERNANCE", not unsafe_findings,
          "All findings remain review-required and cannot change runtime."
          if not unsafe_findings else f"Findings violate review-only governance: {unsafe_findings[:10]}")
    unsafe_proposals = [item.get("proposal_id") for item in proposals
                        if item.get("review_status") != "draft_requires_review"
                        or item.get("implementation_status") != "not_implemented"
                        or item.get("phase_status_mutation_allowed") is not False
                        or item.get("canonical_contract_mutation_allowed") is not False
                        or item.get("runtime_promotion_allowed") is not False]
    check("P8-PROPOSAL-GOVERNANCE", not unsafe_proposals,
          "All proposals remain drafts and cannot mutate phase status, contracts, or runtime."
          if not unsafe_proposals else f"Proposals violate review-only governance: {unsafe_proposals[:10]}")

    governance = report.get("governance", {})
    safe_governance = (
        governance.get("runtime_mutations_performed") is False
        and governance.get("candidate_resources_promoted") is False
        and governance.get("phase_statuses_changed") is False
        and governance.get("canonical_contracts_changed") is False
        and governance.get("amendments_require_review") is True
    )
    check("P8-GLOBAL-GOVERNANCE", safe_governance,
          "Catalogue confirms no runtime mutation, candidate promotion, phase-status mutation, or canonical-contract change.")

    workflow = report.get("workflow_evidence", {})
    check("P8-WORKFLOW-OBSERVABILITY", workflow.get("status") == "collected"
          and int(workflow.get("workflow_count", 0) or 0) > 0,
          "Live workflow definitions and latest-run collection are present; failures remain evidence, not passes.")

    external = report.get("external_lexical", {})
    pud = external.get("pud_evaluation", {}) if isinstance(external, dict) else {}
    pud_status = pud.get("status")
    check("P8-LEXICAL-EVIDENCE-BOUNDARY", pud_status in {
        "fresh_for_current_shard_count", "stale_shard_count_mismatch",
        "not_available", "not_run_without_manifest"
    } and pud.get("rights_and_runtime_boundary", {}).get("runtime_promotion_allowed", False) is False,
          "PUD evidence state is explicit and candidate data cannot be promoted by the collector.")

    passed = all(item["passed"] for item in checks)
    return {
        "contract": "USG-PHASE8-INTEGRATED-ACCEPTANCE/0.1.0",
        "status": "eligible_for_review" if passed else "blocked",
        "phase_accepted": False,
        "checks_passed": sum(item["passed"] for item in checks),
        "checks_total": len(checks),
        "checks": checks,
        "governance": {
            "phase_status_mutation_allowed": False,
            "canonical_contract_mutation_allowed": False,
            "runtime_mutation_allowed": False,
            "candidate_promotion_allowed": False,
            "human_acceptance_required": True,
        },
        "limitations": [
            "A passing gate establishes structural completeness and governance compliance, not semantic accuracy or AGI.",
            "This report never marks Phase 8 accepted; explicit human acceptance and evidence review remain required.",
            "Naturalistic and independent semantic evaluation must be judged within their documented populations."
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = json.loads(args.catalogue.read_text(encoding="utf-8"))
    result = evaluate_phase8_acceptance(report, args.root)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] == "eligible_for_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
