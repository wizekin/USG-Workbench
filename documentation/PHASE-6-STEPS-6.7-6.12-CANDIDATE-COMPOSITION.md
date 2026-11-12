# Phase 6 Steps 6.7–6.12 — Candidate Composition Framework

**Status:** IMPLEMENTED AS A CANDIDATE GRAPH-COMPOSITION CONTRACT; not benchmark-enabled and not natural-language parsing.  
**Contract:** `USG-INTERPRET/0.3.0`  
**Module:** `tools/phase6_broader_semantics_v0_1/`

## Purpose

This increment removes the need for a human annotation or external bilingual semantic dataset to develop the remaining graph operations. It provides a deterministic, source-grounded composition boundary for explicitly supplied candidate structures. It does not pretend that a rule engine can discover all of these structures from arbitrary raw text.

## Coverage

| Roadmap step | Implemented candidate operation | Safety boundary |
|---|---|---|
| 6.7 Coordination | Typed AND, OR, and CONTRAST edges between existing graph nodes; explicit source evidence | Does not invent shared arguments or duplicate participants |
| 6.8 Embedded clauses | MAIN, EMBEDDED, and SUBORDINATE clause nodes with parent links and exact spans | Rejects cycles; attachment must be supplied, not guessed |
| 6.9 Voice and speech acts | Separate ACTIVE/PASSIVE/MIDDLE/UNKNOWN and ASSERTION/QUESTION/COMMAND/REQUEST/UNKNOWN fields | Questions and commands remain distinct from assertions |
| 6.10 Scope | NEGATION, MODALITY, TENSE, ASPECT, QUANTIFIER, and CONDITION operators with explicit LOCAL/CLAUSE/EMBEDDED/UNRESOLVED scope | Missing or implicit scope is rejected; no keyword-only scope inference |
| 6.11 Discourse references | Mention-to-antecedent candidate lists and explicit unresolved status | Even a single candidate is not silently resolved as identity |
| 6.12 Projection | Loss-aware projection diagnostic against unchanged `USG-SEM/1.0` | Refuses to emit a document while any feature lacks a verified lossless mapping |

## Input contract

The caller supplies an immutable source string, language (`en` or `ar`), and a graph containing nodes, relations, clauses, operators, references, features, and provenance. Every node, clause, operator, and relation evidence span is checked against the exact original Unicode code-point slice. Every relation endpoint and operator target must exist. Clause-parent cycles are rejected. All outputs remain `CANDIDATE` / `CANDIDATE_ONLY`.

The engine is intentionally a composition/validation service, not a parser. It cannot claim raw-text extraction quality, language coverage, semantic accuracy, or benchmark acceptance for Steps 6.7–6.12.

## Projection policy

`project_loss_aware` currently returns `NOT_PROJECTABLE` and an explicit list of blockers. This is correct: the Phase 6 candidate graph carries clauses, scoped operators, discourse-reference candidates, and non-canonical semantic relations that do not yet have a proven lossless mapping to the existing `USG-SEM/1.0` schema. The adapter must not drop them or convert candidates into assertions.

## Tests

`tests/test_phase6_broader_semantics.py` exercises coordination, embedded-clause attachment, voice/speech-act separation, explicit operator scope, unresolved references, projection refusal, exact source spans, unknown relations, missing evidence, and clause-cycle rejection. These are contract tests, not a naturalistic benchmark.

## Next engineering boundary

To mark Steps 6.7–6.12 benchmark-enabled, each construction still needs deterministic raw-text candidate extraction and a separately generated reference suite with positive, negative, and ambiguous profiles per language. The graph-composition contract is the shared foundation; it is not a substitute for those evaluations.
