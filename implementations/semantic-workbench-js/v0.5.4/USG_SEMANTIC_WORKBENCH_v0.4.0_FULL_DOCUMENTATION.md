# USG Semantic Workbench v0.4.0 — Full Technical and User Documentation

**Release:** 0.4.0  
**Semantic profile:** `USG-SR/0.4`  
**Application type:** Local-first browser workbench with optional local Ollama integration  
**Status:** Experimental research prototype  

---

## 1. Purpose and scope

USG Semantic Workbench is an experimental environment for converting English text into explicit, inspectable semantic records, reviewing those records, storing accepted claims in a small knowledge base, and applying a deliberately limited set of symbolic inference rules.

Its central design principle is separation of responsibilities:

1. A deterministic local interpreter or an optional local language model proposes an interpretation.
2. The USG semantic layer normalizes the proposal into the v0.4 representation.
3. Validation and evidence checks identify malformed, incomplete, or unsupported parts.
4. A person reviews the candidate and explicitly accepts or discards it.
5. Accepted claims may be used by the small symbolic inference engine, subject to strict eligibility filters.

The workbench is **not** a general-purpose language-understanding system, complete ontology, autonomous learner, consciousness system, or AGI. A structurally valid record can still be semantically wrong. Human review remains required.

## 2. What is included in v0.4.0

The release contains:

| File | Responsibility |
|---|---|
| `index.html` | Application structure and all workbench views/dialogs |
| `styles.css` | Layout, visual styling, responsive presentation |
| `app.js` | Browser-side application state, interpretation, normalization, rendering, storage, knowledge base, patterns, inference, batch runner, import/export |
| `server.js` | Local HTTP server and optional Ollama API bridge |
| `launch_windows.bat` | Windows launcher for the local server and browser |
| `open_directly.bat` | Opens the static UI fallback; does not provide the model bridge |
| `SEMANTIC_REPRESENTATION_SPEC_v0.4.md` | Normative semantic record specification |
| `schemas/usg-semantic-record-v0.4.schema.json` | JSON Schema Draft 2020-12 contract for semantic records |
| `SEMANTIC_SCHEMA.md` | Short schema overview |
| `ARCHITECTURE.md` | Architecture summary |
| `TEST_PLAN.md` | Manual and automated acceptance-test plan |
| `TEST_RESULTS.md` | Recorded release verification results |
| `tests/smoke_test.js` | Automated regression and behavior assertions |
| `tests/fixtures/qwen_batch_v0_3_2.json` | Historical Qwen fixture used for regression replay |

The project uses Node.js built-in modules only. No npm package installation is required for the workbench itself.

## 3. System architecture

### 3.1 High-level processing flow

```text
User enters English text
        |
        v
Choose interpretation engine
  |                         |
  |                         +--> Local Ollama model proposes JSON
  |                              (optional; runs on this PC)
  |
  +--> Deterministic local rule interpreter
        |
        v
USG semantic normalization and enrichment
        |
        v
Evidence alignment, structural checks,
source-cue reconciliation, unresolved reporting
        |
        v
Candidate semantic record
        |
        +--> Inspect Meaning / Structure / Evidence / JSON
        |
        +--> Discard
        |
        +--> Explicit human acceptance
                    |
                    v
             Local knowledge base
                    |
          +---------+----------+
          |                    |
          v                    v
    Pattern discovery    Symbolic reasoning
          |                    |
          v                    v
 Candidate/accepted       Derived claims with
 semantic schemas         rule and premise trace
```

### 3.2 Main components

**Browser interface:** captures text, displays interpretations, provides knowledge and reasoning tools, and manages local workspace data.

**Interpretation engines:** a narrow deterministic English pattern interpreter and an optional Ollama-backed LLM proposer.

**Semantic normalization layer:** standardizes entity/proposition structures and enriches records with v0.4 fields, including modal scope, temporal metadata, quantifier scope, conditions, discourse mentions, event attributes, comparison frames, and candidate claim relations.

**Validation and evidence layer:** checks source-span alignment and reports unresolved or underspecified content. Exact substring alignment is not an entailment check.

**Human review boundary:** candidate claims are not automatically written into the accepted knowledge base.

**Knowledge and inference layer:** stores accepted claims separately from derived claims and runs two symbolic rules under conservative eligibility conditions.

