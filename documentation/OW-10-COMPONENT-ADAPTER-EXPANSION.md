# OW-10 — Component adapter expansion

Status: implementation candidate; acceptance depends on pull-request CI.

## Scope

OW-10 expands the open-world target registry from the three initial profiles to all 11 component families in the OW-0 capability inventory. The continuous campaign now derives its matrix width from `target_profiles.json`; prompt budgets are therefore multiplied by the registered target count rather than a hard-coded three.

The newly registered families are:

- Python native semantic-record model generations (v0.6.0–v1.4.0)
- Python USG-SEM document adapters
- Phase 2 structured semantic-reasoning services
- Phase 3 canonical SQLite store and persistent query interface
- Phase 6 predicate/frame and nominal candidate modules
- USG Kernel Lab local API/CLI
- JavaScript Workbench-to-canonical adapter
- Python reference-kernel v0.4.0 import baseline

The original Phase 4, Phase 5, and JavaScript browser-workbench profiles remain registered.

## What the new Python adapters actually test

For Python package families, the worker imports only the exact module allowlist declared in the target profile. It executes one fresh child process per scenario, using the existing OW-3 process controls. A successful import is reported as `partial`, with explicit metadata that semantic accuracy was not assessed. An import failure is recorded as a runtime failure; it is not converted into a successful result.

This is intentionally an entry-point availability smoke test. It does **not** invoke each module's full business operation, validate semantic outputs, or establish reasoning quality. Model-only packages and adapters must not be scored as natural-language interpreters.

## Explicitly not completed in OW-10

- Browser automation for the JavaScript UI and the JavaScript adapter is still unavailable; these profiles remain `not_executed` until a pinned Playwright/browser runtime, launch/teardown protocol, and UI-specific oracles are implemented.
- Python reference-kernel v0.5.0 is not separately exercised by the v0.4.0 baseline profile.
- The Python smoke adapters do not yet call each service's domain operations. Follow-on adapter work must add isolated, version-pinned operation probes and independent contract oracles.
- The worker remains best-effort process isolation, not a hardened hostile-code sandbox. Do not execute untrusted third-party code with it.
- Naturalistic corpus import remains blocked on license, redistribution, and privacy review. No hidden evaluation corpus or secret seed is stored in this public repository.

## Acceptance

The PR validation workflow checks that every inventory component has exactly one target profile, every declared adapter path exists inside the repository, and campaign budgets are computed from the current registry. Import-smoke execution is evaluated separately from semantic correctness. The expanded matrix increases scheduled campaign size; review the resulting runtime and artifact size before raising cadence budgets.
