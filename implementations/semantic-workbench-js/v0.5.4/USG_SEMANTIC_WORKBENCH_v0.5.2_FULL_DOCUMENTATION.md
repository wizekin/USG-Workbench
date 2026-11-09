# USG Semantic Workbench v0.5.2 — Full documentation

## 1. Purpose and status

USG Semantic Workbench is a local-first research prototype. It accepts source text, optionally obtains a proposal from a local LLM, normalizes supported information, applies a conservative source-grounded clause composer, builds a canonical semantic expression graph, validates graph structure and evidence spans, and presents the candidate for inspection and human acceptance.

It is not a general-purpose semantic parser, theorem prover, independent entailment verifier, or AGI system. Structural validity is not proof of semantic correctness or objective truth.

## 2. v0.5.2 release summary

This is a runtime-reliability release over v0.5.1. It preserves the semantic graph, source composer, predicate frames, evidence semantics, and compatibility projection. The semantic profile remains `USG-SR/0.5.1`; the application release version is `0.5.2`.

### Runtime timeout configuration

Set `USG_MODEL_TIMEOUT_MS` before starting the Node server. Default: 180,000 ms. Valid values are integer milliseconds from 1,000 through 600,000. Invalid values fall back to the default. The timer covers the HTTP request and response-body read to Ollama.

The health endpoint returns, for example:

```json
{"ok":true,"runtime":"node-local-bridge","version":"0.5.2","modelTimeoutMs":180000}
```

Kaggle evaluation sets the timeout to 300,000 ms. The effective timeout is recorded in Kaggle exports.

## 3. Semantic processing architecture

1. Source text is retained.
2. A local model may propose structured claims, scope, and evidence. It is a proposal generator, not a truth source.
3. The finite composer parses supported clause frames and selected operators/connectives. When it covers the complete input, its frames provide the normalized candidate while the original model proposal remains available for audit.
4. The semantic core builds entities, mentions, evidence, predications, operators, connectives, typed relations, and unresolved items.
5. Structural/reference and exact-span checks run.
6. The UI shows Meaning, Structure, Evidence, and JSON views.
7. Human review is required before knowledge acceptance.

## 4. Supported composition

The source composer supports selected simple frames for NEED, LIKE, DISLIKE, WANT, USE, STOP USING, BUY/PURCHASE/ACQUIRE, INCREASE, DECREASE, REDUCE, FAIL, SELL, PRODUCE, RECEIVE, BREAK, START, CLOSE, MEASURE, and copular DIFFER. Selected constructions include IF, UNLESS, WHEN, ALTHOUGH, BECAUSE, BUT, OR, AND, negation, modality, `not every`, `no`, and short multi-sentence discourse.

`UNLESS P, Q` preserves the EXCEPTION marker and represents the ordinary simple exception reading with NOT(P). WHEN is kept distinct from IF. ALTHOUGH is concessive, not causal. BECAUSE records a source-attributed causal statement that is not independently verified. OR remains inclusive-or-unspecified unless exclusivity is explicit. EXPECTED is epistemic expectation, not automatically deontic MUST.

Arbitrary nested connectives, reported speech, relative clauses, unrestricted passive alternations, broad polysemy, attachment ambiguity, and unrestricted coreference remain outside guaranteed coverage. Unsupported or incomplete source forms should not be treated as source-composed.

## 5. Exports and compatibility

New app exports identify Workbench `0.5.2`. The semantic schema version and representation profile remain `0.5.1` / `USG-SR/0.5.1`. Batch exports remain schema `1.3`. Existing legacy `claims` compatibility view and browser workspace storage key are retained.

## 6. Kaggle evaluation

Use the companion `USG_Kaggle_v0.5.2.ipynb` and setup guide. Kaggle requires Internet for runtime/model setup and a GPU accelerator. The notebook attaches the project ZIP as a private Kaggle Dataset input, runs the deterministic test suite, starts Ollama, verifies GPU VRAM allocation, starts the Workbench server with a five-minute model request timeout, and runs the real Workbench batch workflow through a headless DOM runner.

The first run is the original 14-item regression set. The optional 100-sentence corpus is a challenge set with phenomenon labels; its labels are not gold-standard semantic parses. The notebook preserves model output and timing/fallback details.

## 7. Testing

Run `bash tests/run_all_tests.sh` on Linux/macOS or `tests\run_all_tests.bat` on Windows. Run `python tests/validate_schemas.py` for schema/fixture validation. The server timeout test uses a deliberately delayed loopback fake model endpoint.

Local automated tests do not perform live Ollama inference. Kaggle execution must be run separately to confirm the actual model pull, GPU assignment, VRAM placement, and live model outputs.
