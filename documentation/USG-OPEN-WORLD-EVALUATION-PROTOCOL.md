# OW-1 — Evaluation protocol and reporting contracts

**Status:** OW-1 implementation  
**Protocol version:** 1.0.0  
**Prerequisite:** OW-0 repository inventory

## Objective

OW-1 converts the open-world program plan into machine-checkable record contracts. A scenario, an execution attempt, and a campaign report are separate records. The protocol is versioned so later generators and runners can evolve without silently changing old results.

Schemas:
- Scenario: tools/open_world_evaluation/schemas/scenario.schema.json
- Source provenance: tools/open_world_evaluation/schemas/source-provenance.schema.json
- Execution result: tools/open_world_evaluation/schemas/execution-result.schema.json
- Campaign report: tools/open_world_evaluation/schemas/campaign-report.schema.json

## Three populations

1. **unconstrained_random** — generated requests and combinations. A meaningful share remains unclassified before execution. The OW-0 inventory is a routing aid, not a closed task vocabulary.
2. **naturalistic** — examples from public datasets or documentation with approved licenses and privacy review. Preserve source URL, retrieval time, license decision, redistribution permission, privacy review, content digest, attribution, and transformations. A public URL is not a license grant.
3. **controlled_diagnostic** — fixtures with an independent oracle for controlled diagnosis. This population cannot replace random or naturalistic testing.

Population results remain separate. High diagnostic accuracy cannot mask weak random or naturalistic performance.

## Scenario contract

Every scenario pins its case ID, population, creation time, generator/version, seed mode, master seed, case seed, source record, exact input text and UTF-8 SHA-256, target implementation/version/entry point/interface, taxonomy/unclassified flag, oracle declaration, and resource limits.

The validator recomputes the exact input digest from UTF-8 bytes. Naturalistic cases require a public-source kind, URL, retrieval timestamp, approved license, explicit redistribution permission, and approved privacy review. Controlled diagnostic cases require a non-empty independent oracle. Unconstrained random cases may be unclassified and may have no oracle.

## Execution result contract

Every attempt identifies the case, implementation/version/entry point, and exact tested commit. It records timestamps, resource measurements, output digests, structural validation outcomes, optional scoring, failure category, and artifact digests.

The ten outcomes remain distinct:
- completed
- unsupported
- ambiguous
- abstained
- partial
- invalid_output
- timeout
- crashed
- infrastructure_error
- not_executed

They must never be collapsed into one pass/fail value or silently removed from denominators. Unsupported is not a crash; ambiguity is not automatically an error.

## Campaign report contract

A report pins repository commit, protocol/generator/evaluator versions, master seed, timestamps, every outcome count, per-population outcomes, coverage, failure families, novel clusters, limitations, and artifact hashes. Partial and failed campaigns are first-class reports.

The validator checks that:
- all ten outcome counts sum to attempted;
- completed matches outcome_counts.completed;
- all three populations occur exactly once;
- per-population counts reconcile with both population attempt totals and campaign-level totals;
- a complete report has a finish timestamp and at least one attempt.

## Scoring and independence

- Schema, source-span, provenance, graph-invariant, persistence, and replay checks may be deterministic where the target exposes those contracts.
- Semantic correctness scores require an independent oracle. USG's own output, its adapter, or an external parser baseline cannot serve as its own gold annotation.
- Metamorphic tests evaluate declared transformations and invariants, not broad truth.
- Human-rubric scores must preserve the rubric and reviewer provenance.
- Confidence/ranking scores are not probabilities unless separately calibrated and validated.
- No global headline score replaces per-population, per-target, and per-outcome breakdowns.

## Safety and data handling

- Test input is data; the runner must never execute it as shell commands.
- Network is disabled by default per scenario.
- Do not import private chats, secrets, credentials, payment data, or personal records without explicit authorization and a lawful basis.
- Restricted datasets may be referenced by metadata and hashes only when redistribution is not permitted; do not commit prohibited raw data.
- Any future network-based retrieval must use separately reviewed, allowlisted sources.

## OW-1 acceptance

OW-1 is complete when all four schemas validate as Draft 2020-12, source/oracle policies are enforced, ten result outcomes remain individually representable, campaign totals reconcile, positive and negative tests pass, and GitHub Actions runs the validator.

This stage accepts the protocol machinery only. It does not mean that the random generator, isolated execution runner, live scoring campaign, or pilot exists yet.
