# Phase 2 Step 2.10 — Final Exit Acceptance

**Status:** Acceptance gate implemented; final acceptance is pending successful execution on the exact pull-request head and merged main commit.

## Purpose

Step 2.10 evaluates the integrated Phase 2 system as a whole. Passing the individual implementation steps is necessary but not sufficient: the final gate reruns the frozen benchmark evaluator, every Phase 2 regression suite, the integrated Kernel Lab tests, and the Phase 1 compatibility/exit suites.

This step does not add new inference rules, change semantic behavior, or relax any frozen benchmark threshold.

## Acceptance runner

Run from the repository root after installing the existing test dependency:

```powershell
py -m pip install "jsonschema>=4.18,<5"
py -m tools.phase2_exit_acceptance.run --report phase2-exit-acceptance-report.json
```

The runner records each command, exit code, duration, and bounded output tail. It continues after individual failures so the report captures all gate outcomes. The overall result is:

- `ACCEPTED` only when every required check passes;
- `NOT_ACCEPTED` if any check fails.

The report follows `tools/phase2_exit_acceptance/report.schema.json` and identifies the exact repository commit supplied by CI. GitHub Actions uploads the JSON report as the `phase2-exit-acceptance-report` artifact, including on failure when a report was produced.

## Required checks

1. Compile all Phase 2 implementation and Kernel Lab packages.
2. Validate the declarative rule registry and formal rule-semantics contract.
3. Run the frozen Step 2.2 benchmark/evaluator tests without changing its thresholds.
4. Run all Step 2.3–2.8 Phase 2 regression suites, including grounding, inference, evidence assessment, and query behavior.
5. Run the integrated Step 2.9 Kernel Lab tests.
6. Rerun Phase 1 exit acceptance, all versioned Python document-adapter regressions, predicate/frame and operator/scope registry conformance, canonical adapter/serializer/round-trip tests, and Workbench source/reconstruction tests.
7. Verify that the PR does not modify archived releases or implementation baselines.

The gate is automated; no human-review gate is introduced. A missing or failed required check prevents acceptance.

## Semantic invariants explicitly retained

The acceptance record keeps these evidence dimensions independent:

- exact quote/source-span alignment;
- declared semantic-support status;
- relation-claim assessment;
- exact-scope contradiction/conflict assessment;
- source independence;
- corroboration;
- external verification.

Passing structural, inference, or regression tests does not promote a source assertion or derived candidate to objective truth. The system does not select conflict winners. Distinct source identifiers do not establish independence. External verification remains unverified unless an explicitly trusted verifier and procedure are actually executed.

## Scope and limitations

The accepted Phase 2 implementation remains a bounded, deterministic reasoning system over explicit USG-SEM/1.0 structures and the enabled rule subset. It does not establish unrestricted natural-language understanding, objective truth determination, open-domain entailment, autonomous rule learning, distributed execution, multilingual coverage, or production readiness.

The final phase status must remain pending if the acceptance workflow is missing, failed, inconclusive, or has not run on the exact merged commit.
