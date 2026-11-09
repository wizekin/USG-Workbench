# Operator and scope registry 1.0.0

**Registry ID:** `USG-OSR/1.0`  
**Status:** Initial evidence-backed baseline  
**Baseline pair:** Semantic Workbench 0.5.4 → Python reference kernel 0.4.0

## Purpose

This registry specifies which Workbench operators and scope structures can be represented by the Python kernel without changing their meaning. It is separate from both implementation packages and does not modify either baseline.

The registry covers negation, modal operators, quantifiers, connectives, and the conversion of graph-based scope references into nested Python expression nodes. It complements—not replaces—the predicate-to-frame registry.

## Mapping summary

| Workbench construct | Python construct | Disposition |
|---|---|---|
| Negation `NOT(P)` | `NOT(P)` | Exact |
| Unknown polarity | — | Unsupported; not negation |
| Epistemic possibility | `MODAL(POSSIBILITY, EPISTEMIC, P)` | Conditional exact; explicit force required |
| Deontic obligation | `MODAL(NECESSITY, DEONTIC, P)` | Conditional exact; explicit force required |
| `MUST`, `COULD`, `CAN`, `WOULD` | — | Partial; ambiguous readings |
| `WILL` | `TENSE(FUTURE, ...)` | Conditional exact only for explicit temporal-future reading |
| `EXPECTED` | — | Unsupported; no expectation force in Python MODAL |
| `FORALL`, `EXISTS`, counted quantifiers | `Q` | Conditional exact; requires valid restrictor and variable binding |
| `NO` | `Q(FORALL, NOT(body))` | Conditional exact; preserve Workbench's actual structure |
| `NOT(FORALL)` | `NOT(Q(FORALL,...))` | Conditional exact; outer negation scope must remain outer |
| `AND`, `OR` | `AND`, `OR` | Exact |
| `CONDITIONAL` | `COND` | Conditional exact; explicit conditional status and directed links required |
| `EXCEPTION` / unless | `COND(NOT(P), Q)` | Conditional exact only when the explicit unless interpretation and NOT antecedent are present |
| `WHEN` | — | Partial; temporal clause attachment is not the same as ordinary conditional |
| `CONCESSIVE`, `CONTRAST` | — | Unsupported |

The complete machine-readable conditions and reasons are in [v1.0.0.json](v1.0.0.json).

## Critical semantic distinctions

1. **Negation is not unknown polarity.** `POLARITY/UNKNOWN` must never become `NOT`.
2. **Modal labels do not uniquely determine modal force and flavor.** The Python kernel requires both. Conversion is allowed only when Workbench metadata explicitly resolves them.
3. **Future tense is not automatically modality.** `WILL` is treated as future tense only when its source force is explicitly `temporal_future`; volitional or hypothetical readings are not silently rewritten.
4. **Quantifier scope matters.** `NO x P(x)` and `NOT(FORALL x P(x))` are different structures. The Workbench's NO construction is universal quantification over a negated body; preserve that graph.
5. **Conditional is not material implication.** Python `COND` is the natural-language conditional operator. Do not replace it with `IMPLIES`.
6. **Unless already contains a negated antecedent.** The Workbench composer builds `NOT(P)` under the EXCEPTION connective. Do not negate it a second time.
7. **When is not automatically if.** A temporal subordinate clause requires its own temporal interpretation.

## Scope conversion requirements

Workbench operators and connectives reference children by expression IDs. Python stores scope by nested `Node.args`. A converter must therefore:

- Resolve every child reference and convert children before parents.
- Preserve nesting order, directed antecedent/consequent roles, and operand order.
- Detect missing targets, cycles, disconnected nodes, and unsupported children.
- Preserve shared references/DAG structure where the adapter supports it; otherwise report the limitation rather than duplicate or drop meaning.
- Return a partial/unsupported result if any semantically material child or scope relation cannot be represented.

No arbitrary depth or item cap is introduced.

## Evidence

- Workbench operator construction, scope graph, modal and quantifier behavior: `implementations/semantic-workbench-js/v0.5.4/semantic-core.js`
- Workbench source parsing of modal force, quantifiers, and unless: `implementations/semantic-workbench-js/v0.5.4/semantic-composer.js`
- Python operator signatures and parameter enumerations: `implementations/python-kernel/v0.4.0/usg/grammar/node.py`

Automated source-backed checks: `tests/test_operator_scope_registry.py`.

## Scope boundary

This step defines the mapping contract and verifies it against both immutable baselines. It does **not** yet implement the complete document adapter, relation mappings, or round-trip conversion. Those remain subsequent Phase 1 tasks.

## Versioning

Published registry versions are immutable. Any semantic change requires a new version, source evidence, and conformance tests.
