"""Run the complete Phase 2 exit-acceptance gate and emit a machine-readable report."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def command(label: str, args: list[str], env: dict[str, str] | None = None) -> dict:
    started = time.monotonic()
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        args,
        cwd=ROOT,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = proc.stdout or ""
    return {
        "id": label,
        "command": args,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "return_code": proc.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output_tail": output[-6000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="phase2-exit-acceptance-report.json")
    args = parser.parse_args()

    packages = [
        "tools/semantic_reasoning_benchmark_v1_0_0",
        "tools/semantic_rule_registry_v1_0_0",
        "tools/semantic_rule_semantics_v1_0_0",
        "tools/semantic_grounding_v1_0_0",
        "tools/semantic_inference_v1_0_0",
        "tools/semantic_evidence_assessment_v1_0_0",
        "tools/semantic_query_interface_v1_0_0",
        "tools/usg-kernel-lab",
    ]

    checks = [
        ("compile_all_phase2_packages", [sys.executable, "-m", "compileall", "-q", *packages], None),
        ("validate_rule_registry", [sys.executable, "-m", "tools.semantic_rule_registry_v1_0_0.validator"], None),
        ("validate_rule_semantics", [sys.executable, "-m", "tools.semantic_rule_semantics_v1_0_0.validator"], None),
        ("frozen_step_2_2_benchmark", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_semantic_reasoning_benchmark.py", "-v"], None),
        ("phase2_all_step_regressions", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_phase2_*.py", "-v"], None),
        ("kernel_lab_integration", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_usg_kernel_lab.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.7.0", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_exit_acceptance", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_phase1_exit_acceptance.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_versioned_document_adapters", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_python_kernel_v*_document_adapter.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_predicate_frame_registry", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_predicate_frame_registry.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_operator_scope_registry", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_operator_scope_registry.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_document_adapter", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_document_adapter.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_reverse_serializer", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_python_reverse_serializer.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_round_trip_conformance", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_round_trip_conformance.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_workbench_source_python", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_workbench_source_adapter.py", "-v"], {"PYTHONPATH": os.pathsep.join(filter(None, ["implementations/python-kernel/v0.5.0", "tests", os.environ.get("PYTHONPATH", "")]))}),
        ("phase1_workbench_source_node", ["node", "--test", "tests/test_workbench_source_adapter.js"], None),
        ("phase1_workbench_reconstruction_node", ["node", "--test", "tests/test_workbench_reconstruction_adapter.js"], None),
    ]

    results = []
    for label, argv, env in checks:
        result = command(label, argv, env)
        results.append(result)
        print(f"[{result['status']}] {label} ({result['duration_seconds']}s)")
        if result["status"] != "PASS":
            print(result["output_tail"])

    passed = sum(item["status"] == "PASS" for item in results)
    failed = len(results) - passed
    report = {
        "contract": "USG-PHASE-2-EXIT-ACCEPTANCE/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "commit": os.environ.get("GITHUB_SHA"),
        "phase": "2",
        "status": "ACCEPTED" if failed == 0 else "NOT_ACCEPTED",
        "checks_passed": passed,
        "checks_failed": failed,
        "checks_total": len(results),
        "independent_evidence_axes": [
            "quote_alignment",
            "declared_semantic_support",
            "relation_claim_assessment",
            "exact_scope_conflict_assessment",
            "source_independence",
            "corroboration",
            "external_verification",
        ],
        "truth_promotion_performed": False,
        "conflict_winner_selection_performed": False,
        "human_review_gate_required": False,
        "results": results,
    }
    report_path = ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Acceptance report: {report_path}")
    print(f"Phase 2 exit status: {report['status']} ({passed}/{len(results)} checks passed)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
