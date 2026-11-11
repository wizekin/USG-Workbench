# OW-15 — Phase 4 and Phase 5 interpreter operation oracles

Status: implementation candidate; acceptance depends on pull-request CI.

## Objective

OW-14 added operation-level coverage for the Kernel Lab local API/CLI and the Workbench-to-canonical adapter. OW-15 closes another important evaluation gap by executing the bounded Phase 4 and Phase 5 interpretation services through their integrated API tests.

## Added operation suites

| Target | Executed operations | Oracle | Claim boundary |
|---|---|---|---|
| Phase 4 bounded interpreter | Interpret controlled English and Arabic examples, handle unknown lexical items, reject multiple sentences, optionally persist through the local API | Exact completion status, canonical USG-SEM document shape, preserved source text, unresolved abstention, and persistence assertions | Bounded interpreter fixture conformance |
| Phase 5 bounded interpreter | Run the versioned pipeline, inspect stage artifacts, read deterministic resource catalogue, test transaction/role boundaries, persist and replay runs | Exact pipeline contract, stage set, resource manifest digest, rollback behavior, idempotent replay, and stored source snapshot assertions | Bounded interpreter and resource contract conformance |

The runner emits these as separate target suites. They are not mixed into the random-prompt semantic score.

## Limitations

- Phase 4 and Phase 5 tests use controlled English/Arabic fixtures and bounded rule/resource behavior. They do not establish broad multilingual understanding or unrestricted language coverage.
- The Phase 5 resource catalogue digest verifies deterministic repository resources, not the completeness or correctness of an external knowledge base.
- Existing browser, adapter, native model, API, and random-prompt results remain distinct evidence populations.
- No naturalistic corpus or protected hidden holdout is added in this stage.
- Existing worker isolation remains best-effort process isolation, not a hardened sandbox.

## Acceptance

OW-15 is accepted when the operation registry and complete operation runner pass, including the new Phase 4 and Phase 5 suites. Passing results establish only the encoded fixture and API contracts, not general semantic accuracy.
