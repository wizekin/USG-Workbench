# Phase 1 Step 5E — native Source record integration

**Status:** implementation candidate; automated conformance pending  
**Kernel:** Python 0.5.0  
**Interchange:** USG-SEM/1.0 (unchanged)  
**Predecessor:** Step 5D document-level expression integration

## Objective

Extend the Step 5D whole-document boundary with exact native projections for USG-SEM source records. Sources are the first non-expression document record family integrated into the v0.5.0 document boundary.

This step does not attempt to map referents or mentions. Their identity and metadata semantics require separate exact contracts.

## Native projection

The adapter projects a source only when its source type, trust tier, and sensitivity values are all represented by the corresponding v0.5.0 enums. It maps:

- exact source text and SHA-256 text hash;
- language;
- source type, trust tier, and sensitivity;
- URI;
- optional document date, time zone, calendar, and speech time anchor;
- a typed `IdSpace.SOURCE` reference.

USG-SEM IDs are opaque. The adapter creates a deterministic, document-local mapping from source IDs to typed kernel `Ref` values. It does not parse IDs or infer identity from labels.

## Partial and unknown values

USG-SEM permits `UNKNOWN` for source type, trust tier, and sensitivity, while the current v0.5.0 enums do not. Missing optional enum values are also not guessed. A source containing an unsupported or absent enum value remains canonical-only and is listed in `recordMapping.sources.unmappedRefs`. No value is coerced to a different enum or replaced by a default.

The complete original source record remains in the canonical envelope. The document mapping status remains PARTIAL when any source is canonical-only.

## Reverse serialization

The document boundary serializes the current native `Source` records on export, including recomputed SHA-256 hashes after text edits. Sources that could not be projected remain unchanged in the canonical envelope. Source IDs remain the original opaque document IDs through the explicit per-document mapping.

Source edits do not rewrite mentions, evidence, or other records. The normal full-document validator checks span bounds and quote alignment after export; a source edit that invalidates dependent spans is rejected rather than silently adjusting them.

## Explicit non-goals

- No native Referent or Mention projection in Step 5E.
- No inference from referent labels, aliases, or identity strings.
- No cross-document referent merging.
- No source trust promotion or change in security policy.
- No schema changes, semantic caps, silent coercions, or human-review gate.
- No changes to v0.4.0, Workbench v0.5.4, archives, historical baselines, or Node.js workflow/action versions.

## Conformance

The document adapter suite covers exact source projection, typed identity, round-trip serialization, native source text edits and hash recomputation, unknown enum preservation, and all Step 5D document/graph invariants. The full v0.5.0 kernel and immutable baseline suites remain required.