**Local bridge:** serves the UI and, when configured, forwards interpretation requests to an Ollama service restricted to loopback addresses.

## 4. Installation and startup

### 4.1 Requirements

- Windows PC for the supplied launchers.
- Node.js 18 or newer for full mode.
- A modern browser.
- Optional: Ollama installed locally and at least one downloaded model.
- No npm dependencies are required by the workbench.

### 4.2 Start the application

1. Extract `USG_Semantic_Workbench_v0.4.0.zip` into a normal folder.
2. Double-click `launch_windows.bat`.
3. Keep the terminal window open while using the application.
4. Open `http://127.0.0.1:8765` if the browser does not open automatically.
5. Stop the server with `Ctrl+C` in the terminal.

The server binds to `127.0.0.1` and uses port `8765` by default. Set the environment variable `USG_PORT` before launch to use another port.

`open_directly.bat` opens a static UI fallback. The local model bridge and server health checks require the Node server; therefore, full functionality should be run through `launch_windows.bat`.

## 5. User interface and workflows

The sidebar exposes six views.

### 5.1 Overview

The overview is the entry point. It introduces the workbench, provides shortcuts to interpretation and reasoning, and communicates that the project is an experimental local semantic environment. It also indicates that interpretations are proposals and must be reviewed.

### 5.2 Interpret language

This is the primary workflow.

1. Enter an English sentence or passage in the source input.
2. Optionally use one of the example inputs.
3. Select the configured interpretation engine (rule interpreter or connected local model, as applicable).
4. Run interpretation.
5. Inspect the result using four tabs:
   - **Meaning:** human-readable summary of the candidate interpretation.
   - **Structure:** claims and structured semantic fields.
   - **Evidence & source:** source spans, evidence, and provenance information.
   - **JSON:** machine-readable candidate record.
6. Discard the candidate or explicitly accept it into the knowledge base.

The interface does not equate interpretation status with truth. A `candidate` record still requires review.

### 5.3 Knowledge base

The knowledge base displays explicit claims accepted by the user. It supports:

- Searching stored concepts, relations, or evidence.
- Adding a fact manually.
- Exporting knowledge data as JSON.
- Deleting an individual explicit claim after confirmation.
- Resetting the demonstration workspace.

Accepted/source claims are kept distinct from derived claims. The inference engine's output is not silently inserted as an observed source fact.

The initial workspace is seeded with demonstration facts, including:

- `Bird SUBCLASS_OF Animal`
- `Sparrow SUBCLASS_OF Bird`
- `Tweety INSTANCE_OF Sparrow`
- `Thermometer MEASURES Temperature`
- `Scale MEASURES Weight`
- `Speedometer MEASURES Speed`

It also includes starter patterns for `MEASURES` and `SUBCLASS_OF`. These are demonstration data, not facts supplied by the user.

### 5.4 Reasoning lab

The reasoning lab runs the current symbolic rule set over eligible accepted claims. It displays newly derived claims and the rule/premise identifiers used to derive them.

The two implemented rules are:

**R-IS-A-TRANSITIVE**

```text
SUBCLASS_OF(A, B) AND SUBCLASS_OF(B, C)
    => SUBCLASS_OF(A, C)
```

**R-INSTANCE-INHERITANCE**

```text
INSTANCE_OF(X, A) AND SUBCLASS_OF(A, B)
    => INSTANCE_OF(X, B)
```

The engine records premise IDs and a rule ID on each derived claim. It repeats rule application until no additional claims are produced or its internal safety iteration limit is reached.

#### Inference eligibility restrictions

The current engine only uses claims that are:

- positive in polarity;
- asserted in modality;
- not quantified;
- unconditional (no conditions);
- present tense, when tense is specified; and
- explicitly present in reference time when time metadata is present.

Consequently, negative, modal, conditional, quantified, and temporal-change claims may be stored and inspected, but they are not premises for these v0.4 inference rules. This is a deliberate safety boundary, not an accidental omission in the representation.

### 5.5 Pattern library

Pattern discovery groups accepted knowledge by predicate and looks for recurring relationship structures across different entities. A discovered pattern is a candidate schema/hypothesis, not a proven universal rule.

The UI distinguishes:

- **Candidate schemas:** discovered patterns awaiting review.
- **Accepted schemas:** patterns explicitly accepted by the user.

