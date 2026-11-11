# Phase 5 Lexical Foundation v0.5.0 — Productive English Stem Transformations

## Purpose

Extend the v0.4.0 composite lexical foundation with explicit, auditable spelling transformations for a small set of common English inflection patterns. The Phase 5 runtime now uses `usg-en-ar-composite-lexicon@0.5.0`.

## Resource contents

- Existing cumulative English/MSA Arabic discourse resource `usg-en-ar-discourse-lexicon@0.3.0`.
- English starter resource `usg-en-core-starter-lexicon@0.5.0`: 170 entries and 14 morphology rules.
- Composite resource `usg-en-ar-composite-lexicon@0.5.0`.

The v0.4.0 resource file remains preserved as a historical version. The active resource catalogue points to v0.5.0.

## Explicit stem operations

Every morphology rule declares one of four operations:

| Operation | Transformation | Example |
|---|---|---|
| IDENTITY | Strip the registered affix | atom + s → atoms |
| Y_TO_I | Restore final y after stripping ies/ed | stud + y → study |
| RESTORE_E | Restore final e after stripping ing/ed | mak + e → make |
| UNDOUBLE_FINAL | Remove one duplicated final consonant | runn → run |

The resource includes rules for:
- Regular plural and third-person forms ending in `-ies`.
- Present participles/gerunds ending in `-ing` after silent-e deletion or consonant doubling.
- Past-tense forms ending in `-ed` after silent-e deletion, consonant doubling, or y-to-i spelling.

These transformations are only applied when the transformed stem exists as a lexical entry with the required part of speech. The analyzer does not invent an unregistered lemma.

## Decision behavior

- Exact surface lookup remains first.
- Morphology is attempted only when exact lookup finds no entry.
- Each generated candidate records the exact rule ID.
- Multiple senses remain ambiguous.
- Unknown stems remain unresolved.
- A transformation that does not satisfy its structural condition is rejected.

The implementation deliberately does not claim coverage for irregular forms such as `went → go`, broad derivational morphology, all English orthographic alternations, or Arabic non-concatenative morphology.

## Validation

The v0.5.0 workflow validates the resource against the extended JSON schema, compiles the package, runs the lexical foundation tests, runs Phase 5 API and packaging regressions, and runs the full 100-case Phase 5 interpretation benchmark.

The morphology regression set includes surface forms not explicitly stored as entries: `studies`, `cities`, `making`, `running`, `planned`, `loved`, and `studied`. These validate the listed transformations; they are controlled test fixtures, not a representative sample of all English.

## Scope boundary

This release improves selected inflectional coverage. It does not establish high lexical coverage, contextual POS disambiguation, complete morphology, arbitrary-document semantic composition, or open-world generalization. The separate Phase 6 UD PUD experiment remains the relevant external held-out morphology research track; its modest results do not justify promoting its candidate rules wholesale into the runtime.
