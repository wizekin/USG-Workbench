"""Validate the Step 6.6 nominal/modifier definition inventory."""
from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=ROOT/"specifications/phase6-nominal-modifier-rules-0.3.0.schema.json"
RESOURCE=ROOT/"resources/constructions/phase6-v0.3.0/nominal-modifier-rules.json"
def validate():
 schema=json.loads(SCHEMA.read_text(encoding="utf-8")); data=json.loads(RESOURCE.read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(schema).iter_errors(data))
 if errors: raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
 ids=set(); constructions=set()
 for rule in data["rules"]:
  if rule["rule_id"] in ids: raise ValueError("duplicate rule id")
  ids.add(rule["rule_id"])
  key=(rule["language"],rule["construction_id"])
  if key in constructions: raise ValueError("duplicate language/construction id")
  constructions.add(key)
  if rule["status"]!="CANDIDATE": raise ValueError("definition inventory must remain candidate-only")
 if len(constructions)!=10 or {x[0] for x in constructions}!={"en","ar"}: raise ValueError("expected five construction families per language")
 required={"ADJECTIVE_MODIFIER","POSSESSION","NOUN_COMPOUND","PREPOSITIONAL_MODIFIER","TEMPORAL_MODIFIER"}
 if {r["family"] for r in data["rules"]}!=required: raise ValueError("missing nominal/modifier family")
 return data
if __name__=="__main__":
 data=validate(); print(f"validated {len(data['rules'])} candidate nominal/modifier definitions")
