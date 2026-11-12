# USG Long-Term Development Plan

**Plan contract:** USG-LONG-TERM-DEVELOPMENT-PLAN/0.1.0  
**Repository:** wizekin/USG-Workbench  
**Baseline review:** 12 November 2026  
**Status:** Long-horizon plan established; future phases are proposals, not started work.  
**Machine-readable source:** [config/usg-long-term-development-plan-0.1.0.json](../config/usg-long-term-development-plan-0.1.0.json)  
**Schema:** [specifications/usg-long-term-development-plan-0.1.0.schema.json](../specifications/usg-long-term-development-plan-0.1.0.schema.json)  
**Automatic synchronization:** [USG Long-Term Roadmap Synchronization](../.github/workflows/usg-long-term-roadmap-sync.yml)

---

## 1. Why this plan exists

USG is a growing collection of versioned semantic contracts, interpreters, knowledge resources, reasoning services, evaluation systems, adapters, and developer tools. Its long-term development must not depend on one person or one AI model remembering every dependency, old decision, limitation, and acceptance boundary.

This plan is the portfolio-level direction and execution manual for future USG development. It is designed so that a capable coding agent can select one bounded work packet, inspect the exact dependencies, implement it, run the declared tests, publish evidence, and update the plan without having to redesign the project at every step.

The plan deliberately has two layers:

1. **Strategic layer:** explains the intended architecture, long-term direction, phase dependencies, safety rules, and maturity gates. It changes only when evidence or architecture decisions justify a reviewed amendment.
2. **Operational layer:** records the current state of phases, linked backlog items, Phase 6 continuation items, source fingerprints, and changed workstreams. It is refreshed automatically from repository evidence.

The master plan is not a substitute for the detailed phase roadmaps, source registry, resource map, continuation tracker, specifications, or tests. It connects them and defines how they should be used.

## 2. Current baseline and honest capability boundary

This plan starts from the repository state observed on 12 November 2026. The operational sources are newer and more authoritative than old assessment prose when their scopes conflict.

| Area | Current evidence-backed state | Planning consequence |
|---|---|---|
| Canonical semantic interchange | USG-SEM/1.0 and its adapters are established and versioned | Preserve the contract; use a separately versioned migration if it must change |
| Structured reasoning | Phase 2 foundation accepted for its explicit rule/evidence/query scope | Extend through typed dependencies and independently tested reasoning capabilities |
| Persistence | Phase 3 SQLite-backed canonical document store and workspace accepted | Keep SQLite as the single canonical document authority |
| Interpretation | Phase 4 and Phase 5 provide narrow accepted profiles; Phase 6 has a bounded accepted exit | Expand one construction/profile at a time; do not generalize bounded scores |
| Phase 6 continuation | Bounded exit is accepted, while broader construction, scope, reference, projection, and naturalistic-evidence items remain open | Continue through stable P6-CONT identifiers; do not reopen accepted exit steps |
| Semantic knowledge | Phase 7 is accepted for its frozen profile; unresolved cross-language mappings remain visible | Integrate the existing knowledge layer through explicit adapters; do not build a second knowledge database |
| Lexical acquisition | Scheduled external collection and a candidate-only lexical adapter exist | Improve source quality, coverage, and evaluation before considering runtime promotion |
| Open-World evaluation | Randomized campaigns, target adapters, accounting, diagnostics, and a growth planner exist | Use it to locate failures, not as a single semantic-accuracy score |
| Naturalistic evaluation | A bounded English/Arabic PUD pilot exists; its Arabic material is translated and it is not a conversational-request corpus | Complete and characterize it, but do not call it semantic gold |
| Cross-runtime behavior | An implementation inventory exists, but shared conformance is not established | Build common fixtures and run the implementations separately |
| Autonomous improvement | Evidence aggregation and prioritization are automated; a general semantic repair/growth loop is not established | Automate deterministic repairs first; keep semantic candidates gated |
| Phase 8 | Automatic exact-head acceptance is implemented in the repository; a post-merge production acceptance artifact was not verified at the time of this plan | Verify Phase 8 using its authoritative artifact before starting Phase 9 |

The 12 November system-wide capability assessment is a useful historical diagnosis, but its measurements predate some later Phase 6 work. Use the live system improvement backlog, Phase 6 continuation tracker, Phase 7 and Phase 8 records, and current evidence snapshots for operational status.

**What this baseline does not claim:** unrestricted English or Arabic understanding, general semantic correctness, universal knowledge, objective truth verification, human-equivalent reasoning, or AGI. Those are not current accepted capabilities.

## 3. Long-term objective

Build a modular, inspectable, multilingual semantic representation and reasoning system that:

