# OW-12 — Native adapter and browser operation oracles

Status: implementation candidate; acceptance depends on pull-request CI.

## Objective

OW-11 established fixture-backed operation oracles for Phase 2, Phase 3, and Phase 6. OW-12 expands operation-level evidence to the composed Python USG-SEM/1.0 adapter and selected native model boundaries, and adds actual headless-browser execution for the JavaScript Semantic Workbench v0.5.4.

These are separate evidence populations. Neither browser interaction success nor adapter round-trip conformance is a measure of unrestricted semantic reasoning accuracy.

## Added operation suites

| Target | Executed operations | Oracle | Claim boundary |
|---|---|---|---|
| Python USG-SEM document adapter v1.5.1 | Compose all versioned record-family adapters, export a canonical document, round-trip all collections and sidecars, apply independent native edits, preserve unknown/canonical-only records | Controlled multi-family fixture with exact collection and preservation assertions | Fixture-backed adapter contract conformance |
| Native model boundaries | v0.6 referent identity and typed-reference model; v1.4 definitions catalogue and typed constructor invariants | Existing version-specific unit tests | Native model contract conformance for these two selected packages only |

The operation runner adds these suites as distinct target populations and includes their per-suite counts, failures, oracle descriptions, and claim levels in its JSON report. Existing Phase 2, Phase 3, and Phase 6 suites remain unchanged.

## Browser execution lane

The pull-request workflow now installs a bounded Playwright Python dependency and Chromium on `ubuntu-latest`, serves the Workbench as a local static site, and runs browser tests that:

1. Navigate to Interpret language, submit a supported sentence, and verify that an inspectable candidate is rendered with its `SUBCLASS_OF` structure in the JSON view.
2. Navigate through Knowledge base and Pattern library and verify that seeded workspace content renders.

This is real browser execution, unlike DOM-free JavaScript unit tests or import smoke checks. It verifies only the tested user-interface path and static local runtime. It does not test a connected Ollama model, all screens, accessibility comprehensively, cross-browser behavior, persistence across browser versions, or semantic correctness beyond the explicit local-rule fixture.

## Evidence separation and limitations

- Controlled adapter/model fixtures are not a naturalistic corpus and are not mixed into the random prompt scoring denominator.
- The native model suite intentionally covers selected v0.6 and v1.4 packages; it does not claim exhaustive coverage of every versioned model.
- The browser suite covers two deterministic UI paths only. It does not establish general usability or language understanding.
- Phase 6 nominal v0.4.1 remains a development self-consistency gate, not held-out accuracy.
- No naturalistic corpus is added pending licensing, attribution, provenance, redistribution, and privacy review.
- Existing worker isolation remains best-effort process isolation, not a hardened sandbox.
- A passing suite establishes only its encoded assertions on its controlled population.

## Acceptance

OW-12 is accepted when pull-request CI passes the expanded operation registry and all operation suites, and the headless Chromium job executes both browser tests successfully. The resulting evidence must retain the above claim boundaries and remain separate from random-prompt semantic scoring.
