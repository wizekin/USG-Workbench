# USG Semantic Workbench v0.5.1 — Full documentation

## 1. Purpose

USG Semantic Workbench is a local-first research prototype exploring explicit semantic representation. A language model may propose a structured interpretation; the Workbench normalizes supported information, composes selected clauses, builds a canonical semantic graph, validates graph structure, and presents the candidate for human review.

The system deliberately distinguishes:

1. **Model proposal:** the model's own interpretation.
2. **Source-grounded composition:** a finite deterministic grammar's analysis of supported wording and clause structure.
3. **Canonical representation:** the normalized graph of concepts, propositions, operators, connectives, events, evidence, and unresolved information.
4. **Validation:** structural/reference checks, not proof that the graph is entailed by the source.
5. **Knowledge acceptance:** a separate human decision; source assertions are not thereby made objectively true.

This is not a general-purpose semantic parser, a general theorem prover, an independent semantic verifier, or an AGI system.

## 2. v0.5.1 release summary

The first v0.5.0 batch revealed that empty quantifier placeholders could become spurious unresolved-scope expressions, placeholder event attributes could leak into normalized data, and complex clause composition was unreliable. v0.5.1 corrects these defects and adds `semantic-composer.js`.

The source composer parses clause frames separately and composes selected IF, UNLESS, WHEN, ALTHOUGH, BECAUSE, BUT, OR, AND, and short multi-sentence discourse constructions. It retains a finite predicate vocabulary and declines incomplete/unsupported forms. The original LLM proposal summary remains available when a source-grounded parse is selected.

## 3. Installation on Windows

Requirements:

- Windows 10/11.
- Node.js 18 or newer for the full local HTTP/Ollama bridge.
- A modern browser.
- Ollama installed locally and a model downloaded if LLM proposals are needed.

No npm packages are required by the Workbench.

Steps:

1. Extract the ZIP into a new folder. Do not overwrite v0.5.0 or v0.4.0.
2. Double-click `launch_windows.bat`.
3. Keep the server terminal open.
4. Open or let the launcher open `http://127.0.0.1:8765`.
5. In **Local model**, check the Ollama connection and select an installed model.

`open_directly.bat` starts only a static UI fallback. Local LLM bridge functionality requires the Node server.

## 4. Application architecture

### 4.1 `app.js`

The application owns the UI workflow, interpretation adapter, source normalizations, compatibility claim representation, evidence/provenance metadata, workspace persistence, batch testing, and existing knowledge/inference views.

When the source composer covers the entire input:

- its claim frames become the normalized compatibility claims;
- `compositionAudit` identifies the parser/version and records that it was used;
- `modelProposalSummary` retains the original model proposal fields, unresolved items, and warnings;
- the canonical semantic graph is built from the normalized claims and composition metadata.

When the source composer cannot cover all clauses and required arguments, it returns no parse. The regular model/normalization path remains in use and unresolved material must remain visible.

### 4.2 `semantic-composer.js`

Version `0.2.0`, dependency-free UMD module. It parses a finite lexicon of clause frames and applies composition rules independently of the specific sentence text. This allows additional supported predicates to reuse the same connective logic.

Current verb frames include selected forms of NEED, LIKE, DISLIKE, WANT, USE, STOP USING, BUY/PURCHASE/ACQUIRE, INCREASE, DECREASE, REDUCE, FAIL, SELL, PRODUCE, RECEIVE, BREAK, START, CLOSE, and MEASURE, plus copular DIFFER.

Current guaranteed source composition is one main connective construction per input, selected leading/trailing subordinate forms, and short multi-sentence discourse. Arbitrary nested/multiple connectives, relative clauses, reported speech, complex passive constructions, broad ambiguity, and unrestricted coreference are not guaranteed. The grammar is intentionally conservative.

### 4.3 `semantic-core.js`

The canonical graph builder creates:

- entity nodes with provisional graph-local identifiers;
- occurrence-level mention nodes;
- evidence spans and offsets;
- `PREDICATION` nodes with arguments, temporal frames, event frames, provenance, attribution, completeness, and evidence references;
- `OPERATOR` nodes for negation, modality, quantification, unknown polarity, and unresolved scope;
- `CONNECTIVE` nodes for supported conditional/exception/when/concessive/coordination structures;
- typed relations such as source-attributed CAUSE;
- structured unresolved items and graph root identifiers.

The validator checks references, IDs, scopes, supported operators/connectives, cycles, argument requirements, quantifier bindings, evidence span alignment, and acceptance boundaries.

### 4.4 `server.js`