1. preserves what was actually said and where it came from;
2. identifies language-specific lexical and grammatical evidence without hiding ambiguity;
3. constructs syntax and semantic relations using explicit, versioned construction rules;
4. composes words, roles, events, states, properties, operators, and discourse into typed semantic structures;
5. projects meaning into canonical USG documents only when the projection is loss-aware;
6. connects interpretation to provenance-bearing knowledge through read-only, versioned interfaces;
7. performs bounded reasoning with derivations, evidence, conflict handling, and explanations;
8. reports exactly what is supported, unresolved, ambiguous, unsupported, or unknown;
9. improves through reproducible evaluation and a governed candidate-development loop.

The intended end state is not a monolithic AI that guesses one interpretation for every sentence. It is a system of cooperating components whose outputs can be inspected, compared, replayed, challenged, and improved independently.

## 4. Target architecture

The intended processing and evidence path is:

source → segmentation → lexical/morphology candidates → syntax/construction candidates → semantic composition → operators and discourse → validated semantic graph → canonical projection/persistence → knowledge retrieval and reasoning → explanation

The path is not a claim that every stage is already integrated or required for every language. Each stage is independently versioned and may return candidates, partial results, or an explicit unsupported result.

| Layer | Responsibility | Required output discipline |
|---|---|---|
| 1. Input and source preservation | Preserve exact input, source identity, spans, language profile, transformations, and rights metadata | Never silently rewrite the original source |
| 2. Segmentation | Tokenize and divide input into sentence, clause, and other useful units | Preserve offsets and segmentation alternatives |
| 3. Lexical and morphology analysis | Generate forms, lemmas, POS, sense, and morphology candidates | Preserve OOVs, multiple candidates, source identity, and unknown mappings |
| 4. Syntax and construction analysis | Generate constituent, dependency, attachment, argument-structure, and construction candidates | Preserve alternative attachments and unresolved dependencies |
| 5. Semantic composition | Build typed predicates, roles, events, states, properties, and relations | Require source spans, rule IDs, and resource versions |
| 6. Operators and discourse | Add negation, quantification, time, aspect, modality, scope, mentions, and discourse links | Preserve scope ambiguity and unresolved references |
| 7. Canonical projection and persistence | Convert supported semantics into versioned USG documents and persist them | Refuse lossy projection; retain unsupported content explicitly |
| 8. Knowledge and retrieval | Retrieve forms, senses, concepts, classes, relations, and source evidence | Retrieval supplies candidates; it does not establish truth |
| 9. Reasoning and explanation | Execute explicit rules over typed semantic structures and evidence | Return derivations, preconditions, conflicts, limits, and unknown states |
| 10. Evaluation and development intelligence | Compare results with frozen and independent evidence; route failures to work packets | Keep populations and metrics separate |
| 11. Governed automation | Prepare candidate fixes, run sandboxes, evaluate, open PRs, monitor, and roll back | Automation authority is risk-tiered and cannot self-approve semantic truth |

### 4.1 Components that must remain distinct

- **Lexical form, lemma, sense, concept, semantic class, instance, and assertion** are different objects.
- **Candidate evidence and accepted runtime knowledge** are separate lifecycle states.
- **Mention identity, discourse referent, concept identity, and real-world entity identity** must not be conflated.
- **Structural validity, execution success, cross-implementation agreement, empirical support, and semantic correctness** are different claims.
- **A diagnostic symptom and its causal blocker** are not necessarily the same thing.
- **A source being registered as a dependency does not prove that runtime code consumes it.**

## 5. Non-negotiable engineering and evidence rules

Every future phase and every implementation packet inherits these rules.

### 5.1 Contracts and compatibility

1. Keep USG-SEM/1.0 unchanged during ordinary feature work.
2. If a capability cannot be represented losslessly, preserve it in a versioned extension or opaque payload rather than deleting or distorting meaning.
3. A normative change requires a migration proposal, old/new compatibility tests, adapters, round-trip tests, and rollback instructions.
4. Keep API, resource, adapter, interpretation, and persistence versions visible in output envelopes.

### 5.2 Semantic uncertainty

1. Unknown and ambiguous input must remain explicit.
2. Do not force one POS, sense, attachment, role, scope, antecedent, concept mapping, or truth value when evidence is insufficient.
3. A similarity score, frequency count, repeated web record, or language-model suggestion is not proof of identity or entailment.
4. Abstention and unsupported detection are capabilities to measure, not failures to hide.

### 5.3 Dataset and evidence governance

Every data resource must record source, rights/license state, language/profile, population type, retrieval date, transformations, deduplication, digest, and permitted use. If rights are unknown, do not assume that data may be redistributed or used for automated evaluation.

Never pool randomized, controlled-diagnostic, synthetic, historical, external-candidate, and naturalistic results into a single denominator without a defensible, documented reason. Translated Arabic PUD remains translated text and cannot establish native-Arabic conversational performance.

### 5.4 Acceptance and promotion

A capability is accepted only for the exact combination of:

