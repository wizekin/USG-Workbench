# USG interoperability

This directory contains explicit, versioned adapters and conformance work between the distinct USG implementation lines and the canonical semantic contract.

Mappings must be exact and documented. Unsupported or lossy mappings must be reported as partial or unsupported; do not silently coerce, flatten, or discard semantic content. No full interoperability is claimed merely because the implementations are stored in this repository.

## Current Phase 1 work

### Step 1 — predicate-to-frame registry

- [Predicate-to-frame registry 1.0.0](predicate-frame-registry/README.md)
- Registry data: [v1.0.0.json](predicate-frame-registry/v1.0.0.json)
- Initial result: one conditional exact mapping (CLOSES/CLOSED → CLOSE@1); other reviewed predicates are explicitly non-mapped.

### Step 2 — operator and scope registry

- [Operator and scope registry 1.0.0](operator-scope-registry/README.md)
- Registry data: [v1.0.0.json](operator-scope-registry/v1.0.0.json)
- Covers negation, modal force/flavor, quantifier structure, logical connectives, and explicit graph-scope conversion requirements.
- Exact/conditional mappings are separated from ambiguous, partial, and unsupported readings.

### Step 3 — document-level Python adapter (completed)

- [Python adapter package](python_adapter/README.md)
- Canonical contract: [USG-SEM/1.0](../specifications/USG-SEM-1.0.md)
- JSON Schema: [usg-sem-1.0.schema.json](../specifications/usg-sem-1.0.schema.json)
- Preserves the entire canonical document for exact export while projecting only records with exact Python kernel equivalents.
- Unsupported record families and fields remain canonical-only and are reported as partial/unmapped.

### Step 4 — round-trip conformance (completed)

- [Round-trip conformance design and verified gap inventory](round-trip-conformance/README.md)
- **4A completed:** Workbench v0.5.4 → USG-SEM/1.0 source adapter, including Unicode offset conversion.
- **4B–4D completed and merged:** reverse serialization, contract-to-Workbench reconstruction, and executable four-boundary semantic invariant suite.

### Step 5 — Python kernel compatibility extension

- **5A–5J completed and merged:** native expression constructors and separately versioned Source, Referent identity, and Mention models/adapters.
- **5K completed and merged:** native Assertion model v0.8.0. [Step 5K contract](python-kernel-extension/STEP-5K-NATIVE-ASSERTION-MODEL.md).
- **5L completed and merged:** Assertion document adapter v0.8.0. [Step 5L contract](python-kernel-extension/STEP-5L-ASSERTION-DOCUMENT-ADAPTER.md).
- **5M completed and merged:** native Evidence model v0.9.0. [Step 5M contract](python-kernel-extension/STEP-5M-NATIVE-EVIDENCE-MODEL.md). It keeps source-span alignment separate from semantic support, preserves ordered/repeated supporting-rule references, and does not claim entailment or truth evaluation.
- **5N completed and merged:** Evidence document adapter v0.9.0. [Step 5N contract](python-kernel-extension/STEP-5N-EVIDENCE-DOCUMENT-ADAPTER.md). It projects exact/resolvable Evidence records, retains unknown or dangling data in the canonical envelope, and merges native edits only into Evidence records.
- **5O completed and merged:** native Context model v1.0.0 with explicit CONTEXT/SOURCE/REFERENT reference spaces. [Step 5O contract](python-kernel-extension/STEP-5O-NATIVE-CONTEXT-MODEL.md).
- **5P completed and merged:** loss-preserving Context document adapter v1.0.0. [Step 5P contract](python-kernel-extension/STEP-5P-CONTEXT-DOCUMENT-ADAPTER.md). It projects only exact Context records with resolvable typed links and retains unknown/dangling data canonically.
- **5Q completed and merged:** native ExpressionRelation model v1.1.0. [Step 5Q contract](python-kernel-extension/STEP-5Q-NATIVE-EXPRESSION-RELATION-MODEL.md). It preserves directed expression links, typed Evidence references, and explicit verification status without performing relation reasoning.
- **5R completed and merged:** loss-preserving ExpressionRelation document adapter v1.1.0. [Step 5R contract](python-kernel-extension/STEP-5R-EXPRESSION-RELATION-DOCUMENT-ADAPTER.md).
- **5S completed and merged:** native UnresolvedItem model v1.2.0. [Step 5S contract](python-kernel-extension/STEP-5S-NATIVE-UNRESOLVED-ITEM-MODEL.md). It preserves distinct unresolved statuses and leaves ambiguous scope/candidate references opaque.
- **5T completed and merged:** loss-preserving UnresolvedItem document adapter v1.2.0. [Step 5T contract](python-kernel-extension/STEP-5T-UNRESOLVED-ITEM-DOCUMENT-ADAPTER.md).
- **5T1 completed and merged:** corrected UnresolvedItem v1.2.1 with typed Expression `scopeRef` and typed Evidence references. The historical v1.2.0 package remains unchanged.
- **5U completed and merged:** native Derivation model v1.3.0. [Step 5U contract](python-kernel-extension/STEP-5U-NATIVE-DERIVATION-MODEL.md). It preserves heterogeneous provenance references as opaque IDs and keeps derivation status distinct from truth.
- **5V completed and merged:** loss-preserving Derivation document adapter v1.3.0. [Step 5V contract](python-kernel-extension/STEP-5V-DERIVATION-DOCUMENT-ADAPTER.md).
- **5W completed and merged:** native Definitions catalogue model v1.4.0. [Step 5W contract](python-kernel-extension/STEP-5W-NATIVE-DEFINITIONS-MODEL.md). It models Concepts, Frames, Roles, and Relations without inferring ontology or relation semantics.
- **5X completed and merged:** loss-preserving Definitions catalogue document adapter v1.4.0. [Step 5X contract](python-kernel-extension/STEP-5X-DEFINITIONS-DOCUMENT-ADAPTER.md).
- **5Y completed and merged:** composed USG-SEM/1.0 document adapter v1.5.0. [Step 5Y contract](python-kernel-extension/STEP-5Y-COMPLETE-DOCUMENT-ADAPTER.md).
- **5Y1 completed and merged:** composed adapter v1.5.1 delegates to the corrected UnresolvedItem v1.2.1 adapter and verifies typed cross-family references.
- **5Z implemented on branch:** Phase 1 exit acceptance tests and completion record. [Exit acceptance criteria](PHASE-1-EXIT-ACCEPTANCE.md). Phase 1 is not marked complete until the full exit CI gate passes and the PR is merged.

Existing v0.4.0–v1.0.0 model packages, Workbench v0.5.4, USG-SEM/1.0, archives, and immutable baselines remain unchanged.
