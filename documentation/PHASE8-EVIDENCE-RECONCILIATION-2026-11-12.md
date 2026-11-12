# Phase 8 Evidence Reconciliation — 12 November 2026

## External lexical shard inventory

The external lexical data branch is append-only. Its physical shard inventory may contain multiple paths for one logical crawl batch when a workflow retry republishes byte-identical content.

The evidence collector therefore reports both:
- **Physical files and bytes**, which remain part of storage accounting and are never silently deleted.
- **Logical batches**, identified by the batch number in the shard path and reconciled against `manifest.batch_count`.

A repeated batch number with identical SHA-256 content is a duplicate physical copy: it remains visible as a warning and counts once as a logical batch. A repeated batch number with different content is a consistency error. The PUD evaluator also deduplicates byte-identical shard content before counting entries, forms, lemmas, and candidate coverage. Its report records physical shard count, unique shard count, duplicate-copy count, and content digests.

This is a metadata/evaluation correction. It does not rewrite the historical lexical-data branch or change the source licence and provenance records.

## Open-World pipeline-version mismatch

Historical execution records whose declared pipeline contract/version identity does not exactly match the configured target profile are counted under both `pipeline_version_mismatch_record_counts` and `pipeline_identity_mismatch_record_counts`. The growth-plan warning preserves the observed contract and version together, and these records are excluded from stage-dependency attribution. This is intentional: applying a newer dependency graph to an older or unknown pipeline version could mislabel the first blocker and downstream co-occurrences.

The 1,058 records reported in the 12 November 2026 growth-plan snapshot are therefore retained as a historical version-compatibility warning, not converted into 1,058 proven runtime defects. They can be attributed only when a matching historical stage profile is available, or re-evaluated by rerunning the cases against a declared current profile. No historical execution record is edited to manufacture a match.

## Refresh and acceptance boundary

After these changes merge to `main`, the System Evidence and Resource Collection workflow should run on the merge commit. Its new append-only snapshot should contain:
- the physical and logical lexical inventory reconciliation;
- a fresh PUD evaluation over unique shard content;
- the unchanged, explicit Open-World version-mismatch accounting; and
- a newly generated Phase 8 integrated acceptance report.

The integrated gate may report `eligible_for_review` or `blocked`. It must not set `phase_accepted=true`. Explicit human review and acceptance remain required.