- implementation and commit;
- language and construction profile;
- source/resource versions;
- frozen dataset and population;
- positive, negative, ambiguous, boundary, and adversarial cases as applicable;
- declared metrics and thresholds;
- protected prior regression suites;
- explicit limitations and exclusions.

Merging a PR, passing schema validation, generating a candidate, or agreeing with another implementation does not independently accept semantic behavior.

### 5.5 Persistence and reproducibility

Use the existing Phase 3 SQLite authority for canonical semantic documents. Keep caches and indexes rebuildable. Every accepted result must be replayable from its input, code, resources, configuration, and runner versions.

## 6. Portfolio sequencing: work in dependency order, not by phase number alone

Future phase labels P9–P20 are planning identifiers only. They are not approved implementation scopes, current phase statuses, or instructions to begin coding. Re-cut a phase when an evidence-backed smaller increment is safer.

Some tracks may proceed in parallel:

- external lexical acquisition can continue as candidate research;
- Phase 6 continuation can continue within its own gates;
- naturalistic corpus collection and cross-runtime fixture design can progress alongside each other;
- runtime semantic expansion must wait for construction-specific evaluation readiness;
- autonomous candidate generation must wait for reliable test, sandbox, and acceptance infrastructure.

The intended top-level dependency order is:

1. **Close the Phase 8 acceptance loop.** Obtain a fresh post-merge evidence snapshot with an accepted exact-head decision. If blocked, diagnose the check and repair its cause; do not weaken the gate.
2. **Establish shared evaluation and cross-runtime observability (P9).** First freeze a common fixture and result contract. This is the foundation for comparing implementation behavior.
3. **Establish independent evaluation resources and metrics (P10).** Finish the naturalistic pilot and define how independent construction-level gold will be obtained without inventing labels or violating rights.
4. **Improve candidate evidence (P11).** Continue lexical and morphology collection, improve OOV/ambiguity behavior, and benchmark candidate quality.
5. **Expand construction and semantic composition in small units (P12–P13).** Prefer the existing Phase 6 continuation queue and measured high-frequency failures.
6. **Expand scope and discourse (P14–P15).** Only after the required construction and evaluation foundations are in place.
7. **Connect the Phase 7 knowledge layer to runtime consumers (P16).** Prove actual use through code and tests, not registry declarations.
8. **Expand bounded reasoning (P17).** Use explicit rules and evidence with complete derivations and execution budgets.
9. **Automate safe development (P18).** First deterministic test/report/CI repairs, then candidate generation, and only then tightly governed promotion proposals.
10. **Harden Workbench operation and releases (P19).** Consolidate developer-facing contracts and reproducibility after the core interfaces stabilize.
11. **Explore multimodal work only as a later optional horizon (P20).** It is not required to deliver reliable text interpretation.

The exact next task must always be chosen from the latest evidence snapshot and backlog. This sequence is a dependency map, not a promise that every future phase will be implemented exactly as written.

## 7. Future phase packets

The machine-readable file is the detailed task registry. Each item includes its objective, implementation sequence, acceptance criteria, and links to existing backlog/continuation work. The sections below explain the intended deliverable and exit boundary for each future phase.

### P9 — Cross-runtime conformance and reproducible evaluation foundation

**Purpose:** make JS Workbench, Python kernel, Python interpreter, and adapters comparable on exactly the same fixtures without pretending they share identical internals.

**Work packets:**

- **P9.1 — Shared fixture contract:** version a common case format with input, language profile, capabilities under test, expected spans, normalized structures, allowed alternatives, and abstention expectations.
- **P9.2 — Output normalization:** define loss-aware normalization for spans, lexical candidates, constructions, roles, operators, discourse links, unresolved items, and diagnostics while retaining native payload references.
- **P9.3 — Multi-runtime runner:** execute every eligible target separately, capture exact versions, separate skipped/unsupported/not-configured/crashed/timed-out/invalid/mismatch outcomes, and persist per-case outputs.
- **P9.4 — Capability matrix:** publish status by implementation, language profile, construction, and feature; link each claim to exact fixtures and artifacts.
- **P9.5 — Diagnostic dependency graph:** connect first blocking stages, parallel blockers, downstream symptoms, and resource versions without assuming one global pipeline order.
- **P9.6 — Deterministic replay:** pin fixtures, versions, volatile fields, and expected outputs; run protected regressions on each relevant PR.

**Exit:** common fixtures run on eligible implementations, the matrix is evidence-backed, result accounting reconciles, and no feature is expanded merely to force apparent conformance.

**Main risks:** normalizing away meaningful differences, comparing run-specific IDs, or interpreting cross-runtime agreement as semantic truth.

### P10 — Independent evaluation and language evidence programme

**Purpose:** prevent USG from improving its own test scores without improving supported semantic behavior.

**Work packets:**

