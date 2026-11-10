# USG interoperability

This directory contains explicit, versioned adapters and conformance work between the distinct USG implementation lines and the canonical semantic contract.

Mappings must be exact and documented. Unsupported or lossy mappings must be reported as partial or unsupported; do not silently coerce, flatten, or discard semantic content. No full interoperability is claimed merely because the implementations are stored in this repository.

## Current Phase 1 work

### Step 1 — predicate-to-frame registry

- [Predicate-to-frame registry 1.0.0](predicate-frame-registry/README.md)
- Registry data: [v1.0.0.json](predicate-frame-registry/v1.0.0.json)
- Initial result: one conditional exact mapping (`CLOSES/CLOSED` → `CLOSE@1`); other reviewed predicates are explicitly non-mapped.

### Step 2 — operator and scope registry

- [Operator and scope registry 1.0.0](operator-scope-registry/README.md)
- Registry data: [v1.0.0.json](operator-scope-registry/v1.0.0.json)
- Covers negation, modal force/flavor, quantifier structure, logical connectives, and explicit graph-scope conversion requirements.
- Exact/conditional mappings are separated from ambiguous, partial, and unsupported readings.

### Step 3 — document-level Python adapter (completed)

- [Python adapter package](python_adapter/README.md)
- Canonical contract: [USG-SEM/1.0](../specifications/USG-SEM-1.0.md)
- JSON Schema: [usg-sem-1.0.schema.json](../specifications/usg-sem-1.0.schema.json)
- Preserves the entire canonical document for exact export while projecting only source records, supported SemIR roots and assertions that have exact Python kernel 0.4.0 equivalents.
- Referents, mentions, evidence assessments, contexts, definitions, expression relations, unresolved items, derivations, validation metadata and extensions remain canonical-only and are explicitly reported as partial/unmapped where no exact native model exists.
- No SQLite migration, Workbench runtime integration, or changes to either immutable implementation baseline are included.

### Step 4 — round-trip conformance (completed)

- [Round-trip conformance design and verified gap inventory](round-trip-conformance/README.md)
- **4A completed:** [Workbench v0.5.4 → USG-SEM/1.0 source adapter](workbench_adapter/README.md), including exact native snapshot retention, partial-mapping diagnostics, and UTF-16 → Unicode code-point offset conversion.
- Node adapter tests and Python JSON Schema validation are included in CI.
- **4B implementation and CI passed (PR #5 merged):** `python_to_contract_document()` serializes current Python projections into USG-SEM/1.0 and preserves unsupported canonical-only records. **4C completed and merged (PR #6):** `contractToWorkbench()` reconstructs Workbench v0.5.4 from USG-SEM/1.0. **4D completed and merged (PR #7):** executable four-boundary semantic invariant suite passed. Step 3's unchanged-snapshot export is not treated as a reverse serializer.

### Step 5 — Python kernel compatibility extension (active)

- **5A completed and merged (PR #9):** [Python kernel extension semantic contract](python-kernel-extension/STEP-5A-CONTRACT.md). It defines native semantics and invariants for `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER`, including sorts, role/operand alignment, quantifier binding, safe mapping to existing `Q`, serialization, canonicalization, compatibility, and negative conformance cases.
- Step 5A was a design-only change and did not modify USG-SEM/1.0 or either immutable baseline. **5B completed and merged (PR #10):** Python kernel v0.5.0 adds native `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER` constructors plus binder-aware utilities. The v0.4.0 baseline remains immutable.

The registries and adapter target the immutable baseline pair: Workbench v0.5.4 and Python reference kernel 0.4.0. They do not yet establish complete runtime interoperability.

- **5C completed and merged (PR #11):** [Step 5C adapter contract and implementation](python-kernel-extension/STEP-5C-ADAPTER.md); versioned expression-graph adapter at [kernel_v05.py](python_adapter/kernel_v05.py). It projects supported USG-SEM expressions into native v0.5.0 nodes, serializes current nodes back to the contract graph, and keeps v0.4.0 adapter behavior unchanged. Unsupported operators remain explicit `OPAQUE`; invalid known constructions remain canonical-only and are reported.


### Step 5C — USG-SEM ↔ Python kernel v0.5.0 graph adapter

- Adapter API: `contract_graph_roots_to_kernel_v05_partial()`, strict `contract_graph_roots_to_kernel_v05()`, and `kernel_v05_graph_to_contract()`.
- The v0.4.0 document adapter and serializer remain unchanged and continue to target the immutable reference baseline.
- Native constructors preserve SIT/PROP distinctions, ordered role bindings, connective identity, stable quantifier binder identity, and structured metadata.
- Unknown operators are preserved as inference-ineligible `OPAQUE` nodes; `UNRESOLVED_REF` remains a distinct node. Invalid known operators are not downgraded to OPAQUE; their canonical roots remain preserved and are reported.
- Expression-level `semanticKind`, `interpretationStatus`, and `nativeId` remain sidecar metadata rather than being mistaken for kernel truth conditions.
- Reverse serialization traverses current native nodes, preserves DAG identity and canonical-only expressions, and reports partial mappings. No USG-SEM schema change is required.


### Step 5D — kernel v0.5.0 document-level integration

- **Implementation candidate:** [Step 5D document boundary](python-kernel-extension/STEP-5D-DOCUMENT-ADAPTER.md), implemented in [document_v05.py](python_adapter/document_v05.py).
- Public APIs: `document_to_kernel_v05()` and `kernel_v05_document_to_contract()`; exported from the Python adapter package.
- Imports the complete USG-SEM/1.0 envelope, validates it, verifies the isolated kernel version is exactly 0.5.0, and projects declared expression roots through Step 5C.
- Reconstructs the complete document using fresh serialization of current native Nodes while retaining all canonical-only record families, unreachable expressions, and document metadata.
- Per-record-family coverage distinguishes native projection from canonical preservation. Sources, referents, mentions, assertions, evidence, contexts, definitions, relations, unresolved items, derivations, validation, mapping, and extensions remain canonical-only/preserved; no unimplemented native record equivalence is claimed.
- Edited/replaced native nodes receive fresh IDs; unchanged object identities retain their original IDs. Mutating the canonical snapshot is rejected.
- Step 5D does not change USG-SEM/1.0, the v0.4.0 adapter, Workbench v0.5.4, archives, or historical baselines.
