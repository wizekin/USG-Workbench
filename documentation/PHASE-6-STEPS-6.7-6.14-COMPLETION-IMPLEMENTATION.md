# Phase 6 Steps 6.7–6.14 — Candidate Integration and Exit Record

**Status:** implemented and regression-tested as a candidate composition service; not a claim of broad raw-text interpretation or benchmark-enabled constructions.  
**Interpretation contract:** `USG-INTERPRET/0.3.0`.  
**Persistence:** append-only records in the existing SQLite database, through the existing store-owned connection.  
**Canonical documents:** `USG-SEM/1.0` is unchanged.

## What is implemented

- Steps 6.7–6.11: the Phase 6 composition engine validates explicitly supplied coordination, embedded-clause, voice/speech-act, scoped-operator, and discourse-reference graph candidates. A separate strict-template extractor now recognizes ten closed English/MSA patterns (one per language for each of five construction families) and abstains on unmatched input. These are candidate patterns, not broad parsing. It checks exact source spans, endpoint/target references, evidence, allowed relation/operator vocabularies, and clause-parent acyclicity. Reference candidates remain unresolved; no entity identity is inferred.
- Step 6.12: the loss-aware projection guard refuses canonical projection whenever a Phase 6 feature lacks a verified lossless `USG-SEM/1.0` mapping.
- Step 6.13: the shared local API, CLI, and Kernel Lab expose the same composition service. Candidate runs are content-addressed, append-only, digest-checked, and replayable through the existing SQLite connection. No second database owner is introduced.
- Step 6.14: an automatically generated bilingual graph-composition contract suite checks ten language/profile examples. It validates the composition boundary, not naturalistic recognition.

## Explicitly not claimed

The service can compose supplied graphs and can extract candidates for ten exact closed templates. It does **not** extract these constructions from arbitrary raw text or generalize beyond the registered token patterns. The generated benchmark is derived from explicit templates and therefore is not independent evidence of English/MSA interpretation accuracy. No Steps 6.7–6.12 constructions are marked benchmark-enabled by this increment. Step 6.6 remains bounded to its accepted graph-first synthetic-reference scope; all ten recognizers remain candidate-only.

## API

`POST /v3/phase6/extract` accepts `{ "source": string, "language": "en"|"ar", "persist": boolean }`, applies only the registered exact templates, and returns `CANDIDATE_PATTERN_MATCH` or `ABSTAIN`. A match is composed and may be persisted as a candidate run; an abstention does not create a run.\n\n`POST /v3/phase6/compose` accepts `{ "source": string, "language": "en"|"ar", "graph": object, "persist": boolean }`. It returns the candidate-only composition result, projection diagnostics, and optional immutable SQLite run metadata.

`GET /v3/phase6/runs?limit=50` lists recent candidate runs. `GET /v3/phase6/runs/{run_id}` retrieves a digest-verified run. `POST /v3/phase6/runs/{run_id}/replay` recomposes the stored input and compares the result digest.

## CLI

`usg-workbench phase6-extract source.txt --language en [--db PATH] [--no-persist] [--output PATH]` runs the strict-template recognizer. `usg-workbench phase6-compose request.json [--db PATH] [--no-persist] [--output PATH]` uses the same application dispatcher as HTTP. `usg-workbench phase6-replay RUN_ID [--db PATH]` verifies deterministic replay.

## Kernel Lab

The Phase 6 Candidate Composition panel can run strict-template extraction from source text, display the generated candidate graph, or validate an edited graph and display composition/projection diagnostics. It deliberately does not label graph composition as automatic raw-text understanding.

## Exit gate

The generated composition contract benchmark must pass, the API/CLI/Kernel Lab integration tests must pass, candidate-run append-only and replay checks must pass, and the existing Phase 5 regression must remain unchanged. A future increment is required for broader syntax-aware raw-text candidate extraction, independent per-construction bilingual acceptance, and naturalistic evaluation before any of these capabilities can be advertised as enabled.
