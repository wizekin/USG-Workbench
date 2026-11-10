# Phase 1 Step 5C — USG-SEM/1.0 ↔ Python kernel 0.5.0 graph adapter

**Status:** implementation candidate; automated conformance pending  
**Kernel:** Python 0.5.0  
**Interchange:** USG-SEM/1.0 (unchanged)  
**Legacy boundary:** Python kernel 0.4.0 adapter remains unchanged

## Objective

Make the native constructors delivered in Step 5B usable at the canonical interchange boundary. This is an expression-graph adapter, not a claim that every USG-SEM document record is now natively represented by the Python kernel.

## Public API

- `contract_graph_roots_to_kernel_v05_partial(expressions, root_refs)`: independently projects roots, shares successfully built DAG nodes, and reports failed roots.
- `contract_graph_roots_to_kernel_v05(expressions, root_refs)`: strict convenience API; raises if any requested root cannot be projected exactly.
- `kernel_v05_graph_to_contract(imported)`: serializes current native Nodes, preserving original expression IDs when object identity is unchanged and assigning deterministic new IDs to new nodes.

The API lives in `interoperability/python_adapter/kernel_v05.py` and is exported by the adapter package. The caller must isolate the Python import path so `usg` resolves to package version 0.5.0; the adapter checks the loaded version and refuses to run against 0.4.0.

## Exact projection rules

- `PREDICATE_APP`: native SIT constructor; role-to-operand order is retained; all declared argument, event, tense/aspect/temporal, attribution, provenance, completeness, evidence and source-claim metadata is preserved.
- `CONNECTIVE`: native PROP constructor; connective identity, operand roles/order, marker, logical status, antecedent interpretation, condition metadata, disjunction semantics, attribution and evidence are retained.
- `QUANTIFIER`: native PROP constructor with one PROP body, stable binder identity, explicit scope kind, optional restrictor/binding metadata, count, surface text, evidence and attribution.
- `HOLDS` remains explicit wherever a SIT is used in a PROP position. No adapter-side implicit coercion is performed.
- `OPAQUE` and `UNRESOLVED_REF` remain distinct. Neither is eligible as an inference premise.
- Unknown operators are wrapped in OPAQUE with original operator, sort, parameters and operand references retained. This is a PARTIAL preservation mapping, not a semantic interpretation.
- Invalid known operators are not downgraded to OPAQUE. Their roots and all original expression records remain canonical-only and are reported.

## Fields outside the native AST

USG-SEM expression fields such as `semanticKind`, `interpretationStatus`, and `nativeId` are preserved in an identity-keyed sidecar. They are not silently injected into semantic equality or truth conditions. Annotation source references are restored only when their original spans remain aligned; changed native annotations are kept in a separate preservation sidecar when the source identity cannot be proven.

## Reverse serialization

Reverse serialization traverses the current native Node objects rather than replaying the input snapshot. It preserves shared DAG identity, operand order, original IDs for unchanged objects, and all canonical expressions not represented by current native projections. Changed/new nodes receive fresh `py05:node:n` IDs. Unsupported original roots remain roots.

The result includes a mapping report. OPAQUE conversions and failed known roots are PARTIAL. An explicit unresolved reference may be represented losslessly as unresolved content; that does not make it inference-eligible.

## Compatibility and non-goals

- No changes to USG-SEM/1.0 or its JSON Schema.
- No changes to Workbench v0.5.4 or Python kernel v0.4.0.
- No changes to archives or historical baselines.
- No guessed frame, connective, modal, restrictor, or truth-conditional mappings.
- No arbitrary semantic item/depth/operand caps.
- No human-review gate.
- This step does not yet import/serialize all document-level record families (sources, referents, mentions, evidence, contexts, assertions, derivations, etc.) as v0.5.0 native records. Canonical-only document records remain outside this graph adapter.

## Automated conformance

The dedicated test suite checks all three native constructors, sort invariants, metadata round trips, quantifier binder identity and alpha-equivalence, OPAQUE/UNRESOLVED_REF distinction, inference exclusion, unknown operators, malformed known operators, failed-root preservation and shared DAG identity. Existing v0.4.0 document/reverse serializer and four-boundary tests continue to run unchanged.
