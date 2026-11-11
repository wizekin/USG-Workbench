"""Validate v0.4.2 token-boundary-safe gold spans."""
from pathlib import Path
import json,re
from collections import Counter
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/"benchmarks/phase6-interpretation-v0.4.2"
ROLE_KEYS={"ADJECTIVE_MODIFIER":{"HEAD","MODIFIER"},"GENITIVE_RELATION":{"GENITIVE_HEAD","GENITIVE_DEPENDENT"},"NOUN_COMPOUND":{"HEAD","MODIFIER"},"PREPOSITIONAL_MODIFIER":{"HEAD","LOCATION"},"TEMPORAL_MODIFIER":{"EVENT","TIME"}}
def tokens(text): return [{"surface":m.group(), "start":m.start(), "end":m.end()} for m in re.finditer(r"[\\w]+",text,flags=re.UNICODE) if any(ch.isalpha() for ch in m.group())]
def sl(text,s): return "".join(list(text)[s["start"]:s["end"]])
def validate():
 s=json.loads((BASE/"corpus.schema.json").read_text(encoding="utf-8")); d=json.loads((BASE/"corpus.json").read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(s).iter_errors(d))
 if errors: raise ValueError("; ".join(e.message for e in errors[:10]))
 inv={(lang,x["construction_id"]):x["family"] for lang,items in d["construction_inventory"].items() for x in items}
 ids=set(); counts=Counter(); labels={}
 for c in d["cases"]:
  if c["id"] in ids: raise ValueError("duplicate fixture id")
  ids.add(c["id"]); key=(c["language"],c["target_construction"])
  if key not in inv: raise ValueError("unknown construction: "+c["id"])
  tk=(c["language"],c["target_construction"],c["text"])
  if tk in labels and labels[tk]!=c["gold_class"]: raise ValueError("conflicting labels for identical text: "+c["id"])
  labels[tk]=c["gold_class"]; family=inv[key]; counts[(key[0],key[1],c["gold_class"])]+=1
  ts=tokens(c["text"]); starts={t["start"] for t in ts}; ends={t["end"] for t in ts}
  for role,sp in c["expected_role_spans"].items():
   if sl(c["text"],sp)!=sp["surface"] or sp["start"] not in starts or sp["end"] not in ends: raise ValueError("role span mismatch or not token-aligned: "+c["id"]+"/"+role)
   if c["expected_roles"].get(role)!=sp["surface"]: raise ValueError("role binding mismatch: "+c["id"])
  for sp in c["expected_grammatical_markers"]+([c["expected_predicate_span"]] if c["expected_predicate_span"] else []):
   if sl(c["text"],sp)!=sp["surface"] or (sp["start"],sp["end"]) not in {(t["start"],t["end"]) for t in ts}: raise ValueError("marker/predicate is not an exact token span: "+c["id"])
  if c["gold_class"]=="POSITIVE":
   if c["gold_construction"]!=c["target_construction"] or set(c["expected_roles"])!=ROLE_KEYS[family] or c["expected_completion_status"]!="COMPLETE" or c["ambiguity_reason"] is not None: raise ValueError("invalid positive: "+c["id"])
   if (family=="GENITIVE_RELATION")!=(c["expected_relation_type"]=="GENITIVE_UNSPECIFIED"): raise ValueError("genitive relation must remain unspecified: "+c["id"])
   if family=="TEMPORAL_MODIFIER" and c["expected_predicate_span"] is None: raise ValueError("temporal predicate missing: "+c["id"])
  else:
   if c["gold_construction"] is not None or c["expected_roles"] or c["expected_role_spans"] or c["expected_completion_status"] is not None or c["expected_predicate_span"] is not None or c["expected_grammatical_markers"] or c["expected_relation_type"] is not None: raise ValueError("non-positive has unique gold graph: "+c["id"])
   if (c["gold_class"]=="AMBIGUOUS")!=(c["ambiguity_reason"] is not None): raise ValueError("ambiguity reason mismatch: "+c["id"])
 req=d["minimums_per_language_and_construction"]
 for lang,items in d["construction_inventory"].items():
  for x in items:
   for label,n in (("POSITIVE",req["positive"]),("NEGATIVE",req["negative"]),("AMBIGUOUS",req["ambiguous"])):
    if counts[(lang,x["construction_id"],label)]!=n: raise ValueError("fixture count mismatch")
 if len(ids)!=500: raise ValueError("expected 500 fixtures")
 return d
if __name__=="__main__": print(f"validated {len(validate()['cases'])} token-aligned fixtures")
