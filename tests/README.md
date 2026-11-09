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

The predicate/frame test checks registry coverage against the Workbench predicate vocabulary and verifies target frame names, versions, inherited roles, role requirements, and class constraints against the archived Python kernel source.

The operator/scope test checks registry dispositions against Workbench operator declarations and verifies the Python kernel operator signatures, quantifier distinctions, conditional/unless scope semantics, and loss-prevention policy against both immutable source baselines.
