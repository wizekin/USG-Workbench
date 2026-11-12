"""Versioned, non-mutating adapter for external lexical candidate packages.

The adapter validates the published candidate contract and exposes a stable
read-only view for downstream diagnostics. It never edits a LexicalResource,
selects an authoritative source, or promotes a candidate.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

CONTRACT = "USG-LEXICAL-CANDIDATES/0.1.0"
ADAPTER_CONTRACT = "USG-LEXICAL-ADAPTER/0.1.0"


class CandidatePackageError(ValueError):
    """Raised when a candidate package violates the adapter contract."""


def validate_candidate_package(package: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if not isinstance(package, dict):
        return {"status": "invalid", "findings": [{"code": "package_not_object", "severity": "error"}]}
    if package.get("contract") != CONTRACT:
        findings.append({"code": "unsupported_contract", "severity": "error"})
    candidates = package.get("candidates")
    if not isinstance(candidates, list):
        findings.append({"code": "candidates_not_list", "severity": "error"})
        candidates = []
    if package.get("candidate_count") != len(candidates):
        findings.append({"code": "candidate_count_mismatch", "severity": "error"})
    if package.get("promotion_allowed") is not False:
        findings.append({"code": "promotion_boundary_violation", "severity": "error"})
    digest = package.get("content_digest")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        findings.append({"code": "invalid_content_digest", "severity": "error"})
    provenance = package.get("source_provenance")
    if not isinstance(provenance, list) or not provenance:
        findings.append({"code": "missing_source_provenance", "severity": "error"})
    elif any(not isinstance(item, dict) or not isinstance(item.get("provider"), str) or not item["provider"]
             for item in provenance):
        findings.append({"code": "invalid_source_provenance", "severity": "error"})
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            findings.append({"code": "candidate_not_object", "severity": "error", "index": str(index)})
            continue
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            findings.append({"code": "candidate_missing_id", "severity": "error", "index": str(index)})
        elif candidate_id in seen:
            findings.append({"code": "duplicate_candidate_id", "severity": "error", "index": str(index)})
        else:
            seen.add(candidate_id)
        for field in ("lemma", "language", "source_provider", "source_id", "source_entry_id", "source_sense_id"):
            if not isinstance(candidate.get(field), str) or not candidate[field]:
                findings.append({"code": "candidate_missing_" + field, "severity": "error", "index": str(index)})
        if candidate.get("promotion_status") != "candidate_only":
            findings.append({"code": "candidate_not_candidate_only", "severity": "error", "index": str(index)})
        if not isinstance(candidate.get("examples", []), list):
            findings.append({"code": "candidate_examples_not_list", "severity": "error", "index": str(index)})
        if not isinstance(candidate.get("features", []), list):
            findings.append({"code": "candidate_features_not_list", "severity": "error", "index": str(index)})
        if not isinstance(candidate.get("observed_forms", []), list):
            findings.append({"code": "candidate_observed_forms_not_list", "severity": "error", "index": str(index)})
        if not isinstance(candidate.get("relations", []), list):
            findings.append({"code": "candidate_relations_not_list", "severity": "error", "index": str(index)})
    errors = [item for item in findings if item["severity"] == "error"]
    return {
        "contract": ADAPTER_CONTRACT,
        "status": "invalid" if errors else "valid",
        "candidate_count": len(candidates),
        "error_count": len(errors),
        "findings": findings,
        "promotion_allowed": False,
    }


def adapt_candidate_package(package: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a deterministic read-only candidate view."""
    validation = validate_candidate_package(package)
    if validation["status"] != "valid":
        raise CandidatePackageError("Invalid lexical candidate package: " + ", ".join(
            item["code"] for item in validation["findings"] if item["severity"] == "error"
        ))
    candidates = sorted(
        (dict(item) for item in package["candidates"]),
        key=lambda item: (item["language"], item["lemma"], item["part_of_speech"] or "",
                          item["candidate_id"]),
    )
    projection = {
        "contract": ADAPTER_CONTRACT,
        "source_contract": CONTRACT,
        "queried_form": package["queried_form"],
        "candidates": candidates,
        "source_provenance": package["source_provenance"],
        "source_content_digest": package["content_digest"],
        "promotion_allowed": False,
    }
    projection["adapter_digest"] = hashlib.sha256(
        json.dumps(projection, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return projection
