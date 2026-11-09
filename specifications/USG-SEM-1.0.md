# USG-SEM/1.0 — Canonical Semantic Interchange Contract

**Status:** Initial implementation draft for Phase 1  
**Contract identifier:** `USG-SEM/1.0`  
**Schema:** `schema/usg-sem-1.0.schema.json`  
**Compatibility targets:** Semantic Workbench `USG-SR/0.5.1` (packaged in Workbench v0.5.4), Python reference kernel `0.4.0`  

## 1. Purpose and authority

USG-SEM/1.0 defines a versioned, implementation-neutral interchange representation for semantic documents. It is the shared contract between USG implementation lines; it is not another Workbench release number or a claim that every language construction is already understood.

The contract separates semantic meaning from the software that proposed, validated, displayed, or stored it. The canonical semantic graph is the meaning-bearing structure. Flattened claims, display labels, model prompts, review workflows, and database-specific rows are projections or implementation details, not alternate sources of semantic truth.

### Architecture decision for Phase 1

1. **USG-SEM/1.0 is the normative interchange contract.** The Python kernel's typed SemIR, fixed semantic kinds, immutable expression grammar, canonical serialization, and layered records are the strongest formal foundation currently implemented. They inform the contract's type and expression rules.
2. **The Python kernel is the first reference implementation and intended authoritative validation/storage target.** Its current `0.4.0` package cannot yet consume every Workbench construction natively. Until the adapters and kernel extensions pass the conformance suite, this is a target architecture, not a claim that runtime integration is complete.
3. **Workbench v0.5.4 is a source/interpretation frontend and graph-view adapter.** Its proposal, repair, graph-building, and visualization capabilities remain useful. Its internal graph is not independently declared to be the universal semantic authority.
4. **The Semantic Representation Bridge `srb/0.1` remains a historical experiment.** It is not promoted to a canonical producer until an adapter and conformance tests exist.
5. **No human-review gate is part of this contract.** Human workflow metadata in an imported source payload may be retained as non-authoritative extension data for round-trip preservation, but it is neither required nor used to determine semantic validity, truth, or acceptance. Automated validation and evaluation are separate.

This decision may be revised only through a versioned architecture decision and migration. Package versions remain independent from the semantic profile version.

## 2. Non-negotiable semantic invariants

- **No silent semantic loss.** A construction that cannot be mapped must remain explicitly opaque, unresolved, ambiguous, or unsupported, with its source evidence and reason retained.
- **No arbitrary semantic-complexity caps.** Implementations may have separately reported resource budgets, but must not silently truncate meanings, operands, arguments, or graph nodes. A resource stop produces an incomplete result with diagnostics.
- **Structure before prose.** The compositional graph is authoritative. Claims, summaries, and text renderings are derived views.
- **Scope is explicit and ordered.** Negation, modality, quantification, attribution, tense, conditionals, exceptions, and connectives must retain their exact target/operand order. Scope cannot be inferred from array order alone where the operator requires a named role.
- **Semantic kind is not expression sort.** `semanticKind` (e.g. `EVENT`, `PROCESS`, `STATE`) is distinct from `sort` (`TERM`, `SIT`, `PROP`, `VAL`, `TIME`, `ANY`). Coarse sorts must not erase exact-kind checks.
- **Mention is not referent; label is not identity.** Multiple mentions may refer to one referent, and identical labels do not prove identical referents. Aliases and similarity are candidate links, not identity evidence.
- **A description is not an assertion.** An event/situation expression does not by itself assert that the event occurred. Assertions are explicit records pointing to expression content.
- **Epistemic status is not truth.** `SOURCE_ASSERTED` means that a source presents the content as asserted; it does not establish objective truth. `VERIFIED` is permitted only under a separate governed evaluation process.
- **Evidence alignment is not entailment.** An exact quoted substring proves only source alignment. It does not prove that the quote semantically entails the attached expression.
- **Unknown, unspecified, not applicable, withheld, and unresolved are distinct.** No adapter may replace one with another for convenience.
- **Ambiguity is represented, not guessed away.** Alternatives and their support/ranking metadata remain explicit; ordinal ranking is not probability.
- **Model confidence is not semantic modality or epistemic status.** Any model score belongs in processing/diagnostic metadata, never in the meaning-bearing expression.
- **Validity is not correctness.** Schema and structural validation establish conformance to the contract, not that the source was interpreted correctly.