The current discovery method is limited and should not be interpreted as statistical learning, ontology induction at scale, or autonomous concept acquisition.

### 5.6 Local model

This view configures the optional local Ollama integration.

Typical setup:

1. Install Ollama for Windows from `https://ollama.com/download`.
2. Pull a model, for example:

   ```bat
   ollama pull qwen2.5:1.5b
   ```

3. Ensure Ollama is running at `http://127.0.0.1:11434`.
4. In the workbench, open **Local model**.
5. Keep the default Ollama address unless the local service uses another loopback port.
6. Select **Check connection**.
7. Choose one of the installed models and save settings.

The model is not installed or downloaded by the workbench. Model choice and local hardware determine inference speed and output quality.

## 6. Local HTTP server and Ollama bridge

`server.js` uses Node's built-in `http`, `fs`, and `path` modules.

### 6.1 Network binding and restrictions

- Host binding: `127.0.0.1` only.
- Default port: `8765`; override with `USG_PORT`.
- Ollama target hostnames accepted: `localhost`, `127.0.0.1`, and `::1`.
- HTTP and HTTPS are accepted for the loopback Ollama target.
- URL credentials are rejected.
- Request bodies are limited to approximately 1.5 MB.
- Ollama calls have a 150-second timeout.

The bridge rejects non-loopback Ollama destinations. It is designed not to send source text to a remote/cloud LLM endpoint.

### 6.2 Implemented endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Returns local runtime status and workbench version. |
| `GET` | `/api/models?base=http://127.0.0.1:11434` | Queries Ollama `/api/tags` and returns installed model names. |
| `POST` | `/api/interpret` | Sends source text and limited knowledge context to Ollama chat, requests JSON output, and returns the parsed proposal. |
| `GET` / `HEAD` | Static paths | Serves application files such as `/`, `/index.html`, `/app.js`, and `/styles.css`. |

### 6.3 `/api/health`

Successful response example:

```json
{"ok":true,"runtime":"node-local-bridge","version":"0.4.0"}
```

### 6.4 `/api/models`

The optional `base` query parameter identifies the Ollama loopback address. The endpoint returns an object with `ok` and a `models` array. Connection errors return an error response.

### 6.5 `/api/interpret`

The endpoint accepts JSON containing:

- `text`: required source sentence or passage; maximum 12,000 characters.
- `model`: required installed Ollama model name.
- `ollamaUrl`: optional loopback Ollama base URL.
- `knowledge`: optional limited list of existing knowledge items used as context only.

The server constructs a system instruction requesting one JSON semantic proposal. It calls Ollama's `/api/chat` endpoint with `stream:false`, `format:"json"`, and temperature `0.1`. Invalid JSON, empty model output, oversized input, missing fields, and Ollama failures are returned as errors.

Existing knowledge is explicitly described to the model as context, not proof. The model is instructed not to add facts that are absent from the source.

## 7. Semantic interpretation and normalization

### 7.1 Two proposal paths

**Deterministic local interpreter:** recognizes a limited set of English patterns directly in `app.js`. It can be used without Ollama.

**Local LLM proposal:** asks the configured Ollama model for a JSON interpretation. The model's response is not accepted as canonical merely because it is valid JSON.

Both paths feed the same v0.4 enrichment/normalization layer, which applies shared corrections and metadata handling where supported.

### 7.2 Normalization responsibilities

The implemented normalizer includes functions for:

- Normalizing entity labels while preserving surface wording.
- Mapping model predicate and polarity values into supported forms.
- Reconciling predicate/polarity choices with explicit source wording for selected constructions.
- Recovering missing objects from source text for supported patterns.
- Identifying clause-level source spans and tense cues.
- Extracting and structuring `because` clauses.
- Building source evidence offsets and checking exact substring matches.
- Converting model entity/proposition objects into normalized semantic objects.
- Sanitizing modal scope, quantifier scope, event attributes, and comparison frames.
- Separating nested conditional propositions from their containing claim.
- Applying narrow discourse/coreference corrections.
- Creating candidate claim-to-claim contradiction relations when aligned frames differ in polarity.
- Marking incomplete or unresolved structures rather than converting malformed objects into text.

These are explicit rules and heuristics, not a general semantic parser. Unsupported constructions may remain unresolved or be represented only partially.

### 7.3 Implemented deterministic coverage in v0.4

The local rule interpreter includes narrow handling for the following representative patterns:

