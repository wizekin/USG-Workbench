import unittest

from usg.autonomy.ledger import BigModelLedger
from usg.autonomy.policy import (ActionClass, AutonomyMode, AutonomyPolicy, BigModelTask, IssueEffect, VerifierClass,
                                 big_model_may_produce, issue_effect_is_safe)
from usg.autonomy import seal
from usg.config import Calibration, Config
from usg.errors import PolicyDenied, SealViolation
from usg.storage.schema import WriterRole
from tests.helpers import make_db

BE = "free-plan"


class PolicyTests(unittest.TestCase):
    def test_every_action_has_a_requirement(self):
        pol = AutonomyPolicy()
        for a in ActionClass:
            self.assertIn(a, [r.action for r in pol.table()])
            pol.requirement(a)

    def test_forbidden_and_shadow_actions_cannot_activate(self):
        pol = AutonomyPolicy()
        for a in (ActionClass.FOUNDATIONAL_RULE_CHANGE, ActionClass.VALIDATOR_CHANGE, ActionClass.FN_PRIMITIVE_CHANGE,
                  ActionClass.UNIVERSAL_CLAIM, ActionClass.PHYSICAL_MERGE, ActionClass.EQUIVALENCE_OTHER,
                  ActionClass.TRUST_TIER_TO_TRUSTED):
            self.assertEqual(pol.mode(a), AutonomyMode.FORBIDDEN)
            with self.assertRaises(PolicyDenied):
                pol.assert_may_activate(a)
        for a in (ActionClass.FRAME_FUNDAMENTAL, ActionClass.CONCEPT_GENERALIZATION):
            self.assertEqual(pol.mode(a), AutonomyMode.SHADOW_ONLY)
            self.assertFalse(pol.may_activate(a))
            with self.assertRaises(PolicyDenied):
                pol.assert_may_activate(a)

    def test_gated_actions_need_a_real_panel_canary_and_rollback(self):
        pol = AutonomyPolicy()
        gated = [r for r in pol.table() if r.mode is AutonomyMode.GATED]
        self.assertTrue(gated)
        for r in gated:
            self.assertGreaterEqual(r.min_verifier_classes, 2)
            self.assertGreaterEqual(r.min_verifier_classes, len(r.required_verifiers))
            self.assertTrue(r.needs_rollback_plan, r.action)
            req = pol.assert_may_activate(r.action)
            self.assertGreaterEqual(req.min_verifier_classes, 3 if r.min_verifier_classes < 3 else r.min_verifier_classes)
        # high-impact structure changes also need a canary
        for a in (ActionClass.CONCEPT_NEW, ActionClass.INTERP_RULE, ActionClass.CANON_RULE,
                  ActionClass.EQUIVALENCE_ESTABLISHED, ActionClass.FRAME_DOMAIN):
            self.assertTrue(pol.requirement(a).needs_canary)

    def test_equivalence_established_needs_the_strongest_panel(self):
        r = AutonomyPolicy().requirement(ActionClass.EQUIVALENCE_ESTABLISHED)
        self.assertIn(VerifierClass.COUNTEREXAMPLE, r.required_verifiers)
        self.assertGreaterEqual(r.min_verifier_classes, 4)

    def test_rollback_and_lowering_trust_are_always_possible(self):
        pol = AutonomyPolicy()
        for a in (ActionClass.ROLLBACK, ActionClass.TRUST_TIER_LOWER, ActionClass.ASSERTION_STORE_PROVISIONAL):
            self.assertEqual(pol.mode(a), AutonomyMode.AUTOMATIC)

    def test_big_model_can_only_set_general_rules_or_analyse_general_issues(self):
        ok = {
            BigModelTask.GENERAL_RULE_PROPOSAL: {ActionClass.INTERP_RULE, ActionClass.CANON_RULE,
                                                 ActionClass.VALENCE_PATTERN, ActionClass.FIGURATIVE_MAPPING},
            BigModelTask.GENERAL_ISSUE_ANALYSIS: {ActionClass.ISSUE_FINDING},
        }
        for task, allowed in ok.items():
            for a in ActionClass:
                self.assertEqual(big_model_may_produce(task, a), a in allowed, (task, a))
        # it can never touch knowledge, identity, trust or foundations
        for a in (ActionClass.CONCEPT_NEW, ActionClass.ASSERTION_PROMOTE_TRUSTED, ActionClass.EQUIVALENCE_ESTABLISHED,
                  ActionClass.TRUST_TIER_TO_STANDARD, ActionClass.FOUNDATIONAL_RULE_CHANGE):
            for task in BigModelTask:
                self.assertFalse(big_model_may_produce(task, a))

    def test_issue_findings_can_only_raise_scrutiny(self):
        for e in (IssueEffect.RAISE_RISK_FLOOR, IssueEffect.PRIORITISE_REPROCESSING,
                  IssueEffect.REQUEST_RULE_PROPOSAL, IssueEffect.INCREASE_AUDIT_RATE):
            self.assertTrue(issue_effect_is_safe(e))
        for e in (IssueEffect.LOWER_RISK, IssueEffect.SKIP_VALIDATION, IssueEffect.RAISE_TRUST,
                  IssueEffect.DISABLE_CHECK):
            self.assertFalse(issue_effect_is_safe(e))

    def test_min_verifier_floor_comes_from_pinned_config(self):
        cfg = Config()
        self.assertEqual(cfg.status("avp_min_verifier_classes_gated"), Calibration.PINNED)
        pol = AutonomyPolicy(cfg)
        self.assertGreaterEqual(pol.requirement(ActionClass.ANALOGY_RECORD).min_verifier_classes, 3)


