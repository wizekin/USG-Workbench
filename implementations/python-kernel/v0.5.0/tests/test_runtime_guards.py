import dataclasses
import json
import random
import struct
import unittest

from usg.autonomy.panel import AutomatedPanel,Verdict,wilson_upper
from usg.autonomy.policy import ActionClass,VerifierClass as VC
from usg.config import Config,BigModelConfig,LocalModelConfig
from usg.cognition.controller import TaskQueue,Workspace,ResourceGovernor
from usg.cognition.memory import MemoryManager
from usg.concepts.identity import Definition,compare
from usg.core.values import Sensitivity
from usg.encoding.usbf import (BLOCK,FOOTER,HEADER,MAX_BLOCK,DecodeError,Reader,decode,encode,read_varint,varint,zigzag,unzigzag)
from usg.errors import BudgetExceeded,InvariantViolation,PolicyDenied
from usg.grammar.node import ref,var,relate
from usg.learning.dsl import RuleProposal
from usg.learning.engine import LearningEngine,bounded_match
from usg.models.gateway import BigGateway,LocalGateway
from usg.security.text import normalize,segment
from usg.runtime import USG
from usg.util import FakeClock
from usg.storage.database import Database


class BinaryTests(unittest.TestCase):
    def test_varints_roundtrip_and_reject_overlong_truncation_overflow(self):
        for n in (0,1,127,128,16383,16384,2**32,2**64-1):
            self.assertEqual(read_varint(varint(n)),(n,len(varint(n))))
        for b in (b'',b'\x80',b'\x80\x00',b'\xff'*11,b'\xff'*9+b'\x02'):
            with self.subTest(b=b),self.assertRaises(DecodeError):
                read_varint(b)
        for n in (-1,2**64,True,1.5):
            with self.assertRaises(ValueError): varint(n)

    def test_zigzag_signed_range(self):
        for n in (-(2**63),-100,-1,0,1,2**63-1):
            self.assertEqual(unzigzag(zigzag(n)),n)

    def test_multiblock_exact_roundtrip_and_random_access(self):
        records=[{'id':n,'value':'αβ😃'*80} for n in range(100)]
        data=encode(records,block_size=1024)
        reader=Reader(data)
        self.assertGreater(len(reader.metadata['blocks']),10)
        self.assertEqual(list(reader.records()),records)
        self.assertTrue(all(x in records for x in reader.block(2)))

    def test_empty_container(self):
        self.assertEqual(decode(encode([])),[])

    def test_unknown_version_flags_and_pin_rejected(self):
        for offset in (4,5,6,8):
            b=bytearray(encode([{'x':1}]))
            b[offset]=42
            with self.assertRaises(DecodeError):decode(bytes(b))

    def test_truncated_files_never_escape_as_raw_exceptions(self):
        b=encode([{'hello':'world'}])
        for n in range(len(b)):
            with self.assertRaises(DecodeError):decode(b[:n])

    def test_checksums_and_decompression_length_enforced(self):
        b=bytearray(encode([{'hello':'world'}]))
        header_end=read_varint(b,HEADER.size)[1]
        struct.pack_into('<I',b,header_end+4,MAX_BLOCK+1)
        with self.assertRaises(DecodeError):decode(bytes(b))
        b=bytearray(encode([{'hello':'world'}]))
        b[header_end+BLOCK.size] ^= 255
        with self.assertRaises(DecodeError):decode(bytes(b))

    def test_bounded_hostile_input_fuzz(self):
        rng=random.Random(440)
        base=encode([{'expression':{'op':'REF','params':{'ref':'REFERENT:1'}}}])
        accepted=0
        for _ in range(500):
            b=bytearray(base)
            for j in range(rng.randint(1,5)):
                b[rng.randrange(len(b))]=rng.randrange(256)
            try:
                result=decode(bytes(b))
                # Mutating non-semantic UUID/timestamp bytes may be harmless.
                self.assertEqual(result,decode(base))
                accepted+=1
            except DecodeError:pass
        self.assertLess(accepted,100)

    def test_deep_payload_rejected(self):
        x={}
        for _ in range(100):x={'x':x}
        with self.assertRaises(DecodeError):encode([x])


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.clock=FakeClock()
        self.db=Database(clock=self.clock);self.db.migrate()
        self.addCleanup(self.db.close)

    def test_queue_leases_survive_crash_and_fence_stale_workers(self):
        q=TaskQueue(self.db)
        q.enqueue('x','AUDIT',{})
        first=q.claim(lease_seconds=2)
        self.clock.advance(3)
        second=q.claim()
        self.assertEqual(second.id,first.id)
        self.assertNotEqual(second.token,first.token)
        with self.assertRaises(InvariantViolation):q.finish(first)
        q.finish(second,{'ok':True})
        self.assertIsNone(q.claim())

    def test_dead_letter_after_bounded_failures(self):
        q=TaskQueue(self.db)
        q.enqueue('x','AUDIT',{},max_attempts=2)
        q.finish(q.claim(),error='failure')
        self.clock.advance(100)
        q.finish(q.claim(),error='failure')
        self.clock.advance(100)
        self.assertIsNone(q.claim())
        with self.db.read() as r:self.assertEqual(r.scalar('SELECT state FROM task_queue'),'DEAD')

    def test_queue_capacity_and_idempotency(self):
        q=TaskQueue(self.db,capacity=1)
        first=q.enqueue('a','AUDIT',{})
        self.assertEqual(q.enqueue('a','AUDIT',{}),first)
        with self.assertRaises(BudgetExceeded):q.enqueue('b','AUDIT',{})

    def test_workspace_compare_and_swap_and_capacity(self):
        w=Workspace(self.db,capacity=2)
        self.assertEqual(w.snapshot('x'),(0,[]))
        self.assertEqual(w.commit('x',0,['SOURCE:1']),1)
        with self.assertRaises(InvariantViolation):w.commit('x',0,['SOURCE:2'])
        with self.assertRaises(InvariantViolation):w.commit('x',1,['W:t:1'])
        with self.assertRaises(InvariantViolation):w.commit('x',1,['1','2','3'])

    def test_resource_degradation_and_derived_cache_dependencies(self):
        g=ResourceGovernor()
        self.assertEqual(g.plan(input_chars=200001),'DEFER')
        self.assertEqual(g.plan(input_chars=10,free_ram_mb=256),'RULES_ONLY')
        m=MemoryManager(self.db)
        m.cache_inference('q',{'rule':'1'},[1])
        self.assertEqual(m.get_cached('q',{'rule':'1'}),[1])
        self.assertIsNone(m.get_cached('q',{'rule':'2'}))
        self.assertAlmostEqual(m.heat(1,7),.5)

    def test_panel_requires_distinct_classes_not_multiple_model_votes(self):
        panel=AutomatedPanel({VC.LOCAL_MODEL_SECOND_OPINION:lambda c:Verdict(VC.LOCAL_MODEL_SECOND_OPINION,True,'proof')})
        self.assertFalse(panel.evaluate(ActionClass.INTERP_RULE,{},rollback_plan=True,canary_complete=True).approved)

    def test_panel_hard_veto_blocks_quorum(self):
        kinds=(VC.DETERMINISTIC_REPLAY,VC.REGRESSION_SUITE,VC.SYNTHETIC_HELDOUT,VC.METAMORPHIC)
        verifiers={v:lambda c,v=v:Verdict(v,True,'hash') for v in kinds}
        panel=AutomatedPanel(verifiers)
        self.assertTrue(panel.evaluate(ActionClass.INTERP_RULE,{},rollback_plan=True,canary_complete=True).approved)
        verifiers[VC.COUNTEREXAMPLE]=lambda c:Verdict(VC.COUNTEREXAMPLE,False,'counterexample',hard_failure=True)
        self.assertFalse(AutomatedPanel(verifiers).evaluate(ActionClass.INTERP_RULE,{},rollback_plan=True,canary_complete=True).approved)

    def test_unattended_forbidden_and_shadow_actions_never_activate(self):
        for action in (ActionClass.PHYSICAL_MERGE,ActionClass.UNIVERSAL_CLAIM,ActionClass.FOUNDATIONAL_RULE_CHANGE,ActionClass.FRAME_FUNDAMENTAL):
            self.assertFalse(AutomatedPanel().evaluate(action,{}).approved)

    def test_wilson_uncalibrated_is_maximum_risk(self):
        self.assertEqual(wilson_upper(0,0),1)
        self.assertLess(wilson_upper(0,200),.05)
        self.assertGreater(wilson_upper(1,10),wilson_upper(0,10))

    def test_calibration_rejects_nonfinite_and_wrong_types(self):
        for value in (float('nan'),float('inf'),True,'1'):
            with self.assertRaises(InvariantViolation):Config().calibrate('tau_low',value,'run')

    def test_normalization_offsets_keep_original_unicode(self):
        n=normalize('e\u0301\r\n😃')
        self.assertEqual(n.text,'é\n😃')
        self.assertEqual(n.original_span(0,1),SpanForTest(0,2))


