# SYS-09 — Independent Construction-Level Semantic Evidence Protocol

**Status:** protocol draft on an isolated dependency branch; no annotation campaign has started  
**Selected candidate:** `clause_complement.ccomp_xcomp`  
**Dependency:** SYS-08 bilingual PUD structural-frequency diagnostics  
**Related continuation:** Phase 6 P6-CONT-02 (broader embedded, subordinate, relative, and argument-gap attachment)  
**Runtime effect:** none; all construction work remains candidate-only

## 1. Purpose and boundary

SYS-09 defines how USG may obtain independent construction-level semantic evidence before any new syntax, composition, operator, discourse, or lexical rule is promoted into runtime.

The evidence path must distinguish:

1. **Naturalistic text population** — what people actually wrote in a pinned, rights-cleared source.
2. **Syntactic proxy evidence** — source annotations such as Universal Dependencies `ccomp` and `xcomp`.
3. **Independent semantic annotation** — separately authored labels for the construction's semantic attachment, role/relation, spans, alternatives, and uncertainty.
4. **USG candidate predictions** — generated only after the gold set and held-out split are frozen.

These populations and evidence types must never be merged into one score. A syntactic dependency label is not a semantic role, and a high-frequency construction is not evidence that USG interpreted it correctly.

## 2. SYS-08 evidence and bounded construction choice

The pinned full-treebank reproduction is recorded in [the 2026-11-16 PUD structural-frequency report](../evaluations/system-wide/pud-structural-frequency-manual-2026-11-16.json).

The selected candidate is an embedded clausal complement represented by the combined **UD proxy family** `ccomp`/`xcomp`:

- Full English PUD: 348/1,000 sentences contain at least one `ccomp` or `xcomp` arc (453 instances).
- Full Arabic PUD: 349/1,000 sentences contain at least one `ccomp` or `xcomp` arc (437 instances).
- The actual 50-sentence-per-language naturalistic campaign sample contains 18 English and 16 Arabic sentences with one or more such arcs.
- Both subtypes occur in both languages, but their distributions differ. Preserve `ccomp` and `xcomp` as separate syntactic strata; do not collapse their semantic interpretation.

This is a candidate selection for annotation and evaluation design only. The current Phase 4 interpreter has a tiny SVO/VSO pattern registry; the Phase 5 roadmap explicitly identifies nested/multi-clause syntax and composition as unimplemented. P6-CONT-02 already tracks broader embedded-clause attachment, so SYS-09 must route into that existing continuation rather than create a duplicate runtime workstream.

The first naturalistic PUD campaign ran on main before the SYS-08 workflow change. It produced 300 actual target attempts (4 completed, 245 partial, 51 unsupported), with 100 lexical and 99 syntax first blockers and zero semantic-scored attempts. It did **not** contain `structural-frequency.json`. The manual full-treebank reproduction is not a GitHub Actions run and does not verify the branch's Python implementation, tests, or workflow.

## 3. Annotation unit and required semantic distinctions

The annotation unit is one candidate matrix-predicate / embedded-clause relation in its original sentence context. An item may contain multiple complement candidates; each receives a distinct stable annotation unit and source spans.

Before annotation starts, an independently authored, versioned guideline must define:

- the matrix predicate span;
- the embedded clause span and embedded predicate span;
- any overt complementizer/marker span;
- the attachment target and whether the clause functions as a complement, adjunct, coordinated clause, relative clause, quoted material, or unresolved alternative;
- the semantic relation/argument-role label licensed by the context;
- competing analyses, uncertainty, and the exact reason a unique analysis is not justified.

The semantic label inventory must be agreed and frozen by qualified bilingual annotators before annotation. It must not be copied from the runtime grammar, candidate predictions, or UD labels. In particular:

- `ccomp` and `xcomp` are recorded only as optional **syntactic proxy strata** after annotation; they are not semantic labels.
- UD `nsubj`, `obj`, and dependency direction must not be renamed Agent, Patient, Content, or another USG role.
- A marker such as *that*, *to*, or an Arabic complementizer does not by itself prove a semantic relation or attachment.
- Unresolved, genuinely ambiguous, and unannotatable cases remain explicit; annotators must not force a single label to increase coverage.
- Nested complements, control, raising, coordination, relative clauses, and adjunct attachment must be separate boundary labels or out-of-scope cases in the frozen guideline. They must not silently expand the construction definition.

## 4. Independent annotation and adjudication

For every case in the evaluation population:

1. Two qualified annotators independently label the case using the frozen guideline.
2. Annotators are blind to each other's labels, USG outputs, candidate lexicon/ranker outputs, and the UD annotation columns.
3. Each raw annotation is immutable and stored separately, including source spans, labels, alternatives, rationale, and uncertainty.
4. Agreement is reported separately for construction detection, span boundaries, attachment, semantic relation/role, and ambiguity. Do not collapse agreement into one number.
5. Disagreements are reviewed by a separate adjudicator (a third annotator) or by a documented consensus process after the independent labels have been frozen.
6. The adjudication record preserves both original labels, the disagreement category, the adjudicated result, and the reason. Unresolved disagreements remain unresolved/ambiguous.
7. No model-generated label, USG output, or post-hoc benchmark score may be used to rewrite gold.

At least two independent annotators are required per case, with a separately identified adjudicator for the profile. The agreement report must include per-language and per-label counts, raw agreement, an appropriate chance-corrected measure for categorical labels, and exact/overlap span agreement. The metric and its limitations must be stated; no agreement statistic is itself semantic correctness.

## 5. Population design, split, and minimum evidence

