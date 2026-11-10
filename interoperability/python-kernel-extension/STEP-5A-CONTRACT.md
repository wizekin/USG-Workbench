# Phase 1 Step 5A — Python kernel extension semantic contract

**Status:** Design contract for review by automated conformance (implementation not started)  
**Target implementation:** A new, separately versioned Python kernel release after immutable v0.4.0  
**Interchange profile:** USG-SEM/1.0  
**Baseline source:** Workbench v0.5.4 semantic model and current USG-SEM adapters  
**Scope:** Native semantic representation of `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER`, plus the validation and serialization behavior required to use them safely.

## 1. Purpose and non-goals

Step 5A defines the semantic and type contract that a future kernel version must implement. It does not add constructors, change the USG-SEM/1.0 profile, change the current adapters, or modify either immutable implementation baseline.

The objective is not to make every interchange record fit an existing Python operator. It is to give the three currently important interchange constructions exact native representations so that later adapters can distinguish:
- native and validated semantic structures;
- source structures preserved but not yet semantically resolved;
- unsupported or ambiguous content that must remain explicit.

This step does not promise that every Workbench predicate has a registered frame, every connective has a fully formalized truth-conditional interpretation, or every quantifier can be reduced to the current `Q` constructor.

## 2. Governing invariants

All new constructors MUST obey the following:

1. **No silent semantic loss or invention.** Preserve all source meaning-bearing fields. Never invent a frame, role, referent, variable binding, restrictor, connective interpretation, or scope.
2. **No semantic coercion for convenience.** In particular, do not map an unregistered predicate to a guessed `APPLY`, an unknown connective to `AND`/`OR`, or an incomplete quantifier to `Q`.
3. **Sorts are normative.** A situation (`SIT`) is not a proposition (`PROP`). A `PREDICATE_APP` produces `SIT`; a proposition-level operator that takes a situation must use an explicit `HOLDS` boundary.
4. **Operand order and role identity are explicit.** An array position is not a substitute for a named semantic role when the construction has named roles.
5. **Variables have binding identity and scope.** Variable names are labels; binding references and binding scope determine which occurrences are bound.
6. **Unknown values remain distinct.** Unknown, unspecified, unresolved, ambiguous, withheld, and not-applicable are not interchangeable.
7. **Annotations and provenance do not silently become truth conditions.** Evidence, source claims, attribution, and derivation metadata remain separately represented.
8. **No arbitrary semantic count/depth/operand caps.** A separately declared runtime resource budget may stop processing, but must return an incomplete result with diagnostics and preserve the unprocessed input.
9. **Canonical interchange remains authoritative.** Native projection may be partial. Unsupported canonical records remain available and are reported with exact paths/reasons.
10. **v0.4.0 remains immutable.** The extension belongs in a new kernel version and must not rewrite historical packages or baseline fixtures.

## 3. Shared constructor requirements

Each constructor is an immutable typed expression node with:
- a registered operator name;
- a declared result sort;
- ordered child expression references;
- validated, constructor-specific parameters;
- annotations kept outside structural meaning/equality where the kernel architecture already requires that;
- deterministic canonical serialization;
- explicit errors for malformed arity, sort, role, or binding data.

The kernel MUST validate that the interchange `sort` agrees with the native constructor's result sort. It MUST reject extra or missing required parameters rather than silently ignore them. Optional source metadata may be retained in a separately namespaced extension or native metadata channel, but must not alter semantic equality unless a future specification explicitly says otherwise.

## 4. Constructor contract: PREDICATE_APP

### 4.1 Meaning and sort

`PREDICATE_APP` denotes a predicate applied to its role-bound arguments when no exact, versioned frame definition has been established for the application.

- Result sort: **`SIT`**.
- Each operand is an argument expression, in the same order as its corresponding role entry.
- The node describes a situation; it does not assert that the situation occurred.
- It is not an alias for Python `APPLY`.

### 4.2 Required semantic parameters

The native representation MUST preserve:

