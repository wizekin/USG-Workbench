# Phase 2 Step 2.4 — Rule semantics and safety contract

**Status:** Formal declarative semantics and static consistency validator implemented  
**Execution status:** Disabled; no rule matcher or inference executor is introduced  
**Parent roadmap:** [Phase 2 roadmap](PHASE-2-ROADMAP.md)  
**Rule model:** [Step 2.3](PHASE-2-STEP-2.3-RULE-MODEL-AND-REGISTRY.md)  
**Benchmark:** [Step 2.2](PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md)  
**Semantics package:** [USG Rule Semantics v1.0.0](../rules/semantic-reasoning/semantics/v1.0.0/README.md)

## 1. Purpose and boundary

Step 2.4 specifies the exact meaning of rule matching, typed binding, eligibility, constraint evaluation, scope/context preservation, conflicts, non-applicability, and failure outcomes. It is a contract for later implementation. It does not execute rules or activate the four disabled registry entries.

## 2. Applicability outcomes

The rule decision is one of nine distinct outcomes:

| Outcome | Meaning | May produce candidate? |
|---|---|---:|
| `APPLICABLE` | All required premises and constraints pass | Yes, with derivation |
| `NOT_APPLICABLE` | Valid known input fails a declared precondition | No |
| `UNKNOWN` | A required value is explicitly unknown | No |
| `UNRESOLVED` | Required identity/reference/scope cannot be resolved | No |
| `AMBIGUOUS` | Multiple materially distinct bindings remain | No |
| `CONFLICTING` | Relevant premises disagree or are DISPUTED | No |
| `UNSUPPORTED` | Rule, constructor, or operation is outside enabled scope | No |
| `INVALID_INPUT` | Profile, schema, or typed-reference integrity fails | No |
| `RESOURCE_INTERRUPTED` | Processing stops before completion | No |

These outcomes must not be collapsed. UNKNOWN remains distinct from UNRESOLVED; NOT_APPLICABLE does not mean false; missing records do not imply negation.

The precedence contract is fixed in `contract.json`: resource interruption, invalid input, unsupported operation, conflict, ambiguity, unresolved, unknown, non-applicability, and applicability. The first blocking outcome governs the rule decision while all relevant diagnostics and preserved records remain available.

## 3. Exact matching and variable binding

- Resolve the exact registry ID and rule version; no latest-version fallback.
- Resolve typed references by exact target type and ID. Versioned definitions require exact ID and version.
- A variable binds once to a value of its declared type. Every subsequent occurrence must be identical by typed identity.
- Labels, aliases, lexical similarity, and string coercion never establish identity.
- Premises are considered in declared order; required premises must all match.
- A missing matching premise is NOT_APPLICABLE, not a negative semantic fact. A dangling reference is UNRESOLVED; a wrong target type is INVALID_INPUT; multiple possible bindings are AMBIGUOUS.
- Constraints are evaluated in the declared array order. No later constraint can repair or override an earlier failed precondition.

## 4. Initial assertion eligibility policy

The Step 2.3 token `RULE_ELIGIBLE_ASSERTION` resolves to `source-asserted-premise/1.0.0` for the initial reference rules:

- `SOURCE_ASSERTED` is the only initially admitted epistemic status.
- `INFERRED` is not eligible as a premise in this rule-model version; no inferred-premise chaining occurs.
- `VERIFIED` is not implicitly admitted and is never created by rule execution.
- `DISPUTED` yields CONFLICTING.
- `UNKNOWN` yields UNKNOWN and remains recorded as such.
- Missing epistemic status or required interpretation data yields UNRESOLVED.
- The interpretation must be RESOLVED. AMBIGUOUS and UNRESOLVED interpretations keep their respective outcomes.
- Commitment and attributed referent are preserved exactly. ATTRIBUTED requires a resolvable `attributedToRef`; no cross-speaker premise combination is allowed.

