# USG Semantic Workbench v0.5.4

A local-first research prototype for producing inspectable semantic representations from source text and optional local LLM proposals.

**v0.5.4 improves generation diagnosis and semantic consistency.** It builds on the v0.5.3 generate → diagnose → review → repair → recheck loop, but changes how failures are recorded and how conditional/concessive metadata is checked against the canonical semantic graph.

## What changed in v0.5.4

### Generation diagnosis and audit preservation

- Distinguishes repetition-limit aborts, request timeouts, Ollama connection/transport failures, Ollama HTTP errors, malformed response JSON, output-token exhaustion, empty responses, and other model-request failures.
- Retains HTTP status and the full Ollama error response body when Ollama returns a non-success response. For timeout or transport failure where no response arrived, it records that no response was received plus the original error metadata.
- Records failed generation, review, and repair attempts in `modelGenerationAudit`; these failures are no longer silently absent from the audit.
- Preserves full raw model response strings and parse outcomes for generation, review, and repair stages. Partial text from output-token-limit responses is also retained, but is explicitly marked as incomplete and rejected as a complete proposal.
- Exposes the structured failure category and diagnostic object through `/api/interpret` and preserves the full correction audit in exported records. It distinguishes `proposal_contract_failure` (valid JSON missing required USG arrays after repair) from `proposal_repair_exhausted` (no parseable JSON after targeted repair).

A repetition-limit abort is not treated as an output-token truncation. USG does not automatically hide the distinction by simply increasing token budgets or retrying indefinitely. The retained evidence can guide a later targeted retry policy.

### Semantic consistency checks and repairs

- Makes `IF`, `UNLESS`, and `WHEN` condition metadata marker-specific. `IF` remains conditional; `UNLESS` is explicitly an exception relation; `WHEN` remains temporal rather than being relabeled as a generic IF.
- For `UNLESS P, Q`, the compatibility condition records the explicit consequence represented by the parent claim and links to that consequent claim. The canonical `EXCEPTION` connective retains the normalized `NOT(P)` antecedent and the same consequent.
- Validates connective type, marker, logical status, antecedent shape, and compatibility metadata agreement.
- Preserves source evidence references on both clauses of `ALTHOUGH` (`CONCESSIVE`) graph nodes.
- Keeps contradiction relations synchronized between the compatibility `claimRelations` projection and canonical `semanticModel.relations` when the application creates the derived contradiction candidate.

## Semantic complexity remains uncapped

USG does not impose maximum counts for claims, entities, mentions, relations, conditions, event attributes, or unresolved items. It does not solve weak model behavior by truncating legitimate semantic content. Output-token budgets, request timeouts, and repair-round settings are execution safeguards; they are not semantic-complexity limits. A response stopped by the model's output-token boundary is retained as incomplete evidence and is not accepted as a complete proposal.

## Important limitations

- The reviewer is the same selected model used for generation. A second pass is not independent verification.
- Deterministic checks establish structural and selected consistency properties; they do not prove entailment, objective truth, or complete semantic coverage.
- Exact evidence substring alignment does not prove that the quoted span entails a claim.
- The source composer supports a finite English grammar and returns to the model-proposal path when it cannot safely parse a complete supported structure.
- Human review remains required before accepting propositions into the knowledge base.

## Kaggle build

Use `USG_Kaggle_v0.5.4_Concurrent_Ollama.ipynb` with `USG_Semantic_Workbench_v0.5.4.zip` attached as a Kaggle Dataset input. The notebook retains the Qwen/Gemma model tags and 14-sentence regression set, runs deterministic tests before inference, and adds generation-diagnostic audit columns to its CSV summary. It records concurrent worker launch and model residency; do not interpret residency alone as proof of overlapping model inference.

The notebook writes model results and audit traces to `/kaggle/working/usg_kaggle_results/` and creates a downloadable results ZIP.

## Local installation

1. Extract `USG_Semantic_Workbench_v0.5.4.zip` into a new folder; keep the older build as a backup.
2. Run `launch_windows.bat`.
3. Start Ollama and select an installed model in **Local model**.
4. Enter a sentence in **Interpret language** and inspect the **Model generation · diagnosis · repair** audit in the Meaning view.

The local bridge binds to loopback and only accepts a local Ollama destination.

## Main files

- `server.js` — Ollama adapter, typed failure classification, and generation/review/repair audit preservation.
- `generation-correction.js` — deterministic proposal diagnosis and targeted repair prompts.
- `app.js` — model adapter, semantic record enrichment, export, and audit display.
- `semantic-composer.js` — source-grounded clause composition and marker-specific condition metadata.
- `semantic-core.js` — canonical semantic model construction and graph/metadata consistency validation.
- `tests/` — deterministic unit, integration, timeout, failure-audit, and semantic-consistency tests.

The canonical semantic schema/profile remains `USG-SR/0.5.1`; v0.5.4 is an application/runtime release and does not change the schema version.
