# USG Phase 8 — System-Wide Evidence, Resource, and Development Intelligence

**Phase:** 8  
**Status:** AUTOMATED FORMAL ACCEPTANCE ENABLED; exact-head CI determines the recorded Phase 8 decision  
**Primary objective:** make every incoming USG phase and implementation decision use the latest traceable information from the entire repository: canonical contracts, seven development phases, runtime components, adapters, lexical and semantic resources, regression tests, evaluation populations, Open-World campaigns, external lexical acquisition, cross-implementation results, and evidence-driven growth plans.

## 1. Why Phase 8 exists

USG is a multi-part system, not a single interpreter. Its useful assets and results are spread across normative specifications, separate implementation lines, phase roadmaps, tests, benchmark corpora, resource registries, data branches, GitHub Actions, immutable campaign bundles, and planning reports. A phase that consults only its immediate predecessor can unknowingly duplicate work, ignore an available resource, reuse stale measurements, or claim a capability that was only tested in a different population.

Phase 8 creates a continuously refreshed system evidence and resource catalogue. Future work will use that catalogue as a mandatory planning input. The catalogue is not a new semantic runtime, a second canonical database, or an overall intelligence score.

## 2. Mission and non-goals

Phase 8 must:

1. discover and index the system's specifications, schemas, phases, code, adapters, resources, benchmarks, tests, workflows, and evidence outputs;
2. record each resource's version/path/digest, evidence type, rights/use boundary, current status, and intended phase consumers;
3. collect the latest available Open-World campaign reports and preserve population/target/accounting distinctions;
4. refresh the external lexical crawl checkpoint/manifest and evaluate current shards against the pinned PUD population;
5. run the existing evidence-driven growth planner and include its ranked findings, example cases, and acceptance gates;
6. map each finding to existing phases and workstreams before creating a new phase proposal;
7. detect stale, missing, contradictory, or scope-mismatched evidence;
8. preserve an append-only, reproducible history of collected snapshots;
9. require every later phase step to declare which source families, resource versions, evidence populations, and acceptance artifacts it consumes.

It does not:
- make every subsystem one runtime;
- turn lexical data into active runtime knowledge;
- auto-resolve Phase 7 unresolved mappings;
- infer semantic correctness from execution success or structural validity;
- replace SQLite as the canonical document store;
- modify any previously accepted phase, canonical contracts, or runtime resources automatically;
- collapse all system capability into one score.

## 3. Phase inputs and evidence classes

The initial registry must cover, at minimum:

- canonical semantic interchange: USG-SEM/1.0, schemas, adapters, and preservation tests;
- Phases 1–7: each roadmap, completion/acceptance record, implementation boundary, continuation tracker, and related frozen corpus;
- structured reasoning and evidence assessment;
- canonical SQLite persistence, API/CLI, and Kernel Lab;
- Phase 4 and Phase 5 interpretation stages, resource catalogues, and benchmarks;
- Phase 6 construction candidates, automatic acceptance results, and continuation state;
- Phase 7 typed knowledge, rights-aware adapters, mappings, relations, retrieval, inspection, and its frozen 102-case exit report;
- USG-LEXICAL-CANDIDATES/0.1.0 and its candidate-only adapter;
- OOV, homograph, sense ambiguity, and morphology regressions;
- Open-World capability inventory, target registry, generator, runner, scorers, oracles, failure attribution, adaptive discovery, coverage ledger, and immutable campaigns;
- daily evidence-driven growth plans and their source campaign IDs;
- external lexical data branch checkpoint, manifest, shard inventory, PUD evaluation, and rights/provenance boundaries;
- naturalistic PUD pilot, cross-implementation conformance, system-wide assessments, backlog, and other versioned resources discovered later.

Evidence classes must remain distinct: normative contract, accepted component evidence, bounded synthetic evidence, randomized Open-World evidence, naturalistic input-only evidence, external candidate evidence, runtime candidate-only evidence, diagnostic experiment, planning evidence, and historical baseline.

Use modes must also remain explicit: normative, runtime, read-only adapter, candidate-only, benchmark-only, evaluation-only, planning-only, and historical-only.

