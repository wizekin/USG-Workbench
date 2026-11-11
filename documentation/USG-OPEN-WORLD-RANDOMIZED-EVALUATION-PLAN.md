# USG Open-World Randomized Evaluation Program

**Status:** PROPOSED PLAN — implementation and first execution pending  
**Target repository:** `wizekin/USG-Workbench`  
**Purpose:** Measure how the complete available USG system behaves on unpredictable, realistic, diverse inputs, discover unanticipated strengths and failures, and preserve auditable reports.

## 1. Executive intent

Build a continuously expanding evaluation program that gives USG unfamiliar requests rather than only the examples its developers anticipated. The program will generate, collect, mutate, and replay a large and continually growing population of test scenarios; execute them through the real available USG entry points; preserve every input, configuration, output, score, failure, and limitation; and publish human-readable and machine-readable reports in this repository.

The evaluation is deliberately **open-world**. The capability taxonomy in this document is a sampling aid, not a whitelist or a ceiling. The generator must be able to produce tasks outside known categories, combine unrelated categories, and preserve genuinely unclassifiable cases as such. Newly discovered behavior can expand the taxonomy without requiring a redesign of the test harness.

No finite campaign can guarantee testing every possible real-world request or prove universal competence. The operational goal is stronger and more honest: continually sample a broad, evolving approximation of real use; measure known capabilities; expose unknown capability boundaries; and make every result reproducible and inspectable.

## 2. What is being evaluated

The primary subject is the **actual USG system available in the repository**, not an imagined future chatbot. Every run must record the exact implementation, API/CLI/interface, contract versions, resource manifests, enabled modules, configuration, and commit SHA.

The harness should exercise, where present:

1. Raw-input ingestion, normalization boundaries, sentence and clause segmentation.
2. Lexical lookup, morphology, language identification, lexical ambiguity, and unknown terms.
3. Syntax and construction candidates, attachment, word order, and dependency evidence.
4. Predicate frames, valency, semantic roles, participant binding, and argument omission.
5. Nominal/property semantics, modifiers, genitive relations, compounds, and prepositional relations.
6. Coordination, embedding, subordination, relative clauses, and multi-clause composition.
7. Negation, modality, tense/aspect, quantification, scope, conditionals, and other operators.
8. Discourse context, coreference/reference candidates, anaphora, ellipsis, and cross-sentence links where implemented.
9. Ambiguity preservation, alternative analyses, confidence/ranking semantics, abstention, and unsupported constructions.
10. Source fidelity: exact text, Unicode/code-point offsets, span validity, provenance, and derivation traces.
11. Semantic graph validation, canonical USG-SEM projection, loss detection, serialization, export, and round-trip behavior.
12. Resource catalogue behavior, activation/retrieval, versioning, persistence, SQLite integrity, immutable runs, and deterministic replay.
13. Python APIs, CLI, Kernel Lab, and other actual user-facing entry points, tested separately so one interface cannot hide another's failures.
14. Mixed-language and multilingual input, including English, MSA Arabic, code-switching, transliteration, dialectal or unsupported language input, and unknown scripts.
15. Realistic user requests: questions, instructions, corrections, multi-part requests, paraphrases, incomplete context, contradictory statements, follow-up turns, and long documents.
16. Stress and robustness: very long inputs, short fragments, misspellings, punctuation noise, repeated text, Unicode edge cases, malformed structured input, resource exhaustion, and interrupted operations.
17. Adversarial and safety-relevant text handling: quoted instructions, prompt-injection-like strings treated as data, misleading premises, conflicting constraints, harmful or disallowed request content, and attempts to confuse provenance or source spans.
18. Unexpected combinations and **unknown/other** cases that do not fit the taxonomy above.

The harness must not score an absent feature as if it were implemented. It must identify whether a capability is implemented, regression-tested, benchmark-enabled, partial/candidate-only, unsupported, or not yet observable.

## 3. Three complementary test populations

A single test style cannot represent real-world behavior. Maintain three populations and report them separately.

### A. Unconstrained random scenarios

