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


### Step 5D — kernel v0.5.0 document-level integration (completed, PR #12)

- [Step 5D document boundary](python-kernel-extension/STEP-5D-DOCUMENT-ADAPTER.md), implemented in [document_v05.py](python_adapter/document_v05.py).
- Imports and validates the complete USG-SEM/1.0 envelope, verifies the isolated kernel version is exactly 0.5.0, and projects declared expression roots through Step 5C.
- Reconstructs the full document using current native expression Nodes while retaining canonical-only record families, unreachable expressions, and metadata.
- Per-record-family coverage distinguishes native projection from canonical preservation. Step 5D initially left all document record families canonical-only; Step 5E extends this boundary for exact Source records.

### Step 5E — native Source record integration

- **Implementation candidate:** [Step 5E Source integration](python-kernel-extension/STEP-5E-SOURCE-RECORDS.md).
- Extends the v0.5.0 document adapter with native Source projections.
- Preserves opaque USG-SEM source IDs through an explicit document-local typed SOURCE reference map.
- Maps text/hash, language, source type, trust tier, sensitivity, URI, and time anchor only when exact.
- Unknown or absent enum values remain canonical-only and are explicitly listed; no default substitution or enum coercion.
- Reverse export serializes current native Source records and recomputes the SHA-256 hash after text edits. Dependent spans/evidence are checked by full-document validation.
- Referents, mentions, and all other unsupported record families remain canonical-only; no identity inference or cross-document merge is introduced.


### Step 5F — Referent integration contract and native-model gap analysis

- [Step 5F Referent contract](python-kernel-extension/STEP-5F-REFERENT-CONTRACT.md).
- This step identifies the semantic mismatch between USG-SEM/1.0 Referent identity metadata and the existing Python kernel v0.5.0 Referent record.
- The native model does not represent identity status, DOCUMENT/WORKSPACE/CORPUS/GLOBAL identity scope, explicit referent equivalence links, display labels/aliases, or all introduction-context references as distinct fields.
- These fields must not be coerced into ReferentScope, individual_ids, concept references, or labels. Referents remain canonical-only in the v0.5.0 document adapter until a separately versioned native model can represent these distinctions.
- Step 5F makes no schema or kernel-baseline changes. The next implementation step must define and test the required versioned identity model before native Referent projection.


### Step 5G — versioned native Referent identity model

- [Step 5G model contract](python-kernel-extension/STEP-5G-REFERENT-IDENTITY-MODEL.md).
- Adds an independent, additive usg_identity_v06 model at implementations/python-kernel/v0.6.0/; it does not edit the frozen usg v0.5.0 package.
- Models the six identity-resolution statuses and four identity scopes as separate axes; absent status/scope remain absent rather than defaulting to UNKNOWN or a scope.
- Uses explicit typed opaque references to keep referent equivalence, concept classification, source grounding, and introduction-context references in separate target spaces.
- Preserves explicit equivalence links without inferring symmetry, transitivity, or merging referents. Labels and aliases are never identity keys.
- Includes a native Referent record and conformance tests. Document-level adapter integration remains a later step; no full Referent round-trip is claimed yet.
- USG-SEM/1.0, Python kernel v0.5.0, Workbench v0.5.4, archives, immutable baselines, and existing Node.js workflow/action versions remain unchanged.


### Step 5H — USG-SEM/1.0 ↔ Python identity model v0.6.0 document adapter

- **Implementation:** [document_v06.py](python_adapter/document_v06.py); contract: [Step 5H Referent document adapter](python-kernel-extension/STEP-5H-REFERENT-DOCUMENT-ADAPTER.md).
- Public APIs: `document_to_kernel_v06()` and `kernel_v06_document_to_contract()`; exported from `interoperability.python_adapter`.
- Projects exact Referent identity fields into the separate v0.6.0 model, including independent status/scope, explicit typed equivalence links, concept references, supported introduction context, source grounding, and Unicode code-point spans.
- Reports per-record and per-field mapping coverage. Unsupported fields, unknown values, unresolved typed references, and additional contract properties remain canonical-only; no coercion or guessed reference-space assignment.
- Native edits are merged only into Referent records. Unchanged canonical fields, omitted fields, unknown sidecars, Mentions, and all other record families are retained.
- Export rejects stale canonical snapshots and validates the complete document, including source-span bounds.
- The v0.5.0 adapter, USG-SEM/1.0, Workbench v0.5.4, archives, immutable baselines, and existing Node.js action versions remain unchanged.


### Step 5I — native Mention model v0.7.0

- [Step 5I model contract](python-kernel-extension/STEP-5I-NATIVE-MENTION-MODEL.md).
- Adds the independent `usg_discourse_v07` package under `implementations/python-kernel/v0.7.0/`; it does not modify the v0.6.0 Referent identity model or frozen v0.5.0 kernel.
- Represents a Mention as a textual occurrence with its own opaque ID, exact surface text, resolution status, optional mention type, explicit typed Referent/antecedent links, and source grounding.
- Distinguishes MENTION, REFERENT, and SOURCE reference spaces. Surface equality, aliases, or shared Referent links never merge Mention identities.
- Does not infer antecedents, coreference, or referent assignments. Resolution status is not used to invent a link-presence rule.
- This is a model-only step; USG-SEM document adapter integration and full round-trip remain for the following step.
