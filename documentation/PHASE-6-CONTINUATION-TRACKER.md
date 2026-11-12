# Phase 6 Continuation Tracker

**Tracker:** `USG-PHASE-6-CONTINUATION-TRACKER/1.0.0`  
**Bounded Phase 6 exit:** accepted for the registered Steps 6.1–6.14 scopes.  
**Continuation state:** open research and implementation queue; candidate-only boundaries remain in force.  
**Phase 7 relationship:** non-blocking. Phase 7 may proceed independently.  
**Machine-readable source of truth:** [tracker.json](../evaluations/phase6-continuation/tracker.json).  
**Automated report:** [Phase 6 Continuation Tracker workflow](../.github/workflows/phase6-continuation-tracker.yml).

---

## 1. Why this tracker exists

Phase 6 reached its bounded automatic exit for the registered synthetic profiles and integration gates. That acceptance did not complete every broader semantic construction or prove naturalistic language accuracy. Keeping all follow-up research inside the Phase 6 exit gate would make the entire USG development roadmap wait for an open-ended research queue.

This tracker separates those two facts:

- **Phase 6 bounded exit remains accepted.** Do not reopen completed acceptance steps merely because broader research continues.
- **Phase 6 continuation remains active.** New constructions and independent evaluation can be developed, measured, and merged as separate increments.
- **Phase 7 continues independently.** No tracker item blocks Phase 7 by default. A genuine technical dependency must be documented in a specific Phase 7 step rather than inferred from the phase number.

The tracker is a portfolio ledger, not a new semantic runtime, acceptance authority, or second canonical database.

## 2. What is tracked

| ID | Workstream | Initial state | Phase 7 blocking? |
|---|---|---|---|
| P6-CONT-01 | Productive coordination beyond the registered shared-argument profile | Backlog | No |
| P6-CONT-02 | Broader embedded, subordinate, relative, and argument-gap attachment | Backlog | No |
| P6-CONT-03 | Active/passive alternations and speech acts beyond passive questions | Backlog | No |
| P6-CONT-04 | Broader nested operator and quantifier scope | Candidate-only / expansion backlog | No |
| P6-CONT-05 | Discourse-reference candidate expansion and conservative resolution research | Candidate-only / expansion backlog | No |
| P6-CONT-06 | Canonical semantic-assertion projection beyond OPAQUE preservation | Open research | No |
| P6-CONT-07 | Rights-cleared naturalistic evaluation for Phase 6 constructions | Evidence backlog | No |
| P6-CONT-08 | Runtime enablement decision for each candidate construction | Gated / not promoted | No |

The detailed objectives and acceptance gates live in the machine-readable tracker. Update that file in the same PR that adds a new workstream, changes its status, or links a branch/PR. Use the stable marker (for example, `[P6-CONT-01]`) in every related pull-request title so the scheduled tracker can discover it.

## 3. Status meanings

- **backlog:** no active implementation branch/PR is recorded.
- **candidate_only:** candidate implementation exists, but the tracked expansion is not accepted for the broader target.
- **in_progress:** an implementation PR or experiment is active.
- **merged_pending_acceptance:** implementation is merged, but the declared acceptance gate is not yet demonstrated.
- **accepted:** the exact tracked scope passed its declared gates; does not generalize to untested constructions.
- **blocked:** a concrete dependency, rights issue, or missing evidence prevents progress; record the reason.
- **deferred:** intentionally paused without implying rejection.

The tracker does not auto-promote an item to `accepted` merely because a PR is merged. A merged PR, successful import, workflow completion, or synthetic self-consistency result cannot silently change the capability claim.

## 4. Automated monitoring

The dedicated GitHub Actions workflow runs daily and on manual dispatch. It:

1. validates the machine-readable tracker and its schema;
2. searches GitHub pull requests for each stable workstream marker;
3. inspects matching PR state, merge state, branch, head SHA, and available check runs;
4. generates a timestamped JSON and Markdown report;
5. uploads the report as a workflow artifact and exposes the Markdown in the workflow summary.

The monitoring workflow is deliberately separate from Phase 7 implementation and acceptance workflows. It has read-only repository permissions, does not write to `main`, does not modify runtime resources, and does not fail or block Phase 7 when a Phase 6 workstream is still open. A GitHub API lookup failure is reported as a monitoring limitation, not as a semantic failure.

The tracker manifest is the authoritative list of workstreams and their declared status. The generated report is an observation of linked GitHub activity; it does not replace the manifest or establish semantic acceptance.

## 5. Working procedure

For each Phase 6 continuation increment:

1. Select one tracker ID and keep the change bounded.
2. Create a branch and include its marker in the PR title.
3. State the construction, language profile, positive/negative/ambiguous/boundary coverage, exact-span requirements, and abstention policy.
4. Keep output candidate-only until the specific runtime enablement gate passes.
5. Add reproducible evidence and update the tracker manifest with the PR reference and status.
6. Merge only after the relevant tests and compatibility checks on the exact PR head pass.
7. Leave all unrelated tracker items open; do not reopen the bounded Phase 6 exit.

Phase 7 PRs should not be required to pass Phase 6 continuation benchmarks unless they explicitly change a Phase 6 adapter or protected behavior. Conversely, Phase 6 continuation PRs must not be required to complete Phase 7 work.

## 6. Boundaries and safeguards

- The accepted 500-case Step 6.7–6.11 synthetic suite remains evidence for its registered profiles only.
- Step 6.12 remains accepted for lossless OPAQUE preservation only; semantic-assertion projection is separate.
- Candidate graphs and lexical evidence do not become canonical assertions through tracker status changes.
- Naturalistic evidence must record source, license, retrieval date, privacy screening, population, and language limitations.
- Phase 6 output may be supplied to Phase 7 only through a versioned adapter that preserves source provenance and candidate-only state.
- The tracker does not claim full Phase 6 completion, general English/Arabic understanding, or unrestricted semantic coverage.

## 7. Links

- [Phase 6 definitions roadmap](PHASE-6-DEFINITIONS-ROADMAP.md)
- [Phase 6 automatic acceptance factory](PHASE-6-AUTOMATIC-ACCEPTANCE-FACTORY.md)
- [Phase 6 bounded automatic acceptance record](PHASE-6-BOUNDED-AUTOMATIC-ACCEPTANCE-RECORD.md)
- [Phase 7 definitions roadmap](PHASE-7-DEFINITIONS-ROADMAP.md)
- [System improvement backlog](USG-SYSTEM-IMPROVEMENT-BACKLOG.md)
- [GitHub Actions runs](https://github.com/wizekin/USG-Workbench/actions/workflows/phase6-continuation-tracker.yml)
