# USG System Improvement Backlog

**Status:** active evidence-derived backlog; completion states are recorded below  
**Assessment source:** [USG System-Wide Capability Assessment — 2026-11-12](USG-SYSTEM-WIDE-CAPABILITY-ASSESSMENT-2026-11-12.md)

This backlog converts the system-wide assessment into bounded, dependency-ordered work. It is not permission to weaken accepted contracts or promote unvalidated lexical/semantic resources.

## Work queue

| ID | Priority | Work item | Depends on | Definition of done | Runtime impact |
|---|---|---|---|---|---|
| SYS-01 | P0 | Reconcile Open-World case/target/attempt outcome accounting | None | Report has distinct, reconcilable counts for target records, attempted executions, skipped targets, and outcome statuses; zero/empty populations explicit | None |
| SYS-02 | P0 | Add first-blocking-stage and downstream-impact attribution | SYS-01 | Every interpreter result can be grouped by first blocking stage, diagnostic, language, target, population, and resource digest | Diagnostics only |
| SYS-03 | P0 | Add naturalistic corpus pilot | Licensing/privacy review | Small separate population with source URL, license, retrieval date, transformations, deduplication, and privacy checks | None |
| SYS-04 | P0 | Add real browser execution adapter for JS Workbench | Browser automation availability | JS target runs in a real browser; navigation, input, output, errors, and screenshots/logs are reproducible | Test harness only |
| SYS-05 | P1 | Define versioned lexical-candidate adapter contract | SYS-02 | POS/lemma/forms/senses/morphology/provenance/ambiguity exposed as candidates; schema and adapter tests pass | Adapter only; no auto-promotion |
| SYS-06 | P1 | Add OOV and lexical ambiguity regression suite | SYS-05 | Unknown and ambiguous forms remain explicit; no unsupported unique sense/POS assertion | Interpreter diagnostics |
| SYS-07 | P1 | Build stage dependency/error graph | SYS-02 | Root blockers separated from downstream symptoms; every recommendation links to a reproducible case | Diagnostics only |
| SYS-08 | P1 | Add reproducible bilingual PUD structural-frequency diagnostics, then select one bounded construction | SYS-02, SYS-03 | Pinned CoNLL-U hashes verified; per-language sentence/instance frequencies published with UD-proxy labels and denominators; one construction selected only after bilingual evidence review; positive/negative/ambiguous/boundary fixtures frozen | Diagnostics and candidate feature only |
| SYS-09 | P1 | Independent construction-level evidence and acceptance | SYS-08 | Each construction has a separately described evidence population, provenance, limitations, held-out split, and per-language thresholds | Acceptance only |
| SYS-10 | P2 | Audit external Step 6.6 semantic dataset alternatives | SYS-03 | Candidate datasets, annotation-unit mismatches, access, and licensing limitations are documented; no restricted data is copied | Research only |
| SYS-11 | P2 | Automatic bilingual synthetic semantic-reference benchmark | SYS-10 | Graph-first deterministic generator, CC0 benchmark data, ten profiles, exact-span oracle, ambiguity cases, per-profile evaluator, and CI artifacts pass | Evaluation only; no runtime promotion |
| SYS-12 | P2 | Cross-implementation conformance matrix | None | JS Workbench, Python kernel, Python interpreter, and adapters tested separately with explicit version/feature matrix | Adapter/test only |
| SYS-13 | P2 | Kernel Lab stage explanation improvements | SYS-02, SYS-07 | User can inspect source, candidate evidence, rule/resource versions, alternatives, and exact blocker | UI/diagnostic only |
| SYS-14 | P2 | Deterministic replay of accepted failure cases | SYS-02 | Every accepted repair adds a minimized case and reruns prior frozen gates | Tests only |
| SYS-15 | P0 | Evidence-driven unattended growth controller | SYS-01, SYS-02, SYS-07, SYS-14 | Scheduled planner aggregates recent campaign results, ranks first blockers with language/target/resource evidence, and publishes a traceable growth plan without runtime mutation | Planning only |
| SYS-16 | P1 | Bounded automatic repair executor | SYS-15 | Deterministic CI/report/test-harness repairs can be proposed in isolated branches, validated, replayed, and opened as PRs; semantic runtime promotion remains gated | Harness/test/docs only |
| SYS-17 | P1 | Candidate semantic and lexical growth loop | SYS-03, SYS-08, SYS-09, SYS-15 | New lexical/morphology/semantic candidates are generated from measured gaps, independently evaluated, held out, and promoted only through explicit acceptance | Candidate resources until accepted |

## Implementation status — 2026-11-16

