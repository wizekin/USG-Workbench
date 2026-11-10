# Phase 2 Step 2.5 — Deterministic definition, reference, scope, and context grounding

**Status:** Deterministic grounding services and tests implemented  
**Execution status:** No rule matching or inference is introduced  
**Parent roadmap:** [Phase 2 roadmap](PHASE-2-ROADMAP.md)  
**Semantics contract:** [Step 2.4](PHASE-2-STEP-2.4-RULE-SEMANTICS-AND-SAFETY-CONTRACT.md)  
**Package:** [USG Grounding Services v1.0.0](../tools/semantic_grounding_v1_0_0/README.md)

## 1. Purpose

Step 2.5 implements Layer B (semantic grounding) as deterministic, independently testable services over canonical USG-SEM/1.0 documents. The service resolves only explicit references and structural scope. It does not infer identity, choose definitions by label, create missing contexts, or execute rules.

## 2. Resolution result contract

Each result carries:
- a distinct status (`RESOLVED`, `UNRESOLVED`, `AMBIGUOUS`, `CONFLICTING`, `UNKNOWN`, `UNSUPPORTED`, or `INVALID_INPUT`);
- expected record type and exact target ID, when available;
- candidate references without selecting one;
- diagnostic codes;
- provenance identifying the exact document/profile snapshot and resolver version.

A resolver never returns a successful result for a different record type or a label-only match.

## 3. Services

### 3.1 Typed reference resolution

`resolve_reference(expected_type, reference_id)` looks only in the declared collection. If the ID exists only under another collection, the result is INVALID_INPUT with a typed-reference mismatch diagnostic. A missing ID is UNRESOLVED. Duplicate IDs within the expected collection are INVALID_INPUT.

### 3.2 Definition grounding

Concepts and frames carry positive integer record-level versions in USG-SEM/1.0. They resolve only when both opaque ID and requested version match exactly.

Roles and relations do not carry record-level versions in the canonical schema. To obtain versioned grounding for those families, the caller must supply an exact catalogue scope and version (`ONTOLOGY`/ontologyRelease or `GRAMMAR`/grammarVersion). The resolver does not invent a per-record version.

Label lookup is discovery-only. Zero candidates is UNRESOLVED; multiple candidates is AMBIGUOUS; one candidate remains UNRESOLVED with `DEFINITION_LABEL_IS_NOT_IDENTITY` until the exact ID/version is supplied.

### 3.3 Mention and referent identity

A Mention is distinct from a Referent. The resolver follows only explicit `referentRef` when the Mention status is LINKED or RESOLVED. It does not use surface text, aliases, concept labels, or antecedent guesses. Explicit AMBIGUOUS, UNRESOLVED, UNKNOWN, and DISPUTED referent states remain distinct.

### 3.4 Context grounding

An assertion's `evaluationContext.contextRef` must resolve to an exact Context record and its kind must agree. A missing contextRef is UNRESOLVED even when the kind says WORLD. Parent context links are followed exactly; cycles are INVALID_INPUT. Resolving a context hierarchy does not authorize assertion propagation to parent contexts.

### 3.5 Expression scope grounding

`resolve_scope(root, target)` traverses `operandRefs` in declared order and returns the complete ordered operator path with exact parent IDs, operator names, operand indexes/counts, and unchanged params. If a shared subexpression has multiple paths, the result is AMBIGUOUS. Cycles are INVALID_INPUT. Opaque scope paths are UNSUPPORTED. No operator, quantifier, polarity, or temporal structure is flattened or rewritten.

## 4. Step 2.2 compact-fixture compatibility gate

The frozen Step 2.2 v1.0.0 corpus stores compact evaluator snapshots, not complete canonical USG-SEM/1.0 envelopes. The `inspect_compact_benchmark_snapshot` bridge preserves the original payload and lists canonical fields that are missing. It reports PARTIAL and `canonical_document_ready=false` when required canonical fields are absent.

In particular, an omitted `epistemicStatus` is never defaulted to SOURCE_ASSERTED. The bridge does not fabricate sources, context records, expression sorts, assertion origins, commitments, or lifecycle stages. It does not pretend that the compact snapshot is a schema-valid document. A later benchmark extension may add complete canonical documents with explicit synthetic source and assertion declarations; the frozen v1.0.0 corpus remains unchanged.

## 5. Compatibility and safety

- USG-SEM/1.0 and its schema are read-only inputs.
- Phase 1 native models, adapters, registries, archives, and immutable baselines are not modified.
- No global identity, label matching, implicit context, implicit WORLD default, silent coercion, or automatic truth promotion.
- No semantic-size or operand caps.
- No human-review gate.
- Rule registry remains disabled; these services do not execute rules.

## 6. Validation

The focused suite covers exact typed references, wrong target types, missing references, exact definition versions, unversioned role/relation catalogue scope, label-only ambiguity, duplicate IDs, mention identity, UNKNOWN/UNRESOLVED/DISPUTED distinctions, context parent paths and cycles, missing context references, nested operator paths, shared-scope ambiguity, opaque paths, expression cycles, schema-invalid documents, and compact-fixture preservation.

Run:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_grounding.py" -v
```

## 7. Step 2.5 exit criteria

- [x] Exact typed reference resolution implemented.
- [x] Definition ID/version grounding implemented for every canonical definition family.
- [x] Mention-to-referent resolution follows only explicit links.
- [x] Context references and parent paths resolve exactly with cycle detection.
- [x] Expression scope paths preserve operand/operator order and expose multiple paths as ambiguous.
- [x] Compact benchmark snapshots are safely preserved and blocked from false canonical conversion.
- [x] Focused tests and CI workflow added.
- [x] Phase 1 compatibility and immutable baselines preserved.

**Next:** Step 2.6 — deterministic inference executor. It must consume these resolver results, only run explicitly enabled rules, and use a separately versioned benchmark fixture extension with complete canonical documents where required fields are explicit.
