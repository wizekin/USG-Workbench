# USG v0.5.4 automated test results

The v0.5.4 deterministic suite covers semantic foundation, source composition, app integration, smoke/export compatibility, server timeouts, generation correction, typed failure auditing, and the browser/batch handoff of failed-generation audits.

The release gate has passed **329 software test assertions** across the current suite, plus **10 JSON Schema checks** (2 Draft 2020-12 metaschemas, 7 canonical semantic-model fixtures, and 1 complete semantic-record fixture). The new checks include:

- repetition-limit abort distinguished from output-token truncation;
- complete Ollama HTTP error body and typed failure category retained;
- timeout/transport failure metadata retained when no response is received;
- browser and batch adapters preserve server-side failure audits instead of dropping them when `/api/interpret` returns an HTTP error;
- valid HTTP/JSON proposals that still omit required USG arrays are diagnosed as `proposal_contract_failure`, distinct from network/transport failures;
- exhausted invalid-JSON repair is diagnosed as `proposal_repair_exhausted` and retains the failed raw repair output;
- invalid Ollama response-envelope JSON is classified separately from an empty model response and the complete raw body is retained;
- full raw successful response and partial output-token-limit text preserved;
- failed generation and repair attempts retained in `generationArtifacts`;
- IF, UNLESS, and WHEN metadata distinguished and checked;
- EXCEPTION graph antecedent explicitly negated and metadata aligned with the linked consequent;
- CONCESSIVE evidence references preserved;
- contradiction relation synchronized between `claimRelations` and `semanticModel.relations`.

These are deterministic tests using fixtures and a fake Ollama-compatible endpoint. They verify software contracts, retention, and internal consistency—not actual Qwen/Gemma semantic accuracy, model quality, or independent truth verification. The live Kaggle GPU benchmark has not been executed during this packaging run. Notebook static checks also pass for all 15 Python code cells and the embedded Node worker script.