- **P10.1 — Corpus/evidence registry:** version corpus provenance, rights, population, language/profile, transformations, privacy checks, and allowed uses.
- **P10.2 — Naturalistic pilot:** complete and characterize the current English/Arabic PUD pilot, keep translation limitations explicit, and use it for failure discovery rather than ungrounded semantic accuracy claims.
- **P10.3 — Independent annotation protocol:** where human semantic labels are required, define construction-specific guidelines, independent decisions, disagreement, and adjudication; if no valid gold exists, state that it does not exist.
- **P10.4 — Held-out partitions:** split by document/source and near-duplicate group, freeze the acceptance set, and add leakage checks.
- **P10.5 — Metric cards:** define numerator, denominator, exclusions, population, and interpretation for lexical, syntax, roles, scope, discourse, abstention, execution, and semantic metrics separately.
- **P10.6 — Per-construction gates:** freeze positive, negative, ambiguous, boundary, adversarial, and minimal-pair tests and thresholds before the final held-out run.

**Exit:** corpus rights are known for all resources used, the naturalistic pilot is reproducible, held-out evaluation is protected, and each capability has a bounded acceptance profile.

**Main risks:** using synthetic self-consistency as external truth, leakage from candidate generation into the test set, and conflating translated text with native-language performance.

### P11 — Lexical, morphology, and contextual candidate quality

**Purpose:** convert scheduled external lexical retrieval into better candidate evidence while preventing unreviewed dictionary growth from becoming active runtime meaning.

**Work packets:**

- **P11.1 — Source-specific ingestion:** stabilize source identities, shards, manifests, retries, deduplication, rights metadata, and normalized-record provenance.
- **P11.2 — Morphology candidates:** audit source tag mapping and current PUD results; build language-profile-specific candidate features; report per-tag and per-language quality.
- **P11.3 — Lexical adapter integration:** reuse USG-LEXICAL-CANDIDATES and the existing adapter; expose candidate forms, lemmas, POS, senses, morphology, and evidence to interpreters.
- **P11.4 — Contextual ranking:** test contextual ordering against simple baselines on held-out ambiguity cases; return alternatives and calibrated uncertainty rather than a forced answer.
- **P11.5 — Lifecycle/promotion:** define candidate, validated-for-profile, accepted, deprecated, and rejected transitions; require held-out lexical and downstream regressions plus a rollback path.

**Exit:** candidate quality is independently measured, source provenance and rights are retained, ambiguity regressions pass, and any runtime integration is a separate versioned decision.

**Main risks:** using crawl volume as quality, treating POS/morphology coverage as semantic accuracy, or assuming lexical retrieval resolves syntax and discourse.

### P12 — Construction grammar and syntactic coverage expansion

**Purpose:** expand language coverage using one construction at a time, chosen from recurring evidence and backed by a valid evaluation path.

**Work packets:**

- **P12.1 — Construction selection:** rank candidate work by recurrence, supported-language demand, evidence strength, dependencies, evaluation readiness, cost, and regression risk.
- **P12.2 — Nominal/property/possession/modifier semantics:** continue the existing Phase 6 work rather than duplicate it; specify relation direction, role, spans, and ambiguity.
- **P12.3 — Coordination/embedding/subordination/relative clauses:** add complements, relative clauses, conditionals, temporal clauses, and argument gaps as separately testable constructions.
- **P12.4 — Voice/valence/speech acts:** separate grammatical voice, semantic roles, and communicative force using language-specific contrastive cases.
- **P12.5 — Language profiles:** reuse architecture but do not transfer a feature to another language without appropriate evidence.

**Exit:** each construction has versioned rules, per-language evidence, ambiguity/abstention tests, and protected regression results.

**Main risks:** growing a grammar from keyword triggers, accepting only positive examples, or promoting candidate graphs.

### P13 — Semantic composition and canonical meaning projection

**Purpose:** ensure that lexical and syntactic candidates combine into typed semantic documents without losing source meaning.

**Work packets:**

- **P13.1 — Stage composition contracts:** define typed stage inputs/outputs, candidate alternatives, unresolved dependencies, and provenance propagation.
- **P13.2 — Predicate/argument/role/relation composition:** extend existing frames and roles with domain/range constraints, explicit required roles, and conflict handling.
- **P13.3 — Loss-aware canonical projection:** create explicit relation mappings into USG-SEM/1.0; reject unsupported or lossy projection; retain opaque structures where needed.
- **P13.4 — Canonical persistence/replay:** reuse Phase 3 SQLite APIs, immutable revision history, resource references, integrity checks, and deterministic replay.

**Exit:** compositions preserve source/derivation evidence, projection rejects unsupported meaning, and persistence/round-trip tests pass.

**Main risks:** silently dropping roles or operators, overloading one relation type, or creating a second canonical database.

### P14 — Operator, scope, time, and modality system

**Purpose:** make the system distinguish how a statement is qualified, negated, quantified, temporally located, or presented as possible, necessary, desired, or conditional.

**Work packets:**