## 3. Semantic document envelope

A semantic document contains:

| Field | Purpose |
|---|---|
| `profileId` | Exact contract identifier `USG-SEM/1.0`. |
| `documentId` | Opaque ID unique within the producing store; it does not imply global identity. |
| `sources` | Exact source texts, language tags, hashes, source types, trust/sensitivity labels, and optional time anchors. |
| `primarySourceRef` | Default source for spans that do not need an explicit source reference. |
| `definitions` | Optional versioned dictionary snapshot: concepts, frames, roles, relations, and ontology/grammar release identifiers. |
| `referents` | Discourse-level objects. Their IDs do not prove cross-document identity. |
| `mentions` | Textual occurrences and their referent/antecedent links, including unresolved mentions. |
| `expressions` | The compositional semantic graph. Nodes have explicit operator, result sort, operands, parameters, and annotations. |
| `rootExpressionRefs` | Ordered semantic roots for the document. |
| `assertions` | Explicit claims about expression content, with origin, epistemic status, commitment, and evaluation context. |
| `evidence` | Source spans/quotes and separate alignment/support assessments. |
| `contexts` | World, hypothetical, fictional, belief, or domain contexts and their parent links. |
| `expressionRelations` | Cross-expression relations such as supports, contradicts, or causes. |
| `unresolvedItems` | Preserved content that could not be resolved or safely interpreted. |
| `derivations` | Provenance for proposed or derived semantic structures. |
| `validation` | Structural and rule-validation results, not truth judgments. |
| `mapping` | Adapter coverage and unmapped-reference diagnostics; `targetMappings` separately reports compatibility with another implementation/version. |
| `extensions` | Namespaced, non-authoritative source-profile data required for forward compatibility or exact native round-trip. |

The JSON Schema intentionally does not impose `maxItems` on semantic arrays. A resource budget is an execution policy, not a semantic grammar rule.

## 4. Identity and identifier rules

1. IDs are opaque strings; consumers MUST NOT parse their internal structure to infer meaning.
2. IDs MUST be unique within a document across all ID-bearing record collections.
3. Every reference MUST resolve within the document or an explicitly declared external registry.
4. Document-local IDs, workspace IDs, persistent record IDs, concept IDs, and external IDs are different identity scopes.
5. A mention ID identifies an occurrence; a referent ID identifies the discourse referent; a concept ID identifies a reusable type-level meaning; a label is presentation only.
6. Cross-document referent merging requires explicit identity evidence and a versioned equivalence decision. A matching string, embedding similarity, or alias alone is insufficient.
7. An adapter MUST preserve its native IDs in namespaced extension metadata or a persistent mapping table. It MUST NOT use a display label as a canonical ID.

Recommended forms are `wb:entity:<native-id>`, `wb:expr:<native-id>`, and `py:<id-space>:<native-id>`. These are recommendations, not parseable semantics.

## 5. Sources, offsets, and evidence

### 5.1 Source immutability

The exact original source string is retained. Do not normalize whitespace, Unicode composition, punctuation, or spelling before calculating spans or the source hash. `textHash` is SHA-256 over the exact UTF-8 encoding of the stored source string.

### 5.2 Normative span convention

All USG-SEM spans use **zero-based, end-exclusive Unicode code-point offsets** into the exact stored source string. A span is `{sourceRef, start, end, offsetUnit:"unicode_code_point"}`.

This matches Python's `Span` implementation. JavaScript string offsets are UTF-16 code units, so a Workbench adapter MUST convert at its boundary and MUST reject offsets that split a surrogate pair. Tests MUST include supplementary Unicode characters (for example, emoji) before and inside evidence spans.

### 5.3 Evidence semantics

