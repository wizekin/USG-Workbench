# USG bounded repair executor v0.1.0

The executor applies only reviewed, machine-readable repair plans using exact, single-occurrence text replacements in a small allowlist. It is intentionally not an AI coding agent and never executes commands supplied by a plan.

## Safety boundary

- A plan must use `USG-BOUNDED-REPAIR-PLAN/0.1.0`, be committed under `automation/repair-plans/`, have status `ready`, and name a base commit that is an ancestor of the checked-out commit.
- Each target file is pinned by its Git blob SHA-1. A stale target, symlink, path traversal, duplicate match, secret-like replacement, or protected path is rejected.
- Maximum five files, 64 KB of patch text, 256 KB per file, 1 MB total changed bytes, and five minutes of registered tests.
- Plans cannot supply shell commands, Python modules, URLs to fetch, arbitrary file paths, or merge instructions. Validation profiles map to fixed test command lists in code.
- Runtime semantic/syntax/operator/discourse implementations, lexical resources, active resources, gold directories, canonical USG-SEM/1.0 specifications, and accepted Phase 1–5 contracts are outside the allowlist.
- A failed test restores every patched file. The result records hashes, test outcomes, and rollback status.
- The workflow can open a PR after successful tests, but it never merges. Repository Actions PR permissions may prevent automatic PR creation; the artifact and branch are preserved and the failure is reported.
- Candidate resources and semantic gold are never promoted or modified by this executor.

## v0.1 scope

Supported patch scopes: deterministic CI, reporting/diagnostics, packaging metadata, and regression-fixture directories. CI test edits are limited to registered evidence, Open-World, PUD, and executor tests; accepted Phase 4/5 semantic tests are excluded. The initial implementation supports exact text replacement only; it does not create/delete files or regenerate arbitrary package contents. A future template must be separately registered and tested before it is available to plans.

## Plan format

See `specifications/usg-bounded-repair-plan-0.1.0.schema.json`. Each plan contains a fixed validation profile and evidence links. The plan file itself must already be present on main, so the normal repository review process approves the proposed repair before the scheduled executor can apply it.

## Invocation

```bash
python -m tools.usg_repair_executor_v0_1_0.executor \
  --plan automation/repair-plans/REPAIR_ID.json \
  --repo-root . \
  --current-commit "$(git rev-parse HEAD)" \
  --result /tmp/repair-result.json \
  --apply
```

Without `--apply`, the executor validates and previews the plan without writing files or running tests.
