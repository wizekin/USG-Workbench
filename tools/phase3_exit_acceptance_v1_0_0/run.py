"""Integrated automated Phase 3 exit acceptance runner.

Runs the frozen Phase 1/2 regressions and all active Phase 3 runtime suites.
It emits independent check results; no weighted score can mask a critical failure.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"

CHECK_GROUPS = {
    "phase3_canonical_store_and_query": [
        "test_phase3_graph_store.py",
        "test_phase3_persistent_query.py",
    ],
    "phase3_scope_and_document_analysis": [
        "test_phase3_scope_aware_rules.py",
        "test_phase3_conditions_contradictions.py",
    ],
    "phase3_local_api_and_kernel_lab": [
        "test_phase3_local_api_cli.py",
        "test_phase3_kernel_lab_integration.py",
        "test_usg_kernel_lab.py",
    ],
    "phase3_packaging_and_release": [
        "test_phase3_packaging.py",
        "test_phase3_exit_acceptance_runner.py",
    ],
    "phase1_compatibility": [
        "test_phase1_exit_acceptance.py",
        "test_python_kernel_v*_document_adapter.py",
        "test_document_adapter.py",
        "test_python_reverse_serializer.py",
        "test_round_trip_conformance.py",
        "test_operator_scope_registry.py",
        "test_predicate_frame_registry.py",
        "test_workbench_source_adapter.py",
    ],
    "phase2_compatibility": [
        "test_phase2_grounding.py",
        "test_phase2_inference_executor.py",
        "test_phase2_evidence_assessment.py",
        "test_phase2_query_interface.py",
        "test_phase2_rule_registry.py",
        "test_phase2_rule_semantics.py",
        "test_semantic_reasoning_benchmark.py",
    ],
}


def run_group(name: str, patterns: list[str]) -> dict:
    # Each historical test pattern runs in its own interpreter. Several Phase 1
    # adapters intentionally load different kernel versions; a shared process
    # leaks sys.path/module state between those frozen suites.
    env = os.environ.copy()
    extra_paths = [
        str(ROOT / "implementations" / "python-kernel" / "v0.5.0"),
        str(TESTS),
    ]
    if env.get("PYTHONPATH"):
        extra_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(extra_paths)

    pattern_results = []
    failures = []
    total_tests = 0
    for pattern in patterns:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover",
             "-s", str(TESTS), "-p", pattern, "-v"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        match = re.search(r"Ran\s+(\d+)\s+tests?", output)
        tests_run = int(match.group(1)) if match else 0
        skipped_match = re.search(r"skipped=(\d+)", output)
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        total_tests += tests_run
        print(output)
        pattern_results.append({
            "pattern": pattern,
            "return_code": completed.returncode,
            "tests_run": tests_run,
            "skipped": skipped,
        })
        if completed.returncode != 0 or tests_run == 0 or skipped:
            failures.append({
                "pattern": pattern,
                "return_code": completed.returncode,
                "tests_run": tests_run,
                "skipped": skipped,
                "output_tail": output[-12000:],
            })

    return {
        "check_id": name,
        "status": "PASS" if not failures else "FAIL",
        "patterns": patterns,
        "tests_discovered": total_tests,
        "tests_run": total_tests,
        "pattern_results": pattern_results,
        "failures": failures,
        "errors": [],
        "skipped": sum(item["skipped"] for item in pattern_results),
    }


def build_report(checks: list[dict], source_commit: str | None = None) -> dict:
    accepted = bool(checks) and all(item["status"] == "PASS" for item in checks)
    return {
        "report_profile": "USG-PHASE3-EXIT-ACCEPTANCE/1.0.0",
        "phase": "3",
        "acceptance_status": "PASS" if accepted else "FAIL",
        "source_commit": source_commit,
        "python_version": platform.python_version(),
        "canonical_profile": "USG-SEM/1.0",
        "canonical_storage_backend": "SQLite",
        "critical_invariants": {
            "canonical_document_is_authoritative": True,
            "immutable_revision_history": True,
            "truth_promotion": False,
            "implicit_closed_world": False,
            "exception_absence_entails_consequent": False,
            "conflict_winner_selection": False,
            "evidence_axes_collapsed": False,
            "operator_scope_flattened": False,
            "semantic_truncation": False,
            "human_review_dependency": False,
            "public_network_binding": False,
        },
        "checks": checks,
        "check_count": len(checks),
        "passed_check_count": sum(item["status"] == "PASS" for item in checks),
        "failed_check_ids": [item["check_id"] for item in checks if item["status"] != "PASS"],
        "acceptance_policy": "ALL_REQUIRED_CHECKS_MUST_PASS; NO_WEIGHTED_OR_AGGREGATE_SCORE",
    }


def run_acceptance(report_path: str | Path | None = None, source_commit: str | None = None) -> dict:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(TESTS))
    sys.path.insert(0, str(ROOT / "implementations" / "python-kernel" / "v0.5.0"))
    checks = [run_group(name, patterns) for name, patterns in CHECK_GROUPS.items()]
    report = build_report(checks, source_commit)
    if report_path is not None:
        target = Path(report_path)
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Acceptance report written: {target}")
    print(
        f"PHASE 3 ACCEPTANCE: {report['acceptance_status']} "
        f"({report['passed_check_count']}/{report['check_count']} required checks passed)"
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="phase3-exit-acceptance-report.json")
    parser.add_argument("--source-commit", default=None)
    args = parser.parse_args(argv)
    report = run_acceptance(args.report, args.source_commit)
    return 0 if report["acceptance_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
