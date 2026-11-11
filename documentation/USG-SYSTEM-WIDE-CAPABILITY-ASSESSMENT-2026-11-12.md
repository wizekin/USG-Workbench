# USG System-Wide Capability Assessment — 2026-11-12

**Repository:** `wizekin/USG-Workbench`  
**Assessment type:** evidence-based architecture and capability review  
**Evidence baseline:** main-branch documentation, frozen benchmark records, and Open-World campaign `OWC-OW6-43015126807-1`  
**Decision:** improve the evaluation-to-development feedback loop before expanding runtime scope. Do not wait for the external lexical crawl to begin system-level improvement.

## 1. Executive assessment

USG has a substantial, modular semantic-processing foundation: versioned interpretation contracts, lexical and syntax stages, semantic composition, discourse/reference handling, typed frames, scoped operators, evidence and provenance models, a canonical semantic representation, persistent storage, adapters, and a broad test/benchmark program.

However, the evidence supports a much narrower capability claim than the ultimate project ambition. The current system is a collection of bounded, versioned components and interpreters—not yet a broadly reliable general-purpose semantic understanding system. Its strongest results are exact conformance within deliberately limited constructions. Its weakest area is end-to-end coverage of unfamiliar natural-language input.

**Central conclusion:** the highest-value next step is not simply collecting more words. It is building a disciplined loop that connects observed end-to-end failures to stage-level causes, independently validated fixes, and regression benchmarks. Lexical coverage matters, but it cannot by itself resolve syntax, semantic composition, operator scope, reference, or unsupported constructions.

## 2. What the project is ultimately trying to become

The repository describes USG as a versioned semantic grammar and interpretation architecture. Its intended progression is:

1. Preserve the exact source and its provenance.
2. identify language and tokenize/segment the source;
3. produce lexical and morphological candidates without hiding ambiguity;
4. construct syntax and attachment candidates;
5. compose typed predicates, roles, nominal properties, relations, and operators;
6. connect discourse references only when evidence permits;
7. produce a validated, traceable interpretation graph;
8. project to canonical `USG-SEM/1.0` only when the projection does not silently lose meaning;
9. preserve the result, its derivation, resource versions, and reproducibility.

The long-term objective is a reusable, modular semantic reasoning substrate that can be expanded through explicit classes, relations, rules, evidence, and independently tested language resources. It is not achieved merely by accumulating lexical entries or passing isolated unit tests. This assessment makes no AGI or unrestricted-understanding claim.

## 3. Evidence reviewed

The following repository evidence was inspected:

- `README.md` and the Phase 2–6 roadmaps/completion records.
- Phase 4 Step 4.13 bounded interpreter acceptance.
- Phase 5 Step 5.11 frozen benchmark and acceptance report.
- Phase 6 Step 6.6 roadmap, independent-gold feasibility audit, PUD cross-validation, and contextual POS diagnostic.
- Open-World campaign report and machine-readable campaign bundle `OWC-OW6-43015126807-1`.
- Open-World operation-oracle registry and scoring implementation.
- External lexical evaluation, morphology evaluation, and candidate-only policy.
- The current architecture and implementation boundaries in the repository README.

This is a review of recorded evidence and repository artifacts. It is not a fresh execution of every benchmark or every runtime component.

## 4. Measured capability versus intended capability

### 4.1 Open-World campaign

Campaign: [OWC-OW6-43015126807-1](../../evaluations/open-world/campaigns/OWC-OW6-43015126807-1/campaign-report.md)  
Tested commit: `a04806d1480e692913943693b5251535c6a520f0`

| Recorded outcome | Cases |
|---|---:|
| Completed | 44 |
| Partial | 1,013 |
| Unsupported | 946 |
| Ambiguous | 103 |
| Not executed | 1,000 |
| Invalid output | 0 |
| Timeout | 0 |
| Crashed | 0 |
| Infrastructure error | 0 |
| **Total case/target records** | **3,106** |

Population coverage:

| Population | Cases | Important limitation |
|---|---:|---|
| Unconstrained random | 3,000 | Synthetic/randomized requests, not a naturalistic user corpus |
| Controlled diagnostic | 106 | Fixture-backed and intentionally bounded |
| Naturalistic | 0 | No naturalistic population was available |

