import unittest
from tools.phase6_benchmark_v0_4_1.validate import validate
class TestV041(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.d=validate()
 def test_total_and_profiles(self): self.assertEqual(len(self.d["cases"]),500); self.assertEqual(sum(map(len,self.d["construction_inventory"].values())),10)
 def test_no_conflicting_labels_for_identical_text(self):
  seen={}
  for c in self.d["cases"]:
   k=(c["language"],c["target_construction"],c["text"])
   self.assertTrue(k not in seen or seen[k]==c["gold_class"],"conflicting labels: "+c["id"])
   seen[k]=c["gold_class"]
 def test_genitive_never_asserts_ownership(self):
  rows=[c for c in self.d["cases"] if c["target_construction"] in {"en.genitive.of_phrase","ar.genitive.idafa"} and c["gold_class"]=="POSITIVE"]
  self.assertEqual(len(rows),40); self.assertTrue(all(c["expected_relation_type"]=="GENITIVE_UNSPECIFIED" for c in rows))
 def test_genitive_roles_are_structural(self):
  rows=[c for c in self.d["cases"] if c["target_construction"] in {"en.genitive.of_phrase","ar.genitive.idafa"} and c["gold_class"]=="POSITIVE"]
  self.assertTrue(all(set(c["expected_roles"])=={"GENITIVE_HEAD","GENITIVE_DEPENDENT"} for c in rows))
if __name__=="__main__": unittest.main()
