"""Phase 6 strict-template extraction API and immutable replay tests."""
import unittest
from tools.usg_local_api_v1_0_0.application import USGApplication

class Phase6ExtractAPITests(unittest.TestCase):
 def setUp(self): self.app=USGApplication(":memory:")
 def tearDown(self): self.app.close()
 def test_extract_compose_persist_and_replay(self):
  status,result=self.app.dispatch("POST","/v3/phase6/extract",{"source":"Lina and Omar read books.","language":"en","persist":True})
  self.assertEqual(status,200); self.assertEqual(result["extraction"]["status"],"CANDIDATE_PATTERN_MATCH")
  self.assertEqual(result["composition"]["status"],"CANDIDATE_ONLY")
  run_id=result["persistence"]["run_id"]
  status,replay=self.app.dispatch("POST","/v3/phase6/runs/"+run_id+"/replay",{})
  self.assertEqual(status,200); self.assertTrue(replay["deterministic_match"],replay)
 def test_unsupported_text_abstains_without_persisting(self):
  status,result=self.app.dispatch("POST","/v3/phase6/extract",{"source":"An unsupported open-world sentence.","language":"en","persist":True})
  self.assertEqual(status,200); self.assertEqual(result["extraction"]["status"],"ABSTAIN")
  self.assertNotIn("persistence",result); self.assertNotIn("composition",result)

if __name__=="__main__": unittest.main()
