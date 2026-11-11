"""Validate candidate Phase 6 predicate/argument construction rules."""
from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=ROOT/"specifications/phase6-predicate-argument-rules-0.3.0.schema.json"
RULES=ROOT/"resources/constructions/phase6-v0.3.0/predicate-argument-rules.json"
FRAMES=ROOT/"resources/semantic-frames/v0.3.0/registry.json"
def validate_rules():
 schema=json.loads(SCHEMA.read_text(encoding="utf-8")); data=json.loads(RULES.read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(schema).iter_errors(data))
 if errors: raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
 frames=json.loads(FRAMES.read_text(encoding="utf-8")); frame_ids={f["frameId"] for f in frames["frames"]}
 ids=set(); constructions=set()
 for rule in data["rules"]:
  if rule["rule_id"] in ids: raise ValueError("duplicate rule id")
  ids.add(rule["rule_id"])
  if rule["frame_id"] not in frame_ids: raise ValueError("unknown frame reference")
  key=(rule["language"],rule["construction_id"])
  if key in constructions: raise ValueError("duplicate language/construction rule")
  constructions.add(key)
  if rule["status"]!="CANDIDATE": raise ValueError("rules must remain candidate-only")
 expected={(l,c) for l in ("en","ar") for c in (f"{l}.intransitive.basic",f"{l}.ditransitive.basic",f"{l}.copular.predicative",f"{l}.prepositional.location")}
 if constructions!=expected: raise ValueError("rule inventory does not match the eight benchmark construction profiles")
 return data
if __name__=="__main__":
 data=validate_rules(); print(f"validated {len(data['rules'])} candidate construction rules")