`alignmentStatus` records whether the quote is an exact substring at the declared span. `semanticSupportStatus` is separate and defaults to `NOT_ESTABLISHED`. Never convert `exactSourceMatch=true` into a claim that the quoted text entails the semantic node.

## 6. Expression graph

Each expression node includes:

- `id` — unique document-local node ID;
- `op` — a registered constructor;
- `sort` — result sort, distinct from semantic kind;
- optional `semanticKind` — exact semantic kind when known;
- `operandRefs` — ordered references to child expressions;
- `params` — constructor parameters, including role order, frame/version, operator options, or connective marker;
- `annotations` — spans, applied rules, derivation basis, and language features;
- optional `interpretationStatus` — resolved, ambiguous, or unresolved.

The initial registered constructors include the Python SemIR operators (`REF`, `KIND`, `VAR`, `REIFY`, `LIT`, `VALUE`, `HOLE`, `TIME_LIT`, `TIME_REL`, `SPEECH_TIME`, `UNRESOLVED_TIME`, `EXTENT`, `APPLY`, `ASPECT`, `COMPOSE`, `HOLDS`, `RELATE`, `PROPERTY`, `NOT`, `AND`, `OR`, `IMPLIES`, `COND`, `COUNTERFACTUAL`, `Q`, `MODAL`, `TENSE`, `TEMPORAL`, `ATTRIBUTE`, `SAME_AS`, `DIFFERENT_FROM`, `DIRECT`, `FIG`, `ALT`, `ASSERT`, `ERROR`) plus the interchange constructors `PREDICATE_APP`, `CONNECTIVE`, `QUANTIFIER`, `UNRESOLVED_REF`, and `OPAQUE`.

The added interchange constructors are not silently treated as existing Python 0.4.0 operators. The Python adapter reports them as unsupported for native SemIR import until a kernel grammar version explicitly supports their semantics.

### 6.1 Predicate application

`PREDICATE_APP` represents a predicate application when the source implementation has a meaningful predicate label and role-bound arguments but no registered `FrameDefinition` reference. It carries the predicate label as data, a `roles` array aligned position-by-position with `operandRefs`, and any known frame metadata. It MUST NOT be converted to a registered `APPLY` frame unless the target frame reference and version are actually resolved.

`APPLY` is used when a versioned frame definition is available. The number/order of fillers and role bindings must agree.

### 6.2 Quantifier preservation

The interchange constructor `QUANTIFIER` has one proposition operand (its scoped body). Its parameters retain the source quantifier/operator, variable, restrictor, and variable-binding metadata. It is intentionally separate from Python SemIR `Q`: an adapter may map it to `Q` only when the restrictor predicate, variable binding, and exact scope have a validated correspondence. A lexical quantifier label alone is not enough.

### 6.3 Operators and connectives

Operator scope is represented through operands and constructor parameters. The first operand of unary operators is the scoped body. For binary constructors, operand order is normative. `CONNECTIVE` carries an explicit connective kind and directed operand roles (`antecedent`/`consequent`) or an explicitly unordered/ordered operand role list.

A `WHEN`, `UNLESS`, `CONCESSIVE`, or contrast relation must not be relabelled as a plain `AND`/`OR` solely to fit a narrower target grammar.

### 6.4 Opaque and unresolved constructions

`OPAQUE` is a preservation node, not a successful interpretation. It must carry the original construction type/value, a reason, relevant evidence/source-span references where available, and an interpretation status. It is ineligible for semantic inference unless a later, versioned rule maps it into a registered constructor. `UNRESOLVED_REF` preserves an argument position and optional mention reference when a referent cannot be established; it must not create a new referent merely to satisfy a role.

## 7. Assertions, status axes, and epistemic boundaries

The following axes remain independent:

- `interpretationStatus`: whether the meaning was resolved, ambiguous, or unresolved;
- `validationStatus`: whether structural/rule checks passed, failed, or remain uncertain/not checked;
- `lifecycleStage`: processing/promotion stage, including automated evaluation;
- `epistemicStatus`: SOURCE_ASSERTED, INFERRED, VERIFIED, DISPUTED, or UNKNOWN;
- `evidenceAssessment`: source alignment/support/corroboration assessment.

