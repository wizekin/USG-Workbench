import unittest
from tools.phase6_benchmark_v0_4_2.validate import validate
class TestV042(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.d=validate()
 def test_total(self): self.assertEqual(len(self.d["cases"]),500)
 def test_corrected_office_of_marker(self):
  c=next(x for x in self.d["cases"] if x["id"]=="en.possession.of_phrase.positive.6")
  s=c["expected_grammatical_markers"][0]
  self.assertEqual(c["text"][s["start"]:s["end"]],"of")
  self.assertEqual(s["start"],11)
 def test_all_markers_are_complete_tokens(self):
  for c in self.d["cases"]:
   for s in c["expected_grammatical_markers"]:
    self.assertEqual(c["text"][s["start"]:s["end"]],s["surface"])
if __name__=="__main__": unittest.main()
