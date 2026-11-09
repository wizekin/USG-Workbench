# Migration from USG v0.5.3 to v0.5.4

## Upgrade

1. Keep a backup of your v0.5.3 folder and exported JSON files.
2. Extract `USG_Semantic_Workbench_v0.5.4.zip` into a new directory.
3. Reuse the same local Ollama models; no model download is required unless the model is not installed locally.
4. Start the new Workbench with `launch_windows.bat`.
5. For Kaggle, use `USG_Kaggle_v0.5.4_Concurrent_Ollama.ipynb` and attach the v0.5.4 project ZIP to the notebook Dataset. Add `USG_Kaggle_Challenge_Corpus_100.csv` to that Dataset only when running the optional challenge corpus.

## Compatibility

- The semantic profile remains `USG-SR/0.5.1`; the canonical semantic JSON Schemas are unchanged.
- Existing v0.5.3 semantic records remain readable by the application. New records include more complete diagnostic metadata when model calls fail.
- Existing `claims`, `claimRelations`, and `conditions` compatibility projections remain available. Derived contradiction relations are synchronized with `semanticModel.relations` in the application output.
- The release does not cap claims, entities, mentions, relations, conditions, event attributes, or unresolved items.

## New diagnostic categories

The v0.5.4 audit separates model-call failures from proposal-finalization failures. Relevant categories include `repetition_abort`, `timeout`, `connection_or_transport_error`, `ollama_http_error`, `response_parse_error`, `output_token_limit`, `empty_response`, `proposal_contract_failure`, and `proposal_repair_exhausted`.

A `proposal_contract_failure` means a valid JSON proposal still omitted one or more required USG arrays after targeted repair. `proposal_repair_exhausted` means the repair attempts did not yield parseable JSON. These are not interchangeable with a network failure. Failed call details and available raw text are retained in `modelGenerationAudit` and in batch fallback exports.

## Runtime note

Set `OLLAMA_KEEP_ALIVE` to a duration with units, such as `24h`. The v0.5.4 Kaggle notebook uses `24h`; do not use the earlier bare `-1` value that appeared in the v0.5.3 runtime setup history.

## Test status

The v0.5.4 release package passed 329 deterministic software assertions and 10 JSON Schema checks. The notebook's 15 Python code cells and embedded Node worker passed static syntax checks. These checks do not replace a live Kaggle Qwen/Gemma run or a human semantic evaluation.
