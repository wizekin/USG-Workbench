# USG Semantic Workbench v0.5.2 — Change report

## Release intent

v0.5.2 is a runtime-reliability release over the v0.5.1 semantic baseline. It deliberately does not change the canonical semantic graph contract, composition rules, supported predicate vocabulary, or evidence-validation semantics. This keeps the same source inputs comparable across the two releases.

## Changes

### Configurable model request timeout
- New environment variable: `USG_MODEL_TIMEOUT_MS`.
- Default: `180000` ms (180 seconds).
- Accepted range: 1,000–600,000 ms. Non-integer, unsafe, or out-of-range values use the default.
- The deadline covers the Ollama HTTP request and response-body read.
- Timeout messages report the effective configured duration.

### Runtime observability
- `/api/health` returns `version: "0.5.2"` and `modelTimeoutMs`.
- Kaggle notebook configures 300,000 ms and refuses to proceed if the live service does not report the expected release or timeout.
- Kaggle export records `workbenchVersion: "0.5.2"`, `semanticSchemaVersion: "0.5.1"`, and the configured timeout.

### Semantic compatibility
- `USG-SR/0.5.1` and semantic schema `0.5.1` remain unchanged.
- Existing `claims` compatibility projection and browser workspace storage key are retained.
- The deterministic semantic core and clause composer are unchanged from v0.5.1.

## Verification

The v0.5.2 suite includes all previous semantic foundation, composition, app integration, and smoke tests plus a new server timeout test using a deliberately delayed local Ollama-compatible endpoint. See `TEST_RESULTS.md` for the run report.

The automated suite does not run live model inference. Kaggle GPU/model execution remains a separate runtime check and must be repeated in the user's Kaggle session.
