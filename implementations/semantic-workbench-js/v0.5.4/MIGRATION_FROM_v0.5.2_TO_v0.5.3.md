# Migration: v0.5.2 → v0.5.3

v0.5.3 is an application-layer upgrade. The semantic representation profile remains `USG-SR/0.5.1`.

## Upgrade

1. Keep the v0.5.2 folder and any Kaggle outputs as a backup.
2. Attach `USG_Semantic_Workbench_v0.5.3.zip` to the Kaggle notebook as an input dataset.
3. Use `USG_Kaggle_v0.5.3.ipynb` and run its cells from top to bottom.
4. Keep the previous model tags and regression sentences for comparable testing.
5. Inspect the new `modelGenerationAudit` field in each result. It records the correction stages and remaining findings.

## New runtime control

`USG_MAX_REPAIR_ROUNDS` defaults to 2 and accepts 0–3. It controls how many feedback corrections may be attempted. It does not limit the count or complexity of semantic records.

The model output budget is retried at 4,096, 8,192, and 16,384 tokens when Ollama signals a length stop. A result truncated at the highest retry is not accepted as complete.

## Compatibility

- Existing saved workspaces are retained by the same local-storage key.
- Batch export schema remains `1.3`.
- Semantic schema version remains `0.5.1`.
- New batch result entries also carry `modelGenerationAudit`.
- The previous v0.5.2 source composer and canonical semantic graph remain included.