Generate fresh requests from broad compositional primitives and free-form templates, with no fixed list of permitted task types. Randomly combine language, length, domain, intent, discourse structure, ambiguity, noise, constraints, and context. Reserve a meaningful portion for unconstrained prompts that are not assigned a capability label before execution.

### B. Naturalistic real-world scenarios

Build a legally usable, privacy-reviewed corpus from public-domain/openly licensed text, public task/request datasets, documentation examples, and carefully anonymized or synthetic user-like requests. Track each source's URL, license, version, retrieval date, transformation, and attribution. Never ingest private user conversations, secrets, credentials, or personal data without explicit authorization and a lawful basis. Avoid treating synthetic paraphrases of one source as independent examples.

### C. Controlled diagnostic scenarios

Use generated fixtures with known expected structure and deterministic oracles to isolate specific behaviors. Include positive, negative, ambiguous, unsupported, and boundary cases. These are essential for diagnosing failures but must never be mistaken for the full real-world distribution.

Keep these populations separate in all aggregate metrics. A high score on controlled fixtures must not conceal poor performance on naturalistic or unconstrained requests.

## 4. Random generation strategy

Use a layered generator rather than a fixed test-case list:

- **Seed source:** draw a fresh master seed from operating-system entropy for each campaign. Record the seed and generator version in the report so the exact campaign can be replayed. Support explicit seed override for debugging.
- **Compositional generation:** sample independently and jointly from language, topic/domain, request intent, syntactic form, semantic relation, discourse context, length, ambiguity, noise, and constraint dimensions.
- **Open prompt generation:** create requests from open-ended prompt patterns and source-derived task descriptions. Allow free-form generation paths that do not require a predefined capability label.
- **Mutation:** paraphrase, reorder, omit context, add distractors, introduce typos, alter punctuation, combine clauses, change names/entities, switch language, insert quoted text, and create minimal pairs.
- **Metamorphic testing:** create related inputs where a known transformation should preserve or predictably change a structural property. Examples include harmless paraphrase, word-order changes where grammar permits, adding negation, changing singular/plural, and adding a modifier.
- **Adversarial sampling:** deliberately search for parser confusion, false certainty, invalid spans, silent information loss, incorrect unique interpretations, and crashes.
- **Novelty pressure:** reduce repeated near-duplicates using normalized text hashes and similarity-based clustering. Preserve deliberate minimal pairs and repeated-run trials.
- **Adaptive sampling:** allocate additional samples to newly discovered failures, unstable cases, underrepresented languages/domains, and low-confidence or abstention-heavy areas. Do not let adaptive sampling erase a separate unbiased random sample.
- **Unclassified bucket:** every run must reserve capacity for cases not classified by the known taxonomy. New recurring clusters become candidate additions to the taxonomy after review.

A seed makes a run reproducible; it does not make a random sample representative of all real users. Report the sampling method and limitations.

## 5. Simulation matrix — breadth without a closed boundary

The initial sampler should deliberately span the following dimensions, while remaining free to generate outside them:

| Dimension | Examples of variation |
|---|---|
| Language and script | English, MSA Arabic, code-switching, transliteration, other languages/scripts |
| Domain | Everyday life, science, medicine, education, law, finance, programming, history, culture, travel, engineering, fiction, unknown |
| Request form | Question, command, explanation request, comparison, summary, extraction, classification, transformation, multi-step request, conversational follow-up |
| Linguistic structure | Simple/complex clauses, coordination, subordination, relative clauses, passive, nominal phrases, fragments |
| Semantic structure | Agent/patient, experiencer/stimulus, possession, attributes, location, time, cause, purpose, comparison, condition, modality |
| Context | No context, one prior turn, long context, missing antecedent, conflicting context, irrelevant distractors |
| Ambiguity | Lexical, syntactic, referential, scope, underspecification, genuine multiple readings |
| Input quality | Clean, typo-heavy, unpunctuated, noisy, duplicated, malformed, very long, Unicode edge cases |
| Constraints | Multiple requirements, impossible requirements, conflicting instructions, hidden assumptions, changing requirements |
| Expected behavior | Interpret, preserve alternatives, ask/abstain if supported, mark unsupported, reject invalid data, fail safely |
| Novelty | Familiar pattern, rare combination, unseen combination, unclassifiable prompt |

