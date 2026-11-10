# Phase 3 Step 3.8 — Packaging and one-command demo

**Status:** IMPLEMENTED — awaiting exact-PR-head CI and merge.
**Package:** `usg-workbench-local==0.1.0`.
**Canonical storage:** SQLite.
**Canonical profile:** USG-SEM/1.0.

## Install

From the repository source:

```bash
python -m pip install -r requirements-phase3.lock
python -m pip install .
```

The wheel includes the Phase 3 tools, schemas, declarative rules, frozen benchmark fixtures, the v0.7.0 Mention model adapter dependency, Kernel Lab assets, and runnable sample documents.

## One-command browser demo

```bash
usg-workbench lab --db ./usg-workbench.sqlite3
```

Open `http://127.0.0.1:8765`. The lab binds only to loopback. To use the HTTP API without the browser UI:

```bash
usg-workbench serve --db ./usg-workbench.sqlite3
```

Other CLI commands include validate, store, get, check, conditions, contradictions, query, export, and revisions. Use `usg-workbench --help` for the complete command list.

## Included sample

- `examples/phase3/sample-usg-sem-1.0.json` — complete canonical document.
- `examples/phase3/sample-query.json` — structured query with an explicit rule allowlist.
- `examples/phase3/README.md` — guided local demo.

The example produces a `DERIVED_NOT_VERIFIED` candidate; it does not establish objective truth and does not interpret raw text.

## Reproducible release manifest

`scripts/build_release_manifest.py` generates `release/phase3-release-manifest.json` with sorted file paths, byte sizes, and SHA-256 hashes. The manifest excludes itself, contains no generation timestamp, and is deterministic for an unchanged source tree. Runtime and build dependencies have separate exact-version lock files:

- `requirements-phase3.lock`
- `requirements-build.lock`

CI builds both wheel and source distribution, installs the wheel into a fresh virtual environment, verifies the installed entry point and packaged sample document, and uploads the distributions plus generated manifest as a build artifact.

## Scope

This is a local Python package and demo, not a public hosted service or production/security certification. It introduces no cloud dependencies, paid APIs, raw-text parser, schema mutation, truth promotion, implicit closed-world assumption, or semantic truncation.
