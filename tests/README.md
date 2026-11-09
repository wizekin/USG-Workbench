# USG cross-implementation tests

This directory contains contract-level fixtures, adapter tests, round-trip conformance tests, and regression cases spanning implementation boundaries.

Each test must identify the contract and implementation versions it covers. Package-local tests remain with their respective implementation baselines.

## Current Phase 1 checks

Run the source-backed predicate/frame registry checks from the repository root:

```bash
python -m unittest discover -s tests -p "test_predicate_frame_registry.py" -v
```

The test checks registry coverage against the Workbench predicate vocabulary and verifies target frame names, versions, inherited roles, role requirements, and class constraints against the archived Python kernel source.
