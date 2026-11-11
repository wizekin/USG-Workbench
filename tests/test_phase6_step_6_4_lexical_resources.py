"""Phase 6 Step 6.4 lexical and morphology resource tests."""
import unittest
from tools.phase6_lexical_resources_v0_3_0.validate import validate_resource
class Phase6Step64LexicalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.data=validate_resource()
 def test_bilingual_profiles_and_candidate_only(self):
  self.assertEqual({e["language"] for e in self.data["entries"]},{"en","ar"})
  self.assertTrue(all(e["status"]=="CANDIDATE" for e in self.data["entries"]))
  self.assertTrue(all(r["status"]=="CANDIDATE" for r in self.data["morphology_rules"]))
 def test_every_entry_has_exact_source_evidence(self):
  self.assertTrue(all(e["evidence"] for e in self.data["entries"]))
  self.assertTrue(all(ev["start"]<ev["end"] for e in self.data["entries"] for ev in e["evidence"]))
 def test_unknown_forms_are_not_generated_by_rules(self):
  rules={r["rule_id"]:r for r in self.data["morphology_rules"]}
  self.assertEqual(set(rules),{"en.present-third-person-singular-s","ar-definite-article-al"})
  self.assertTrue(all(r["pattern"]["example_forms"] for r in rules.values()))
 def test_polysemous_predicate_forms_keep_separate_sense_candidates(self):
  for language,form in (("en","waits"),("ar","انتظر")):
   senses={e["sense_id"] for e in self.data["entries"] if e["language"]==language and e["form"]==form}
   self.assertIn("usg.sense.event.intransitive",senses)
   self.assertIn("usg.sense.spatial.location",senses)
 def test_lexical_inventory_covers_both_profiles(self):
  counts={lang:sum(e["language"]==lang for e in self.data["entries"]) for lang in ("en","ar")}
  self.assertGreater(counts["en"],0); self.assertGreater(counts["ar"],0)
if __name__=="__main__": unittest.main()
