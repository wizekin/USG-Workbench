"""Bounded Phase 4 v0.1.0 exit-acceptance evaluator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.phase4_interpretation_benchmark_v0_1_0 import evaluate as evaluate_benchmark

def evaluate() -> dict:
    docs = [
        f"PHASE-4-STEP-4.{step}-{name}.md"
        for step, name in [
            ("1", "INTERPRETATION-CONTRACT"),
            ("2", "SOURCE-INGESTION-SEGMENTATION"),
            ("3", "LEXICAL-ANALYSIS"),
            ("4", "SYNTAX-ANALYSIS"),
            ("5", "SEMANTIC-COMPOSITION"),
            ("6", "MENTIONS-REFERENCE"),
            ("7", "DISCOURSE-CONTEXT"),
            ("8", "ASSERTION-EVIDENCE"),
            ("9", "RESOURCE-REGISTRY"),
            ("10", "MODEL-ADAPTER"),
            ("11", "INTEGRATED-API"),
            ("12", "BENCHMARK"),
        ]
    ]
    missing_docs = [name for name in docs if not (ROOT / "documentation" / name).is_file()]
    required_modules = [
        "source.py", "lexical.py", "syntax.py", "compose.py", "mentions.py",
        "discourse.py", "assertion_evidence.py", "resources.py", "model_adapter.py",
        "pipeline.py",
    ]
    missing_modules = [
        name for name in required_modules
        if not (ROOT / "tools" / "usg_interpretation_v0_1_0" / name).is_file()
    ]
    fixtures_path = ROOT / "benchmarks/phase4-interpretation/v0.1.0/fixtures.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    benchmark = evaluate_benchmark(fixtures)
    checks = {
        "all_step_definition_and_implementation_docs_present": not missing_docs,
        "all_interpretation_stages_present": not missing_modules,
        "frozen_benchmark_accepted": all(benchmark["acceptance"].values()),
        "usg_sem_1_0_schema_present": (ROOT / "specifications/usg-sem-1.0.schema.json").is_file(),
        "canonical_sqlite_store_present": (ROOT / "tools/semantic_graph_store_v1_0_0/store.py").is_file(),
        "kernel_lab_raw_text_interface_present": (ROOT / "tools/usg-kernel-lab/index.html").is_file(),
    }
    return {
        "acceptance_profile": "USG-INTERPRET/0.1.0",
        "release_scope": "BOUNDED_DEMONSTRATOR",
        "result": "ACCEPTED_BOUNDED_DEMONSTRATOR" if all(checks.values()) else "NOT_ACCEPTED",
        "checks": checks,
        "missing_step_documents": missing_docs,
        "missing_interpretation_modules": missing_modules,
        "benchmark_metrics": benchmark["metrics"],
        "limitations": [
            "The bundled lexical resource is a tiny demonstrator lexicon, not broad English or Arabic coverage.",
            "Only explicit English SVO and Modern Standard Arabic SVO/VSO three-word patterns are enabled.",
            "Multi-sentence composition, negation, modality, tense/aspect operators, coordination, nested syntax, and general coreference remain unsupported.",
            "Repeated mention surfaces remain unresolved candidates, not established identity.",
            "Discourse markers are detected but their full scope and entailments are not inferred.",
            "Assertions remain DISCOVERED with UNKNOWN epistemic status and NONE commitment; evidence support remains NOT_ESTABLISHED.",
            "Optional model proposals are source-span validated but are not automatically promoted into authoritative resources.",
            "Acceptance applies only to the frozen six-case v0.1.0 benchmark and is not a claim of unrestricted language understanding or truth determination.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate()
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if report["result"] == "ACCEPTED_BOUNDED_DEMONSTRATOR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
