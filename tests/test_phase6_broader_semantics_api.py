"""Shared API integration tests for Phase 6 candidate composition."""
import unittest
from tools.usg_local_api_v1_0_0.application import USGApplication

class Phase6CandidateAPITests(unittest.TestCase):
    def setUp(self): self.app=USGApplication(":memory:")
    def tearDown(self): self.app.close()
    def request(self):
        source="Lina and Omar read books."
        graph={"nodes":[{"id":"lina","kind":"PERSON","span":{"start":0,"end":4}},{"id":"omar","kind":"PERSON","span":{"start":9,"end":13}}],"relations":[{"type":"AND","source":"lina","target":"omar","feature":"COORDINATION","evidence":{"start":5,"end":8}}],"clauses":[],"operators":[],"references":[],"features":["COORDINATION"],"speech_act":"ASSERTION","voice":"ACTIVE","provenance":[{"rule_id":"api.fixture.v1","resource_id":"test.resource/1"}]}
        return {"source":source,"language":"en","graph":graph,"persist":True}
    def test_health_advertises_candidate_only_contract(self):
        status,result=self.app.dispatch("GET","/health")
        self.assertEqual(status,200); self.assertEqual(result["phase6_candidate_pipeline"],"USG-INTERPRET/0.3.0")
        self.assertEqual(result["phase6_candidate_capabilities"],"CANDIDATE_ONLY")
    def test_compose_store_get_and_replay(self):
        status,result=self.app.dispatch("POST","/v3/phase6/compose",self.request())
        self.assertEqual(status,200); self.assertEqual(result["composition"]["status"],"CANDIDATE_ONLY")
        self.assertEqual(result["projection"]["status"],"NOT_PROJECTABLE")
        run_id=result["persistence"]["run_id"]
        status,stored=self.app.dispatch("GET","/v3/phase6/runs/"+run_id)
        self.assertEqual(status,200); self.assertEqual(stored["result"]["composition"],result["composition"])
        status,replay=self.app.dispatch("POST","/v3/phase6/runs/"+run_id+"/replay",{})
        self.assertEqual(status,200); self.assertTrue(replay["deterministic_match"],replay)
    def test_run_list_and_invalid_input(self):
        self.app.dispatch("POST","/v3/phase6/compose",self.request())
        status,result=self.app.dispatch("GET","/v3/phase6/runs?limit=10")
        self.assertEqual(status,200); self.assertEqual(result["count"],1)
        request=self.request(); request["graph"]["nodes"][0]["span"]={"start":0,"end":999}
        status,result=self.app.dispatch("POST","/v3/phase6/compose",request)
        self.assertEqual(status,400); self.assertEqual(result["error"]["code"],"PHASE6_COMPOSE_INVALID")

if __name__=="__main__": unittest.main()
