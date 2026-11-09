# Migration: USG Workbench v0.5.0 → v0.5.1

## Compatibility

- v0.5.1 keeps the existing browser storage key and `claims` compatibility projection.
- Existing v0.5.0 and v0.4.0 folders should be kept unchanged as rollback points.
- New exports identify `workbenchVersion: "0.5.1"`, `semanticSchemaVersion: "0.5.1"`, and `representationProfile: "USG-SR/0.5.1"`.
- New canonical output may include composition audit metadata and source-composed clause frames.
- The original LLM proposal summary is stored separately when the source-grounded composer supplies the normalized record.

## Safe upgrade procedure

1. Stop the v0.5.0 server window.
2. Extract the v0.5.1 ZIP into a separate new folder.
3. Do not overwrite v0.5.0 or old JSON exports.
4. Start v0.5.1 using `launch_windows.bat`.
5. Check `/api/health` for `version: 0.5.1` if you need to verify which server is running.
6. Re-run the same fixed test sentences, separately on Qwen and Gemma.
7. Export both batch JSON files without manual editing.
8. Compare raw model responses, proposal summary, normalized claims, canonical graph, and semantic validation separately.

## Interpretation changes

- Empty/placeholder quantifier objects are no longer treated as unsupported quantifiers.
- Placeholder or source-unaligned event attributes are discarded.
- Supported full-source compositions may be normalized by the deterministic source composer; model output remains available in `modelProposalSummary` and in batch `rawModelResponse`.
- If the source composer cannot parse every clause and required argument, it declines and the ordinary model path remains active.
- `UNLESS` now exposes the negated antecedent explicitly while preserving the surface `EXCEPTION` relation.
- EXPECTED is separated from MUST.

## Important caution

A structurally complete composition is not proof that the parser selected the intended reading of an ambiguous sentence. Keep human review enabled and do not bulk-accept new candidate records. Milestone 1 remains under evaluation.
