"""Validate the candidate nominal lexicon against its source fixtures."""
from pathlib import Path
import json
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
RESOURCE=ROOT/"resources/lexical/phase6-v0.4.1/nominal-candidate.json"
SCHEMA=ROOT/"specifications/phase6-nominal-lexicon-0.4.1.schema.json"
CORPUS=ROOT/"benchmarks/phase6-interpretation-v0.4.1/corpus.json"
def validate():
 r=json.loads(RESOURCE.read_text(encoding="utf-8")); s=json.loads(SCHEMA.read_text(encoding="utf-8")); c=json.loads(CORPUS.read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(s).iter_errors(r))
 if errors: raise ValueError("; ".join(e.message for e in errors[:10]))
 cases={x["id"]:x for x in c["cases"]}; keys=set()
 for e in r["entries"]:
  key=(e["language"],e["form"],e["part_of_speech"],e["sense_id"])
  if key in keys: raise ValueError("duplicate lexical entry: "+str(key))
  keys.add(key)
  if e["language_profile"]!=c["language_profiles"][e["language"]] or e["status"]!="CANDIDATE": raise ValueError("invalid lexical language/status")
  for ev in e["evidence"]:
   if ev["fixture_id"] not in cases: raise ValueError("unknown lexical evidence fixture")
   source=cases[ev["fixture_id"]]["text"]
   if "".join(list(source)[ev["start"]:ev["end"]])!=ev["surface"] or ev["surface"]!=e["form"]: raise ValueError("lexical evidence span mismatch: "+ev["fixture_id"])
 if r["morphology_rules"]: raise ValueError("candidate lexicon must not imply productive morphology")
 return r
if __name__=="__main__":
 r=validate(); print(f"validated {len(r['entries'])} closed-profile candidate lexical entries")