| Parameter | Contract |
|---|---|
| `predicate` | Non-empty source predicate identifier/label. It is data, not a globally unique concept or frame identity. |
| `roles` | Ordered array with exactly one role entry per operand. Each role is a non-empty role label; preserve source spelling/case in source metadata and use a separately defined canonical form only where required. |
| `argumentRequirements` | Optional structured constraints from the source; preserve unknown fields without interpreting them as satisfied constraints. |
| `argumentBindings` | Optional per-argument binding metadata, aligned to operands, including variable identity, bound referent, and mention reference when present. |
| `eventFrame` | Optional source frame description and participants/attributes. It is not a registered target frame unless registry identity and version are resolved. |
| `grammaticalTense`, `aspect`, `temporalFrame` | Preserve temporal/aspectual information. These values must not be dropped or silently promoted to independent operators without an exact mapping rule. |
| `attribution`, `provenance`, `evidenceRefs`, `completeness` | Preserve source claim, attribution, evidence, and completeness information as separate axes. |
| `nativeSourceClaimId` | Optional source-native claim identity; never use as semantic predicate identity. |

The exact Workbench adapter field names above describe the current source payload. The new kernel API may use typed records internally, but round-trip serialization MUST preserve their values and distinctions.

### 4.3 Invariants

- `len(roles) == len(operands)`; each argument remains associated with its own role.
- Multi-valued roles retain their source order and any explicit ordinal/binding identity.
- A missing role is an explicit unresolved/unknown role, not a guessed role.
- Duplicate role names are permitted only where the source semantics permit multiple values; they must remain distinguishable by ordinal/argument identity.
- A predicate label alone does not establish a frame.
- If a registered frame and version are resolved, conversion to `APPLY` is allowed only when the predicate-to-frame registry conditions, required roles, role kinds, fillers, and all material source attributes are satisfied. Otherwise retain `PREDICATE_APP`.
- A `SIT` child is not implicitly converted to `PROP`. Proposition-taking parents use `HOLDS(SIT)` where required by the target signature.

### 4.4 Operations

The new kernel version MUST support construction, validation, traversal, structural equality, deterministic serialization/deserialization, and preservation through canonicalization. Canonicalization MUST NOT reorder role-bound operands or merge distinct argument occurrences. Generic logical inference MUST NOT treat a bare `PREDICATE_APP` as an assertion.

## 5. Constructor contract: CONNECTIVE

### 5.1 Meaning and sort

`CONNECTIVE` denotes a semantic relation connecting two or more proposition-bearing operands. Result sort: **`PROP`**.

The constructor preserves the connective identity and operand-role structure. It does not assume that every connective is a Boolean conjunction/disjunction or that every binary relation is a material conditional.

### 5.2 Required semantic parameters

| Parameter | Contract |
|---|---|
| `connective` | Non-empty connective identifier (for example `AND`, `OR`, `CONDITIONAL`, `EXCEPTION`, `WHEN`, `CONCESSIVE`, `CONTRAST`). Preserve unknown identifiers. |
| `operandRoles` | Ordered array with exactly one role per operand. Directed conditionals use `antecedent` then `consequent`; other structures use explicit role names or stable `operand_n` labels only when the source has no stronger roles. |
| `marker` | Optional surface connective marker; lexical marker is not itself a semantic interpretation. |
| `logicalStatus` | Optional source classification, preserved as metadata; must not be treated as proof of truth-functional equivalence. |
| `antecedentInterpretation` | Optional explicit interpretation of the antecedent; retain distinctions such as negated antecedent. |
| `conditionMetadata` | Optional structured conditional/consequent metadata. Preserve effect, logical status, consequence interpretation, and source claim references. |
| `disjunctionSemantics` | Optional disjunction interpretation; do not infer exclusive/inclusive behavior from `OR` alone. |
| `attribution`, `evidenceRefs` | Preserve attribution and evidence independently of connective semantics. |

### 5.3 Arity and operand rules

- The constructor requires at least two operands unless a future, separately versioned connective definition explicitly defines another arity.
- `operandRoles` length MUST equal operand count.
- Role labels MUST be non-empty and unique within a single connective unless a future connective definition explicitly permits repeated role labels.
- For directed conditionals, `antecedent` and `consequent` are both required exactly once, and their operand order is normative.
- For other multi-operand connectives, the registered connective definition determines whether order is significant, whether operands are grouped, and which role pattern is legal. In the absence of such a definition, preserve order and do not apply commutative normalization.
- Every operand MUST be `PROP`. A situation-valued child requires an explicit `HOLDS` wrapper.
- A missing or unresolved operand is not replaced with a fabricated proposition; preserve it through an explicit unresolved/opaque child and report partial interpretation.