def SpanForTest(a,b):
    from usg.core.spans import Span
    return Span(a,b)


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.db=Database(clock=FakeClock());self.db.migrate();self.addCleanup(self.db.close)
        self.calls=[]

    def transport(self,*args):
        self.calls.append(args)
        return {'choices':[{'message':{'content':json.dumps({'findings':[{'code':'FRAME_GAP','effect':'RAISE_RISK_FLOOR'}]})}}]}

    def test_defaults_make_no_network_calls(self):
        result=BigGateway(self.db,backend=BigModelConfig(),transport=self.transport).analyze('GENERAL_ISSUE_ANALYSIS',{'FRAME_GAP':20})
        self.assertFalse(result.ok);self.assertEqual(self.calls,[])
        self.assertFalse(LocalGateway(transport=self.transport).choose('FRAME_SELECTION','source',['GIVE']).ok)

    def test_remote_accepts_only_aggregates_and_two_general_tasks(self):
        cfg=BigModelConfig(True,'https://example.invalid/v1','free-model')
        g=BigGateway(self.db,backend=cfg,transport=self.transport)
        self.assertFalse(g.analyze('INTERPRET_SENTENCE',{'FRAME_GAP':20}).ok)
        self.assertFalse(g.analyze('GENERAL_ISSUE_ANALYSIS',{'text':'sensitive source'}).ok)
        self.assertTrue(g.analyze('GENERAL_ISSUE_ANALYSIS',{'FRAME_GAP':20}).ok)
        self.assertEqual(len(self.calls),1)
        self.assertNotIn('source_data',json.dumps(self.calls))
        self.assertFalse(g.analyze('GENERAL_ISSUE_ANALYSIS',{'FRAME_GAP':20}).ok)
        self.assertEqual(len(self.calls),1)

    def test_failed_requests_count_and_open_circuit_breaker(self):
        def broken(*args):raise OSError('offline')
        g=BigGateway(self.db,backend=BigModelConfig(True,'https://example.invalid/v1','free'),transport=broken)
        self.assertFalse(g.analyze('GENERAL_ISSUE_ANALYSIS',{'FRAME_GAP':20}).ok)
        self.assertEqual(g.ledger.usage_summary('big')['calls_24h'],1)
        self.assertGreater(g.ledger.usage_summary('big')['cooldown_until'],self.db.clock.now())

    def test_remote_findings_cannot_relax_validation(self):
        def bad(*args):return {'choices':[{'message':{'content':'{"findings":[{"code":"FRAME_GAP","effect":"SKIP_VALIDATION"}]}'}}]}
        g=BigGateway(self.db,backend=BigModelConfig(True,'https://example.invalid/v1','free'),transport=bad)
        self.assertFalse(g.analyze('GENERAL_ISSUE_ANALYSIS',{'FRAME_GAP':20}).ok)

    def test_local_rejects_nonloopback_and_caches_closed_choices(self):
        def reply(*args):self.calls.append(args);return {'message':{'content':'{"choice":"GIVE"}'}}
        remote=LocalGateway(LocalModelConfig('ollama','https://example.com','tiny'),transport=reply)
        self.assertFalse(remote.choose('FRAME_SELECTION','x',['GIVE']).ok)
        self.assertEqual(self.calls,[])
        local=LocalGateway(LocalModelConfig('ollama','http://127.0.0.1:11434','tiny'),transport=reply)
        self.assertTrue(local.choose('FRAME_SELECTION','x',['GIVE']).ok)
        self.assertTrue(local.choose('FRAME_SELECTION','x',['GIVE']).cached)
        self.assertEqual(len(self.calls),1)

    def test_local_output_cannot_invent_frames(self):
        def bad(*args):return {'message':{'content':'{"choice":"NEW_FRAME"}'}}
        g=LocalGateway(LocalModelConfig('ollama',model='tiny'),transport=bad)
        self.assertFalse(g.choose('FRAME_SELECTION','source',['GIVE']).ok)


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.s=USG();self.addCleanup(self.s.close)
        self.engine=LearningEngine(self.s.db,Config({'canary_units':20}))

    def proposal(self):
        return RuleProposal('CONSUMED_EAT','consumed','ate',('John consumed an apple.','Mary consumed bread.'),
                            ('John consumed a florb.','John consumed an apple and Mary consumed bread.'),
                            (('John consumed an apple.','John did not consume an apple.'),))

    def test_rule_dsl_rejects_executable_and_privileged_fields(self):
        d=self.proposal().to_json()
        for field,value in (('python','print(1)'),('trust','TRUSTED')):
            with self.assertRaises(InvariantViolation):RuleProposal.from_json({**d,field:value})
        with self.assertRaises(InvariantViolation):dataclasses.replace(self.proposal(),trigger='.*')

    def test_scoped_definition_comparison_does_not_merge_similar_labels(self):
        a=Definition(1,'ENTITY','medicine',frozenset({'A'}),True,'DEFINITIONAL')
        b=dataclasses.replace(a,concept_id=2)
        self.assertEqual(compare(a,b).grade,'ESTABLISHED')
        self.assertEqual(compare(a,dataclasses.replace(b,complete=False)).relation,'UNDETERMINED')
        self.assertEqual(compare(a,dataclasses.replace(b,scope='engineering')).relation,'UNDETERMINED')
        self.assertNotEqual(compare(a,dataclasses.replace(b,provenance='EMPIRICAL')).grade,'ESTABLISHED')

    def test_matcher_preserves_variable_identity_and_budget(self):
        p=relate('KNOWS',var('x'),var('x'))
        self.assertIsNone(bounded_match(p,relate('KNOWS',ref('REFERENT:1'),ref('REFERENT:2'))))
        self.assertIsNotNone(bounded_match(p,relate('KNOWS',ref('REFERENT:1'),ref('REFERENT:1'))))
        with self.assertRaises(InvariantViolation):bounded_match(p,p,max_steps=1)

    def test_automatic_proposal_tests_canary_activation_and_rollback(self):
        p=self.proposal()
        cid=self.engine.propose(p)
        self.assertEqual(self.engine.propose(p),cid)
        staged=self.engine.stage_rule(cid)
        self.assertTrue(staged['staged'],staged)
        self.assertEqual(self.engine.active_aliases(),{})
        for _ in range(200):state=self.engine.observe_canary(staged['bundle_id'])
        self.assertEqual(state,'ACTIVE')
        self.assertEqual(self.engine.active_aliases(),{'consumed':'ate'})
        self.engine.rollback(staged['bundle_id'],'counterexample')
        self.assertEqual(self.engine.active_aliases(),{})

    def test_vetoed_proposal_never_reappears(self):
        cid=self.engine.propose(self.proposal())
        self.engine.veto(cid,'unsupported origin')
        self.assertEqual(self.engine.propose(self.proposal()),cid)
        with self.assertRaises(PolicyDenied):self.engine.stage_rule(cid)

    def test_unvetted_semantic_alias_is_deferred_without_human_review(self):
        p=dataclasses.replace(self.proposal(),name='UNKNOWN_ALIAS',trigger='munched',
                              positive=('John munched an apple.','Mary munched bread.'))
        cid=self.engine.propose(p)
        result=self.engine.stage_rule(cid)
        self.assertFalse(result['staged'])
        self.assertEqual(result['reason'],'NO_INDEPENDENT_LEXICAL_PROOF')

    def test_quantified_description_does_not_create_particular_subject(self):
        self.s.ingest('Every doctor opened the door.')
        with self.s.db.read() as r:
            self.assertEqual(r.scalar('SELECT COUNT(*) FROM referent'),1)

    def test_automatic_source_probation_never_grants_trusted(self):
        from usg.cognition.worker import Worker
        self.s.config=Config({'probation_clean_units':10})
        self.s.ingest('\n'.join('John ate an apple.' for _ in range(10)),trust_tier='QUARANTINE')
        self.assertEqual(Worker(self.s).probation(),1)
        with self.s.db.read() as r:
            self.assertEqual(r.scalar('SELECT trust_tier FROM source'),'STANDARD')

    def test_active_rule_regression_rolls_back_automatically_during_ingest(self):
        cid=self.engine.propose(self.proposal())
        staged=self.engine.stage_rule(cid)
        for _ in range(200):self.engine.observe_canary(staged['bundle_id'])
        self.assertTrue(self.engine.active_aliases())
        self.s.ingest('John consumed an argument.')
        self.assertEqual(self.engine.active_aliases(),{})
        self.assertEqual(self.s.query(),[])


if __name__=='__main__':unittest.main()