## 4. Ten-step roadmap

| Step | Deliverable | Acceptance condition | Status |
|---|---|---|---|
| 8.1 | Versioned system evidence source registry | All required evidence families and phase status records have stable IDs, source paths, evidence classes, consumer phases, refresh policy, and guardrails | Implemented on main; validation workflow active |
| 8.2 | Phase/resource-consumption map | Each phase declares required and optional source families, allowed use modes, and prohibited uses; explicitly states that availability does not prove runtime consumption | Implemented on main; validation workflow active |
| 8.3 | Repository-wide evidence collector | Deterministic path discovery and SHA-256 inventory; schema-validated JSON/Markdown catalogue; missing files are explicit | Implemented on main; validation workflow active |
| 8.4 | Operational evidence refresh | Current external branch manifest/checkpoint and physical shard hashes, fresh PUD lexical/morphology evaluation, recent campaign reports, current growth plan, and latest run status for each GitHub Actions workflow are collected in one snapshot | Implemented on main; collection outcomes remain source-dependent and are reported explicitly |
| 8.5 | Freshness and evidence-quality diagnostics | Detect stale PUD/report shard-count mismatch, physical shard drift, missing workflow results, failed workflow runs, missing reports, old baselines, population mismatch, rights uncertainty, and unsupported inference from evidence | Implemented on main with explicit stale/invalid/future/unknown timestamp states and lexical/Open-World reconciliation diagnostics |
| 8.6 | Discovery deduplication and impact classification | New findings link to existing SYS backlog items, continuation tracker IDs, prior findings, or a stable new discovery record | Stable kind/evidence/scope fingerprints, same-snapshot deduplication, prior-snapshot recurrence links, and existing backlog-ID matching implemented on main |
| 8.7 | Phase-aware routing and amendment proposals | Existing continuation is preferred; accepted phases can receive explicit amendment proposals; contract changes route through migration plans | Stable draft-only proposal records implemented on main; no phase, contract, or runtime mutation is permitted |
| 8.8 | Mandatory phase resource manifest | Every Phase 8+ roadmap has a schema-valid phase resource manifest; future step changes must update it with exact resource/evidence dependencies and candidate/runtime boundaries | Implemented for Phase 8 baseline; CI policy gate active |
| 8.9 | Growth-planner integration | Growth plan, Open-World findings, lexical gaps, conformance gaps, and knowledge-layer findings are prioritized in one explainable view without overriding source-specific metrics | Cross-source queue now includes explicit cross-runtime capability/gate gaps and Phase 7 unresolved mapping candidates; source metrics remain separate and no combined semantic score is calculated |
| 8.10 | Integrated Phase 8 exit acceptance | The required validation job passes on the exact catalogue commit and every integrated acceptance check passes; the decision records its commit, workflow run, attempt, checks, and deterministic decision ID | Automatic formal acceptance is implemented; failures remain blocked and preserve diagnostics |

## 4A. Discovery management and integrated prioritization (8.6–8.9)

The collector assigns a stable discovery key from finding kind, evidence references, and phase scope; wording changes alone do not create a new identity. Duplicate observations in one snapshot are collapsed, and the last 100 append-only catalogue snapshots are consulted for recurrence links. Existing backlog IDs are linked only when present in the backlog document; the collector never creates, closes, or reprioritizes backlog work items.

Each discovery receives a descriptive phase-impact classification and an explicit migration-review flag when a normative contract or canonical invariant change is declared. This classification does not change phase status. The integrated queue orders findings by severity and displays recurrence and growth-planner evidence as separate reasons. Original planner metrics (including priority score, blocker counts, recurrence, and acceptance gate) remain source metrics; no aggregate intelligence or semantic-quality score is calculated. All proposals remain review-required and runtime changes remain disabled.

## 5. Resource-consumption rule for every later phase

Before a phase or step implementation begins, it must publish a resource-consumption entry containing:

- source-family IDs from the system evidence registry;
- exact contract, resource, corpus, and implementation versions/digests;
- whether each source is normative, runtime, candidate-only, benchmark-only, evaluation-only, or planning-only;
- current accepted and unaccepted capabilities that the step will reuse;
- source rights/provenance constraints;
- expected coverage/benefit and known limitations;
- tests and independent evidence needed to validate any changed behavior.