### 5.4 Semantic distinctions and normalization

- `CONDITIONAL` is not automatically `IMPLIES`.
- `EXCEPTION`/unless retains its actual antecedent polarity and scope; do not negate it twice.
- `WHEN` remains distinct from conditional/if unless a versioned temporal attachment rule establishes equivalence.
- `CONCESSIVE` and `CONTRAST` remain distinct from `AND` and `OR`.
- `AND`/`OR` may use their existing canonical rules only when the connective registry confirms the corresponding semantics and no source role/order information would be lost.
- Attribution, evidence, condition metadata, and disjunction interpretation are never erased by logical normalization.

### 5.5 Operations

The kernel MUST implement typed construction, validation, traversal, scope-aware serialization, and canonicalization. Scope extraction and any inference rule MUST consult the connective identity and role names, not infer meaning from array position alone. Unknown connective kinds remain representable but are not eligible for connective-specific inference.

## 6. Constructor contract: QUANTIFIER

### 6.1 Meaning and sort

`QUANTIFIER` denotes a quantified proposition with one proposition operand: the scoped body. Result sort: **`PROP`**.

It remains a distinct constructor from Python v0.4.0 `Q` until a validated mapping proves that the source restrictor and variable-binding model are exactly representable by `Q`.

### 6.2 Required semantic parameters

| Parameter | Contract |
|---|---|
| `operatorType` | Source operator family; preserve the source value. |
| `operator` | Non-empty quantifier/operator identifier, such as `FORALL`, `EXISTS`, `NO`, or a counted quantifier. |
| `variable` | Bound variable identifier/name where supplied. |
| `restrictor` | Optional structured restrictor descriptor including predicate and referent identity when available. Its absence is not repaired by inventing a restrictor. |
| `variableBinding` | Optional binding descriptor: variable, role, and restrictor referent identity. Must agree with actual bound occurrences. |
| `scopeKind` | Source scope classification; preserve unknown values. |
| `surfaceText`, `evidenceRefs` | Optional source surface and evidence references. |
| `attribution` | Optional attribution, preserved independently. |

The source adapter's current single operand is the scoped body. Restrictor and binding descriptors are parameters in the existing USG-SEM/1.0 interchange shape; this Step 5A contract does not silently reinterpret them as an additional operand.

### 6.3 Binding and scope invariants

- The single operand MUST be `PROP`. A `SIT` body requires explicit `HOLDS`.
- A bound variable has a stable binder identity. A display name alone is insufficient where shadowing or multiple binders can occur.
- Every bound occurrence MUST resolve to exactly one binder in the correct scope. Free variables remain free and are reported; they are not captured by proximity or name similarity.
- The binder scopes over the body and only those restrictor components explicitly declared in its binding rule. Scope boundaries MUST be defined, not inferred from traversal order.
- Restrictor predicate, restrictor referent, binding role, and variable occurrences must remain associated. A missing or conflicting link yields an unresolved/partial quantifier, not a guessed binding.
- Nested quantifiers preserve nesting order. No quantifier movement across negation, modality, attribution, or connectives is permitted as canonicalization.
- Preserve exact operator identity and any count/cardinality parameter. Do not infer `EXISTS`, `FORALL`, `NO`, or count from lexical labels alone.

### 6.4 Mapping to Q

A future adapter may map `QUANTIFIER` to `Q` only if all of the following are proven:
1. the quantifier operator has an exact target `Q.quant` and any required count `n`;
2. the restrictor can be represented as the target `Q` restrictor proposition;
3. the scoped body maps to the target `Q` scope proposition;
4. all variable occurrences and binding boundaries match the target binder semantics;
5. negation and quantifier scope are structurally identical;
6. no source metadata that affects meaning is lost.

If any condition fails, preserve native `QUANTIFIER` and report the specific mapping limitation. Do not convert an unresolved quantifier scope into a completed quantified proposition.

### 6.5 Operations