These are sampling axes, not a promise that USG already supports each behavior. Unsupported and out-of-distribution inputs are valuable test cases: the system should expose its limits rather than invent support.

## 6. Execution protocol

For every scenario:

1. Assign a globally unique case ID and record population, source, generator version, master seed, case seed, and generation trace.
2. Record the exact input bytes/text and a content digest; preserve language/script metadata without rewriting the original.
3. Execute the real selected USG entry point in an isolated state directory/database. No scenario may inherit another scenario's mutable state unless the scenario explicitly tests multi-turn continuity.
4. Capture stdout/stderr, structured outputs, exceptions, exit status, resource usage, timing, and all available derivation/provenance traces.
5. Validate output schema, source spans, graph invariants, provenance links, persistence integrity, and replay behavior with deterministic checks.
6. Apply task-specific scoring only when a defensible oracle exists. Distinguish exact gold comparison, metamorphic invariants, structural validation, reference-based scoring, and subjective judgement.
7. Record unknown, unsupported, abstained, ambiguous, timeout, crash, and infrastructure-error outcomes as distinct statuses. Never silently drop them from denominators.
8. Repeat a stratified subset to measure repeatability. Re-run the same cases after code/resource changes to measure regressions.
9. Save every failure with a minimized reproducer when reduction is safe and meaningful.
10. Generate a report even if the run fails partway; partial runs must be labelled partial and include completed/attempted counts.

Use per-case time, memory, and input-size limits to prevent one pathological scenario from consuming the entire runner. Isolate test data and do not permit test prompts to execute commands or access external secrets.

## 7. Scoring and reporting

Do not collapse all behavior into one headline score. Publish at least:

- **Execution reliability:** completed, timeout, crash, infrastructure failure, and unhandled-exception rates.
- **Structural validity:** schema validity, graph invariant violations, valid source spans, and provenance completeness.
- **Semantic correctness:** precision/recall/F1 or task-specific accuracy only where independent gold labels exist; report per construction and per language.
- **Calibration and uncertainty:** only where scores have a validated probabilistic interpretation; raw ranking scores must not be described as probabilities.
- **Ambiguity and abstention:** correct ambiguity preservation, unsupported-case recognition, false unique interpretations, and unnecessary abstentions.
- **Robustness:** behavior under paraphrase, noise, context perturbation, adversarial changes, long inputs, and resource pressure.
- **Consistency:** repeated-run semantic agreement, deterministic replay agreement, and sensitivity to irrelevant prompt changes.
- **Coverage:** attempted and completed counts by language, domain, task family, construction, input length, and novel/unclassified cluster.
- **Performance:** latency distributions (median, p90, p95), throughput, peak memory, database growth, and resource costs.
- **Change impact:** per-case and per-category regressions/improvements against the previous comparable version.

For subjective/open-ended cases, use a documented rubric and a separately calibrated judge. Automated or model-based judges are provisional evidence, not ground truth. Human review should be used for a stratified sample and for high-impact disputed failures when available. Report inter-rater/judge disagreement and confidence intervals where statistically appropriate.

Always include the denominator, missing/invalid counts, uncertainty, and limitations. Do not award a semantic-correctness score merely because output is well-formed or internally consistent.

## 8. Scale and continuous campaign

The campaign should be effectively unbounded over time, but each execution must have an explicit resource budget:

- **Smoke run:** small sample on pull requests; catches harness breakage and obvious regressions.
- **Daily exploration:** broad randomized sample with a modest fixed time/resource budget.
- **Weekly deep run:** much larger sample, multiple seeds, repeated cases, and adaptive failure exploration.
- **Release evaluation:** frozen, versioned sample with hidden seed revealed after completion, plus replay of prior release cases.
- **On-demand stress run:** user-triggered larger campaign with configurable case count, languages, domains, duration, and resource ceiling.