- **P14.1 — Typed operator registry:** define operator type, target, operand, scope, language realization, and legal interactions.
- **P14.2 — Negation and quantifier scope:** evaluate nested scope with minimal pairs and ambiguity alternatives.
- **P14.3 — Tense/aspect/modality/temporal relations:** distinguish event time, reference time, duration, completion, possibility, obligation, and underspecification.
- **P14.4 — Conditional/comparative composition:** represent antecedent, consequent, operands, and scope without assuming causality.

**Exit:** operators are typed, their interactions are tested per language, scope alternatives remain visible, and unsupported temporal/modal claims abstain.

### P15 — Discourse, reference, and entity tracking

**Purpose:** connect mentions and discourse information across sentences without confusing a name, a mention, a concept, and a real-world identity.

**Work packets:**

- **P15.1 — Mention/context records:** create stable mention IDs, spans, grammatical features, discourse role, and context evidence.
- **P15.2 — Conservative antecedent ranking:** preserve multiple antecedents and a no-antecedent option; measure false identity merges.
- **P15.3 — Discourse relations:** build typed temporal, causal, contrastive, elaboration, and reference relations only where the evidence and contract support them.

**Exit:** mention chains are traceable, reference decisions are calibrated, false merges are measured, and document-level replay preserves source provenance.

### P16 — Knowledge-layer integration and contextual retrieval

**Purpose:** make the existing Phase 7 knowledge layer useful to interpreters and reasoning services while retaining its lifecycle and data boundaries.

**Work packets:**

- **P16.1 — Prove runtime consumers:** inspect code, add integration tests, and publish an actual consumption matrix for Phase 7 adapters.
- **P16.2 — Evidence-based concept mappings:** review unresolved cross-language mappings and improve only those supported by exact source evidence.
- **P16.3 — Contextual retrieval diagnostics:** explain retrieval features and ranking; keep association, frequency, truth, and entailment separate.
- **P16.4 — Candidate-aware interpreter integration:** add explicit read-only retrieval at stage boundaries and preserve knowledge version/evidence IDs in outputs.

**Exit:** code/tests prove actual knowledge consumption; unresolved mappings remain explicit; retrieval is read-only and does not mutate canonical facts.

### P17 — Evidence-grounded semantic reasoning and explanation

**Purpose:** extend the Phase 2 reasoning foundation to richer interpretation and knowledge without inventing conclusions.

**Work packets:**

- **P17.1 — Rule dependency contracts:** define typed preconditions, inputs, outputs, resource versions, and side-effect limits.
- **P17.2 — Support/conflict/contradiction:** preserve evidence for and against propositions; deduplicate correlated sources and retain unknown.
- **P17.3 — Bounded multi-step inference:** define depth, branching, memory/time, and recursion limits; return complete proof/derivation traces.
- **P17.4 — Document/discourse/temporal reasoning:** reason over multi-sentence structures while preserving scope, time, reference uncertainty, and source evidence.

**Exit:** every accepted conclusion has a replayable derivation, conflict and unknown states are preserved, and independent evaluation supports each claimed reasoning capability.

### P18 — Governed autonomous development and candidate learning

**Purpose:** close the loop from observed failures to proposed and validated repairs without allowing USG to certify its own semantic truth.

**Work packets:**

- **P18.1 — Bounded deterministic repair executor:** automate allowlisted test, fixture, packaging, report, documentation, and CI repairs in isolated branches/sandboxes with exact replay.
- **P18.2 — Candidate generators:** generate lexical, morphology, grammar, frame, and mapping proposals only into candidate artifacts with provenance and explicit evidence gaps.
- **P18.3 — Active evaluation selection:** choose informative cases using recurrence, uncertainty, and coverage without changing held-out membership.
- **P18.4 — Candidate decision packets:** produce accept/reject/needs-evidence reports with independent evaluation and rollback artifacts.
- **P18.5 — Risk-tiered automation:** restrict unattended merge authority to explicitly low-risk change classes; keep semantic/runtime, normative, and rights decisions behind stronger gates.

**Exit:** planner, generator, and executor are separate; candidate generation cannot mutate runtime; held-out leakage and self-validation are blocked; rollback is tested.

**Main risks:** a model-generated patch weakening its own tests, auto-changing acceptance thresholds, treating generated labels as independent gold, or giving a general bot broad merge rights.

### P19 — Workbench integration, release engineering, and operational hardening

**Purpose:** make accepted capabilities usable by a developer through consistent APIs, CLI, Kernel Lab, and reproducible local execution.

**Work packets:**

- **P19.1 — Developer-facing run contract:** expose consistent run envelopes and diagnostics while retaining native implementation detail.
- **P19.2 — Portable local operation:** pin versions, provide fresh-environment setup, offline tests, deterministic fixtures, recovery, and backup procedures.
- **P19.3 — Performance/resource budgets:** instrument latency, memory, storage, cache behavior, and workflow usage; optimize only after profiling.
- **P19.4 — Releases and compatibility:** version contracts/resources/adapters/releases, publish migration notes, and keep release archives immutable.

