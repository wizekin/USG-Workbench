# USG Semantic Workbench v0.5.0 — Full User and Technical Documentation

**Release:** 0.5.0  
**Semantic profile:** `USG-SR/0.5`  
**Architecture stage:** Milestone 1 — Semantic foundation (first implementation)  
**Runtime:** Windows + Node.js local server + optional Ollama model  
**Status:** Experimental research prototype

---

## 1. Executive overview

USG Semantic Workbench is an experimental local-first environment for transforming natural-language sentences into explicit semantic records, inspecting the proposed interpretations, accepting reviewed claims into a local knowledge base, and running a small set of symbolic inference rules.

Version 0.5.0 introduces a canonical compositional semantic graph. Earlier versions represented much of the semantic information in a list of claim objects with fields such as subject, predicate, object, polarity, tense, modality, conditions, and evidence. Those fields remain available for compatibility, but v0.5 adds a graph in which propositions, operators, and connectives refer to one another explicitly.

This makes it possible to represent structures such as:

```text
MIGHT(
  NOT(
    NEEDS(customer, tool)
  )
)
```

rather than storing “might” and “negative” as independent fields without an explicit relationship showing which has scope over which.

The Workbench is **not** a general language-understanding system. It depends on a local language model proposal or a limited deterministic English rule interpreter. The semantic core builds and validates a graph from the available proposal; it cannot independently guarantee that a model correctly understood the sentence.

### 1.1 The three central boundaries

1. **Interpretation:** Qwen, Gemma, or a local rule proposes claims from text.
2. **Representation and structural validation:** USG normalizes the proposal into `USG-SR/0.5`, verifies structural consistency, and records unsupported content.
3. **Knowledge and reasoning:** the user reviews and explicitly accepts claims; a separate, limited inference engine operates on accepted knowledge.

Structural validation does not equal semantic verification. Acceptance records a reviewed source interpretation; it does not automatically establish objective truth.

## 2. Installation and startup

### 2.1 Requirements

- Windows 10 or 11.
- Node.js 18 or newer for full local model integration.
- A modern browser.
- Ollama installed locally if LLM interpretation is required.
- A model already downloaded to Ollama, such as the user's existing Qwen or Gemma installation.

No npm package installation is required by the Workbench. The server uses Node.js built-in modules.

### 2.2 Install in a separate folder

1. Keep the previous v0.4.0 folder as a backup.
2. Extract `USG_Semantic_Workbench_v0.5.0.zip` into a new normal Windows folder.
3. Do not extract over the older version.
4. Run `launch_windows.bat`.
5. A terminal window starts the server and the browser opens at `http://127.0.0.1:8765`.
6. Keep the server terminal open while using the Workbench.

The launcher checks for Node.js. If Node.js is unavailable, it can start a static Python server fallback, but the Ollama bridge requires the Node.js server.

### 2.3 Connect Ollama

1. Start Ollama on the PC.
2. Confirm the selected model is installed.
3. Open **Local model** in the Workbench.
4. Keep the default Ollama address: `http://127.0.0.1:11434`.
5. Click **Check connection**.
6. Select the model returned by Ollama.
7. Save the settings if the interface asks you to.

The local bridge only accepts loopback Ollama destinations (`localhost`, `127.0.0.1`, or `::1`). The Workbench does not send model prompts to a cloud provider.

For meaningful version comparisons, keep the same model name/version and generation settings across runs. The current test scripts do not automatically standardize every Ollama model parameter beyond the configured request.

## 3. Main interface and workflow

### 3.1 Interpret language

This area accepts a single source sentence or text. After analysis, the Workbench displays several views.

#### Meaning

Shows the source sentence, its plain-language interpretation, candidate claims, and warnings. A readable interpretation is not proof that the semantic record is correct.

#### Structure

Shows two related views:

- **Compatibility proposition view:** the earlier subject/predicate/object representation and the associated polarity, tense, modality, quantifier, condition, and causal metadata.
- **Canonical semantic expression graph:** v0.5 entities, mentions, predications, operators, connectives, relations, root expressions, validation status, and unresolved items.

The canonical graph is the primary representation for scope-aware work in v0.5.

#### Evidence & source

Shows the original input, evidence quotes, source spans, provenance, and other review information. A quote that exactly matches the source confirms source alignment only. It does not prove that the quote entails the claim or that the claim is true.

#### JSON

Shows the structured semantic record. New v0.5 records contain:

- `schemaVersion: "0.5.0"`;
- `representationProfile: "USG-SR/0.5"`;
- the compatibility `claims` array;
- `semanticModel`;
- `semanticValidation`;
- warnings and unresolved content.

