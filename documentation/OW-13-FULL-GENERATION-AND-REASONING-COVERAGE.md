# OW-13 — Full native-generation and reasoning coverage

Status: implementation candidate; acceptance depends on pull-request CI.

## Objective

OW-12 added selected native-model boundary checks for v0.6 and v1.4 and expanded browser execution to basic navigation and interpretation. OW-13 closes the version gaps between those two model endpoints and exercises a real Workbench reasoning-and-export flow.

## Expanded native model suite

The registered `python-native-semantic-models-v06-v14` operation suite now runs the versioned native test modules for:

- v0.6 referent identity
- v0.7 discourse mentions
- v0.8 assertions
- v0.9 evidence
- v1.0 contexts
- v1.1 expression relations
- v1.2.1 unresolved items
- v1.3 derivations
- v1.4 semantic definitions

The tests are run from each generation's own package path. They remain a bounded contract suite: they verify the invariants encoded by those version-specific tests, not every public API behavior, all combinations of records, or end-to-end semantic accuracy.

## Expanded browser workflow

The Chromium suite adds a third end-to-end path:

1. Open the reasoning lab and run the deterministic forward-chaining engine against the seeded knowledge graph.
2. Verify the expected instance-inheritance conclusion for Tweety and Animal.
3. Export the workspace and verify that the browser produces a dated JSON backup download.

The prior browser checks for sentence interpretation and view navigation remain active.

## Evidence and limitations

- Native model contract results, adapter results, browser results, and randomized prompt results remain distinct populations.
- Browser reasoning verifies a small explicit rule set on seeded demo facts. It does not demonstrate general reasoning competence.
- The browser export test verifies download initiation and filename only; it does not validate backup restoration or cross-browser compatibility.
- The native generation suite runs existing version-specific tests; it is not a new exhaustive test of every field and operation.
- No naturalistic corpus is added pending licensing, attribution, provenance, redistribution, and privacy review.
- No hidden holdout set is introduced in this stage. A public repository cannot safely contain secret evaluation answers.
- Existing worker isolation remains best-effort process isolation, not a hardened sandbox.

## Acceptance

OW-13 is accepted when pull-request CI passes the expanded native-model suite and all three headless Chromium tests. No aggregate semantic-accuracy claim is made from these contract and UI checks.
