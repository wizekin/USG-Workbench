"""Loss-preserving USG-SEM/1.0 Assertion adapter for native model v0.8.0."""
from __future__ import annotations
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"

def _load_assertion_model():
    try:
        import usg_assertion_v08 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_assertion_v08": raise
    import importlib.util, sys
    package_dir = Path(__file__).resolve().parents[2] / "implementations" / "python-kernel" / "v0.8.0" / "usg_assertion_v08"
    spec = importlib.util.spec_from_file_location("usg_assertion_v08", package_dir / "__init__.py", submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None: raise ImportError("Cannot load native Assertion model")
    model = importlib.util.module_from_spec(spec); sys.modules["usg_assertion_v08"] = model; spec.loader.exec_module(model)
    return model

_model = _load_assertion_model()
MODEL_VERSION = _model.MODEL_VERSION
AssertionOrigin, EpistemicStatus = _model.AssertionOrigin, _model.EpistemicStatus
CommitmentKind, EvaluationContextKind = _model.CommitmentKind, _model.EvaluationContextKind
LifecycleStage, EvaluationContext = _model.LifecycleStage, _model.EvaluationContext
NativeAssertionV08, ReferenceSpace, TypedReference = _model.NativeAssertionV08, _model.ReferenceSpace, _model.TypedReference
_ASSERTION_FIELDS = {"id","expressionRef","origin","epistemicStatus","commitment","attributedToRef","evaluationContext","lifecycleStage","sourceRef","evidenceRefs","definitionRef","alternativeGroupRef"}
_CONTEXT_FIELDS = {"kind","contextRef","name"}
_COLLECTIONS = ("sources","referents","mentions","expressions","assertions","evidence","contexts","expressionRelations","unresolvedItems","derivations")

@dataclass
class KernelV08Document:
    document: dict[str, Any]
    original_digest: str
    assertions: dict[str, NativeAssertionV08]
    assertion_snapshots: dict[str, NativeAssertionV08]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]
    def export_contract_document(self, *, validate: bool = True, schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError("Canonical document snapshot was modified; refusing stale native Assertion merge.")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("assertions", [])}
        targets = _target_ids(result)
        for key, native in self.assertions.items():
            if not isinstance(native, NativeAssertionV08): raise ContractMappingError(f"Non-NativeAssertionV08 record for {key}")
            if native.external_id != key: raise ContractMappingError(f"Native Assertion key {key!r} does not match opaque ID")
            if key not in records or key not in self.assertion_snapshots: raise ContractMappingError(f"Native Assertion {key!r} has no canonical snapshot")
            _merge_assertion_edit(records[key], self.assertion_snapshots[key], native, targets)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems: raise ContractMappingError("Serialized kernel v0.8.0 document is invalid: " + "; ".join(problems[:20]))
        return result

def _ids(doc, collection):
    return {x["id"] for x in doc.get(collection, []) if isinstance(x, Mapping) and isinstance(x.get("id"), str)}
def _definition_ids(doc):
    defs = doc.get("definitions") or {}; out = set()
    for group in ("concepts","frames","roles","relations"):
        out.update(x["id"] for x in defs.get(group, []) if isinstance(x, Mapping) and isinstance(x.get("id"), str))
    return out
def _target_ids(doc):
    return {ReferenceSpace.ASSERTION:_ids(doc,"assertions"), ReferenceSpace.EXPRESSION:_ids(doc,"expressions"),
        ReferenceSpace.SOURCE:_ids(doc,"sources"), ReferenceSpace.REFERENT:_ids(doc,"referents"),
        ReferenceSpace.EVIDENCE:_ids(doc,"evidence"), ReferenceSpace.CONTEXT:_ids(doc,"contexts"),
        ReferenceSpace.DEFINITION:_definition_ids(doc), ReferenceSpace.ALTERNATIVE_GROUP:set()}
def _enum(cls, value):
    try: return cls(value)
    except (ValueError, TypeError): return None

