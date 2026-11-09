# Migration: USG Workbench v0.5.1 → v0.5.2

## Compatibility

- Semantic schema remains `0.5.1`; representation profile remains `USG-SR/0.5.1`.
- New Workbench release identity is `0.5.2`.
- Batch export remains schema `1.3`; `workbenchVersion` is `0.5.2` and `semanticSchemaVersion` is `0.5.1`.
- The existing browser storage key and legacy `claims` projection are retained.
- Existing v0.5.1 and earlier folders should remain unchanged as rollback points.

## Runtime timeout

Set `USG_MODEL_TIMEOUT_MS` before starting `server.js` to override the Ollama request deadline. The default is 180 seconds. Allowed values are integer milliseconds from 1,000 through 600,000; invalid values use the default. Kaggle evaluation uses 300 seconds to reduce avoidable fallback caused by slower model responses.

The live `/api/health` endpoint reports `modelTimeoutMs` and the running release version. Do not rely on a stale server window: verify both values before a batch run.

## Safe upgrade

1. Keep the v0.5.1 folder and results unchanged.
2. Extract `USG_Semantic_Workbench_v0.5.2.zip` into a separate folder.
3. Run `tests/run_all_tests.bat` on Windows (or `bash tests/run_all_tests.sh` on Linux).
4. Start the new server and confirm `/api/health` returns version `0.5.2`.
5. Re-run the fixed 14-sentence benchmark with the same model tags and settings.
6. Compare normalized claims, composition audit, canonical graph, validation, raw model output, and timeout/fallback counts separately.

A longer timeout may increase maximum waiting time for an individual slow request. It does not improve or certify the model's semantic interpretation.
