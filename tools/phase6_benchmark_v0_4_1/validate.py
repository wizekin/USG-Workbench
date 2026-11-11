"""Validate the Phase 6 v0.4.1 candidate gold corpus."""
from pathlib import Path
import json
from collections import Counter
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/"benchmarks/phase6-interpretation-v0.4.1"
ROLE_KEYS={"ADJECTIVE_MODIFIER":{"HEAD","MODIFIER"},"GENITIVE_RELATION":{"GENITIVE_HEAD","GENITIVE_DEPENDENT"},"NOUN_COMPOUND":{"HEAD","MODIFIER"},"PREPOSITIONAL_MODIFIER":{"HEAD","LOCATION"},"TEMPORAL_MODIFIER":{"EVENT","TIME"}}
def sl(text,span):
 if span["start"]<0 or span["end"]<=span["start"]: raise ValueError("invalid span bounds")
 return "".join(list(text)[span["start"]:span["end"]])
def validate():
 s=json.loads((BASE/"corpus.schema.json").read_text(encoding="utf-8")); d=json.loads((BASE/"corpus.json").read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(s).iter_errors(d))
 if errors: raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors[:12]))
 inv={}
 for lang,items in d["construction_inventory"].items():
  for x in items:
   key=(lang,x["construction_id"])
   if key in inv or x["enabled"] is not False or x["family"] not in ROLE_KEYS: raise ValueError("invalid candidate construction inventory: "+str(key))
   inv[key]=x["family"]
 ids=set(); counts=Counter()
 for c in d["cases"]:
  if c["id"] in ids: raise ValueError("duplicate fixture id: "+c["id"])
  ids.add(c["id"]); key=(c["language"],c["target_construction"])
  if key not in inv: raise ValueError("unknown construction: "+c["id"])
  family=inv[key]; counts[(key[0],key[1],c["gold_class"])]+=1
  roles=c["expected_roles"]; spans=c["expected_role_spans"]
  if set(roles)!=set(spans): raise ValueError("role/span key mismatch: "+c["id"])
  for role,span in spans.items():
   if sl(c["text"],span)!=span["surface"] or roles[role]!=span["surface"]: raise ValueError("role/source mismatch: "+c["id"]+"/"+role)
  evidence=list(c["expected_grammatical_markers"])
  if c["expected_predicate_span"] is not None: evidence.append(c["expected_predicate_span"])
  for span in evidence:
   if sl(c["text"],span)!=span["surface"]: raise ValueError("evidence span mismatch: "+c["id"])
  if c["gold_class"]=="POSITIVE":
   if c["gold_construction"]!=c["target_construction"] or set(roles)!=ROLE_KEYS[family] or c["expected_completion_status"]!="COMPLETE" or c["ambiguity_reason"] is not None: raise ValueError("invalid positive annotation: "+c["id"])
   if family=="TEMPORAL_MODIFIER" and c["expected_predicate_span"] is None: raise ValueError("temporal predicate evidence missing: "+c["id"])
   if family!="TEMPORAL_MODIFIER" and c["expected_predicate_span"] is not None: raise ValueError("unexpected predicate span: "+c["id"])
   if (family=="GENITIVE_RELATION")!=(c["expected_relation_type"]=="GENITIVE_UNSPECIFIED"): raise ValueError("genitive relation must remain semantically unspecified: "+c["id"])
  else:
   if c["gold_construction"] is not None or roles or spans or c["expected_completion_status"] is not None or c["expected_predicate_span"] is not None or c["expected_grammatical_markers"] or c["expected_relation_type"] is not None: raise ValueError("non-positive contains unique semantic graph: "+c["id"])
   if (c["gold_class"]=="AMBIGUOUS")!=(c["ambiguity_reason"] is not None): raise ValueError("ambiguity annotation mismatch: "+c["id"])
 req=d["minimums_per_language_and_construction"]
 for lang,con in inv:
  for label,n in (("POSITIVE",req["positive"]),("NEGATIVE",req["negative"]),("AMBIGUOUS",req["ambiguous"])):
   if counts[(lang,con,label)]!=n: raise ValueError(f"fixture count mismatch: {lang}/{con}/{label}")
 if len(ids)!=500: raise ValueError("expected 500 fixtures")
 return d
if __name__=="__main__": print(f"validated {len(validate()['cases'])} candidate fixtures with genitive semantics explicitly unspecified")