Keep the following separate in every manifest and report:

- naturalistic PUD-derived cases;
- independently authored or otherwise controlled diagnostic cases;
- synthetic graph-first reference cases;
- randomized Open-World cases.

For a first bilingual construction pilot, the held-out evaluation population must contain, **per language**, at least:

- 20 positive cases;
- 20 negative/adversarial cases;
- 10 ambiguous or attachment-boundary cases.

These are minimum counts, not permission to stop when a profile is linguistically unbalanced. The current 50-sentence PUD sample contains only 18 English and 16 Arabic syntactic-proxy positives for the combined family, so it is insufficient by itself for the positive minimum in both languages. Candidate sampling must expand over the pinned 1,000-sentence source or another rights-cleared source, while preserving source/document provenance.

Split by source document or `newdoc` group, not by random sentence alone. Development, annotation calibration, and held-out test groups must be disjoint by source group, source item ID, and normalized-text hash. The held-out labels remain inaccessible to the implementation and growth planner until the candidate and thresholds are frozen. Report any unavailable split or overlap as a blocker, not as zero leakage.

Negative and boundary sampling should include plausible near-misses: adjunct clauses, relative clauses, coordinated clauses, non-clausal complements, marker-like strings without a complement, ambiguous attachment, nested complements, and cases where the text does not support a unique relation. The final inventory must be reviewed by annotators; these examples are sampling categories, not preassigned gold labels.

## 6. Rights, privacy, and provenance

For every source release, pin and retain:

- repository, release/commit, source file, sentence/document IDs, Git blob SHA-1, content SHA-256, retrieval time, and transformation history;
- exact source license, license file hash, attribution, contributor/acknowledgement information, and share-alike obligations;
- whether automated evaluation and redistribution are permitted;
- deduplication, privacy-screen method, exclusions, and known limitations.

The current PUD sources declare CC BY-SA 3.0. The campaign includes the license text and a source manifest, but its short `ATTRIBUTION.md` points to pinned upstream READMEs rather than embedding their full contributor/acknowledgement content. Before external redistribution, include the pinned README files or their complete attribution content and verify share-alike packaging. This is a packaging review item, not a claim that the source license is invalid.

The existing PUD privacy screen rejects email and URL patterns but retains public proper names and is not comprehensive personal-data detection. It is suitable only for the documented bounded internal evaluation, not a general-purpose personal-data corpus. No private user data may be imported.

The Arabic PUD sample is translated and is not representative of native MSA. English PUD also contains translated sentences. These limitations must remain attached to every downstream report.

External SemEval/PropBank resources remain candidate sources until exact files, annotation units, access, redistribution, and evaluation rights are independently verified. Do not copy restricted or uncertain data into the repository.

## 7. Held-out evaluation and acceptance gate

Before scoring the held-out set, freeze the construction definition, annotation guideline, semantic label inventory, source/resource versions, split, candidate version, and per-language thresholds.

Report separately for English and Arabic, and separately for `ccomp` and `xcomp` strata where available:

- construction detection precision and recall;
- exact matrix-predicate, embedded-clause, embedded-predicate, and marker spans;
- attachment-target accuracy;
- semantic relation/argument-role accuracy;
- negative abstention and false-positive rate;
- ambiguity preservation and false-unique resolution count;
- calibration only if confidence has been independently calibrated;
- coverage and abstention, with explicit denominators.

Thresholds must be frozen before the held-out evaluation. The proposed minimum gate is at least 95% for positive detection, exact spans, attachment, and semantic relation per language; 100% abstention on frozen negatives; 100% preservation of gold ambiguity; and zero false-unique ambiguity resolutions. Any different threshold requires a documented, prospective review; thresholds must never be weakened after seeing held-out results.

A passing gold-set gate is still not permission for automatic runtime promotion. Runtime syntax/composition changes require a regression fixture before implementation, complete frozen Phase 1–5 and relevant Phase 6 regressions, affected language/target campaigns, rollback notes, and an explicit independent acceptance decision. Canonical `USG-SEM/1.0` and accepted Phase 1–5 contracts remain unchanged.

## 8. Existing assets that must not be conflated

- The current Phase 6 automatic synthetic-reference benchmark contains 500 graph-first cases for ten **nominal/modifier** profiles. It is a controlled synthetic reference, not human-annotated naturalistic gold and not a clause-complement benchmark.
- `specifications/phase6-independent-gold-manifest-1.0.schema.json` is tied to the Phase 6 `USG-INTERPRET/0.3.0` ten-profile/500-case contract. Reuse its safeguards as precedent, but do not repurpose it unchanged for SYS-09.
- `PHASE-6-STEP-6.6-INDEPENDENT-GOLD-ACCEPTANCE-PROTOCOL.md` is historical and superseded; the active Step 6.6 acceptance is the automatic synthetic-reference protocol.
- PUD CoNLL-U annotations remain syntactic evidence only. They cannot fill the semantic annotation fields in this protocol.

## 9. Current blockers and safe next steps

**Not available in this run:**

- two independent bilingual annotators for each case;
- a separate adjudicator;
- a frozen, independently reviewed semantic label inventory for clausal complements;
- rights-cleared, accessible external semantic data beyond the PUD text itself.

Therefore no semantic gold has been created, no annotation has been accepted, and no semantic rule may be promoted.

Safe next steps are to review this protocol with qualified English/MSA semantic annotators, freeze the annotation guideline and label inventory, prepare a rights-complete PUD source package, and create a source-document-disjoint candidate sample. Until those prerequisites exist, all clause-complement labels remain unannotated candidates and all runtime behavior remains unchanged.
