# USG evidence repair report — logical shard reconciliation

**ID:** USG-EVID-LOGICAL-SHARD-COUNT-2026-11-19  
**Base commit:** `41a429ea3d389cf4548d49796221674edc43ed2f`  
**Implementation branch:** `fix/system-evidence-logical-shard-count-20261119`  
**Implementation commit before this report:** `06252eed57c85e5e4328ca313049f46729e41571`  
**Scope:** Phase 8 evidence diagnostics and reporting only. No lexical data, runtime semantic rules, gold labels, or canonical contracts changed.

## Reproduction

The lexical shard auditor deliberately distinguishes logical batches from physical files. Identical duplicate physical copies are warnings, remain included in physical storage accounting, and do not increase the logical batch count.

The current crawl evidence demonstrates this distinction:

- Crawl run [#85](https://github.com/wizekin/USG-Workbench/actions/runs/44536390794): 31 logical batches, 32 physical shard files, one identical duplicate; remote audit status `passed_with_warnings`, with no audit errors.
- PUD candidate evaluation [#56](https://github.com/wizekin/USG-Workbench/actions/runs/44587417135): evaluated shard count 31.
- The previous system-evidence catalogue [run #94](https://github.com/wizekin/USG-Workbench/actions/runs/44471808037) compared physical file count to logical manifest batch count. That conflated duplicate physical storage with missing/extra logical batches and produced a false high-severity stale-evaluation diagnosis.

## Repair hypothesis and acceptance criteria

Use `logical_batch_count` plus the auditor's `matches_manifest` result for reconciliation. Preserve `physical_file_count`, duplicate-copy count, and physical bytes separately for storage reporting.

Acceptance criteria:

1. 31 logical batches / 32 physical files / one identical duplicate reconciles as matched.
2. A true logical batch-count mismatch or `matches_manifest=false` remains a mismatch and keeps the PUD evaluation stale.
3. Physical file counts and storage bytes remain visible; duplicates are not silently discarded.
4. Candidate-only and no-runtime-mutation boundaries remain unchanged.

## Changes

- `tools/system_evidence/collector.py`: reconcile using logical batches; expose logical and physical counts and duplicate-copy count; clarify Markdown output.
- `tools/system_evidence/freshness.py`: emit the shard-count contradiction only for logical batch-count disagreement.
- `tests/test_system_evidence_catalogue.py`: add duplicate-physical-copy acceptance and true logical-mismatch regression cases.
- `tests/test_system_evidence_freshness.py`: add a duplicate-copy non-contradiction regression while retaining true-mismatch coverage.

## Verification

- Exact branch freshness module and test file: **6/6 tests passed** locally with `python -m unittest discover -s tests -p 'test_system_evidence_freshness.py' -v`.
- Collector-function probe against the current 31/32/1 evidence: passed; a synthetic 30-logical-batch mismatch remained rejected.
- Full repository catalogue tests and the complete Phase 8 suite: **not run**. The local environment did not contain a full repository checkout, and the available GitHub plugin exposes no workflow-dispatch action. No GitHub CI check-run is claimed.

## Rollback and publication

This is an isolated branch based on `41a429e`; main is unchanged. Roll back by discarding this branch or reverting its collector/freshness/test commits. No pull request was opened and no merge was attempted.