# USG Semantic Workbench v0.5.3 — Full documentation

## 1. Purpose

v0.5.3 introduces a correction mechanism around model-generated semantic proposals. Its goal is to improve how a selected language model constructs and revises a source-grounded response, rather than changing which runtime hosts the model.

## 2. Processing flow

### 2.1 Generate

The selected model receives the original source text, the USG proposal contract, and any supplied knowledge context. The prompt requires source-grounded claims, clear separation of predicate and polarity, preservation of scope, exact source evidence, and all distinct semantic content. It explicitly forbids arbitrary item-count limits.

The initial output budget is 4,096 tokens. If Ollama reports a length stop, USG retries at 8,192 and then 16,384 tokens. A response that still reports a length stop at the final budget is not accepted as a complete proposal.

### 2.2 Diagnose

`generation-correction.js` performs deterministic checks. Current checks include:

- one JSON object and the required top-level arrays;
- intent and interpretation presence;
- claim subject, predicate, and polarity;
- exact-substring evidence quotes;
- structured condition propositions; nested semantic structures are not rejected merely for being nested, and the full raw proposal is retained when the compatibility projection cannot normalize every level;
- valid event-attribute collection shape;
- duplicate claims with the same semantic signature and same evidence;
- duplicate entity identifiers and duplicate canonical entities;
- mention references to missing entities or antecedents;
- assertion records with neither a claim nor an explicit unresolved explanation.

These checks catch defects; they do not prove entailment.

### 2.3 Review

The same selected model receives the source, complete candidate, and deterministic diagnostics in a reviewer role. It checks for omitted content, unsupported additions, argument-role errors, scope/polarity/tense/modality problems, quantifier errors, coreference defects, duplication, evidence problems, and unjustified unresolved items.

The reviewer must not impose semantic item-count limits or delete valid distinct content. Its findings are model-generated feedback, not ground truth.

### 2.4 Repair

When deterministic errors or material reviewer findings are reported, USG sends a targeted correction prompt containing:

- the original source, explicitly authoritative;
- the complete current proposal;
- deterministic diagnostics;
- reviewer findings.

The repair instruction preserves correct content and changes only defective or missing parts. It requires a complete corrected JSON object, not a partial patch. The default is two repair rounds; configure `USG_MAX_REPAIR_ROUNDS` to 0–3.

### 2.5 Recheck and audit

After each repair, USG repeats deterministic diagnosis and the reviewer pass. The output contains `correctionAudit` with status, initial and final findings, reviewer status, repair count, and generation metrics. In the browser, open the Meaning tab and inspect **Model generation · diagnosis · repair**.

Possible statuses:

- `reviewed` — no repair was needed and the reviewer completed without reporting repair-triggering defects;
- `repaired` — one or more correction rounds ran and no repair-triggering defect remains;
- `needs_review` — errors remain, or the reviewer reports uncertainty after the permitted repair rounds;
- `review_unavailable` — deterministic checks ran but the reviewer did not produce a usable review;
- `unrepaired` — no parseable/contract-complete proposal could be recovered.

None of these statuses proves semantic correctness.

## 3. Semantic item preservation

The app adapter no longer slices returned semantic collections to fixed counts. It also retains the complete `modelProposalRaw` object in interactive records so deeper nesting is not silently lost when the compatibility projection has not yet modeled it. Claims, unresolved items, conditions, and event attributes are retained as returned. The diagnosis layer likewise has no maximum counts for claims, entities, mentions, relations, conditions, event attributes, or unresolved content.

Resource safeguards remain: source input character bounds, service timeout, adaptive output-token budgets, maximum repair rounds, and the existing browser / batch transport constraints. These govern compute and execution, not the semantic structure the source may require.

## 4. Kaggle evaluation

Use `USG_Kaggle_v0.5.3.ipynb` with `USG_Semantic_Workbench_v0.5.3.zip` attached as an input dataset. The notebook retains the selected Qwen/Gemma model tags and original 14-sentence regression set. This allows direct before/after comparisons without changing the inference environment.

The exported item now contains `modelGenerationAudit`. Compare:

- repair rate and remaining findings;
- number of generated and repaired tokens;
- response time by generation stage;
- whether missing clauses, duplicated claims, invalid evidence, and malformed conditions are corrected;
- semantic accuracy judged against independently annotated expected interpretations.

Do not use `completed` or `reviewed` as accuracy scores. Human-labelled semantic accuracy remains necessary.

## 5. Limitations and next research step

The current reviewer is the same model in a separate pass. It may share blind spots with the initial generator. A later milestone could add a genuinely independent symbolic/linguistic auditor, a second-model evaluator, and a labelled evaluation set with per-phenomenon error analysis. The current implementation is a first operational correction loop, not a claim that USG can automatically solve every reasoning failure.
