# Migration Guide: USG-SR/0.4 to USG-SR/0.5

## Summary

USG v0.5.0 preserves the legacy `claims` representation and adds a canonical `semanticModel` graph. Existing v0.4 records can be opened through the Workbench's existing import/normalization path and enriched into the v0.5 representation.

## Version changes

| Item | v0.4 | v0.5 |
|---|---|---|
| Workbench | 0.4.0 | 0.5.0 |
| Semantic profile | `USG-SR/0.4` | `USG-SR/0.5` |
| Semantic record | 0.4.0 | 0.5.0 |
| Batch export | 1.2 | 1.3 |
| Canonical expression graph | Not mandatory | Mandatory |
| Structured unresolved items | Limited/unstructured | `semanticModel.unresolvedItems` |
| Quantifier binding | Claim metadata | Operator node + variable/restrictor binding |

## What remains compatible

- The legacy `claims` array remains in the record.
- Existing local knowledge data is not intentionally reset by this release.
- Existing v0.4 record and schema files remain included.
- The existing local Ollama bridge is unchanged in purpose and endpoint configuration.
- The UI continues to display the compatibility proposition view while adding the canonical graph.
- During v0.5 acceptance, the existing knowledge base still stores the reviewed compatibility claims and claim-level relations; full graph-backed knowledge persistence is deferred to Milestone 2.

## What changes in new exports

New semantic exports include:

```json
{
  "schemaVersion": "0.5.0",
  "representationProfile": "USG-SR/0.5",
  "semanticModel": {
    "profile": "USG-SR/0.5",
    "version": "0.5.0",
    "canonical": true,
    "compatibilityView": "record.claims"
  },
  "semanticValidation": {}
}
```

Batch export uses schema `1.3`, `workbenchVersion: 0.5.0`, and `semanticSchemaVersion: 0.5.0`.

## Migration cautions

1. A v0.4 claim cannot always be converted losslessly. Missing scope, argument, or clause information remains unresolved.
2. Entity IDs in the v0.5 graph are local graph identifiers and must not be treated as global identity keys.
3. Evidence offset alignment only confirms that a quote is present at the specified source span; it does not prove that the quote entails a claim.
4. The canonical graph is currently a per-interpretation representation. Accepted knowledge is still stored through the legacy claim projection; graph-backed knowledge persistence is Milestone 2.
5. A record with unresolved items may have `semanticValidation.valid: true` (its graph is structurally valid) and `semanticValidation.status: partial`. The application blocks acceptance of partial records.
6. Do not overwrite the original v0.4 data export. Keep it as a migration source and rollback point.

## Recommended update procedure

1. Stop the v0.4 server.
2. Extract v0.5.0 into a separate folder.
3. Keep the v0.4 folder and any JSON backups unchanged.
4. Start v0.5.0 using `launch_windows.bat`.
5. Use the same browser profile and local address if you need to inspect existing local workspace data.
6. Import an existing v0.4 JSON record only if needed; inspect its new `semanticModel` and `semanticValidation` fields.
7. Run the regression batch and export fresh results.
8. Compare v0.5 results with the archived v0.4 JSON exports.
