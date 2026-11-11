# Phase 5 — Step 5.10: Integrated API, CLI, and Kernel Lab

**Status:** IMPLEMENTED CANDIDATE — exact-head acceptance pending  
**Pipeline:** `USG-INTERPRET/0.2.0`  
**Integration service:** `phase5-interpretation-integration/0.1.0`  
**Persistence:** one canonical SQLite store and one store-owned connection

## 1. Purpose

Step 5.10 exposes the already implemented Phase 5.2–5.9 artifacts through the existing local application. It does not add new grammar coverage or silently convert the v0.2 semantic graph into a `USG-SEM/1.0` document.

The integration is deliberately an orchestration and inspection boundary:

1. preserve the exact source snapshot;
2. run the accepted v0.2 lexical, segmentation, operator, syntax, semantic-composition, and discourse stages;
3. return all candidates, alternatives, spans, statuses, resource versions, and diagnostics;
4. optionally persist the complete interpretation envelope as an immutable processing run;
5. allow deterministic replay against the exact resource manifest used by the original run.

## 2. Store-owned connection and role-checked access

`CanonicalDocumentStore` remains the sole SQLite connection owner. Step 5.10 adds `resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=False|True)`:

- only the declared `USG_RESOURCE_CATALOGUE` role is accepted;
- read sessions set SQLite `query_only` and reject writes;
- write sessions acquire the store lock, begin `BEGIN IMMEDIATE`, and own commit/rollback;
- nested or externally opened transactions are rejected;
- the adapter returns the exact connection already owned by the canonical store;
- closing the store closes the connection used by the resource catalogue and run store.

Neither `SQLiteResourceCatalogue` nor `SQLiteInterpretationRunStore` opens, closes, commits, or rolls back a connection. Their schema installation and writes occur only inside the caller's transaction. No test-only raw connection escape hatch or second database connection is used.

## 3. Integrated v0.2 pipeline

`Phase5InterpretationService` orchestrates the existing modules in this order:

1. `ingest_source` — exact text, language profile, deterministic source ID, SHA-256;
2. lexical and morphology candidate analysis using the bundled v0.3 lexicon;
3. sentence/clause segmentation;
4. operator candidate and scope analysis;
5. syntax candidate analysis with recognized operator tokens excluded from ordinary argument selection;
6. nested semantic composition using the registered frame set;
7. discourse mention, reference-candidate, and sentence-relation analysis.

The result envelope includes:

- `USG-INTERPRET/0.2.0` and integration version;
- exact source text, language, source ID, SHA-256, and Unicode code-point offset declaration;
- resource manifest digest and exact resource IDs, types, versions, and hashes;
- every stage's version, status, and serialized artifact;
- semantic graph composition and candidate alternatives;
- discourse reference candidates;
- explicit diagnostics and resource limits;
- safety declarations that no USG-SEM document was emitted, no truth was promoted, and no identity or association was resolved.

The pipeline's completion status is conservative: unsupported, ambiguous, partial, and resource-limited outcomes remain explicit. A completed execution is not automatically a complete interpretation.

## 4. Immutable interpretation runs and deterministic replay

The new `usg_interpretation_run` table is an append-only processing-artifact ledger in the same canonical SQLite database file and connection. It is not a second canonical semantic-document store.

- The complete result envelope is canonicalized as UTF-8 JSON.
- The run ID is derived from the result SHA-256 digest; identical results are idempotent.
- The exact source text is checked against its source digest before persistence and on retrieval.
- SQLite triggers reject run updates and deletes.
- A run pins the resource manifest digest that governed its interpretation.
- Replay re-runs the stored source with the same current manifest and compares the complete canonical result digest.
- If the catalogue manifest has changed, replay is refused with an explicit resource-mismatch response rather than silently using new resources.

Usage events do not change the resource manifest digest; adding a resource or provisional association does.

## 5. Local API

