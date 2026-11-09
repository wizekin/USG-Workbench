# USG Semantic Workbench v0.5.1 — Change report

## Why this release exists

The first v0.5.0 live batch exposed defects that were not just model mistakes: empty quantifier metadata was incorrectly turned into unresolved quantifier scope, placeholder event metadata could leak into normalized records, and clause/connective extraction was unreliable for several sentence classes.

## Code changes

### 1. Normalization corrections
- Empty/placeholder quantifier objects are treated as absent.
- A meaningful but unsupported quantifier is still preserved as unresolved.
- Event attributes are restricted to supported types and must be grounded in the source text.
- Placeholder values and placeholder normalized values are rejected.
- The original model proposal and its warnings are retained separately when a complete source-composition parse replaces it as the normalized candidate.

### 2. Reusable semantic composition
- Added `semantic-composer.js` (version 0.2.0).
- Clause parsing is separate from connective composition and predicate vocabulary.
- Supported constructions include IF, UNLESS, WHEN, ALTHOUGH, BECAUSE, BUT, OR, AND, and short discourse sequences.
- Leading and trailing forms are supported for the main subordinate markers.
- Nested negation/modality, clause-local tense, selected quantifiers, pronoun resolution, and event frequency are represented explicitly.
- `UNLESS P, Q` explicitly scopes NOT over P while keeping the EXCEPTION marker.
- Unsupported/incomplete patterns return no deterministic parse rather than fabricating a proposition.

### 3. Canonical semantic graph corrections
- EXPECTED is a registered modal operator.
- CONCESSIVE is validated as a directed connective.
- Resolved pronouns retain their surface mention type and antecedent entity link.
- Expanded predicate frame registry covers the new supported lexicon.
- Normalized event attributes reject placeholders before being attached to event frames.

### 4. Prompt and interface
- Ollama prompt asks for clause-separated propositions, correct connectives, source-grounded attributes, and EXPECTED rather than MUST for epistemic expectation.
- UI script order loads `semantic-composer.js` before semantic core and app.
- Batch exports report Workbench and semantic schema version 0.5.1.

## Verification

- 332 JavaScript assertions passed across foundation, composition, application integration, and existing smoke/regression tests.
- 10 JSON Schema/meta-schema and fixture checks passed.
- Local server health endpoint returned version 0.5.1.
- Root page and key static assets returned HTTP 200.

No live Qwen/Gemma Ollama inference was performed in the build environment. User-side live testing remains required.

## Remaining known limits

This is not a general English semantic parser. It has a finite predicate/valency lexicon, limited coreference, and currently covers one main connective construction per source input plus selected short discourse. Arbitrary nested connectives, reported speech, relative clauses, passive alternations, polysemy, and broad ambiguity require future work. Milestone 1 remains open pending blind, human-labelled accuracy evaluation.
