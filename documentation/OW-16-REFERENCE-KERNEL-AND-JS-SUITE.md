# OW-16 — Reference kernel and full Workbench regression coverage

Status: implementation candidate; acceptance depends on pull-request CI.

## Objective

OW-15 added integrated operation oracles for Phase 4 and Phase 5. OW-16 adds the older Python reference-kernel contract boundary and runs the full existing JavaScript Workbench regression suite rather than only the focused adapter tests.

## Reference-kernel operation suite

The registered `python-reference-kernel-v04-v05` suite includes:

- v0.4.0 core records and lifecycle/epistemic transition invariants
- Grammar builders, sorts, scope, alpha-renaming, canonical serialization, and structural/full hashes
- Frame inheritance, role constraints, ontology compatibility, and validation rules
- Formal candidate validator behavior and rule-citation checks
- v0.5.0 adapter and document-adapter round-trip/metadata preservation fixtures

The v0.4 tests are aggregated through the kernel's own `tests` package so its helper modules and relative imports resolve correctly.

## JavaScript Workbench regression suite

The PR validation lane now runs the repository's complete `run_all_tests.sh` script in addition to the Workbench-to-canonical adapter tests and headless Chromium UI tests. This includes JavaScript syntax checks and the existing semantic foundation, composition, app composition, failure audit, local interpretation smoke, server timeout, and generation-correction suites.

## Claim boundaries

- The reference-kernel tests are controlled implementation contract tests, not a naturalistic language corpus.
- The Workbench JavaScript tests establish the tested source-level and application regression assertions only.
- Browser UI tests, Node regression tests, Python kernel tests, API tests, and random prompt campaigns remain separate evidence populations.
- Passing reference-kernel tests do not prove that later model generations inherit all v0.4 guarantees.
- No naturalistic corpus or private holdout is added. Licensing/privacy review and protected evaluation storage remain prerequisites.
- Existing worker isolation remains best-effort process isolation, not a hardened sandbox.

## Acceptance

OW-16 is accepted when the expanded operation runner passes, the full Workbench JavaScript regression script passes, and the existing Chromium browser suite remains green. No aggregate general semantic-accuracy claim is made.