**Exit:** a fresh environment can run the supported workflow, diagnostics/provenance are inspectable, resource use is measured, and releases can be replayed and recovered.

### P20 — Optional multimodal and grounded-world research horizon

**Purpose:** investigate whether the semantic architecture can extend to image, audio, video, and event evidence after the text system has reliable contracts, provenance, and evaluation.

**Work packets:**

- **P20.1 — Modality-neutral evidence links:** study links between text spans, image regions, audio intervals, video frames, and observations without silently changing the canonical semantic contract.
- **P20.2 — One bounded multimodal pilot:** choose one rights-cleared task with independent evaluation and compare with a text-only baseline.

**Exit:** evidence justifies the added complexity, the existing text architecture remains stable, and rights/privacy/evaluation are independently accepted. This is exploratory and is not on the critical path.

## 8. Near-term execution queue

The first tasks should be selected from the current repository sources, not guessed from the phase numbers.

| Order | Work | Current evidence | Rule |
|---:|---|---|---|
| 1 | Verify Phase 8 exact-head formal acceptance | Implementation merged; post-merge acceptance artifact not yet verified | Diagnose blocked checks and fix their cause; do not weaken gates |
| 2 | Complete the registered naturalistic PUD pilot | Generator/source validation exists; full scheduled campaign must be checked | Report only input/coverage/failure discovery unless independent semantic gold exists |
| 3 | Complete the initial cross-runtime common fixture work | Inventory exists; shared conformance is not yet established | Start with capabilities already supported by two implementations |
| 4 | Finish bounded replay and failure-attribution gaps | SYS-02/SYS-07 are implemented for registered profiles; SYS-14 still has corpus-wide follow-up | Keep exact fixtures/resources and volatile-field policy pinned |
| 5 | Implement bounded deterministic repair execution | SYS-16 is the next safe autonomy increment | Only deterministic harness/report/test/CI changes; sandbox and replay required |
| 6 | Select one construction and independently evaluate it | SYS-08/SYS-09 and Phase 6 continuation provide the route | Prefer the earliest repeated blocker with a credible acceptance oracle |
| 7 | Continue external lexical/morphology evaluation | Crawl and candidate adapter already exist | Continue candidate-only; do not equate crawl completion with semantic improvement |
| 8 | Integrate Phase 7 knowledge only where code/tests prove consumption | Phase 7 accepted for frozen profile; unresolved mappings remain | Read-only adapter; no automatic assertion promotion |

The SYS backlog may re-order these tasks when fresh evidence arrives. The Phase 6 tracker remains authoritative for its eight continuation items. Do not duplicate those IDs inside a new phase or reopen their bounded accepted exit.

## 9. Standard work packet: instructions for a coding agent

Every implementation increment must be made as one small, self-contained packet. The agent must follow this procedure in order.

### Step 1 — Establish the exact state

1. Fetch current main; record commit SHA and clean/dirty state.
2. Read this plan, the relevant phase roadmap, central documentation hub, SYS backlog, Phase 6 tracker, source registry, phase/resource map, and relevant resource manifest.
3. Read the latest system evidence snapshot and the relevant acceptance reports.
4. Search for an existing implementation, adapter, continuation ID, regression, or proposal before creating new code.
5. Check whether a current branch/PR already owns the work. Do not duplicate active work.

### Step 2 — Select one bounded objective

1. Choose one stable work item ID.
2. State one exact behavior or evidence gap to change.
3. List prerequisites and prove each is available.
4. Define in-scope languages, constructions, profiles, resources, and outputs.
5. List explicit non-goals.
6. Classify the change: documentation/test/harness, deterministic infrastructure, candidate resource, runtime semantics, normative contract, or data-rights decision.

### Step 3 — Prepare the implementation

1. Inspect current code and tests before proposing a file layout.
2. Prefer modifying an existing module over adding a parallel subsystem.
3. Add or update the relevant schema/contract before implementation when a new interface is required.
4. Keep the change behind a candidate flag or versioned adapter if acceptance is not yet established.
5. Preserve raw input, candidate alternatives, provenance, and source resource versions.
6. Add positive, negative, ambiguous, boundary, adversarial, and compatibility tests as applicable.

### Step 4 — Run validation

1. Run focused tests first.
2. Run the relevant stage suite and protected prior-phase regressions.
3. Run benchmark/evaluation profiles at the exact declared version.
4. Run deterministic replay and check the exact PR head.
5. Validate JSON schemas, packaging, documentation links, and generated artifacts.
6. Compare before/after metrics with the same denominator and dataset.
7. Do not weaken tests, thresholds, or held-out data to make a PR pass.

### Step 5 — Publish the evidence and decision

