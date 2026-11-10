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

Phase 1 Step 4 round-trip tests are being developed under the verified four-boundary plan in `interoperability/round-trip-conformance/README.md`. Do not label snapshot-only export as an executable round trip; the source adapter and Python reverse serializer must exist before end-to-end conformance can pass.
