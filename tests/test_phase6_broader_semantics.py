"""Adversarial contract tests for Phase 6 Steps 6.7–6.12 candidate composition."""
import unittest
from tools.phase6_broader_semantics_v0_1 import compose, project_loss_aware, CompositionError

class BroaderSemanticsTests(unittest.TestCase):
 def base(self):
  text="Ada and Ben read books because rain fell."
  return text,"en",{"nodes":[{"id":"ada","kind":"PERSON","span":{"start":0,"end":3}},{"id":"ben","kind":"PERSON","span":{"start":8,"end":11}},{"id":"read","kind":"EVENT","span":{"start":12,"end":16}},{"id":"books","kind":"THING","span":{"start":17,"end":22}},{"id":"rain","kind":"THING","span":{"start":31,"end":35}},{"id":"fell","kind":"EVENT","span":{"start":36,"end":40}}],"relations":[],"clauses":[{"id":"main","kind":"MAIN","span":{"start":0,"end":22}},{"id":"cause","kind":"SUBORDINATE","parent_id":"main","span":{"start":23,"end":40}}],"operators":[],"references":[],"provenance":[{"rule_id":"fixture.rule.1","resource_id":"fixture.resource.1"}],"features":["COORDINATION","EMBEDDED_CLAUSE"],"speech_act":"ASSERTION","voice":"ACTIVE"}
 def test_coordination_and_embedded_clause_are_preserved(self):
  text,lang,g=self.base(); g["relations"]=[{"type":"AND","source":"ada","target":"ben","feature":"COORDINATION","evidence":{"start":4,"end":7}}]
  out=compose(text,lang,g)
  self.assertEqual(out["status"],"CANDIDATE_ONLY")
  self.assertEqual(out["graph"]["relations"][0]["status"],"CANDIDATE")
  self.assertEqual(out["graph"]["clauses"][1]["parent_id"],"main")
 def test_operator_scope_is_explicit_and_not_inferred(self):
  text,lang,g=self.base(); g["operators"]=[{"type":"NEGATION","target_id":"read","scope":"CLAUSE","span":{"start":12,"end":16}}]
  out=compose(text,lang,g); self.assertEqual(out["graph"]["operators"][0]["scope"],"CLAUSE")
 def test_voice_and_speech_act_are_kept_separate(self):
  text,lang,g=self.base(); g["voice"]="PASSIVE"; g["speech_act"]="QUESTION"
  out=compose(text,lang,g); self.assertEqual(out["grammatical"],{"voice":"PASSIVE","speech_act":"QUESTION"})
 def test_reference_candidates_never_become_identity(self):
  text,lang,g=self.base(); g["references"]=[{"mention_id":"ben","antecedent_candidates":["ada","rain"],"uniqueness_evidence":False}]
  out=compose(text,lang,g); self.assertEqual(out["graph"]["references"][0]["status"],"UNRESOLVED")
  self.assertIsNone(out["graph"]["references"][0]["resolved_antecedent"])
  self.assertFalse(out["safety"]["identity_resolution_performed"])
 def test_single_candidate_is_still_not_auto_resolved(self):
  text,lang,g=self.base(); g["references"]=[{"mention_id":"ben","antecedent_candidates":["ada"],"uniqueness_evidence":True}]
  out=compose(text,lang,g); self.assertEqual(out["graph"]["references"][0]["status"],"CANDIDATE_UNIQUE_NOT_RESOLVED")
 def test_projection_refuses_silent_loss(self):
  text,lang,g=self.base(); result=compose(text,lang,g); projection=project_loss_aware(result)
  self.assertEqual(projection["status"],"NOT_PROJECTABLE"); self.assertIsNone(projection["document"])
  self.assertFalse(projection["silent_loss"]); self.assertTrue(projection["diagnostics"])
 def test_bad_source_span_is_rejected(self):
  text,lang,g=self.base(); g["nodes"][0]["span"]={"start":0,"end":3,"surface":"Eve"}
  with self.assertRaises(CompositionError): compose(text,lang,g)
 def test_unknown_relation_and_missing_evidence_are_rejected(self):
  text,lang,g=self.base(); g["relations"]=[{"type":"OWNS","source":"ada","target":"books"}]
  with self.assertRaises(CompositionError): compose(text,lang,g)
 def test_clause_cycles_are_rejected(self):
  text,lang,g=self.base(); g["clauses"][0]["parent_id"]="cause"
  with self.assertRaises(CompositionError): compose(text,lang,g)
 def test_operator_without_explicit_scope_is_rejected(self):
  text,lang,g=self.base(); g["operators"]=[{"type":"MODALITY","target_id":"read","span":{"start":12,"end":16}}]
  with self.assertRaises(CompositionError): compose(text,lang,g)

if __name__=="__main__": unittest.main()