- `not every` versus `no` quantifier distinction;
- an `if` antecedent and consequent with independent tense;
- paired positive and negative clauses;
- a past-to-present change using `no longer`;
- `might` modality;
- a two-sentence purchase/use pattern with limited `He`/`it` reference resolution and frequency;
- a stop-using statement with a `because` failure clause;
- `does not dislike` as negative `DISLIKE`;
- “Prices were different” with a context-dependent comparison frame.

This list is a statement of narrow implemented patterns, not broad language coverage.

## 8. Semantic record model (`USG-SR/0.4`)

The normative definitions are in `SEMANTIC_REPRESENTATION_SPEC_v0.4.md`; the JSON Schema is in `schemas/usg-semantic-record-v0.4.schema.json`.

### 8.1 Top-level record

A semantic record uses:

- `schema`: `USG-SEMANTIC-RECORD`;
- `schemaVersion`: `0.4.0`;
- `representationProfile`: `USG-SR/0.4`;
- `sourceText`: original source text;
- `intent` and `interpretation`;
- `claims`: candidate propositions;
- `entities` and `mentions`: entity registry and source mentions;
- `claimRelations`: relations between claims;
- `explanations`: source-attributed explanations such as causal links;
- `unresolved`: items that could not be safely interpreted; and
- `validation`: aggregate validation/review information.

Every claim requires review. Validation status is not a truth label.

### 8.2 Claims and propositions

A claim represents a proposition with structured subject, predicate, and optional object, plus semantic metadata. The implementation maintains fields including:

- `id`;
- `subject`;
- `predicate`;
- `object` (may be `null`);
- `polarity`;
- `tense`;
- `modality`;
- `modalScope`;
- `time`;
- `quantifierScope`;
- `comparisonFrame`;
- `eventAttributes`;
- `conditions`;
- `causalLinks`;
- `completeness`;
- `evidence`;
- `provenance`;
- `sourceKind`;
- `ruleId`;
- `confidence`;
- `createdAt`; and
- `note`.

The predicate vocabulary is extensible and currently includes examples such as `SUBCLASS_OF`, `INSTANCE_OF`, `MEASURES`, `NEEDS`, `LIKE`, `DISLIKE`, `PART_OF`, `CAUSES`, `HAS_PROPERTY`, `DIFFER`, `CHANGE`, `INCREASE`, `STOP_USING`, `USES`, `BOUGHT`, and `FAILS`.

Entity types are provisional labels, not a complete ontology. Unknown is preferable to inventing a type.

### 8.3 Entity surface text and canonical text

Entity structures preserve the source-facing phrase and a normalized/canonical label separately. Determiner/reference information can distinguish definite, indefinite, unmarked, unknown, and resolved-pronoun references. Entity IDs and mention records can connect repeated mentions to a registry entry.

`object: null` is valid where the predicate is intransitive or the source omits an object. A null object must not become the literal strings `"null"` or `"[object Object]"`.

### 8.4 Polarity and predicate identity

Polarity is represented independently of predicate identity.

- “does not like” → `LIKE` with negative polarity.
- “does not dislike” → `DISLIKE` with negative polarity.

The latter is not automatically promoted to positive `LIKE`. Negation does not by itself establish inability, impossibility, or a stronger universal rule.

### 8.5 Tense, modality, and time

Legacy-compatible `tense` is `past`, `present`, `future`, or `unknown`.

`modality` can be `asserted`, `possible`, `necessary`, `obligatory`, `possible_or_ability`, or `unknown`. `modalScope` records operator, force, scope, and surface marker (for example `MIGHT`). A modal proposition is not treated as an unconditional asserted fact.

`time` supplements grammatical tense with aspect, reference time, source tense, clause evidence, and temporal adverbials where available. Grammatical tense and temporal reference are distinct. The implementation does not provide full temporal logic or event calculus.

### 8.6 Quantifier scope

The supported distinction includes:

```text
Not every customer needs the tool:
NOT(FORALL x: Customer(x) -> NEEDS(x, tool))

No customer needs the tool:
FORALL x: Customer(x) -> NOT(NEEDS(x, tool))
```

These are not equivalent. The prototype handles selected forms, not arbitrary nested quantifier expressions or fully compositional first-order logic.

### 8.7 Conditions and nested propositions

