# USG System-Wide Evidence and Resource Integration

**Contracts:** `USG-SYSTEM-EVIDENCE-SOURCE-REGISTRY/0.1.0`, `USG-SYSTEM-EVIDENCE-CATALOGUE/0.1.0`, and `USG-PHASE-RESOURCE-MANIFEST/0.1.0`.

## Purpose

The USG Workbench contains multiple versioned systems, not one monolithic runtime. Its useful knowledge is distributed across the canonical semantic contract, phase implementation records, rule and resource registries, candidate adapters, Open-World campaigns, benchmark fixtures, external lexical shards, cross-implementation diagnostics, workflow artifacts, and growth plans.

This integration layer indexes those assets and results so future development begins with a review of what already exists, what is accepted, what is candidate-only, which evidence is current, and which parts of the system should consume them. It is a development-intelligence control plane. It does not become another semantic runtime or persistence authority.

## Machine-readable sources

- `config/usg-system-evidence-source-registry-0.1.0.json` — stable source-family IDs, repository path patterns, use modes, consumers, refresh policies, and guardrails.
- `config/usg-phase-resource-consumption-map-0.1.0.json` — required/optional source families for each phase, allowed use modes, and routing policy.
- `config/usg-long-term-development-plan-0.1.0.json` plus `documentation/USG-LONG-TERM-DEVELOPMENT-PLAN.md` — proposed long-horizon trajectory, explicit future work packets, dependencies, exit criteria, and plan-maintenance policy. Future phases are planning labels, not implementation authorization.
- `specifications/usg-system-evidence-source-registry-0.1.0.schema.json` — registry schema.
- `specifications/usg-system-evidence-catalogue-0.1.0.schema.json` — generated catalogue schema.
- `specifications/usg-phase-resource-manifest-0.1.0.schema.json` and `templates/phase-resource-manifest-0.1.0.template.json` — mandatory dependency/evidence description for incoming phase steps.

The registry includes the canonical USG-SEM/1.0 boundary, Phase 1–7 records, structured reasoning, SQLite persistence, Phase 4/5 interpreters, Phase 6 candidate expansion, Phase 7 knowledge, lexical candidate adapter, OOV/ambiguity regressions, Open-World evaluation, evidence-driven growth planning, external lexical acquisition, naturalistic input-only evaluation, cross-implementation conformance, bundled resources, system assessments/backlog, and the long-term development plan.

The phase/resource map declares intent to reuse a source. It does not prove that the runtime imports it. Actual integration must be verified in code and tests.

## Collection workflow

The scheduled workflow `.github/workflows/system-evidence-collection.yml` runs daily and can be dispatched manually. It:

1. inventories registered source families in the selected main-branch commit and records SHA-256/file-size metadata;
2. fetches the current `usg-external-lexical-data` branch checkpoint and manifest;
3. recalculates English PUD exact-form/lemma candidate coverage and mapped morphology-candidate metrics against the currently published lexical shards;
4. runs the existing evidence-driven growth planner against recent immutable Open-World campaigns;
5. collects population-specific campaign counts and execution accounting;
6. collects the latest non-PR run status for each GitHub Actions workflow and distinguishes success, failure, in-progress, no-run, disabled, and collection-error states;
7. creates a schema-validated system evidence catalogue, discovery list, freshness diagnostics, and phase-impact routes;
8. generates stable review-only phase proposals and evaluates the integrated Phase 8 gate; formal acceptance is automatic only after the upstream validation job passes on the exact catalogue commit and all integrated checks pass;
9. stores the catalogue, formal acceptance decision (including exact commit, workflow run/attempt, check results, and deterministic decision ID), and source evidence in an append-only run-specific directory and uploads it as an Actions artifact;
10. attempts to publish the snapshot through a pull request.

The integrated acceptance result is either `accepted` or `blocked`. `accepted` is a formal automatic decision for the bounded Phase 8 development-intelligence/control-plane scope, issued only after exact-head GitHub Actions validation and all integrated checks pass. A `blocked` result is preserved with the snapshot rather than discarded; no human approval can override a failed or missing check. The decision does not authorize semantic-runtime changes, candidate promotion, canonical-contract changes, or acceptance of any other phase.

A missing branch, evaluation error, missing campaign, or absent report is recorded as unavailable evidence; it is never interpreted as a zero score. The latest committed snapshot is the latest published snapshot, not necessarily the latest workflow attempt if publication was blocked.

## Refreshing manually

With the repository checkout, Python 3.11, and `jsonschema==4.23.0` installed:

```bash
python -m unittest discover -s tests -p "test_system_evidence_catalogue.py" -v

python -m tools.open_world_evaluation.growth_controller \
  --max-campaigns 20 \
  --output /tmp/usg-growth-plan.json \
  --markdown /tmp/usg-growth-plan.md

python -m tools.usg_external_lexical_v0_1_0.pud_evaluation \
  --data-dir /path/to/usg-external-lexical-data/shards \
  --output /tmp/external-lexical-pud-evaluation.json

python -m tools.system_evidence.collector \
  --external-manifest /path/to/state/manifest.json \
  --external-checkpoint /path/to/state/checkpoint.json \
  --pud-evaluation /tmp/external-lexical-pud-evaluation.json \
  --growth-plan /tmp/usg-growth-plan.json \
  --commit-sha <main-commit-sha> \
  --external-branch-commit <data-branch-commit-sha> \
  --output /tmp/system-evidence-catalogue.json \
  --markdown /tmp/system-evidence-catalogue.md
```