class LedgerTests(unittest.TestCase):
    def make(self, **over):
        db, clock = make_db()
        cfg = Config({"bm_enabled": True, **over})
        return BigModelLedger(db, cfg, clock), clock, db

    def go(self, led, task="GENERAL_RULE_PROPOSAL", i=500, o=300, digest=None):
        return led.reserve(BE, task, i, o, digest)

    def test_disabled_by_default(self):
        db, clock = make_db()
        led = BigModelLedger(db, Config(), clock)
        d = led.reserve(BE, "GENERAL_RULE_PROPOSAL", 100, 100)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "BIG_MODEL_DISABLED")

    def test_task_whitelist_and_size_limits(self):
        led, _, _ = self.make()
        self.assertEqual(self.go(led, task="TRANSLATE_THIS_SENTENCE").reason, "TASK_NOT_ALLOWED")
        self.assertEqual(self.go(led, i=999_999).reason, "INPUT_TOO_LARGE")
        self.assertEqual(self.go(led, o=999_999).reason, "OUTPUT_TOO_LARGE")
        self.assertTrue(self.go(led).allowed)

    def test_min_interval_then_hourly_cap(self):
        led, clock, _ = self.make()  # defaults: 1 call/hour, 30 min interval
        self.assertTrue(self.go(led).allowed)
        d = self.go(led)
        self.assertEqual(d.reason, "MIN_INTERVAL")
        self.assertGreater(d.retry_after_s, 0)
        clock.advance(1801)
        self.assertEqual(self.go(led).reason, "HOURLY_CAP")
        clock.advance(3600)
        self.assertTrue(self.go(led).allowed)

    def test_daily_cap(self):
        led, clock, _ = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=2)
        self.assertTrue(self.go(led).allowed)
        self.assertTrue(self.go(led).allowed)
        self.assertEqual(self.go(led).reason, "DAILY_CAP")
        clock.advance(86401)
        self.assertTrue(self.go(led).allowed)

    def test_token_cap(self):
        led, _, _ = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=10,
                              bm_max_tokens_per_day=1500)
        self.assertTrue(self.go(led, i=500, o=300).allowed)
        self.assertTrue(self.go(led, i=300, o=300).allowed)
        self.assertEqual(self.go(led, i=500, o=300).reason, "TOKEN_CAP")

    def test_duplicate_digest_is_never_sent_twice(self):
        led, clock, _ = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=10)
        d1 = self.go(led, digest="abc")
        self.assertTrue(d1.allowed)
        led.settle(d1.reservation_id, True, 400, 200)
        self.assertEqual(self.go(led, digest="abc").reason, "DUPLICATE_DIGEST")
        self.assertTrue(self.go(led, digest="different").allowed)
        clock.advance(8 * 86400)
        self.assertTrue(self.go(led, digest="abc").allowed)

    def test_failures_trigger_exponential_cooldown_and_success_resets(self):
        led, clock, _ = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=50,
                                  bm_cooldown_base_s=600)
        d = self.go(led)
        led.settle(d.reservation_id, False, detail="HTTP 429")
        blocked = self.go(led)
        self.assertEqual(blocked.reason, "COOLDOWN")
        self.assertAlmostEqual(blocked.retry_after_s, 600, delta=1)
        clock.advance(601)
        d2 = self.go(led)
        self.assertTrue(d2.allowed)
        led.settle(d2.reservation_id, False, detail="HTTP 500")
        blocked = self.go(led)
        self.assertAlmostEqual(blocked.retry_after_s, 1200, delta=1)  # doubled
        clock.advance(1201)
        d3 = self.go(led)
        led.settle(d3.reservation_id, True, 100, 50)
        self.assertTrue(self.go(led).allowed)  # breaker reset by success

    def test_failed_calls_still_count_against_quota(self):
        led, clock, _ = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=2,
                                  bm_cooldown_base_s=10)
        for _ in range(2):
            d = self.go(led)
            led.settle(d.reservation_id, False)
            clock.advance(25)  # longer than both exponential cooldowns (10s, 20s)
        self.assertEqual(self.go(led).reason, "DAILY_CAP")

    def test_stale_reservations_are_reaped_but_still_count(self):
        led, clock, db = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=1)
        self.assertTrue(self.go(led).allowed)  # never settled (simulated crash)
        clock.advance(1000)
        self.assertEqual(self.go(led).reason, "DAILY_CAP")
        with db.read() as r:
            self.assertEqual(r.scalar("SELECT status FROM model_budget_ledger"), "FAILED")

    def test_usage_summary(self):
        led, _, _ = self.make(bm_max_calls_per_hour=10, bm_min_interval_s=0, bm_max_calls_per_day=10)
        d = self.go(led, i=400, o=100)
        led.settle(d.reservation_id, True, 380, 90)
        s = led.usage_summary(BE)
        self.assertEqual((s["calls_1h"], s["calls_24h"], s["tokens_24h"]), (1, 1, 470))

    def test_check_is_read_only(self):
        led, _, db = self.make()
        self.assertTrue(led.check(BE, "GENERAL_ISSUE_ANALYSIS", 100, 100).allowed)
        with db.read() as r:
            self.assertEqual(r.scalar("SELECT COUNT(*) FROM model_budget_ledger"), 0)

    def test_only_ledger_role_may_write_the_ledger(self):
        _, _, db = self.make()
        with self.assertRaises(PolicyDenied):
            with db.write(WriterRole.PROMOTION) as t:
                t.execute("INSERT INTO model_budget_ledger(at,backend,task_type,status) VALUES(1,'x','y','OK')")