A condition contains a nested proposition with its own subject, predicate, object, polarity, tense, modality, and time metadata. Its marker, scope, effect, consequence, evidence, and logical status are stored separately.

For an `if` clause, the antecedent is not represented as an observed fact simply because it appears in the sentence. The `conditional_not_asserted` status indicates that the proposition is conditional. An IF antecedent can have present grammatical tense while its consequent is future.

`unless` is represented as an exception marker. The prototype does not infer an unstated outcome for the exception case.

Malformed nested structures are retained as unresolved rather than converted into accidental entity strings.

### 8.8 Discourse entities and mentions

The `entities` registry stores canonical entities. `mentions` records surface mentions and their possible entity references. The v0.4 resolver is intentionally narrow; supported examples include selected `He` and `it` links in a two-sentence purchase/use construction, the repeated `it` in a paired NEEDS construction, and `it` referring to the tool in the stop-using/because-failure pattern.

This is not general anaphora resolution. Ambiguous pronouns and complex discourse should remain unresolved or be reviewed.

### 8.9 Event attributes

Modifiers belonging to an event are stored in `eventAttributes`, rather than appended to an entity/object label. For example, “uses it every day” can store a frequency attribute normalized to `P1D`. Selected normalized frequencies include `P1D`, `P1W`, `P1M`, and `P1Y`. Full temporal interval arithmetic is not implemented.

### 8.10 Comparison frames and completeness

A sentence such as “Prices were different” can yield an interpretable `DIFFER` claim even though the comparison reference is missing. The comparison frame can be marked `context_dependent`, while sentence-level completeness remains complete. A later task requiring pairwise comparison or calculation must still request the missing comparison reference/set.

Completeness statuses include `complete`, `underspecified`, `unresolved`, and `not_applicable`, with missing roles and a note.

### 8.11 Claim relations and causation

The implemented claim relation is a heuristic `CONTRADICTS` candidate. It is considered only when relevant proposition frames align (including arguments, temporal frame, modal operator, quantifier scope, event attributes, and conditions) and polarity differs. It is a review cue, not a proof or automatic resolution.

Causal explanations use `CAUSE` with attribution `source_asserted`. This records that the source text asserts a cause/effect relation; it does not verify objective causality.

### 8.12 Evidence, provenance, and confidence

Evidence records the source quote and offsets. Offsets use JavaScript string indexing. `verified: true` means the quote exactly matches the corresponding source substring. It does not prove that the quote entails the claim.

Model-provided quotes and their exact-match status are tracked separately. Provenance distinguishes origins such as `local_llm_proposal`, `local_rule`, and `demo_seed`. Confidence is an informal estimate and is not calibrated probability.

### 8.13 Validation statuses

- `candidate`: one or more claims exist and no known unresolved/underspecified components remain;
- `partial`: claims exist, but unresolved content or underspecified roles remain;
- `unresolved`: no usable claim was produced.

`allClaimsRequireReview` remains true. A `candidate` result does not mean the proposition is objectively true or certainly understood.

## 9. Batch test runner

The batch runner is available in the Interpret language view.

- Accepts up to 100 sentences, one sentence per line.
- Processes requests sequentially.
- Uses the selected local model when configured.
- A failed request does not stop the remaining batch; the export includes the error and fallback record.
- Does not overwrite the current single-sentence candidate.
- Does not automatically accept results into the knowledge base.
- Exports one JSON file containing source sentences, engine/model details, normalized records, warnings, and errors.

Batch export uses `schemaVersion: "1.2"` and identifies `semanticSchemaVersion: "0.4.0"`.

A `completed` or `partial` batch status is an execution/record status, **not** an accuracy score. To evaluate a model, inspect the raw proposal, normalized result, warnings, unresolved items, conditions, quantifier scope, time, references, and claim relations.

## 10. Persistence, import, and export

### 10.1 Browser storage

Workspace data is stored in browser `localStorage` for the current browser profile. The internal saved-state format remains `schemaVersion: 2` for compatibility with earlier workbench releases.

The persisted state includes claims, patterns, derived claims, relations, last reasoning-run time, and interpretation history where present. Clearing browser data or switching browser profiles can make the local workspace unavailable. Export backups regularly.

### 10.2 Workspace export

The workspace export downloads a JSON backup with application/version metadata, semantic schema version, export timestamp, and the current state.

### 10.3 Workspace import

