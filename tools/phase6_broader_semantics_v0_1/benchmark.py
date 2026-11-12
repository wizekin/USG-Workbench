"""Automatically generated contract benchmark for Phase 6 graph composition.

Fixtures are constructed from explicit grammar templates, not human annotations.
The suite measures graph composition invariants only; it does not measure raw-text
recognition, naturalistic language accuracy, or generalization.
"""
from __future__ import annotations
from .engine import compose, project_loss_aware


def _span(text, surface, occurrence=0):
    start=-1; cursor=0
    for _ in range(occurrence+1):
        start=text.find(surface,cursor)
        if start<0: raise ValueError(f"surface not found: {surface}")
        cursor=start+len(surface)
    return {"start":start,"end":start+len(surface),"surface":surface}


def fixtures():
    rows=[]
    examples=[
      ("en","Lina and Omar read books.",[("lina","PERSON","Lina"),("omar","PERSON","Omar"),("read","EVENT","read"),("books","THING","books")],"COORDINATION"),
      ("ar","قرأ علي و سارة الكتاب.",[("read","EVENT","قرأ"),("ali","PERSON","علي"),("sara","PERSON","سارة"),("book","THING","الكتاب")],"COORDINATION"),
      ("en","Lina knows that Omar left.",[("lina","PERSON","Lina"),("knows","EVENT","knows"),("omar","PERSON","Omar"),("left","EVENT","left")],"EMBEDDED_CLAUSE"),
      ("ar","علمت ليلى أن عمر غادر.",[("knew","EVENT","علمت"),("layla","PERSON","ليلى"),("omar","PERSON","عمر"),("left","EVENT","غادر")],"EMBEDDED_CLAUSE"),
      ("en","Was the book read?",[("book","THING","book"),("read","EVENT","read")],"VOICE_SPEECH_ACT"),
      ("ar","هل قُرئ الكتاب؟",[("read","EVENT","قُرئ"),("book","THING","الكتاب")],"VOICE_SPEECH_ACT"),
      ("en","Lina may not leave.",[("lina","PERSON","Lina"),("leave","EVENT","leave")],"OPERATOR_SCOPE"),
      ("ar","قد لا يغادر علي.",[("leave","EVENT","يغادر"),("ali","PERSON","علي")],"OPERATOR_SCOPE"),
      ("en","Lina met Omar. She smiled.",[("lina","PERSON","Lina"),("omar","PERSON","Omar"),("she","MENTION","She"),("smiled","EVENT","smiled")],"DISCOURSE_REFERENCE"),
      ("ar","قابلت ليلى عمر. هي ابتسمت.",[("layla","PERSON","ليلى"),("omar","PERSON","عمر"),("she","MENTION","هي"),("smiled","EVENT","ابتسمت")],"DISCOURSE_REFERENCE"),
    ]
    for index,(lang,source,nodes,profile) in enumerate(examples,1):
        node_rows=[{"id":node_id,"kind":kind,"span":_span(source,surface)} for node_id,kind,surface in nodes]
        graph={"nodes":node_rows,"relations":[],"clauses":[],"operators":[],"references":[],"provenance":[{"rule_id":f"synthetic.{profile.lower()}.v1","resource_id":"synthetic-template-registry/1"}],"features":[profile],"speech_act":"UNKNOWN","voice":"UNKNOWN"}
        if profile=="COORDINATION":
            conjunction="and" if lang=="en" else "و"
            graph["relations"]=[{"type":"AND","source":nodes[0][0] if lang=="en" else nodes[1][0],"target":nodes[1][0] if lang=="en" else nodes[2][0],"feature":"COORDINATION","evidence":_span(source,conjunction)}]
        elif profile=="EMBEDDED_CLAUSE":
            split=source.index("that") if lang=="en" else source.index("أن")
            graph["clauses"]=[{"id":"main","kind":"MAIN","span":{"start":0,"end":len(source[:split].rstrip()),"surface":source[:split].rstrip()}},{"id":"embedded","kind":"EMBEDDED","parent_id":"main","span":{"start":split,"end":len(source),"surface":source[split:]}}]
        elif profile=="VOICE_SPEECH_ACT":
            graph["voice"]="PASSIVE"; graph["speech_act"]="QUESTION"
        elif profile=="OPERATOR_SCOPE":
            if lang=="en": ops=[("MODALITY","may","leave"),("NEGATION","not","leave")]
            else: ops=[("MODALITY","قد","يغادر"),("NEGATION","لا","يغادر")]
            graph["operators"]=[{"type":typ,"target_id":"leave","scope":"CLAUSE","span":_span(source,marker)} for typ,marker,target in ops]
        elif profile=="DISCOURSE_REFERENCE":
            graph["references"]=[{"mention_id":"she","antecedent_candidates":[nodes[0][0],nodes[1][0]],"uniqueness_evidence":False}]
        rows.append({"id":f"phase6-compose-{index:02d}","language":lang,"profile":profile,"source":source,"graph":graph})
    return rows


def run_benchmark():
    results=[]
    for fixture in fixtures():
        result=compose(fixture["source"],fixture["language"],fixture["graph"])
        projection=project_loss_aware(result)
        valid=result["status"]=="CANDIDATE_ONLY" and result["source"]["text"]==fixture["source"] and result["safety"]["canonical_assertions_emitted"] is False
        if fixture["profile"]=="DISCOURSE_REFERENCE":
            valid=valid and result["graph"]["references"][0]["status"]=="UNRESOLVED" and result["graph"]["references"][0]["resolved_antecedent"] is None
        if fixture["profile"] in {"VOICE_SPEECH_ACT","OPERATOR_SCOPE"}:
            valid=valid and (result["grammatical"]["voice"]=="PASSIVE" if fixture["profile"]=="VOICE_SPEECH_ACT" else len(result["graph"]["operators"])==2)
        valid=valid and projection["status"]=="NOT_PROJECTABLE" and projection["silent_loss"] is False
        results.append({"case_id":fixture["id"],"language":fixture["language"],"profile":fixture["profile"],"passed":bool(valid)})
    counts={}
    for row in results:
        key=f"{row['language']}/{row['profile']}"; counts[key]={"passed":int(row["passed"]),"total":1}
    return {"benchmark_id":"USG-PHASE6-COMPOSITION-CONTRACT","benchmark_version":"0.1.0","evaluation_scope":"GENERATED_GRAPH_COMPOSITION_CONTRACT_ONLY","case_count":len(results),"passed":sum(x["passed"] for x in results),"failed":sum(not x["passed"] for x in results),"by_profile":counts,"raw_text_recognition_measured":False,"naturalistic_accuracy_claimed":False,"results":results}
