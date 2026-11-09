# USG Semantic Workbench v0.5.4 — Change report

## Objective

Improve the ability to diagnose local-model generation failures and prevent semantic metadata from contradicting the canonical graph. This release does not reduce semantic item counts or redefine completeness to accommodate a small or unreliable model.

## 1. Generation failure diagnosis

`server.js` now assigns typed categories to request failures: `repetition_abort`, `timeout`, `connection_or_transport_error`, `ollama_http_error`, `response_parse_error`, `output_token_limit`, `empty_response`, and `model_request_error`.

For Ollama HTTP failures, the diagnostic records the HTTP status and complete response body. For aborted or failed transport requests where no response exists, it records `responseReceived: false`, timing, timeout configuration, original error details, and available transport error codes. This makes a timeout distinguishable from a model-side repetition abort or a malformed JSON response.

Generation, reviewer, and repair requests now preserve failed attempts in the correction audit. When a model returns valid JSON but still omits required USG arrays after repair, USG reports `proposal_contract_failure`; when repair never yields parseable JSON, it reports `proposal_repair_exhausted`. These proposal-contract failures are not mislabeled as connection failures. Successful stages preserve the complete raw response and JSON parse result. Output-token-limit attempts preserve their partial response but are marked incomplete and rejected as complete proposals. No arbitrary semantic-item cap or automatic unbounded retry was added.

## 2. Conditional metadata consistency

The app adapter previously normalized the nested condition status too generically. It now preserves marker-specific semantics:

| Marker | Effect | Logical status |
|---|---|---|
| IF | `condition_for_assertion` | `conditional_not_asserted` |
| UNLESS | `exception_to_assertion` | `exception_relation_asserted` |
| WHEN | `temporal_condition_for_assertion` | `when_clause_not_asserted` |

For UNLESS, the compatibility condition now records the consequence represented by the parent claim and a link to that consequent. The canonical `EXCEPTION` connective stores the same metadata and retains an explicit negated antecedent. The graph validator checks the marker/connective relationship, exception antecedent shape, status, and compatibility metadata agreement.

## 3. Additional graph consistency

- Concessive (`ALTHOUGH`) connective nodes retain source-evidence references for both linked clauses.
- Derived contradiction candidates are reflected in both `claimRelations` and `semanticModel.relations` so clients of either view do not silently miss the relation.
- Proposal diagnostics now check condition effect/status mismatches and dangling proposal claim-relation endpoints.

The browser and batch adapter also retains the server failure audit when `/api/interpret` returns an HTTP error, so fallback records preserve the diagnostic instead of only preserving an error string. The Kaggle summary exports terminal proposal failure categories separately from individual failed generation artifacts. Invalid Ollama response-envelope JSON is classified as a parse failure and its full body is retained.

## 4. Regression coverage

New tests cover repetition-limit abort diagnostics, HTTP error preservation, timeout diagnostics, partial output-token response retention, full successful raw-response retention, marker-specific IF/UNLESS/WHEN metadata, canonical EXCEPTION agreement, CONCESSIVE evidence references, invalid metadata detection, and contradiction compatibility synchronization.

The complete deterministic suite passes **329 software test assertions**, plus 10 JSON Schema checks (see `TEST_RESULTS.md`). These tests validate software behavior against controlled fixtures/fake Ollama responses; they do not establish live Qwen/Gemma accuracy. The Kaggle GPU workload has not been executed as part of this package build. The companion notebook passed static parsing for all 15 Python code cells and a Node syntax check of its embedded worker script.

## 5. Compatibility

- Workbench application version: `0.5.4`.
- Semantic representation/schema profile: `USG-SR/0.5.1` (unchanged).
- No maximum count is imposed on semantic elements.
- The same-model reviewer remains a second pass, not independent verification.