### 3.2 Review and acceptance

A candidate is not automatically added to the knowledge base.

Before accepting a candidate, inspect:

1. subject and object identities;
2. predicate identity;
3. polarity and its scope;
4. modality and its scope;
5. quantifier and variable binding;
6. grammatical tense and temporal reference;
7. embedded conditions and causal relations;
8. pronoun resolution;
9. evidence spans;
10. warnings and unresolved items.

The v0.5 UI blocks acceptance when the canonical model is structurally invalid or has partial/unresolved content. A structurally valid candidate still requires explicit user acceptance. In this first v0.5 increment, acceptance persists the reviewed compatibility claims and their claim-level relations into the existing local knowledge store; the entire canonical expression graph is not yet the knowledge store's primary persisted object. That broader graph-backed knowledge layer is Milestone 2.

## 4. Processing pipeline

```text
Source sentence
    |
    v
Local rule interpreter OR Ollama LLM proposal
    |
    v
safeModelInterpretation / source normalization
    |
    v
Compatibility claim record (v0.4-compatible fields)
    |
    v
USGSemanticCore.buildSemanticModel()
    |-- entities
    |-- mentions
    |-- evidence
    |-- predications
    |-- operators
    |-- connectives
    |-- relations
    `-- unresolved items
    |
    v
USGSemanticCore.validateSemanticModel()
    |
    v
Meaning / Structure / Evidence / JSON views
    |
    v
Human review and explicit acceptance
    |
    v
Existing knowledge base and restricted inference engine
```

The LLM does not author the canonical graph directly. It proposes a compatibility-style claim structure. `semantic-core.js` constructs the canonical graph from that normalized proposal. Therefore, v0.5 has a canonical per-interpretation representation, but the existing knowledge and inference subsystems still consume the compatibility claim projection; they have not yet been migrated to operate over the full expression graph.

## 5. Canonical semantic representation

The authoritative specification is `SEMANTIC_REPRESENTATION_SPEC_v0.5.md`. This section summarizes how the current implementation uses its objects.

### 5.1 Semantic entities

Entities are graph-local normalized referents. Example labels include `customer`, `tool`, `prices`, and `thermometer`.

An entity contains:

- `id`;
- `canonicalText`;
- `type`;
- `aliases`;
- `identityStatus`.

Automatically generated entities are provisional. Matching canonical labels may be grouped inside the current record, but this does not establish that the same word always means the same thing. The current implementation does not provide general word-sense disambiguation or cross-document identity resolution.

### 5.2 Mentions and coreference

A mention preserves the exact surface form used in the source and may point to an entity. A mention can be:

- linked to an entity;
- resolved to an antecedent entity;
- unresolved.

If the source contains “it” but the system cannot safely determine its antecedent, USG keeps an unresolved mention. It does not create an entity whose name is literally “it”.

The current discourse resolver is limited to selected patterns and is not a general coreference engine. Mention spans may be absent when the source adapter does not provide them.

### 5.3 Evidence

Evidence objects contain the source text, quote, start/end offsets, exact-source-match result, optional original model quote, and a note describing the meaning of verification.

Offsets are half-open JavaScript string offsets `[start, end)` and follow JavaScript UTF-16 string indexing. The validator checks whether the quote matches the source substring. It does not check semantic entailment.

### 5.4 PREDICATION expressions

A predication represents a predicate and its argument roles. Its current fields include:

- predicate;
- arguments;
- argument requirements and missing roles;
- grammatical tense;
- aspect;
- temporal frame;
- event frame;
- attribution;
- provenance;
- completeness;
- evidence references;
- source claim ID.

The initial built-in argument registry treats the following predicates as requiring both subject and object: `NEEDS`, `LIKE`, `DISLIKE`, `BUY`, `BOUGHT`, `PURCHASE`, `PURCHASED`, `USE`, `USES`, `USED`, `STOP_USING`, `MEASURE`, and `MEASURES`. This is a deliberately limited registry. Other predicates are not covered by a universal valency grammar.

If a known required role is missing, the proposition becomes underspecified/unresolved and a structured unresolved item is recorded. `DIFFER(prices)` can still be sentence-level interpretable without a named comparison target; a task requiring pairwise comparison may separately require that missing context.

### 5.5 Event frames

Every predication has an event/state/relation frame. It contains:

- frame ID;
- provisional kind (`event`, `state`, `relation`, `unknown`);
- predicate;
- participants;
- attributes.

Event attributes include selected items such as frequency. For example, “every day” can be represented as event frequency `P1D` rather than being appended to an object label.

Frame kind classification currently relies on a limited predicate list. It is not a general ontology or event calculus.

### 5.6 OPERATOR expressions

An operator points to the expression it modifies by `scope.targetId`.

| Operator type | Current use |
|---|---|
| `NEGATION` | `NOT` applied to a target expression. |
| `MODAL` | `MIGHT`, `MAY`, `MUST`, `SHOULD`, `CAN`, and related supported values; unknown operators become `UNKNOWN`. |
| `QUANTIFIER` | `FORALL`, `EXISTS`, `EXACTLY_ONE`, `AT_LEAST_ONE`, or `AT_MOST_ONE`, subject to a supported restrictor and variable binding. |
| `POLARITY` | Explicit unknown polarity. |
| `UNRESOLVED_SCOPE` | A recognized scope operator that cannot yet be represented safely. Its proposition remains visibly wrapped as unresolved rather than being treated as unconditional. |

Examples:

`The customer does not like the tool.`

```text
NOT
  └─ LIKE(customer, tool)
