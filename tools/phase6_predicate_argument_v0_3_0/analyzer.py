"""Bounded Phase 6 predicate/argument interpreter for eight benchmark constructions."""
from __future__ import annotations
from pathlib import Path
import json,unicodedata
ROOT=Path(__file__).resolve().parents[2]
LEXICON=ROOT/"resources/lexical/phase6-v0.3.0/en-ar-candidate.json"
RULES=ROOT/"resources/constructions/phase6-v0.3.0/predicate-argument-rules.json"
FRAME_BY_FAMILY={"intransitive":"usg.frame.event.intransitive","ditransitive":"usg.frame.transfer.ditransitive","copular":"usg.frame.predication.copular","prepositional":"usg.frame.relation.location"}
def _tokens(text):
 out=[]; start=None
 for i,ch in enumerate(text):
  category=unicodedata.category(ch)
  is_letter=category.startswith("L")
  is_mark=category.startswith("M")
  if is_letter or (is_mark and start is not None):
   if start is None: start=i
  elif start is not None:
   out.append({"surface":text[start:i],"start":start,"end":i}); start=None
 if start is not None: out.append({"surface":text[start:],"start":start,"end":len(text)})
 return out
def _index():
 data=json.loads(LEXICON.read_text(encoding="utf-8")); out={}
 for e in data["entries"]: out.setdefault((e["language"],e["form"].casefold() if e["language"]=="en" else e["form"]),[]).append(e)
 return out
def _entry(index,lang,tok):
 return index.get((lang,tok["surface"].casefold() if lang=="en" else tok["surface"]),[])
def _has_sense(index,lang,tok,sense):
 return any(e["sense_id"]==sense for e in _entry(index,lang,tok))
def _pos(index,lang,tok,allowed):
 return any(e["part_of_speech"] in allowed for e in _entry(index,lang,tok))
def _span(text,tok):
 return {"start":tok["start"],"end":tok["end"],"surface":text[tok["start"]:tok["end"]]}
def _phrase_span(text,tokens,start,end):
 return {"start":tokens[start]["start"],"end":tokens[end]["end"],"surface":text[tokens[start]["start"]:tokens[end]["end"]]}
def analyze(text,language):
 if language not in {"en","ar"} or not isinstance(text,str) or not text.strip(): raise ValueError("language and non-empty source text are required")
 ts=_tokens(text); ix=_index(); found=[]
 def add(construction,rule,frame,roles,predicate,markers=()):
  bindings={}; spans={}
  for role,(a,b) in roles.items():
   bindings[role]=text[ts[a]["start"]:ts[b]["end"]]
   spans[role]=_phrase_span(text,ts,a,b)
  found.append({"construction_id":construction,"rule_id":rule,"frame_id":frame,"role_bindings":bindings,"role_spans":spans,"predicate_span":_span(text,ts[predicate]),"grammatical_markers":[_span(text,ts[i]) for i in markers]})
 if language=="en":
  if len(ts)==2 and _pos(ix,language,ts[0],{"PROPN","NOUN"}) and _has_sense(ix,language,ts[1],"usg.sense.event.intransitive"):
   add("en.intransitive.basic","en.intransitive.basic.v1",FRAME_BY_FAMILY["intransitive"],{"AGENT":(0,0)},1)
  if len(ts)==5 and _pos(ix,language,ts[0],{"PROPN","NOUN"}) and _has_sense(ix,language,ts[1],"usg.sense.transfer") and _pos(ix,language,ts[2],{"PROPN","NOUN"}) and _pos(ix,language,ts[3],{"DET"}) and _pos(ix,language,ts[4],{"NOUN"}):
   add("en.ditransitive.basic","en.ditransitive.basic.v1",FRAME_BY_FAMILY["ditransitive"],{"AGENT":(0,0),"RECIPIENT":(2,2),"THEME":(3,4)},1)
  if len(ts)==3 and _pos(ix,language,ts[0],{"PROPN","NOUN"}) and _has_sense(ix,language,ts[1],"usg.sense.copula") and _pos(ix,language,ts[2],{"ADJ"}):
   add("en.copular.predicative","en.copular.predicative.v1",FRAME_BY_FAMILY["copular"],{"ENTITY":(0,0),"ATTRIBUTE":(2,2)},2,(1,))
  if len(ts) in {4,5} and _pos(ix,language,ts[0],{"PROPN","NOUN"}) and _has_sense(ix,language,ts[1],"usg.sense.spatial.location") and _pos(ix,language,ts[2],{"ADP"}) and all(_pos(ix,language,t,{"DET","NOUN","PROPN"}) for t in ts[3:]):
   add("en.prepositional.location","en.prepositional.location.v1",FRAME_BY_FAMILY["prepositional"],{"ENTITY":(0,0),"LOCATION":(2,len(ts)-1)},1)
 else:
  if len(ts)==2 and _has_sense(ix,language,ts[0],"usg.sense.event.intransitive") and _pos(ix,language,ts[1],{"NOUN","PROPN"}):
   add("ar.intransitive.basic","ar.intransitive.basic.v1",FRAME_BY_FAMILY["intransitive"],{"AGENT":(1,1)},0)
  if len(ts)==4 and _has_sense(ix,language,ts[0],"usg.sense.transfer") and all(_pos(ix,language,t,{"NOUN","PROPN"}) for t in ts[1:]):
   add("ar.ditransitive.basic","ar.ditransitive.basic.v1",FRAME_BY_FAMILY["ditransitive"],{"AGENT":(1,1),"RECIPIENT":(2,2),"THEME":(3,3)},0)
  if len(ts)==2 and _pos(ix,language,ts[0],{"NOUN","PROPN"}) and _pos(ix,language,ts[1],{"ADJ"}):
   add("ar.copular.predicative","ar.copular.predicative.v1",FRAME_BY_FAMILY["copular"],{"ENTITY":(0,0),"ATTRIBUTE":(1,1)},1)
  if len(ts)==4 and _has_sense(ix,language,ts[0],"usg.sense.spatial.location") and _pos(ix,language,ts[1],{"NOUN","PROPN"}) and _pos(ix,language,ts[2],{"ADP"}) and _pos(ix,language,ts[3],{"NOUN","PROPN"}):
   add("ar.prepositional.location","ar.prepositional.location.v1",FRAME_BY_FAMILY["prepositional"],{"ENTITY":(1,1),"LOCATION":(2,3)},0)
 if len(found)!=1: return {"status":"ABSTAIN" if not found else "AMBIGUOUS","construction_id":None,"alternatives":found}
 item=found[0]
 return {"status":"COMPLETE","construction_id":item["construction_id"],"frame_id":item["frame_id"],"frame_version":"0.3.0","role_bindings":item["role_bindings"],"role_spans":item["role_spans"],"predicate_span":item["predicate_span"],"grammatical_markers":item["grammatical_markers"],"derivation":{"rule_id":item["rule_id"],"lexical_resource":"phase6.lexicon.bilingual.candidate/0.3.0","frame_registry":"USG-FRAME-REGISTRY/0.3.0"}}
def predict_corpus(corpus):
 rows=[]
 for case in corpus["cases"]:
  result=analyze(case["text"],case["language"])
  rows.append({"case_id":case["id"],**result})
 return {"predictions":rows}
