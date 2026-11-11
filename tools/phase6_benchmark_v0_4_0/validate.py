from pathlib import Path
import json
from collections import Counter
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/"benchmarks/phase6-interpretation-v0.4.0"
def validate():
 s=json.loads((BASE/"corpus.schema.json").read_text()); d=json.loads((BASE/"corpus.json").read_text()); errors=list(Draft202012Validator(s).iter_errors(d))
 if errors: raise ValueError("; ".join(e.message for e in errors[:10]))
 ids=set(); counts=Counter()
 for c in d["cases"]:
  if c["id"] in ids: raise ValueError("duplicate fixture id")
  ids.add(c["id"]); counts[(c["language"],c["target_construction"],c["gold_class"])]+=1
  for role,sp in c["expected_role_spans"].items():
   if "".join(list(c["text"])[sp["start"]:sp["end"]])!=sp["surface"]: raise ValueError(f"bad role span {c['id']}:{role}")
  for sp in ([c["expected_predicate_span"]] if c["expected_predicate_span"] else [])+c["expected_grammatical_markers"]:
   if "".join(list(c["text"])[sp["start"]:sp["end"]])!=sp["surface"]: raise ValueError(f"bad predicate/marker span {c['id']}")
 for lang,items in d["construction_inventory"].items():
  for item in items:
   for cls,n in (("POSITIVE",20),("NEGATIVE",20),("AMBIGUOUS",10)):
    if counts[(lang,item["construction_id"],cls)]!=n: raise ValueError(f"wrong fixture count {lang}/{item['construction_id']}/{cls}")
 if len(ids)!=500: raise ValueError(f"expected 500 fixtures, got {len(ids)}")
 return d
if __name__=='__main__': print(f'validated {len(validate()["cases"])} fixtures and Unicode spans')
