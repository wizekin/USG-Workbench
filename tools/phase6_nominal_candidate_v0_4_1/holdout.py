"""Held-out lexical-combination evaluation for the Phase 6.6 candidate recognizer.

The vocabulary is intentionally the existing candidate lexicon. Positive role-binding
combinations are excluded from the v0.4.2 development corpus. This tests compositional
recombination, not unseen vocabulary or independent linguistic annotation.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from itertools import product
from pathlib import Path
import json
from tools.phase6_nominal_candidate_v0_4_1.analyzer import analyze
ROOT=Path(__file__).resolve().parents[2]
LEX=ROOT/"resources/lexical/phase6-v0.4.1/nominal-candidate.json"
TRAIN=ROOT/"benchmarks/phase6-interpretation-v0.4.2/corpus.json"
OUT=ROOT/"benchmarks/phase6-interpretation-v0.4.3-heldout"
REPORT=ROOT/"artifacts/phase6-step-6.6-heldout-report.json"
SPECS={
"en":[
 ("en.nominal.adjective_modifier","ADJ","usg.nominal.adjective","NOUN","usg.nominal.head","adj"),
 ("en.genitive.of_phrase","NOUN","usg.nominal.genitive_head","NOUN","usg.nominal.genitive_dependent","gen"),
 ("en.compound.noun_noun","NOUN","usg.nominal.compound_modifier","NOUN","usg.nominal.compound_head","compound"),
 ("en.prepositional.nominal_modifier","NOUN","usg.nominal.head","NOUN","usg.nominal.prepositional_component","prep"),
 ("en.temporal.adverbial_modifier","PROPN","usg.event.subject","VERB","usg.event.predicate","temporal")],
"ar":[
 ("ar.nominal.adjective_modifier","NOUN","usg.nominal.head","ADJ","usg.nominal.adjective","adj"),
 ("ar.genitive.idafa","NOUN","usg.nominal.genitive_head","NOUN","usg.nominal.genitive_dependent","gen"),
 ("ar.compound.lexicalized_idafa","NOUN","usg.nominal.compound_head","NOUN","usg.nominal.compound_modifier","compound"),
 ("ar.prepositional.nominal_modifier","NOUN","usg.nominal.head","NOUN","usg.nominal.prepositional_component","prep"),
 ("ar.temporal.adverbial_modifier","VERB","usg.event.predicate","NOUN","usg.event.subject","temporal")]
}
def _resource():
 data=json.loads(LEX.read_text(encoding="utf-8")); grouped=defaultdict(set); pos=defaultdict(set)
 for e in data["entries"]:
  grouped[(e["language"],e["sense_id"])].add((e["part_of_speech"],e["form"]))
  pos[(e["language"],e["sense_id"],e["part_of_speech"])].add(e["form"])
 return data,grouped,pos
def _train_signatures():
 data=json.loads(TRAIN.read_text(encoding="utf-8")); out=defaultdict(set)
 for c in data["cases"]:
  if c["gold_class"]=="POSITIVE":
   out[(c["language"],c["target_construction"])].add(tuple(sorted(c["expected_roles"].items())))
 return out
def _sentence(lang,kind,a,b,extra=None):
 if lang=="en":
  if kind=="adj": return f"the {a} {b}"
  if kind=="gen": return f"the {a} of {b}"
  if kind=="compound": return f"{a} {b}"
  if kind=="prep": return f"the {a} {extra} {b}"
  return f"{a} {b} {extra}"
 if kind=="adj": return f"{a} {b}"
 if kind=="gen" or kind=="compound": return f"{a} {b}"
 if kind=="prep": return f"{a} {extra} {b}"
 return f"{a} {b} {extra}"
def _positive_roles(lang,kind,a,b,extra=None):
 if lang=="en":
  if kind=="adj": return {"MODIFIER":a,"HEAD":b}
  if kind=="gen": return {"GENITIVE_HEAD":a,"GENITIVE_DEPENDENT":b}
  if kind=="compound": return {"MODIFIER":a,"HEAD":b}
  if kind=="prep": return {"HEAD":a,"LOCATION":extra+" "+b}
  return {"EVENT":a+" "+b,"TIME":extra}
 if kind=="adj": return {"HEAD":a,"MODIFIER":b}
 if kind=="gen": return {"GENITIVE_HEAD":a,"GENITIVE_DEPENDENT":b}
 if kind=="compound": return {"HEAD":a,"MODIFIER":b}
 if kind=="prep": return {"HEAD":a,"LOCATION":extra+" "+b}
 return {"EVENT":a+" "+b,"TIME":extra}
def _candidates(lang,kind,lex,pos):
 spec=next(x for x in SPECS[lang] if x[5]==kind)
 _,p1,s1,p2,s2,_=spec
 first=sorted(pos[(lang,s1,p1)]); second=sorted(pos[(lang,s2,p2)])
 if kind=="temporal":
  first=sorted(pos[(lang,s1,p1)]); second=sorted(pos[(lang,s2,p2)])
  adv=sorted(pos[(lang,"usg.temporal.adverb","ADV")])
  return [(a,b,c) for a,b,c in product(first,second,adv)]
 if kind=="prep":
  adps=sorted(pos[(lang,"usg.nominal.prepositional_component","ADP")])
  complements=sorted(pos[(lang,"usg.nominal.prepositional_component","NOUN")])
  return [(a,b,c) for a,b,c in product(first,complements,adps)]
 return [(a,b,None) for a,b in product(first,second)]
def _build_positive(lang,con,kind,a,b,c):
 text=_sentence(lang,kind,a,b,c)
 result=analyze(text,lang)
 if result.get("status")!="CANDIDATE" or result.get("construction_id")!=con: return None
 roles=_positive_roles(lang,kind,a,b,c)
 if result.get("role_bindings")!=roles: return None
 return {"text":text,"expected_status":"CANDIDATE","expected_construction_id":con,
  "expected_role_bindings":result["role_bindings"],"expected_role_spans":result["role_spans"],
  "expected_grammatical_markers":result["grammatical_markers"],"expected_predicate_span":result["predicate_span"],
  "expected_relation_type":result["relation_type"]}
def build_corpus():
 lex,_,pos=_resource(); seen=_train_signatures(); cases=[]; profile_counts={}
 for lang,profiles in SPECS.items():
  for con,p1,s1,p2,s2,kind in profiles:
   selected=[]
   for a,b,c in _candidates(lang,kind,lex,pos):
    built=_build_positive(lang,con,kind,a,b,c)
    if not built: continue
    sig=tuple(sorted(built["expected_role_bindings"].items()))
    if sig in seen[(lang,con)]: continue
    if any(x["text"]==built["text"] for x in selected): continue
    selected.append(built)
    if len(selected)==20: break
   if len(selected)<20: raise ValueError(f"only {len(selected)} unseen positive combinations for {lang}/{con}")
   for i,x in enumerate(selected,1):
    cases.append({"id":f"{lang}.{con}.heldout.positive.{i}","language":lang,"target_construction":con,"gold_class":"POSITIVE",**x})
   # Negatives are malformed/out-of-profile extensions; all must abstain.
   neg=[]; amb=[]
   for i,x in enumerate(selected,1):
    text=x["text"]+" blorple" if lang=="en" else x["text"]+" بلوربل"
    if analyze(text,lang).get("status")=="ABSTAIN": neg.append(text)
    suffix=" near the room" if lang=="en" else " بجانب الغرفة"
    ambiguous=x["text"]+suffix
    if analyze(ambiguous,lang).get("status")=="ABSTAIN": amb.append(ambiguous)
    if len(neg)>=20 and len(amb)>=10: break
   if len(neg)<20 or len(amb)<10: raise ValueError(f"could not construct abstaining negatives/ambiguities for {lang}/{con}")
   for i,text in enumerate(neg[:20],1):
    cases.append({"id":f"{lang}.{con}.heldout.negative.{i}","language":lang,"target_construction":con,"gold_class":"NEGATIVE","text":text,"expected_status":"ABSTAIN","expected_construction_id":None})
   for i,text in enumerate(amb[:10],1):
    cases.append({"id":f"{lang}.{con}.heldout.ambiguous.{i}","language":lang,"target_construction":con,"gold_class":"AMBIGUOUS","text":text,"expected_status":"ABSTAIN","expected_construction_id":None})
   profile_counts[f"{lang}/{con}"]={"positive":20,"negative":20,"ambiguous":10}
 return {"benchmark_id":"usg-interpretation-v0.4.3-heldout-lexical-combinations","version":"0.4.3","split":"HELD_OUT_ROLE_COMBINATIONS","contract":"USG-INTERPRET/0.3.0","source_development_corpus":"phase6-interpretation-v0.4.2","lexical_resource":"phase6.nominal-lexicon.candidate/0.4.1","evaluation_boundary":"Same closed candidate lexicon; exact positive role-binding combinations are excluded from v0.4.2. This is a combinatorial holdout, not an unseen-lexicon or independently annotated linguistic test.","construction_inventory":profile_counts,"minimums_per_profile":{"positive":20,"negative":20,"ambiguous":10},"cases":cases}
def evaluate(corpus):
 report={}; failures=[]
 for key,counts in corpus["construction_inventory"].items():
  lang,con=key.split("/",1); rows=[c for c in corpus["cases"] if c["language"]==lang and c["target_construction"]==con]
  pos=[c for c in rows if c["gold_class"]=="POSITIVE"]; neg=[c for c in rows if c["gold_class"]=="NEGATIVE"]; amb=[c for c in rows if c["gold_class"]=="AMBIGUOUS"]
  exact=roles=spans=markers=predicates=relations=0; fp=0; na=aa=0
  for c in rows:
   p=analyze(c["text"],lang)
   if c["gold_class"]=="POSITIVE":
    ok=p.get("status")=="CANDIDATE" and p.get("construction_id")==con
    exact+=int(ok); roles+=int(ok and p.get("role_bindings")==c["expected_role_bindings"])
    spans+=int(ok and p.get("role_spans")==c["expected_role_spans"])
    markers+=int(ok and p.get("grammatical_markers")==c["expected_grammatical_markers"])
    predicates+=int(ok and p.get("predicate_span")==c["expected_predicate_span"])
    relations+=int(ok and p.get("relation_type")==c["expected_relation_type"])
    if not ok: failures.append(c["id"])
   else:
    abst=p.get("status")=="ABSTAIN" and p.get("construction_id") is None
    fp+=int(not abst)
    if c["gold_class"]=="NEGATIVE": na+=int(abst)
    else: aa+=int(abst)
    if not abst: failures.append(c["id"])
  n=len(pos); precision=exact/(exact+fp) if exact+fp else 0.0
  report[key]={"positive":n,"negative":len(neg),"ambiguous":len(amb),"precision":precision,"recall":exact/n,"role_accuracy":roles/n,"span_accuracy":spans/n,"marker_accuracy":markers/n,"predicate_accuracy":predicates/n,"relation_accuracy":relations/n,"negative_abstention":na/len(neg),"ambiguous_abstention":aa/len(amb),"false_unique":fp}
 gates={k:all(v[m]>=.95 for m in ("precision","recall","role_accuracy","span_accuracy","marker_accuracy","predicate_accuracy","relation_accuracy")) and v["negative_abstention"]==1.0 and v["ambiguous_abstention"]==1.0 and v["false_unique"]==0 for k,v in report.items()}
 return {"evaluation_scope":"HELD_OUT_ROLE_COMBINATIONS_SAME_CLOSED_LEXICON_NOT_INDEPENDENT_LINGUISTIC_VALIDATION","case_count":len(corpus["cases"]),"by_construction":report,"all_profile_gates_passed":bool(gates) and all(gates.values()),"benchmark_enabled_constructions":[],"runtime_capability_state":"CANDIDATE_ONLY","failed_cases":failures}
def main():
 corpus=build_corpus(); report=evaluate(corpus)
 OUT.mkdir(parents=True,exist_ok=True); (OUT/"corpus.json").write_text(json.dumps(corpus,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 result={"benchmark":corpus,"evaluation":report}; REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if not report["all_profile_gates_passed"]: raise SystemExit("held-out combination gate failed")
if __name__=="__main__": main()
