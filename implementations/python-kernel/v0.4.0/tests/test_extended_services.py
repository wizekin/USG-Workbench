import tempfile
import unittest
from usg.runtime import USG
from usg.validation.evaluation import EvidencePolicy,EvaluationProcess,sign_attestation
from usg.storage.partitions import DomainPartitions
from usg.errors import StorageError
from usg.encoding.optimizer import choose_plan
from usg.cognition.reasoner import KernelReasoner


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.s=USG();self.addCleanup(self.s.close)
        self.s.ingest('John ate an apple.')
        with self.s.db.read() as r:self.claim=r.scalar('SELECT full_hash FROM expression e JOIN assertion a ON a.content_id=e.node_id')
        self.keys={'a':('origin-a',b'a'*32),'b':('origin-b',b'b'*32)}
        self.e=EvaluationProcess(self.s,EvidencePolicy('TEST-EVIDENCE'),self.keys)

    def receipt(self,authority,verdict='SUPPORT'):
        origin,key=self.keys[authority]
        return sign_attestation(key,authority=authority,origin=origin,claim_hash=self.claim,verdict=verdict,issued_at=self.s.db.clock.now())

    def test_independent_authenticated_evidence_reaches_trusted_view(self):
        result=self.e.evaluate(1,[self.receipt('a'),self.receipt('b')])
        self.assertEqual(result['decision'],'VERIFIED')
        self.assertEqual(len(self.s.query(view='trusted')),1)

    def test_repetition_or_forged_evidence_does_not_promote(self):
        a=self.receipt('a');forged={**self.receipt('b'),'signature':'bad'}
        self.assertEqual(self.e.evaluate(1,[a,a,forged])['decision'],'DEFERRED')
        self.assertEqual(self.s.query(view='trusted'),[])

    def test_authenticated_contradiction_removes_trusted_eligibility(self):
        self.e.evaluate(1,[self.receipt('a'),self.receipt('b')])
        self.assertEqual(self.e.evaluate(1,[self.receipt('a','CONTRADICT')])['decision'],'DISPUTED')
        self.assertEqual(self.s.query(view='trusted'),[])

    def test_stale_attestations_and_other_claims_are_rejected(self):
        receipts=[]
        for authority in self.keys:
            origin,key=self.keys[authority]
            receipts.append(sign_attestation(key,authority=authority,origin=origin,claim_hash=self.claim,verdict='SUPPORT',issued_at=self.s.db.clock.now()-1000000))
        self.assertEqual(self.e.evaluate(1,receipts)['decision'],'DEFERRED')


class PhysicalAndReasoningTests(unittest.TestCase):
    def test_partition_versions_and_global_ids_survive_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            with DomainPartitions(td,max_open=1) as p:
                p.publish('medicine',1,[{'space':'CONCEPT','id':7,'body':{'label':'Doctor'}}])
                p.publish('medicine',2,[{'space':'CONCEPT','id':7,'body':{'label':'Doctor v2'}}])
                self.assertEqual(p.get('medicine','CONCEPT',7)['label'],'Doctor v2')
                self.assertEqual(p.get('medicine','CONCEPT',7,version=1)['label'],'Doctor')
                with self.assertRaises(StorageError):p.publish('medicine',1,[])
            with DomainPartitions(td) as p:self.assertEqual(p.get('medicine','CONCEPT',7)['label'],'Doctor v2')

    def test_optimizer_checks_both_codecs_and_exact_semantics(self):
        report=choose_plan([{'x':'repeat','n':i} for i in range(50)],block_sizes=(1024,4096))
        self.assertEqual(len(report['trials']),4)
        self.assertEqual(report['semantic_changes'],0)

    def test_completed_transfer_has_possession_effect_not_ownership(self):
        with USG() as s:
            s.ingest('John has given Mary a book.')
            facts=KernelReasoner(s).run(view='source')['state_entailments']
            self.assertTrue(any(x['relation']=='HOLDS' and x['arguments'][-1]=='POSSESSION' for x in facts),facts)
            self.assertFalse(any(x['relation']=='OWNS' for x in facts))

    def test_negated_or_intended_effect_never_escapes_context(self):
        with USG() as s:
            s.ingest('John has not given Mary a book.')
            s.ingest('John wants to open the door.')
            self.assertEqual(KernelReasoner(s).run(view='source')['state_entailments'],[])


if __name__=='__main__':unittest.main()
