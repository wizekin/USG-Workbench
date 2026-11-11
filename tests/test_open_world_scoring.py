"""Tests for OW-4 structural validation and oracle-aware scoring."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest

from jsonschema import Draft202012Validator

from tools.open_world_evaluation.generate_scenarios import ScenarioGenerator
from tools.open_world_evaluation.score_cases import score_pair
from tools.open_world_evaluation.validate_protocol import validate_instance

STAMP = "2026-11-11T13:00:00Z"
COMMIT = "c" * 40


def make_case(target_id: str, text: str = "Ada writes code."):
    case = ScenarioGenerator(
        seed="ow4-scoring-test",
        target_ids=[target_id],
        created_at=STAMP,
    ).generate(1)[0]
    case["input"]["text"] = text
    case["input"]["utf8_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    case["input"]["language_hint"] = "en"
    return case


def make_record(case, payload, outcome="completed"):
    compact = json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return {
        "schema_version": "1.0.0",
        "attempt_id": "OWA-OW4-TEST-0001",
        "case_id": case["case_id"],
        "target": {
            "component_id": case["target"]["component_id"],
            "component_version": case["target"]["component_version"],
            "entry_point": case["target"]["entry_point"],
            "commit_sha": COMMIT,
        },
        "started_at": STAMP,
        "finished_at": "2026-11-11T13:00:01Z",
        "outcome": outcome,
        "execution": {"duration_ms": 12.0, "timed_out": False},
        "capture": {
            "output_sha256": hashlib.sha256(compact).hexdigest(),
            "output_media_type": "application/json",
            "inline_output": payload,
        },
        "validation": {"diagnostics": []},
        "scoring": [],
        "artifacts": [],
    }


def make_phase5_payload(case):
    text = case["input"]["text"]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    tokens = []
    for index, (word, start) in enumerate((("Ada", 0), ("writes", 4), ("code", 11))):
        tokens.append({
            "token": {
                "token_id": f"tok:{index}",
                "start": start,
                "end": start + len(word),
                "surface_text": word,
            }
        })
    candidate = {
        "construction_id": "en.simple_transitive.svo",
        "role_token_refs": [
            ["AGENT", "tok:0"], ["ACTION", "tok:1"], ["PATIENT", "tok:2"]
        ],
    }
    target_result = {
        "pipeline_contract": "USG-INTERPRET/0.2.0",
        "completion_status": "COMPLETE",
        "source": {"text": text, "sha256": digest},
        "source_sha256": digest,
        "resource_manifest_digest": "d" * 64,
        "stages": {
            "lexical": {"artifact": {"tokens": tokens}},
            "segmentation": {"artifact": {}},
            "operators": {"artifact": {}},
            "syntax": {"artifact": {"clauses": [{"candidates": [candidate]}]}},
            "semantic_composition": {"artifact": {"status": "COMPOSED"}},
            "discourse": {"artifact": {}},
        },
        "safety": {"truth_promotion": False},
    }
    return {"outcome": outcome_from_completion("COMPLETE"), "target_result": target_result}


def outcome_from_completion(status):
    return "completed" if status == "COMPLETE" else "partial"


class OpenWorldScoringTests(unittest.TestCase):
    def test_phase5_structural_checks_pass_without_claiming_semantic_accuracy(self):
        case = make_case("phase5-bounded-interpreter")
        record = make_record(case, make_phase5_payload(case))
        score = score_pair(case, record)
        self.assertEqual(score["structural_status"], "valid", score["failed_checks"])
        self.assertTrue(score["structural_checks"]["source_spans_and_token_refs"])
        self.assertEqual(
            score["semantic_scoring"]["status"],
            "not_scored_no_independent_oracle",
        )
        self.assertEqual(score["semantic_scoring"]["metrics"], [])

    def test_phase5_invalid_source_span_is_detected(self):
        case = make_case("phase5-bounded-interpreter")
        payload = make_phase5_payload(case)
        payload["target_result"]["stages"]["lexical"]["artifact"]["tokens"][0]["token"]["end"] = 999
        record = make_record(case, payload)
        score = score_pair(case, record)
        self.assertEqual(score["structural_status"], "invalid")
        self.assertIn("source_spans_and_token_refs", score["failed_checks"])

    def test_input_and_output_digest_integrity_are_checked(self):
        case = make_case("phase5-bounded-interpreter")
        record = make_record(case, make_phase5_payload(case))
        record["capture"]["output_sha256"] = "0" * 64
        score = score_pair(case, record)
        self.assertEqual(score["structural_status"], "invalid")
        self.assertIn("output_digest_valid", score["failed_checks"])

    def test_case_and_execution_identity_mismatch_is_detected(self):
        case = make_case("phase5-bounded-interpreter")
        record = make_record(case, make_phase5_payload(case))
        record["target"]["component_version"] = "9.9.9"
        score = score_pair(case, record)
        self.assertIn("target_matches", score["failed_checks"])

    def test_not_executed_target_is_not_marked_as_failed(self):
        case = make_case("js-semantic-workbench-v054")
        payload = {
            "outcome": "not_executed",
            "reason": "browser adapter not implemented",
        }
        record = make_record(case, payload, outcome="not_executed")
        score = score_pair(case, record)
        self.assertEqual(score["structural_status"], "not_applicable")
        self.assertFalse(score["semantic_scoring"]["metrics"])

    def test_independent_human_rubric_is_not_automatically_fabricated(self):
        case = make_case("phase5-bounded-interpreter")
        case["oracle"] = {
            "type": "human_rubric", "independent": True,
            "oracle_id": "review-panel-v1",
        }
        record = make_record(case, make_phase5_payload(case))
        score = score_pair(case, record)
        self.assertEqual(
            score["semantic_scoring"]["status"],
            "requires_independent_human_rubric_review",
        )
        self.assertEqual(score["semantic_scoring"]["metrics"], [])

    def test_score_result_schema_accepts_generated_score(self):
        case = make_case("phase5-bounded-interpreter")
        record = make_record(case, make_phase5_payload(case))
        score = score_pair(case, record)
        schema_path = "tools/open_world_evaluation/schemas/score-result.schema.json"
        import pathlib
        schema = json.loads((pathlib.Path(__file__).resolve().parents[1] / schema_path).read_text())
        errors = list(Draft202012Validator(schema).iter_errors(score))
        self.assertEqual(errors, [])

    def test_phase5_wrong_source_text_is_invalid(self):
        case = make_case("phase5-bounded-interpreter")
        payload = make_phase5_payload(case)
        payload["target_result"]["source"]["text"] = "different text"
        record = make_record(case, payload)
        score = score_pair(case, record)
        self.assertIn("source_preservation", score["failed_checks"])


if __name__ == "__main__":
    unittest.main()
