"""Acceptance and adversarial coverage for the seven implementation workstreams."""
import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from usg.config import Config
from usg.concepts.definitions import Constraint, DefinitionStore
from usg.cognition.controller import TaskQueue, ResourceGovernor
from usg.cognition.resources import ResourceSnapshot, decide
from usg.cognition.worker import Worker
from usg.cognition.reasoner import KernelReasoner
from usg.core.records import Source
from usg.core.spans import Span
from usg.encoding import templates
from usg.encoding.compact import dumps as compact_dumps
from usg.encoding.linked_data import graph, to_turtle
from usg.encoding.optimizer import choose_plan
from usg.encoding.usbf import DecodeError, decode, encode
from usg.errors import InvariantViolation, PolicyDenied
from usg.grammar.node import apply, assert_, holds, kind, not_, prop, ref, relate, value, var, walk
from usg.interpretation.dependencies import ConlluAnalysis, DependencyInterpreter
from usg.interpretation.resources import LexicalResource
from usg.learning.engine import LearningEngine, bounded_match
from usg.learning.semantic import SemanticLearner, anti_unify, test_generalization
from usg.runtime import USG
from usg.storage.database import Database
from usg.storage.schema import WriterRole as W
from usg.util import FakeClock
from usg.validation.calibration import Calibrator
from usg.validation.contextual import ContextualValidator, ConflictIndex, index_claim, world_atoms
from usg.validation.evaluation import EvidencePolicy, EvaluationProcess


class DefinitionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.s=USG();self.addCleanup(self.s.close)
        self.definitions=DefinitionStore(self.s)
        self.c=Constraint(relate('INSTANCE_OF',var('self'),kind('Person')))

    def test_versions_are_immutable_and_stale_writes_fail(self):
        first=self.definitions.publish('Doctor','medicine',[self.c],complete=True)
        self.assertEqual(first,self.definitions.publish('Doctor','medicine',[self.c],complete=True))
        changed=Constraint(relate('INSTANCE_OF',var('self'),kind('Entity')))
        with self.assertRaises(InvariantViolation):self.definitions.publish('Doctor','medicine',[changed])
        second=self.definitions.publish('Doctor','medicine',[changed],expected_version=1)
        self.assertNotEqual(first,second)
        self.assertEqual(self.definitions.get('Doctor','medicine',1)['superseded_by'],second)
        self.assertTrue(self.s.audit_store()['ok'])
        with self.s.db.write(W.PROMOTION) as t:
            with self.assertRaises(Exception):t.execute("UPDATE definition_constraint SET expr='{}'")

    def test_only_defining_essential_constraints_inherit(self):
        self.definitions.publish('Person','medicine',[self.c,Constraint(prop(var('self'),'AgeGroup',value('Young')),'TYPICAL','EMPIRICAL')])
        inherited=self.definitions.inherit('Doctor','medicine')
        self.assertEqual(len(inherited),1)
        self.assertEqual(self.definitions.inherit('Doctor','engineering'),[])

    def test_empirical_definitions_cannot_define_identity(self):
        with self.assertRaises(PolicyDenied):Constraint(self.c.expression,provenance='EMPIRICAL')
        self.definitions.publish('Doctor','medicine',[self.c])
        self.assertFalse(self.definitions.identity_definition('Doctor','medicine').complete)

    def test_free_variables_and_instance_identifiers_are_rejected(self):
        for expression in (relate('INSTANCE_OF',ref('REFERENT:1'),kind('Person')),relate('INSTANCE_OF',var('other'),kind('Person'))):
            with self.assertRaises(PolicyDenied):self.definitions.publish('Doctor','medicine',[Constraint(expression)])

    def test_definition_inference_is_scoped_to_domain_model(self):
        self.definitions.publish('Person','medicine',[self.c])
        self.s.ingest('The doctor examined the patient.')
        plain=KernelReasoner(self.s).run(view='source')
        self.assertEqual(plain['definition_entailments'],[])
        facts=KernelReasoner(self.s).run(view='source',scope='medicine')['definition_entailments']
        self.assertTrue(facts)
        self.assertTrue(all(f['eval_context']=='DOMAIN_MODEL' for f in facts))


