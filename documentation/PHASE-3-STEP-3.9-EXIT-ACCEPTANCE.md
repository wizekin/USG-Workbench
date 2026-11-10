# Phase 3 Step 3.9 — Integrated exit acceptance

**Status:** IMPLEMENTED — awaiting exact-PR-head acceptance and merge.
**Acceptance profile:** `USG-PHASE3-EXIT-ACCEPTANCE/1.0.0`.
**Canonical storage:** SQLite.

## Acceptance runner

Run from the repository root:

```bash
python -m pip install -r requirements-phase3.lock
PYTHONPATH=tests:implementations/python-kernel/v0.5.0 python -m tools.phase3_exit_acceptance_v1_0_0.run --report phase3-exit-acceptance-report.json
```

The runner reports independent required check groups:
1. canonical SQLite store and revision-pinned query;
2. scope-aware rules and condition/contradiction services;
3. local API and Kernel Lab integration;
4. package and release-manifest behavior;
5. Phase 1 compatibility;
6. Phase 2 compatibility.

Every check must pass. Missing tests, skipped required tests, failures, or errors block acceptance. The report contains check-level counts and failure details; there is no weighted score or aggregate score that can conceal a critical failure.

## Integrated CI gate

The dedicated workflow runs the acceptance runner on the exact PR head, runs the frozen JavaScript/Phase 1 checks, builds the wheel and source distribution, generates the deterministic SHA-256 release manifest, installs the wheel into a clean virtual environment, and launches both the standalone API and browser Kernel Lab against one shared SQLite file.

The final smoke test stores the packaged sample through the API, reads it through the Kernel Lab endpoint, checks integrity, runs the structured sample query, inspects conditions and contradictions, and confirms the revision and digest are shared across both interfaces.

## Acceptance invariants

- USG-SEM/1.0 remains unchanged and authoritative.
- SQLite is the only canonical persistence backend.
- Canonical snapshots and revision history remain complete and immutable.
- No truth promotion, implicit closed-world assumption, exception-absence inference, conflict winner selection, evidence-axis collapse, operator-scope flattening, or semantic truncation.
- No human-review dependency, public network binding, cloud dependency, or paid API.
- Unsupported raw-text interpretation remains explicitly unsupported.

## Scope of a pass

A pass establishes that the enumerated Phase 1, Phase 2, Phase 3, packaging, and local integration acceptance checks passed on the tested source revision. It does not establish unrestricted natural-language understanding, world-truth determination, distributed execution, multilingual coverage, or production/security certification.
