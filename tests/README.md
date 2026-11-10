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

The complete four-boundary round trip is not yet implemented. Step 4B now serializes Python projections back to USG-SEM/1.0; Workbench reconstruction and end-to-end semantic invariant tests remain required before full conformance can pass.