class ContextAndCalibrationTests(unittest.TestCase):
    def test_l5_is_reported_without_fabricated_panel_agreement(self):
        with USG() as s:
            result=s.ingest('John ate an apple.')
            checks={r['check']:r['result'] for r in result['units'][0]['validation']['results']}
            self.assertEqual(checks['VC-C01'],'PASS')
            self.assertEqual(checks['VC-C07'],'NOT_CHECKED')
            self.assertEqual(checks['VC-C05'],'NOT_CHECKED')

    def test_conflicts_require_same_referents_time_and_context(self):
        p=relate('INSTANCE_OF',ref('REFERENT:1'),kind('Person'))
        pos=list(world_atoms(assert_(p)))
        neg=list(world_atoms(assert_(not_(p))))
        other=list(world_atoms(assert_(relate('INSTANCE_OF',ref('REFERENT:2'),kind('Person')))))
        self.assertEqual(pos[0][0],neg[0][0]);self.assertNotEqual(pos[0][1],neg[0][1])
        self.assertNotEqual(pos[0][0],other[0][0])

    def test_negation_does_not_escape_quantifiers_or_modalities(self):
        from usg.grammar.node import modal, q
        p=relate('INSTANCE_OF',var('x'),kind('Person'))
        self.assertEqual(list(world_atoms(assert_(q('FORALL','x',p,p)))),[])
        self.assertEqual(list(world_atoms(assert_(modal('POSSIBILITY','EPISTEMIC',holds(apply('EAT',1,{})))))),[])

    def test_reused_signing_keys_cannot_fabricate_independence(self):
        with USG() as s:
            with self.assertRaises(ValueError):EvaluationProcess(s,EvidencePolicy('x'),{'a':('a',b'a'*32),'b':('b',b'a'*32)})

    def test_calibration_counts_origins_once_and_persists(self):
        with tempfile.TemporaryDirectory() as td:
            path=str(Path(td)/'x.db')
            with USG(path) as s:
                c=Calibrator(s.db,s.config)
                for i in range(50):c.observe(str(i),'easy',1.0,True,'same')
                self.assertFalse(c.report('easy')['calibrated'])
                for i in range(50):c.observe('new'+str(i),'easy',1.0,True,str(i))
                self.assertTrue(c.report('easy')['calibrated'])
                c.tune('activation_top_k',40,'run-1','easy')
                with self.assertRaises(InvariantViolation):c.tune('max_nesting_depth',10,'run-2','easy')
            with USG(path) as s:self.assertEqual(s.config['activation_top_k'],40)

    def test_calibration_detects_recent_drift(self):
        clock=FakeClock();db=Database(clock=clock);db.migrate()
        self.addCleanup(db.close);c=Calibrator(db,Config())
        for i in range(80):
            clock.advance(1);c.observe(str(i),'drift',1.0,i<40,str(i))
        self.assertTrue(c.report('drift')['drift'])
        with self.assertRaises(ValueError):c.tune('activation_top_k',40,'x','drift')


def conllu(rows):
    return '\n'.join('\t'.join(map(str,(i,form,lemma,upos,'_',features,head,rel,'_','_'))) for i,form,lemma,upos,features,head,rel in rows)+'\n'


