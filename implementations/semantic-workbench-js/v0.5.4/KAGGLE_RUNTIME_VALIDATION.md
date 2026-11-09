# v0.5.3 Kaggle runtime integration — validation record

Date: 2026-11-08

## Source reviewed

Reviewed the library notebook `usg-workbenh-0-5-2.ipynb`, including its saved executed concurrent benchmark cell and execution outputs. The saved run shows two workers launched without waiting for the other, 14 input cases per model, simultaneous `/api/ps` residency, and non-zero VRAM for both model tags. In that v0.5.2 saved run, Gemma produced 14 completed cases; Qwen produced 9 completed cases and 5 fallback-after-error cases. Those are historical v0.5.2 results, not v0.5.3 accuracy results.

## Applied to the v0.5.3 Kaggle setup

- Retained the exact Qwen and Gemma model tags and original 14-sentence regression set.
- Set `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_PARALLEL=1`, and `OLLAMA_KEEP_ALIVE=-1` before launching Ollama.
- Isolated the session on a dynamically selected loopback port and stopped relying on an existing Ollama daemon on `11434`.
- Used `/api/chat` for preflight, matching the endpoint the v0.5.3 Workbench actually uses; the previous notebook's `/api/generate` warm-up could fail to detect this endpoint mismatch early.
- Used `think:false` only for the Gemma warm-up request.
- Added simultaneous `/api/ps` and `size_vram` checks before the Workbench starts and after each concurrent run.
- Added two independent Node/jsdom workers launched concurrently, each selecting its own model and the dedicated Ollama URL.
- Added early checks for missing configuration, worker runner, or model preflight data.
- Made the Workbench bridge startup repeat-safe: it stops only a previous notebook-owned bridge and selects a free loopback port if the preferred one is occupied.
- Added row-level correction audit fields and a per-model operational summary; preserved service and worker logs in the downloadable result ZIP.
- Kept the v0.5.3 semantic generation/correction logic and schema unchanged in this runtime-only integration.

## Validation performed

- Notebook: 30 cells; all 15 Python code cells compile/parse.
- Embedded JavaScript runner: `node --check` passed.
- Ollama server startup cell: executed against a fake local Ollama-compatible service; dedicated-port start, `/api/version`, and `/api/tags` checks passed.
- Ollama model warm-up/residency cell: executed against simulated Qwen and Gemma responses; `/api/chat`, Gemma `think:false`, non-zero VRAM metadata, and simultaneous residency checks passed.
- Residency failure case: simulated a one-model capacity that evicts Qwen when Gemma is loaded; the notebook rejected the configuration before evaluation.
- v0.5.3 app test suite: passed (44 semantic foundation tests, 103 semantic composition tests, 65 app composition tests, smoke tests, server timeout tests, and generation-correction integration tests).

## Not performed

The notebook has not been run on a live Kaggle GPU in this packaging session, and no new Qwen/Gemma live accuracy or timing result is claimed. The existing v0.5.2 saved output only validates the earlier two-worker setup; v0.5.3 must produce its own results on Kaggle.
