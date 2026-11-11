# OW-11 — Operation-level evaluation and independent oracles

Status: implementation candidate; acceptance depends on pull-request CI.

## Objective

OW-10 registered all inventoried component families and added import-only smoke checks. OW-11 adds a separate operation-evaluation lane for components that expose deterministic, fixture-testable operations. It must not treat module imports, synthetic expected outputs, or a candidate-only development gate as general semantic accuracy.

## Operation suites

| Target | Executed operation | Independent oracle | Claim boundary |
|---|---|---|---|
| Phase 2 structured semantic reasoning | Run the deterministic inference executor on its versioned executor fixtures | Fixture-declared completion status, candidate count, diagnostics, canonical input validity, and safety assertions | Operation contract conformance for the two enabled reference rules |
| Phase 3 canonical SQLite store | Store, reload, revision, integrity, index rebuild, and persistent-query operations | Exact canonical bytes/hash, immutable revision metadata, compare-and-swap behavior, and query revision/hash assertions | Storage and query contract conformance |
| Phase 6 candidate expansion | Predicate/argument and nominal candidate analyzers over their registered corpora | Gold role bindings/spans and negative abstention; nominal v0.4.1 has only its documented development self-consistency gate | Mixed gold-fixture conformance and development-only candidate self-consistency |

The runner is `tools/open_world_evaluation/operation_oracles.py`. It records per-target test counts, failures, errors, oracle descriptions, claim levels, and explicit limitations in a JSON report. It refuses to overwrite a report. The continuous workflow runs the suite before the random campaign and uploads the report as a separate artifact so it remains available even if later campaign stages fail.

## Separation from random prompt evaluation

Operation suites use controlled, repository-owned fixtures. They are not repeated once per random natural-language prompt, because those prompts are not valid operation inputs for structured storage, rule execution, or typed adapters. Random prompt outcomes and operation-oracle outcomes therefore remain separate populations and separate artifacts.

The operation report is not merged into the random campaign's semantic accuracy denominator. It is an additional evidence stream describing whether specific, versioned operations satisfy their stated contracts on their fixture set.

## Known limits

- The Phase 6 nominal v0.4.1 lexical resource is derived from its development positives. Its gate is not held-out accuracy and must never be reported as such.
- The Python document-adapter family, native model snapshots, Kernel Lab API/CLI, and workbench adapter remain import-smoke-only or without an operation oracle in this stage.
- The JavaScript browser UI remains not executed; OW-11 does not install an unpinned browser or pretend browser coverage exists.
- No naturalistic corpus is added. License, redistribution, attribution, provenance, and privacy review remain prerequisites.
- The existing worker remains best-effort process isolation, not a hardened sandbox.
- A passing operation suite establishes only the explicit assertions and fixture population listed by that suite. It does not establish unrestricted real-world reasoning competence.

## Acceptance

OW-11 is accepted when CI runs all listed suites against the current main commit, every suite has a non-zero test count and passes, the report clearly labels each oracle/claim boundary, and the continuous campaign retains the report artifact independently of random-prompt scoring.