```

`The customer might not need the tool.`

```text
MIGHT
  └─ NOT
       └─ NEEDS(customer, tool)
```

`Not every customer needs the tool.`

```text
NOT
  └─ FORALL x : CUSTOMER(x)
       └─ NEEDS(x, tool)
```

`No customer needs the tool.`

```text
FORALL x : CUSTOMER(x)
  └─ NOT
       └─ NEEDS(x, tool)
```

These graph structures are not interchangeable. The quantifier variable and restrictor are linked to the corresponding argument in the predication.

The current adapter supports only selected quantifier expressions, primarily “not every” and “no”. A schema-supported quantifier such as `MOST` is not necessarily extractable from source text; when unsupported, it remains explicitly unresolved.

### 5.7 CONNECTIVE expressions

Connectives combine or relate two or more expressions.

- `CONDITIONAL`: IF antecedent and consequent.
- `EXCEPTION`: UNLESS construction.
- `WHEN`: a temporal/conditional WHEN clause, kept distinct from generic IF.
- `AND`, `OR`: coordination.
- `CONTRAST`: contrastive coordination such as BUT.

The current adapter creates structured subordinate nodes for IF, UNLESS, and WHEN when it has a valid nested proposition. Unsupported markers such as ALTHOUGH are preserved as unresolved; they are not mislabeled as simple IF conditions.

An IF or WHEN antecedent is embedded and is not promoted to an observed root fact. An UNLESS exception does not automatically invent what happens if the exception condition holds.

### 5.8 Relations and causality

A causal explanation is stored as a relation between expression roots. It retains source attribution, evidence, and `verification: not_independently_verified`.

This means the sentence says that one clause is the reason for another. It does not independently prove objective causation.

Candidate contradiction relations remain review candidates. They are not a theorem that the source statements are inconsistent in every possible context.

### 5.9 Unresolved items

Each unresolved item records an ID, source surface text, reason, status (`unresolved`, `unsupported`, or `ambiguous`), optional evidence reference, and semantic scope. Unresolved items are part of the canonical model and are displayed in the Structure view.

## 6. Semantic validation

The `semanticValidation` object reports `valid`, `status`, errors, warnings, and counts.

| Status | Meaning |
|---|---|
| `valid` | Implemented structural/reference checks passed; no unresolved items. |
| `valid_with_warnings` | Structural checks passed; warnings remain. |
| `partial` | Graph is structurally valid but contains unresolved/unsupported material. |
| `invalid` | Structural or reference checks failed. |
| `unavailable` | Semantic core was not loaded. |

The current validator checks:

- profile and version;
- unique entity, mention, evidence, expression, and unresolved-item IDs;
- entity, mention, evidence, expression, root, and relation references;
- source quote offsets and exact substring matching;
- subject argument or explicit unresolved pronoun mention;
- known predicate argument requirements;
- event frame participants;
- quantifier restrictor, variable binding, and predicate argument binding;
- supported operator and connective values;
- operator/connective scope targets;
- expression graph cycles;
- required human review and non-truth boundary.

It does not prove source entailment, calibrate model confidence, verify the truth of the content, or resolve all linguistic ambiguities.

## 7. Knowledge base and inference engine

The existing accepted-claim store, derived-claim store, patterns, and claim relations remain in place. User acceptance is explicit. The current inference engine retains the narrow earlier rules:

- `R-IS-A-TRANSITIVE`;
- `R-INSTANCE-INHERITANCE`.

Those rules operate on a restricted class of accepted claims and do not yet reason generally over the full v0.5 expression graph. They should not be described as broad natural-language reasoning.

The accepted knowledge base stores the compatibility claim data and accepted provenance; v0.5 is not yet a full knowledge-graph store. Building a richer concept graph and graph-native reasoning are later milestones.

## 8. Batch evaluation

### 8.1 Run a batch

1. Connect Qwen or Gemma through Ollama.
2. Open the batch runner in **Interpret language**.
3. Put one sentence on each line (up to 100).
4. Run sequentially.
5. Export the JSON after completion.

The batch result records the model, URL, timestamps, source sentence, engine, status, normalized semantic record, canonical graph, warnings, and errors.

### 8.2 Batch statuses

- `completed`: no unresolved/partial semantic content was reported.
- `partial`: at least one valid semantic part exists, but some information is incomplete or unsupported.
- `unresolved`: no usable claim could be represented.
- `fallback_after_error`: the local model request failed and fallback handling was used.

These are processing/representation statuses, not model accuracy scores.

Batch export uses schema `1.3` and `semanticSchemaVersion: 0.5.0`.

### 8.3 Evaluation discipline

For Qwen/Gemma comparisons:

- use the same v0.5 build;
- use the same exact sentences;
- keep Ollama model version and generation settings fixed within each comparison;
- do not edit JSON results manually;
- send the raw exports for evaluation;
- distinguish model errors, source-normalization corrections, semantic-core structural outcomes, and unresolved items.

## 9. Local API and runtime

The Node server binds to loopback and exposes the health/model/interpretation APIs used by the UI. The health route is:

`GET http://127.0.0.1:8765/api/health`