Import accepts a JSON backup containing either a top-level `state` object or a state object directly. It checks for the expected internal `schemaVersion: 2`, claims array, and patterns array. After confirmation, imported data replaces the data currently stored in that browser profile.

Import is not a merge operation. Export the current workspace before importing another backup.

### 10.4 Other exports

- Knowledge base view: JSON export of knowledge data.
- Interpretation view: copy candidate semantic JSON.
- Batch runner: export batch results as JSON.

## 11. Versioning and compatibility

Three version markers serve different purposes:

| Context | Version |
|---|---|
| Application release | `0.4.0` |
| Exported semantic record | `schemaVersion: "0.4.0"`, profile `USG-SR/0.4` |
| Batch export envelope | `schemaVersion: "1.2"`, `semanticSchemaVersion: "0.4.0"` |
| Browser persisted workspace | Internal `schemaVersion: 2` |

The browser storage version was deliberately retained to preserve compatibility with earlier workbench state. Do not assume that the internal storage version and exported semantic-record version are the same thing.

## 12. Privacy and security characteristics

- The local server binds to loopback (`127.0.0.1`).
- The Ollama bridge rejects non-loopback destinations.
- The workbench does not require an account, cloud API key, or remote model service.
- With Ollama configured, source text and a limited knowledge context are sent to the local Ollama process on the same PC.
- Workspace information is stored in browser local storage, not a central workbench database.
- Browser storage is not a backup system; export files should be kept separately.

These properties describe the supplied prototype implementation. They are not a formal security audit or guarantee about the user's operating system, browser extensions, local Ollama installation, or machine.

## 13. Testing and release verification

### 13.1 Automated checks recorded for v0.4.0

The release's `TEST_RESULTS.md` records:

- 118 smoke-test assertions passed, 0 failed;
- JavaScript syntax checks passed for `app.js`, `server.js`, and `tests/smoke_test.js`;
- JSON Schema Draft 2020-12 meta-schema validation passed;
- 12 representative semantic records validated against the v0.4 JSON Schema with zero schema errors;
- `/api/health` returned version `0.4.0`;
- application root and `/app.js` returned HTTP 200.

These checks validate implementation behavior, regression fixtures, schema structure, and local server operation. They are not a broad semantic-accuracy benchmark.

### 13.2 Run checks on Windows

From the extracted project directory:

```bat
node --check app.js
node --check server.js
node --check tests\smoke_test.js
node tests\smoke_test.js
```

### 13.3 Live local-model evaluation

The recorded release checks did not run a fresh live inference session against the user's installed Ollama models. The historical Qwen fixture was replayed through the current adapter; fixture replay is not the same as a live model run.

To evaluate a live model:

1. Start Ollama and connect it in the workbench.
2. Open **Interpret language** and locate **Batch test runner**.
3. Run the ten-sentence test set in `TEST_PLAN.md`.
4. Export the JSON result.
5. Repeat for another model if comparison is needed.
6. Compare each raw proposal with its normalized record and the source sentence.

The ten-sentence test set covers negated DISLIKE, paired positive/negative claims, conditional clauses with separate tense, because-causation, modality, temporal change, limited coreference/frequency, comparison context, causal explanation, and quantifier scope.

## 14. Known limitations and explicitly unimplemented capabilities

The following boundaries are important when interpreting v0.4.0:

1. **English-only, narrow coverage:** deterministic patterns cover selected sentence forms, not unrestricted English.
2. **LLM errors remain possible:** a local model can omit claims, collapse clauses, misidentify scope, or resolve pronouns incorrectly. Normalization only corrects cases covered by explicit rules.
3. **Limited coreference:** no general discourse/anaphora resolver is implemented.
4. **Limited quantifiers:** selected `not every` and `no` forms are supported; there is no general compositional quantifier logic.
5. **Limited ontology:** entity types and predicates are provisional/extensible labels, not a complete formal ontology.
6. **Limited reasoning:** only subclass transitivity and instance inheritance are implemented.
7. **No inference over rich logical structures:** conditions, modality, quantifier scope, negative claims, and temporal changes are excluded from the current simple inference rules.
8. **No general theorem prover:** there is no general-purpose first-order logic engine, defeasible logic, or complete proof system.
9. **No full temporal/event reasoning:** time metadata is lightweight; no event calculus or full interval arithmetic is implemented.
10. **Heuristic contradiction detection:** `CONTRADICTS` is a candidate relation, not a proof, resolution, or truth-maintenance system.
11. **Causation is source-attributed:** the system records what the source claims; it does not independently validate causality.
12. **Evidence alignment is not entailment:** exact source quote matching verifies textual alignment only.
13. **Confidence is uncalibrated:** confidence values must not be interpreted as statistically calibrated probabilities.
14. **No autonomous learning:** pattern discovery groups existing facts; it does not establish an autonomous learning process.
15. **No AGI/consciousness claim:** the release does not demonstrate general intelligence, awareness, or independent world understanding.

