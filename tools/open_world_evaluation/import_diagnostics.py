"""Import repository-authored Phase 4/5 gold fixtures as controlled OW scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TARGETS_PATH = ROOT / "tools" / "open_world_evaluation" / "target_profiles.json"
PHASE4_CORPUS = ROOT / "benchmarks" / "phase4-interpretation" / "v0.1.0" / "fixtures.json"
PHASE5_CORPUS = ROOT / "benchmarks" / "phase5-interpretation-v0.2.1" / "corpus.json"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _target_registry() -> dict[str, dict[str, Any]]:
    data = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return {item["component_id"]: item for item in data["targets"]}


def _case(
    *,
    case_id: str,
    source_id: str,
    source_digest: str,
    source_version: str,
    text: str,
    language: str,
    target: dict[str, Any],
    expected: dict[str, Any],
    taxonomy: list[str],
    master_seed: str,
    created_at: str,
) -> dict[str, Any]:
    case_seed = _sha256(f"{master_seed}:{case_id}".encode("utf-8"))
    return {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "population": "controlled_diagnostic",
        "created_at": created_at,
        "generator": {
            "id": "usg-repository-diagnostic-corpus-importer",
            "version": "1.0.0",
            "seed_mode": "imported",
            "master_seed": master_seed,
            "case_seed": case_seed,
            "generation_trace": [
                f"source={source_id}",
                f"source_version={source_version}",
                "imported_without_text_mutation",
            ],
            "mutation_ops": [],
        },
        "source": {
            "kind": "diagnostic_fixture",
            "source_id": source_id,
            "content_digest": source_digest,
            "transformations": ["scenario-envelope_mapping_only"],
        },
        "input": {
            "text": text,
            "utf8_sha256": _sha256(text.encode("utf-8")),
            "language_hint": language,
        },
        "target": {
            "component_id": target["component_id"],
            "component_version": target["component_version"],
            "entry_point": target["entry_point"],
            "interface": target["interface"],
            "contract_versions": target.get("contract_versions", []),
        },
        "taxonomy": {
            "labels": taxonomy,
            "unclassified": False,
        },
        "oracle": {
            "type": "structural",
            "independent": True,
            "oracle_id": f"{source_id}:{case_id}",
            "expected": expected,
        },
        "resource_limits": {
            "wall_time_seconds": 30,
            "memory_megabytes": 1024,
            "max_input_bytes": 100_000,
            "network_access": False,
        },
    }


def import_diagnostic_scenarios(
    *,
    phase4_path: Path = PHASE4_CORPUS,
    phase5_path: Path = PHASE5_CORPUS,
    created_at: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    timestamp = created_at or _utc_now()
    targets = _target_registry()
    p4_bytes = phase4_path.read_bytes()
    p5_bytes = phase5_path.read_bytes()
    p4 = json.loads(p4_bytes.decode("utf-8"))
    p5 = json.loads(p5_bytes.decode("utf-8"))
    cases: list[dict[str, Any]] = []

    p4_target = targets["phase4-bounded-interpreter"]
    p4_seed = _sha256(p4_bytes)
    for index, fixture in enumerate(p4["cases"], start=1):
        expected = {
            "expected_completion_status": fixture["expected_completion_status"],
            "expected_expression_count": fixture["expected_expression_count"],
            "gold_class": "OTHER",
            "expected_construction": None,
            "expected_roles": {},
            "expected_role_spans": {},
        }
        cases.append(_case(
            case_id=f"OW-DIAG-P4-{index:06d}",
            source_id=p4["benchmark_id"],
            source_digest=p4_seed,
            source_version=p4["version"],
            text=fixture["text"],
            language=fixture["language"],
            target=p4_target,
            expected=expected,
            taxonomy=["phase4", "bounded_interpreter", fixture["id"]],
            master_seed=p4_seed,
            created_at=timestamp,
        ))

    p5_target = targets["phase5-bounded-interpreter"]
    p5_seed = _sha256(p5_bytes)
    for index, fixture in enumerate(p5["cases"], start=1):
        expected = {
            "expected_completion_status": fixture.get("expected_completion_status"),
            "expected_expression_count": None,
            "gold_class": fixture["gold_class"],
            "expected_construction": fixture.get("expected_construction"),
            "expected_roles": fixture.get("expected_roles", {}),
            "expected_role_spans": fixture.get("expected_role_spans", {}),
        }
        cases.append(_case(
            case_id=f"OW-DIAG-P5-{index:06d}",
            source_id=p5["benchmark_id"],
            source_digest=p5_seed,
            source_version=p5["version"],
            text=fixture["text"],
            language=fixture["language"],
            target=p5_target,
            expected=expected,
            taxonomy=["phase5", "simple_transitive", fixture["gold_class"], fixture["id"]],
            master_seed=p5_seed,
            created_at=timestamp,
        ))

    manifest = {
        "manifest_version": "1.0.0",
        "importer_version": "1.0.0",
        "population": "controlled_diagnostic",
        "created_at": timestamp,
        "case_count": len(cases),
        "by_target": {
            "phase4-bounded-interpreter": sum(
                case["target"]["component_id"] == "phase4-bounded-interpreter" for case in cases
            ),
            "phase5-bounded-interpreter": sum(
                case["target"]["component_id"] == "phase5-bounded-interpreter" for case in cases
            ),
        },
        "sources": [
            {
                "benchmark_id": p4["benchmark_id"],
                "version": p4["version"],
                "path": str(phase4_path.relative_to(ROOT)),
                "sha256": p4_seed,
                "case_count": len(p4["cases"]),
                "annotation_scope": "bounded USG-INTERPRET/0.1.0 completion status and expression count",
            },
            {
                "benchmark_id": p5["benchmark_id"],
                "version": p5["version"],
                "path": str(phase5_path.relative_to(ROOT)),
                "sha256": p5_seed,
                "case_count": len(p5["cases"]),
                "annotation_scope": p5["scope"],
            },
        ],
        "independence_note": (
            "Gold expectations are repository-authored, versioned diagnostic annotations stored separately "
            "from execution output. They are independent of the runtime execution path but are not an "
            "external third-party human-annotation study."
        ),
    }
    return cases, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import repository-owned Phase 4/5 gold fixtures as OW diagnostic scenarios."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--phase4-corpus", type=Path, default=PHASE4_CORPUS)
    parser.add_argument("--phase5-corpus", type=Path, default=PHASE5_CORPUS)
    parser.add_argument("--created-at")
    args = parser.parse_args(argv)
    if args.output.exists() or args.manifest.exists():
        parser.error("refusing to overwrite existing diagnostic case or manifest output")
    try:
        cases, manifest = import_diagnostic_scenarios(
            phase4_path=args.phase4_corpus,
            phase5_path=args.phase5_corpus,
            created_at=args.created_at,
        )
        from .validate_protocol import validate_instance
        for case in cases:
            errors = validate_instance("scenario", case)
            if errors:
                raise ValueError(f"{case['case_id']}: " + "; ".join(errors))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            for case in cases:
                stream.write(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n")
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        with args.manifest.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f"Imported {len(cases)} controlled diagnostic cases.")
    print(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