The campaign status is **PARTIAL**, not a pass. The report records 1,000 not-executed outcomes and also a zero unexecuted-case count; these fields describe different accounting layers and should be made clearer in a future report. The JavaScript/browser-only target is explicitly not executed without a browser automation adapter.

The 44 completed outcomes must not be described as a 1.4% semantic accuracy score: the denominator mixes target executions, unsupported/partial outcomes, and not-executed target records, and the campaign has no universal semantic gold oracle. They are execution outcome counts, not semantic correctness measurements.

The largest reported failure signatures involve:
- unresolved lexical tokens and lexical ambiguity;
- incomplete syntax;
- unresolved semantic clauses;
- incomplete operators;
- unresolved discourse antecedents.

These signatures are consistent with a pipeline whose stages are present but whose coverage and cross-stage resolution remain incomplete.

### 4.2 Phase 4

Phase 4 is accepted as a six-case, bounded offline demonstrator. It preserves source text and has conservative unsupported/unresolved behavior, but its grammar and lexical resources are intentionally tiny. Its acceptance does not imply broad English or Arabic interpretation.

### 4.3 Phase 5

Phase 5 Step 5.11 passed its 100-case benchmark with 100% precision/recall and exact role/span metrics for:
- English simple-transitive SVO;
- MSA Arabic simple-transitive VSO;
- MSA Arabic simple-transitive SVO.

This is valuable evidence of exact behavior within those three target constructions. It is not evidence for general English/Arabic language understanding, multi-domain discourse, or arbitrary semantic relations.

### 4.4 Phase 6

Steps 6.1–6.5 are accepted for their defined bounded scope. Step 6.6 remains open because an independently adjudicated bilingual semantic-gold set for the target nominal/property/modifier constructions has not yet been assembled and rights-cleared. Step 6.7 remains blocked.

The PUD POS experiments are useful diagnostics, not semantic acceptance:
- Fold-derived lexical candidate coverage: English 82.6%, Arabic 75.5%.
- Gold UPOS candidate inclusion: English 80.9%, Arabic 74.0%.
- Candidate ambiguity among seen tokens: English 34.2%, Arabic 29.2%.
- Contextual HMM: English 82.55% versus 82.04% unigram; Arabic 79.59% versus 81.96% unigram.

The HMM does not show a consistent improvement and should not be integrated into the runtime on this evidence.

### 4.5 External lexical evidence

The current external crawl has 602 processed headwords against a source snapshot of 1,396,111 expected headwords. The latest independent English PUD evaluation reports:
- exact surface coverage: 2.44%;
- OOV: 97.56%;
- gold UPOS candidate recall: 1.74%;
- exact gold-lemma coverage: 2.10%;
- morphology candidate-pool precision and recall for the mapped tags: 0%.

The 0% morphology overlap is a diagnostic result for a very small, incomplete candidate inventory and a limited source-tag mapping. It is not proof that all source morphology is wrong.

Do not conflate these external-crawl figures with the higher fold-derived PUD candidate-coverage experiment. They use different inventories and evaluation procedures.

## 5. Overall capability map

| System area | Evidence-backed status | Assessment |
|---|---|---|
| Canonical semantic model and schemas | Implemented and contract-tested | Strong structural foundation |
| Persistence, replay, integrity | Implemented and phase-tested | Strong bounded engineering foundation |
| Typed frames, roles, operators, evidence | Implemented in versioned modules | Functional within tested contracts |
| Phase 4/5 interpretation | Benchmark-enabled for narrow profiles | Reliable only within measured constructions |
| Lexical coverage | Candidate resources plus external crawl | Major bottleneck; external crawl still tiny |
| Contextual POS/morphology | Experimental diagnostics | No consistently superior runtime candidate yet |
| Syntax/semantic composition breadth | Partial/candidate and construction-specific | Major capability gap |
| Discourse/reference | Implemented in bounded stages | Unresolved antecedents remain a visible failure cluster |
| Naturalistic end-to-end understanding | No naturalistic campaign population | Not yet measured |
| JavaScript Workbench open-world execution | Browser adapter absent in campaign | 1,000 target records not executed |
| Bilingual semantic gold for Phase 6 | Not yet rights-cleared/adjudicated | Blocks Step 6.6/6.7 acceptance |
| Cross-implementation unification | Explicit adapters and version boundaries exist | Do not assume all implementation lines are one runtime |

