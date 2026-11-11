# OW-5 — Campaign reporting and append-only regression storage

**Status:** OW-5 implementation  
**Campaign report:** schema 1.0.0  
**Bundle manifest:** 1.0.0

## Pipeline

OW-5 converts the three independent OW-1/OW-3/OW-4 streams into one immutable campaign bundle:

1. Scenario JSONL and optional generator manifest.
2. Execution-result JSONL.
3. Score-result JSONL.
4. Campaign report JSON, validated against the OW-1 campaign-report schema and the cross-population count validator.
5. Human-readable Markdown summary.
6. Bundle manifest with SHA-256 and byte-size records for every stored file.

The output layout is:

    evaluations/open-world/campaigns/<campaign-id>/
      scenario-cases.jsonl
      execution-results.jsonl
      score-results.jsonl
      generation-manifest.json       # optional
      minimized-reproducers.jsonl    # optional
      campaign-report.json
      campaign-report.md
      bundle-manifest.json

Campaign IDs are path-safe and directories are created using a temporary sibling plus an atomic rename. The destination is never overwritten. A duplicate campaign ID fails closed. Existing reports are immutable; corrections or reruns require a new campaign ID.

## Report semantics

The report records all ten target-result outcomes, every population (including populations with zero cases), per-population result records and actual attempts, targets, languages, taxonomy labels, scenarios without result records, failure families, within-campaign clusters, and artifact hashes.

A campaign is:
- **complete** only when each of the three populations has cases and every scenario has at least one actual target invocation;
- **partial** when at least one actual invocation occurred but scenario or population coverage is incomplete;
- **failed** when no actual target invocation occurred, even if not_executed result records exist.

This is a completeness classification, not a quality score. A campaign can be complete and still show many unsupported requests, crashes, or invalid outputs.

Clusters are deterministic groupings of the same observed outcome/structural failure signature within one campaign. They are marked unreviewed. A cluster is not called a newly discovered failure family until it has been compared with prior reports and reviewed by a person.

## Explicit execution accounting (additive to report v1.0.0)

The historical report field attempted is retained for compatibility and counts all execution-result records, including records whose outcome is not_executed. It must not be interpreted as the number of target invocations.

New reports add coverage.execution_accounting with:
- scenario_count: scenario records in the input bundle;
- result_record_count: all execution-result records (must equal legacy attempted);
- actual_attempt_count: result records whose outcome is not not_executed;
- not_executed_record_count: target records explicitly marked not_executed;
- scenario counts with any result, with an actual attempt, with only not-executed records, with no result record, and with multiple result records;
- per-target versions of the same result/attempt/not-executed accounting.

Per-population rows carry the same accounting object. These counts must reconcile across target, population, and campaign levels. The legacy coverage.unexecuted_case_count means scenarios with no result record; it does not count not_executed result records.

Campaign status now follows actual execution:
- **complete** requires at least one actual attempt for every scenario and non-empty coverage of all three populations;
- **partial** means at least one actual attempt occurred, but scenario or population coverage is incomplete;
- **failed** means no actual target invocation occurred, even if not_executed result records were written.

## First-blocking-stage attribution

New reports include coverage.stage_attribution. The analyzer uses explicit blocking diagnostics or blocking stage statuses and a versioned target-specific dependency graph in tools/open_world_evaluation/stage_dependency_graph.json. It identifies first blockers as blocked stages with no other blocked declared ancestor. Independent parallel blockers are retained together. It reports:
- counts by first blocking stage, including multiple parallel first blockers;
- dependency-related later-stage blocking diagnostic co-occurrences;
- breakdowns by target, population, and language;
- representative case IDs;
- records without a target-result payload, without a blocking diagnostic, and with unmapped stage names.

This is deliberately called **first blocker**, not proven root cause. A dependency edge means a stage consumes an upstream artifact; it does not prove an upstream failure caused a later diagnostic. The Phase 4 and Phase 5 profiles differ because their stage dependencies differ. Unknown stages and targets without a registered graph profile are reported rather than forced into a guessed order. Missing diagnostics are not silently assigned to lexical or any other stage.

The accounting and attribution are reporting/diagnostic improvements only. They do not change interpreter behavior or establish semantic correctness.

## Bounded failure minimization

The delta-debug utility attempts to remove token chunks while preserving the same failure signature:
- structural-invalid checks must remain the same, or
- runtime outcomes such as timeout, crash, or invalid output must remain the same.

Only a bounded number of cases and re-execution attempts may be requested. The original case and execution record are never mutated. A minimized reproducer receives a new case ID and updated source digest, and is saved as a separate artifact. Unsupported/ambiguous/partial semantic outcomes are not automatically minimized because reducing their text can change meaning or move the input outside the tested scope.

Example:

    python -m tools.open_world_evaluation.minimize_failures \
      --cases campaign-cases.jsonl \
      --results campaign-results.jsonl \
      --scores campaign-scores.jsonl \
      --output minimized-reproducers.jsonl \
      --commit-sha <tested-commit-sha> \
      --max-cases 5 --max-attempts 24

## Build and store a bundle

After generating, executing, and scoring the cases:

    python -m tools.open_world_evaluation.campaign_pipeline \
      --campaign-id OWC-2026-11-11-PILOT-001 \
      --cases campaign-cases.jsonl \
      --results campaign-results.jsonl \
      --scores campaign-scores.jsonl \
      --generation-manifest campaign-cases.jsonl.manifest.json \
      --commit-sha <tested-commit-sha> \
      --output-root evaluations/open-world/campaigns

The resulting directory should be committed as a new path in a pull request. Do not amend or replace a published campaign directory. For recurring work, future scheduled workflows can open a new report PR for each unique campaign ID.

## OW-5 acceptance boundary

OW-5 provides validated JSON and Markdown reports, reproducible artifact hashes, failure clustering, optional bounded minimization, and local append-only bundle creation. It does not make empty populations appear populated, does not infer semantic accuracy, and does not silently change generator, evaluator, or USG thresholds.
