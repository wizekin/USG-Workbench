# USG Semantic Workbench v0.5.4 — Architecture

## 1. Overview

v0.5.3 preserves the v0.5.1 semantic representation and adds a generation-correction control loop around model proposals. The system separates model interpretation, proposal diagnosis, same-model second-pass review, targeted repair, source-grounded composition, canonical graph construction, and structural validation. It remains a research prototype with a finite English clause grammar.

```text
Source text
   ↓
Local Ollama model proposal (optional)
   ↓
Source-grounded semantic composer (semantic-composer.js)
   ├─ Parse independently supported clause frames
   ├─ Attach scoped negation / modality / quantification
   ├─ Compose IF / UNLESS / WHEN / ALTHOUGH
   ├─ Compose BUT / OR / AND
   ├─ Represent BECAUSE as source-attributed causal relation
   └─ Resolve limited discourse references
   ↓
Compatibility claims + composition metadata
   ↓
Canonical semantic graph (semantic-core.js)
   ├─ Entities / mentions / evidence
   ├─ PREDICATION / OPERATOR / CONNECTIVE nodes
   ├─ Typed relations and unresolved items
   └─ Structural/reference validation
   ↓
Inspection UI and human review
   ↓
Existing accepted-claim knowledge base / limited inference
```

## 2. Components

### Browser interface and application adapter (`index.html`, `styles.css`, `app.js`)
- Captures source input and displays Meaning, Structure, Evidence, and JSON views.
- Supports deterministic local interpretation and optional Ollama model proposals.
- Runs the source-grounded composer before canonicalization when the complete source matches its supported grammar.
- Preserves the original model proposal summary and its warnings for comparison.
- Keeps the `claims` compatibility projection and existing workspace format.
- Removes empty quantifier placeholders and non-source-grounded event attributes.
- Preserves unresolved content when the source composer declines an unsupported input.

### Source-grounded composer (`semantic-composer.js`)
- Dependency-free browser/Node module, version `0.2.0`.
- Uses a reusable clause-frame parser separate from the predicate vocabulary.
- Supports selected simple clause frames, negation, modal operators, `not every`/`no`, and selected event attributes.
- Composes selected leading/trailing IF, UNLESS, WHEN, ALTHOUGH, BECAUSE; top-level BUT/OR/AND; and limited multi-sentence discourse.
- Retains independent tense per clause and limited coreference.
- Returns `null` when a required clause or argument cannot be safely represented; it does not mark an incomplete frame as a complete parse.
- It is a finite grammar, not unrestricted natural-language parsing. One principal connective per source input is the current reliable coverage target; arbitrary nested attachment is not claimed.

### Canonical semantic core (`semantic-core.js`)
- Builds graph-local provisional entities, occurrence-level mentions, and evidence nodes.
- Converts claims into `PREDICATION` nodes.
- Wraps propositions using explicit negation, modality, quantifier, unknown polarity, or unresolved-scope `OPERATOR` nodes.
- Builds `CONNECTIVE` nodes for IF/UNLESS/WHEN/ALTHOUGH and coordination.
- Interprets `UNLESS P, Q` with a NOT operator over P while retaining the EXCEPTION marker.
- Preserves source-attributed CAUSE edges as not independently verified.
- Validates graph identity/reference, scopes, quantifier bindings, known argument roles, evidence spans, cycles, and acceptance boundaries.

### Local bridge and generation correction (`server.js`, `generation-correction.js`)
- Uses Node built-in modules only.
- Serves on loopback and restricts Ollama destinations to local addresses.
- Prompts models to produce clause-separated claims, explicit operators/connectives, source-grounded attributes, and `EXPECTED` for epistemic expectation.
- Adds deterministic diagnosis of proposal shape, evidence alignment, duplicates, references, and condition structure.
- Runs a second-pass review using the same selected model, then sends targeted repair feedback when the checks find correctable defects. The second pass is not an independent model or proof.
- Retries output-token resource boundaries with adaptive budgets; these do not cap the number of semantic items. A still-truncated response is rejected, not silently accepted.
- Retains the full raw proposal for audit when the compatibility projection cannot express nested content.
- Does not create cloud inference dependency.
- Uses a configurable `USG_MODEL_TIMEOUT_MS` request deadline (default 180,000 ms; bounded from 1,000 to 600,000 ms). The health endpoint reports the effective timeout.

## 3. Semantic distinctions

- A source proposition is attributed to the source voice; objective truth remains unestablished.
- Evidence quote alignment is not entailment verification.
- `IF` and `WHEN` antecedents are not promoted to observed facts.
- `UNLESS` normalizes its exception condition to an explicit negated antecedent while retaining the original marker.
- `ALTHOUGH` relates two propositions as concessive, without implying causation.
- `BECAUSE` records the speaker's causal claim and is not independently verified.
- `OR` remains inclusive-or-unspecified.
- `EXPECTED` is epistemic expectation, not automatically deontic obligation.

## 4. Storage and roadmap boundary

Accepted knowledge still uses the legacy claim store and claim-level relations. The full canonical expression graph is inspectable/exportable but is not yet the primary persisted knowledge graph. Reasoning still does not operate generally over all nested semantic expressions. Those are later milestone deliverables.


## 5. v0.5.2 runtime configuration

`USG_MODEL_TIMEOUT_MS` controls the maximum duration of an Ollama HTTP request, including response-body reading. Invalid or out-of-range values fall back to 180,000 ms. Kaggle evaluation configures 300,000 ms to reduce avoidable timeout fallbacks observed in the v0.5.1 live run. The health endpoint reports both the Workbench release and effective timeout. The semantic schema and canonical graph profile remain at v0.5.1 for compatibility.


## 6. v0.5.3 generation-correction boundary

The model proposal passes through `generate → diagnose → second-pass review → targeted repair → recheck`. The app adapter no longer truncates claim, condition, event-attribute, or unresolved-item arrays by fixed count. The same selected model performs the reviewer pass, so it can share the generator's blind spots. `modelGenerationAudit` records stage metrics, findings, and repair status. The loop does not change model weights and is not fine-tuning; it is an inference-time feedback and validation protocol.


## 7. v0.5.4 diagnostics and consistency boundary

The Ollama adapter classifies response and transport failures separately. Each failed generation/review/repair attempt remains represented in `generationArtifacts`; successful raw responses, JSON parse outcomes, partial output-limit text, HTTP error bodies, and timeout/transport diagnostics are retained where available. `responseReceived:false` explicitly distinguishes failures that occurred before an HTTP response was obtained. Repetition-limit aborts are not conflated with output-token-length stops.

Condition compatibility metadata is marker-specific: IF is conditional, UNLESS is exceptional, and WHEN is temporal. The semantic graph retains the original connective marker, validates the normalized NOT antecedent for EXCEPTION, and checks that condition metadata agrees with the canonical connective. CONCESSIVE nodes preserve evidence references for both clauses. Derived contradiction relations are projected into both compatibility and canonical relation lists.

These checks improve diagnosability and internal consistency; they do not prove semantic entailment or correctness. No semantic element-count caps are introduced.
