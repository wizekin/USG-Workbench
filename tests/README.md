# USG cross-implementation tests

This directory contains contract-level fixtures, adapter tests, round-trip conformance tests, and regression cases spanning implementation boundaries.

Each test must identify the contract and implementation versions it covers. Package-local tests remain with their respective implementation baselines.

## Current Phase 1 checks

Predicate/frame registry:

```bash
python -m unittest discover -s tests -p "test_predicate_frame_registry.py" -v
```

Operator/scope registry:

```bash
python -m unittest discover -s tests -p "test_operator_scope_registry.py" -v
```

Document-level Python adapter:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_document_adapter.py" -v
```

The document adapter tests verify the full USG-SEM/1.0 envelope, exact source and assertion projections where supported, shared expression-DAG identity across roots, explicit partial mapping for unsupported kernel records/constructors, Unicode code-point spans, and exact canonical-document export. The adapter does not alter the Python kernel 0.4.0 baseline or write to its SQLite store.

The predicate/frame test checks registry coverage against the Workbench predicate vocabulary and verifies target frame names, versions, inherited roles, role requirements, and class constraints against the archived Python kernel source.

The operator/scope test checks registry dispositions against Workbench operator declarations and verifies the Python kernel operator signatures, quantifier distinctions, conditional/unless scope semantics, and loss-prevention policy against both immutable source baselines.


Python reverse serializer (Phase 1 Step 4B):

```bash
python -m unittest discover -s tests -p "test_python_reverse_serializer.py" -v
```

The reverse serializer tests cover fresh serialization of current Python Source,
SemIR Node and Assertion projections; operand order; modified roots; annotation
source-reference safety; preservation of unsupported original roots; canonical
snapshot integrity; and JSON Schema validation. Canonical-only record classes
remain in the output and are explicitly listed as unmapped to kernel 0.4.0.

Workbench source adapter (Phase 1 Step 4A):

```bash
node --test tests/test_workbench_source_adapter.js
python -m unittest discover -s tests -p "test_workbench_source_adapter.py" -v
```

The source adapter tests exercise Workbench v0.5.4 semantic-model conversion, operator/connective scope, argument-role ordering, unresolved mentions, native snapshot digests, partial mapping, dangling references, and UTF-16 → Unicode code-point offset conversion. The Python test validates the actual generated document against the USG-SEM/1.0 JSON Schema.

The complete four-boundary execution test is implemented in Step 4D. The expected result is document-level PARTIAL wherever Python 0.4.0 lacks an exact native constructor or enum; those records must remain canonical and explicitly reported. This is successful conformance to the loss-preservation contract, not a claim that every Workbench semantic construction is natively executable in Python 0.4.0.


End-to-end semantic invariant conformance (Phase 1 Step 4D):

```bash
python -m unittest discover -s tests -p "test_round_trip_conformance.py" -v
```

This suite executes Workbench v0.5.4 → USG-SEM/1.0 → Python kernel 0.4.0
projection → fresh USG-SEM/1.0 serialization → Workbench reconstruction. It
compares semantic invariants rather than generated IDs or incidental JSON
ordering. It includes nested operator scope, FORALL versus EXISTS scope under
negation, directed IF/UNLESS, WHEN versus CONCESSIVE, role ordering, tense,
aspect, temporal metadata, attribution, unresolved mentions, evidence alignment
after supplementary Unicode, relation metadata, multiple roots, unsupported
canonical constructors, source-builder warnings, stale native snapshots, and a
512-root graph. A PARTIAL result is expected where Python 0.4.0 lacks an exact
constructor; the canonical graph must survive unchanged and be reported rather
than coerced.


Python kernel 0.5.0 USG-SEM graph adapter (Phase 1 Step 5C):

```bash
python -m unittest discover -s tests -p "test_python_kernel_v05_adapter.py" -v
```

This suite exercises native `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER` projections, reverse graph serialization, binder identity, OPAQUE/UNRESOLVED_REF distinctions, unknown and malformed operators, and shared DAG identity. It runs in an isolated Python process with the v0.5.0 package path; the existing v0.4.0 adapter remains unchanged.


Python kernel 0.5.0 document-level adapter (Phase 1 Step 5D):

```bash
python -m unittest discover -s tests -p "test_python_kernel_v05_document_adapter.py" -v
```

This suite verifies the full USG-SEM/1.0 document envelope around native v0.5.0
expression roots, preservation/reporting of canonical-only record families,
fresh serialization of edited native Nodes, immutable snapshot enforcement,
unreachable-expression retention, and invalid-document rejection. It does not
claim native v0.5.0 document records for sources, referents, mentions,
assertions, evidence, contexts, definitions, relations, unresolved items, or
derivations.
