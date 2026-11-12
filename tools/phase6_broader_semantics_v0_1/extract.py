"""Strict template-based raw-text candidate extraction for Phase 6.

This is a closed, deterministic grammar probe, not a general parser. It emits
candidate graphs only for exact supported templates and abstains otherwise.
"""
from __future__ import annotations
import re

TOKEN_RE = re.compile(r"[A-Za-z]+|[\u0621-\u064A\u066E-\u06D3\u06FA-\u06FC][\u0621-\u064A\u066E-\u06D3\u06FA-\u06FC\u064B-\u065F\u0670]*")

def _tokens(source):
    return [{"surface":m.group(0),"start":m.start(),"end":m.end()} for m in TOKEN_RE.finditer(source)]

def _node(source, token, node_id, kind):
    return {"id":node_id,"kind":kind,"span":{"start":token["start"],"end":token["end"],"surface":source[token["start"]:token["end"]]}}

def _evidence(source, token):
    return {"start":token["start"],"end":token["end"],"surface":source[token["start"]:token["end"]]}

def _empty_graph():
    return {"nodes":[],"relations":[],"clauses":[],"operators":[],"references":[],"features":[],"speech_act":"UNKNOWN","voice":"UNKNOWN","provenance":[]}

def extract_candidate_graph(source, language):
    if not isinstance(source,str) or not source.strip() or language not in {"en","ar"}:
        raise ValueError("non-empty source and language en/ar are required")
    tokens=_tokens(source); words=[t["surface"] for t in tokens]; graph=_empty_graph(); template=None
    def add_nodes(spec):
        graph["nodes"].extend(_node(source,tokens[i],node_id,kind) for i,node_id,kind in spec)
    if language=="en" and len(words)==5 and words[1].casefold()=="and" and words[0][:1].isupper() and words[2][:1].isupper():
        template="en.coordinated.subjects.v1"
        add_nodes([(0,"subject_1","PERSON"),(2,"subject_2","PERSON"),(3,"predicate","EVENT"),(4,"object","THING")])
        graph["relations"]=[{"type":"AND","source":"subject_1","target":"subject_2","feature":"COORDINATION","evidence":_evidence(source,tokens[1])}]
        graph["features"]=["COORDINATION"]
    elif language=="ar" and len(words)==5 and words[2]=="و":
        template="ar.coordinated.subjects.v1"
        add_nodes([(0,"predicate","EVENT"),(1,"subject_1","PERSON"),(3,"subject_2","PERSON"),(4,"object","THING")])
        graph["relations"]=[{"type":"AND","source":"subject_1","target":"subject_2","feature":"COORDINATION","evidence":_evidence(source,tokens[2])}]
        graph["features"]=["COORDINATION"]
    elif language=="en" and len(words)==5 and words[2].casefold()=="that" and words[0][:1].isupper() and words[3][:1].isupper():
        template="en.embedded.complement.v1"
        add_nodes([(0,"matrix_subject","PERSON"),(1,"matrix_predicate","EVENT"),(3,"embedded_subject","PERSON"),(4,"embedded_predicate","EVENT")])
        split=tokens[2]["start"]
        graph["clauses"]=[{"id":"main","kind":"MAIN","span":{"start":0,"end":tokens[1]["end"],"surface":source[:tokens[1]["end"]]}},{"id":"embedded","kind":"EMBEDDED","parent_id":"main","span":{"start":split,"end":len(source),"surface":source[split:]}}]
        graph["relations"]=[{"type":"COMPLEMENT","source":"matrix_predicate","target":"embedded_predicate","feature":"EMBEDDED_CLAUSE","evidence":_evidence(source,tokens[2])}]
        graph["features"]=["EMBEDDED_CLAUSE"]
    elif language=="ar" and len(words)==5 and words[2]=="أن":
        template="ar.embedded.complement.v1"
        add_nodes([(0,"matrix_predicate","EVENT"),(1,"matrix_subject","PERSON"),(3,"embedded_subject","PERSON"),(4,"embedded_predicate","EVENT")])
        split=tokens[2]["start"]
        graph["clauses"]=[{"id":"main","kind":"MAIN","span":{"start":0,"end":tokens[1]["end"],"surface":source[:tokens[1]["end"]]}},{"id":"embedded","kind":"EMBEDDED","parent_id":"main","span":{"start":split,"end":len(source),"surface":source[split:]}}]
        graph["relations"]=[{"type":"COMPLEMENT","source":"matrix_predicate","target":"embedded_predicate","feature":"EMBEDDED_CLAUSE","evidence":_evidence(source,tokens[2])}]
        graph["features"]=["EMBEDDED_CLAUSE"]
    elif language=="en" and len(words)==4 and words[0].casefold() in {"was","were","is","are"} and words[1].casefold() in {"the","a","an"} and source.rstrip().endswith("?"):
        template="en.passive.question.v1"
        add_nodes([(2,"patient","THING"),(3,"predicate","EVENT")])
        graph["voice"]="PASSIVE"; graph["speech_act"]="QUESTION"; graph["features"]=["VOICE","SPEECH_ACT"]
    elif language=="ar" and len(words)==3 and words[0]=="هل" and source.rstrip().endswith("؟"):
        template="ar.passive.question.v1"
        add_nodes([(1,"predicate","EVENT"),(2,"patient","THING")])
        graph["voice"]="PASSIVE"; graph["speech_act"]="QUESTION"; graph["features"]=["VOICE","SPEECH_ACT"]
    elif language=="en" and len(words)==4 and words[1].casefold() in {"may","might","must","can","could","should"} and words[2].casefold() in {"not","never"} and words[0][:1].isupper():
        template="en.modal.negation.scope.v1"
        add_nodes([(0,"subject","PERSON"),(3,"predicate","EVENT")])
        graph["operators"]=[{"type":"MODALITY","target_id":"predicate","scope":"CLAUSE","span":_evidence(source,tokens[1])},{"type":"NEGATION","target_id":"predicate","scope":"CLAUSE","span":_evidence(source,tokens[2])}]
        graph["features"]=["OPERATOR"]
    elif language=="ar" and len(words)==4 and words[0]=="قد" and words[1]=="لا":
        template="ar.modal.negation.scope.v1"
        add_nodes([(2,"predicate","EVENT"),(3,"subject","PERSON")])
        graph["operators"]=[{"type":"MODALITY","target_id":"predicate","scope":"CLAUSE","span":_evidence(source,tokens[0])},{"type":"NEGATION","target_id":"predicate","scope":"CLAUSE","span":_evidence(source,tokens[1])}]
        graph["features"]=["OPERATOR"]
    elif language=="en" and len(words)==5 and words[0][:1].isupper() and words[2][:1].isupper() and words[3].casefold() in {"he","she","they","it"}:
        template="en.discourse.pronoun.candidates.v1"
        add_nodes([(0,"antecedent_candidate","PERSON"),(2,"antecedent_candidate_2","PERSON"),(3,"mention","MENTION"),(4,"predicate","EVENT")])
        graph["references"]=[{"mention_id":"mention","antecedent_candidates":["antecedent_candidate","antecedent_candidate_2"],"uniqueness_evidence":False}]
        graph["features"]=["DISCOURSE_REFERENCE"]
    elif language=="ar" and len(words)==5 and words[3] in {"هو","هي","هم","هن"}:
        template="ar.discourse.pronoun.candidates.v1"
        add_nodes([(1,"antecedent_candidate","PERSON"),(2,"antecedent_candidate_2","PERSON"),(3,"mention","MENTION"),(4,"predicate","EVENT")])
        graph["references"]=[{"mention_id":"mention","antecedent_candidates":["antecedent_candidate","antecedent_candidate_2"],"uniqueness_evidence":False}]
        graph["features"]=["DISCOURSE_REFERENCE"]
    if template is None:
        return {"status":"ABSTAIN","language":language,"template_id":None,"graph":graph,"diagnostics":[{"code":"NO_CLOSED_TEMPLATE_MATCH","message":"No registered Phase 6 candidate template matched the exact token pattern."}],"capability_state":"CANDIDATE_ONLY"}
    graph["provenance"]=[{"rule_id":template,"resource_id":"phase6.closed-template-grammar/0.1.0"}]
    return {"status":"CANDIDATE_PATTERN_MATCH","language":language,"template_id":template,"graph":graph,"diagnostics":[],"capability_state":"CANDIDATE_ONLY","recognition_scope":"EXACT_CLOSED_TEMPLATE"}