## 6. Main diagnosis

### A. Evaluation is more mature than broad interpretation

The repository has extensive schemas, test suites, acceptance workflows, reproducible fixtures, and open-world infrastructure. That is a genuine strength. But the current open-world campaign has no naturalistic cases and many unsupported/partial outcomes. More test infrastructure alone will not increase semantic capability.

### B. Lexical coverage is a bottleneck, but not the only bottleneck

The external crawl is too small to materially improve the overall interpreter yet. Even a complete dictionary would not automatically solve attachment, scope, roles, clause composition, or reference. The lexical subsystem must expose candidate sets, ambiguity, morphology, and provenance to later stages without pretending that a word lookup is a semantic decision.

### C. Stage-local diagnostics need to become an actionable error graph

The open-world failure signatures repeatedly combine lexical, syntax, operator, semantic-composition, and discourse failures. USG should preserve a structured dependency chain showing:
- which stage produced the first blocking diagnostic;
- which later stages were consequently incomplete;
- which rule/resource/version was consulted;
- what evidence would be needed to resolve the candidate;
- whether the result is fixable by a resource, grammar rule, parser, or evaluation-oracle change.

This avoids treating every partial result as a lexical failure.

### D. Independent evaluation is the limiting factor for safe expansion

Phase 6 correctly refuses to promote candidate constructions without suitable gold evidence. This is not administrative overhead; it prevents self-consistency tests from being mistaken for semantic correctness. The next work must close the evaluation gap without weakening acceptance criteria.

### E. A single overall score would be misleading

USG needs separate measurements for:
- execution reliability;
- source/span/provenance integrity;
- lexical coverage and ambiguity;
- syntax/attachment;
- semantic-role and relation correctness;
- operator/scope correctness;
- discourse/reference;
- abstention and unsupported detection;
- end-to-end semantic correctness where independent gold exists.

Do not combine these into one weighted "intelligence" or "understanding" score until defensible denominators and independent oracles exist.

## 7. Prioritized modifications

### Priority 0 — Evaluation truth and observability

1. **Reconcile Open-World outcome accounting.** Make target records, execution attempts, skipped targets, unsupported outputs, and genuinely unexecuted scenarios separate counters with explicit denominators.
2. **Add target-by-stage failure attribution.** Aggregate first blocking stage, downstream consequences, diagnostic codes, language, population, and implementation version.
3. **Add a naturalistic evaluation population.** Start with small, legally usable, privacy-reviewed open datasets and keep it separate from generated and controlled fixtures.
4. **Execute the JavaScript Workbench target.** Add a real browser automation adapter or explicitly keep the target out of executable coverage; never silently count it as tested.
5. **Preserve per-case reproducibility.** Link every failure family to exact cases, source commit, resource digests, and replay instructions.

### Priority 1 — Improve the interpretation pipeline using measured bottlenecks

6. **Lexical candidate interface.** Define a versioned adapter that exposes lemma, POS candidates, observed forms, source provenance, sense ambiguity, and morphology candidates to the interpreter. It must return candidate evidence, not a chosen meaning.
7. **OOV and ambiguity handling.** Add explicit policies for unknown words, multiple POS candidates, multi-sense entries, and conflicting sources. The interpreter must preserve alternatives or abstain when the evidence is insufficient.
8. **Stage dependency/error graph.** Connect lexical and syntax candidates to semantic composition and discourse diagnostics. Report root blockers separately from downstream symptoms.
9. **Construction-first expansion.** Prioritize a small number of high-frequency, independently testable constructions over broad, unvalidated rule growth. Each construction requires positive, negative, ambiguous, and boundary gold cases per language.
10. **Do not integrate the current HMM.** Its Arabic regression and negligible English gain do not justify replacing the existing lexical baseline.

### Priority 2 — Close semantic evidence gaps

11. **Resolve Phase 6 Step 6.6 data access and rights.** Verify SemEval task files and licenses, map each annotation unit to the exact USG construction, and identify uncovered modifier relations.
12. **Create a provisional MSA gold set only with explicit labels.** If open data is insufficient, use documented annotation guidelines, independent review, adjudication, and clear provisional-versus-adjudicated status.
13. **Keep semantic gold held out.** Do not train candidate resources or tune grammar against the final evaluation split.
14. **Require per-construction/per-language acceptance.** Do not let aggregate success hide an unsupported language or relation family.