def _project_assertion(item, targets):
    aid=item["id"]; mapped=["id"]; bad=[]
    expr=item.get("expressionRef")
    if not isinstance(expr,str) or expr not in targets[ReferenceSpace.EXPRESSION]: return None,mapped,["expressionRef"]
    specs=(("origin",AssertionOrigin),("epistemicStatus",EpistemicStatus),("commitment",CommitmentKind),("lifecycleStage",LifecycleStage))
    values={}
    for field,cls in specs:
        v=_enum(cls,item.get(field))
        if v is None: bad.append(field)
        else: values[field]=v; mapped.append(field)
    ctx=item.get("evaluationContext")
    if not isinstance(ctx,Mapping): return None,mapped,bad+["evaluationContext"]
    kind=_enum(EvaluationContextKind,ctx.get("kind"))
    if kind is None: return None,mapped,bad+["evaluationContext.kind"]
    def link(field,space):
        v=item.get(field)
        if v is None: mapped.append(field); return None
        if isinstance(v,str) and v in targets[space]: mapped.append(field); return TypedReference(space,v)
        bad.append(field); return None
    attributed=link("attributedToRef",ReferenceSpace.REFERENT)
    source=link("sourceRef",ReferenceSpace.SOURCE)
    definition=link("definitionRef",ReferenceSpace.DEFINITION)
    raw_evidence=item.get("evidenceRefs",[])
    evidence=()
    if isinstance(raw_evidence,list) and all(isinstance(v,str) and v in targets[ReferenceSpace.EVIDENCE] for v in raw_evidence):
        evidence=tuple(TypedReference(ReferenceSpace.EVIDENCE,v) for v in raw_evidence); mapped.append("evidenceRefs")
    else: bad.append("evidenceRefs")
    raw_ctx=ctx.get("contextRef"); context_ref=None
    if raw_ctx is None: mapped.append("evaluationContext.contextRef")
    elif isinstance(raw_ctx,str) and raw_ctx in targets[ReferenceSpace.CONTEXT]:
        context_ref=TypedReference(ReferenceSpace.CONTEXT,raw_ctx); mapped.append("evaluationContext.contextRef")
    else: bad.append("evaluationContext.contextRef")
    name=ctx.get("name")
    if name is None or isinstance(name,str): mapped.append("evaluationContext.name")
    else: name=None; bad.append("evaluationContext.name")
    bad.extend("evaluationContext."+k for k in sorted(set(ctx)-_CONTEXT_FIELDS))
    if item.get("alternativeGroupRef") is None: mapped.append("alternativeGroupRef")
    else: bad.append("alternativeGroupRef")
    bad.extend(sorted(set(item)-_ASSERTION_FIELDS))
    if any(f in bad for f,_ in specs): return None,mapped,bad
    native=NativeAssertionV08(external_id=aid,expression_ref=TypedReference(ReferenceSpace.EXPRESSION,expr),
        origin=values["origin"],epistemic_status=values["epistemicStatus"],commitment=values["commitment"],
        evaluation_context=EvaluationContext(kind,context_ref,name),lifecycle_stage=values["lifecycleStage"],
        attributed_to_ref=attributed,source_ref=source,evidence_refs=evidence,definition_ref=definition,alternative_group_ref=None)
    return native,mapped,bad

def _require_target(ref, space, targets):
    if not isinstance(ref,TypedReference) or ref.space is not space: raise ContractMappingError(f"Reference must explicitly target {space.value}")
    if ref.external_id not in targets[space]: raise ContractMappingError(f"{space.value} reference {ref.external_id!r} does not resolve in canonical document")
def _merge_assertion_edit(record,snapshot,current,targets):
    if current.external_id != snapshot.external_id: raise ContractMappingError("Assertion identity is immutable")
    if current.expression_ref != snapshot.expression_ref:
        _require_target(current.expression_ref,ReferenceSpace.EXPRESSION,targets); record["expressionRef"]=current.expression_ref.external_id
    for attr,field,cls in (("origin","origin",AssertionOrigin),("epistemic_status","epistemicStatus",EpistemicStatus),("commitment","commitment",CommitmentKind),("lifecycle_stage","lifecycleStage",LifecycleStage)):
        before,after=getattr(snapshot,attr),getattr(current,attr)
        if before != after:
            if not isinstance(after,cls): raise ContractMappingError(f"{field} must be a known {cls.__name__}")
            record[field]=after.value
    b,a=snapshot.evaluation_context,current.evaluation_context
    if b.kind != a.kind:
        if not isinstance(a.kind,EvaluationContextKind): raise ContractMappingError("Invalid evaluationContext.kind")
        record.setdefault("evaluationContext",{})["kind"]=a.kind.value
    if b.name != a.name:
        c=record.setdefault("evaluationContext",{})
        if a.name is None: c.pop("name",None)
        elif isinstance(a.name,str): c["name"]=a.name
        else: raise ContractMappingError("evaluationContext.name must be string or None")
    if b.context_ref != a.context_ref:
        c=record.setdefault("evaluationContext",{})
        if a.context_ref is None: c.pop("contextRef",None)
        else: _require_target(a.context_ref,ReferenceSpace.CONTEXT,targets); c["contextRef"]=a.context_ref.external_id
    for attr,field,space in (("attributed_to_ref","attributedToRef",ReferenceSpace.REFERENT),("source_ref","sourceRef",ReferenceSpace.SOURCE),("definition_ref","definitionRef",ReferenceSpace.DEFINITION)):
        before,after=getattr(snapshot,attr),getattr(current,attr)
        if before != after:
            if after is None: record.pop(field,None)
            else: _require_target(after,space,targets); record[field]=after.external_id
    if snapshot.evidence_refs != current.evidence_refs:
        if not isinstance(current.evidence_refs,tuple): raise ContractMappingError("evidence_refs must be tuple")
        for ref in current.evidence_refs: _require_target(ref,ReferenceSpace.EVIDENCE,targets)
        record["evidenceRefs"]=[r.external_id for r in current.evidence_refs]

