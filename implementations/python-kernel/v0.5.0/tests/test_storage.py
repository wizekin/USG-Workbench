import sqlite3
import threading
import unittest

from usg.core.ids import IdSpace, Ref
from usg.core.values import Component
from usg.errors import InvariantViolation, PolicyDenied, StorageError
from usg.storage.audit import GENESIS, verify_chain
from usg.storage.database import Database
from usg.storage.registry import IdRegistry
from usg.storage.schema import WriterRole
from tests.helpers import make_db


class DatabaseTests(unittest.TestCase):
    def test_migrate_is_idempotent(self):
        db, _ = make_db()
        self.assertEqual(db.migrate(), [])
        self.assertGreaterEqual(db.schema_version(), 1)

    def test_file_db_uses_wal_and_integrity_ok(self):
        db, _ = make_db(file=True)
        self.assertEqual(db.journal_mode(), "wal")
        self.assertTrue(db.integrity_check())
        with db.write(WriterRole.RELEASE) as t:
            t.execute("INSERT INTO meta(key,value) VALUES('k','v')")
        with db.read() as r:
            self.assertEqual(r.scalar("SELECT value FROM meta WHERE key='k'"), "v")
        db.checkpoint()

    def test_strict_tables_reject_wrong_types(self):
        db, _ = make_db()
        with self.assertRaises(sqlite3.IntegrityError):
            with db.write(WriterRole.REGISTRY) as t:
                t.execute("INSERT INTO id_sequence(space,next_id) VALUES('X','not-an-int')")

    def test_writer_roles_are_enforced(self):
        db, _ = make_db()
        with self.assertRaises(PolicyDenied):
            with db.write(WriterRole.CANDIDATE_STORE) as t:  # does not own id_sequence
                t.execute("INSERT INTO id_sequence(space,next_id) VALUES('CONCEPT',2)")
        with self.assertRaises(PolicyDenied):
            with db.write(WriterRole.LEDGER) as t:
                t.execute("DELETE FROM sealed_manifest")
        with self.assertRaises(PolicyDenied):  # DDL is never allowed in a write txn
            with db.write(WriterRole.RELEASE) as t:
                t.execute("DROP TABLE meta")
        with self.assertRaises(PolicyDenied):
            with db.write() as t:
                pass
        with self.assertRaises(PolicyDenied):  # read txn cannot write
            with db.read() as r:
                r.query("DELETE FROM meta")

    def test_rollback_on_error(self):
        db, _ = make_db()
        with self.assertRaises(RuntimeError):
            with db.write(WriterRole.RELEASE) as t:
                t.execute("INSERT INTO meta(key,value) VALUES('a','1')")
                raise RuntimeError("boom")
        with db.read() as r:
            self.assertIsNone(r.one("SELECT * FROM meta WHERE key='a'"))

    def test_with_cte_cannot_smuggle_writes(self):
        db, _ = make_db()
        with self.assertRaises(PolicyDenied):
            with db.read() as r:
                r.query("WITH x AS (SELECT 1) DELETE FROM meta")


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.db, self.clock = make_db()
        self.reg = IdRegistry()

    def alloc(self, space=IdSpace.CONCEPT, **kw):
        with self.db.write(WriterRole.REGISTRY) as t:
            return self.reg.allocate(t, space, record_kind=kw.pop("record_kind", "Concept"), **kw)

    def test_sequential_per_space(self):
        a, b = self.alloc(), self.alloc()
        f = self.alloc(IdSpace.FRAME, record_kind="Frame")
        self.assertEqual((a.n, b.n, f.n), (1, 2, 1))
        self.assertEqual(f.space, IdSpace.FRAME)

    def test_provisional_space(self):
        p = self.alloc(IdSpace.PROVISIONAL, record_kind="ProvisionalConcept")
        self.assertTrue(p.is_provisional)
        self.assertEqual(str(p), "P:1")

    def test_idempotent_allocation(self):
        a = self.alloc(idempotency_key="car|en|everyday")
        b = self.alloc(idempotency_key="car|en|everyday")
        c = self.alloc(idempotency_key="other")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        with self.assertRaises(InvariantViolation):
            self.alloc(IdSpace.FRAME, record_kind="Frame", idempotency_key="car|en|everyday")

    def test_only_registry_role_may_allocate(self):
        with self.assertRaises(PolicyDenied):
            with self.db.write(WriterRole.PROMOTION) as t:
                self.reg.allocate(t, IdSpace.CONCEPT, record_kind="Concept")

    def test_ids_never_reused_after_tombstone(self):
        a, b = self.alloc(), self.alloc()
        with self.db.write(WriterRole.REGISTRY) as t:
            self.reg.tombstone(t, a, replaced_by=b, reason="duplicate")
        c = self.alloc()
        self.assertEqual(c.n, 3)
        with self.db.read() as r:
            self.assertEqual(self.reg.resolve_status(r, a), "TOMBSTONE")
            self.assertEqual(self.reg.resolve_status(r, b), "ACTIVE")
            self.assertEqual(self.reg.resolve_status(r, Ref(IdSpace.CONCEPT, 99)), "UNKNOWN")
            e = self.reg.get(r, a)
            self.assertEqual(e.replaced_by, b)
        with self.assertRaises(InvariantViolation):
            with self.db.write(WriterRole.REGISTRY) as t:
                self.reg.tombstone(t, a)
        with self.assertRaises(InvariantViolation):
            with self.db.write(WriterRole.REGISTRY) as t:
                self.reg.set_status(t, a, "PROMOTED")
        with self.assertRaises(StorageError):
            with self.db.read() as r:
                self.reg.require_resolvable(r, Ref(IdSpace.CONCEPT, 77))

    def test_rollback_leaves_no_phantom_allocation(self):
        with self.assertRaises(RuntimeError):
            with self.db.write(WriterRole.REGISTRY) as t:
                self.reg.allocate(t, IdSpace.CONCEPT, record_kind="Concept")
                raise RuntimeError("abort")
        with self.db.read() as r:
            self.assertEqual(self.reg.count(r, IdSpace.CONCEPT), 0)
        self.assertEqual(self.alloc().n, 1)

    def test_tombstone_is_audited(self):
        a = self.alloc()
        with self.db.write(WriterRole.REGISTRY) as t:
            self.reg.tombstone(t, a, reason="x")
        with self.db.read() as r:
            rows = r.query("SELECT * FROM audit_log")
        self.assertEqual([x["event"] for x in rows], ["ID_TOMBSTONED"])

    def test_concurrent_allocation_is_unique_and_gap_free(self):
        db, _ = make_db(file=True)
        reg = IdRegistry()
        out, errs = [], []

        def worker():
            try:
                for _ in range(25):
                    with db.write(WriterRole.REGISTRY) as t:
                        out.append(reg.allocate(t, IdSpace.CONCEPT, record_kind="Concept").n)
            except Exception as e:  # pragma: no cover
                errs.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(errs, [])
        self.assertEqual(len(out), 200)
        self.assertEqual(sorted(out), list(range(1, 201)))

    def test_concurrent_idempotent_proposals_yield_one_id(self):
        db, _ = make_db(file=True)
        reg = IdRegistry()
        out = []

        def worker():
            with db.write(WriterRole.REGISTRY) as t:
                out.append(reg.allocate(t, IdSpace.CONCEPT, record_kind="Concept", idempotency_key="same-proposal"))

        threads = [threading.Thread(target=worker) for _ in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(len(set(out)), 1)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.db, self.clock = make_db()

    def append(self, n=3, actor=Component.PROMOTION_CONTROLLER, event="PROMOTED"):
        with self.db.write(WriterRole.REGISTRY) as t:
            for i in range(n):
                self.clock.advance(1)
                t.audit(actor, event, f"CONCEPT:{i + 1}", "ok")

    def rows(self):
        with self.db.read() as r:
            return r.query("SELECT * FROM audit_log ORDER BY seq")

    def test_chain_links_and_verifies(self):
        self.append(4)
        rows = self.rows()
        self.assertEqual(rows[0]["prev_hash"], GENESIS)
        self.assertEqual(rows[1]["prev_hash"], rows[0]["entry_hash"])
        self.assertEqual(verify_chain(rows), (True, None))

    def test_updates_and_deletes_are_blocked(self):
        self.append(2)
        raw = self.db.raw_unsafe_connection()
        with self.assertRaises(sqlite3.DatabaseError):
            raw.execute("UPDATE audit_log SET event='X' WHERE seq=1")
        with self.assertRaises(sqlite3.DatabaseError):
            raw.execute("DELETE FROM audit_log WHERE seq=1")

    def test_out_of_band_tamper_is_detected(self):
        self.append(5)
        raw = self.db.raw_unsafe_connection()
        raw.execute("DROP TRIGGER audit_no_update")
        raw.execute("UPDATE audit_log SET detail='forged' WHERE seq=3")
        ok, bad = verify_chain(self.rows())
        self.assertFalse(ok)
        self.assertEqual(bad, 3)

    def test_deletion_in_middle_detected(self):
        self.append(5)
        raw = self.db.raw_unsafe_connection()
        raw.execute("DROP TRIGGER audit_no_delete")
        raw.execute("DELETE FROM audit_log WHERE seq=2")
        ok, bad = verify_chain(self.rows())
        self.assertFalse(ok)
        self.assertEqual(bad, 3)

    def test_models_cannot_be_actors_of_decisions(self):
        for actor in (Component.MODEL_GATEWAY, Component.BIG_MODEL_GATEWAY):
            with self.assertRaises(PolicyDenied):
                self.append(1, actor=actor, event="PROMOTED")
        self.append(1, actor=Component.BIG_MODEL_GATEWAY, event="MODEL_CALL")  # logging is fine
        self.assertEqual(len(self.rows()), 1)

    def test_detail_is_truncated(self):
        with self.db.write(WriterRole.REGISTRY) as t:
            t.audit(Component.SYSTEM, "NOTE", "x", "d" * 5000)
        self.assertEqual(len(self.rows()[0]["detail"]), 500)


if __name__ == "__main__":
    unittest.main()
