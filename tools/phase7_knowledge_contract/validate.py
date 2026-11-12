"""Structural and cross-reference validation for USG-KNOWLEDGE/0.1.0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "specifications" / "usg-knowledge-0.1.0.schema.json"


class KnowledgeBundleError(ValueError):
    """Raised when a knowledge bundle violates structural or referential rules."""


def validate_bundle(bundle: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"schema: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
              for e in validator.iter_errors(bundle)]
    if errors:
        return sorted(errors)

    records = bundle["records"]
    sources = bundle["sources"]
    evidence = bundle["evidence"]
    contexts = bundle["contexts"]
    mappings = bundle["mappings"]
    relations = bundle["relations"]

    def unique_ids(items: list[dict[str, Any]], label: str) -> set[str]:
        ids = [item["id"] for item in items]
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
        if duplicates:
            errors.append(f"{label}: duplicate IDs: {', '.join(duplicates)}")
        return set(ids)

    record_ids = unique_ids(records, "records")
    source_ids = unique_ids(sources, "sources")
    evidence_ids = unique_ids(evidence, "evidence")
    context_ids = unique_ids(contexts, "contexts")
    unique_ids(mappings, "mappings")
    unique_ids(relations, "relations")

    for source in sources:
        if source["rights_status"] in {"RESTRICTED", "UNKNOWN", "PROHIBITED"} and source["redistribution"] == "ALLOWED":
            errors.append(f"source {source['id']}: redistribution cannot be ALLOWED when rights are {source['rights_status']}")
    for item in evidence:
        if item["source_id"] not in source_ids:
            errors.append(f"evidence {item['id']}: unknown source_id {item['source_id']}")
    for record in records:
        for field, known in (("source_ids", source_ids), ("evidence_ids", evidence_ids), ("context_ids", context_ids)):
            for ref in record.get(field, []):
                if ref not in known:
                    errors.append(f"record {record['id']}: unknown {field} reference {ref}")
        if record["kind"] == "LEXICAL_SENSE":
            lemma_id = record["payload"].get("lemma_record_id")
            lemma = next((x for x in records if x["id"] == lemma_id), None)
            if lemma is None or lemma["kind"] != "LEMMA":
                errors.append(f"record {record['id']}: lemma_record_id must reference a LEMMA record")
    for mapping in mappings:
        if mapping["source_record_id"] not in record_ids or mapping["target_record_id"] not in record_ids:
            errors.append(f"mapping {mapping['id']}: source and target must reference existing records")
        if mapping["source_record_id"] == mapping["target_record_id"]:
            errors.append(f"mapping {mapping['id']}: self-mapping is not allowed")
        for ref in mapping["evidence_ids"]:
            if ref not in evidence_ids:
                errors.append(f"mapping {mapping['id']}: unknown evidence reference {ref}")
        for ref in mapping["context_ids"]:
            if ref not in context_ids:
                errors.append(f"mapping {mapping['id']}: unknown context reference {ref}")
    for relation in relations:
        if relation["subject_record_id"] not in record_ids or relation["object_record_id"] not in record_ids:
            errors.append(f"relation {relation['id']}: subject and object must reference existing records")
        if relation["subject_record_id"] == relation["object_record_id"]:
            errors.append(f"relation {relation['id']}: self-relation is not allowed by the base profile")
        for ref in relation["evidence_ids"]:
            if ref not in evidence_ids:
                errors.append(f"relation {relation['id']}: unknown evidence reference {ref}")
        for ref in relation["context_ids"]:
            if ref not in context_ids:
                errors.append(f"relation {relation['id']}: unknown context reference {ref}")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", nargs="?", type=Path, default=ROOT / "examples" / "phase7-knowledge-bundle-0.1.0.json")
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    errors = validate_bundle(bundle)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"VALID: {args.bundle} conforms to USG-KNOWLEDGE/0.1.0 structural and reference checks")
    print("NOTE: validity does not establish truth, rights eligibility, or semantic acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
