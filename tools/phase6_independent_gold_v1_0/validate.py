"""Fail-closed validator for the Phase 6 independent semantic-gold gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "specifications/phase6-independent-gold-manifest-1.0.schema.json"
EXPECTED = {
    ("en", "en.nominal.adjective_modifier"),
    ("en", "en.genitive.of_phrase"),
    ("en", "en.compound.noun_noun"),
    ("en", "en.prepositional.nominal_modifier"),
    ("en", "en.temporal.adverbial_modifier"),
    ("ar", "ar.nominal.adjective_modifier"),
    ("ar", "ar.genitive.idafa"),
    ("ar", "ar.compound.lexicalized_idafa"),
    ("ar", "ar.prepositional.nominal_modifier"),
    ("ar", "ar.temporal.adverbial_modifier"),
}


def validate_manifest(data: dict) -> dict:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        details = [
            "%s: %s" % ("/".join(map(str, error.absolute_path)) or "<root>", error.message)
            for error in errors[:20]
        ]
        raise ValueError("independent-gold manifest schema failed: " + "; ".join(details))

    observed = [(profile["language"], profile["construction_id"]) for profile in data["profiles"]]
    if len(observed) != len(set(observed)):
        raise ValueError("duplicate language/construction profile")
    if set(observed) != EXPECTED:
        missing = sorted(EXPECTED - set(observed))
        extra = sorted(set(observed) - EXPECTED)
        raise ValueError(f"profile inventory mismatch; missing={missing}; extra={extra}")

    for profile in data["profiles"]:
        annotators = profile["independent_annotator_ids"]
        if profile["adjudicator_id"] in annotators:
            raise ValueError(
                "adjudicator must be distinct from annotators: "
                f'{profile["language"]}/{profile["construction_id"]}'
            )

    if data["annotation"]["adjudication"]["method"] == "third_annotator":
        if not data["annotation"]["adjudication"]["separate_adjudicator"]:
            raise ValueError("third-annotator adjudication requires a separate adjudicator")

    return {
        "status": "INDEPENDENT_GOLD_MANIFEST_ACCEPTED",
        "profile_count": len(observed),
        "case_count": data["cases"]["case_count"],
        "public_redistribution_allowed": True,
        "independent_human_annotation": True,
        "model_generated_labels": False,
        "development_leakage_count": 0,
        "benchmark_enabled_constructions": [],
        "note": (
            "Manifest eligibility is necessary but not sufficient; the interpreter "
            "must still pass the frozen per-profile quality gates."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="Path to a manifest JSON file")
    args = parser.parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    print(json.dumps(validate_manifest(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
