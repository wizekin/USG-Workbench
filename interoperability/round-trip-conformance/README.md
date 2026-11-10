# Phase 1 Step 4 — Round-trip conformance

**Status:** Step 4A–4D implemented, CI-validated, and merged (PRs #5–#7)  
**Contract:** USG-SEM/1.0  
**Baseline pair:** Semantic Workbench 0.5.4 / Python reference kernel 0.4.0  
**Branch:** `phase1/semantic-invariant-conformance`

## Objective

Establish executable, semantic-invariant conformance across:

`Workbench 0.5.4 native model → USG-SEM/1.0 → Python kernel 0.4.0 → USG-SEM/1.0 → Workbench 0.5.4 native model`

This is not satisfied by importing a canonical document and returning an unchanged copy. Each conversion boundary must execute, and the test must compare meaning-bearing invariants.

## Verified starting point

1. The Step 1 predicate/frame registry and Step 2 operator/scope registry describe approved and conditional mappings. They are registries, not runtime adapters.
2. Step 3 provides a document-level USG-SEM → Python projection. It preserves the canonical document as an authoritative snapshot and refuses to export that snapshot after mutation.
3. Step 4B now provides `python_to_contract_document()`, which serializes current Python `Source`, `Node`, and `Assertion` projections into a new USG-SEM document. It retains unsupported canonical-only records and reports them as partial/unmapped.
4. Step 4A now provides an executable Workbench 0.5.4 → USG-SEM adapter.
5. Workbench's native semantic core emits `PREDICATION`, `OPERATOR`, and `CONNECTIVE` expression records with explicit references and scope metadata. These are the source structures to adapt; display text is not a substitute.
6. The Workbench baseline stores evidence offsets as JavaScript string offsets (UTF-16 code units), whereas USG-SEM requires zero-based, end-exclusive Unicode code-point offsets. The adapter must convert offsets and reject any span that splits a surrogate pair.
7. Workbench v0.5.4 includes a native `acceptanceBoundary.requiresHumanReview` field. This is legacy application workflow metadata, not a USG-SEM semantic validity rule. It may be retained only as inert, namespaced native payload for exact archival round-trip; it must not become a required human gate in the canonical contract or Python projection.
8. The Workbench builder can discard unsupported or source-unaligned event attributes while emitting a warning. An adapter cannot recover information already discarded upstream. Such a warning must prevent a lossless source-mapping claim; the original input record/native payload must remain available if exact source round-trip is required.
9. The Python adapter converts contract annotation spans into kernel `Ann` pairs but does not retain the associated `sourceRef` in the native annotation. It detects multiple source IDs but the single source ID is also not represented by `Ann`. The current mapping report must therefore be tightened: a projected annotation is not fully reversible unless its source identity is preserved separately.
10. Python `node_to_json` serializes native expression trees, but its JSON shape (`args`, nested recursively) is not the USG-SEM graph shape (`id`, `operandRefs`). A reverse adapter must perform an explicit DAG traversal and identity assignment; it cannot pass this serialization through as canonical contract data.
11. Workbench's native semantic-model validator enforces its legacy `acceptanceBoundary.requiresHumanReview` flag. This is an immutable-baseline behavior and must not be treated as a requirement of the new canonical adapter. The adapter must keep that flag inert in namespaced archival metadata and validate semantic structure independently.

## Implementation sequence

### 4A — Workbench source adapter — completed

Implemented in `interoperability/workbench_adapter/` with a documented API, source-model mapping, native snapshot integrity digests, explicit partial statuses, Unicode offset conversion, Node tests, and JSON Schema validation in CI. See the adapter README for exact conversion behavior and known boundaries.

### 4A — Workbench source adapter — completed

Implemented in `interoperability/workbench_adapter/`. It maps Workbench v0.5.4
semantic models into USG-SEM/1.0, preserving argument/role order, operator
scope, directed connective roles, unresolved mentions, evidence, provenance,
and native payload integrity. It converts UTF-16 offsets to Unicode code-point
offsets and reports incomplete mappings as PARTIAL. See the adapter README.

### 4B — Python projection and reverse serializer — implementation added

Implemented in `interoperability/python_adapter/reverse.py` and exported as
`python_to_contract_document()`.

- Serializes current Python `Source`, `Node`, and `Assertion` projections;
  it does not return the original snapshot as a substitute.
- Traverses SemIR as a graph, preserving shared DAG identity, multiple roots,
  operator identity, sort, parameters, ordered operands, and supported annotations.
- Retains canonical-only records and unsupported original records/roots rather
  than dropping them.
- Restores annotation span source references only when offsets exactly match
  the imported canonical annotation. Changed spans without source identity are
  preserved in a namespaced extension and reported PARTIAL.
- Rejects a modified canonical envelope to prevent stale canonical-only data
  from being merged into the output.
- Reports unsupported records and fields; no guessed source association or
  constructor coercion is used.

Tests are in `tests/test_python_reverse_serializer.py` and are included in the
interoperability CI workflow. PR #5 is merged and its implementation/CI checks
passed. The broader cross-boundary semantic invariant suite remains Step 4D.

### 4C — Workbench reconstruction adapter — completed (PR #6 merged)

Implemented on `phase1/workbench-reconstruction` in
`interoperability/workbench_adapter/reconstruct.js`, exposed as
`contractToWorkbench()`.

- Reconstructs Workbench predications, operators and connectives from canonical
  graph fields, preserving argument/role order, bindings, nested scope and
  directed connective operands.
- Converts Unicode code-point spans back to UTF-16 offsets.
- Verifies both native and canonical-projection digests before restoring
  archival-only metadata.
- Never uses the native snapshot to overwrite canonical semantic fields.
- Reconstructs from changed canonical content while returning PARTIAL and
  refusing stale native restoration.
- Reports OPAQUE/unsupported constructors and canonical-only document records;
  it does not coerce or silently discard them.
- Keeps the legacy human-review field outside the reconstructed semantic model;
  if verified, it is exposed only as inert archival metadata.

The implementation has a dedicated Node test suite wired into interoperability
CI. The PR #6 CI run passed, including the new reconstruction tests and the
immutable-baseline check. PR #6 is merged into `main`.

### 4D — semantic invariant suite — completed (PR #7 merged)

Implemented initially in `tests/test_round_trip_conformance.py`, with the
Node bridge `tests/round_trip_conformance_bridge.js` executing both Workbench
adapter boundaries. The suite drives the canonical document through the Python
0.4.0 document projection and reverse serializer between those boundaries.

The first executable suite covers the following semantic invariants. It also
exercises the typed `SIT → HOLDS → PROP` boundary and exact modal force/flavor
mapping required for schema-valid operator operands:

- positive and negative predication;
- nested negation and modality scope;
- quantifier/restrictor/variable binding, including NOT(FORALL) versus NO;
- directed IF and UNLESS/EXCEPTION antecedent-consequent structure;
- WHEN and CONCESSIVE remaining distinct;
- predicate role order and conditional frame mapping;
- tense, aspect, temporal frame and adverbials;
- attribution and assertion commitment;
- mention/referent distinction and unresolved pronouns;
- evidence quote alignment and supplementary Unicode before/inside spans;
- shared DAG identity, multiple roots, and large graphs;
- unsupported constructors, metadata, and partially mapped roots;
- source builder warnings and upstream-discarded attributes;
- canonical edits invalidating stale native snapshots.

The suite compares semantic invariants, not generated opaque IDs or irrelevant serialization order. Exact source text, operand order, role binding, scope, status axes, and reference relationships are invariant.

The Python 0.4.0 kernel currently has no exact native constructors for the
Workbench adapter's `PREDICATE_APP`, `CONNECTIVE`, and some metadata-bearing
nodes. Step 4D therefore requires an explicit PARTIAL mapping report while
proving that unsupported canonical graph nodes, operands, roots, and metadata
survive the Python boundary without coercion. A separate supported-kernel
control case proves that native `RELATE` and `Assertion` projections are
actually imported and freshly serialized. This is not a LOSSLESS claim for the
entire Workbench model.

The merged suite also exercises a 512-root graph without semantic count caps.
It compares semantic invariants, not generated opaque IDs or incidental JSON
ordering. CI passed all 16 Python conformance tests, all Workbench adapter tests,
USG-SEM schema validation, and the immutable-baseline check. Step 4D is complete
as a conformance suite; the explicitly reported PARTIAL mappings remain known
runtime compatibility gaps for a future kernel/contract extension.

## Next stage — Phase 1 Step 5

Step 4 is complete. The next stage is the versioned Python-kernel compatibility extension. **Step 5A contract drafted** in [`interoperability/python-kernel-extension/STEP-5A-CONTRACT.md`](../python-kernel-extension/STEP-5A-CONTRACT.md). It formalizes the native semantics and test obligations for `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER`. Step 5A does not change kernel code; Step 5B may begin only after the contract passes automated consistency checks. The Python 0.4.0 package remains immutable.

## Status vocabulary

- `LOSSLESS`: every meaning-bearing field in the declared source scope has an exact target representation and passes round-trip invariant checks.
- `PARTIAL`: some fields/records are preserved canonically or as explicit native extension data but do not have exact target-native equivalents. All such items must be listed with paths/refs and reasons.
- `UNMAPPED`: no safe semantic mapping exists for the declared source scope. The source data remains available; no guessed conversion is emitted.

A whole-document result cannot be marked LOSSLESS merely because supported roots converted successfully while other roots or document records were omitted.

## Boundaries

- Do not modify `archives/` or `implementations/`; they are immutable baselines.
- Do not add arbitrary semantic item-count, nesting-depth, or operand-count caps.
- Do not infer mappings from lexical similarity.
- Do not silently flatten, reorder, drop, invent, or coerce semantic content.
- Do not claim open-domain semantic correctness from structural round-trip tests.
- CI must run the cross-implementation tests and verify immutable baseline paths remain unchanged.

## Acceptance criteria

Step 4 is complete only when an executable end-to-end conversion test exercises all four boundaries and verifies the listed semantic invariants. Unsupported cases must pass by being explicitly and correctly reported as partial/unmapped, not by pretending they round-trip losslessly.
