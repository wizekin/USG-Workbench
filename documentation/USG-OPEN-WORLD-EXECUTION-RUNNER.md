# OW-3 — Isolated execution runner

**Status:** OW-3 implementation  
**Runner:** USG Open-World Execution Runner 1.0.0  
**Protocol:** OW-1 execution-result schema 1.0.0

## Purpose

OW-3 executes one scenario per fresh Python child process using fixed, repository-owned adapters. The parent runner validates each input against the OW-1 scenario protocol, enforces a wall-clock timeout, captures stdout/stderr, computes output digests, maps the target's declared completion status to a distinct execution outcome, validates the resulting execution record, and writes append-only JSONL results.

## Implemented target adapters

- **Phase 4 v0.1.0:** actual `InterpretationService.interpret(text, language)` Python API; emits the actual USG-SEM/1.0 document projection.
- **Phase 5 v0.2.0:** actual `Phase5InterpretationService.interpret(text, language, resource_manifest_digest=...)` Python API. OW-3 computes the digest from a fresh in-memory SQLite catalogue populated with the same bundled resource descriptors, matching the real Phase 5 resource-catalogue boundary. Phase 5 output remains USG-INTERPRET/0.2.0; it is not promoted to a USG-SEM document.
- **JavaScript Semantic Workbench v0.5.4:** registered, but currently returns `not_executed` because OW-3 does not yet include a browser automation adapter. This is not counted as a USG failure.

## Isolation and safety properties

- A fresh `python -m tools.open_world_evaluation.worker` child process handles each case. No shell is used; scenario text is JSON input data, never executable code.
- Each child receives an allowlisted environment. Repository credentials and cloud tokens are not forwarded.
- The child runs from a private temporary working directory. Python user-site loading is disabled.
- Per-case wall-clock timeout is enforced by the parent. The child also applies CPU, address-space, file-size, and open-file limits where the platform exposes Python's `resource` module.
- Scenario `network_access` must be false. The worker blocks Python socket connection entry points before loading a target adapter.
- The Phase 5 resource digest is computed with a fresh in-memory SQLite catalogue; no persistent user database is opened or modified.
- Each output line is validated against the OW-1 execution-result schema. Existing output files are never overwritten.

## Important security boundary

This is a **process-isolated evaluation worker**, not a hardened hostile-code sandbox. It does not provide a kernel network namespace, seccomp policy, Windows Job Object, filesystem chroot, container boundary, or protection against every possible native-extension escape. The fixed adapter map and data-only input remove the need to execute generated text, but the runner should still be used only with repository-owned code in the current implementation. OW-3 disables network use at the Python socket layer and records this as best-effort containment; hardened OS/container isolation remains future work before executing untrusted target binaries or plugins.

## Outcome mapping

The target's own status is kept separate from infrastructure failures:

- COMPLETE / COMPLETED → `completed`
- UNSUPPORTED → `unsupported`
- AMBIGUOUS → `ambiguous`
- PARTIAL / INCOMPLETE / INCOMPLETE_RESOURCE_LIMIT → `partial`
- malformed/unknown output → `invalid_output`
- parent deadline exceeded → `timeout`
- unexpected worker termination → `crashed`
- child could not start → `infrastructure_error`
- deliberately unimplemented target adapter → `not_executed`

Mixed language hints are mapped to a supported Phase 4/5 language profile only when necessary; the requested hint, selected profile, and mapping decision are stored with the captured result. This is not evidence of bilingual code-switching support.

## Usage

Generate cases:

    python -m tools.open_world_evaluation.generate_scenarios --count 100 --seed "ow3-smoke" --output evaluations/ow3-cases.jsonl

Execute them against the pinned repository commit:

    python -m tools.open_world_evaluation.execute_cases --input evaluations/ow3-cases.jsonl --output evaluations/ow3-results.jsonl --commit-sha <40-character-commit-sha> --max-wall-seconds 60

The output is one OW-1 execution-result JSON object per attempted case. A run summary is printed to stdout. The output is append-only by convention: the CLI refuses an existing output path; interrupted runs leave their already-written records intact and require a new output path for a continuation.

## JavaScript Semantic Workbench browser target (SYS-04)

The registered `js-semantic-workbench-v054` target now uses
`tools/open_world_evaluation/browser_adapter.py`. The adapter starts the
Workbench's own Node bridge on a dynamically selected loopback port, launches
headless Chromium through Playwright, opens the actual browser UI, enters the
scenario text, invokes **Analyze sentence**, and captures the resulting
candidate interpretation JSON.

The adapter currently supports the Workbench's English interpreter only.
Non-English scenarios are recorded as `unsupported`, not silently translated
or sent to another implementation. It uses the deterministic local rule
fallback; no Ollama model is required or used.

Browser requests are restricted to loopback hosts by Playwright routing.
Service workers are disabled and Chromium background networking is disabled.
The Node bridge itself binds only to `127.0.0.1`; its model URL validator also
rejects non-loopback Ollama destinations. The worker grants browser scenarios
a 45-second wall limit and 2 GiB address-space budget. The stable target result
projection removes generated claim IDs and timestamps but preserves semantic
fields, evidence spans, unresolved items, warnings, and source text.

The adapter is tested in a real Chromium process by
`.github/workflows/open-world-browser-adapter.yml`. The full OW-6 target
matrix installs the same browser runtime before executing cases. A browser
execution pass establishes that the UI path ran and returned a structured
candidate; it does not establish semantic correctness or broad language
coverage.

## Deterministic replay of recorded cases (SYS-14)

Use the replay utility to re-run recorded cases at the exact commit that produced their original execution records:

    python -m tools.open_world_evaluation.replay_cases \
      --cases evaluations/<campaign>/scenarios.jsonl \
      --results evaluations/<campaign>/execution-results.jsonl \
      --output evaluations/replays/<unique-replay-name>.json \
      --commit-sha <40-character-tested-commit-sha> \
      --max-cases 25

The current Git checkout must exactly match --commit-sha. The utility refuses to label a replay with a commit that is not checked out. Original execution-result records must also identify that same commit. This means historical replay requires checking out the original tested commit first; replaying old cases against current main is a new experiment, not a deterministic replay.

The tool validates input records, skips not_executed records, replays a bounded number of actual attempts, and writes a new report without overwriting an existing report. Each entry compares the original and replay outcomes plus a canonical digest of the target_result projection.

The target-specific policy is in tools/open_world_evaluation/replay_stability_profiles.json. Only explicitly listed volatile fields are excluded (currently Phase 4 document.documentId and document.createdAt). The Phase 4 policy also canonicalizes exact source-ID references that are generated anew for each invocation; it does not remove source text, spans, expressions, or semantic content. Every other target_result field, including pipeline and resource versions, remains part of the comparison. Unknown targets and pipeline-version mismatches are marked not_comparable rather than guessed. A mismatch is reported distinctly as an outcome mismatch or target-result mismatch, with differing JSON paths included for target-result mismatches.

An exact match establishes repeatability only for the selected case, implementation commit, and resource versions. It does not establish semantic correctness. Replay reports are append-only evidence and should be retained beside the campaign they reproduce.

## OW-3 acceptance boundary

OW-3 provides actual child-process execution for Phase 4 and Phase 5, a clearly recorded not-executed result for the browser-only target, time/resource limits, hashes, and schema-valid execution records. It does not yet provide the browser adapter, append-only campaign storage, an adaptive scheduler, a full hostile-code sandbox, or scored large-scale simulations.
