# USG Semantic Workbench v0.5.4 — Kaggle Qwen/Gemma setup

This is the Kaggle companion for `USG_Kaggle_v0.5.4_Concurrent_Ollama.ipynb`. It runs the actual Workbench source, tests it before inference, and records the v0.5.4 generation and semantic consistency audit.

## Setup workflow

1. Checks for an NVIDIA GPU and Node.js 18+.
2. Extracts `USG_Semantic_Workbench_v0.5.4.zip` and verifies the project structure.
3. Runs the full deterministic software test suite before model inference.
4. Starts a notebook-owned Ollama listener on a free loopback port.
5. Pulls and warms `qwen2.5:1.5b` and `dhiltgen/gemma4:e4b-it-q4_K_M-ggml` through `/api/chat`.
6. Requires simultaneous model residency and non-zero VRAM when GPU mode is required.
7. Launches independent Workbench workers for each model and reports per-sentence progress.
8. Exports complete result records, failure diagnostics, raw model artifacts, logs, and summary CSVs.

## Key runtime configuration

| Setting | Value |
|---|---:|
| `OLLAMA_MAX_LOADED_MODELS` | `2` |
| `OLLAMA_NUM_PARALLEL` | `1` per model |
| `OLLAMA_KEEP_ALIVE` | `24h` |
| `USG_MODEL_TIMEOUT_MS` | `300000` |
| `USG_MAX_REPAIR_ROUNDS` | `2` |

`OLLAMA_KEEP_ALIVE` must be a duration with a unit. The notebook uses `24h`, not a bare numeric value or `-1`.

## Outputs

The notebook creates `/kaggle/working/usg_kaggle_results/` containing a JSON export per model, `modelGenerationAudit` records, `worker_*.log`, `progress_*.json`, `ollama_server.log`, `usg_server.log`, and `usg_kaggle_summary.csv`. The results ZIP includes these diagnostics.

The v0.5.4 summary adds the number of generation artifacts, raw responses received, failure records, output-limit partials, terminal proposal-failure categories, request timing, and categorized failure counts. It distinguishes operational completion from semantic accuracy.

## Failure diagnosis

The server distinguishes repetition-limit aborts, timeout, transport/connection errors, HTTP errors, invalid response JSON, output-token limit, empty response, and other request errors. It also distinguishes `proposal_contract_failure` (valid JSON missing required USG fields after repair) from `proposal_repair_exhausted` (repair never produced parseable JSON). For HTTP errors, the complete response body is retained. Where the transport fails before a response arrives, the audit records that fact and preserves available underlying error metadata. Failed generation/reviewer/repair requests remain in the correction audit.

Condition checks now require consistent marker-specific metadata: IF is conditional, UNLESS is exceptional, and WHEN is temporal. The canonical graph checks EXCEPTION antecedent negation and agrees with its condition compatibility metadata. CONCESSIVE nodes retain source evidence references, and derived contradiction relations are synchronized across compatibility and canonical graph views.

## Interpretation limits

The same model performs the reviewer pass; it is not independent verification. Structural tests do not prove semantic entailment. Concurrent worker launch and simultaneous model residency do not by themselves prove GPU inference overlap. This package has not been run against live Kaggle Qwen/Gemma inference during build; no new model accuracy result is claimed.
