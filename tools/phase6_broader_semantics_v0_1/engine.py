"""Deterministic, source-grounded graph composition for Phase 6 Steps 6.7–6.12.

This module composes explicitly supplied candidates; it is not a natural-language
parser and never promotes a candidate to a canonical fact.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json

CONTRACT = "USG-INTERPRET/0.3.0"
FEATURES = {"COORDINATION", "EMBEDDED_CLAUSE", "VOICE", "SPEECH_ACT", "OPERATOR", "DISCOURSE_REFERENCE", "SUBORDINATE_CLAUSE", "NOMINAL_PROPERTY", "POSSESSION", "MODIFIER"}
RELATIONS = {"AND", "OR", "CONTRAST", "COMPLEMENT", "RELATIVE", "TEMPORAL", "CAUSAL", "CONDITIONAL", "AGENT", "PATIENT", "THEME", "RECIPIENT", "ATTRIBUTE", "POSSESSOR", "POSSESSED", "MODIFIES", "COREF_CANDIDATE"}
OPERATORS = {"NEGATION", "MODALITY", "TENSE", "ASPECT", "QUANTIFIER", "CONDITION"}
VOICES = {"ACTIVE", "PASSIVE", "MIDDLE", "UNKNOWN"}
SPEECH_ACTS = {"ASSERTION", "QUESTION", "COMMAND", "REQUEST", "UNKNOWN"}

class CompositionError(ValueError):
    """Raised when a candidate graph violates the composition contract."""

def _span(source, value, label):
    if not isinstance(value, dict) or set(value) < {"start", "end"}:
        raise CompositionError(f"{label}: span requires start and end")
    start, end = value["start"], value["end"]
    if type(start) is not int or type(end) is not int or start < 0 or end <= start or end > len(source):
        raise CompositionError(f"{label}: invalid Unicode code-point offsets")
    surface = source[start:end]
    if value.get("surface", surface) != surface:
        raise CompositionError(f"{label}: span surface does not match exact source slice")
    return {"start": start, "end": end, "surface": surface}

def _unique(items, key, label):
    seen=set()
    for item in items:
        value=item.get(key)
        if not isinstance(value,str) or not value:
            raise CompositionError(f"{label}: missing {key}")
        if value in seen:
            raise CompositionError(f"{label}: duplicate {key} {value}")
        seen.add(value)
    return seen

def compose(source, language, graph):
    """Validate and compose a candidate graph without inferring missing bindings.

    graph keys: nodes, relations, clauses, operators, references, provenance.
    All node spans are exact source slices. Every edge is typed and references
    existing nodes. Cross-clause edges are represented explicitly.
    """
    if not isinstance(source,str) or not source or language not in {"en","ar"}:
        raise CompositionError("non-empty source and language en/ar are required")
    if not isinstance(graph,dict): raise CompositionError("graph must be an object")
    nodes=deepcopy(graph.get("nodes",[])); relations=deepcopy(graph.get("relations",[]))
    clauses=deepcopy(graph.get("clauses",[])); operators=deepcopy(graph.get("operators",[]))
    references=deepcopy(graph.get("references",[])); provenance=deepcopy(graph.get("provenance",[]))
    for name,items in (("nodes",nodes),("relations",relations),("clauses",clauses),("operators",operators),("references",references),("provenance",provenance)):
        if not isinstance(items,list): raise CompositionError(f"{name} must be an array")
    node_ids=_unique(nodes,"id","nodes")
    for node in nodes:
        if not isinstance(node.get("kind"),str) or not node["kind"]: raise CompositionError("node kind is required")
        node["span"]=_span(source,node.get("span"),f"node {node['id']}")
        node["status"]="CANDIDATE"
    clause_ids=_unique(clauses,"id","clauses")
    for clause in clauses:
        if clause.get("kind") not in {"MAIN","EMBEDDED","SUBORDINATE"}: raise CompositionError("unsupported clause kind")
        clause["span"]=_span(source,clause.get("span"),f"clause {clause['id']}")
        if clause.get("parent_id") is not None and clause["parent_id"] not in clause_ids: raise CompositionError("unknown parent clause")
        if clause.get("parent_id")==clause["id"]: raise CompositionError("clause cannot parent itself")
    for edge in relations:
        if edge.get("type") not in RELATIONS: raise CompositionError("unknown semantic relation type")
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids: raise CompositionError("relation references unknown node")
        if edge["type"]=="COREF_CANDIDATE": edge["status"]="UNRESOLVED_CANDIDATE"
        else: edge["status"]="CANDIDATE"
        if "evidence" not in edge: raise CompositionError("every relation requires source evidence")
        edge["evidence"]=_span(source,edge["evidence"],"relation evidence")
        if edge.get("feature") and edge["feature"] not in FEATURES: raise CompositionError("unknown relation feature")
    for operator in operators:
        if operator.get("type") not in OPERATORS: raise CompositionError("unknown operator")
        if operator.get("target_id") not in node_ids and operator.get("target_id") not in clause_ids: raise CompositionError("operator target is unknown")
        operator["span"]=_span(source,operator.get("span"),"operator")
        operator["status"]="CANDIDATE"
        if operator.get("scope") not in {"LOCAL","CLAUSE","EMBEDDED","UNRESOLVED"}: raise CompositionError("operator scope must be explicit")
    for ref in references:
        if ref.get("mention_id") not in node_ids: raise CompositionError("reference mention is unknown")
        antecedents=ref.get("antecedent_candidates",[])
        if not isinstance(antecedents,list) or any(x not in node_ids for x in antecedents): raise CompositionError("reference antecedent candidate is unknown")
        if len(antecedents)==1 and ref.get("uniqueness_evidence"):
            ref["status"]="CANDIDATE_UNIQUE_NOT_RESOLVED"
        else: ref["status"]="UNRESOLVED"
        ref["resolved_antecedent"] = None
    # Reject cyclic clause-parent chains, preserving only a tree/forest structure.
    parents={c["id"]:c.get("parent_id") for c in clauses}
    for cid in clause_ids:
        seen=set(); cur=cid
        while cur is not None:
            if cur in seen: raise CompositionError("cyclic clause embedding")
            seen.add(cur); cur=parents.get(cur)
    speech_act=graph.get("speech_act","UNKNOWN"); voice=graph.get("voice","UNKNOWN")
    if speech_act not in SPEECH_ACTS: raise CompositionError("unknown speech act")
    if voice not in VOICES: raise CompositionError("unknown voice")
    digest=sha256(source.encode("utf-8")).hexdigest()
    features=sorted(set(graph.get("features",[])))
    if any(x not in FEATURES for x in features): raise CompositionError("unknown graph feature")
    return {
        "pipeline_contract":CONTRACT,"pipeline_version":"usg-phase6-composition/0.1.0",
        "status":"CANDIDATE_ONLY","source":{"text":source,"sha256":digest,"language":language,"offset_unit":"unicode_code_point"},
        "graph":{"nodes":nodes,"relations":relations,"clauses":clauses,"operators":operators,"references":references},
        "grammatical":{"voice":voice,"speech_act":speech_act},"features":features,
        "provenance":provenance,"safety":{"canonical_assertions_emitted":False,"identity_resolution_performed":False,"candidate_promotion_performed":False},
    }

def project_loss_aware(result):
    """Refuse projection unless a separately implemented lossless mapping exists.

    Phase 6 graph features do not yet have a verified complete mapping into the
    unchanged USG-SEM/1.0 contract. This diagnostic prevents silent information loss.
    """
    if not isinstance(result,dict) or result.get("pipeline_contract")!=CONTRACT:
        raise CompositionError("a Phase 6 composition result is required")
    graph=result.get("graph",{})
    blockers=[]
    if result.get("status")!="CANDIDATE_ONLY": blockers.append("non-candidate result contract is not supported")
    if result.get("features"): blockers.extend(f"feature_not_losslessly_mapped:{x}" for x in result["features"])
    if graph.get("clauses"): blockers.append("clause structure has no verified USG-SEM/1.0 projection")
    if graph.get("operators"): blockers.append("operator scope has no verified lossless projection")
    if graph.get("references"): blockers.append("discourse reference candidates cannot be projected as identity")
    if graph.get("relations"): blockers.append("candidate semantic relations are not canonical assertions")
    return {"status":"NOT_PROJECTABLE","target_contract":"USG-SEM/1.0","document":None,
            "diagnostics":sorted(set(blockers or ["no verified Phase 6 to USG-SEM/1.0 projection adapter is registered"])),
            "silent_loss":False}
