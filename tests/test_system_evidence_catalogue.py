"""Phase 8 evidence catalogue, resource inventory, and phase routing tests."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from tools.system_evidence.collector import collect_catalogue, render_markdown, validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/usg-system-evidence-source-registry-0.1.0.json"


class SystemEvidenceCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "specifications").mkdir()
        (self.root / "specifications/USG-SEM-1.0.md").write_text("canonical contract fixture", encoding="utf-8")
        (self.root / "specifications/usg-sem-1.0.schema.json").write_text("{}", encoding="utf-8")
        campaign = self.root / "evaluations/open-world/campaigns/CAMP-001"
        campaign.mkdir(parents=True)
        (campaign / "campaign-report.json").write_text(json.dumps({
            "campaign_id": "CAMP-001", "created_at": "2026-11-12T10:00:00Z",
            "status": "partial", "tested_commit_sha": "abc123",
            "coverage": {
                "case_count": 12,
                "population_case_counts": {"unconstrained_random": 10, "controlled_diagnostic": 2},
                "target_case_counts": {"phase5": 12},
                "execution_accounting": {"actual_attempt_count": 12, "not_executed_record_count": 0},
                "stage_attribution": {"first_blocking_stage_counts": {"lexical": 5}},
            },
            "outcome_counts": {"completed": 2, "partial": 5, "unsupported": 5},
        }), encoding="utf-8")
        (campaign / "bundle-manifest.json").write_text("{}", encoding="utf-8")
        self.manifest = self.root / "manifest.json"
        self.checkpoint = self.root / "checkpoint.json"
        self.pud = self.root / "pud.json"
        self.shard_inventory = self.root / "shard-inventory.json"
        self.shard_inventory.write_text(json.dumps({
            "status": "matches_manifest_with_duplicates", "snapshot_id": "snapshot-x",
            "file_count": 2, "unique_content_count": 2, "physical_file_count": 3,
            "duplicate_file_count": 1,
            "duplicate_groups": [{"sha256": "a" * 64, "canonical_path": "shard-1.jsonl.gz",
                                  "duplicate_paths": ["shard-1-retry.jsonl.gz"]}],
            "total_size_bytes": 220, "unique_content_size_bytes": 150,
            "files": [{"path": "shard-1.jsonl.gz", "size_bytes": 70, "sha256": "a" * 64},
                      {"path": "shard-1-retry.jsonl.gz", "size_bytes": 70, "sha256": "a" * 64},
                      {"path": "shard-2.jsonl.gz", "size_bytes": 80, "sha256": "b" * 64}],
        }), encoding="utf-8")
        self.growth = self.root / "growth.json"
        self.manifest.write_text(json.dumps({
            "status": "in_progress", "processed_headwords": 5, "expected_headwords": 10,
            "processed_entries": 8, "processed_senses": 12, "batch_count": 2,
            "stored_bytes": 100, "storage_budget_bytes": 1000,
            "pending_retries": 0, "retried_headwords": 3, "recovered_headwords": 3,
            "retry_dead_letter_headwords": 0, "source_snapshot_id": "snapshot-x",
            "last_batch": {"headwords": 2, "entries": 3, "senses": 4, "stop_reason": "headword_limit"},
        }), encoding="utf-8")
        self.checkpoint.write_text(json.dumps({"page_index": 1, "entry_index": 5, "cycle_number": 1}), encoding="utf-8")
        self.pud.write_text(json.dumps({
            "lexical_shard_count": 1, "lexicon_form_count": 20, "lexicon_lemma_count": 10,
            "pud_commit": "pinned", "pud_sentences": 1000, "lexical_source_is_candidate_only": True,
            "runtime_promotion_allowed": False,
            "totals": {"token_coverage": 0.1, "oov_rate": 0.9, "gold_tag_candidate_recall_all_tokens": 0.05,
                       "gold_lemma_coverage": 0.08, "gold_lemma_upos_candidate_recall": 0.04},
            "morphology_evaluation": {"totals": {"candidate_pool_precision": 0.0, "candidate_recall": 0.0}},
        }), encoding="utf-8")
        self.growth.write_text(json.dumps({
            "contract": "USG-EVIDENCE-DRIVEN-GROWTH-PLAN/0.1.0",
            "generated_at": "2026-11-12T10:00:00Z", "campaigns_analyzed": 1,
            "ranked_actions": [{"stage": "lexical", "priority_score": 12.5,
                               "proposed_action": "Review lexical OOV evidence.",
                               "acceptance_gate": "independent_lexical_evaluation",
                               "observed_first_blocker_records": 5,
                               "campaign_recurrence_count": 1,
                               "example_case_ids": ["CASE-1"]}],
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def collect(self, **kwargs):
        return collect_catalogue(
            self.root, registry_path=REGISTRY,
            external_manifest_path=self.manifest,
            external_checkpoint_path=self.checkpoint,
            pud_evaluation_path=self.pud,
            external_shard_inventory_path=self.shard_inventory,
            growth_plan_path=self.growth,
            repository_name="wizekin/USG-Workbench", commit_sha="test-sha",
            generated_at="2026-11-12T12:00:00Z", **kwargs)

    def test_registry_is_valid_and_has_all_eight_phase_profiles(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        validate_registry(registry)
        self.assertEqual([item["id"] for item in registry["phases"]],
                         ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"])

    def test_phase_resource_manifest_template_validates(self):
        template_path = ROOT / "templates/phase-resource-manifest-0.1.0.template.json"
        schema_path = ROOT / "specifications/usg-phase-resource-manifest-0.1.0.schema.json"
        template = json.loads(template_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(template)
        self.assertEqual(template["contract"], "USG-PHASE-RESOURCE-MANIFEST/0.1.0")
        self.assertTrue(template["governance"]["candidate_resources_remain_separate"])

    def test_phase_resource_map_covers_all_eight_phases(self):
        path = ROOT / "config/usg-phase-resource-consumption-map-0.1.0.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        schema_path = ROOT / "specifications/usg-phase-resource-consumption-map-0.1.0.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
        self.assertEqual(value["contract"], "USG-PHASE-RESOURCE-CONSUMPTION-MAP/0.1.0")
        self.assertEqual({item["phase_id"] for item in value["phases"]},
                         {f"P{i}" for i in range(1, 9)})
        self.assertIn("existing_phase_amendment_proposal",
                      {item["route"] for item in value["dependency_rules"]})
        phase8 = next(item for item in value["phases"] if item["phase_id"] == "P8")
        self.assertIn("system_evidence_catalogue_and_phase_manifest", phase8["required_sources"])

    def test_catalogue_indexes_source_families_and_exact_asset_hashes(self):
        report = self.collect()
        canonical = next(item for item in report["source_families"] if item["id"] == "canonical_semantic_interchange")
        paths = {item["path"] for item in canonical["files"]}
        self.assertIn("specifications/USG-SEM-1.0.md", paths)
        self.assertIn("specifications/usg-sem-1.0.schema.json", paths)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in canonical["files"]))
        self.assertGreater(report["asset_summary"]["unique_indexed_path_count"], 0)

    def test_live_external_manifest_metrics_are_freshness_aware(self):
        report = self.collect()
        external = report["external_lexical"]
        self.assertEqual(external["progress"]["headword_completion_percent"], 50.0)
        self.assertEqual(external["progress"]["processed_senses"], 12)
        self.assertEqual(external["pud_evaluation"]["status"], "stale_shard_count_mismatch")
        self.assertFalse(external["pud_evaluation"]["rights_and_runtime_boundary"]["runtime_promotion_allowed"])

    def test_fresh_pud_report_is_accepted_only_when_shard_counts_match(self):
        value = json.loads(self.pud.read_text(encoding="utf-8"))
        value["lexical_shard_count"] = 2
        self.pud.write_text(json.dumps(value), encoding="utf-8")
        report = self.collect()
        self.assertEqual(report["external_lexical"]["pud_evaluation"]["status"],
                         "fresh_for_current_shard_count")
        self.assertEqual(report["external_lexical"]["pud_evaluation"]["evaluated_shard_count"], 2)
        self.assertEqual(report["external_lexical"]["shard_inventory"]["status"], "matches_manifest_with_duplicates")
        self.assertEqual(report["external_lexical"]["shard_inventory"]["physical_file_count"], 3)
        self.assertEqual(report["external_lexical"]["shard_inventory"]["duplicate_file_count"], 1)

    def test_pud_metrics_remain_stale_when_physical_shard_count_disagrees(self):
        value = json.loads(self.pud.read_text(encoding="utf-8"))
        value["lexical_shard_count"] = 2
        self.pud.write_text(json.dumps(value), encoding="utf-8")
        inventory = json.loads(self.shard_inventory.read_text(encoding="utf-8"))
        inventory["file_count"] = 1
        self.shard_inventory.write_text(json.dumps(inventory), encoding="utf-8")
        report = self.collect()
        self.assertEqual(report["external_lexical"]["pud_evaluation"]["status"],
                         "stale_shard_count_mismatch")
        self.assertEqual(report["external_lexical"]["shard_inventory"]["status"], "count_mismatch")

    def test_latest_campaign_population_and_accounting_are_preserved(self):
        report = self.collect()
        latest = report["open_world"]["latest_campaign"]
        self.assertEqual(latest["campaign_id"], "CAMP-001")
        self.assertEqual(latest["execution_accounting"]["actual_attempt_count"], 12)
        self.assertEqual(latest["population_case_counts"]["unconstrained_random"], 10)
        self.assertEqual(latest["naturalistic_case_count"], 0)

    def test_growth_recommendations_route_to_existing_phase_review(self):
        report = self.collect()
        action = next(item for item in report["discoveries"] if item["kind"] == "growth_planner_recommendation")
        self.assertIn("P6", action["phase_impacts"])
        self.assertIn(action["route"], {"existing_phase_continuation", "existing_phase_amendment_proposal"})
        self.assertFalse(action["runtime_change_allowed"])
        self.assertEqual(action["review_status"], "observed_requires_review")

    def test_live_workflow_failure_is_preserved_and_routed(self):
        workflow_path = self.root / "workflow-runs.json"
        workflow_path.write_text(json.dumps({
            "contract": "USG-GITHUB-ACTIONS-EVIDENCE/0.1.0",
            "repository": "wizekin/USG-Workbench",
            "workflow_count": 1, "latest_run_count": 1,
            "status_counts": {"failure": 1},
            "workflows": [{
                "workflow_id": 42, "name": "Phase 5 Integrated Acceptance",
                "path": ".github/workflows/phase5-step-5-10-integration.yml",
                "state": "active", "status": "failure",
                "latest_run": {"run_id": 123, "conclusion": "failure", "head_sha": "deadbeef",
                               "html_url": "https://example.test/run/123", "event": "push"}
            }],
            "collection_errors": [],
            "interpretation_boundary": "Operational workflow result only; not semantic correctness."
        }), encoding="utf-8")
        report = collect_catalogue(
            self.root, registry_path=REGISTRY, external_manifest_path=self.manifest,
            external_checkpoint_path=self.checkpoint, pud_evaluation_path=self.pud,
            external_shard_inventory_path=self.shard_inventory, workflow_runs_path=workflow_path,
            growth_plan_path=self.growth, repository_name="wizekin/USG-Workbench",
            commit_sha="test-sha", generated_at="2026-11-12T12:00:00Z")
        self.assertEqual(report["workflow_evidence"]["latest_run_count"], 1)
        finding = next(item for item in report["discoveries"]
                       if item["kind"] == "latest_github_workflow_run_failed")
        self.assertEqual(finding["phase_impacts"], ["P5"])
        self.assertEqual(finding["details"]["run_id"], 123)
        self.assertFalse(finding["runtime_change_allowed"])

    def test_exact_duplicate_external_shard_is_reported_but_not_treated_as_stale(self):
        report = self.collect()
        self.assertEqual(report["external_lexical"]["pud_evaluation"]["status"],
                         "fresh_for_current_shard_count")
        finding = next(item for item in report["discoveries"]
                       if item["kind"] == "external_lexical_duplicate_shard_content")
        self.assertEqual(finding["details"]["duplicate_file_count"], 1)
        self.assertEqual(finding["severity"], "informational")
        self.assertFalse(finding["runtime_change_allowed"])

    def test_catalogue_never_mutates_runtime_phase_status_or_contracts(self):
        report = self.collect()
        governance = report["governance"]
        self.assertFalse(governance["runtime_mutations_performed"])
        self.assertFalse(governance["candidate_resources_promoted"])
        self.assertFalse(governance["phase_statuses_changed"])
        self.assertFalse(governance["canonical_contracts_changed"])
        self.assertTrue(governance["amendments_require_review"])
        self.assertNotIn("overall_intelligence_score", report)

    def test_report_schema_is_valid_and_markdown_explains_limits(self):
        report = self.collect()
        rendered = render_markdown(report)
        self.assertIn("External records remain candidate evidence", rendered)
        self.assertIn("Open-World", rendered)
        self.assertIn("phase routing", rendered)
        self.assertTrue(report["discoveries"])


if __name__ == "__main__":
    unittest.main()
