from contextlib import closing
import dataclasses
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from usg.acceptance import run
from usg.autonomy import seal
from usg.conformance import build,PARTS,STEPS
from usg.core.records import Source
from usg.core.spans import Span
from usg.foundation.install import install_foundation
from usg.grammar.node import and_,apply,aspect,assert_,holds,kind,not_,prop,ref,relate,speech_time,tense,time_lit,value
from usg.grammar.serialize import node_from_json
from usg.interpretation.parser import DeterministicInterpreter
from usg.release import upgrade
from usg.runtime import USG
from usg.storage.database import Database
from usg.storage import schema
from usg.storage.schema import WriterRole as W
from usg.validation.validator import Validator,ValidationContext
from usg.grammar.typecheck import Typechecker

ROOT=Path(__file__).resolve().parents[1]


class TraceabilityTests(unittest.TestCase):
    def test_all_twelve_parts_and_seven_steps_have_existing_modules_and_tests(self):
        import importlib
        for _,modules,tests in PARTS.values():
            for name in modules:self.assertTrue((ROOT/'usg'/name).is_file(),name)
            for target in tests:
                parts=target.split('.')
                module=importlib.import_module('.'.join(parts[:2]))
                if len(parts)>2:self.assertTrue(hasattr(module,parts[2]),target)
        self.assertEqual(len(STEPS),7)

    def test_requirements_retain_source_locations_without_inventing_conformance(self):
        report=build(ROOT/'SPECIFICATION.md')
        lines=(ROOT/'SPECIFICATION.md').read_text(encoding='utf8').splitlines()
        self.assertEqual(len(report['parts']),12)
        self.assertGreater(len(report['requirements']),300)
        self.assertFalse(report['full_conformance'])
        self.assertEqual(len({r['id'] for r in report['requirements']}),len(report['requirements']))
        for requirement in report['requirements']:
            self.assertEqual(lines[requirement['source_line']-1].strip(),requirement['statement'])