Every PR must state:
- packet ID and objective;
- source commit and implementation/resource versions;
- files/modules changed;
- tests and exact run artifacts;
- population/language/construction boundaries;
- accepted/candidate/unresolved status;
- regressions and known limitations;
- risk class and rollback procedure;
- docs, hub, README, backlog, tracker, and resource-manifest changes.

Only the declared acceptance authority may change the work item's state. A merged PR alone is not semantic acceptance.

### Step 6 — Update the plan

1. Update the detailed phase/task record and machine-readable source of truth in the same PR if scope, dependencies, or acceptance changed.
2. Update the SYS backlog or Phase 6 tracker if the implementation belongs to an existing item.
3. Update the system evidence registry and the phase resource manifest where a new resource/source dependency was introduced.
4. Update the central documentation hub and README when the project navigation or major status changed.
5. Leave unrelated phases and work items unchanged.

## 10. Standard task packet template

Use this template when a coding agent starts an implementation. It is intentionally explicit so the next agent does not have to invent a development process.

~~~yaml
packet_id: PXX.Y
title: "One bounded implementation objective"
status: planned
source_commit: "<exact main SHA>"
phase_scope: "one phase and one declared profile"
related_backlog_ids: []
related_continuation_ids: []
dependencies:
  - "exact contract, file, or acceptance artifact"
in_scope:
  languages: []
  constructions: []
  resources: []
  outputs: []
not_in_scope:
  - "explicitly excluded behavior"
change_class: "docs_test_harness | deterministic_infrastructure | candidate_resource | runtime_semantics | normative_contract | data_rights"
implementation:
  existing_modules_to_reuse: []
  expected_files: []
  ordered_actions: []
tests:
  positive: []
  negative: []
  ambiguous: []
  boundary: []
  adversarial: []
  compatibility: []
acceptance:
  exact_metrics_and_denominators: []
  required_workflows: []
  independent_evidence: []
  protected_regressions: []
  held_out_requirements: []
provenance:
  input_commit: ""
  resource_versions_and_digests: []
  dataset_population: ""
  license_and_rights_status: ""
rollback:
  procedure: ""
  protected_baselines: []
deliverables:
  code: []
  tests: []
  documentation: []
  evidence_artifacts: []
completion:
  merged_commit: null
  acceptance_artifact: null
  status: "not_started"
~~~

Do not start implementation when a required dependency or evidence source is unavailable. Either finish that dependency or split the packet into a separately acceptable preparatory task.

## 11. Continuous plan synchronization

The plan includes a deterministic synchronizer and a GitHub Actions workflow.

### Trigger behavior

The workflow runs:
- after pushes to main that touch registered source areas such as specifications, code, resources, tests, benchmarks, documentation, evaluation evidence, or workflows;
- weekly, to catch status drift even when no code change triggers a run;
- manually, when an AI agent or maintainer requests a refresh.

### Inputs read

The synchronizer reads:
- long-term plan JSON and schema;
- system evidence source registry;
- SYS improvement backlog implementation-status table;
- Phase 6 continuation tracker;
- published Phase 8 integrated-acceptance artifacts;
- source file paths declared in the plan.

### Outputs

It generates:
- evaluations/roadmap/plan-sync/latest.json;
- evaluations/roadmap/plan-sync/latest.md.

The report contains source SHA-256 fingerprints, current registered phase statuses, linked SYS/Phase 6 work-item statuses, the latest Phase 8 acceptance state, changed paths, affected planned workstreams, and maintenance actions. A generated report is published through a status-only pull request.

### What is automatic and what is proposal-only

**Automatic:**
- read current phase statuses from the registered source registry;
- read SYS implementation status from the backlog's explicit status table;
- read Phase 6 continuation statuses from its JSON tracker;
- verify the latest published Phase 8 decision artifact;
- fingerprint source documents and evidence folders;
- map changed paths to planned workstreams;
- generate a status and impact report.

**Proposal-only:**
- changing long-term architecture;
- adding, removing, or reordering future phases;
- changing priorities or acceptance thresholds;
- declaring a semantic capability accepted;
- promoting lexical/semantic candidates;
- changing canonical contracts;
- making dataset rights decisions;
- authorizing broad autonomous merges.

This separation is intentional. A deterministic updater can safely observe what changed and which tasks need re-evaluation. It must not invent strategy or semantic truth from a commit diff. The master plan is changed by a focused PR with its rationale and evidence, not by overwriting the strategy on every push.

## 12. Priority selection rules

When several tasks are available, choose the next one using these questions in order:

1. Is the failure recurring in actual evidence, or is it only a speculative feature request?
2. Does it affect an explicitly supported language/profile or block a declared capability?
3. Is the evidence independent and appropriate to the claim being made?
4. Does resolving it unblock multiple downstream stages?
5. Is a valid acceptance oracle available now?
6. Can the work be divided into a smaller independently testable change?
7. What is the implementation and ongoing workflow/storage cost?
8. Could the change break accepted behavior, alter rights boundaries, or modify a normative contract?