USG-SEM/1.0 keeps origin, epistemic status, commitment, interpretation status, evaluation context, and lifecycle stage as separate axes. A lifecycle stage such as AUTOMATICALLY_EVALUATED or PROMOTED is not a substitute for an epistemic status or a truth certificate.

This initial policy is deliberately narrow. Expanding eligible statuses or allowing inferred-premise chaining requires a new explicit policy version and new benchmark cases; it must not happen by default.

## 5. Scope and context semantics

| Axis | Required behavior |
|---|---|
| Typed identity | Exact record type, ID, and version where applicable |
| Context | Exact contextRef equality when a rule requires same context |
| Attribution | Preserve exact commitment and attributedToRef |
| Polarity | Preserve negation and its scope |
| Modality | Preserve operator, force, and scope |
| Quantification | Preserve quantifier, variable binding, restrictor, body, and nesting |
| Temporal scope | Preserve tense, relation direction, and ordered event references |
| Roles | Preserve exact role/filler pairs and order |
| Definitions | Resolve exact identity/version; label-only match remains ambiguous |

A missing required context or attribution reference is unresolved, not defaulted to WORLD or AUTHOR.

## 6. Constraint semantics

The versioned contract defines all 19 constraint kinds in the rule-model schema, including typed identity, constructors, operator direction, status eligibility, context, attribution, polarity, modality, quantifier scope, temporal order, role order, exact definition versions, explicit closed-world requirements, and premise availability.

Each constraint has a defined meaning, failure outcome, and diagnostic code. The validator ensures every constraint kind declared by the rule model is defined here and that every registry diagnostic is present in the diagnostic catalogue.

## 7. Conflict and open-world policy

- Conflicts are preserved. No winner is selected by recency, frequency, confidence, or ordering.
- A DISPUTED premise or unresolved same-scope conflict is ineligible for the initial rules.
- OPEN is the default world assumption.
- Absence is not negation.
- Closed-world negation requires an explicit task-scoped policy, exact named domain, CLOSED declaration, established completeness for the predicate/scope, and absence within that exact snapshot.
- Closure never becomes global merely because one named domain is closed.

## 8. Determinism, provenance, and resources

Rule selection order comes from the explicit task. Premises and constraints use declared order. Candidate order is deterministic. Duplicate conclusion identity may be projected once, but every distinct derivation must be retained.

Every candidate must carry the exact input references, rule ID/version, method, output references, status, and ordered derivation links. A derivation records how a candidate was produced; it does not establish truth.

Budgets limit execution work, not semantic graph size, operands, candidate meanings, or records. Interruption occurs at safe boundaries, returns RESOURCE_INTERRUPTED/INCOMPLETE, preserves all input items and completed traces, and cannot claim completion. Semantic truncation and dropping unprocessed input are forbidden.

## 9. Validation and tests

The static validator checks:
- contract schema validity;
- all rule-model constraint kinds have definitions;
- all diagnostics used by registry rules are catalogued;
- all registry rule IDs/versions and benchmark versions match the contract;
- all premise eligibility tokens resolve to an explicit policy;
- closed-world requirements remain explicit and complete;
- execution remains disabled and all safety invariants remain false/forbidden.

Run:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_rule_semantics.py" -v
```

## 10. Step 2.4 exit criteria

- [x] Applicability and failure outcomes distinguished.
- [x] Exact typed matching and binding specified.
- [x] Initial assertion eligibility policy defined from USG-SEM/1.0 status axes.
- [x] Scope, context, attribution, polarity, modality, quantifier, temporal, and role policies defined.
- [x] All rule-model constraint kinds receive formal meanings and diagnostics.
- [x] Conflict and open-world behavior fixed.
- [x] Determinism, derivation, and resource-interruption semantics fixed.
- [x] Static consistency validation and tests added.
- [x] Rule execution remains disabled; Phase 1 compatibility is preserved.

**Next:** Step 2.5 — deterministic definition, reference, scope, and context grounding services. They must implement exact resolution without activating rule execution.
