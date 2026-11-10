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
- **5L implementation in progress:** [Assertion document adapter v0.8.0](python-kernel-extension/STEP-5L-ASSERTION-DOCUMENT-ADAPTER.md). Projects exact, resolvable Assertion fields; keeps unsupported/dangling fields and Alternative Group references canonical-only; merges native edits only into Assertion records.
- Existing v0.4.0–v0.7.0 models, Workbench v0.5.4, USG-SEM/1.0, archives, and immutable baselines remain unchanged.