class SealTests(unittest.TestCase):
    def test_install_and_verify(self):
        db, _ = make_db()
        self.assertFalse(seal.verify_seal(db).ok)  # nothing sealed yet
        m = seal.install_seal(db)
        self.assertEqual(set(m), set(seal.SEALED_MODULES))
        self.assertTrue(seal.verify_seal(db).ok)
        seal.assert_sealed(db)
        self.assertEqual(seal.install_seal(db), m)  # idempotent
        with db.read() as r:
            self.assertEqual(r.scalar("SELECT event FROM audit_log"), "SEAL_INSTALLED")

    def test_tampered_manifest_is_detected(self):
        db, _ = make_db()
        seal.install_seal(db)
        db.raw_unsafe_connection().execute("UPDATE sealed_manifest SET sha256='00' WHERE name='usg.autonomy.policy'")
        rep = seal.verify_seal(db)
        self.assertFalse(rep.ok)
        self.assertEqual(rep.mismatches, ("usg.autonomy.policy",))
        with self.assertRaises(SealViolation):
            seal.assert_sealed(db)

    def test_cannot_overwrite_without_explicit_reseal(self):
        db, _ = make_db()
        seal.install_seal(db)
        db.raw_unsafe_connection().execute("UPDATE sealed_manifest SET sha256='00' WHERE name='usg.errors'")
        with self.assertRaises(SealViolation):
            seal.install_seal(db)
        seal.install_seal(db, reseal=True)  # release-time action
        self.assertTrue(seal.verify_seal(db).ok)

    def test_module_added_after_install_is_reported_missing(self):
        db, _ = make_db()
        seal.install_seal(db, ["usg.errors"])
        rep = seal.verify_seal(db, ["usg.errors", "usg.core.ids"])
        self.assertFalse(rep.ok)
        self.assertEqual(rep.missing, ("usg.core.ids",))

    def test_hash_is_stable(self):
        self.assertEqual(seal.module_hash("usg.errors"), seal.module_hash("usg.errors"))
        with self.assertRaises(SealViolation):
            seal.module_hash("usg.no_such_module")


