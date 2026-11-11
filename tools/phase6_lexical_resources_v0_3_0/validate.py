"""Validation for the candidate Phase 6 bilingual lexical/morphology resource."""
from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=ROOT/"specifications/phase6-lexical-resource-0.3.0.schema.json"
RESOURCE=ROOT/"resources/lexical/phase6-v0.3.0/en-ar-candidate.json"
CORPUS=ROOT/"benchmarks/phase6-interpretation-v0.3.0/corpus.json"
FRAMES=ROOT/"resources/semantic-frames/v0.3.0/registry.json"
def validate_resource():
 schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
 data=json.loads(RESOURCE.read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(schema).iter_errors(data))
 if errors: raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
 corpus=json.loads(CORPUS.read_text(encoding="utf-8"))
 cases={c["id"]:c for c in corpus["cases"]}
 keys=set()
 for entry in data["entries"]:
  key=(entry["language"],entry["form"],entry["part_of_speech"])
  if key in keys: raise ValueError(f"duplicate lexical entry: {key}")
  keys.add(key)
  if entry["language_profile"]!=corpus["language_profiles"][entry["language"]]:
   raise ValueError(f"language profile mismatch: {key}")
  for ev in entry["evidence"]:
   case=cases.get(ev["fixture_id"])
   if case is None: raise ValueError(f"unknown evidence fixture: {ev['fixture_id']}")
   if case["language"]!=entry["language"]: raise ValueError("cross-language evidence")
   if case["text"][ev["start"]:ev["end"]]!=ev["surface"] or ev["surface"]!=entry["form"]:
    raise ValueError(f"invalid exact source span: {key}/{ev['fixture_id']}")
 for rule in data["morphology_rules"]:
  if rule["language_profile"]!=corpus["language_profiles"][rule["language"]]:
   raise ValueError(f"morphology language profile mismatch: {rule['rule_id']}")
  for fixture_id in rule["evidence_fixture_ids"]:
   if fixture_id not in cases or cases[fixture_id]["language"]!=rule["language"]:
    raise ValueError(f"invalid morphology evidence: {rule['rule_id']}/{fixture_id}")
  for form in rule["pattern"]["example_forms"]:
   if not any(e["form"]==form and e["language"]==rule["language"] for e in data["entries"]):
    raise ValueError(f"morphology example lacks lexical evidence: {form}")
 if data["status"]!="CANDIDATE" or any(e["status"]!="CANDIDATE" for e in data["entries"]) or any(r["status"]!="CANDIDATE" for r in data["morphology_rules"]):
  raise ValueError("lexical resource must remain candidate-only")
 frames=json.loads(FRAMES.read_text(encoding="utf-8"))
 expected_ref=data["resource_id"]+"/"+data["version"]
 for frame in frames["frames"]:
  for realization in frame["lexicalRealizations"]:
   if expected_ref not in realization["resourceRefs"]:
    raise ValueError("frame realization lacks Phase 6 lexical resource reference: "+frame["frameId"])
 return data
if __name__=="__main__":
 data=validate_resource()
 print(f"validated {len(data['entries'])} lexical entries and {len(data['morphology_rules'])} candidate morphology rules")