Expected v0.5 response includes version `0.5.0`.

The Ollama address remains the configured loopback address, normally `http://127.0.0.1:11434`. The server rejects remote destinations; it is not a public inference gateway.

## 10. Data storage and privacy

- The Workbench uses browser local storage for the existing local workspace data.
- Data is local to the browser profile and is not encrypted by this application.
- Clearing browser data can remove local workspace state.
- Export regular backups before upgrades or manual cleanup.
- The local model adapter sends source text and a limited context list to Ollama running on the same PC.
- No cloud LLM provider is configured by this release.

## 11. Testing and verification

Run:

```bat
node --check app.js
node --check server.js
node --check semantic-core.js
node tests\semantic_foundation_test.js
node tests\smoke_test.js
```

Or execute `tests\run_all_tests.bat`. To validate the Draft 2020-12 JSON Schemas and representative fixtures as well, install the optional Python package and run:

```bat
python -m pip install jsonschema
python tests\validate_schemas.py
```

The deterministic tests verify code behavior on fixtures. They do not invoke a live Ollama model. JSON Schemas can be checked with a Draft 2020-12 compatible validator; the build process tested both schemas and representative semantic model fixtures.

## 12. Known limitations and unimplemented work

- English-focused narrow extraction, not a general semantic parser.
- Limited coreference and no robust discourse-level entity tracking.
- Entities are provisional and graph-local; no cross-document identity service.
- Limited predicate valency list; no full semantic role labeling.
- No comprehensive treatment of concessive, relative, reported speech, nested attitude, or arbitrary subordinate clauses.
- Scope is explicitly represented after normalization, but current source extraction does not disambiguate every possible operator order.
- Limited quantifier extraction despite the wider representational vocabulary.
- No independent semantic-entailment verifier.
- No full temporal logic, event calculus, or reasoning over arbitrary expression graphs.
- No full knowledge graph or autonomous knowledge construction.
- No controlled autonomous learning or rule induction.
- No calibrated confidence scores or broad human-labelled benchmark.

## 13. Milestone 1 completion status

v0.5.0 implements the first canonical semantic foundation: compositional graph nodes, scoped operators, connectives, unresolved items, argument requirements, reference validation, and migration compatibility.

Milestone 1 is **not yet certified complete**. The remaining acceptance work is to run live Qwen/Gemma tests on the user's PC, build a human-labelled unseen-sentence benchmark, measure performance by semantic category, and close remaining scope/coverage gaps without regressing the deterministic suite.

## 14. Package contents

See `README.md` for the file inventory. The primary implementation files are:

- `app.js` — UI, source normalization, LLM proposal adapter, batch runner, knowledge/inference workflow.
- `semantic-core.js` — canonical graph construction and structural validation.
- `MILESTONE_1_STATUS.md` — explicit milestone implementation status and exit requirements.
- `server.js` — local-only server and Ollama bridge.
- `schemas/` — v0.5 record and canonical-model schemas plus historical v0.4 schema.
- `tests/` — smoke/regression and semantic foundation tests.