### Priority 3 — Integration and usability

15. **Maintain separate implementation lines.** Keep the JS Workbench, Python reference kernel, and Python interpreter distinct; expand only through explicit versioned adapters and round-trip conformance.
16. **Improve Kernel Lab explanations.** Present stage-by-stage candidate evidence, rules used, unresolved alternatives, and exact reasons for partial/unsupported status.
17. **Add deterministic regression replay.** Every accepted fix should add the minimized failing case to the correct population and rerun prior frozen benchmarks.

## 8. Proposed implementation sequence

| Order | Deliverable | Exit condition |
|---:|---|---|
| 1 | Open-World accounting correction | Counts reconcile across case, target, and attempt levels |
| 2 | Failure-attribution report | First blocker and downstream stage effects visible per case |
| 3 | Naturalistic corpus pilot | License/provenance/privacy reviewed; separate score population |
| 4 | Browser execution adapter | JS target actually executes and reports its own outcomes |
| 5 | Lexical candidate adapter contract | Candidate evidence is consumable without runtime promotion |
| 6 | OOV/ambiguity regression suite | Unknown and ambiguous cases abstain/preserve alternatives correctly |
| 7 | One construction expansion pilot | Independent per-language gold and frozen acceptance gate |
| 8 | Phase 6 Step 6.6/6.7 decision | Independent semantic-gold and acceptance requirements satisfied |

This sequence is dependency-aware. It deliberately does not attempt to rewrite the interpreter, replace the canonical semantic model, or bulk-import lexical data.

## 9. What should not be changed now

- Do not rewrite `USG-SEM/1.0` to fit a new candidate construction.
- Do not merge the JS Workbench and Python kernel into one implementation without explicit conformance.
- Do not treat lexical co-occurrence, related-word edges, usage counts, or model confidence as truth or semantic entailment.
- Do not promote the external lexical crawl or experimental HMM into active runtime resources.
- Do not weaken the Phase 2/3/4/5 acceptance thresholds to improve apparent pass rates.
- Do not claim naturalistic or unrestricted semantic understanding from randomized synthetic prompts.
- Do not unblock Phase 6 Step 6.7 before the independent semantic-gold gate is satisfied.

## 10. Acceptance and follow-up

This document is a system-level diagnosis and improvement proposal, not a claim that the listed modifications have already been implemented. Each implementation should be a separate bounded change with tests, documentation, reproducible evidence, and a PR. Runtime changes that affect interpretation semantics require their own independent acceptance evidence.

**Recommended immediate next step:** implement Priority 0 items 1 and 2 together, because reliable accounting and root-cause attribution will tell us which runtime improvement is most valuable. Then build the lexical candidate adapter only after its contract is tied to those diagnostics.

## Source records

- [Repository overview](../README.md)
- [Open-World campaign report](../evaluations/open-world/campaigns/OWC-OW6-43015126807-1/campaign-report.md)
- [Phase 4 bounded acceptance](PHASE-4-STEP-4.13-EXIT-ACCEPTANCE.md)
- [Phase 5 benchmark acceptance](PHASE-5-STEP-5.11-BENCHMARK-EXIT-ACCEPTANCE.md)
- [Phase 6 roadmap](PHASE-6-DEFINITIONS-ROADMAP.md)
- [Phase 6 independent gold audit](PHASE-6-STEP-6.6-INDEPENDENT-GOLD-DATASET-AUDIT.md)
- [Phase 6 PUD POS cross-validation](PHASE-6-STEP-6.6-PUD-POS-CROSSVALIDATION.md)
- [Phase 6 contextual POS diagnostic](PHASE-6-STEP-6.6-PUD-CONTEXTUAL-POS.md)
- [External lexical PUD evaluation](EXTERNAL-LEXICAL-PUD-EVALUATION-v0.1.0.md)
- [Open-World evaluation protocol](USG-OPEN-WORLD-EVALUATION-PROTOCOL.md)
- [Open-World operation oracles](OW-16-REFERENCE-KERNEL-AND-JS-SUITE.md)
