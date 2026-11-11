"""Evaluator for corrected Phase 6 gold annotations v0.3.1."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/"benchmarks/phase6-interpretation-v0.3.1/corpus.json"
SCHEMA=ROOT/"benchmarks/phase6-interpretation-v0.3.1/corpus.schema.json"
def load_corpus(path=CORPUS):
 corpus=json.loads(Path(path).read_text(encoding="utf-8"))
 schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
 errors=list(Draft202012Validator(schema).iter_errors(corpus))
 if errors: raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
 ids=set(); inventory={(l,x["construction_id"]) for l,items in corpus["construction_inventory"].items() for x in items}; counts=defaultdict(Counter)
 for case in corpus["cases"]:
  if case["id"] in ids: raise ValueError("duplicate fixture id: "+case["id"])
  ids.add(case["id"]); key=(case["language"],case["target_construction"])
  if key not in inventory: raise ValueError("unknown construction: "+str(key))
  counts[key][case["gold_class"]]+=1
  spans=list(case["expected_role_spans"].values())
  if case["expected_predicate_span"] is not None: spans.append(case["expected_predicate_span"])
  spans.extend(case["expected_grammatical_markers"])
  for span in spans:
   if span["end"]>len(case["text"]) or case["text"][span["start"]:span["end"]]!=span["surface"]:
    raise ValueError("invalid exact span: "+case["id"])
  if case["expected_roles"]!={k:v["surface"] for k,v in case["expected_role_spans"].items()}:
   raise ValueError("participant role/span mismatch: "+case["id"])
  if case["gold_class"]=="POSITIVE":
   if case["gold_construction"]!=case["target_construction"] or not case["expected_roles"]:
    raise ValueError("positive case lacks participant role graph: "+case["id"])
   if case["expected_completion_status"]!="COMPLETE" or case["ambiguity_reason"] is not None:
    raise ValueError("invalid positive completion/ambiguity status: "+case["id"])
   if case["expected_predicate_span"] is None and not case["expected_grammatical_markers"]:
    raise ValueError("positive case lacks predicate/marker evidence: "+case["id"])
  else:
   if case["gold_construction"] is not None or case["expected_roles"] or case["expected_role_spans"] or case["expected_predicate_span"] is not None or case["expected_grammatical_markers"]:
    raise ValueError("non-positive case must not contain a unique graph: "+case["id"])
   if case["expected_completion_status"] is not None: raise ValueError("negative target class must not force pipeline status")
   if (case["gold_class"]=="AMBIGUOUS")!=(case["ambiguity_reason"] is not None): raise ValueError("ambiguity reason mismatch")
 required=corpus["minimums_per_language_and_construction"]
 for key in sorted(inventory):
  for label,minimum in (("POSITIVE",required["positive"]),("NEGATIVE",required["negative"]),("AMBIGUOUS",required["ambiguous"])):
   if counts[key][label]<minimum: raise ValueError(f"insufficient denominator for {key}/{label}")
 return corpus
def evaluate(corpus,predictions):
 gold={x["id"]:x for x in corpus["cases"]}; rows=predictions.get("predictions")
 if not isinstance(rows,list): raise ValueError("predictions must contain predictions array")
 pred={}
 for row in rows:
  cid=row.get("case_id") if isinstance(row,dict) else None
  if cid not in gold or cid in pred: raise ValueError("unknown or duplicate prediction case_id: "+str(cid))
  pred[cid]=row
 report={}; inventory=[(l,x["construction_id"]) for l,cs in corpus["construction_inventory"].items() for x in cs]
 for lang,construction in sorted(inventory):
  cases=[x for x in corpus["cases"] if x["language"]==lang and x["target_construction"]==construction]
  pos=[x for x in cases if x["gold_class"]=="POSITIVE"]; neg=[x for x in cases if x["gold_class"]=="NEGATIVE"]; amb=[x for x in cases if x["gold_class"]=="AMBIGUOUS"]
  if not pos or not neg or not amb: raise ValueError("empty metric denominator: "+lang+"/"+construction)
  tp=fp=fn=roles=spans=pred_spans=marker_spans=0; neg_abs=amb_abs=0
  for case in cases:
   p=pred.get(case["id"],{}); selected=p.get("construction_id")==construction
   if case["gold_class"]=="POSITIVE":
    tp+=int(selected); fn+=int(not selected)
    roles+=int(selected and p.get("role_bindings",{})==case["expected_roles"])
    predicted=p.get("role_spans",{}); valid=predicted==case["expected_role_spans"]
    spans+=int(selected and valid)
    pred_spans+=int(selected and p.get("predicate_span")==case["expected_predicate_span"])
    marker_spans+=int(selected and p.get("grammatical_markers",[])==case["expected_grammatical_markers"])
   elif case["gold_class"]=="NEGATIVE": fp+=int(selected); neg_abs+=int(not selected)
   else: fp+=int(selected); amb_abs+=int(not selected)
  predicted_count=tp+fp
  report[f"{lang}/{construction}"]={"fixture_count":len(cases),"positive_denominator":len(pos),"negative_denominator":len(neg),"ambiguous_denominator":len(amb),"precision":tp/predicted_count if predicted_count else 0.0,"recall":tp/len(pos),"role_accuracy":roles/len(pos),"source_span_accuracy":spans/len(pos),"predicate_span_accuracy":pred_spans/len(pos),"grammatical_marker_accuracy":marker_spans/len(pos),"negative_abstention":neg_abs/len(neg),"ambiguous_abstention":amb_abs/len(amb),"false_unique_constructions":fp}
 return {"benchmark_id":corpus["benchmark_id"],"case_count":len(corpus["cases"]),"by_construction":report}
def quality_gate(report):
 gates={}
 for key,m in report["by_construction"].items():
  gates[key]=(m["precision"]>=.95 and m["recall"]>=.90 and m["role_accuracy"]>=.95 and m["source_span_accuracy"]>=.95 and m["predicate_span_accuracy"]>=.95 and m["grammatical_marker_accuracy"]>=.95 and m["negative_abstention"]==1.0 and m["ambiguous_abstention"]==1.0 and m["false_unique_constructions"]==0)
 return {"passed":bool(gates) and all(gates.values()),"by_construction":gates}
if __name__=="__main__":
 corpus=load_corpus()
 print(f"validated {len(corpus['cases'])} corrected fixtures across {len(corpus['construction_inventory']['en'])+len(corpus['construction_inventory']['ar'])} construction profiles")