class ConfigTests(unittest.TestCase):
    def test_register_is_consistent(self):
        from usg.config import REGISTER
        names = [c.name for c in REGISTER]
        self.assertEqual(len(names), len(set(names)))
        cfg = Config()
        for c in REGISTER:
            if isinstance(c.value, bool):
                continue
            if c.lo is not None:
                self.assertGreaterEqual(c.value, c.lo, c.name)
            if c.hi is not None:
                self.assertLessEqual(c.value, c.hi, c.name)
            self.assertEqual(cfg.get(c.name), c.value)

    def test_big_model_defaults_are_tiny_and_off(self):
        cfg = Config()
        self.assertFalse(cfg.get("bm_enabled"))
        self.assertLessEqual(cfg.get("bm_max_calls_per_day"), 3)
        self.assertLessEqual(cfg.get("bm_max_calls_per_hour"), 1)
        self.assertLessEqual(cfg.get("bm_max_input_tokens"), 2500)

    def test_pinned_constants_cannot_be_auto_calibrated(self):
        cfg = Config()
        for name in ("bm_max_calls_per_day", "wilson_z", "avp_min_verifier_classes_gated", "bm_enabled"):
            self.assertEqual(cfg.status(name), Calibration.PINNED)
            with self.assertRaises(Exception) as cm:
                cfg.calibrate(name, cfg.get(name), "run-1")
            self.assertEqual(getattr(cm.exception, "code", ""), "CONFIG-PINNED")

    def test_calibration_inside_bounds_is_recorded(self):
        cfg = Config()
        self.assertIn("tau_medium", cfg.uncalibrated())
        ev = cfg.calibrate("tau_medium", 0.04, "run-7", "audit upper bound 0.031 over 400 units")
        self.assertEqual((ev.old, ev.new), (0.05, 0.04))
        self.assertEqual(cfg.status("tau_medium"), Calibration.CALIBRATED)
        self.assertNotIn("tau_medium", cfg.uncalibrated())
        self.assertEqual(len(cfg.history), 1)

    def test_calibration_outside_bounds_is_rejected(self):
        cfg = Config()
        for bad in (0.0001, 0.9):
            with self.assertRaises(Exception) as cm:
                cfg.calibrate("tau_medium", bad, "run-8")
            self.assertEqual(getattr(cm.exception, "code", ""), "CONFIG-BOUNDS")
        self.assertEqual(cfg.get("tau_medium"), 0.05)
        with self.assertRaises(KeyError):
            cfg.get("no_such_constant")

    def test_backend_configs_from_env(self):
        from usg.config import BigModelConfig, LocalModelConfig
        self.assertEqual(LocalModelConfig.from_env({}).backend, "none")
        self.assertEqual(LocalModelConfig.from_env({"USG_LOCAL_MODEL": "qwen2.5:3b"}).backend, "ollama")
        self.assertFalse(BigModelConfig.from_env({}).enabled)
        # URL and model alone are not enough: an explicit enable flag is also required
        self.assertFalse(BigModelConfig.from_env({"USG_BIG_URL": "http://x", "USG_BIG_MODEL": "m"}).enabled)
        self.assertTrue(BigModelConfig.from_env(
            {"USG_BIG_URL": "http://x", "USG_BIG_MODEL": "m", "USG_BIG_ENABLED": "1"}).enabled)


if __name__ == "__main__":
    unittest.main()
