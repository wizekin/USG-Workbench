"""Phase 6 candidate run persistence, API, CLI and generated contract benchmark."""
import json
import sqlite3
import unittest
from tools.phase6_broader_semantics_v0_1.engine import compose, project_loss_aware
from tools.phase6_broader_semantics_v0_1.runs import SQLitePhase6CandidateRunStore, Phase6RunIntegrityError
from tools.phase6_broader_semantics_v0_1.benchmark import run_benchmark

class Phase6IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.connection=sqlite3.connect(":memory:")
        self.connection.row_factory=sqlite3.Row
        self.connection.execute("BEGIN")
        self.store=SQLitePhase6CandidateRunStore(self.connection)
        self.source="Lina and Omar read books."
        self.graph={"nodes":[{"id":"lina","kind":"PERSON","span":{"start":0,"end":4}},{"id":"omar","kind":"PERSON","span":{"start":9,"end":13}}],"relations":[{"type":"AND","source":"lina","target":"omar","feature":"COORDINATION","evidence":{"start":5,"end":8}}],"clauses":[],"operators":[],"references":[],"provenance":[{"rule_id":"fixture.rule","resource_id":"fixture.resource"}],"features":["COORDINATION"]}
        self.result=compose(self.source,"en",self.graph)
        self.manifest="a"*64
    def tearDown(self): self.connection.close()
    def test_append_only_round_trip_and_replay_inputs(self):
        metadata=self.store.put(self.source,"en",self.graph,self.result,self.manifest)
        stored=self.store.get(metadata["run_id"])
        self.assertEqual(stored["input"],{"source":self.source,"language":"en","graph":self.graph})
        self.assertEqual(stored["result"],self.result)
        self.assertEqual(self.store.put(self.source,"en",self.graph,self.result,self.manifest)["status"],"UNCHANGED")
    def test_run_records_cannot_be_updated_or_deleted(self):
        metadata=self.store.put(self.source,"en",self.graph,self.result,self.manifest)
        with self.assertRaises(sqlite3.IntegrityError): self.connection.execute("UPDATE usg_phase6_candidate_run SET result_sha256=? WHERE run_id=?",("b"*64,metadata["run_id"]))
        with self.assertRaises(sqlite3.IntegrityError): self.connection.execute("DELETE FROM usg_phase6_candidate_run WHERE run_id=?",(metadata["run_id"],))
    def test_list_is_bounded(self):
        self.store.put(self.source,"en",self.graph,self.result,self.manifest)
        self.assertEqual(len(self.store.list(1)),1)
        with self.assertRaises(ValueError): self.store.list(0)
    def test_generated_bilingual_composition_benchmark_passes(self):
        report=run_benchmark()
        self.assertEqual(report["case_count"],10)
        self.assertEqual(report["failed"],0,report)
        self.assertFalse(report["raw_text_recognition_measured"])
        self.assertFalse(report["naturalistic_accuracy_claimed"])
    def test_projection_never_emits_canonical_document(self):
        projection=project_loss_aware(self.result)
        self.assertEqual(projection["status"],"NOT_PROJECTABLE")
        self.assertIsNone(projection["document"])

if __name__=="__main__": unittest.main()
