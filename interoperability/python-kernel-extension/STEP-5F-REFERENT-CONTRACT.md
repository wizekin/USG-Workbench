# Phase 1 Step 5F — Referent integration contract and native-model gap analysis

**Status:** design gate; native adapter implementation intentionally blocked pending a versioned kernel model extension  
**Current kernel:** Python 0.5.0  
**Interchange:** USG-SEM/1.0 (unchanged)  
**Predecessor:** Step 5E native Source record integration

## Objective

Define the exact boundary required before projecting USG-SEM Referent records into the Python kernel. A Referent is a discourse entity, not merely a label or a real-world individual. Its discourse identity, identity-resolution state, identity scope, concept classification, introduction context, source grounding, and display metadata must remain distinct.

The current v0.5.0 usg.core.records.Referent is a useful native model, but it is not an exact representation of the complete USG-SEM/1.0 Referent record. Step 5F therefore establishes the required contract and records the blocking semantic gaps rather than introducing a misleading partial object or changing the already-versioned kernel in place.

## Semantic distinctions that must remain separate

1. **Referent identity:** the opaque identity of this discourse entity, represented by the USG-SEM referent ID. It is not the label.
2. **Concept identity/classification:** conceptRefs identify concepts that classify the referent. They do not identify the individual referent.
3. **Display labels and aliases:** label and aliases are lexical/display data. Equal labels or aliases do not establish coreference or identity.
4. **Identity resolution:** identity.status distinguishes PROVISIONAL, RESOLVED, AMBIGUOUS, UNRESOLVED, DISPUTED, and UNKNOWN. These states are not interchangeable.
5. **Identity scope:** identity.scope distinguishes DOCUMENT, WORKSPACE, CORPUS, and GLOBAL. It is not the same axis as a referent being discourse-local or a resolved individual.
6. **Equivalence claims:** identity.equivalenceRefs are explicit links to other referents. They must not be converted into external individual identifiers or automatically merged.
7. **Introduction context:** introducedIn.kind and introducedIn.contextRef describe the context in which the referent was introduced. They are not source spans and must not be confused with identity scope.
8. **Source grounding:** sourceRef and sourceSpan locate the source evidence for the referent; they do not establish identity resolution.

## v0.5.0 native-model gap inventory

The existing native Referent contains kind, instance_of, number, cardinality, genericity, scope, introduced_in, individual_ids, source, span, and ref.

| USG-SEM field | v0.5.0 candidate | Decision |
|---|---|---|
| id | ref: IdSpace.REFERENT | Typed, document-local ID mapping is feasible; IDs remain opaque. |
| semanticKind | kind: SemKind | Only exact enum values accepted, and the native referent invariant rejects definition-only kinds. |
| conceptRefs | instance_of: tuple[Ref, ...] | Candidate mapping to typed CONCEPT refs, but concept-definition resolution remains a separate boundary. |
| number | number: Number | Exact enum mapping where present; absent values must not be replaced by a semantic default. |
| genericity | genericity: Genericity | Exact enum mapping where present; absence must not be silently treated as SPECIFIC. |
| sourceRef | source: Ref | Exact only when the referenced Source has a native typed mapping. |
| sourceSpan | span: Span | Exact only with a native Source mapping and valid Unicode code-point offsets. |
| introducedIn.kind | introduced_in.kind | Enum names overlap, but the full record still requires a compatible context reference. |
| introducedIn.contextRef | introduced_in.ref | Not safely typed by the current contract-to-kernel boundary; do not guess NODE, INSTANCE, or another ID space. |
| label, aliases | No native fields | Must remain canonical sidecar data; never use them as identity keys. |
| identity.status | No native equivalent | No mapping to ReferentScope; retain exact status in the canonical record. |
| identity.scope | No native equivalent | DOCUMENT/WORKSPACE/CORPUS/GLOBAL is not equivalent to DISCOURSE_LOCAL/RESOLVED_INDIVIDUAL. |
| identity.equivalenceRefs | No exact native equivalent | Do not map to individual_ids; retain explicit referent-to-referent links. |
| identity.basis | No native equivalent | Preserve verbatim; do not infer evidence or resolution authority. |

cardinality and individual_ids in the native model have no direct field in the USG-SEM/1.0 Referent shape. They must not be populated by guessing from number, labels, aliases, or equivalence links.

## Required implementation boundary

A future native adapter must:

- use a deterministic, document-local typed IdSpace.REFERENT mapping while preserving opaque external IDs;
- never merge referents based on labels, aliases, concept membership, or model similarity;
- preserve the full identity status and identity scope as separate first-class values;
- preserve equivalence references as directed/explicit referent links unless a separately specified equivalence contract defines symmetry and merge behavior;
- preserve the distinction between concept references and referent identity;
- retain unsupported fields in the canonical envelope and report exact field paths and reasons;
- refuse to claim LOSSLESS when any meaning-bearing identity or context field lacks native representation;
- serialize edits without rewriting mentions or other dependent records;
- validate referent source spans against the current native Source text and reject stale/out-of-range spans rather than adjusting them;
- keep Referent and Mention as separate record families; mention occurrence and antecedent semantics are not implied by a Referent projection.

## Versioning decision

Do not modify the already-versioned Python kernel 0.5.0 Referent class in place to add missing identity semantics. The next implementation step must first introduce a separately versioned kernel model extension (or a new kernel version) that can represent identity status, identity scope, equivalence links, and introduction-context references without conflation. The document adapter can then target that explicit version and retain compatibility with v0.5.0.

USG-SEM/1.0 remains unchanged in Step 5F. No changes are made to the v0.4.0 kernel, Workbench v0.5.4, archives, immutable baselines, or Node.js workflow/action versions.

## Step 5F exit criteria

1. The native-vs-contract field gap is explicit and reviewable.
2. No semantically non-equivalent fields are coerced or defaulted.
3. Identity, concept classification, labels, aliases, identity scope, and introduction context remain distinct.
4. The next kernel-version work has concrete required fields and conformance obligations.
5. The existing v0.5.0 adapter continues to report Referents as canonical-only until an exact target model exists.

## Required conformance cases for the next native implementation

- Same label, different referent IDs: remain distinct.
- Different labels, same explicit referent ID: preserve one referent record without deriving identity from labels.
- RESOLVED versus AMBIGUOUS versus UNRESOLVED versus DISPUTED versus UNKNOWN: preserve each state exactly.
- DOCUMENT versus WORKSPACE versus CORPUS versus GLOBAL: preserve each scope exactly and independently of resolution status.
- Explicit equivalenceRefs: preserve exact targets and direction; do not merge records.
- conceptRefs versus equivalenceRefs: preserve their different target spaces and meanings.
- WORLD introduction versus CONTENT_OF/NEGATED/CONDITIONAL/HYPOTHETICAL introduction: preserve context kind and reference identity.
- Missing or unknown enum values: canonical-only with exact diagnostics, never defaulted.
- Source spans: Unicode code-point alignment, including non-BMP text; invalidated spans cause export validation failure.
- Round-trip and native edits: retain canonical-only fields, stable opaque IDs, referent order, and all dependent mentions unchanged.
