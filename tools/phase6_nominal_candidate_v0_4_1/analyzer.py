"""Closed-profile candidate recognizer for Phase 6 Step 6.6.
Scores are development self-consistency only because its lexical inventory is derived
from the same v0.4.1 positive fixtures. It is never benchmark-enabled by this module.
"""
from __future__ import annotations
from pathlib import Path
import json
import unicodedata

ROOT=Path(__file__).resolve().parents[2]
LEXICON=ROOT/"resources/lexical/phase6-v0.4.1/nominal-candidate.json"

def _tokens(text):
    out=[]; start=None
    for i,ch in enumerate(text):
        cat=unicodedata.category(ch)
        is_token=cat.startswith("L") or cat.startswith("M")
        if is_token:
            if start is None: start=i
        elif start is not None:
            out.append({"surface":text[start:i],"start":start,"end":i}); start=None
    if start is not None: out.append({"surface":text[start:],"start":start,"end":len(text)})
    return out

def _index():
    data=json.loads(LEXICON.read_text(encoding="utf-8")); idx={}
    for e in data["entries"]:
        form=e["form"].casefold() if e["language"]=="en" else e["form"]
        idx.setdefault((e["language"],form),[]).append(e)
    return idx

def _entries(idx,lang,tok):
    form=tok["surface"].casefold() if lang=="en" else tok["surface"]
    return idx.get((lang,form),[])

def _has(idx,lang,tok,pos,sense=None):
    return any(e["part_of_speech"]==pos and (sense is None or e["sense_id"]==sense) for e in _entries(idx,lang,tok))

def _span(text,tokens,start,end):
    a=tokens[start]["start"]; b=tokens[end]["end"]
    return {"start":a,"end":b,"surface":text[a:b]}

def _candidate(text,lang,construction,rule,roles,tokens,markers=(),predicate=None,relation_type=None):
    bindings={}; spans={}
    for role,(a,b) in roles.items():
        spans[role]=_span(text,tokens,a,b); bindings[role]=spans[role]["surface"]
    semantic_relation = relation_type or {
        "en.nominal.adjective_modifier": "ATTRIBUTE",
        "ar.nominal.adjective_modifier": "ATTRIBUTE",
        "en.compound.noun_noun": "LEXICALIZED_COMPOUND_COMPONENT",
        "ar.compound.lexicalized_idafa": "LEXICALIZED_COMPOUND_COMPONENT",
        "en.prepositional.nominal_modifier": "LOCATIVE_NOMINAL_MODIFIER",
        "ar.prepositional.nominal_modifier": "LOCATIVE_NOMINAL_MODIFIER",
        "en.temporal.adverbial_modifier": "EVENT_TIME",
        "ar.temporal.adverbial_modifier": "EVENT_TIME",
    }.get(construction)
    return {"status":"CANDIDATE","candidate_only":True,"construction_id":construction,
        "role_bindings":bindings,"role_spans":spans,
        "grammatical_markers":[_span(text,tokens,i,i) for i in markers],
        "predicate_span":_span(text,tokens,*predicate) if predicate else None,
        "relation_type":relation_type,
        "semantic_relation_candidate":semantic_relation,
        "derivation":{"rule_id":rule,"lexical_resource":"phase6.nominal-lexicon.candidate/0.4.1",
                      "evaluation_scope":"IN_SAMPLE_CLOSED_LEXICON"}}

