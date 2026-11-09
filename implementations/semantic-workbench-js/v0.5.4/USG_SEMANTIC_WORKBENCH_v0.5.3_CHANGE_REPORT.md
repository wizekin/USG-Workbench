# USG Semantic Workbench v0.5.3 — Change report

## Objective

Correct defective model response construction inside the existing USG workflow. This release changes the generation logic and its feedback cycle; it does not change the inference environment or select a different model.

## Implemented

- Added `generation-correction.js` for deterministic diagnosis, reviewer-report normalization, and targeted repair prompt construction.
- Added a generate → diagnose → review → repair → recheck workflow to `/api/interpret`.
- Added adaptive output-token retries when Ollama reports `done_reason: "length"` (4,096, 8,192, then 16,384 tokens).
- Added a separate reviewer pass that compares the source and full proposal. It uses the same selected model and is explicitly not treated as proof.
- Added deterministic checks for proposal shape, missing required fields, invalid polarity, missing or non-exact evidence quotes, duplicate claims, duplicate entity IDs/entities, dangling entity references, and malformed condition structures. Nested structures are retained rather than rejected, and the full raw proposal is preserved for structures that the compatibility projection cannot fully normalize.
- Added a two-round default repair budget, configurable from 0 to 3 with `USG_MAX_REPAIR_ROUNDS`.
- Added correction audit metadata to interactive and batch results, including stage, output-token metrics, repair count, reviewer status, and remaining findings.
- Added a compact audit view to the Meaning tab.
- Removed silent semantic truncation from the app adapter: no fixed count limits for claims, unresolved items, conditions, or event attributes.
- Expanded prompts to explicitly reject arbitrary semantic item-count limits and require preservation of all distinct source-grounded content.

## Not changed

- The Qwen/Gemma model tags and Ollama runtime are not replaced.
- The canonical semantic profile remains `USG-SR/0.5.1`; the compatibility schema and knowledge lifecycle are retained.
- Human acceptance remains required.
- Existing deterministic source-composition behavior remains in place.

## Known limitations

- Generator and reviewer are the same model; the second pass can share the generator's blind spots.
- The diagnosis layer is not a complete formal natural-language entailment checker.
- Repair rounds and token budgets are runtime controls. They do not impose semantic item-count limits, but a response that reaches the highest output-token boundary is still rejected as incomplete.
- A model review that reports no issues is not a semantic proof.

## Verification

The complete automated suite passes, including the new fake-Ollama integration test demonstrating: adaptive token-budget escalation, reviewer detection of an omitted clause, targeted repair, final review, and preservation of unbounded semantic item arrays in the app adapter.


## Kaggle concurrent runtime integration

The updated companion notebook incorporates the actual two-worker approach from the uploaded v0.5.2 notebook. It launches Qwen and Gemma Workbench workers concurrently after preloading both models into Ollama and confirming simultaneous GPU VRAM residency. The notebook uses a dedicated Ollama listener with its concurrency environment configured before `ollama serve` starts, avoiding the former stop/restart sequence. Each worker exports the normal v0.5.3 semantic result and `modelGenerationAudit`. This is a Kaggle evaluation-orchestration improvement; it does not alter the Workbench's semantic-generation or correction logic. See `OLLAMA_KAGGLE_CONCURRENT_SETUP.md`.
