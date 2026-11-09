# USG Semantic Workbench v0.5.4 — Full documentation

## 1. Purpose and release scope

USG Semantic Workbench is a local-first research prototype that produces inspectable semantic representations from source text and optional local LLM proposals. v0.5.4 improves generation-failure diagnosis, audit preservation, and consistency between compatibility claims/conditions and the canonical semantic graph. It does not attempt to compensate for weak models by capping semantic complexity.

## 2. Generation and correction flow

### 2.1 Generate

The selected model receives the original source, the USG proposal contract, and optional contextual knowledge. The prompt requires source-grounded propositions, explicit polarity and scope, separate clause treatment where needed, and preservation of all legitimate semantic items. It explicitly forbids maximum counts on claims, entities, mentions, relations, conditions, event attributes, or unresolved items.

The generation output budgets are adaptive runtime controls. When Ollama reports a length stop, USG retries with a larger output budget. A result that still terminates at the output boundary is rejected as a complete proposal. Partial text is retained in the generation trace for diagnosis.

### 2.2 Diagnose

`generation-correction.js` checks the proposal contract, required arrays, claim roles and polarity, evidence alignment, condition structure and marker-specific metadata, event-attribute structure, duplicate claims/entities, entity/mention references, and claim-relation endpoints. These tests are structural/source-alignment diagnostics; they do not prove entailment.

### 2.3 Review

The same selected model receives the source, complete candidate proposal, and deterministic findings in a reviewer role. It can flag omissions, unsupported content, scope/polarity/tense/modality errors, coreference issues, duplication, evidence problems, and unjustified unresolved content. The reviewer is a second pass, not an independent evaluator or proof of correctness.

### 2.4 Repair and recheck

USG sends the original source, full current proposal, and targeted findings back to the model. Correct content should be preserved while diagnosed defects are repaired. Deterministic diagnosis and the reviewer pass run again after repair. The default repair-round ceiling is configurable; it limits correction iterations, not semantic items.

## 3. Failure taxonomy and evidence retention

v0.5.4 distinguishes:

- `repetition_abort` — Ollama explicitly reports a token-repeat/repetition limit abort;
- `timeout` — the HTTP request exceeds its configured deadline;
- `connection_or_transport_error` — Ollama or the Workbench bridge cannot be reached or the transport fails before a response;
- `ollama_http_error` — Ollama returns a non-success HTTP status;
- `response_parse_error` — the Ollama response envelope or model proposal cannot be parsed as JSON;
- `output_token_limit` — the model signals a length stop or unfinished output;
- `empty_response` — the model returns no usable content;
- `model_request_error` — another request failure not covered by the above categories.

The server records timestamps, duration, phase, endpoint, timeout, HTTP status, original transport error details, and full response body when available. `responseReceived:false` distinguishes a timeout/transport failure from an HTTP response. Generation, review, and repair failures remain in `modelGenerationAudit.generationArtifacts`; they are not silently omitted. Successful raw model responses and parse status are preserved. Partial response text from output-token-limit attempts is retained but marked incomplete.

The browser and batch adapter now preserve the server's failure audit on HTTP error paths. Thus a `fallback_after_error` record can carry both the local-rule fallback interpretation and the full model-failure audit. The fallback result must not be counted as a successful LLM generation.

A repetition abort is not reclassified as an output-token limit. USG does not simply retry it by increasing the output budget or silently discard it. The audit is evidence for designing a targeted retry policy later.

## 4. Semantic consistency changes

### 4.1 IF, UNLESS, and WHEN

Compatibility metadata is normalized from the source marker:

| Marker | Effect | Logical status |
|---|---|---|
| IF | `condition_for_assertion` | `conditional_not_asserted` |
| UNLESS | `exception_to_assertion` | `exception_relation_asserted` |
| WHEN | `temporal_condition_for_assertion` | `when_clause_not_asserted` |

The condition is explicitly linked to its actual parent/consequent claim. If a model supplies a conflicting effect, logical status, vague `unspecified` consequence, or dangling consequent identifier, the application adapter derives canonical metadata from the marker and parent claim. The original raw model response remains available in the generation audit.

For `UNLESS P, Q`, USG stores the exception condition as an explicit `NOT(P)` antecedent and preserves `Q` as the parent claim/consequent. The original `UNLESS` marker remains attached to the canonical `EXCEPTION` connective. The graph validator rejects incompatible marker/type/status/effect metadata and verifies the negated antecedent structure.

`WHEN` remains distinct from `IF`; the graph validator treats a generic conditional effect on a `WHEN` connective as an error, not merely an informational warning.

### 4.2 Concessive evidence and contradiction relations

`ALTHOUGH` produces a `CONCESSIVE` connective whose evidence references preserve both linked source clauses. Derived contradiction candidates are synchronized between the compatibility `claimRelations` collection and the canonical `semanticModel.relations` collection.

## 5. Export and Kaggle evaluation

The Kaggle companion notebook is `USG_Kaggle_v0.5.4_Concurrent_Ollama.ipynb`; it expects `USG_Semantic_Workbench_v0.5.4.zip` as a dataset input. It runs the deterministic suite before model inference and retains the existing Qwen/Gemma 14-case regression benchmark. The evaluation summary includes request timestamps/latency, audit artifact counts, raw response counts, failure-stage counts, repetition aborts, timeouts, transport failures, HTTP failures, and output-token partial counts.

The notebook creates individual per-model JSON exports and a ZIP containing those exports, summary CSV, worker logs, progress snapshots, and service logs. Concurrent worker launch and simultaneous residency do not by themselves prove overlapping inference; inspect the timestamped request intervals when that distinction matters.

## 6. Test evidence and interpretation limits

The v0.5.4 deterministic suite passes 329 software test assertions. A further 10 JSON Schema checks pass, including both schema metaschemas, seven graph fixtures, and a complete semantic-record fixture. These tests use local deterministic fixtures and a fake Ollama-compatible server; they validate software contracts and failure/audit handling, not live model accuracy. All 15 Python code cells in the companion notebook parse successfully, and its embedded Node worker passes `node --check`.

The live Kaggle Qwen/Gemma benchmark has not been run during package construction. A structurally valid or `reviewed` result is not an accuracy score. The same-model reviewer may share the generator's blind spots. Human assessment and independently labelled test data remain necessary.

## 7. Semantic capacity policy

There are no arbitrary count limits for semantic claims, entities, mentions, relations, conditions, event attributes, or unresolved items. Resource/time limits can stop a computation or trigger an incomplete-response diagnosis, but they must never silently redefine the amount of meaning the source is allowed to contain.
