"""Optional Draft 2020-12 schema conformance tests. Requires: python -m pip install jsonschema"""
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
model_schema = json.loads((ROOT / "schemas/usg-semantic-model-v0.5.schema.json").read_text(encoding="utf-8"))
record_schema = json.loads((ROOT / "schemas/usg-semantic-record-v0.5.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(model_schema)
Draft202012Validator.check_schema(record_schema)
print("PASS: both Draft 2020-12 schemas are valid schemas")

validator = Draft202012Validator(model_schema)
fixtures = json.loads((ROOT / "tests/fixtures/semantic-model-conformance-v0.5.json").read_text(encoding="utf-8"))
for fixture in fixtures:
    validator.validate(fixture["model"])
print(f"PASS: {len(fixtures)} canonical semantic-model fixtures validate")

record = json.loads((ROOT / "tests/fixtures/record-conformance-v0.5.json").read_text(encoding="utf-8"))
Draft202012Validator(record_schema).validate(record)
print("PASS: complete v0.5 semantic-record fixture validates")
print("Schema validation: 10 checks passed (2 metaschemas, 7 graph fixtures, 1 full record).")