## 15. Recommended interpretation of the system's outputs

Use the following mental model:

- **Raw model output:** what the optional LLM proposed.
- **Normalized semantic record:** what the workbench could structure and reconcile under implemented rules.
- **Validation status:** whether known structural/incompleteness issues remain.
- **Human-accepted knowledge:** claims deliberately approved for storage.
- **Derived claim:** a conclusion generated by one of the two implemented symbolic rules from eligible premises.

These are different stages. Do not treat one as interchangeable with another.

## 16. Troubleshooting

### Browser does not open

Open `http://127.0.0.1:8765` manually and confirm the terminal still shows the server running.

### Port 8765 is already in use

Close the other process using the port or set `USG_PORT` to another available port before starting the server.

### Ollama connection fails

- Confirm Ollama is installed and running.
- Confirm its local API address, normally `http://127.0.0.1:11434`.
- Confirm at least one model has been pulled (`ollama list`).
- Use **Check connection** in the Local model view.
- The workbench will not connect to a remote Ollama host; this is intentional.

### Model returns invalid JSON or empty output

Try a shorter source passage or a different instruction model. The adapter expects JSON. A model request failure is reported and batch execution continues with a fallback record.

### Knowledge seems to disappear

Check that the same browser profile is being used. Browser local storage is profile-specific and may be cleared by browser cleanup. Restore from a previously exported workspace backup if available.

### A claim is marked candidate but looks wrong

`candidate` is not a correctness guarantee. Inspect the source, claim arguments, polarity, modality, time, conditions, references, evidence, and unresolved fields. Discard incorrect interpretations rather than accepting them.

## 17. File map for developers

### `app.js`

The principal browser-side implementation. Major functional areas include:

- utility and entity/claim constructors;
- initial workspace state, local-storage loading/saving;
- navigation and metrics;
- evidence construction and deterministic interpretation;
- local runtime checks and model-result normalization;
- predicate/polarity reconciliation;
- source clause and tense recovery;
- because-clause extraction and causal parsing;
- semantic entity/proposition conversion;
- modal, quantifier, event, and comparison sanitizers;
- narrow discourse/coreference handling;
- condition normalization and claim relation generation;
- v0.4 record enrichment;
- single-sentence and batch interpretation;
- Meaning/Structure/Evidence/JSON rendering;
- explicit claim acceptance;
- knowledge-base rendering and manual fact entry;
- symbolic reasoning;
- pattern discovery and acceptance;
- model settings and connection checks;
- workspace and JSON import/export.

### `server.js`

The local HTTP server, Ollama URL validation, request parsing/size limits, Ollama fetch timeout/error handling, prompt construction, API endpoints, and static-file serving.

### `index.html` and `styles.css`

The complete browser UI structure and presentation. The main views are Overview, Interpret language, Knowledge base, Reasoning lab, Pattern library, and Local model.

### Schema and specification files

The Markdown specification defines the semantic contract and intended boundaries. The JSON Schema validates the shape of exported semantic records. Passing JSON Schema validation does not prove semantic correctness.

## 18. Source-of-truth documents

For the v0.4.0 release, use these documents for their respective purposes:

- **This document:** full application and implementation documentation.
- **`SEMANTIC_REPRESENTATION_SPEC_v0.4.md`:** normative semantic representation specification.
- **`schemas/usg-semantic-record-v0.4.schema.json`:** machine-readable structural schema.
- **`ARCHITECTURE.md`:** concise architecture overview.
- **`TEST_PLAN.md`:** test cases and manual evaluation procedure.
- **`TEST_RESULTS.md`:** recorded checks and limitations of those checks.

---

*End of USG Semantic Workbench v0.4.0 full documentation.*
