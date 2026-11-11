"""Run trusted, fixture-backed operation suites for registered USG components.

These suites are separate from random natural-language prompt scoring. Every
suite uses repository-controlled fixtures and independent expected outputs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"
REGISTRY = ROOT / "tools" / "open_world_evaluation" / "target_profiles.json"

# Test suites whose fixtures include expected outcomes independently of the
# component under test. Nominal v0.4.1 is explicitly development self-consistency,
# not held-out semantic accuracy.
SUITES: dict[str, dict[str, Any]] = {
    "phase2-structured-semantic-reasoning": {
        "tests": ["test_phase2_inference_executor.py"],
        "oracle": "executor benchmark fixtures: expected completion status, candidate count, diagnostics, and safety invariants",
        "claim": "operation_contract_conformance",
    },
    "phase3-canonical-sqlite-store": {
        "tests": ["test_phase3_graph_store.py", "test_phase3_persistent_query.py"],
        "oracle": "canonical snapshot, SHA-256, revision, compare-and-swap, index integrity, and pinned-query assertions",
        "claim": "operation_contract_conformance",
    },
    "phase6-candidate-expansion": {
        "tests": ["test_phase6_step_6_5_predicate_argument.py", "test_phase6_nominal_candidate_v0_4_1.py"],
        "oracle": "gold role bindings/spans, negative abstention, and declared development-only candidate gate",
        "claim": "mixed_gold_and_development_oracles",
    },
    "python-usg-sem-document-adapters-v15": {
        "tests": ["test_python_kernel_v15_document_adapter.py"],
        "oracle": "complete multi-family fixture: native projection, round-trip preservation, cross-family edits, and canonical-only record retention",
        "claim": "fixture_backed_adapter_contract_conformance",
        "python_paths": [
            "implementations/python-kernel/v0.5.0",
            "implementations/python-kernel/v0.8.0",
            "implementations/python-kernel/v0.9.0",
            "implementations/python-kernel/v1.0.0",
            "implementations/python-kernel/v1.1.0",
            "implementations/python-kernel/v1.2.0",
            "implementations/python-kernel/v1.2.1",
            "implementations/python-kernel/v1.3.0",
            "implementations/python-kernel/v1.4.0",
        ],
    },
    "python-native-semantic-models-v06-v14": {
        "tests": [
            "implementations/python-kernel/v0.6.0/tests/test_referent_identity.py",
            "implementations/python-kernel/v0.7.0/tests/test_native_mention.py",
            "implementations/python-kernel/v0.8.0/tests/test_native_assertion.py",
            "implementations/python-kernel/v0.9.0/tests/test_native_evidence.py",
            "implementations/python-kernel/v1.0.0/tests/test_native_context.py",
            "implementations/python-kernel/v1.1.0/tests/test_native_expression_relation.py",
            "implementations/python-kernel/v1.2.1/tests/test_native_unresolved_item.py",
            "implementations/python-kernel/v1.3.0/tests/test_native_derivation.py",
            "implementations/python-kernel/v1.4.0/tests/test_native_definitions.py",
        ],
        "oracle": "versioned native model constructor invariants, typed-reference boundaries, identity semantics, and definition catalogue invariants",
        "claim": "native_model_contract_conformance",
        "python_paths": [
            "implementations/python-kernel/v0.6.0/usg_identity_v06",
            "implementations/python-kernel/v0.7.0/usg_discourse_v07",
            "implementations/python-kernel/v0.8.0/usg_assertion_v08",
            "implementations/python-kernel/v0.9.0/usg_evidence_v09",
            "implementations/python-kernel/v1.0.0/usg_context_v10",
            "implementations/python-kernel/v1.1.0/usg_expression_relation_v11",
            "implementations/python-kernel/v1.2.1/usg_unresolved_v121",
            "implementations/python-kernel/v1.3.0/usg_derivation_v13",
            "implementations/python-kernel/v1.4.0/usg_definitions_v14",
        ],
    },
    "kernel-lab-local-api-cli": {
        "tests": ["test_phase3_local_api_cli.py"],
        "oracle": "HTTP dispatch contracts, SQLite persistence/revision semantics, query snapshot behavior, interpretation persistence, route validation, and loopback-only server binding",
        "claim": "local_api_and_cli_contract_conformance",
    },
    "workbench-to-canonical-adapter": {
        "tests": ["test_workbench_source_adapter.py"],
        "oracle": "source-aligned Unicode offset conversion, USG-SEM/1.0 schema validation, explicit predicate/operator structure, unresolved-reference preservation, and acceptance-boundary archival",
        "claim": "fixture_backed_adapter_contract_conformance",
    },
}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_suites() -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    target_ids = {item["component_id"] for item in registry.get("targets", [])}
    results = []
    for target_id, specification in SUITES.items():
        if target_id not in target_ids:
            raise ValueError(f"operation suite target is not registered: {target_id}")
        target_tests = []
        for filename in specification["tests"]:
            relative_path = Path(filename)
            path = ROOT / relative_path if relative_path.parts[0] == "implementations" else TESTS / relative_path
            if not path.is_file():
                raise FileNotFoundError(f"registered operation-oracle test is missing: {filename}")
            for relative in specification.get("python_paths", []):
                resolved = str(ROOT / relative)
                if resolved not in sys.path:
                    sys.path.insert(0, resolved)
            module = _load_module(path, "ow12_" + filename.replace(".", "_"))
            target_tests.append(unittest.defaultTestLoader.loadTestsFromModule(module))
        suite = unittest.TestSuite(target_tests)
        result = unittest.TestResult()
        suite.run(result)
        results.append({
            "component_id": target_id,
            "test_files": specification["tests"],
            "test_count": result.testsRun,
            "passed": result.testsRun - len(result.failures) - len(result.errors),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "failure_details": [
                {"test": test.id(), "traceback": trace[-12000:]}
                for test, trace in result.failures + result.errors
            ],
            "oracle_description": specification["oracle"],
            "claim_level": specification["claim"],
            "status": "PASS" if result.wasSuccessful() and result.testsRun > 0 else "FAIL",
        })
    return {
        "report_version": "1.0.0",
        "program": "USG-OPEN-WORLD-OPERATION-ORACLES",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "target_profile_count": len(target_ids),
        "operation_suite_count": len(results),
        "test_count": sum(item["test_count"] for item in results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(item["failed"] for item in results),
        "errors": sum(item["errors"] for item in results),
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "semantic_accuracy_claim": "not_assessed_as_a_general_open_world_metric",
        "suites": results,
        "limitations": [
            "Operation suites use controlled repository fixtures; they are not a naturalistic open-world corpus.",
            "The Phase 6 v0.4.1 nominal candidate gate is development self-consistency on a fixture-derived lexicon, not held-out accuracy.",
            "Operation-level suites cover only the listed targets and fixtures; other targets remain import-smoke-only or not-executed.",
            "The v1.5 composed-adapter suite is a controlled fixture population, not an independently sampled production corpus.",
            "Native model suites exercise selected v0.6 referent-identity and v1.4 definition-model boundaries, not every versioned model package.",
            "Browser checks exercise the local Workbench UI workflow only; they do not assess semantic correctness.",
            "Passing tests establish only the assertions encoded by their independent fixture oracles.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run independent fixture-backed USG operation oracles.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("refusing to overwrite an existing operation-oracle report")
    try:
        report = run_suites()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": report["status"],
        "test_count": report["test_count"],
        "passed": report["passed"],
        "failed": report["failed"],
        "errors": report["errors"],
        "suites": [{"component_id": x["component_id"], "status": x["status"], "test_count": x["test_count"]} for x in report["suites"]],
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