class LanguageAdapterTests(unittest.TestCase):
    def test_resource_extends_vocabulary_and_preserves_existing_ambiguity(self):
        with USG() as base:
            resource=LexicalResource({'resource_id':'test','version':1,'entries':[
                {'language':'en','form':'surgeon','concepts':['Doctor']},
                {'language':'en','form':'bank','concepts':['Company']}]},base.foundation.ontology)
        with USG(resource=resource) as s:
            result=s.ingest('The surgeon examined the patient.')
            self.assertEqual(result['counts'],{'RESOLVED':1})
            self.assertTrue(s.audit_store()['ok'])
            self.assertEqual(set(resource.resolve('bank').concepts),{'Company','Organization','Location'})

    def test_resource_rejects_code_and_unknown_concepts(self):
        with USG() as s:
            for item in ({'resource_id':'x','version':1,'entries':[],'python':'print(1)'},
                         {'resource_id':'x','version':1,'entries':[{'language':'en','form':'x','concepts':['Ghost']}]}):
                with self.assertRaises(ValueError):LexicalResource(item,s.foundation.ontology)

    def test_dependency_adapter_compiles_noncanonical_word_order(self):
        text='An apple John ate.'
        rows=[(1,'An','an','DET','_',2,'det'),(2,'apple','apple','NOUN','_',4,'obj'),
              (3,'John','John','PROPN','_',4,'nsubj'),(4,'ate','eat','VERB','Tense=Past',0,'root'),(5,'.','.','PUNCT','_',4,'punct')]
        analysis=ConlluAnalysis(conllu(rows),text)
        with USG(analysis=analysis) as s:
            result=s.ingest(text)
            self.assertEqual(result['counts'],{'RESOLVED':1},result)
            self.assertEqual(len(s.query(frame='EAT',role='EATER',label='john')),1)
            self.assertTrue(s.audit_store()['ok'])

    def test_dependency_cycle_and_token_omission_fail_before_ingestion(self):
        for rows in ([(1,'John','John','PROPN','_',2,'nsubj'),(2,'ate','eat','VERB','_',1,'root')],
                     [(1,'John','John','PROPN','_',0,'root')]):
            with self.assertRaises(ValueError):ConlluAnalysis(conllu(rows),'John ate an apple.')

    def test_unhandled_dependency_is_not_silently_dropped(self):
        text='John ate an apple quickly.'
        rows=[(1,'John','John','PROPN','_',2,'nsubj'),(2,'ate','eat','VERB','_',0,'root'),
              (3,'an','an','DET','_',4,'det'),(4,'apple','apple','NOUN','_',2,'obj'),
              (5,'quickly','quickly','ADV','_',2,'advmod'),(6,'.','.','PUNCT','_',2,'punct')]
        with USG(analysis=ConlluAnalysis(conllu(rows),text)) as s:
            self.assertEqual(s.ingest(text)['counts'],{'UNRESOLVED':1})
            self.assertEqual(s.query(),[])


class LearningLifecycleTests(unittest.TestCase):
    def test_anti_unification_preserves_coreference_and_negative_contrasts(self):
        a=relate('PART_OF',ref('REFERENT:1'),ref('REFERENT:1'))
        b=relate('PART_OF',ref('REFERENT:2'),ref('REFERENT:2'))
        pattern=anti_unify(a,b)
        self.assertEqual(pattern.args[0],pattern.args[1])
        self.assertTrue(test_generalization(pattern,[a,b],[not_(a)])['passed'])
        self.assertIsNone(bounded_match(pattern,relate('PART_OF',ref('REFERENT:1'),ref('REFERENT:2'))))

    def test_generalization_requires_contrastive_evidence_and_budgets(self):
        p=relate('PART_OF',ref('REFERENT:1'),ref('REFERENT:2'))
        self.assertFalse(test_generalization(p,[p],[])['passed'])
        with self.assertRaises(ValueError):anti_unify(p,p,max_nodes=1)

    def activate(self,s):
        s.ingest('John consumed an apple.')
        engine=LearningEngine(s.db,s.config)
        ids=SemanticLearner(s).discover_aliases()
        self.assertTrue(ids)
        staged=engine.stage_rule(ids[0]);self.assertTrue(staged['staged'],staged)
        for i in range(200):engine.observe_canary(staged['bundle_id'],observation_key=str(i))
        return engine,staged['bundle_id']

    def test_automatic_alias_discovery_and_deduplicated_canary(self):
        with USG() as s:
            engine,bundle=self.activate(s)
            self.assertEqual(engine.active_aliases(),{'consumed':'ate'})
            before=None
            with s.db.read() as r:before=r.scalar('SELECT observations FROM promotion_bundle WHERE bundle_id=?',(bundle,))
            for i in range(5):engine.observe_canary(bundle,observation_key='0')
            with s.db.read() as r:self.assertEqual(r.scalar('SELECT observations FROM promotion_bundle WHERE bundle_id=?',(bundle,)),before)

    def test_rollback_invalidates_dependent_claims_and_reprocesses(self):
        with USG() as s:
            engine,bundle=self.activate(s)
            s.ingest('Mary consumed bread.')
            self.assertTrue(s.query(frame='EAT'))
            engine.rollback(bundle,'adversarial counterexample')
            self.assertEqual(s.query(),[])
            worker=Worker(s);self.assertGreater(worker.reprocess_invalidated(),0)
            self.assertGreater(worker.drain()['completed'],0)
            self.assertEqual(s.query(),[])
            self.assertTrue(s.audit_store()['ok'])


