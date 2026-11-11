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
| SYS-08 | P1 | Select one construction for bilingual expansion pilot | SYS-02, SYS-03 | Construction chosen using evidence/frequency and available gold; per-language positive/negative/ambiguous/boundary fixtures frozen | Candidate feature |
| SYS-09 | P1 | Independent construction-level gold and acceptance | SYS-08 | Independent source, rights, annotation protocol, held-out split, and per-language thresholds documented and passed | Acceptance only |
| SYS-10 | P2 | Resolve Phase 6 Step 6.6 data/rights gap | SYS-03 | Exact SemEval/other source files, annotation units, licenses, and missing construction coverage documented | None |
| SYS-11 | P2 | Provisional MSA gold annotation pathway | SYS-10 if public gold insufficient | Guidelines, annotator independence, adjudication, disagreement handling, and provisional label documented | Evaluation only |
| SYS-12 | P2 | Cross-implementation conformance matrix | None | JS Workbench, Python kernel, Python interpreter, and adapters tested separately with explicit version/feature matrix | Adapter/test only |
| SYS-13 | P2 | Kernel Lab stage explanation improvements | SYS-02, SYS-07 | User can inspect source, candidate evidence, rule/resource versions, alternatives, and exact blocker | UI/diagnostic only |
| SYS-14 | P2 | Deterministic replay of accepted failure cases | SYS-02 | Every accepted repair adds a minimized case and reruns prior frozen gates | Tests only |

## Implementation status — 2026-11-12

| ID | Current state | Evidence |
|---|---|---|
| SYS-01 | **Complete** | PR #185 merged to main; merge commit ebfcd46f85f7795f4d736178aab72270e044782c. Explicit result-record, actual-attempt, skipped-target, scenario, target, and population accounting is validated. |
| SYS-02 | **Core implementation merged; attribution-completeness follow-up in validation** | PR #185 added initial first-blocker attribution. Follow-up PR #188 adds diagnostic-code counts, resource fingerprints, and strict pipeline-version matching before applying a dependency profile. |
| SYS-07 | **Complete for registered Phase 4/5 profiles** | PR #186 merged to main; merge commit 39fd60d2c9ab4089820a7441a29d90aa957cac3a. Phase-specific DAG dependencies preserve parallel blockers and avoid a false global linear order. |
| SYS-14 | **Initial implementation in validation** | PR #187 adds pinned replay, target-result comparison, explicit volatile-field policy, and CI smoke replay. Full automatic replay of every accepted repair and frozen failure corpus remains a follow-up acceptance step. |

These are implementation states, not claims that USG's semantic accuracy has improved. The work so far improves evaluation trustworthiness and repeatability; it does not add new accepted language-understanding capabilities.

## Execution rules

1. Work topologically: do not start dependent work while its prerequisite contract or evidence is missing.
2. Prefer evaluation/diagnostic improvements before semantic runtime changes.
3. Every implementation PR must include tests, documentation, and a reproducible report.
4. Keep naturalistic, randomized, and controlled-diagnostic populations separate.
5. Keep candidate lexical and morphology evidence out of active runtime resources until independent acceptance and a separate integration decision.
6. Never treat a test harness pass as semantic accuracy.
7. Do not modify accepted Phase 1–5 contracts or the canonical `USG-SEM/1.0` schema as incidental cleanup.
8. Do not claim Step 6.6 or Step 6.7 accepted until the roadmap's independent-gold requirements are satisfied.

## First execution batch

The first safe batch is SYS-01 + SYS-02. It changes reporting and diagnostics rather than interpretation behavior, and it will make later lexical, syntax, semantic, and discourse work evidence-directed.

SYS-03 and SYS-04 can proceed independently once their licensing/privacy and browser automation prerequisites are available. SYS-05 must follow the stage-diagnostic contract so the lexical adapter answers a measured system need rather than adding another isolated resource pipeline.
