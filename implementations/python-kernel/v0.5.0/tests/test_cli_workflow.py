import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def cli(*args):
    env={**os.environ,'PYTHONIOENCODING':'utf-8'}
    env.pop('USG_LOCAL_MODEL',None)
    env.pop('USG_BIG_ENABLED',None)
    return subprocess.run([sys.executable,'-m','usg',*map(str,args)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)


class WorkflowTests(unittest.TestCase):
    def test_complete_offline_cli_workflow(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'a.db'
            result=cli('ingest','--db',db,'--text','The doctor gave the patient medication.','--compact')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['counts'],{'RESOLVED':1})
            result=cli('query','--db',db,'--frame','GIVE')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(json.loads(result.stdout)),1)
            result=cli('reason','--db',db,'--view','source')
            self.assertTrue(json.loads(result.stdout)['inferences'])
            self.assertEqual(cli('verify','--db',db).returncode,0)
            export=Path(td)/'export.usbf'
            result=cli('export','--db',db,'--output',export)
            self.assertEqual(result.returncode,0,result.stderr)
            result=cli('import','--db',Path(td)/'b.db','--file',export)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['imported_trusted_claims'],0)

    def test_inbox_cli_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            inbox=Path(td)/'inbox';inbox.mkdir()
            (inbox/'a.txt').write_text('John ate an apple.\nThe florb quuxed.',encoding='utf-8')
            db=Path(td)/'x.db'
            result=cli('run','--db',db,'--input',inbox)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['jobs']['completed'],1)
            result=cli('run','--db',db,'--input',inbox)
            self.assertEqual(json.loads(result.stdout)['jobs']['completed'],0)

    def test_arabic_cli_has_utf8_output_and_codepoint_spans(self):
        with tempfile.TemporaryDirectory() as td:
            result=cli('ingest','--db',Path(td)/'x.db','--language','ar','--text','الولد أكل التفاحة.','--compact')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['counts'],{'RESOLVED':1})

    def test_errors_are_machine_readable_without_tracebacks(self):
        result=cli('ingest','--text','','--db',':memory:')
        self.assertEqual(result.returncode,1)
        self.assertIn('error',json.loads(result.stderr))
        self.assertNotIn('Traceback',result.stderr)


if __name__=='__main__':unittest.main()
