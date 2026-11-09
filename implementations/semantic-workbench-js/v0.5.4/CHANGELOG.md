## v0.5.4 — 2026-11-08

- Adds typed diagnosis for model repetition-limit aborts, timeouts, Ollama transport/HTTP failures, response parse failures, empty responses, and output-token exhaustion; distinguishes proposal-contract failure from exhausted JSON repair.
- Retains full Ollama HTTP error bodies, original transport metadata, raw successful model responses, invalid JSON text, and partial output-token-limit responses where available.
- Preserves failed generation, review, and repair attempts in `modelGenerationAudit` rather than losing them on exception paths, including through browser/batch fallback handling.
- Keeps repetition aborts distinct from output-token truncation; no automatic retry policy or semantic item-count cap is introduced.
- Fixes marker-specific condition metadata for IF, UNLESS, and WHEN, including explicit UNLESS consequent linkage and canonical EXCEPTION metadata validation.
- Preserves source evidence references on CONCESSIVE graph nodes.
- Synchronizes derived contradiction relations between compatibility and canonical graph views.
- Extends Kaggle summaries with per-request timing and proposal-failure categories; the notebook also uses the valid Ollama duration `24h` for model residency.
- Keeps the semantic profile at `USG-SR/0.5.1`; human review remains required.

## v0.5.1 — Source-grounded semantic composition correction

- Added a reusable clause composer that parses clause frames independently and composes IF, UNLESS, WHEN, BUT, OR, AND, ALTHOUGH, BECAUSE, and multi-sentence discourse structures when its grammar can safely parse every clause.
- Added source-grounded expectation operator `EXPECTED` (epistemic expectation, not deontic MUST).
- Fixed empty/placeholder quantifier metadata so it is treated as absent rather than manufacturing `UNRESOLVED_SCOPE`.
- Discarded placeholder, unsupported, or source-unaligned event attributes.
- Preserved original LLM proposals as a summary while using the source-grounded compositional parse as the normalized candidate when the whole sentence is covered.
- Added explicit concessive connective validation and composition audit metadata.
- Retained conservative fallback: if the composer cannot parse all clauses, the existing model proposal path remains in use and unresolved content is not fabricated.

## v0.5.0 — Canonical semantic foundation (first implementation)

- Added `semantic-core.js`, a browser/Node-compatible canonical graph builder and structural validator.
- Added `USG-SR/0.5`, the canonical semantic expression graph profile.
- Preserved v0.4 `claims` as a compatibility view and enriched new records with `semanticModel` and `semanticValidation`.
- Added explicit `PREDICATION`, `OPERATOR`, and `CONNECTIVE` graph nodes.
- Added scoped negation, modal, quantifier, unknown-polarity, and unresolved-scope operators.
- Bound supported quantifier variables to their predicate arguments and restrictor entities.
- Added IF, UNLESS, WHEN, and coordination connectives with non-assertion status for embedded antecedents.
- Added structured `unresolvedItems`; unsupported subordinate markers are not mislabeled as conditionals.
- Preserved unresolved pronouns as mentions rather than manufacturing pronoun-named entities.
- Added known argument-role requirements, missing-predicate protection, graph reference/cycle checks, and event-frame participant checks.
- Blocked knowledge acceptance for partial/invalid canonical semantic graphs.
- Added v0.5 record/model JSON Schemas, migration guide, implementation blueprint, and regression tests.
- Batch export advanced to schema 1.3.
- Retained v0.4 schema and documentation as historical compatibility references.

## v0.4.0 — USG Semantic Representation Specification

- Defined the `USG-SR/0.4` representation and machine-readable record schema.
- Added nested condition propositions, temporal/modality metadata, quantifier scope, event attributes, narrow coreference, provenance, and evidence tracking.
- Preserved candidate contradiction links and comparison frames.
- Restricted existing inference to selected present/asserted/unconditional claims.

## v0.3.3 and earlier

See the prior release history for source-anchored corrections, batch evaluation, fallback handling, local Ollama integration, knowledge storage, and initial symbolic inference.


## v0.5.2 — 2026-11-08

- Preserves the v0.5.1 semantic representation, source composer, graph validation, and legacy compatibility projection.
- Adds a bounded, configurable Ollama request timeout through `USG_MODEL_TIMEOUT_MS` (default 180,000 ms; allowed range 1,000–600,000 ms).
- Adds `modelTimeoutMs` to `/api/health` so notebook runs can verify effective runtime configuration.
- Updates Workbench identity and batch/workspace export release metadata to 0.5.2 while keeping semantic schema/profile at 0.5.1.
- Adds a regression test that simulates an unresponsive Ollama endpoint and verifies timeout behavior.
- Adds Kaggle evaluation configuration using a 300-second model timeout and records that timeout in each exported result bundle.

The timeout change addresses execution timeouts observed during the v0.5.1 Kaggle run. It does not claim to improve semantic accuracy.

## v0.5.3 — 2026-11-08

- Adds a generate → diagnose → review → targeted repair → recheck loop around model proposals.
- Adds deterministic diagnostics for contract shape, source evidence, duplicates, entity references, and condition structure.
- Adds a same-model reviewer pass for omissions, unsupported content, scope, polarity, argument roles, coreference, and evidence.
- Adds adaptive output-token retries when the model signals a length stop.
- Records correction-stage metrics and findings in `modelGenerationAudit` for interactive and batch results.
- Removes silent semantic count truncation for claims, unresolved items, conditions, and event attributes.
- Keeps the semantic profile at `USG-SR/0.5.1`; human review remains required.


## v0.5.3 Kaggle runtime setup revision — 2026-11-08

- Applies the proven Qwen/Gemma concurrent-worker execution path from the uploaded v0.5.2 notebook to the v0.5.3 generation-correction pipeline.
- Starts a notebook-owned Ollama server with `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_PARALLEL=1`, and `OLLAMA_KEEP_ALIVE=-1` set before the server launches.
- Uses a dedicated dynamically selected loopback port so the notebook does not unknowingly reuse or terminate an unrelated default Ollama service.
- Warms both exact model tags through the Workbench's `/api/chat` endpoint, checks `/api/ps` for simultaneous residency and non-zero VRAM, and blocks evaluation when the preflight fails.
- Launches independent Qwen and Gemma Workbench workers concurrently for regression, bulk, and Wikipedia inputs, with per-item progress files and separate logs/JSON exports.
- Records execution mode, Ollama URL/configuration, residency metadata, and the v0.5.3 `modelGenerationAudit` in each worker export.
- Keeps the semantic schema and v0.5.3 generation/diagnosis/repair behavior unchanged.
