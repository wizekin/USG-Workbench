# USG Growth Policy and Autonomy

**Policy contract:** `USG-GROWTH-POLICY/0.1.0`  
**Purpose:** let USG improve continuously without allowing its optimization process to drift away from its original purpose.

## North star

USG is a modular semantic-reasoning architecture built around reusable semantic classes, objects, relations, operators, construction rules, and traceable evidence. It is not intended to become only a larger word list, a collection of unrelated benchmarks, or a monolithic pattern matcher.

The system should progressively improve its ability to:

1. Retrieve lexical and morphological evidence while preserving source, lemma, form, sense, and ambiguity.
2. Recognize constructions and syntactic relations across supported language profiles.
3. Compose lexical and syntactic evidence into explicit semantic roles, frames, and relations.
4. Represent operators and scope, including negation, quantification, modality, tense, aspect, and conditionals.
5. Track discourse entities, mentions, reference candidates, and unresolved antecedents.
6. Support semantic queries, inference, evidence assessment, contradiction detection, and persistent knowledge.
7. Preserve multilingual distinctions instead of silently translating or relabeling unsupported input.
8. Explain each result through source spans, rule IDs, resource versions, candidate alternatives, and diagnostics.

## The continuous growth loop

The intended loop is:

`observe → diagnose → prioritize → propose → sandbox → evaluate → accept → replay → monitor`

- **Observe:** collect unit tests, frozen benchmark results, randomized and naturalistic campaigns, lexical evaluations, browser tests, persistence tests, and cross-implementation results.
- **Diagnose:** identify the earliest supported blocker using target-specific dependency graphs; retain parallel blockers and distinguish downstream symptoms.
- **Prioritize:** rank recurring failures by stage, diagnostic code, language, target, population, resource fingerprint, and campaign recurrence.
- **Propose:** create a bounded change proposal with exact reproducer cases and an explicit acceptance gate.
- **Sandbox:** keep new rules, lexical records, morphology, and semantic frames in candidate branches or versioned candidate resources.
- **Evaluate:** run positive, negative, ambiguous, boundary, multilingual, adversarial, regression, and replay tests as applicable.
- **Accept:** require independent evidence appropriate to the capability. Structural validity or agreement between two implementations is not enough to establish semantic correctness.
- **Replay:** rerun accepted failure cases against the exact tested commit and resource versions.
- **Monitor:** compare the new result with frozen baselines; revert or reject changes that regress accepted behavior.

## What may happen automatically

The unattended controller may:

- run scheduled tests and campaigns within explicit resource budgets;
- aggregate reports and rank recurring failures;
- create new candidate-only lexical packages and diagnostic artifacts;
- add reproducible regression cases for already accepted behavior;
- repair deterministic CI, packaging, report-generation, and test-harness defects when the repair is independently tested;
- open a pull request for review and preserve the complete evidence bundle;
- stop a proposal when evidence is incomplete or a safety gate fails.

The current evidence-driven growth controller is a planner: it reads campaign artifacts, computes first-blocker diagnostics, and publishes a ranked plan. It does not yet synthesize or merge semantic rules. This is deliberate; the next safe expansion is to automate bounded, test-backed repairs before attempting autonomous semantic-rule generation.

## Changes that require independent acceptance

The following must not be silently promoted by a background process:

- external lexical entries, lemmas, senses, morphology, and source mappings into active runtime resources;
- new syntax or construction rules;
- semantic frames, role mappings, relations, or composition rules;
- operator scope or discourse-reference rules;
- new gold labels, benchmark thresholds, or acceptance claims;
- changes to `USG-SEM/1.0`, accepted Phase 1–5 contracts, or language-profile semantics.

Promotion requires source and license review, provenance, an independent oracle or adjudicated gold where semantic correctness is claimed, held-out evaluation, negative and ambiguity tests, regression replay, and a separately versioned integration decision.

## Non-negotiable invariants

1. **Modularity:** specialized components remain independently testable and replaceable.
2. **Traceability:** every accepted interpretation must retain the source and versioned evidence that supports it.
3. **Explicit uncertainty:** ambiguity and unsupported input remain explicit; do not force a unique answer to improve completion rates.
4. **Candidate/runtime separation:** retrieved lexical and semantic evidence is not active knowledge until accepted.
5. **Contract stability:** accepted schemas and contracts change only through explicit versioned migrations.
6. **Independent evaluation:** a system cannot validate its own semantic correctness merely by repeating its own assumptions.
7. **No score gaming:** never hide unsupported outcomes, change denominators, remove difficult cases, or rewrite baselines to make a metric look better.
8. **Reproducibility:** every accepted repair has exact commit, resource versions, frozen tests, and deterministic replay evidence.
9. **Language integrity:** unsupported language profiles are reported as unsupported, not silently mapped to a different language.
10. **Rollback:** any accepted change that breaks a frozen gate is rejected or rolled back.

## How success is measured

Do not collapse USG into one intelligence score. Track separate dimensions:

- execution reliability and reproducibility;
- source/span/provenance integrity;
- lexical coverage, ambiguity, and morphology candidate quality;
- construction and syntactic-role coverage;
- semantic frame/role correctness against independent gold;
- operator scope correctness;
- discourse/reference correctness;
- abstention and unsupported-input calibration;
- cross-implementation conformance;
- persistence, query, and inference integrity;
- multilingual coverage by language and construction.

A growth plan is a prioritization artifact, not a correctness score. A completed component test is not proof of broad understanding.

## Current autonomy boundary

USG can already run scheduled lexical retrieval, scheduled evaluation workflows, deterministic diagnostics, candidate-only lexical adaptation, and replay checks. The new growth controller adds an unattended evidence aggregation and prioritization cycle. Full autonomous semantic self-correction is not yet established: it requires the independent gold, naturalistic data, safe candidate sandbox, acceptance, and rollback gates above.