| ID | Current state | Evidence |
|---|---|---|
| SYS-01 | **Complete** | PR #185 merged to main; merge commit ebfcd46f85f7795f4d736178aab72270e044782c. Explicit result-record, actual-attempt, skipped-target, scenario, target, and population accounting is validated. |
| SYS-02 | **Complete for registered Phase 4/5 profiles** | PR #185 added accounting and initial attribution; PR #188 added diagnostic-code counts, resource fingerprints, and strict pipeline-version matching before applying a dependency profile. |
| SYS-07 | **Complete for registered Phase 4/5 profiles** | PR #186 merged to main; merge commit 39fd60d2c9ab4089820a7441a29d90aa957cac3a. Phase-specific DAG dependencies preserve parallel blockers and avoid a false global linear order. |
| SYS-14 | **Initial implementation merged; corpus-wide replay remains open** | PR #187 adds pinned replay, target-result comparison, explicit volatile-field policy, and CI smoke replay. Full automatic replay of every accepted repair and frozen failure corpus remains a follow-up acceptance step. |
| SYS-12 | **Initial inventory complete; cross-runtime conformance not yet tested** | PR #192 publishes component evidence and five explicit cross-runtime acceptance gates. It deliberately does not claim semantic equivalence. |
| SYS-13 | **Complete for Phase 5 Kernel Lab explanations** | PR #191 merged; stage guide, first diagnostic location, statuses, source spans, resource version/hash, and expandable stage artifacts are displayed separately from the raw envelope. |
| SYS-05 | **Complete** | PR #190 publishes the versioned `USG-LEXICAL-CANDIDATES/0.1.0` JSON Schema and deterministic `USG-LEXICAL-ADAPTER/0.1.0` read-only adapter with provenance/identity checks and candidate-only enforcement. |
| SYS-06 | **Complete** | PR #190 adds English OOV and polysemy regressions plus Arabic OOV regression; unknown forms remain unresolved and bank remains ambiguous. |
| SYS-03 | **First 50-per-language campaign executed; report branch published but not merged to main** | Run [43810018720](https://github.com/wizekin/USG-Workbench/actions/runs/43810018720) generated campaign `OWC-NAT-PUD-43810018720-1`: 300 actual attempts, 4 completed, 245 partial, 51 unsupported; 150 English and 150 Arabic cases, 100 per target. First blockers: lexical 100 and syntax 99. No semantic gold was available. The append-only report is committed on `reports/naturalistic-pud-43810018720-1` at `e6841e98d5512c19b98b58e15da0ec956d3d60af`, but PR creation failed because Actions cannot create/approve PRs; repository auto-merge is disabled. The naturalistic population is executed evidence, not yet part of main's committed campaign history. PUD remains news/Wikipedia text; Arabic is translated. |
| SYS-08 | **Full pinned-source frequencies reproduced manually; clause-complement candidate selected; workflow/fixtures acceptance pending** | Branch `automation/sys-08-pud-structural-frequency` contains the diagnostic implementation and eight unit tests. The exact pinned English/Arabic CoNLL-U blob SHA-1 and SHA-256 values were verified; a manual full-treebank report is committed on the dependent branch at `evaluations/system-wide/pud-structural-frequency-manual-2026-11-16.json`. The `ccomp`/`xcomp` proxy appears in 348/1,000 English and 349/1,000 Arabic sentences; in the actual 50-sentence campaign sample it appears in 18/50 English and 16/50 Arabic sentences. `clause_complement.ccomp_xcomp` is selected for independent annotation/evaluation design only and maps to existing P6-CONT-02. The first campaign on main still lacks `structural-frequency.json`; no Actions run has tested the branch workflow or unit suite, and positive/negative/ambiguous/boundary fixtures are not frozen. No runtime promotion. |
| SYS-09 | **Independent semantic-gold protocol drafted; annotation and adjudication unavailable** | `documentation/USG-SYS-09-CONSTRUCTION-LEVEL-SEMANTIC-GOLD-PROTOCOL.md` defines two blind annotators per case, a separate adjudicator, preserved raw disagreements, source/document-disjoint held-out splits, per-language positive/negative/ambiguous minima, rights/privacy controls, and separate metrics. It explicitly distinguishes UD proxies from semantic gold and the existing Phase 6 synthetic nominal benchmark. No annotators, adjudicator, frozen semantic label inventory, or accepted semantic dataset are available; no gold labels have been created and no runtime rule is promoted. |
| SYS-04 | **Complete for English browser execution** | PR #194 adds the Chromium/Playwright adapter. OWC-OW7 run 43670079717 confirms adapter v0.1.0/Chromium 159 execution with loopback-only networking and the local rule fallback. It does not add Arabic support or semantic correctness guarantees. |
| SYS-15 | **Planner runs; newest plan is stale against current campaigns** | PR #195 adds the daily scheduled growth controller and first-blocker/resource-aware ranking. The latest plan artifact from run [43813242170](https://github.com/wizekin/USG-Workbench/actions/runs/43813242170), generated 2026-11-16T05:54:35Z, still analyzes only OWC-OW6. It omits OWC-OW7 run 43807165809 and naturalistic PUD run 43810018720 because their report bundles are on unmerged branches. The plan retains a 1,058-record Phase 5 pipeline-version mismatch warning from OW6. |

These are implementation states, not claims that USG's semantic accuracy has improved. The work so far improves evaluation trustworthiness and repeatability; it does not add new accepted language-understanding capabilities.

## Evidence refresh — 2026-11-16

- The latest Open-World campaign is `OWC-OW7-43807165809-1` ([run 43807165809](https://github.com/wizekin/USG-Workbench/actions/runs/43807165809)); its 1,100 randomized records and 106 controlled-diagnostic records remain separate. Its report branch is `reports/ow7-43807165809-1` at `14f9a5be4b9a34e564d9ebcbf8c6fa7ba6b00705`; Actions PR creation failed. No naturalistic cases were included in that campaign.
- The latest growth plan does not yet incorporate either report branch. Do not treat a generated plan as current evidence when its input campaigns are unmerged.
- The PUD campaign report contains CC BY-SA 3.0 license and attribution files and pins both source commits. The source manifest records the privacy-screen limitations and the absence of USG semantic gold. Full contributor attribution remains a packaging review item because the bundle points to pinned upstream READMEs rather than embedding their named contributor lists.
- No semantic runtime, canonical USG-SEM/1.0 contract, accepted Phase 1–5 contract, gold label, or candidate-resource acceptance state changed in this evidence refresh.


- SYS-08 manual full-treebank diagnostic: [pinned bilingual frequency report](../evaluations/system-wide/pud-structural-frequency-manual-2026-11-16.json) verifies both source blob/content hashes and selects `clause_complement.ccomp_xcomp` for candidate annotation only. The first campaign artifact still lacks the workflow-generated structural-frequency report.
- SYS-09 protocol draft: [independent construction-level semantic-gold pathway](USG-SYS-09-CONSTRUCTION-LEVEL-SEMANTIC-GOLD-PROTOCOL.md). No independent annotators/adjudicator are available, so no semantic gold or runtime acceptance is claimed.

## Execution rules

1. Work topologically: do not start dependent work while its prerequisite contract or evidence is missing.
2. Prefer evaluation/diagnostic improvements before semantic runtime changes.
3. Every implementation PR must include tests, documentation, and a reproducible report.
4. Keep naturalistic, randomized, and controlled-diagnostic populations separate.
5. Keep candidate lexical and morphology evidence out of active runtime resources until independent acceptance and a separate integration decision.
6. Never treat a test harness pass as semantic accuracy.
7. Do not modify accepted Phase 1–5 contracts or the canonical `USG-SEM/1.0` schema as incidental cleanup.
8. State acceptance at the exact evidence boundary: Step 6.6 is accepted for the graph-first synthetic reference domain; do not generalize that result to naturalistic language accuracy or production promotion.

## Current execution sequence

1. **SYS-08 — PUD structural-frequency diagnostics:** compute reproducible English/Arabic construction counts from the pinned CoNLL-U sources; keep UD syntax proxies separate from semantic gold. Use the full naturalistic campaign's measured bilingual evidence to select one bounded construction. Do not mark the naturalistic population established until the campaign artifact and publication behavior are verified.
2. **SYS-09 — independent construction-level semantic gold:** define annotation units, annotator guidance, adjudication, ambiguity/abstention labels, provenance, and held-out evaluation before any semantic rule promotion.
3. **SYS-16 — bounded repair executor:** automate deterministic CI, reporting, packaging, and regression-fixture repairs in isolated branches; run tests/replay and preserve rollback; never auto-promote semantic rules or resources.
4. **SYS-17 — candidate lexical/semantic growth loop:** derive candidates from measured failure clusters, source licensing, ambiguity tests, independent gold, held-out evaluation, and rollback.
5. **SYS-12 — cross-runtime conformance:** freeze shared fixtures and compare implementations independently. Agreement is component conformance evidence, not semantic correctness.
6. **SYS-14 — deterministic replay:** extend replay to accepted repairs and the frozen failure corpus.
7. **SYS-10/11 — Phase 6 prerequisites:** continue rights, independent-gold, and annotation prerequisites when available; preserve existing bounded synthetic acceptance without generalizing it to naturalistic semantics.

The completed SYS-04 browser adapter is exercised by OWC-OW7 through Playwright, but the JavaScript target remains English-only and uses the deterministic local rule fallback. The SYS-15 planner remains a planning system, not a code-changing agent. The current growth plan is stale because OWC-OW7 is not committed to main.

## Phase 6 Step 6.6 follow-up status — 2026-11-12

- **SYS-10 — external-data feasibility audit complete:** SemEval, PropBank, PUD, and WojoodRelations are documented with access, scope, and rights limitations. None is a prerequisite for the selected automatic route.
- **SYS-11 — automatic synthetic reference implementation complete:** the graph-first generator, 500-case bilingual corpus, ten-profile evaluator, exact-span validation, CC0 data license, tests, and CI workflow replace the human-annotation dependency.
- **Step 6.6 bounded acceptance:** all ten synthetic profile gates pass; no human annotations or model-generated labels are used. All ten runtime constructions remain candidate-only. Step 6.7 may proceed as candidate development; naturalistic semantic validation remains separately unclaimed. See [the automatic synthetic-reference protocol](PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md).
