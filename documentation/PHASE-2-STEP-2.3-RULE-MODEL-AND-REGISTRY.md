# Phase 2 Step 2.3 — Rule model and registry

**Status:** Declarative model and registry contract implemented; entries remain disabled  
**Runtime status:** No rule loader, matcher, or inference executor is introduced  
**Parent roadmap:** [Phase 2 roadmap](PHASE-2-ROADMAP.md)  
**Definitions:** [Step 2.1](PHASE-2-STEP-2.1-SEMANTIC-REASONING-DEFINITIONS.md)  
**Benchmark:** [Step 2.2](PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md)  
**Registry package:** [USG Semantic Rule Registry v1.0.0](../rules/semantic-reasoning/v1.0.0/README.md)

## 1. Purpose

Step 2.3 defines a separately versioned rule model and registry format. It does not implement rule matching or execution. The rule data must be validated and auditable before Step 2.4 specifies exact execution semantics and Step 2.6 introduces an executor.

The registry is intentionally non-executable: `execution_enabled=false`, and every rule is marked `SPECIFIED_NOT_EXECUTABLE`. The later executor cannot treat a registry record as active merely because it is schema-valid.

## 2. Version and compatibility boundary

- Rule model: `USG-RULE/1.0.0`
- Registry: `USG-SEMANTIC-RULE-REGISTRY/1.0.0`
- Input profile: `USG-SEM/1.0`
- Benchmark contract: `USG-SEMANTIC-REASONING/1.0.0`

Rules remain in an additive package outside the canonical USG-SEM/1.0 document. This avoids silently adding a Rule record family or typed rule-reference space to the Phase 1 profile. Existing Evidence and Derivation rule IDs remain opaque unless an exact registry identity/version is explicitly referenced by a Phase 2 execution contract.

## 3. Rule record requirements

Every rule includes:
1. Stable opaque `rule_id` and explicit semantic version.
2. Purpose, category, and description.
3. Declared typed variables with requiredness.
4. Ordered, typed premise patterns and explicit field bindings.
5. Machine-readable constraints, parameters, and failure diagnostics.
6. Explicit context, attribution, polarity, modality, quantifier, temporal, role-order, and world-assumption policies.
7. One or more conclusion-candidate templates.
8. Task assumptions and closed-domain policy requirements.
9. Non-applicability conditions and diagnostic codes.
10. Positive and negative/boundary/adversarial benchmark references.
11. Deterministic matching/order, duplicate conclusion, cycle, interruption, and preservation semantics.
12. Compatibility declarations for USG profile, rule model, registry, benchmark, and adapter.

### 3.1 Typed variables and premises

A variable declares its value type; a reference cannot be rebound as a different record type by label or lexical similarity. Premise order is explicit. Each premise has a stable local ID, a requiredness flag, a record type, variable bindings, and fixed fields.

Constraints are declarative data. This version validates their shape and required diagnostics but does not interpret or execute them.

### 3.2 Scope and context

The rule explicitly declares its behavior for exact context identity, attribution, polarity, modality, quantifier scope, temporal scope, role order, and world assumptions. A rule may not omit a relevant axis and rely on an undocumented default. This model version records exact policies; the execution meaning and conflict/non-applicability behavior are specified in Step 2.4.

### 3.3 Conclusion effect

A template creates only a `conclusion_candidate` and carries `epistemic_effect=DERIVED_NOT_VERIFIED` with `truth_promotion=false`. It cannot promote source assertions to VERIFIED, CORROBORATED, or objective truth. Derivation provenance is mandatory in the template contract.

### 3.4 Closed-world rules

A closed-world rule must declare `EXPLICIT_CLOSED_COMPLETE_ONLY`, require a task-scoped policy reference, and include independent constraints for domain closure, domain completeness, and absence within that exact domain. The registry itself does not make any domain closed. Open-world absence remains non-negating.

### 3.5 Resource and determinism

The declared execution profile requires deterministic premise order and exact typed matching without coercion. Resource interruption returns an INCOMPLETE result and preserves all input items. Semantic truncation is forbidden; there is no semantic item, operand, or graph-size cap in this rule model.

## 4. Initial declarative rule set

The v1.0.0 registry includes four disabled reference rules:
- modus ponens;
- left conjunction elimination;
- explicit complete closed-domain negation;
- preservation of the directed BEFORE relation.

Each rule links to positive and negative/boundary fixtures in the Step 2.2 corpus. The registry is a model/contract artifact, not an inference engine or proof that these rules have been executed.

## 5. Validation and CI

The JSON Schema uses Draft 2020-12 with closed object shapes for the registry and rule fields. The Python registry validator additionally checks cross-record invariants that JSON Schema alone cannot express:

- unique rule IDs and versions;
- all fixture references exist in the exact v1.0.0 corpus;
- each rule has positive and negative/boundary coverage;
- all field/template variable references are declared;
- every benchmark reference-policy rule ID/version exists in the registry;
- closed-world rules require a task policy, closed domain, complete domain, and scoped absence;
- all rules remain disabled, deterministic, exact-match/no-coercion, and non-truth-promoting.

Run:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_rule_registry.py" -v
```

## 6. Step 2.3 exit criteria

- [x] Versioned typed rule model and strict schema defined.
- [x] Registry format and disabled reference rules created.
- [x] Premises, constraints, scope/context, conclusions, assumptions, diagnostics, and test metadata represented.
- [x] Rule references tied to benchmark fixtures.
- [x] Closed-world, truth-promotion, determinism, and resource safeguards machine-validated.
- [x] Focused unit tests and CI workflow added.
- [x] USG-SEM/1.0 and all Phase 1 baselines left unchanged.

**Next:** Step 2.4 — formal rule semantics and safety contract. It must specify how each declared constraint and failure outcome is interpreted before any rule can be executed.