class RuntimeAndEncodingAcceptanceTests(unittest.TestCase):
    def test_resource_decisions_are_measured_and_conservative(self):
        governor=ResourceGovernor()
        self.assertEqual(decide(ResourceSnapshot(None,1000,None),governor),'RULES_ONLY')
        self.assertEqual(decide(ResourceSnapshot(100,1000,None),governor),'DEFER')
        self.assertEqual(decide(ResourceSnapshot(2000,10,None),governor),'DEFER')

    def test_memory_pressure_defers_without_consuming_a_lease(self):
        with USG() as s:
            worker=Worker(s);worker.queue.enqueue('x','INGEST',{'text':'John ate an apple.'})
            with patch('usg.cognition.worker.snapshot',return_value=ResourceSnapshot(64,1000,None)):
                self.assertEqual(worker.drain()['completed'],0)
            with s.db.read() as r:self.assertEqual(r.scalar('SELECT attempts FROM task_queue'),0)

    def test_aging_and_lease_renewal(self):
        clock=FakeClock();db=Database(clock=clock);db.migrate();self.addCleanup(db.close)
        queue=TaskQueue(db);first=queue.enqueue('old','AUDIT',{},priority=100)
        clock.advance(100*60+1);queue.enqueue('new','AUDIT',{},priority=0)
        task=queue.claim(lease_seconds=10);self.assertEqual(task.id,first)
        queue.renew(task,20);clock.advance(11);queue.finish(task)

    def test_template_round_trip_preserves_distinct_occurrences(self):
        records=[{'frame':'GIVE','roles':{'AGENT':i,'THEME':'book'},'event':i} for i in range(100)]
        self.assertEqual(templates.loads(templates.dumps(records)),records)
        self.assertEqual(decode(encode(records,codec='template')),records)
        report=choose_plan(records,block_sizes=(4096,),codecs=('json','compact','template'))
        self.assertEqual(len(report['trials']),3)

    def test_template_decoder_rejects_missing_extra_and_recursive_slots(self):
        for template,slots in ((['S'],[]),(['S'],[1,2]),(['R',0],[1]),(['S'],[{}])):
            data=compact_dumps({'profile':'USG-TEMPLATES-1','templates':[template],'records':[[0,slots]]})
            with self.assertRaises(DecodeError):templates.loads(data)

    def test_optimizer_skips_an_unrepresentable_compact_integer(self):
        result=choose_plan([{'large':2**100}],block_sizes=(1024,))
        self.assertEqual(result['selected']['codec'],'json')
        self.assertTrue(result['unavailable'])

    def test_function_inheritance_does_not_infer_an_entity_class(self):
        with USG() as s:
            s.ingest('The doctor examined the heart.')
            facts=KernelReasoner(s).run(view='source')['inferences']
            self.assertTrue(any(x['relation']=='HAS_FUNCTION' and x['object']=='FN.TRANSPORT' for x in facts),facts)
            self.assertFalse(any(x['relation']=='INSTANCE_OF' and x['object']=='Pump' for x in facts))

    def test_linked_data_preserves_opaque_ast_and_unique_installation_ids(self):
        with USG() as s:
            s.ingest('John wants to open the door.')
            document=graph(s);turtle=to_turtle(document)
            self.assertIn('wasDerivedFrom',turtle)
            self.assertIn('minCount',turtle)
            claims=[x for x in document['@graph'] if 'usg:payload' in x]
            self.assertEqual(len(claims),1)
            self.assertIn('WANT',claims[0]['usg:payload'])
            aid=claims[0]['@id']
        with USG() as s:
            s.ingest('John wants to open the door.')
            self.assertNotEqual(aid,next(x['@id'] for x in graph(s)['@graph'] if 'usg:payload' in x))


if __name__=='__main__':unittest.main()
