from __future__ import annotations
import sys, unittest
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/"implementations/python-kernel/v0.8.0"))
from interoperability.python_adapter.document_v08 import document_to_kernel_v08,kernel_v08_document_to_contract
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_assertion_v08 import EpistemicStatus,EvaluationContext,EvaluationContextKind,LifecycleStage,ReferenceSpace,TypedReference

class KernelV08DocumentAdapterTests(unittest.TestCase):
 def make_document(self):
  return {"profileId":"USG-SEM/1.0","documentId":"test:document","sources":[{"id":"s:1"}],"primarySourceRef":"s:1",
   "definitions":{"concepts":[{"id":"d:concept","label":"concept","semanticKind":"ENTITY","version":1}],"frames":[],"roles":[],"relations":[]},
   "referents":[{"id":"r:1","label":"Author"}],"mentions":[],
   "expressions":[{"id":"x:1","op":"LIT","sort":"PROP","operandRefs":[],"params":{}},{"id":"x:2","op":"LIT","sort":"PROP","operandRefs":[],"params":{}}],
   "rootExpressionRefs":["x:1"],"assertions":[{"id":"a:1","expressionRef":"x:1","origin":"SOURCE_TEXT","epistemicStatus":"SOURCE_ASSERTED","commitment":"ATTRIBUTED","attributedToRef":"r:1",
   "evaluationContext":{"kind":"WORLD","contextRef":"c:1","name":"ordinary world"},"lifecycleStage":"DISCOVERED","sourceRef":"s:1","evidenceRefs":["e:2","e:1","e:2"],"definitionRef":"d:concept"}],
   "evidence":[{"id":"e:1"},{"id":"e:2"}],"contexts":[{"id":"c:1","kind":"WORLD"}],"expressionRelations":[],"unresolvedItems":[],"derivations":[],
   "validation":{"structuralStatus":"NOT_CHECKED","checks":[],"validator":"fixture","contractVersion":"USG-SEM/1.0"},
   "mapping":{"sourceProfile":"fixture","sourceVersion":"1","status":"LOSSLESS","unmappedRefs":[]},"extensions":{"org.usg.test":{"preserve":True}}}
 def test_exact_fields_and_typed_links_project(self):
  x=document_to_kernel_v08(self.make_document(),validate=False); n=x.assertions["a:1"]
  self.assertEqual(n.expression_ref.space,ReferenceSpace.EXPRESSION); self.assertEqual(n.attributed_to_ref.space,ReferenceSpace.REFERENT)
  self.assertEqual(n.source_ref.space,ReferenceSpace.SOURCE); self.assertEqual([r.external_id for r in n.evidence_refs],["e:2","e:1","e:2"])
  self.assertEqual(n.definition_ref.space,ReferenceSpace.DEFINITION); self.assertEqual(n.evaluation_context.context_ref.space,ReferenceSpace.CONTEXT)
  self.assertEqual(x.mapping_report["targetVersion"],"0.8.0")
 def test_assertion_and_expression_are_distinct(self):
  n=document_to_kernel_v08(self.make_document(),validate=False).assertions["a:1"]
  self.assertNotEqual(n.external_id,n.expression_ref.external_id)
 def test_alternative_group_remains_canonical_only(self):
  d=self.make_document(); d["assertions"][0]["alternativeGroupRef"]="group:1"; x=document_to_kernel_v08(d,validate=False)
  e=x.record_mapping["assertions"]["records"]["a:1"]; self.assertEqual(e["status"],"PARTIAL"); self.assertIn("alternativeGroupRef",e["unmappedFields"])
  self.assertEqual(kernel_v08_document_to_contract(x,validate=False)["assertions"],d["assertions"])
 def test_dangling_optional_links_remain_canonical_only(self):
  d=self.make_document(); a=d["assertions"][0]; a.update(attributedToRef="missing:r",sourceRef="missing:s",evidenceRefs=["e:1","missing:e"])
  a["evaluationContext"]["contextRef"]="missing:c"; x=document_to_kernel_v08(d,validate=False); n=x.assertions["a:1"]
  self.assertIsNone(n.attributed_to_ref); self.assertIsNone(n.source_ref); self.assertEqual(n.evidence_refs,()); self.assertIsNone(n.evaluation_context.context_ref)
  fields=x.record_mapping["assertions"]["records"]["a:1"]["unmappedFields"]
  for f in ("attributedToRef","sourceRef","evidenceRefs","evaluationContext.contextRef"): self.assertIn(f,fields)
  self.assertEqual(kernel_v08_document_to_contract(x,validate=False)["assertions"],d["assertions"])
 def test_unknown_required_enum_keeps_assertion_canonical_only(self):
  d=self.make_document(); d["assertions"][0]["epistemicStatus"]="FUTURE_STATUS"; x=document_to_kernel_v08(d,validate=False)
  self.assertNotIn("a:1",x.assertions); self.assertEqual(x.record_mapping["assertions"]["records"]["a:1"]["status"],"UNMAPPED")
  self.assertEqual(kernel_v08_document_to_contract(x,validate=False)["assertions"],d["assertions"])
 def test_extra_context_metadata_is_preserved(self):
  d=self.make_document(); d["assertions"][0]["evaluationContext"]["futureFrame"]={"x":1}; x=document_to_kernel_v08(d,validate=False)
  self.assertIn("evaluationContext.futureFrame",x.record_mapping["assertions"]["records"]["a:1"]["unmappedFields"])
  self.assertEqual(kernel_v08_document_to_contract(x,validate=False)["assertions"][0]["evaluationContext"]["futureFrame"],{"x":1})
 def test_native_edits_merge_only_assertion_and_preserve_sidecars(self):
  d=self.make_document(); d["assertions"][0]["nativeId"]="legacy:native"; x=document_to_kernel_v08(d,validate=False); old=x.assertions["a:1"]
  x.assertions["a:1"]=replace(old,epistemic_status=EpistemicStatus.DISPUTED,lifecycle_stage=LifecycleStage.DEFERRED,
   evaluation_context=EvaluationContext(EvaluationContextKind.HYPOTHETICAL,TypedReference(ReferenceSpace.CONTEXT,"c:1"),"counterfactual frame"),
   evidence_refs=(TypedReference(ReferenceSpace.EVIDENCE,"e:1"),))
  out=kernel_v08_document_to_contract(x,validate=False); a=out["assertions"][0]
  self.assertEqual(a["epistemicStatus"],"DISPUTED"); self.assertEqual(a["lifecycleStage"],"DEFERRED")
  self.assertEqual(a["evaluationContext"]["kind"],"HYPOTHETICAL"); self.assertEqual(a["evaluationContext"]["name"],"counterfactual frame")
  self.assertEqual(a["evidenceRefs"],["e:1"]); self.assertEqual(a["nativeId"],"legacy:native")
  self.assertEqual(out["expressions"],d["expressions"]); self.assertEqual(out["sources"],d["sources"]); self.assertEqual(out["extensions"],d["extensions"])
 def test_changed_references_must_resolve_in_correct_collection(self):
  x=document_to_kernel_v08(self.make_document(),validate=False); old=x.assertions["a:1"]
  x.assertions["a:1"]=replace(old,source_ref=TypedReference(ReferenceSpace.SOURCE,"not:there"))
  with self.assertRaises(ContractMappingError): kernel_v08_document_to_contract(x,validate=False)
  x=document_to_kernel_v08(self.make_document(),validate=False); old=x.assertions["a:1"]
  x.assertions["a:1"]=replace(old,expression_ref=TypedReference(ReferenceSpace.CONTEXT,"c:1"))
  with self.assertRaises(ContractMappingError): kernel_v08_document_to_contract(x,validate=False)
 def test_stale_snapshot_is_rejected(self):
  x=document_to_kernel_v08(self.make_document(),validate=False); x.document["assertions"][0]["commitment"]="NONE"
  with self.assertRaises(ContractMappingError): kernel_v08_document_to_contract(x,validate=False)
 def test_non_assertion_records_remain_canonical_only(self):
  x=document_to_kernel_v08(self.make_document(),validate=False); self.assertEqual(x.record_mapping["expressions"]["status"],"UNMAPPED")
  self.assertEqual(kernel_v08_document_to_contract(x,validate=False)["definitions"],self.make_document()["definitions"])
 def test_dangling_required_expression_prevents_projection(self):
  d=self.make_document(); d["assertions"][0]["expressionRef"]="missing:x"; x=document_to_kernel_v08(d,validate=False)
  self.assertNotIn("a:1",x.assertions); self.assertEqual(x.record_mapping["assertions"]["records"]["a:1"]["status"],"UNMAPPED")
 def test_wrong_native_reference_space_rejected(self):
  x=document_to_kernel_v08(self.make_document(),validate=False); old=x.assertions["a:1"]
  with self.assertRaises(ValueError): replace(old,source_ref=TypedReference(ReferenceSpace.CONTEXT,"c:1"))

if __name__=="__main__": unittest.main()