def analyze(text,language):
    if language not in {"en","ar"} or not isinstance(text,str) or not text.strip():
        raise ValueError("language and non-empty source text are required")
    ts=_tokens(text); ix=_index(); n=len(ts); found=[]
    def pos(i,p,s=None): return 0<=i<n and _has(ix,language,ts[i],p,s)
    if language=="en":
        # DET? ADJ NOUN
        off=1 if n==3 and pos(0,"DET") else 0
        if n-off==2 and pos(off,"ADJ","usg.nominal.adjective") and pos(off+1,"NOUN","usg.nominal.head"):
            found.append(_candidate(text,language,"en.nominal.adjective_modifier","en.nominal.adjective-modifier.v1",
                {"MODIFIER":(off,off),"HEAD":(off+1,off+1)},ts))
        # DET? NOUN of DET? NOUN/PROPN; the genitive subtype is deliberately unspecified.
        start=1 if n in {4,5} and pos(0,"DET") else 0
        if n-start in {3,4} and pos(start,"NOUN","usg.nominal.genitive_head") and pos(start+1,"ADP","usg.grammar.adposition") and ts[start+1]["surface"].lower()=="of":
            dep=start+2+(1 if start+3<n and pos(start+2,"DET") else 0)
            if dep==n-1 and (pos(dep,"NOUN","usg.nominal.genitive_dependent") or pos(dep,"PROPN","usg.nominal.genitive_dependent")):
                found.append(_candidate(text,language,"en.genitive.of_phrase","en.genitive.of-phrase.v1",
                    {"GENITIVE_HEAD":(start,start),"GENITIVE_DEPENDENT":(start+2,dep)},ts,markers=(start+1,),relation_type="GENITIVE_UNSPECIFIED"))
        # NOUN NOUN; compound direction is modifier then head in English.
        if n==2 and pos(0,"NOUN","usg.nominal.compound_modifier") and pos(1,"NOUN","usg.nominal.compound_head"):
            found.append(_candidate(text,language,"en.compound.noun_noun","en.compound.noun-noun.v1",
                {"MODIFIER":(0,0),"HEAD":(1,1)},ts))
        # DET? NOUN ADP DET? NOUN
        start=1 if n in {4,5} and pos(0,"DET") else 0
        if n-start in {3,4} and pos(start,"NOUN","usg.nominal.head") and pos(start+1,"ADP","usg.nominal.prepositional_component"):
            loc=start+2+(1 if start+3<n and pos(start+2,"DET") else 0)
            if loc==n-1 and pos(loc,"NOUN","usg.nominal.prepositional_component"):
                found.append(_candidate(text,language,"en.prepositional.nominal_modifier","en.prepositional.nominal-modifier.v1",
                    {"HEAD":(start,start),"LOCATION":(start+1,n-1)},ts,markers=(start+1,)))
        # PROPN VERB ADV
        if n==3 and pos(0,"PROPN") and pos(1,"VERB","usg.event.predicate") and pos(2,"ADV","usg.temporal.adverb"):
            found.append(_candidate(text,language,"en.temporal.adverbial_modifier","en.temporal.adverbial-modifier.v1",
                {"EVENT":(0,1),"TIME":(2,2)},ts,predicate=(1,1)))
    else:
        # NOUN ADJ
        if n==2 and pos(0,"NOUN","usg.nominal.head") and pos(1,"ADJ","usg.nominal.adjective"):
            found.append(_candidate(text,language,"ar.nominal.adjective_modifier","ar.nominal.adjective-modifier.v1",
                {"HEAD":(0,0),"MODIFIER":(1,1)},ts))
        # NOUN NOUN can be genitive or registered lexicalized compound; keep both if both licensed.
        if n==2:
            if pos(0,"NOUN","usg.nominal.genitive_head") and pos(1,"NOUN","usg.nominal.genitive_dependent"):
                found.append(_candidate(text,language,"ar.genitive.idafa","ar.genitive.idafa.v1",
                    {"GENITIVE_HEAD":(0,0),"GENITIVE_DEPENDENT":(1,1)},ts,relation_type="GENITIVE_UNSPECIFIED"))
            if pos(0,"NOUN","usg.nominal.compound_head") and pos(1,"NOUN","usg.nominal.compound_modifier"):
                found.append(_candidate(text,language,"ar.compound.lexicalized_idafa","ar.compound.lexicalized-idafa.v1",
                    {"HEAD":(0,0),"MODIFIER":(1,1)},ts))
        # NOUN ADP NOUN
        if n==3 and pos(0,"NOUN","usg.nominal.head") and pos(1,"ADP","usg.nominal.prepositional_component") and pos(2,"NOUN","usg.nominal.prepositional_component"):
            found.append(_candidate(text,language,"ar.prepositional.nominal_modifier","ar.prepositional.nominal-modifier.v1",
                {"HEAD":(0,0),"LOCATION":(1,2)},ts,markers=(1,)))
        # VERB NOUN ADV
        if n==3 and pos(0,"VERB","usg.event.predicate") and pos(1,"NOUN","usg.event.subject") and pos(2,"ADV","usg.temporal.adverb"):
            found.append(_candidate(text,language,"ar.temporal.adverbial_modifier","ar.temporal.adverbial-modifier.v1",
                {"EVENT":(0,1),"TIME":(2,2)},ts,predicate=(0,0)))
    if len(found)==1: return found[0]
    if len(found)>1: return {"status":"AMBIGUOUS","candidate_only":True,"construction_id":None,"alternatives":found}
    return {"status":"ABSTAIN","candidate_only":True,"construction_id":None,"alternatives":[]}

def predict_corpus(corpus):
    return {"predictions":[{"case_id":c["id"],**analyze(c["text"],c["language"])} for c in corpus["cases"]]}