def document_to_kernel_v08(document:Mapping[str,Any],*,validate:bool=True,schema_path:str|Path=SCHEMA_PATH)->KernelV08Document:
    if not isinstance(document,Mapping): raise TypeError("document must be a mapping")
    payload=copy.deepcopy(dict(document))
    if payload.get("profileId")!="USG-SEM/1.0": raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems=validate_contract_document(payload,schema_path)
        if problems: raise ContractMappingError("Invalid USG-SEM document: "+"; ".join(problems[:20]))
    targets=_target_ids(payload); natives={}; snapshots={}; entries={}; mapped=[]; unmapped=[]; diagnostics=[]
    for item in payload.get("assertions",[]):
        native,fields,bad=_project_assertion(item,targets)
        if native is None:
            bad=sorted(set(bad+["required native projection unavailable"])); unmapped.append(item["id"])
            entries[item["id"]]={"status":"UNMAPPED","mappedFields":fields,"unmappedFields":bad,"notes":["Complete Assertion remains canonical-only; no required field was guessed or coerced."]}
            diagnostics.append(f"assertion {item['id']} remains canonical-only: "+", ".join(bad)); continue
        natives[item["id"]]=native; snapshots[item["id"]]=native; bad=sorted(set(bad))
        status="PARTIAL" if bad else "LOSSLESS"
        (unmapped if bad else mapped).append(item["id"])
        if bad: diagnostics.append(f"assertion {item['id']} has canonical-only fields: "+", ".join(bad))
        entries[item["id"]]={"status":status,"mappedFields":fields,"unmappedFields":bad,"notes":["Unsupported/dangling fields remain canonical-only."] if bad else []}
    mapping={"assertions":{"status":"PARTIAL" if unmapped else "LOSSLESS","mapped":sorted(mapped),"unmappedRefs":sorted(unmapped),"records":entries,
        "notes":["Assertion is a claim about an Expression, not the Expression itself.","Origin, epistemic status, commitment, evaluation context, and lifecycle are independent.","No truth judgment, evidence entailment, lifecycle transition, or inference is performed."]}}
    canonical=[]
    for collection in _COLLECTIONS:
        if collection=="assertions": continue
        ids=sorted(_ids(payload,collection)); canonical.extend(ids)
        mapping[collection]={"status":"UNMAPPED" if ids else "LOSSLESS","mapped":[],"unmappedRefs":ids,"notes":["Preserved in canonical envelope; not projected by this adapter."] if ids else []}
    defs=sorted(_definition_ids(payload)); canonical.extend(defs)
    mapping["definitions"]={"status":"UNMAPPED" if defs else "LOSSLESS","mapped":[],"unmappedRefs":defs,"notes":["Definitions remain canonical-only; only typed Definition references are projected."] if defs else []}
    for key in ("validation","mapping","extensions"): mapping[key]={"status":"PRESERVED","mapped":[],"unmappedRefs":[],"notes":["Preserved verbatim; not promoted to native kernel authority."]}
    all_unmapped=sorted(set(canonical+unmapped))
    report={"sourceProfile":"USG-SEM/1.0","sourceVersion":"1.0","targetProfile":"usg-python-kernel","targetVersion":MODEL_VERSION,
        "status":"PARTIAL" if all_unmapped else "LOSSLESS","unmappedRefs":all_unmapped,"recordMapping":copy.deepcopy(mapping),
        "notes":["Complete canonical document remains authoritative.","Only exact, resolvable Assertion fields project into native v0.8.0.",
        "Alternative Group references remain canonical-only because USG-SEM/1.0 has no corresponding record collection.","All non-Assertion record families remain canonical-only."]}
    return KernelV08Document(payload,_digest(payload),natives,snapshots,mapping,report,diagnostics)

def kernel_v08_document_to_contract(imported:KernelV08Document,*,validate:bool=True,schema_path:str|Path=SCHEMA_PATH)->dict[str,Any]:
    if not isinstance(imported,KernelV08Document): raise TypeError("imported must be KernelV08Document")
    return imported.export_contract_document(validate=validate,schema_path=schema_path)
