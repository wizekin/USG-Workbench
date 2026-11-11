"""Development-only self-consistency evaluation for Step 6.6."""
from pathlib import Path
import json
from collections import defaultdict
from tools.phase6_benchmark_v0_4_1.validate import validate as load_gold
from tools.phase6_nominal_candidate_v0_4_1.validate import validate as validate_lexicon
from tools.phase6_nominal_candidate_v0_4_1.analyzer import predict_corpus
ROOT=Path(__file__).resolve().parents[2]
def evaluate(corpus,predictions):
 gold={x["id"]:x for x in corpus["cases"]}; pred={x["case_id"]:x for x in predictions["predictions"]}
 if set(gold)!=set(pred): raise ValueError("prediction coverage must exactly match corpus")
 inventory=[(l,x["construction_id"]) for l,items in corpus["construction_inventory"].items() for x in items]
 report={}
 for lang,con in inventory:
  cases=[c for c in corpus["cases"] if c["language"]==lang and c["target_construction"]==con]
  pos=[c for c in cases if c["gold_class"]=="POSITIVE"]; neg=[c for c in cases if c["gold_class"]=="NEGATIVE"]; amb=[c for c in cases if c["gold_class"]=="AMBIGUOUS"]
  tp=fp=roles=spans=markers=predicates=relations=0; neg_abs=amb_abs=0
  for c in cases:
   p=pred[c["id"]]; selected=p.get("construction_id")==con and p.get("status")=="CANDIDATE"
   if c["gold_class"]=="POSITIVE":
    tp+=int(selected)
    roles+=int(selected and p.get("role_bindings")==c["expected_roles"])
    spans+=int(selected and p.get("role_spans")==c["expected_role_spans"])
    markers+=int(selected and p.get("grammatical_markers")==c["expected_grammatical_markers"])
    predicates+=int(selected and p.get("predicate_span")==c["expected_predicate_span"])
    relations+=int(selected and p.get("relation_type")==c["expected_relation_type"])
   elif c["gold_class"]=="NEGATIVE":
    fp+=int(p.get("construction_id") is not None); neg_abs+=int(p.get("construction_id") is None)
   else:
    fp+=int(p.get("construction_id") is not None); amb_abs+=int(p.get("construction_id") is None)
  precision=tp/(tp+fp) if tp+fp else 0.0
  report[f"{lang}/{con}"]={"positive":len(pos),"negative":len(neg),"ambiguous":len(amb),"precision":precision,"recall":tp/len(pos),"role_accuracy":roles/len(pos),"span_accuracy":spans/len(pos),"marker_accuracy":markers/len(pos),"predicate_accuracy":predicates/len(pos),"relation_accuracy":relations/len(pos),"negative_abstention":neg_abs/len(neg),"ambiguous_abstention":amb_abs/len(amb),"false_unique":fp}
 gates={k:(v["precision"]>=.95 and v["recall"]>=.95 and v["role_accuracy"]>=.95 and v["span_accuracy"]>=.95 and v["marker_accuracy"]>=.95 and v["predicate_accuracy"]>=.95 and v["relation_accuracy"]>=.95 and v["negative_abstention"]==1.0 and v["ambiguous_abstention"]==1.0 and v["false_unique"]==0) for k,v in report.items()}
 return {"evaluation_scope":"IN_SAMPLE_CLOSED_LEXICON_SELF_CONSISTENCY_NOT_GENERALIZATION","case_count":len(corpus["cases"]),"by_construction":report,"development_gate_passed":bool(gates) and all(gates.values()),"benchmark_enabled_constructions":[],"runtime_capability_state":"CANDIDATE_ONLY"}
def main():
 corpus=load_gold(); validate_lexicon(); predictions=predict_corpus(corpus); report=evaluate(corpus,predictions)
 out={"evaluation":report,"predictions":predictions}
 path=ROOT/"artifacts/phase6-step-6.6-development-report.json"; path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if not report["development_gate_passed"]: raise SystemExit("candidate development self-consistency gate failed")
if __name__=="__main__": main()
