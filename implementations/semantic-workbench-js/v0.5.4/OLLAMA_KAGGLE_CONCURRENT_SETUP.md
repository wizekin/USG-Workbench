# Ollama + Qwen/Gemma concurrent evaluation profile (USG v0.5.4)

This document describes the runtime profile used by `USG_Kaggle_v0.5.4_Concurrent_Ollama.ipynb`. It carries forward the prior Qwen/Gemma worker setup and packages the v0.5.4 generation diagnostics and semantic-consistency checks.

## Models

- `qwen2.5:1.5b`
- `dhiltgen/gemma4:e4b-it-q4_K_M-ggml`

The notebook starts its own Ollama listener, warms the exact tags through `/api/chat`, and confirms both are resident in `/api/ps` with non-zero VRAM when GPU mode is required. Separate Workbench workers are launched without waiting for one worker to finish before starting the other. This demonstrates concurrent orchestration and simultaneous residency; only timestamped request intervals can establish that the actual Workbench requests overlap during inference.

## Runtime settings

| Variable | Value | Purpose |
|---|---:|---|
| `OLLAMA_MAX_LOADED_MODELS` | `2` | Permit both model weights to remain loaded. |
| `OLLAMA_NUM_PARALLEL` | `1` | One active request per model. |
| `OLLAMA_KEEP_ALIVE` | `24h` | Keep the models resident for the evaluation window. |
| `OLLAMA_MODELS` | `/kaggle/working/ollama_models` | Keep model files in notebook working storage. |
| `OLLAMA_HOST` | dynamically selected loopback port | Avoid reusing an unrelated/default service. |
| `USG_MODEL_TIMEOUT_MS` | `300000` | Five-minute per-request deadline. |
| `USG_MAX_REPAIR_ROUNDS` | `2` | Correction iterations, not a semantic item limit. |

Use a duration with a unit for `OLLAMA_KEEP_ALIVE`, such as `24h`. A bare `-1` or `24` is not a valid duration on the Ollama build used for this workflow.

## What the v0.5.4 audit adds

Each record's `modelGenerationAudit.generationArtifacts` preserves successful raw responses and parse status for generation, review, and repair. Failed requests are retained with typed categories, error details, and HTTP response bodies when present. Timeout/transport cases state when no response was received. Output-token-limit partial text is preserved but marked incomplete. The summary CSV includes counts of these artifacts and failure categories.

The main failure categories are `repetition_abort`, `timeout`, `connection_or_transport_error`, `ollama_http_error`, `response_parse_error`, `output_token_limit`, `empty_response`, and `model_request_error`. A repetition abort is not treated as a longer token budget problem. No semantic complexity cap is applied.

## Run instructions

1. Open `USG_Kaggle_v0.5.4_Concurrent_Ollama.ipynb`.
2. Enable Internet and select a GPU in Kaggle Notebook Settings.
3. Attach a Kaggle Dataset containing `USG_Semantic_Workbench_v0.5.4.zip`. For the optional 100-case evaluation, add `USG_Kaggle_Challenge_Corpus_100.csv` to the same Dataset.
4. Run the notebook from top to bottom. The default benchmark is the original 14-sentence regression set.
5. Download `/kaggle/working/USG_Kaggle_Evaluation_Results.zip` when the notebook completes.

The notebook runs deterministic software tests before loading models. A failed preflight or worker does not become a semantic fallback score. Successful worker outputs and logs are preserved when the other worker fails.

## Important interpretation limits

- Model residency is not proof of overlapping inference; the output should be examined for overlapping request intervals if that measurement is required.
- Completed or structurally valid output is not a semantic-accuracy score.
- The reviewer is a second pass by the same selected model, not an independent evaluator.
- Full raw audit data is useful for diagnosis but may make export files larger.
- No live Kaggle Qwen/Gemma accuracy result is claimed by this package build.