The Node bridge serves the app locally and forwards model requests to loopback Ollama only. It does not introduce cloud inference. The model prompt asks for separate clauses, explicit scope, source-grounded event attributes, and an EXPECTED operator for epistemic expectation.

## 5. Semantic composition rules

### 5.1 Atomic proposition

`The customer needs the tool` is represented as `NEEDS(customer, tool)`.

### 5.2 Negation

`The customer does not dislike the tool` is represented as `NOT(DISLIKE(customer, tool))`. It is not converted into `LIKE`.

### 5.3 Modal scope

`The customer might not need the tool` is represented as:

```text
MIGHT
  └── NOT
      └── NEEDS(customer, tool)
```

### 5.4 Quantifier scope

`Not every customer needs the tool` is represented as `NOT(FORALL x: CUSTOMER(x) -> NEEDS(x, tool))`.

`No customer needs the tool` is represented as `FORALL x: CUSTOMER(x) -> NOT(NEEDS(x, tool))`.

The first does not imply that no customer needs the tool.

### 5.5 Conditional

`If prices increase, the customer will stop using the tool` contains an embedded antecedent and a future consequent. The antecedent is not stored as an observed fact. Each clause keeps its own tense.

### 5.6 Unless

`Unless prices increase, the customer does not need the tool` is represented using an EXCEPTION connective. The exception condition is explicitly wrapped in NOT, corresponding to `IF NOT(INCREASE(prices)) THEN NOT(NEEDS(customer, tool))` in the standard simple unless reading. The original marker remains visible.

### 5.7 When

WHEN is a distinct connective, not automatically rewritten as IF. The source antecedent is embedded; this release does not fully disambiguate all habitual, temporal, and conditional readings.

### 5.8 Although

ALTHOUGH retains both propositions and relates them with CONCESSIVE. It does not automatically create a causal relation.

### 5.9 Because

BECAUSE produces cause/effect propositions and a CAUSE relation with `attribution.kind=source_asserted` and `verification=not_independently_verified`.

### 5.10 Coordination

BUT creates a contrastive connective; OR creates inclusive-or-unspecified disjunction unless exclusive meaning is supplied; AND creates conjunction. Clause propositions are not collapsed into one object phrase.

### 5.11 Discourse references and frequency

The composer has narrow source-grounded HE/SHE/THEY and IT/THEM resolution for selected discourse patterns. Frequency phrases such as `every day` are attached to event frames, not merged into object labels.

### 5.12 EXPECTED

`The customer is expected to need the tool` uses EXPECTED with epistemic expectation force. It is not interpreted as a deontic obligation.

### 5.13 Difference

`Prices were different` remains a sentence-level proposition even when the comparison target is absent. The missing target can matter for pairwise comparison tasks but does not automatically make the sentence uninterpretable.

## 6. Evidence, confidence, and acceptance

An exact evidence span means that the quoted substring is present at the stored offsets. It does not prove the proposition follows from that text. Confidence fields are not calibrated probabilities. All candidates require human review before knowledge acceptance. `accepted` means reviewed and admitted into the application's knowledge store, not independently proven true.

## 7. Batch testing

The batch runner accepts one sentence per line. v0.5.1 exports schema 1.3 and includes `workbenchVersion`, `semanticSchemaVersion`, raw model response, normalized record, canonical semantic graph, validation, warnings, engine, and processing status.

For model comparisons:

- use the same 14 benchmark sentences exactly;
- run Qwen and Gemma separately;
- keep model versions and settings fixed;
- do not edit exported JSON;
- inspect raw model output, proposal summary, normalized claims, canonical graph, and validation separately;
- treat timeouts/fallbacks separately from model output quality.

Processing status such as `completed` is not a semantic accuracy score.

## 8. Automated verification

Run `tests\\run_all_tests.bat`. It includes syntax checks, semantic foundation tests, composition tests, app integration tests, and the existing smoke/regression suite. Optional schema checks use `python tests\\validate_schemas.py` with `jsonschema` installed.

The v0.5.1 build verification passed 332 JavaScript assertions and 10 schema checks. It also passed a local HTTP health/static-asset check. These tests do not invoke live Ollama inference.

## 9. Known limitations and next milestones

Milestone 1 is still open pending live Qwen/Gemma testing and an independently human-labelled unseen-sentence benchmark. The current grammar does not cover arbitrary nested connectives, all verb valencies, relative clauses, reported speech, full voice alternations, unrestricted discourse coreference, word-sense disambiguation, or ambiguity resolution.

The accepted knowledge store still persists the legacy claim projection rather than the full graph as a graph-native database. Existing inference is limited and does not reason generally over all nested operators, conditions, quantifiers, or temporal/event frames. Independent semantic verification and controlled learning are future milestones.