Start with a pilot sized to fit free GitHub-hosted runner limits, then increase only after measuring actual runtime and storage. Avoid running the full expensive campaign on every pull request. Do not assume GitHub Actions minutes, artifact retention, or repository storage are unlimited. Keep raw large outputs in workflow artifacts where appropriate and commit compact, durable summaries and reproducibility metadata to Git.

The program should support parallel workers only after verifying that the USG database/state is isolated per worker. The existing SQLite ownership and transaction rules remain authoritative; do not introduce concurrent direct access to one store-owned database file.

## 9. Repository layout and report retention

Proposed structure:

```text
evaluation/open-world/
  README.md
  protocol/
    GENERATION-PROTOCOL.md
    SCORING-RUBRICS.md
    CAPABILITY-TAXONOMY.md
    DATA-SOURCES-AND-LICENSES.md
  generators/
  scenarios/
    fixtures/
    seeds/
  harness/
  validators/
  reports/
    README.md
    YYYY/
      YYYY-MM-DD/
        campaign-<run-id>/
          summary.md
          summary.json
          metrics.json
          coverage.json
          failures.jsonl
          manifest.json
          reproducers/
  schemas/
```

For every campaign, commit at least:

- a Markdown executive report;
- machine-readable JSON summary and metrics;
- a manifest containing commit SHA, system/contract/resource versions, generator/scorer versions, seed, environment, and timestamps;
- coverage and failure-category breakdowns;
- links to full logs/artifacts where the complete payload is too large for Git.

Never overwrite an old report. Reports are append-only and tied to the exact tested commit. Large raw traces may be retained as GitHub Actions artifacts with their retention period recorded; the repository must still preserve enough metadata to reproduce and interpret the run.

## 10. Failure taxonomy and automatic discovery loop

Every failure should be classified, with multiple labels permitted:

- parsing/segmentation;
- lexical/morphological;
- attachment/construction;
- semantic role/frame;
- nominal/property/modifier;
- operator/scope;
- discourse/reference;
- ambiguity/abstention;
- source-span/provenance;
- semantic projection/serialization;
- persistence/replay/integrity;
- API/CLI/UI integration;
- multilingual/code-switching;
- robustness/resource exhaustion;
- safety/data-boundary;
- evaluator/oracle defect;
- infrastructure/environment;
- unknown/new failure family.

The loop is:

**Generate → Execute → Validate → Score → Cluster → Minimize → Report → Add regression fixture → Re-run.**

A failure may create a new regression fixture, but it must not automatically change USG grammar, resources, or acceptance thresholds. Keep evaluation evidence separate from development decisions to avoid tuning to the test set.

## 11. Anti-bias, independence, and auditability

- Freeze generator and scoring versions per campaign.
- Preserve a hidden random sample and reveal its seed only after the run is complete.
- Keep development/regression fixtures separate from fresh evaluation samples.
- Never tune USG against the current hidden sample; after a sample is used for development, mark it as exposed and rotate it out of the hidden pool.
- Use independent annotations for semantic claims; USG's own output or adapter rules cannot serve as their own gold truth.
- Track dataset licenses and provenance. Do not redistribute restricted corpora in Git; store source references, permitted derived data, and hashes instead.
- Keep deterministic structural checks separate from subjective semantic judgements.
- Publish failures and negative results, not only successful demonstrations.
- Include known limitations, confidence intervals, sampling bias, possible data overlap, and evaluator uncertainty in each report.

## 12. Acceptance gates

The evaluation program itself is accepted only when:

1. It can invoke every currently supported USG entry point selected for the campaign and records any unavailable entry point explicitly.
2. It produces both reproducible seeded cases and fresh entropy-seeded cases.
3. It supports labeled and unclassified/open-world scenarios.
4. It separates controlled, naturalistic, and unconstrained populations in reports.
5. It records all attempts, including crashes, timeouts, abstentions, unsupported outputs, and partial runs.
6. It validates source spans, provenance, graph/schema invariants, persistence, and replay where those facilities exist.
7. It never claims semantic correctness without independent evidence.
8. It generates append-only Markdown and JSON reports linked to the tested commit and configuration.
9. It has smoke, scheduled, deep, and on-demand execution modes with explicit resource ceilings.
10. A clean replay of a seeded campaign reproduces the same generated cases and deterministic outputs within documented environmental tolerances.
11. Existing Phase 1–6 tests and contracts remain unchanged and pass.
12. A pilot report is committed, including failures and limitations, before the program is described as operational.

A passing harness acceptance gate means the **evaluation machinery** works. It does not mean USG passes the evaluation or that USG has unrestricted semantic understanding.

## 13. Ordered implementation roadmap

| Stage | Deliverable | Exit condition |
|---|---|---|
| OW-0 | Repository inventory and capability/entry-point map | Every current USG implementation, API, interface, contract, resource set, and existing benchmark is mapped; gaps are explicit. |
| OW-1 | Evaluation protocol, taxonomy, report schemas, source/license policy | Protocol reviewed against current repository boundaries; schemas validate; no capability is assumed. |
| OW-2 | Seeded open-world scenario generator | Reproducible generation, fresh entropy seeds, unclassified cases, novelty control, and mutation tests pass. |
| OW-3 | Isolated execution harness | Real USG entry points execute with per-case isolation, budgets, complete capture, and failure preservation. |
| OW-4 | Oracle and validator portfolio | Deterministic, metamorphic, external-reference, and rubric-based scoring are separated and tested. |
| OW-5 | Report and regression pipeline | Markdown/JSON reports, manifests, failure clusters, minimized reproducers, and append-only storage work. |
| OW-6 | Pilot campaign | First broad campaign runs; report includes actual results, failure analysis, coverage gaps, costs, and limitations. |
| OW-7 | Continuous exploration | Smoke, daily, weekly, release, and on-demand workflows operate within measured budgets. |
| OW-8 | Adaptive discovery | Failure-driven sampling, novel cluster discovery, taxonomy evolution, and hidden-sample rotation work without leaking test sets. |
| OW-9+ | Ongoing expansion | Add languages, entry points, data sources, modalities, simulators, and newly discovered request families as USG evolves. No terminal scope is imposed. |

Each stage is a separately tested change. Merge automatically only when its required checks pass; do not weaken checks or merge a failing implementation to preserve momentum.

## 14. Research basis and design rationale

This plan follows established evaluation principles: define what is measured; justify sampling; separate capability from formatting and infrastructure; preserve held-out evaluation data; disclose contamination and dataset limitations; repeat stochastic experiments; report uncertainty; and perform failure analysis. Relevant background:

- [Guidelines for empirical studies in software engineering involving large language models (2026)](https://link.springer.com/article/10.1007/s10664-026-10922-3) — construct validity, sampling, contamination controls, repeated runs, statistical reporting, and error analysis.
- [Bridging Cognitive Architecture and Developmental Measurement for Artificial General Intelligence](https://pmc.ncbi.nlm.nih.gov/articles/PMC13514576/) — expandable generative task spaces with explicit seeds, sampling protocols, and reproducibility.
- [A statistical framework for evaluating the repeatability and reproducibility of large language models](https://pmc.ncbi.nlm.nih.gov/articles/PMC12637745/) — separating repeatability from reproducibility and evaluating semantic stability.
- [A Theoretical Framework for Statistical Evaluability of Generative Models (ICML 2026)](https://research.google/pubs/a-theoretical-framework-for-statistical-evaluability-of-generative-models/) — limits of drawing reliable population-level conclusions from finite samples of generative behavior.

These sources inform methodology; they do not certify this plan or imply that USG is an LLM.

## 15. Initial operating principle

The first pilot should not be designed to make USG look good. It should be designed to discover what happens. The report must be allowed to show very low scores, large unsupported areas, crashes, invalid outputs, and unknown behavior. Those are useful findings. The program succeeds when it gives an honest, reproducible map of USG's actual behavior and keeps improving that map as the system changes.
