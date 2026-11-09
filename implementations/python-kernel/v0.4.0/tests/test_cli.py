import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run([sys.executable, "-m", "usg", *args], cwd=ROOT, capture_output=True, text=True)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.db = os.path.join(tempfile.mkdtemp(prefix="usg_cli_"), "x.db")

    def test_init_status_verify(self):
        r = run("init", "--db", self.db)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreater(json.loads(r.stdout)["sealed_modules"], 0)
        st = json.loads(run("status", "--db", self.db).stdout)
        self.assertTrue(st["seal_ok"])
        self.assertTrue(st["foundation_ok"])
        self.assertEqual((st["concepts"], st["frames"]), (81, 57))
        self.assertGreaterEqual(st["kernel_frames"], 20)
        self.assertTrue(st["audit_chain_ok"])
        self.assertFalse(st["big_model_configured"])
        self.assertEqual(run("verify", "--db", self.db).returncode, 0)

    def test_verify_fails_on_seal_tamper(self):
        run("init", "--db", self.db)
        c = sqlite3.connect(self.db)
        c.execute("UPDATE sealed_manifest SET sha256='00' WHERE name='usg.autonomy.policy'")
        c.commit()
        c.close()
        r = run("verify", "--db", self.db)
        self.assertEqual(r.returncode, 2)
        self.assertIn("SEAL FAILED", r.stderr)
        self.assertEqual(run("reseal", "--db", self.db).returncode, 0)
        self.assertEqual(run("verify", "--db", self.db).returncode, 0)

    def test_verify_fails_on_audit_tamper(self):
        run("init", "--db", self.db)
        c = sqlite3.connect(self.db)
        c.execute("DROP TRIGGER audit_no_update")
        c.execute("UPDATE audit_log SET detail='forged' WHERE seq=1")
        c.commit()
        c.close()
        r = run("verify", "--db", self.db)
        self.assertEqual(r.returncode, 3)

    def test_verify_fails_on_foundation_tamper(self):
        run("init", "--db", self.db)
        c = sqlite3.connect(self.db)
        c.execute("UPDATE concept SET doc='edited' WHERE canonical_label='Argument'")
        c.commit()
        c.close()
        r = run("verify", "--db", self.db)
        self.assertEqual(r.returncode, 4)
        self.assertIn("FOUNDATION", r.stderr)

    def test_init_is_idempotent(self):
        first = json.loads(run("init", "--db", self.db).stdout)
        second = json.loads(run("init", "--db", self.db).stdout)
        self.assertFalse(first["foundation_already_installed"])
        self.assertTrue(second["foundation_already_installed"])
        self.assertEqual(first["foundation_hash"], second["foundation_hash"])

    def test_policy_table(self):
        r = run("policy")
        self.assertEqual(r.returncode, 0)
        self.assertIn("FOUNDATIONAL_RULE_CHANGE", r.stdout)
        self.assertIn("FORBIDDEN", r.stdout)


if __name__ == "__main__":
    unittest.main()
