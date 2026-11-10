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

### Step 4 — round-trip conformance (active)

- [Round-trip conformance design and verified gap inventory](round-trip-conformance/README.md)
- **4A completed:** [Workbench v0.5.4 → USG-SEM/1.0 source adapter](workbench_adapter/README.md), including exact native snapshot retention, partial-mapping diagnostics, and UTF-16 → Unicode code-point offset conversion.
- Node adapter tests and Python JSON Schema validation are included in CI.
- **4B implementation and CI passed (PR #5 merged):** `python_to_contract_document()` serializes current Python projections into USG-SEM/1.0 and preserves unsupported canonical-only records. **4C completed and merged (PR #6):** `contractToWorkbench()` reconstructs Workbench v0.5.4 from USG-SEM/1.0. **4D completed and merged (PR #7):** executable four-boundary semantic invariant suite passed. Step 3's unchanged-snapshot export is not treated as a reverse serializer.

### Step 5 — Python kernel compatibility extension (in progress)

- **5A contract drafted:** [Python kernel extension semantic contract](python-kernel-extension/STEP-5A-CONTRACT.md). It defines native semantics and invariants for `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER`, including sorts, role/operand alignment, quantifier binding, safe mapping to existing `Q`, serialization, canonicalization, compatibility, and negative conformance cases.
- Step 5A is a design-only change. It does not modify USG-SEM/1.0, either immutable implementation baseline, or the current adapters. Step 5B will implement the contract in a separately versioned Python kernel release only after the contract checks pass.

The registries and adapter target the immutable baseline pair: Workbench v0.5.4 and Python reference kernel 0.4.0. They do not yet establish complete runtime interoperability.

- **5B implementation in progress:** new versioned Python kernel package at [v0.5.0](../implementations/python-kernel/v0.5.0/README.md). The immutable v0.4.0 baseline remains unchanged. Step 5B adds typed native constructors and binder-aware utilities; exact semantic mappings remain explicit and conservative.
