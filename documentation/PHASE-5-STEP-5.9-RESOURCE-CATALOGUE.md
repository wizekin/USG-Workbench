# Phase 5 — Step 5.9: Persistent Semantic Resource Catalogue

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Catalogue:** `sqlite-semantic-resource-catalogue/0.1.0`  
**Storage:** existing caller-owned canonical SQLite connection

## 1. Deliverables

- Append-only SQLite tables for versioned resource descriptors, provisional semantic associations, and association-use events.
- SHA-256 verification and deterministic resource manifests/digests.
- Deterministic registration of the bundled lexical, operator, grammar, discourse, frame, and expression-schema resources.
- Active/secondary association retrieval using weight, observation count, recency, and slow exponential decay.
- Immutable definitions/resources and provisional-only associations; no association promotion or identity/entailment semantics.

## 2. Canonical database boundary

The catalogue accepts a caller-owned sqlite3 connection and never opens a database file, creates a second connection, commits, or rolls back. The host must pass the same SQLite connection used by the canonical store and owns all transaction boundaries. Installation and writes require an already-open caller transaction. This adapter adds tables to the supplied database; it is not a new database backend. The current Python Kernel Database wrapper does not expose its connection as a public API, so integration must not use its test-only raw connection escape hatch. Step 5.10 must provide a safe, role-checked adapter/migration before the Kernel Lab uses this catalogue.

## 3. Immutability and versioning

Resource descriptors and association records are append-only. SQLite triggers reject update/delete. A changed resource must be registered under a new resource ID/version and a new digest. Usage events are also append-only. Usage events affect retrieval ranking but do not change the canonical resource manifest digest or registry version.

## 4. Association retrieval

For each provisional association, retrieval computes a derived activation score:

`score = weight × (1 + ln(1 + observations)) × exp(-ln(2) × age / halfLife)`

The highest-ranked associations are returned in ACTIVE and SECONDARY tiers. The score is retrieval metadata only; it is not a probability, definition, identity, or truth value. Associations remain PROVISIONAL regardless of frequency or activation.

## 5. Acceptance tests

Tests cover caller-connection reuse, transaction ownership, append-only triggers, duplicate/version behavior, deterministic manifests and digests, bundled-resource hash verification, active/secondary ranking, usage/decay behavior, no promotion, and rollback. Phase 4 and Phase 5 Steps 5.2–5.8 regressions must pass.

## 6. Integration boundary

Step 5.10 will connect this catalogue to the existing application services and Kernel Lab. The catalogue itself deliberately does not reach into private database internals or bypass the canonical store's transaction API.
