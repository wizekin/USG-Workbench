# Phase 3 Step 3.4 — Scope-aware rule expansion

**Status:** IMPLEMENTED — awaiting exact-PR-head CI and merge.
**Profile:** `USG-SCOPE-AWARE-RULES/1.0.0`
**Canonical input:** `USG-SEM/1.0`; no canonical schema changes.

## Supported structural subset

- **NOT:** a resolved unary NOT frame points to exactly one child expression. Nested NOT nodes remain separate linked frames; no polarity flattening or rewriting occurs.
- **IF:** a resolved binary IMPLIES frame preserves ordered antecedent and consequent references. It does not itself infer a consequent; the separately activated Phase 2 Modus Ponens rule remains responsible for eligible premise matching.
- **UNLESS:** because USG-SEM/1.0 deliberately leaves COND parameter vocabulary open, this version recognizes only COND with `params.conditionalKind = "UNLESS"` and exactly two operands. The adapter mapping is explicit: operand 0 is the consequent; operand 1 is the exception. This is a representation contract for this adapter, not a change to USG-SEM/1.0. It produces a conditional frame only; absence of the exception never entails the consequent.
- **Attribution:** assertion commitment, attributed speaker reference, context, and epistemic status are preserved as separate exact bindings. This step never transfers an attributed proposition to AUTHOR commitment.

Unknown COND mappings, malformed arities, unresolved operators, and unsupported shapes abstain with diagnostics. No natural-language parsing is claimed.

## Safety

No canonical document is mutated. No truth is promoted. No implicit closed-world assumption is introduced. Operator scope is not flattened. Inferred-premise chaining is not added. No semantic arrays or graph nodes are truncated. The analyzer does not conflate evidence alignment, semantic support, contradiction, corroboration, or external verification.

## Tests

Automated cases cover IF direction/order, nested NOT, explicit UNLESS representation, unsupported conditional mappings, attribution preservation, context/commitment separation, invalid input, determinism, and input immutability.

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase3_scope_aware_rules.py" -v
```
