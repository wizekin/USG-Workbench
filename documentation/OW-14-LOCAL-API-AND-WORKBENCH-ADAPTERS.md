# OW-14 — Local API and Workbench adapter operation oracles

Status: implementation candidate; acceptance depends on pull-request CI.

## Objective

OW-13 completed native-model test coverage across the available v0.6–v1.4 generations and extended browser tests through deterministic reasoning and JSON export. OW-14 adds operation-level checks for the remaining high-value integration boundaries: the Kernel Lab local API/CLI and the Workbench-to-canonical USG-SEM adapter.

## Added operation suites

| Target | Executed operations | Oracle | Claim boundary |
|---|---|---|---|
| Kernel Lab local API/CLI | Health and validation routes, document create/read/export, idempotent writes, revision conflicts, stored-snapshot queries, interpretation persistence, conditions/contradictions, invalid routes, and server binding | Existing deterministic API tests using temporary SQLite databases and versioned Phase 2 fixtures | Local API and CLI contract conformance |
| Workbench-to-canonical adapter | Convert the Workbench semantic model into USG-SEM/1.0, validate against the canonical JSON Schema, and verify source offsets, predicate/operator structure, unresolved references, and archival metadata | Controlled fixture with exact schema and field assertions | Fixture-backed adapter contract conformance |

The continuous evaluation runner now reports these as distinct suites. The JavaScript adapter's source and reconstruction test files are also run directly with Node's test runner in the PR validation lane.

## Validation boundaries

- API tests use temporary SQLite files and deterministic repository fixtures; they do not test multi-user production deployment, hostile network exposure, or load.
- The local API's loopback-only binding assertion is retained as a security boundary. This stage does not expose the API publicly.
- Adapter tests validate the explicitly represented fixture semantics and canonical schema. They do not prove lossless mapping for every possible Workbench graph.
- Node adapter tests, Python operation tests, browser tests, and random prompt outcomes remain separate evidence populations.
- No naturalistic corpus or private hidden holdout is introduced. Corpus licensing/privacy review and protected holdout infrastructure remain prerequisites.
- Existing worker isolation remains best-effort process isolation, not a hardened sandbox.

## Acceptance

OW-14 is accepted when the expanded operation runner passes, the Node adapter tests pass, and the existing Chromium browser suite remains green. Passing results establish only the tested integration contracts, not unrestricted semantic reasoning accuracy.