The kernel MUST implement binder-aware traversal, free-variable detection, capture-avoiding substitution, alpha-equivalence/canonicalization, deterministic serialization, and validation of binding references. Existing `Q` behavior must remain compatible. Quantifier-aware reasoning MUST operate on the explicit binder/restrictor/scope model, not string matching.

## 7. OPAQUE and unresolved behavior

`OPAQUE` and `UNRESOLVED_REF` remain distinct preservation mechanisms:
- `OPAQUE` means the construction is retained but its semantic operator is not safely interpreted.
- `UNRESOLVED_REF` means an argument/reference position is known but its referent is not resolved.

The new kernel MUST preserve these nodes and their evidence/reasons. It MUST NOT treat opaque content as an ordinary predicate, proposition, or inference premise. Resolving one requires a later explicit, versioned rule with tests.

## 8. Serialization and compatibility requirements

The future kernel release MUST:
- round-trip each new constructor without changing operator identity, sort, operand order, role bindings, variable binding, count, scope, attribution, or evidence references;
- serialize to the existing USG-SEM/1.0 graph shape (`id`, `op`, `sort`, `operandRefs`, `params`, annotations/status fields);
- preserve DAG sharing and multiple roots;
- detect missing references and cycles;
- distinguish semantic parameters from source/native extension metadata;
- report unsupported fields with node references and reasons;
- preserve v0.4.0 serialized documents and APIs under explicit compatibility tests;
- avoid returning LOSSLESS when any meaning-bearing data is canonical-only or otherwise unrepresented.

## 9. Required automated conformance matrix

| Area | Required positive cases | Required negative/adversarial cases |
|---|---|---|
| PREDICATE_APP | ordered role bindings; repeated role with distinct ordinals; unknown predicate label preserved; optional frame metadata retained; SIT/HOLDS boundary | role/operand count mismatch; empty role; guessed APPLY mapping; dropped argument; SIT relabelled PROP |
| CONNECTIVE | directed conditional roles; ordered multi-operand connective; WHEN vs CONDITIONAL; UNLESS with exactly one intended negation; CONCESSIVE/CONTRAST identity; evidence/attribution retention | role count mismatch; missing antecedent/consequent; unknown connective coerced to AND; invalid operand sort; commutative reordering without registered rule |
| QUANTIFIER | FORALL/EXISTS/count preservation; nested binders; shadowing; restrictor/body distinction; exact Q mapping where proven | free variable; conflicting binding; absent restrictor guessed; NOT(FORALL) confused with NO; quantifier moved across negation; count loss |
| Cross-cutting | serialization round-trip; shared DAG; multiple roots; canonicalization idempotence; compatibility fixture from v0.4.0 | cycles; missing refs; stale native snapshot; metadata loss; partial result incorrectly labelled LOSSLESS |
| Resource behavior | large graph completes within available resources | controlled resource stop reports incomplete work without truncation or semantic success claim |

All tests must assert meaning-bearing invariants, not generated IDs or incidental JSON property order. Include supplementary Unicode evidence spans and nested combinations across all three constructors.

## 10. Versioning and implementation boundary

- Step 5A is a design artifact only.
- Step 5B must introduce a new kernel version (version number to be selected when implementation scope and release metadata are prepared). It must not edit `implementations/python-kernel/v0.4.0/`.
- USG-SEM/1.0 remains unchanged if the new kernel can implement the existing contract exactly. If a required semantic change cannot be expressed in USG-SEM/1.0, stop and propose a separately versioned interchange-profile change; do not smuggle it into an implementation release.
- Registries remain separately versioned. Any new predicate-frame or connective mapping requires source evidence and conformance tests.
- No human-review gate is introduced.
- Node.js workflow/action versions are outside this step and remain unchanged.

## 11. Step 5A exit criteria

Step 5A is complete when:
1. the three constructor contracts are explicit and mutually consistent;
2. result sorts, operand arity/order, role semantics, quantifier binding, and Q mapping conditions are unambiguous;
3. serialization, canonicalization, validation, and compatibility obligations are testable;
4. the negative cases prevent the coercions and semantic losses identified in Step 4D;
5. the document is reviewed against the current adapter, JSON Schema, registries, and immutable v0.4.0 grammar.

Step 5A does not claim native kernel support. Once its contract and CI checks pass, Step 5B may implement it in a new kernel version.