class ReleaseAcceptanceTests(unittest.TestCase):
    def test_packaged_acceptance_is_offline_and_passes(self):
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('network is forbidden')):
            report=run()
        self.assertTrue(report['passed'],report['checks'])
        self.assertEqual(report['models_used'],0)

    def test_schema_four_upgrade_preserves_identity_jobs_and_backup(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'old.db';backup=Path(td)/'backup.db'
            with Database(str(path)) as db:
                with patch.object(schema,'MIGRATIONS',[m for m in schema.MIGRATIONS if m[0]<=4]):db.migrate()
                install_foundation(db);seal.install_seal(db)
                with db.write(W.QUEUE) as t:
                    t.execute("INSERT INTO task_queue(dedup_key,kind,payload,state,priority,max_attempts,available_at) VALUES('legacy','AUDIT','{}','READY',10,3,0)")
                with db.read() as r:old_id=r.scalar("SELECT concept_id FROM concept WHERE canonical_label='Doctor'")
            result=upgrade(path,backup)
            self.assertTrue(result['upgraded'])
            with USG(path) as s:
                with s.db.read() as r:
                    self.assertEqual(r.scalar("SELECT concept_id FROM concept WHERE canonical_label='Doctor'"),old_id)
                    self.assertEqual(r.scalar('SELECT dedup_key FROM task_queue'),'legacy')
                self.assertTrue(s.audit_store()['ok'])
            with closing(sqlite3.connect(str(backup))) as c:self.assertEqual(c.execute('SELECT MAX(version) FROM schema_migration').fetchone()[0],4)

    def test_failed_post_upgrade_check_restores_prior_database(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'old.db';backup=Path(td)/'backup.db'
            with USG(path) as s:s.ingest('John ate an apple.')
            # First audit in packaged acceptance passes; the upgrade's audit fails.
            from usg.errors import StorageError
            with patch('usg.acceptance.run',return_value={'passed':True,'checks':[]}),patch.object(USG,'audit_store',return_value={'ok':False}):
                with self.assertRaises(StorageError):upgrade(path,backup)
            with USG(path) as s:
                self.assertEqual(len(s.query()),1)
                self.assertTrue(s.audit_store()['ok'])


class ContextRegressionTests(unittest.TestCase):
    def test_stored_derivation_replays_after_resource_is_not_configured(self):
        from usg.interpretation.resources import LexicalResource
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'resource.db'
            with USG() as initial:
                resource=LexicalResource({'resource_id':'replay','version':1,'entries':[{'language':'en','form':'surgeon','concepts':['Doctor']}]},initial.foundation.ontology)
            with USG(path,resource=resource) as s:s.ingest('The surgeon examined the patient.')
            with USG(path) as s:
                self.assertTrue(s.audit_store()['ok'])
                with s.db.write(W.CANDIDATE_STORE) as t:
                    payload=json.loads(t.scalar('SELECT payload FROM candidate'))
                    payload['lexical_resource']['entries'][0]['concepts']=['Person']
                    t.execute('UPDATE candidate SET payload=?',(json.dumps(payload),))
                self.assertFalse(s.audit_store()['ok'])

    def test_unavailable_contextual_service_never_reports_success(self):
        from usg.validation.contextual import ContextualValidator
        text='John ate an apple.'
        interpreted=DeterministicInterpreter().interpret(Source(text),Span(0,len(text)))
        context=ContextualValidator(panel_verifier=lambda candidate:(_ for _ in ()).throw(RuntimeError('offline')))
        results={x.check_id:x.result.value for x in context(interpreted.candidate)}
        self.assertEqual(results['VC-C07'],'UNCERTAIN')

    def test_question_never_becomes_a_world_assertion(self):
        with USG() as s:
            self.assertEqual(s.ingest('John ate an apple?')['counts'],{'UNRESOLVED':1})
            self.assertEqual(s.query(),[])

    def test_arabic_negation_and_diacritics_preserve_spans_and_context(self):
        with USG() as s:
            result=s.ingest('الولد لم يأكل التفاحة.',language='ar')
            self.assertEqual(result['counts'],{'RESOLVED':1},result)
            from usg.grammar.node import walk
            self.assertTrue(any(n.op=='NOT' for _,n in walk(node_from_json(s.query()[0]['expression']))))
            with s.db.read() as r:self.assertEqual(r.scalar("SELECT COUNT(*) FROM referent WHERE introduced_kind='WORLD'"),0)
            self.assertEqual(s.ingest('الطَّبِيبُ فَحَصَ المريض.',language='ar')['counts'],{'RESOLVED':1})
            self.assertTrue(s.audit_store()['ok'])

    def test_new_pipeline_supersedes_claims_and_reuses_world_mentions(self):
        text='John ate an apple. He opened the door.'
        with USG() as s:
            self.assertEqual(s.ingest(text)['counts'],{'RESOLVED':2})
            with s.db.read() as r:before=r.scalar('SELECT COUNT(*) FROM referent')
            # A real interpretation-affecting configuration change creates a
            # new pipeline checkpoint without merging two discourse people.
            s.config.override('alt_max_per_group',5)
            self.assertEqual(s.ingest(text)['counts'],{'RESOLVED':2})
            self.assertEqual(len(s.query()),2)
            self.assertEqual(len(s.query(view='all')),4)
            with s.db.read() as r:self.assertEqual(r.scalar('SELECT COUNT(*) FROM referent'),before)

    def test_past_operators_do_not_imply_identical_occurrence_times(self):
        with USG() as s:
            validator=Validator(ValidationContext(Typechecker(s.foundation.frames)))
            p=relate('PART_OF',ref('REFERENT:1'),ref('REFERENT:2'))
            failures=[]
            expression=assert_(and_(tense('PAST',speech_time(),p),tense('PAST',speech_time(),not_(p))))
            validator._logic(expression,lambda code,*args,**kwargs:failures.append(code))
            self.assertNotIn('VC-G03',failures)

    def test_essential_completed_effect_conflict_is_detected_in_one_context(self):
        with USG() as s:
            validator=Validator(ValidationContext(Typechecker(s.foundation.frames)))
            door=ref('REFERENT:1')
            completed=holds(aspect('PERFECT',apply('OPEN',1,{'AGENT':ref('REFERENT:2'),'UNDERGOER':door})))
            failures=[]
            validator._logic(assert_(and_(completed,prop(door,'Openness',value('ClosedState')))),lambda code,*args,**kwargs:failures.append(code))
            self.assertIn('VC-G05',failures)

    def test_jsonld_sources_reenter_quarantine_without_imported_trust(self):
        from usg.encoding.linked_data import graph,import_jsonld,to_trig
        with USG() as s:
            s.ingest('John ate an apple.')
            document=graph(s,mode='reversible')
            self.assertIn(':context> {',to_trig(document))
        with USG() as s:
            result=import_jsonld(s,document)
            self.assertEqual(result['reinterpreted_sources'],1)
            self.assertEqual(s.query(view='trusted'),[])
            with s.db.read() as r:self.assertEqual(r.scalar('SELECT trust_tier FROM source'),'QUARANTINE')


if __name__=='__main__':unittest.main()