These values MUST NOT be collapsed into a single `confidence`, `valid`, `accepted`, or `truth` flag.

An assertion references expression content and may state its origin (`SOURCE_TEXT`, `GRAMMATICAL`, `BACKGROUND_INFERENCE`, `IMPORTED_RESOURCE`, or `CURATED`), commitment (`AUTHOR`, `ATTRIBUTED`, `NONE`), attributed referent, evaluation context, and lifecycle stage. A source-attributed conditional or hypothetical expression is not equivalent to asserting its antecedent as an actual-world fact.

The lifecycle stage `AUTOMATICALLY_EVALUATED` denotes automated evaluation only. There is no human-approval stage in this contract.

## 8. Unresolved and incomplete content

Adapters and interpreters retain unresolved material as first-class records. Each item includes status, reason, source text/surface when available, scope, evidence references, and candidate references. Unsupported syntax, missing argument roles, unknown antecedents, conflicting evidence, and resource interruptions must be diagnosable separately.

A partial document is a valid deliverable when its unresolved content is explicit and the graph is structurally consistent. It must not be relabelled complete merely because generation terminated.

## 9. Provenance and model metadata

A derivation identifies the responsible component/method, input/output references, rule IDs, model identity (when applicable), timestamp, and result. Model-generated content remains a proposal until deterministic validation and applicable evaluation gates pass. Model confidence, token counts, retry counts, and runtime errors belong in processing metadata, not semantic content.

## 10. Validation requirements

A conforming validator checks:

1. JSON Schema validity;
2. unique IDs and valid references;
3. root expression existence;
4. expression graph acyclicity;
5. constructor arity and required parameters where the constructor is registered;
6. sort constraints and exact semantic-kind constraints where known;
7. role/operand alignment for `APPLY` and `PREDICATE_APP`;
8. source span bounds and quote alignment;
9. separation of mention, referent, and concept identities;
10. assertion origin/epistemic consistency;
11. explicit unresolved/opaque state for unmapped content;
12. no inference through opaque or unresolved nodes.

A passing validation certificate means the artifact conforms to the defined structural and rule subset. It does not prove that an interpretation is correct or that an asserted statement is true.

## 11. Adapter and round-trip requirements

- A source adapter MUST publish a mapping report with `LOSSLESS`, `PARTIAL`, or `UNMAPPED` status for source-to-contract conversion. Compatibility with another implementation/version MUST be reported separately under `targetMappings`; it must not be conflated with whether the source model was represented in USG-SEM.
- `PARTIAL` mappings must enumerate unsupported nodes and provide preservation nodes/extension payloads; they must not silently delete unsupported semantics.
- A reverse adapter MUST reconstruct every supported semantic distinction exactly, including operand order, polarity, modality, quantifier binding, attribution, context, evidence offsets, and unresolved state.
- Native payloads may be preserved under a namespaced `extensions` object solely to guarantee exact source-profile round-trip. They are archival compatibility data and are not a second canonical semantic store.
- An adapter MUST NOT import a source application's human-review requirement into the canonical semantic contract.
- Conformance fixtures must include positive, negative, nested-scope, conditional, exception, modal, quantifier, attributed, temporal, unresolved, ambiguous, unknown-value, and Unicode-span cases.

## 12. Phase 1 implementation boundary

This initial Phase 1 package supplies the contract schema, architecture decision, Python SemIR node adapter, Workbench v0.5.4 graph adapter, structural conformance tests, and migration map. It does **not** yet change either production branch's database or grammar, connect Workbench to the Python runtime, migrate existing knowledge stores, or claim complete semantic coverage. Those changes require the adapter tests and explicit mappings to pass first.

## 13. Versioning

- Additive optional fields and new extension keys may be backward-compatible within a minor contract revision.
- Changes to operator meaning, sort signatures, scope order, status axes, offset conventions, or identity semantics require a new major profile.
- A new operator is added only with a formal definition, constructor signature, validation rules, reference examples, and positive/negative tests.
- The profile version is independent of `workbench` and `usg` package versions.