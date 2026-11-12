"""Cross-implementation and knowledge-layer evidence inputs for Phase 8 discovery."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MATRIX_PATH = Path("evaluations/system-wide/cross-implementation-matrix-2026-11-12.json")
PHASE7_RECORD = Path("documentation/PHASE-7-COMPLETION-RECORD.md")


def collect_system_intelligence(root: Path) -> dict[str, Any]:
    root = Path(root)
    findings: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "cross_implementation": {"status": "not_collected", "implementation_count": 0,
                                 "capability_count": 0, "non_component_tested_capabilities": [],
                                 "pending_gate_count": 0},
        "knowledge_layer": {"status": "not_collected", "unresolved_mapping_count": None,
                            "mapping_proposal_count": None, "promotion_allowed": False},
    }

    matrix_path = root / MATRIX_PATH
    if matrix_path.is_file():
        try:
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            summary["cross_implementation"] = {
                **summary["cross_implementation"], "status": "collection_error",
                "error": str(error),
            }
        else:
            if matrix.get("contract") != "USG-CROSS-IMPLEMENTATION-MATRIX/0.1.0":
                summary["cross_implementation"] = {
                    **summary["cross_implementation"], "status": "unsupported_contract",
                }
            else:
                implementations = matrix.get("implementations", [])
                capability_gaps = []
                for implementation in implementations:
                    for capability in implementation.get("capabilities", []):
                        status = str(capability.get("status", "unknown"))
                        if status != "component_tested":
                            capability_gaps.append({
                                "implementation_id": implementation.get("id"),
                                "implementation_version": implementation.get("version"),
                                "capability_id": capability.get("id"),
                                "status": status,
                                "evidence": capability.get("evidence", []),
                                "notes": capability.get("notes"),
                            })
                pending_gates = [
                    {"gate_id": item.get("id"), "status": item.get("status"),
                     "requirement": item.get("requirement")}
                    for item in matrix.get("cross_implementation_gates", [])
                    if item.get("status") != "accepted"
                ]
                summary["cross_implementation"] = {
                    "status": "collected",
                    "contract": matrix.get("contract"),
                    "assessment_date": matrix.get("assessment_date"),
                    "implementation_count": len(implementations),
                    "capability_count": sum(len(item.get("capabilities", [])) for item in implementations),
                    "non_component_tested_capabilities": capability_gaps,
                    "pending_gate_count": len(pending_gates),
                    "pending_gates": pending_gates,
                    "policy": matrix.get("policy", {}),
                    "source_path": MATRIX_PATH.as_posix(),
                }
                if capability_gaps:
                    findings.append({
                        "kind": "cross_implementation_conformance_gaps",
                        "severity": "high" if any(item["status"].startswith(("not_tested", "blocked")) for item in capability_gaps) else "medium",
                        "summary": "The conformance inventory contains capabilities that are not established, not tested, blocked, or deliberately disabled; component tests are not cross-runtime evidence.",
                        "evidence_refs": [MATRIX_PATH.as_posix()],
                        "phase_impacts": ["P8"],
                        "details": {"capability_gap_count": len(capability_gaps),
                                    "capability_gaps": capability_gaps[:50],
                                    "runtime_promotion_allowed": False},
                    })
                if pending_gates:
                    findings.append({
                        "kind": "cross_implementation_gates_pending",
                        "severity": "medium",
                        "summary": f"{len(pending_gates)} cross-implementation conformance gates remain unaccepted.",
                        "evidence_refs": [MATRIX_PATH.as_posix()],
                        "phase_impacts": ["P8"],
                        "details": {"pending_gate_count": len(pending_gates),
                                    "pending_gates": pending_gates,
                                    "independent_semantic_gold_required": True},
                    })

    phase7_path = root / PHASE7_RECORD
    if phase7_path.is_file():
        text = phase7_path.read_text(encoding="utf-8")
        match = re.search(
            r"(\d+)\s*/\s*(\d+)\s+cross-language sense-to-concept mapping proposals remained\s+UNRESOLVED",
            text, re.IGNORECASE)
        if match:
            unresolved, total = int(match.group(1)), int(match.group(2))
            summary["knowledge_layer"] = {
                "status": "collected",
                "unresolved_mapping_count": unresolved,
                "mapping_proposal_count": total,
                "promotion_allowed": False,
                "source_path": PHASE7_RECORD.as_posix(),
                "interpretation": "Unresolved proposals remain unresolved; the collector does not infer mappings or promote concepts.",
            }
            if unresolved:
                findings.append({
                    "kind": "knowledge_layer_unresolved_mapping_candidates",
                    "severity": "informational",
                    "summary": f"{unresolved} of {total} Phase 7 cross-language mapping proposals remain explicitly unresolved.",
                    "evidence_refs": [PHASE7_RECORD.as_posix()],
                    "phase_impacts": ["P7", "P8"],
                    "details": {"unresolved_mapping_count": unresolved,
                                "mapping_proposal_count": total,
                                "promotion_allowed": False,
                                "human_annotation_required": False},
                })
    return {"summary": summary, "findings": findings}