A resource being present in the repository does not mean the runtime currently imports it. The resource-consumption map records declared relationships; tests and code inspection must verify actual integrations.

## 6. Phase-aware discovery and modification policy

New observations follow this state progression:

`observed → collected → deduplicated → impact_assessed → routed → proposal → implemented → validated → accepted`

Routing order:

1. **Existing continuation first.** If the evidence belongs to a known open continuation (for example Phase 6 construction expansion or the external lexical crawl), update that workstream rather than inventing a new phase.
2. **Amend an accepted phase when appropriate.** If a new discovery extends a Phase 2–7 capability or exposes a gap within its boundary, create an explicit amendment proposal against that phase. Keep its old acceptance record intact and add a new scope/version-specific acceptance record.
3. **Use a versioned migration for normative changes.** Any change to USG-SEM/1.0, accepted schemas, canonical persistence invariants, or interpretation contracts requires a dedicated migration, compatibility adapter, and all affected regression gates.
4. **Create a new phase only for genuinely cross-cutting work.** Phase 9 and later are not pre-locked. Their definitions should arise from collected evidence, dependency analysis, and the remaining system-wide capability map.

The collector may create observations and candidate proposals automatically. The dedicated Phase 8 acceptance evaluator may automatically accept only Phase 8's bounded evidence/development-intelligence control-plane scope, and only after the upstream GitHub Actions validation job succeeds on the exact catalogue commit and every integrated gate passes. It records a traceable decision. A blocked result cannot be overridden by manual approval; missing evidence or failed checks must be corrected and the workflow rerun. This authority does not extend to other phases, gold-label changes, threshold weakening, candidate-resource promotion, runtime semantic changes, or normative-contract changes; those remain separately governed.

## 7. Initial evidence baseline and warnings

The 12 November 2026 collection baseline starts from:
- the accepted USG-SEM/1.0 canonical contract and its adapter family;
- bounded Phase 1–5 completion records;
- Phase 6 registered synthetic acceptance plus a separately open continuation tracker;
- Phase 7 completion for its frozen English/MSA Arabic profile (102 retrieval cases, two polysemy cases, 43 unresolved mappings retained);
- the current external lexical data branch manifest, refreshed by the collection workflow rather than an old assessment snapshot;
- stored Open-World campaigns and the daily growth planner, with their actual population and execution accounting preserved.

The historical Open-World OW-6 campaign was partial and contained 3,000 unconstrained-random plus 106 controlled-diagnostic cases; it was not a naturalistic user-request corpus. The earlier capability assessment's external lexical figures described a much smaller historical checkpoint. They must not be copied forward as current. The collection workflow recalculates English PUD lexical/morphology coverage against the latest available shard set and records the exact shard count and pinned PUD source.

## 8. Snapshot and reproducibility policy

Each collection run creates an append-only snapshot under:

`evaluations/system-wide/evidence-catalogue/<run-id>/`

A snapshot contains:
- catalogue JSON and human-readable Markdown;
- growth-plan JSON and Markdown;
- latest external lexical manifest and checkpoint;
- current external PUD evaluation report or an explicit collection error;
- source commit and external data-branch commit;
- path digests, evidence references, population counts, and collection timestamp.

Historical snapshots are never overwritten. A later run uses a new path. The latest main-branch snapshot is the latest published snapshot, not necessarily the latest Actions run if publication permissions or a workflow failed. Live Actions status remains a separate operational source.

## 9. Exit boundary

Phase 8 will be accepted when a newly created development phase can reliably answer:

- What relevant implementations, contracts, resources, tests, and prior results already exist?
- Which of those are accepted, candidate-only, diagnostic, historical, or missing?
- Which source version and rights boundary does each dependency have?
- Which failures or coverage gaps should drive the work?
- Is the correct route an existing phase continuation, an amendment to an accepted phase, a migration, or a genuinely new phase?
- What regression and independent evidence is required before the change can be accepted?

Phase 8 is a system-wide development-intelligence layer. It does not itself establish broader natural-language understanding.
