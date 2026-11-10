# Semantic kernel correction: exact semantic-kind validation

Date: 2026-11-07  
Scope: targeted correction to Milestone 1, Step 3 (semantic kernel)

## Defect

The expression grammar has five broad sorts. Several distinct semantic kinds
share one sort:

- `EVENT`, `PROCESS`, and `STATE` share `SIT`.
- `VALUE` and `QUANTITY` share `VAL`.

The typechecker previously mapped a role's `expected_kind` to a broad sort and
stopped there. As a result, it accepted a `STATE` expression in an `EVENT` role,
a `PROCESS` expression in an `EVENT` role, and a `QUANTITY` in a `VALUE` role.
This contradicted the exact kind requirement in Specification Part 3 §3.3.2,
which defines kind mismatch as `INCOMPATIBLE`.

## Correction

`usg/grammar/typecheck.py` now performs two separate checks for a role filler:

1. **Sort compatibility** remains the broad grammar check. It still rejects
   category errors such as a proposition supplied where a situation is required.
2. **Exact semantic-kind compatibility** derives the expression's kind and
   compares it with `RoleSpec.expected_kind`.

The exact-kind derivation uses:

- `APPLY`: the frame's declared `situation_kind` (`EVENT`, `STATE`, or
  `PROCESS`).
- `ASPECT`: the kind of the underlying situation.
- `COMPOSE`: `PROCESS`, as defined in Specification Part 3 §3.18.
- `KIND`: the referenced ontology concept's kind.
- `VALUE` and `LIT`: `VALUE` and `QUANTITY` respectively, with non-quantity
  literals treated as `VALUE`.
- `REF`, `VAR`, and `REIFY`: `ENTITY`, consistent with the `TERM` grammar.
- Temporal constructors: `TIME`.
- Propositional constructors: `PROPOSITION`.
- `ALT`: each alternative is checked independently; all branches must satisfy
  the role's exact kind.

A known mismatch produces `SG-TYP-001`. A mismatch inside a registered
figurative literal is retained as `W-FIGURATIVE`, following the existing
figurative-validation path. Where the current grammar cannot determine one
kind, validation records `W-TYPE-UNDETERMINED` instead of inventing a kind.

The existing five-sort grammar and canonical serialization are unchanged.

`KIND` references to definition kinds are also rejected at the role boundary,
using the existing `can_fill_role` rule from the semantic-kind model.

## Regression coverage

New tests in `tests/test_typecheck.py` cover:

- `EVENT` versus `STATE` within `SIT`.
- `EVENT` versus `PROCESS` within `SIT`.
- `COMPOSE` as a `PROCESS`.
- `VALUE` versus `QUANTITY` within `VAL`.
- `PROPERTY` versus `VALUE`, where `PROPERTY` has no direct entry in
  `KIND_TO_SORT`.
- Every branch of a mixed-kind `ALT`.
- Figurative literal handling for an exact-kind mismatch.

## Remaining specification issue

Part 4 uses `situation_kind=SYSTEM` for structural frames, but Part 2's fixed
`SemKind` vocabulary has no `SYSTEM` kind and Part 3's `SIT` sort lists only
`EVENT`, `STATE`, and `PROCESS`. The checker therefore does not guess that a
`SYSTEM` frame is one of those kinds; its kind remains undetermined when used
as a role filler. This inconsistency needs an explicit specification decision
before introducing a new semantic kind or changing the sort system.

## Verification in this package

- Targeted typechecker tests: passed.
- Full project suite using the project's documented command
  (`python -m unittest discover -s tests -t .`): 436 tests passed.
- Full release acceptance (`python -m usg acceptance --full`): passed, all 13
  checks; 49-case constructed benchmark passed.
- No model calls were made.

The release acceptance and constructed benchmark establish covered behavior
and implementation consistency only; they do not establish open-domain natural
language accuracy.