The existing `USGApplication` dispatches both Phase 4 `/v1` and Phase 5 `/v2` routes.

| Method | Route | Purpose |
|---|---|---|
| GET | `/v2/resources` | Resource manifest, registry version, and manifest digest |
| POST | `/v2/interpret` | Run Phase 5 pipeline; optional immutable persistence |
| GET | `/v2/interpretations?limit=N` | List recent immutable run IDs |
| GET | `/v2/interpretations/{run_id}` | Retrieve and integrity-check a stored run |
| GET | `/v2/interpretations/{run_id}/export` | Export the exact stored interpretation envelope |
| POST | `/v2/interpretations/{run_id}/replay` | Re-run and compare the exact result digest |
| POST | `/v2/associations` | Register an explicitly provisional association |
| GET | `/v2/associations?source_ref=...` | Retrieve exact-source provisional candidates by ACTIVE/SECONDARY ranking |
| POST | `/v2/associations/{association_id}/use` | Append an association usage event |

The existing Phase 4 `/v1/interpret` endpoint is unchanged and continues to emit a canonical `USG-SEM/1.0` document for its bounded accepted scope.

## 6. CLI

The same `USGApplication` services are exposed through:

- `usg-workbench interpret-v2 <file> --language en|ar [--no-persist] [--output result.json]`;
- `usg-workbench resources`;
- `usg-workbench associations <source_ref> [--active-limit N] [--secondary-limit N]`;
- `usg-workbench replay <run_id>`.

All commands accept the existing `--db` path and use the same canonical SQLite store.

## 7. Kernel Lab

The local-only Kernel Lab now routes `/v2` requests through the same application instance and adds:

- a Phase 5 source-text panel with English/MSA Arabic selection;
- optional immutable run persistence;
- full stage, semantic-composition, alternatives, and diagnostic inspection;
- stored run ID and deterministic replay comparison;
- resource manifest inspection;
- exact-source provisional association retrieval.

The browser does not open SQLite, maintain a parallel database, or implement semantic interpretation logic. It is a view over the local application API. The server remains loopback-only.

## 8. Explicit limits

- The v0.2 pipeline remains limited to the constructions enabled by Steps 5.2–5.8 and their registered resources.
- The result envelope is not a `USG-SEM/1.0` document. Canonical document persistence continues through the existing v1 document routes only.
- Association retrieval does not resolve identity, promote definitions, or establish entailment.
- Resource manifests pin bundled descriptors and implementation digests; this step does not add arbitrary runtime code loading or unrestricted resource editing.
- No model, cloud API, paid service, telemetry, or network dependency is introduced.
- No Phase 1–4 contract, Phase 4 v0.1 behavior, normative USG-SEM schema, archived release, or historical implementation is rewritten.

## 9. Acceptance

The Step 5.10 suite verifies:

- role-gated, read-only and transactional access to the store-owned connection;
- rollback of failed catalogue operations;
- deterministic bundled-resource registration and manifest digest;
- exact source fidelity and all six Phase 5 stage artifacts;
- immutable/idempotent run persistence, integrity-checked export, and deterministic replay;
- refusal to replay when the resource manifest changes;
- provisional association registration, retrieval, and append-only usage;
- CLI command exposure;
- real HTTP routing through the Kernel Lab server and Phase 5 UI controls.

The dedicated workflow runs Step 5.10 tests, all Phase 5 regressions, frozen Phase 4 tests, Phase 3 local API/CLI and graph-store regressions, plus protected-contract diff checks. Existing Phase 3 integrated exit and Step 5.9 resource-catalogue workflows are also triggered by the changed integration paths.

## 10. Next step

After this step passes exact-head CI and merges, proceed to **Step 5.11 — Expanded Benchmark, Performance, and Integrated Exit Acceptance**. Step 5.11 will measure the actual enabled construction coverage and resource-limit behavior on the exact merged main commit; it must not broaden grammar merely to improve aggregate scores.
