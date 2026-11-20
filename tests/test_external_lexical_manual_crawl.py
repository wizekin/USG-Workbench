"""Offline contract tests for the one-launch lexical completion controller."""
from __future__ import annotations

import unittest

from tools.usg_external_lexical_v0_1_0.manual_crawl import (
    STORAGE_BUDGET_BYTES,
    STORAGE_BUDGET_MIB,
    checkpoint_count,
    checkpoint_signature,
    run_session,
)


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeCrawler:
    def __init__(self, total: int, *, stored_bytes: int = 0, clock: FakeClock | None = None):
        self.clock = clock
        self.state = {
            "expected_headwords": total,
            "processed_headwords": 0,
            "page_index": 0,
            "entry_index": 0,
            "batch_number": 0,
            "stored_bytes": stored_bytes,
            "retried_headwords": 0,
            "recovered_headwords": 0,
            "retry_failed_headwords": 0,
            "retry_dead_letter_headwords": 0,
            "failed_pages": 0,
            "retry_queue": [],
            "status": "in_progress",
            "source_snapshot_id": "fixture-snapshot",
        }
        self.calls: list[dict] = []

    def load_checkpoint(self):
        return dict(self.state)

    def run_batch(self, **kwargs):
        self.calls.append(kwargs)
        count = min(kwargs["max_headwords"], self.state["expected_headwords"] - self.state["processed_headwords"])
        self.state["processed_headwords"] += count
        self.state["page_index"] += 1
        self.state["batch_number"] += 1
        self.state["stored_bytes"] += max(1, count) * 100
        self.state["status"] = (
            "complete"
            if self.state["processed_headwords"] >= self.state["expected_headwords"]
            else "in_progress"
        )
        if self.clock is not None:
            self.clock.advance(2)
        return {
            "status": self.state["status"],
            "stop_reason": "source_snapshot_complete" if self.state["status"] == "complete" else "headword_limit",
            "batch": {"headwords": count, "entries": count, "senses": count * 2, "compressed_bytes": count * 100},
            "published": True,
        }


class ManualLexicalLauncherTests(unittest.TestCase):
    def test_storage_budget_is_exactly_700_mib(self) -> None:
        self.assertEqual(STORAGE_BUDGET_MIB, 700)
        self.assertEqual(STORAGE_BUDGET_BYTES, 700 * 1024 * 1024)

    def test_repeats_real_crawler_batches_until_target(self) -> None:
        crawler = FakeCrawler(total=5)
        result = run_session(
            crawler,
            target_total=5,
            batch_headwords=2,
            session_runtime_seconds=3600,
            reserve_seconds=10,
            run_id="test",
        )
        self.assertEqual(result["status"], "target_reached")
        self.assertEqual(checkpoint_count(crawler.load_checkpoint()), 5)
        self.assertEqual([call["max_headwords"] for call in crawler.calls], [2, 2, 1])
        self.assertEqual(result["session_processed_headwords"], 5)
        self.assertEqual(result["storage_budget_bytes"], 700 * 1024 * 1024)

    def test_stops_before_running_when_checkpoint_is_at_storage_limit(self) -> None:
        crawler = FakeCrawler(total=10, stored_bytes=STORAGE_BUDGET_BYTES)
        result = run_session(
            crawler,
            target_total=10,
            session_runtime_seconds=3600,
            reserve_seconds=10,
        )
        self.assertEqual(result["status"], "storage_limit_reached")
        self.assertEqual(crawler.calls, [])

    def test_dispatches_one_continuation_when_session_budget_is_used(self) -> None:
        clock = FakeClock()
        crawler = FakeCrawler(total=100, clock=clock)
        dispatched = []
        def dispatch(**kwargs):
            dispatched.append(kwargs)

        result = run_session(
            crawler,
            target_total=100,
            batch_headwords=1,
            session_runtime_seconds=301,
            reserve_seconds=300,
            continue_chain=True,
            continuation_dispatcher=dispatch,
            monotonic=clock,
        )
        self.assertEqual(result["status"], "continuation_dispatched")
        self.assertEqual(len(dispatched), 1)
        self.assertEqual(dispatched[0], {"target_total": 100, "batch_headwords": 1})
        self.assertEqual(result["remaining_headwords"], 99)

    def test_checkpoint_signature_detects_cursor_or_storage_change(self) -> None:
        first = {"processed_headwords": 10, "page_index": 2, "entry_index": 3, "stored_bytes": 100}
        second = {**first, "entry_index": 4}
        self.assertNotEqual(checkpoint_signature(first), checkpoint_signature(second))

    def test_rejects_batch_size_above_workflow_safe_limit(self) -> None:
        crawler = FakeCrawler(total=100)
        with self.assertRaises(ValueError):
            run_session(crawler, target_total=100, batch_headwords=30_001)


if __name__ == "__main__":
    unittest.main()
