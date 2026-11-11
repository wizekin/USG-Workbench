import unittest
from tools.phase6_benchmark_v0_4_0.validate import validate
class TestV040(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.d=validate()
 def test_total(self): self.assertEqual(len(self.d['cases']),500)
 def test_candidate_only(self): self.assertTrue(all(not x['enabled'] for a in self.d['construction_inventory'].values() for x in a))
 def test_ten_profiles(self): self.assertEqual(sum(map(len,self.d['construction_inventory'].values())),10)
if __name__=='__main__': unittest.main()
