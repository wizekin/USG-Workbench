"""Tests for pinned, deterministic replay of recorded OW scenarios."""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tools.open_world_evaluation.replay_cases import (
    compare_replay,
    replay_records,
    stable_target_result_digest,
)

COMMIT = "a" * 40
TARGET = "phase4-bounded-interpreter"


def make_case(case_id="case-1"):
    return {
        "case_id": case_id,
        "target": {"component_id": TARGET},
        "input": {"utf8_sha256": "b" * 64},
    }


def target_result(document_id="old-id", created_at="2026-01-01T00:00:00Z", expression="expr:1"):
    return {
        "pipeline_contract": "USG-INTERPRET/0.1.0",
        "pipeline_version": "usg-interpretation/0.1.0",
        "completion_status": "COMPLETE",
        "document": {
            "documentId": document_id,
            "createdAt": created_at,
            "expressions": [{"id": expression, "op": "PREDICATE"}],
        },
    }


def make_record(case_id="case-1", outcome="completed", result=None, attempt="attempt-original"):
    return {
        "case_id": case_id,
        "attempt_id": attempt,
        "outcome": outcome,
        "target": {"component_id": TARGET, "commit_sha": COMMIT},
        "capture": {"inline_output": {"target_result": result or target_result()}},
    }


class DeterministicReplayTests(unittest.TestCase):
    def test_known_volatile_phase4_document_fields_are_excluded(self):
        original = make_record(result=target_result("doc-A", "2026-01-01T00:00:00Z"))
        replay = make_record(result=target_result("doc-B", "2026-02-01T00:00:00Z"), attempt="attempt-replay")
        first, version1 = stable_target_result_digest(original, TARGET)
        second, version2 = stable_target_result_digest(replay, TARGET)
        self.assertEqual(first, second)
        self.assertEqual(version1, "usg-interpretation/0.1.0")
        self.assertEqual(version1, version2)

    def test_semantic_target_result_change_is_not_hidden(self):
        original = make_record(result=target_result(expression="expr:1"))
        replay = make_record(result=target_result(expression="expr:2"), attempt="attempt-replay")
        entry = compare_replay(original, replay)
        self.assertEqual(entry["status"], "target_result_mismatch")
        self.assertFalse(entry["target_result_matches"])
        self.assertEqual(entry["differing_json_paths"], ["document.expressions[0].id"])

    def test_outcome_change_is_reported_separately(self):
        original = make_record(outcome="partial")
        replay = make_record(outcome="completed", attempt="attempt-replay")
        entry = compare_replay(original, replay)
        self.assertEqual(entry["status"], "outcome_mismatch")
        self.assertFalse(entry["outcome_matches"])

    def test_pipeline_version_mismatch_is_not_comparable(self):
        original = make_record()
        replayed = make_record(result={
            **target_result(),
            "pipeline_version": "usg-interpretation/9.9.9",
        }, attempt="attempt-replay")
        entry = compare_replay(original, replayed)
        self.assertEqual(entry["status"], "not_comparable")
        self.assertIsNone(entry["target_result_matches"])

    def test_replay_records_produce_schema_valid_exact_match_report(self):
        case = make_case()
        original = make_record()
        def executor(_case, *, commit_sha, max_wall_seconds):
            self.assertEqual(commit_sha, COMMIT)
            self.assertGreater(max_wall_seconds, 0)
            return make_record(
                result=target_result("new-id", "2026-03-01T00:00:00Z"),
                attempt="attempt-replay",
            )
        report = replay_records([case], [original], commit_sha=COMMIT, executor=executor)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["counts"]["exact_match"], 1)
        schema_path = Path(__file__).resolve().parents[1] / "tools/open_world_evaluation/schemas/replay-report.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report))
        self.assertEqual(errors, [])

    def test_not_executed_records_are_skipped_not_replayed(self):
        case = make_case()
        skipped = make_record(outcome="not_executed")
        report = replay_records(
            [case], [skipped], commit_sha=COMMIT,
            executor=lambda *_args, **_kwargs: self.fail("not_executed must not be replayed"),
        )
        self.assertEqual(report["status"], "no_cases")
        self.assertEqual(report["skipped_not_executed_record_count"], 1)

    def test_original_result_must_be_pinned_to_requested_commit(self):
        case = make_case()
        original = make_record()
        original["target"]["commit_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "different commit"):
            replay_records([case], [original], commit_sha=COMMIT)

    def test_selected_case_ids_and_budget_are_enforced(self):
        cases = [make_case("case-1"), make_case("case-2")]
        records = [make_record("case-1"), make_record("case-2", attempt="attempt-2")]
        report = replay_records(
            cases, records, commit_sha=COMMIT, max_cases=1,
            selected_case_ids={"case-2"},
            executor=lambda case, **_kwargs: make_record(
                case["case_id"], attempt="attempt-replay"
            ),
        )
        self.assertEqual(report["selected_case_count"], 1)
        self.assertEqual(report["replayed_record_count"], 1)
        self.assertEqual(report["not_replayed_due_to_budget_count"], 0)
        with self.assertRaisesRegex(ValueError, "missing"):
            replay_records(cases, records, commit_sha=COMMIT, selected_case_ids={"absent"})


if __name__ == "__main__":
    unittest.main()