Prefer fixing the earliest evidenced blocker over a later-stage workaround. Prefer a small capability with a trustworthy acceptance gate over a broad feature with no way to measure correctness. When no valid gold or rights-cleared data exists, work on observability, candidate evidence, or an explicit evaluation protocol rather than pretending acceptance is possible.

## 13. Automation authority and safety tiers

| Change class | Automation allowed | Required gate |
|---|---|---|
| Documentation navigation, formatting, report generation | May be generated and proposed automatically | Link/schema checks and review of changed facts |
| Test harness, deterministic accounting, packaging, CI repair | May be generated in an isolated branch | Focused tests, protected regressions, exact replay, rollback |
| Candidate lexical/morphology/knowledge records | May be collected/generated as candidate artifacts | Source rights, provenance, candidate schema, held-out evaluation |
| Candidate grammar/frame/operator proposals | May be generated as non-runtime proposals | Reproducible cases, independent evaluation plan, no runtime import |
| Runtime semantic behavior | Must remain separately gated | Per-profile independent acceptance, regressions, versioned integration decision, rollback |
| Normative schema/canonical persistence changes | Never as an incidental automatic repair | Explicit migration proposal, compatibility tests, affected-phase acceptance |
| Dataset licensing/privacy/redistribution decisions | Not decided by an automated coding agent | Verified rights basis and appropriate owner decision |

An AI agent may implement a work packet with little additional planning when the contract, dependencies, tests, and acceptance criteria are already explicit. It must stop and produce a blocker report rather than make up missing semantics, gold labels, licenses, thresholds, or approval authority.

## 14. Maturity gates

Do not use calendar dates as proof of progress. USG reaches each maturity gate only when its evidence exists.

| Gate | Maturity | Evidence required |
|---|---|---|
| M1 | Reliable bounded components | Deterministic contracts, source preservation, provenance, and repeatable tests |
| M2 | Reproducible cross-runtime behavior | Common fixtures and scoped conformance reports across eligible implementations |
| M3 | Independently evaluated construction coverage | Rights-cleared, held-out, per-language construction evidence and calibrated abstention |
| M4 | Compositional document interpretation | Several constructions, operators, and discourse links compose without loss |
| M5 | Evidence-grounded knowledge and reasoning | Traceable retrieval/inference with conflict, unknown states, and bounded execution |
| M6 | Governed continuous improvement | Candidate generation, sandboxing, independent evaluation, acceptance, replay, rollback, and risk-tiered automation |
| M7 | Optional broader modalities and deployments | Separate evidence that added complexity is justified and safe |

A maturity gate can be met for one language/profile while another remains unsupported. Always state the scope.

## 15. Change-control rules for this plan

Amend this plan when:
- a new source family or implementation line changes the architecture;
- an acceptance result invalidates or materially changes a planned dependency;
- a recurring failure cluster changes task priority;
- a phase becomes too broad and must be split;
- a migration changes the normative architecture;
- an existing workstream is superseded by stronger evidence.

For each amendment:
1. identify the old assumption and the new evidence;
2. link the relevant commit, resource, benchmark, or acceptance artifact;
3. show which phase/task IDs change;
4. update the JSON plan and Markdown together;
5. update the schema only when the plan contract itself changes;
6. add tests for any machine-readable field or synchronization behavior changed;
7. keep previous acceptance artifacts and historical snapshots immutable.

Do not change the plan merely because an AI proposes a plausible feature. The proposal must name the capability gap, relevant evidence, expected improvement, dependencies, and measurable exit condition.

## 16. What this plan intentionally does not promise

- It does not promise that every listed future phase will be implemented or that the proposed phase boundaries will never change.
- It does not promise unrestricted natural-language understanding or AGI.
- It does not assume more lexical data automatically yields better semantic interpretation.
- It does not assume that adding a knowledge graph automatically creates factual knowledge.
- It does not authorize automatic promotion of candidate resources or semantic rules.
- It does not treat synthetic, translated, or randomized benchmarks as universal semantic truth.
- It does not require finishing all Phase 6 continuation research before unrelated work can progress.
- It does not start Phase 9 as part of establishing this plan.

## 17. Definition of success for the roadmap itself

The roadmap is working when a new human or AI contributor can:

1. identify the current main commit and authoritative project status;
2. find the existing code, data, tests, and prior decisions relevant to one work packet;
3. understand its prerequisites and exclusions without inventing a new architecture;
4. make a bounded change in the correct module;
5. run the exact required tests and replay;
6. publish evidence that distinguishes structural success from semantic correctness;
7. update the correct tracker and documentation;
8. leave candidate/runtime, accepted/unaccepted, and supported/unsupported boundaries intact.

The strategic plan should evolve as USG evolves. The status synchronizer keeps repository state visible; the evidence-driven review process keeps the strategy honest.
