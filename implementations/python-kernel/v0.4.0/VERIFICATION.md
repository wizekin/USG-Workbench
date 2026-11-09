# Verification report: USG 0.2.0

Date: 2026-10-23. Runtime: Python 3.12.14, SQLite 3.53.1, Windows.

- Full regression suite: **375 tests passed** (`test-results.txt`). This includes
  the original tests, recovered validator tests, new integration/CLI tests,
  permission and quota checks, lifecycle/rollback checks, and hostile binary
  input tests with 500 seeded mutations plus truncation cases.
- Constructed test split: **49 cases passed**, including 40 supported or
  explicitly ambiguous representations and 9 cases requiring abstention.
  Frame accuracy and role F1 are 1.0 on this small subset; no false-confident
  resolution, validation failure or contrastive collapse was observed. All
  49 binary round trips passed. See `benchmark-baseline.json` for the measured
  confidence interval, timing scope and codec sizes. These numbers do not
  establish accuracy on arbitrary documents.
- Fresh unattended inbox demo: one job completed; seven source units produced
  six source assertions and one unresolved candidate. Code seal, foundation
  hash, audit chain, stored types, evidence and spans verified successfully.
- Reversible export produced `output/demo.usbf`; quarantine re-import into a
  fresh database and subsequent integrity verification both passed. Imported
  archive statuses were not trusted.
- SQLite snapshot creation passed: `output/demo-snapshot.db`.
- Offline wheel build and isolated installation passed. The installed package
  independently ingested and audited a source with no third-party dependency
  or model request. Result: `output/package-smoke-result.json`.

The implementation requires no human review and no AI service in normal use.
Optional local/remote gateways were tested with mocked transports; no claim is
made about an untested provider/model's accuracy or free-plan availability.

The exact implementation boundary is recorded in `IMPLEMENTATION.md`.
Unrestricted universal language understanding, unconstrained ontology invention,
production-scale domain sharding and the proposed compact bit-packed USBF
layout remain outside this bounded reference implementation.
