"""Persistent budget ledger for the remote ("big") model.

Free plans are tiny and unforgiving, so every call must pass this ledger
*before* anything is sent, and every attempt (even failed ones) counts against
the caps. The ledger is persisted in SQLite so quotas survive restarts.

Rules enforced (in order):
  disabled -> task not allowed -> oversized request -> circuit-breaker cooldown
  -> minimum interval -> hourly cap -> daily cap -> daily token cap
  -> duplicate digest (novelty protection: never ask the same question twice)

Failures trigger exponential back-off (circuit breaker). Reservations that were
never settled (crash) are reaped to FAILED so they cannot leak quota forever
-- but they still count, which is the conservative direction.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config
from ..storage.database import Database, ReadTxn, WriteTxn
from ..storage.schema import WriterRole
from ..util import Clock, SystemClock
from .policy import BigModelTask

_HOUR = 3600.0
_DAY = 86400.0


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    reason: str
    retry_after_s: float = 0.0
    reservation_id: int | None = None


class BigModelLedger:
    def __init__(self, db: Database, config: Config, clock: Clock | None = None):
        self.db = db
        self.config = config
        self.clock: Clock = clock or db.clock or SystemClock()
        self._valid_tasks = {t.value for t in BigModelTask}

    # -- decision logic (pure over a read view) ----------------------------
    def _evaluate(self, r: ReadTxn, backend: str, task_type: str, est_in: int, est_out: int,
                  digest_hash: str | None, now: float) -> BudgetDecision:
        c = self.config
        if not c.get("bm_enabled"):
            return BudgetDecision(False, "BIG_MODEL_DISABLED")
        if task_type not in self._valid_tasks:
            return BudgetDecision(False, "TASK_NOT_ALLOWED")
        if type(est_in) is not int or type(est_out) is not int or est_in < 0 or est_out < 0:
            return BudgetDecision(False, "INVALID_TOKEN_ESTIMATE")
        if est_in > c.get("bm_max_input_tokens"):
            return BudgetDecision(False, "INPUT_TOO_LARGE")
        if est_out > c.get("bm_max_output_tokens"):
            return BudgetDecision(False, "OUTPUT_TOO_LARGE")

        br = r.one("SELECT cooldown_until FROM model_breaker WHERE backend=?", (backend,))
        if br is not None and br["cooldown_until"] > now:
            return BudgetDecision(False, "COOLDOWN", retry_after_s=float(br["cooldown_until"] - now))

        last = r.scalar("SELECT MAX(at) FROM model_budget_ledger WHERE backend=?", (backend,))
        gap = float(c.get("bm_min_interval_s"))
        if last is not None and now - last < gap:
            return BudgetDecision(False, "MIN_INTERVAL", retry_after_s=float(gap - (now - last)))

        calls_h = int(r.scalar("SELECT COUNT(*) FROM model_budget_ledger WHERE backend=? AND at>=?",
                               (backend, now - _HOUR), 0))
        if calls_h >= c.get("bm_max_calls_per_hour"):
            oldest = r.scalar("SELECT MIN(at) FROM model_budget_ledger WHERE backend=? AND at>=?",
                              (backend, now - _HOUR), now)
            return BudgetDecision(False, "HOURLY_CAP", retry_after_s=float(max(0.0, oldest + _HOUR - now)))

        calls_d = int(r.scalar("SELECT COUNT(*) FROM model_budget_ledger WHERE backend=? AND at>=?",
                               (backend, now - _DAY), 0))
        if calls_d >= c.get("bm_max_calls_per_day"):
            oldest = r.scalar("SELECT MIN(at) FROM model_budget_ledger WHERE backend=? AND at>=?",
                              (backend, now - _DAY), now)
            return BudgetDecision(False, "DAILY_CAP", retry_after_s=float(max(0.0, oldest + _DAY - now)))

        tokens_d = int(r.scalar(
            "SELECT COALESCE(SUM(input_tokens+output_tokens),0) FROM model_budget_ledger WHERE backend=? AND at>=?",
            (backend, now - _DAY), 0))
        if tokens_d + est_in + est_out > c.get("bm_max_tokens_per_day"):
            return BudgetDecision(False, "TOKEN_CAP")

        if digest_hash:
            dup = r.scalar(
                "SELECT COUNT(*) FROM model_budget_ledger WHERE digest_hash=? AND status IN ('OK','RESERVED') AND at>=?",
                (digest_hash, now - float(c.get("bm_digest_dedup_s"))), 0)
            if dup:
                return BudgetDecision(False, "DUPLICATE_DIGEST")
        return BudgetDecision(True, "OK")

    # -- public API --------------------------------------------------------
    def check(self, backend: str, task_type: str, est_in: int, est_out: int,
              digest_hash: str | None = None) -> BudgetDecision:
        """Read-only: would a call be allowed right now?"""
        with self.db.read() as r:
            return self._evaluate(r, backend, task_type, est_in, est_out, digest_hash, self.clock.now())

    def reserve(self, backend: str, task_type: str, est_in: int, est_out: int,
                digest_hash: str | None = None) -> BudgetDecision:
        """Atomically re-check and reserve quota. Call ``settle`` afterwards."""
        now = self.clock.now()
        with self.db.write(WriterRole.LEDGER) as txn:
            self._reap(txn, now)
            decision = self._evaluate(txn, backend, task_type, est_in, est_out, digest_hash, now)
            if not decision.allowed:
                return decision
            cur = txn.execute(
                "INSERT INTO model_budget_ledger(at,backend,task_type,status,input_tokens,output_tokens,digest_hash)"
                " VALUES(?,?,?,?,?,?,?)",
                (now, backend, task_type, "RESERVED", int(est_in), int(est_out), digest_hash),
            )
            return BudgetDecision(True, "RESERVED", reservation_id=int(cur.lastrowid))

    def settle(self, reservation_id: int, ok: bool, in_tokens: int = 0, out_tokens: int = 0, detail: str = "") -> None:
        if type(in_tokens) is not int or type(out_tokens) is not int or in_tokens < 0 or out_tokens < 0:
            from ..errors import InvariantViolation
            raise InvariantViolation('settlement requires nonnegative token counts', 'SG-GOV-009')
        now = self.clock.now()
        with self.db.write(WriterRole.LEDGER) as txn:
            row = txn.one("SELECT backend,status FROM model_budget_ledger WHERE id=?", (reservation_id,))
            if row is None or row["status"] != "RESERVED":
                return
            backend = row["backend"]
            status = "OK" if ok else "FAILED"
            if ok:
                txn.execute(
                    "UPDATE model_budget_ledger SET status=?, input_tokens=?, output_tokens=?, detail=? WHERE id=?",
                    (status, int(in_tokens), int(out_tokens), detail[:300], reservation_id),
                )
                txn.execute(
                    "INSERT INTO model_breaker(backend,consecutive_failures,cooldown_until) VALUES(?,?,?) "
                    "ON CONFLICT(backend) DO UPDATE SET consecutive_failures=0, cooldown_until=0",
                    (backend, 0, 0.0),
                )
            else:
                # a failed call may still have consumed quota; keep the estimate unless real usage is known
                txn.execute("UPDATE model_budget_ledger SET status=?, detail=? WHERE id=?",
                            (status, detail[:300], reservation_id))
                if in_tokens or out_tokens:
                    txn.execute("UPDATE model_budget_ledger SET input_tokens=?, output_tokens=? WHERE id=?",
                                (int(in_tokens), int(out_tokens), reservation_id))
                prev = txn.one("SELECT consecutive_failures FROM model_breaker WHERE backend=?", (backend,))
                n = (int(prev["consecutive_failures"]) if prev else 0) + 1
                cool = min(float(self.config.get("bm_cooldown_max_s")),
                           float(self.config.get("bm_cooldown_base_s")) * (2 ** min(n - 1, 30)))
                txn.execute(
                    "INSERT INTO model_breaker(backend,consecutive_failures,cooldown_until) VALUES(?,?,?) "
                    "ON CONFLICT(backend) DO UPDATE SET consecutive_failures=excluded.consecutive_failures, "
                    "cooldown_until=excluded.cooldown_until",
                    (backend, n, now + cool),
                )

    def _reap(self, txn: WriteTxn, now: float) -> None:
        stale = now - float(self.config.get("bm_stale_reservation_s"))
        txn.execute(
            "UPDATE model_budget_ledger SET status='FAILED', detail='stale reservation reaped' "
            "WHERE status='RESERVED' AND at<?",
            (stale,),
        )

    def usage_summary(self, backend: str) -> dict:
        now = self.clock.now()
        with self.db.read() as r:
            return {
                "calls_1h": int(r.scalar("SELECT COUNT(*) FROM model_budget_ledger WHERE backend=? AND at>=?",
                                         (backend, now - _HOUR), 0)),
                "calls_24h": int(r.scalar("SELECT COUNT(*) FROM model_budget_ledger WHERE backend=? AND at>=?",
                                          (backend, now - _DAY), 0)),
                "tokens_24h": int(r.scalar(
                    "SELECT COALESCE(SUM(input_tokens+output_tokens),0) FROM model_budget_ledger "
                    "WHERE backend=? AND at>=?", (backend, now - _DAY), 0)),
                "cooldown_until": float(r.scalar("SELECT cooldown_until FROM model_breaker WHERE backend=?",
                                                 (backend,), 0.0)),
            }