If PUD evaluation fails, pass `--pud-error` with a JSON error object and do not pass a stale previous evaluation as current. If an external input is not available, omit it and record why it could not be collected.

## Resource and evidence labels

Every registered source carries:
- a **use mode** (normative, runtime, read-only adapter, candidate-only, benchmark-only, evaluation-only, planning-only, historical-only);
- an **evidence class** (accepted component evidence, bounded synthetic evidence, randomized Open-World evidence, naturalistic input-only evidence, external candidate evidence, diagnostic experiment, planning evidence, historical baseline, or normative contract);
- intended consumer phases and explicit limitations/guardrails.

Those labels prevent an available file from being mistaken for an accepted runtime dependency. External lexical shards are candidate evidence even when their crawl/audit is successful. UD/PUD input is not semantic gold. Open-World execution results are not a universal correctness denominator. Phase 7 unresolved mappings remain unresolved.

## Long-term roadmap synchronization

The repository maintains a separate long-term development plan in
`documentation/USG-LONG-TERM-DEVELOPMENT-PLAN.md` and
`config/usg-long-term-development-plan-0.1.0.json`. The plan is a planning
artifact, not a semantic runtime or a phase acceptance authority.

The workflow `.github/workflows/usg-long-term-roadmap-sync.yml` runs on relevant
main-branch changes, weekly, and manually. Its deterministic synchronizer reads
the phase registry, SYS backlog implementation-status table, Phase 6
continuation tracker, and Phase 8 exact-head decision artifact. It fingerprints
the plan's source files, reports affected workstreams from changed paths, and
publishes a status-only pull request.

The synchronizer does not edit the strategic plan or source-of-truth trackers,
infer completion from a merge, start future phases, promote candidate resources,
or change runtime/canonical semantics. New strategy, priority changes, phase
boundary changes, and semantic acceptance remain explicit proposals with their
own evidence and gates.

## Mandatory manifest for incoming steps

Every new phase step should add or update a resource manifest based on `templates/phase-resource-manifest-0.1.0.template.json`. It records exact source family/path/version/digest, use mode, whether runtime integration has actually been verified, rights status, evidence populations, dependencies, and acceptance gates.

Before a new step begins:
1. search the source registry and catalogue for reusable contracts, modules, resources, benchmarks, and diagnostics;
2. inspect the exact version/commit and verify it fits the proposed capability;
3. declare whether the source is required or optional and its allowed use mode;
4. reuse existing tests and add gaps to the relevant phase's regression suite;
5. state what evidence would justify acceptance and what it does not establish.

The consumption map's entries are defaults; the per-step manifest is the exact declaration. A listed source-family consumer is not proof of runtime usage.

## Discovery routing: continue, amend, migrate, or create

New findings progress through:

`observed → collected → deduplicated → impact_assessed → routed → proposal → implemented → validated → accepted`

Route in this order:

1. **Existing continuation:** use an open continuation tracker/workstream when the discovery fits it (for example, Phase 6 construction expansion or the external lexical crawl).
2. **Existing phase amendment:** if a finding expands or exposes a gap in an accepted Phase 1–7 capability, create an explicit amendment proposal against that phase. Preserve the old acceptance record; do not silently rewrite it.
3. **Versioned migration:** if the change alters USG-SEM/1.0, a normative schema, accepted API/output semantics, or canonical persistence invariants, use a separate migration contract and compatibility plan.
4. **New cross-cutting phase:** only use a future phase when the evidence-backed capability is genuinely cross-cutting and no current continuation or amendment owns it.

The collector creates observations and suggested routes only. The latest Actions run status is operational execution evidence: a passing workflow does not prove the semantic correctness of the evaluated output. It never changes phase statuses, code, runtime resources, canonical contracts, or promotion decisions. A later implementation may be automated in a governed branch/PR workflow, but semantic changes still need their independently declared acceptance evidence.

## Evidence interpretation rules

- Normative contracts are authoritative for interchange; code comments and historical docs do not silently supersede them.
- Accepted phase results are bounded by their recorded profile, language, corpus, version, and metrics.
- Candidate lexical/semantic resources remain separate from active runtime resources.
- Randomized, controlled diagnostic, naturalistic, synthetic, and external lexical populations are never pooled without a defensible common denominator.
- Missing, skipped, unexecuted, stale, or failed infrastructure evidence is reported explicitly.
- First-blocker attribution is a diagnostic starting point, not proof of root causation.
- Cross-implementation agreement is not proof of semantic correctness.
- No overall intelligence/AGI score is computed.

## Current Phase 8 status

The current implementation inventories source families and phase consumers, collects stored campaign and growth-planner results, refreshes external lexical/PUD evidence, records workflow outcomes, detects stale and contradictory evidence, deduplicates recurring findings, classifies phase impacts, and creates review-only proposal records, and integrates cross-implementation capability gaps plus the Phase 7 unresolved mapping inventory into the same discovery queue. The integrated gate checks structural coverage and governance and can only mark the work eligible for human review or blocked; it cannot accept Phase 8. Operational collection now runs the integrated gate and preserves its report with each snapshot. A blocked result is retained for diagnosis rather than discarded. Review of generated proposals, confirmation that a production snapshot is eligible for review, and explicit Phase 8 acceptance remain outstanding.
