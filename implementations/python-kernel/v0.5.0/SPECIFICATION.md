
I want a full implementation of the Universal Semantic Grammar with all the modifications and enhancements you added but with the following limitations:

- No human review or intervention at all. I want all processes to be fully automated.
- Limited or no usage of big AI models because I have only access to free plans. I want the usage of big AI models to be with only setting general rules or maybe general issues

# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 1 of 12: Foundations, Principles, Enhancement Register, Conventions
---

## 1.1 What this document is

- **USG** is the language: the types, frames, expressions, rules, and validation protocol.
- **USGS** is the system that implements it [F1-A §3.1]. The name USGS is your project's working name, not an established standard.
- This is a **specification**, not code. Part 12 defines the first runnable kernel.
- The sources are a design dialogue. I resolved their contradictions, closed the questions they left open, and recorded every change in the Enhancement Register (§1.9).
- Statements are labelled **Normative** (MUST/SHOULD/MAY), **Informative**, or **[Provisional]**. A provisional item is a numeric or design choice the sources say must be confirmed by benchmark before it is fixed.

---

## 1.2 Source corpus and citation tags

| Tag | Source | Content |
|---|---|---|
| F1-A | File 1, "Part 3" | Discovering meaning, semantic compiler, bootstrap (§3.1–3.18) |
| F1-B | File 1, "Part 4" | Rule-governed AI, validation, coaching-document extraction (§1–15) |
| F1-C | File 1, "Brain-Inspired Part 1" | Cognitive architecture integration (§1–20) |
| F1-D | File 1, "Brain-Inspired Part 2" | Internal data structure, storage, communication (§2.1–2.29) |
| F2-A | File 2, "Part 3" | Formal recursive grammar (§3.1–3.28) |
| F2-B | File 2, "Part 4" | Inheritance, composition, generalization (§4.1–4.28) |
| F2-C | File 2, "Part 5" | Identity, concept resolution (§5.1–5.31) |
| F3-A | File 3, "Part 6" | Binary encoding and compression (§6.1–6.33) |
| F3-B | File 3, "Part 7" | Learning and knowledge acquisition (§7.1–7.36) |
| F3-C | File 3, "Part 8" | Technology, testing, first prototype (§8.1–8.32) |
| REF | `problem-solving-coach.md` | Reference only |

Source notes:
1. The sources reuse "Part 3", "Part 4", and so on for different documents, hence the tags.
2. File 2 ends mid-sentence ("The central principle is:"). I reconstructed that closing principle from the body of F2-C as P-03 and P-11.
3. The earlier "Brain-Inspired AI Modeling" conversation was not supplied. I know it only through the summaries in F1-C §1, §5, §6.
4. The sources reference external tools and standards: spaCy, Ollama, llama.cpp, SHACL, PROV-O, RDF 1.2, FAISS, and others. Their capabilities change. Part 12 adds a verification gate before any of them is relied on.
5. REF contributed mechanisms, not features. As F1-B §14 decided, the fourteen coaching lenses are not merged into USG. Only their computational principles are used.

---

## 1.3 Definition, objective, and scope

**Definition (Normative).** USG is a typed, recursive, frame-based semantic language. It represents the meaning of human-language statements as compositions of reusable frames, roles, concepts, and referents. Every construction is independently verifiable, and every stored claim carries its evidence and epistemic status [F1-A §3.1; F1-D §2.28; F2-A §3.27].

**Objective.** The sources explicitly rejected "compress all human knowledge by replacing words with binary numbers". The objective is:

> Construct a compact, reusable, machine-interpretable representation of knowledge that supports semantic retrieval, generalization, reasoning, and controlled learning. [F3-A §6.28]

Compression is a secondary optimization target. Semantic usefulness is the reason to build the system.

**Two encoding modes** [F1-A §3.15]:
- **Semantic mode** keeps what is needed for meaning-based retrieval, reasoning, and analysis. Wording may be lost.
- **Reversible mode** adds lexical and grammatical information so the source text can be reconstructed exactly. It is not assumed to beat conventional text compression. That must be measured.

**In scope for the specification:** everything in Parts 2–11.

**Implemented first (the kernel, Part 12):** a small set of types and frames, a rulebook, a local-model interpreter with validation, SQLite storage, and a benchmark [F3-C §8.29].

**Specified but deferred in implementation** [F3-C §8.29]:
- automatic universal ontology expansion
- large-scale graph mining
- sophisticated binary compression
- multiple simultaneous language models
- full domain partitioning
- autonomous grammar rewriting
- a complete procedural reasoning engine

**Non-goals:**
- a general text compressor [F3-A §6.28]
- a truth oracle (USG represents what is claimed, not what is true)
- a biological brain simulation [F1-C §16]
- an AI-centred architecture [F3-C §8.1]

---

## 1.4 Requirements

| ID | Requirement | Source |
|---|---|---|
| R-1 | Semantic accuracy: AI-produced structures follow approved rules and pass independent validation | F3-C §8 intro |
| R-2 | Universal generalization: reusable taxonomic, functional, structural, and procedural patterns across domains | F3-C §8 intro; F2-B §4.1 |
| R-3 | Personal-computer practicality: no whole-knowledge-base residency, no duplicate model copies | F1-C §8; F3-C §8.25 |
| R-4 | Auditability: every committed item traceable to source span, rule, version, and reviewer | F1-B §3; F2-B §4.25 |
| R-5 | Language independence at the core, with language-specific distinctions preserved | F1-D §2.25; F2-A §3.1 |
| R-6 | Controlled evolution: grammar and dictionary grow without drift or duplication | F1-C §13; F3-B §7.15 |
| R-7 | Model independence: replacing the AI, parser, or storage engine does not change the grammar | F1-A §3.9; F1-C §2 |

---

## 1.5 Design principles

Every later section is checked against these. Source tags show where each originates.

| ID | Principle | Source |
|---|---|---|
| P-01 | **Grammar as contract.** The Semantic Grammar is the internal language and stable contract. AI models, parsers, and storage engines are replaceable. | F1-A concl.; F1-C §2; F2-A §3.20 |
| P-02 | **Discovering meaning and representing meaning are different problems.** A model can understand a sentence yet encode it inconsistently. The two are separate layers. | F1-A intro |
| P-03 | **AI proposes, the system disposes.** The AI may not modify the grammar, merge identities, mark anything verified, approve its own output, or change validation rules. This is enforced by software permissions, not prompts. | F1-B §1; F2-A §3.25; F3-B §7.35 |
| P-04 | **Deterministic first.** Python does everything checkable. The AI handles contextual interpretation only. Reuse learned patterns to cut model calls. Escalate by risk. | F1-A §3.7–3.11; F3-B §7.31 |
| P-05 | **Meaning is not truth.** What a sentence means is separate from whether it is true. Source-asserted, inferred, and verified claims are kept distinct. | F1-B §12; F1-D §2.26; F2-A §3.13 |
| P-06 | **No unsupported content.** Every element traces to a source span, a declared inference rule with valid premises, or an authorized evidence source. A plausible assumption is never stored as a stated fact. | F1-A §3.6; F2-A §3.14 |
| P-07 | **Preserve what is unknown.** Unspecified is not absent. Ambiguity is retained. Open-world reasoning is the default. Abstaining is a legitimate outcome. | F1-A §3.7; F2-C §5.7; F3-B §7.33 |
| P-08 | **Types and tokens are separate.** Concepts and frames are types. Referents, events, and assertions are tokens. A sentence about "a doctor" does not name a particular real doctor. | F1-A §3.13–3.14; F3-B §7.4 |
| P-09 | **Frames are the compositional core.** Meaning is built by frame application. The graph is the logical store. Structures are recursive. | F1-A §3.6; F2-A §3.4; F1-D §2.8 |
| P-10 | **Structurally valid is not semantically correct.** Validation has five levels. "Formally valid" never means "correct". | F1-B §3–4, §6 |
| P-11 | **Identity is stable and reversible.** IDs are immutable and carry no semantics. Labels are not identity. Equivalence is a versioned, reversible mapping rather than a deletion. | F1-D §2.6; F2-C §5.12, §5.16 |
| P-12 | **Reuse before create; compose before extend.** Check for an existing concept before proposing a new one. Prefer composing existing frames over new fundamental frames. Grammar growth is bounded. | F1-A §3.4; F3-B §7.15; F2-B §4.23 |
| P-13 | **Learning is not promotion.** Everything learned is a candidate. Foundational rules are protected from the learner. | F3-B §7.21, §7.25 |
| P-14 | **Similarity is not equivalence.** Structural and functional similarity become reusable abstractions only after counterexample, discrimination, and information-preservation tests. | F2-B §4.15, §4.26; F1-C §6 |
| P-15 | **Semantic abstraction and compression are separate decisions** with separate success criteria. | F2-B §4.18; F3-A §6.14 |
| P-16 | **Universal identity does not mean universal residency.** Knowledge is partitioned and activated sparsely. Activation controls accessibility, not truth. A retrieval weight is not a probability. | F1-C §8–10; F1-D §2.15 |
| P-17 | **Logical model, physical storage, and binary encoding are independent layers.** | F1-D §2.4; F2-C §5.29; F3-A §6.2 |
| P-18 | **Everything is versioned and auditable.** Grammar, ontology, frames, rules, and encodings are versioned, and old records stay interpretable. | F2-B §4.25; F3-A §6.19 |
| P-19 | **Interpretation, knowledge retrieval, and reasoning are separate tasks**, never one opaque model call. | F1-C §14 |
| P-20 | **Modules cooperate through messages and immutable snapshots.** There is one authoritative writer per store, and the workspace is versioned. | F1-C §4; F1-D §2.11–2.12 |
| P-21 | **Language-independent core.** Language-specific distinctions (tense, aspect, definiteness, evidentiality) are preserved. The lexical layer is separate from the semantic layer. | F1-D §2.25; F2-A §3.1 |
| P-22 | **Resource-bounded.** Models are shared services. Budgets are explicit. Heavy modules load on demand. | F1-C §3; F3-C §8.17, §8.25 |
| P-23 | **Measure before scaling.** Benchmarks, held-out sets, negative pairs, and abstention scoring come first. Correctness comes before compression. | F1-A §3.16; F3-C §8.21–8.29 |
| P-24 | **Purpose test for every mechanism.** A mechanism is included only if it improves accuracy, generalization, compression, efficiency, or maintainability. Biological resemblance is not a justification. The system's own processing history is stored apart from world knowledge. | F1-C §16, §19 |
| P-25 | **Source text is data, never instructions** (added; see E-13). | Enhancement |

---

## 1.6 Architecture overview

The sources describe the system three ways: a nine-stage "semantic compiler" [F1-A §3.9], a cognitive architecture of controllers and modules [F1-C §3, §15], and a learning architecture [F3-B §7.34]. This is the single consolidated view.

```text
                         CENTRAL CONTROLLER (deterministic)
        task planning · priorities · budgets · retries · escalation · commits
                                   │
                         COGNITIVE WORKSPACE (versioned, reference-only)
                                   │
 ┌─────────────┬───────────────────┼───────────────────┬──────────────────┐
 │INTERPRETATION│      MEANING      │    ASSURANCE      │  LEARNING &      │
 │  PLANE       │      PLANE        │    PLANE          │  GENERALIZATION  │
 │              │                   │                   │  PLANE           │
 │ tokenizer    │ Type system       │ Derivation        │ 4 learning       │
 │ syntax       │ Frame library     │ certificate       │ engines          │
 │ semantic     │ Expression        │ 5-level validator │ pattern discovery│
 │ parser       │ grammar           │ metacognition     │ generalization   │
 │ (rules +     │ Rulebook          │ review queue      │ counterexample   │
 │ local AI)    │ Semantic IR       │ evidence &        │ promotion        │
 │ frame/concept│ Lexical layer     │ epistemics        │ controller       │
 │ resolvers    │                   │                   │ optimizer        │
 └──────┬───────┴─────────┬─────────┴─────────┬─────────┴────────┬─────────┘
        └─────────────────┴─────────┬─────────┴──────────────────┘
                                    │
        KNOWLEDGE PLANE: Global Concept Registry · domain stores ·
        semantic / episodic / procedural memory · active cache
                                    │
        STORAGE & ENCODING PLANE: SQLite relational typed graph ·
        USBF binary blocks · local dictionaries · indexes
```

The compiler stages map onto the planes. Tokenizer and syntax analyzer belong to Interpretation. The semantic parser, frame resolver, and concept resolver span Interpretation and Meaning. The validator belongs to Assurance. The IR belongs to Meaning. The binary encoder and knowledge store belong to Storage. Part 8 details the flow.

Planes are logical units, not necessarily separate processes [F1-C §3]. The diagram shows dependencies, not a one-way pipeline. Modules iterate. Validation can send a candidate back, and retrieval can run before interpretation completes [F1-C §15].

---

## 1.7 Conventions

### 1.7.1 Normative language
MUST, MUST NOT, SHOULD, SHOULD NOT, MAY carry their usual specification meanings.

### 1.7.2 Rule ID scheme (Enhancement E-01)

The sources use at least four colliding rule-ID styles. This specification uses **`SG-<DOMAIN>-<NNN>`**, where the domain is one of:

`FND` foundational · `CON` construction · `TYP` types · `FRM` frames · `INT` interpretation · `EVD` evidence · `CAN` canonicalization · `IDN` identity · `GEN` generalization · `LRN` learning · `KNW` knowledge/inference · `ENC` encoding · `GOV` governance and versioning · `SEC` security

Interpretation rules may carry a readable alias, for example `SG-INT-010 PASSIVE_AGENT_MAPPING`.

**Legacy-ID mapping** (every explicit ID in the sources):

| Legacy ID | Source | Meaning | New ID |
|---|---|---|---|
| SG-001 | F1-B §2 | Entity typed only with sufficient evidence | SG-INT-001 |
| SG-002 | F1-B §2 | Role assigned only if frame supports it and evidence exists | SG-FRM-001 |
| SG-003 | F1-B §2 | No unsupported facts | SG-EVD-001 |
| SG-004 | F1-B §2 | Preserve uncertainty | SG-EVD-002 |
| SG-005 | F1-B §2 | Reuse existing concepts | SG-IDN-001 |
| SG-006 | F1-B §2 | Separate observation from inference | SG-EVD-003 |
| SG-007 | F1-B §2 | Representation satisfies frame constraints | SG-CON-001 |
| SG-TYPE-001 | F2-A §3.5 | Role-type compatibility unless coercion applies | SG-TYP-001 |
| SG-FRAME-002 | F2-A §3.8 | Specialized frame inherits compatibly | SG-FRM-002 |
| SG-INHERIT-001 | F2-B §4.9 | Specialization preserves parent commitments | SG-FRM-002 (merged) |
| SG-EVIDENCE-003 | F2-A §3.14 | Every asserted element is supported | SG-EVD-001 (merged with SG-003) |
| SG-CANON-004 | F2-A §3.16 | Canonical sharing only if meaning preserved | SG-CAN-001 |
| SG-IDENTITY-005 | F2-A §3.18 | Merge only if equivalence established in scope | SG-IDN-002 |
| SG-GENERALIZE-006 | F2-A §3.19 | Generalization preserves common relations, no unsupported claims | SG-GEN-001 |
| SG-GEN-001 | F2-B §4.15 | No universal rule from observed examples alone | SG-GEN-002 |
| SG-IDENTITY-001 | F2-C §5.7 | Open world: missing is not incompatible | SG-KNW-001 |
| SG-IDENTITY-002 | F2-C §5.20 | Defining-constraint change needs versioning and review | SG-GOV-001 |
| SG-MERGE-001 | F2-C §5.12 | Equivalence as a reversible versioned mapping | SG-IDN-003 |
| SG-LEARN-001 | F3-B §7.11 | Investigate existing concept before proposing a new one | SG-LRN-001 |
| SG-ROLE-001, SG-FRAME-001 | F3-C §8.2, §8.18 | Illustrative JSON examples only | SG-FRM-001, SG-CON-002 |

Named rules (PASSIVE_AGENT_MAPPING, NEGATION_SCOPE_RULE, FRAME_EXISTS, and similar) are assigned IDs in Part 5.

### 1.7.3 Five orthogonal status axes (Enhancement E-02)

The sources use at least five overlapping status vocabularies:

- valid / uncertain / invalid
- resolved / ambiguous / unresolved
- the discovered-to-promoted candidate lifecycle
- verified / disputed / unknown
- the E0–E5 evidence ladder

They answer different questions and MUST NOT be merged into one field.

| Axis | Question | Values | Source |
|---|---|---|---|
| A. Interpretation outcome | Did we determine the meaning? | RESOLVED · AMBIGUOUS (alternatives retained) · UNRESOLVED | F3-B §7.33 |
| B. Validation result | Which checks passed? | per level L1–L5: PASS / FAIL / NOT_CHECKED / UNCERTAIN, aggregated as FORMALLY_VALID / UNCERTAIN / INVALID | F1-B §4, §6 |
| C. Lifecycle stage | How far along is this record? | DISCOVERED → STRUCTURED → VALIDATED_FORMALLY → REVIEWED_SEMANTICALLY → CORROBORATED → PROMOTED; also REJECTED, DEFERRED, DEPRECATED | F3-B §7.25 |
| D. Epistemic status | What is the claim's standing in the world? | SOURCE_ASSERTED · INFERRED · VERIFIED · DISPUTED · UNKNOWN | F1-B §12; F2-A §3.13 |
| E. Evidence vector | What supports it, on which dimensions? | SourceEvidence, ExtractionMethod, RuleValidation, Corroboration, Uncertainty, ReviewStatus | F1-B §8.5 |

Parts 5 and 6 define the transitions between values.

---

## 1.8 Glossary

| Term | Meaning |
|---|---|
| Concept | A reusable meaning with a stable ID (a type): Heart, Transfer |
| Lexical sense | A word-form's possible meaning, mapped to concepts in the lexical layer |
| Referent (discourse entity) | A particular thing mentioned in a source ("a doctor" in sentence 1). It is not a real-world individual unless resolved. |
| Frame | A reusable structure defining roles, constraints, and state semantics for a situation (a type) |
| Role | A named participant slot in a frame |
| Frame instance | A particular situation built by applying a frame to bindings |
| Proposition | A content that can be true or false, such as a negated or hypothetical situation. It is distinct from an occurring event. |
| Assertion | A proposition plus its source, evidence, and epistemic status |
| Semantic IR | The validated internal structure into which language is compiled |
| Candidate | Any proposed record not yet promoted |
| Canonical | A validated, normalized representation accepted by the system |
| Derivation certificate | A machine-checkable record of how a candidate was built: source spans, frame, roles, rules |
| Rulebook | The authoritative, machine-readable collection of construction, interpretation, and knowledge rules |
| Validator | Deterministic checker, with escalation to review for what cannot be formalized |
| Registry | The sole authoritative allocator and recorder of stable IDs |
| Cognitive Workspace | The versioned, reference-only store of the task in progress |
| SemanticHub | Retrieves stable concept knowledge: what a concept means |
| ContextIntegrator | Decides what a concept means here, given context |
| Domain store | A partition of detailed knowledge, sharing global concept IDs |
| Provisional concept | A registered but unvalidated placeholder concept that cannot enter trusted knowledge |
| Promotion | An authorized transition of a candidate into trusted knowledge or grammar |
| USBF | Universal Semantic Binary Format, the proposed container format (Part 11) |
| Functional ontology | A classification by what components do, separate from what they are |
| Generalization budget | Explicit limits on candidate abstractions per learning cycle |

---

## 1.9 Source audit: the Enhancement Register

I audited the sources for contradictions, gaps, unsafe assumptions, and under-specified mechanisms. Each item below was corrected before its content entered the specification. "Resolved in" says where the fix is specified.

| ID | Issue found | Source | Enhancement | Resolved in |
|---|---|---|---|---|
| E-01 | Rule IDs collide: SG-001 vs SG-EVIDENCE-003 duplicate "no unsupported facts"; SG-GEN-001 vs SG-GENERALIZE-006; SG-IDENTITY-002 used in two meanings | F1-B §2; F2-A; F2-C | One namespace with a legacy map (§1.7.2) | Part 1, 5 |
| E-02 | Five overlapping status vocabularies | various | Five orthogonal status axes (§1.7.3) | Part 1, 5, 6 |
| E-03 | Evidence ladder E0–E5 mixes dimensions. The source itself warns that formal derivation and source reliability differ. | F1-B §8.5 | Evidence vector is primary. E-level is a derived workflow label. | Part 6 |
| E-04 | Role names inconsistent (AGENT / EXAMINER / PRACTITIONER / SOURCE). The role "PATIENT" collides with the concept Patient. | F1-A, F2-A, F3-B | Two-tier roles: universal thematic roles with frame-specific specializations | Part 2, 4 |
| E-05 | Examples conflate concepts and referents ("PATIENT = PATIENT"), against the source's own type/token rule | F1-A §3.13 vs later | Role fillers MUST be referents or explicit kind-references | Part 2, 3 |
| E-06 | "TRANSFER" is overloaded: a function, a frame, and give / offer / lend / sell variants. Offer and attempt must not become completed events. | F2-A §3.16; F3-B §7.23 | Frame family plus a realization-status modifier (ATTEMPTED / OFFERED / COMPLETED) | Part 3, 4 |
| E-07 | Functional ontology lists differ (DECIDE vs PROCESS/REGULATE; TRANSPORT vs TRANSFER) | F1-B §8.1; F2-B §4.5 | Separate FN namespace with defined relations among functions | Part 4 |
| E-08 | Grammar v0.1 left twelve items open (scope, quantifiers, modal/temporal operators, equality, unknowns, ambiguity, provenance…) | F2-A §3.23 | Grammar v1.0 closes all twelve | Part 3 |
| E-09 | One presence bit per role cannot distinguish unexpressed / explicitly unknown / not applicable / withheld | F3-A §6.7 | Two-level role-state encoding | Part 11 |
| E-10 | Template-worth inequality ignores per-instance parameters and index cost | F3-A §6.13 | N(L − R − P) > D + I | Part 11 |
| E-11 | Spreading-activation formula is unbounded. The source notes it needs normalization. | F1-D §2.16 | Bounded, normalized, decayed, top-k activation | Part 10 |
| E-12 | Generalization score Q(G) lets weighted reuse offset semantic error | F2-B §4.17 | Correctness is a hard gate. Score ranks only the survivors. | Part 9 |
| E-13 | Source text could contain instructions to the interpreting AI, and malicious documents are noted only as a promotion risk | F3-B §7.12 | Source text is data. Isolation, quarantine tiers, SEC rules. | Part 5, 6 |
| E-14 | Relative times need an anchor. The source says so but gives no record for it. | F1-A §3.13; F2-A §3.12 | Source record carries a time anchor, time zone, and calendar | Part 2, 3 |
| E-15 | Review-priority table is "illustrative" and agreement between two models is not proof of correctness | F3-B §7.18, §7.17 | Calibration procedure with human-audited samples, including audit of auto-accepted low-risk cases | Part 6 |
| E-16 | Metrics lack operational definitions, especially abstention quality | F3-C §8.22 | Defined metrics, including coverage-versus-error curves | Part 12 |
| E-17 | Coaching-file mechanisms (novelty protection, "do not overinterpret", evidence ladder, ≥3 occurrences, user veto, scaffolding fade) are only partly mapped | REF; F1-B §8–9 | Pattern graduation and human veto. Redundancy check before analysis. Observation / interpretation / pattern / identity-claim classes. | Part 6, 9 |
| E-18 | Grammar and ontology versioning is required but not specified | F2-B §4.25; F3-A §6.19 | Semantic versioning with compatibility classes and migration records | Part 2, 11 |
| E-19 | Equality and identity operators are missing from the grammar | F2-A §3.23 | SAME_AS / DIFFERENT_FROM / coreference chains with scope | Part 3 |
| E-20 | SQLite is the first store but concurrent writers, and the registry as sole writer, are not specified | F1-D §2.24; F2-C §5.18 | Single-writer registry, WAL mode, idempotent proposal keys | Part 7, 11 |
| E-21 | Multilingual claims lack a layer for language-specific distinctions | F1-D §2.25 | Language Annotation layer attached to instances | Part 2, 8 |
| E-22 | "Round trip" equality is undefined without a canonical serialization | F3-A §6.31 | Canonical ordering and canonical bytes for IR equality, with hash check | Part 11 |
| E-23 | Cost function C = αS + βV + γP has no calibration procedure | F2-A §3.22 | Constraint-first selection, with weights calibrated on the benchmark | Part 3, 12 |
| E-24 | Interop with RDF / OWL / SHACL is mentioned but no mapping is given | F1-B §5; F1-D §2.21 | Defined export mapping | Part 11 |
| E-25 | No explicit gate to re-verify tool and standard capabilities at build time | F3-C §8 | Technology verification gate | Part 12 |

---

## 1.10 Roadmap

| Part | Contents |
|---|---|
| **1** | Foundations, principles, enhancement register, conventions (this part) |
| **2** | Semantic type system and data model: records, roles, IDs, relations, versioning |
| **3** | The formal grammar v1.0: expressions, operators, scope, time, modality, negation, causation, ambiguity, canonicalization |
| **4** | Frames, functional ontology, abstraction layers, Foundation Package |
| **5** | Rulebook, Semantic Derivation Protocol, five-level validation |
| **6** | Evidence, provenance, truth status, review, security |
| **7** | Concept identity and resolution |
| **8** | Interpretation pipeline: language to IR, bootstrapping, resources, multilingual |
| **9** | Learning, generalization, grammar evolution |
| **10** | Cognitive architecture, memory, resource management |
| **11** | Storage schema and binary encoding (USBF) |
| **12** | Technology, testing, benchmarks, kernel specification, coverage matrix, closure of all open questions |

Part 12 ends with a traceability matrix from every source section to the spec section that implements it. It also closes each open-question list the sources leave behind: F2-A §3.23 and §3.28, F1-D §2.29, F3-B §7.36.


---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 2 of 12: Semantic Type System and Data Model

This part defines what exists in USG: the semantic kinds, the record categories, roles, relations, identifiers, referents, the lexical layer, versioning, and the invariants every store must satisfy. Part 3 defines how these are composed into expressions.

---

## 2.1 Layered record model

The sources separate reusable definitions from particular assertions [F1-A §3.14]. They add a provenance layer [F1-A §3.14] and a separate processing-history store [F1-C §19]. The consolidated model has five layers:

```text
 LAYER L  LEXICAL         word forms ──► lexical senses ──► concept IDs
 LAYER D  DICTIONARY      concepts · definitions · relations · roles · frames · rules
                          (type level; changes rarely; versioned)
 LAYER I  INSTANCE STORE  referents · frame instances · propositions · assertions
                          (token level; grows with every source processed)
 LAYER P  PROVENANCE      sources · spans · evidence · certificates · reviews
 LAYER H  PROCESS HISTORY tasks · attempts · failures · validation outcomes
                          (about the system itself, never mixed with world knowledge)
```

An index layer, the **Global Concept Registry** (§2.13), cuts across all five.

**Why this matters (Normative).** Millions of instances reference a small dictionary, so frame and concept definitions are stored once [F1-A §3.14]. This normalization lets one concept definition be shared by every document that mentions it.

---

## 2.2 Semantic kinds

The sources list "semantic types" in three different places [F1-B §15; F1-D §2.3; F3-B §7.3], and some lists overlap with ontology classes. This spec separates two things (Enhancement E-27):

- **Semantic kinds** are a small, fixed vocabulary built into the grammar. Adding or changing one is a MAJOR grammar change (§2.12).
- **Ontology classes** are concepts in the growing dictionary (Vehicle, Fluid, AnimateEntity). They are related by IS_A and are not kinds.

Role type constraints can use either. "THEME must be an ENTITY" is a kind constraint. "FOOD must be an EdibleEntity" is a class constraint.

| Kind | Definition | Example | Origin |
|---|---|---|---|
| ENTITY | Anything that can be a participant: objects, substances, organisms, places, organizations, abstract entities | Doctor, Water, Cairo | F1-B §15 |
| EVENT | Bounded occurrence with temporal extent | Arrival, Examination | F1-B §15 |
| PROCESS | Ongoing or composite change with no inherent endpoint, or an aggregate of events | Digestion, Manufacturing | F1-B §15; F2-B §4.10 |
| STATE | Condition holding over an interval without change | Allergic, Closed | F1-B §15 |
| PROPERTY | An attribute dimension with a value domain | Color, Temperature | F1-B §15 |
| VALUE | A member of a property's value domain | Red, Solid | F1-D §2.3 |
| QUANTITY | A magnitude with dimension and unit, or a pure count | 37.5 °C, 2 | F1-B §15 |
| RELATION | A relation-type definition | HAS_PART | F1-B §15 |
| ROLE | A participant-slot definition | AGENT | F1-B §15 |
| FRAME | A situation template | Transfer | F1-D §2.3 |
| PROPOSITION | A truth-evaluable content, which need not be actual | "John ate the apple", as embedded in a negation | F3-B §7.3 |
| CONSTRAINT | A formal restriction on kinds, classes, roles, or values | EXPECTED_TYPE = Edible | F1-B §15 |
| TIME | An instant, interval, duration, or unresolved temporal expression | 2026-10-15, YESTERDAY | added |
| FUNCTION | A capability or purpose, in the FN namespace (Part 4) | FN.TRANSPORT | added |
| EXPRESSION | A linguistic object discussed as such | the word "bank" | added |

Additions and reasons:
- TIME is needed because temporal reasoning requires its own typed values [F2-A §3.12].
- FUNCTION is needed for the functional ontology [F1-B §8.1].
- EXPRESSION covers the one case where words are concepts: when we discuss the words themselves [F1-D §2.20].

**Kind rules (Normative):**
1. Every concept, referent, and expression node has exactly one kind.
2. ROLE, RELATION, FRAME, and CONSTRAINT are definition kinds. They MUST NOT fill a role in a frame instance.
3. All other kinds MAY fill roles, subject to the role's constraints.
4. There are no implicit kind coercions. A kind change is an explicit operator (for example REIFY or NOMINALIZE, Part 3) with a registered rule. A figurative reading is handled separately (Part 3, SG-TYP-001).

---

## 2.3 Record categories

The sources propose seven logical record categories plus a lexical layer [F1-D §2.20]. Instance-level entities, mentioned in F1-A §3.13 as "ENTITY_REFERENCE", need a record of their own. I added it as Referent, and added a handful of support records.

| Layer | Record | Purpose |
|---|---|---|
| D | **Concept** | Identifies a reusable meaning |
| D | **ConceptDefinition** | A scoped, versioned definition of a concept (§2.9) |
| D | **RelationDefinition** | A permitted relationship with logical properties (§2.8) |
| D | **RoleDefinition** | A participant slot (§2.6) |
| D | **FrameDefinition** | A reusable semantic structure (Part 4) |
| D | **RuleDefinition** | A construction, interpretation, or knowledge rule (Part 5) |
| D | **EquivalenceMapping** | A reversible, versioned identity mapping (§2.14, Part 7) |
| D | **ExternalMapping** | An alignment to WordNet, FrameNet, and similar (Part 8) |
| L | **LexicalEntry / LexicalSense** | Word forms and their candidate concepts (§2.10) |
| I | **Referent** | A particular entity mentioned in a source (§2.5) |
| I | **FrameInstance** | A situation description built from a frame (§2.11) |
| I | **Assertion** | A claim about content, with its status (§2.11) |
| P | **Source / Span** | Origin text and exact locations (§2.12) |
| P | **EvidenceRecord** | What supports an assertion (Part 6) |
| P | **DerivationCertificate** | How a candidate was constructed (Part 5) |
| any | **LanguageAnnotation** | Language-specific distinctions (§2.12) |
| any | **OntologyRelease** | A named snapshot of dictionary versions (§2.13) |

### Universal record header

```text
RecordHeader
    id               stable ID in this record's ID space
    record_kind      one of the categories above
    status           lifecycle stage (status axis C, §1.7.3)
    version          integer, per record
```

The sources chose a minimal header on purpose [F1-D §2.6]. Definitions and properties are separate relationship records, so a sparse graph stores only edges that exist. In addition, every record MUST be resolvable to the grammar version and ontology release under which it was created (§2.13).

---

## 2.4 Identifiers

### 2.4.1 ID policy

Decided in F1-D §2.6 and F2-C §5.15–5.16, with the one addition marked below.

1. **ID spaces.** Separate typed integer spaces: CONCEPT, FRAME, ROLE, RELATION, RULE, REFERENT, INSTANCE, ASSERTION, EVIDENCE, SOURCE, CERTIFICATE. A bare integer is never an ID. It is always an (ID space, integer) pair.
2. **Allocation.** The Registry is the only allocator, transactionally, from a global integer sequence per space [F2-C §5.15 Option A]. Future distributed operation adds external GUIDs through a mapping table (Option D) without changing internal IDs.
3. **Immutable.** An ID never changes meaning and is never reused. Merged, split, or deprecated records leave a **tombstone**, and old references stay resolvable [F1-D §2.6].
4. **Meaning-free.** An ID encodes no classification, domain, or hierarchy [F2-C §5.16]. Domains are tracked in the Registry. Short binary codes come from local dictionaries (Part 11), never from ID design.
5. **Labels are not identity.** Labels are editable attributes.
6. **Content hash ≠ ID.** A definition version's hash detects exact duplicates. It is not a stable identifier [F3-A §6.11].
7. **0 is invalid** in every space.
8. **Provisional IDs.** Provisional concepts and frames use a separate `P` space (`P:1001`) [F2-C §5.19]. A provisional ID MAY appear only in provisional records and MUST NOT appear in trusted knowledge (Invariant I-07).
9. **Task-local handles (added).** During processing, controllers create working nodes with workspace-local handles (`W:3`), scoped to one task and version of the workspace. These handles are never persisted. They are mapped to permanent IDs at commit by the Registry. This keeps concurrent controllers from allocating colliding or duplicate IDs [F1-D §2.6, §2.11].

### 2.4.2 Four kinds of identity

Separated explicitly [F2-C §5.2]:

| Identity | Example | Where it lives |
|---|---|---|
| Lexical | "car" and "car" as written forms | LexicalEntry |
| Sense | "car" and "automobile" mean the same | LexicalSense mappings |
| Concept | Two records defining the same meaning | Concept IDs and EquivalenceMapping |
| Individual | Two descriptions of the same physical car | Referent identity (§2.5) |

Two different operations act on them, RESOLVE_CONCEPT and RESOLVE_INDIVIDUAL (Part 7). "A red car" and "a red automobile" may share a concept without sharing an individual.

---

## 2.5 Referents (discourse entities)

A concept is a type. A referent is a particular thing mentioned in a source [F1-A §3.13; F3-B §7.4]. The sources' own later examples blur this ("PATIENT = PATIENT"). The rule below makes it normative (Enhancement E-05).

**Rule SG-CON-003 (Normative).** A role filler in a frame instance MUST be a referent, a literal, a time expression, a proposition or frame-instance reference, or an explicit **kind-reference** `KIND(concept)`. It MUST NOT be a bare concept ID.

```text
Referent
    header
    kind               semantic kind (ENTITY, EVENT, ...)
    instance_of        concept IDs (may be several; may be empty)
    scope              DISCOURSE_LOCAL | RESOLVED_INDIVIDUAL
    individual_ids     external IDs when resolved (e.g. Wikidata), optional
    number             SINGULAR | PLURAL | MASS | UNSPECIFIED
    cardinality        exact integer, range, or UNSPECIFIED   ("two tablets")
    genericity         SPECIFIC | GENERIC
    source_id, span    where it was introduced
```

`KIND(DOG)` is used for generic statements ("Dogs bark"). Part 3 defines how generic, existential, and universal readings are distinguished.

**Rules:**
- A discourse-local referent MUST NOT be merged with another source's referent unless RESOLVE_INDIVIDUAL authorizes it, with evidence. A repeated phrase ("a doctor") does not mean the same doctor.
- Coreference inside one source (pronouns, repeated definites) creates a coreference link between referents. The link is a validated claim with its own evidence, not a silent merge.
- A referent's properties are stored as assertions, not as fields. For "the young doctor", `Young` is a PropertyAssertion on the doctor referent [F1-A §3.13].

---

## 2.6 Roles: the two-tier system (Enhancement E-04)

Role names in the sources vary: AGENT, EXAMINER, PRACTITIONER, SOURCE, EATER. A role "PATIENT" also collides with the medical concept Patient. The fix is two tiers.

**Tier 1: universal thematic roles.** A closed, small set owned by the grammar.

| Role | Meaning |
|---|---|
| AGENT | Intentional initiator or doer |
| CAUSE | Non-agentive causer (entity, event, or state) |
| EXPERIENCER | Entity in a perceptual or mental state |
| UNDERGOER | Participant changed or affected (the thematic-role literature's "patient"; renamed to avoid clashing with the concept Patient) |
| THEME | Participant moved, transferred, located, or discussed, not necessarily changed |
| RECIPIENT | Receiver of a transfer or communication |
| BENEFICIARY | Party for whose benefit something is done |
| INSTRUMENT | Means used |
| SOURCE | Origin of motion, transfer, or information |
| GOAL | Destination or endpoint |
| LOCATION | Place of the situation |
| PATH | Route |
| TIME | When the situation holds |
| MANNER | How |
| PURPOSE | Intended outcome |
| CONTENT | Situation or proposition that is believed, said, wanted, or known |
| STIMULUS | What is perceived or reacted to |
| COMITATIVE | Co-participant |
| MEASURE | Quantity or degree |

**Tier 2: frame-specific roles.** Each frame defines its own roles. Every tier-2 role MUST declare the tier-1 role it specializes:

```text
EXAMINER          ⊑ AGENT
EXAMINED_ENTITY   ⊑ THEME
FOOD (in EAT)     ⊑ UNDERGOER
LESSOR            ⊑ AGENT      LESSEE ⊑ RECIPIENT
```

Why two tiers:
- Cross-frame queries ("all agents of any event") work through tier 1.
- Active/passive mapping rules (Part 8) are stated once at tier 1 and apply to every frame.
- Cross-domain analogy (Part 9) aligns roles through tier-1 parents.
- Compression (Part 11) is unaffected, since frames still define their own ordered role lists.

**Display convention.** Roles are printed with a `role:` prefix (`role:UNDERGOER`) and concepts with a `concept:` prefix. Stored IDs are in separate spaces, so there is no collision.

### RoleDefinition

```text
RoleDefinition
    header
    name, tier (1|2), parent_role      (tier 2 MUST name a tier-1 parent)
    expected_kind                       kind constraint
    expected_class                      class constraint (concept ID), optional
    requiredness                        REQUIRED | OPTIONAL
    cardinality                         (min, max)
    coercion_allowed                    registered coercion rule IDs, default none
```

### Value states and basis (Enhancement E-29)

Requiredness describes the frame. What an instance says about a role is a separate matter. The sources describe four unfilled-role situations in different places [F1-B §8.4; F3-A §6.7], and Part 3 gives them operational meaning. Each role binding in an instance carries one **value state**:

| Value state | Meaning |
|---|---|
| SPECIFIED | A value is given |
| UNSPECIFIED | The source does not express it. The system MUST NOT invent it. |
| UNKNOWN | The source states that it is unknown |
| NOT_APPLICABLE | The role does not apply to this situation |
| WITHHELD | Deliberately withheld or redacted |

A SPECIFIED binding also carries a **basis**: `EXPLICIT` (stated in the source), `GRAMMATICAL` (derived from syntax), or `BACKGROUND` (inferred from background knowledge) [F2-A §3.14]. A BACKGROUND binding MUST NOT be stored as source-stated. It is an inference with its own epistemic status.

A REQUIRED role may have value state UNSPECIFIED. The frame says the situation conceptually involves that participant, and the instance says the source did not name it. "John transferred money" leaves SOURCE and DESTINATION UNSPECIFIED, and nothing is invented [F1-B §8.4].

### Multiple roles per referent (Enhancement E-30)

One referent MAY fill several roles of one frame instance, unless the frame declares those roles disjoint. In "John gave Mary a book", John fills both AGENT and SOURCE. The sources' examples varied on whether the giver is "agent" or "source". Both are true, so the model allows both.

---

## 2.7 Properties and values

A property assertion is a standard compiled structure. The shorthand `CAR HAS_PROPERTY RED` is allowed in authoring but compiles to [F1-D §2.3]:

```text
PropertyAssertion
    bearer       referent or KIND(concept)
    property     concept of kind PROPERTY (e.g. COLOR)
    value        VALUE concept, QUANTITY literal, or other literal
    degree       optional (comparative or intensity)
    time         optional TIME
```

```text
CONCEPT: COLOR          kind = PROPERTY
    value_domain        enumeration of VALUE concepts, or a QUANTITY dimension
    bearer_constraint   permitted kinds/classes (soft; extensible)
```

Validation obligations:
- A VALUE (such as RED) MUST NOT be used where a PROPERTY is expected. The validator rejects it and offers the compiled form [F1-D §2.3].
- A value MUST be in the property's value domain.
- Measurements require a unit or declared scale ("37.5" alone is invalid) [F2-A §3.3].
- Bearer constraints are deliberately soft. Color applies to lights, images, and materials as well as physical objects, so a bearer-class constraint lists permitted classes and can be extended by versioned review [F1-D §2.3].

---

## 2.8 Relations

### RelationDefinition

```text
RelationDefinition
    header
    name
    category            LOGICAL | ASSOCIATIVE | EPISTEMIC
    domain, range       kind and class constraints
    arity               2 (n-ary situations use frames)
    logical_properties  reflexive/irreflexive, symmetric/asymmetric,
                        transitive, functional, inverse_of, sub_relation_of
    cycles_allowed      true | false
    reasoning_policy    OPEN_WORLD (default) | CLOSED_WORLD(scope)
    weight_semantics    ASSOCIATIVE only; see below
```

### Three categories [F1-D §2.15]

| Category | Examples | Weights allowed? | Semantics |
|---|---|---|---|
| LOGICAL | SUBCLASS_OF, INSTANCE_OF, PROPER_PART_OF | No | Formal; may support inference |
| ASSOCIATIVE | RELATED_TO, CO_OCCURS_WITH, CONTEXTUALLY_ASSOCIATED_WITH | Yes | Retrieval aid only |
| EPISTEMIC | POSSIBLY_CAUSES | No (uses evidence vector) | Requires evidence and uncertainty |

**Rule SG-KNW-002 (Normative).** An associative weight MUST record the scoring model that produced it (`model_id`, Enhancement E-32). It means "useful for retrieval under that model". It MUST NOT be read as probability, confidence, or logical validity [F1-D §2.15].

### Starter relation catalogue

| Relation | Category | Logical properties | Notes |
|---|---|---|---|
| SUBCLASS_OF | LOGICAL | reflexive, transitive | Mutual subclassing implies equivalent extensions under OWL-style semantics. It is flagged as a probable equivalence, not automatically an error [F1-D §2.9]. |
| PROPER_SUBCLASS_OF | LOGICAL | irreflexive, asymmetric, transitive | |
| INSTANCE_OF | LOGICAL | | Referent to concept |
| PROPER_PART_OF | LOGICAL | irreflexive, asymmetric, transitive | Idealized strict parthood [F1-D §2.9] |
| PHYSICAL_COMPONENT_OF | LOGICAL | specializes PROPER_PART_OF | [Provisional: transitivity per subtype needs domain review] |
| MATERIAL_PORTION_OF | LOGICAL | specializes PROPER_PART_OF | |
| ORGANIZATIONAL_MEMBER_OF | LOGICAL | not transitive | "Employee of Company" is not physical composition [F2-B §4.4] |
| INFORMATIONAL_COMPONENT_OF | LOGICAL | | |
| HAS_PART | LOGICAL | inverse_of PART_OF family | Inverses are derived, not stored twice (Part 11) |
| HAS_FUNCTION | LOGICAL | | To a FUNCTION concept (Part 4) |
| TYPICALLY_HAS | EPISTEMIC | defeasible | Typical properties, not exceptionless |
| KNOWS | LOGICAL | cycles_allowed = true | A valid social cycle [F1-D §2.9] |
| ASSOCIATED_WITH | ASSOCIATIVE | symmetric | Weighted |

Temporal relations (Allen's thirteen) and CAUSES are defined in Part 3.

**Cycle rules (Normative).** Cycles are allowed or forbidden per relation, not globally [F1-D §2.9]. The validator MUST reject a cycle in any relation declared `cycles_allowed = false`. Recursive structures MUST be referenced, not expanded, and traversal has a configurable depth limit [F1-D §2.8].

---

## 2.9 Concepts and their definitions

### Concept (identity only)

```text
Concept
    header
    kind                 semantic kind
    canonical_label      editable, not identity
    definition_status    COMPLETE | INCOMPLETE (provisional concepts only INCOMPLETE)
    registry data        domains (primary + additional), location refs (§2.13)
```

### ConceptDefinition (scoped and versioned)

A concept's meaning is given by definitions. A concept can have several, one per scope [F2-C §5.13, §5.23]. Examples: LIFE in biology versus philosophy, or water as chemical species versus ordinary substance.

```text
ConceptDefinition
    concept_id, definition_id, definition_version
    semantic_scope       domain context, theory, or ontology release
    constraints          partitioned into four classes (below)
    valid_from_release, superseded_by
    evidence refs
```

Constraints are partitioned [F2-C §5.5]:

| Class | Meaning | Inherited as |
|---|---|---|
| ESSENTIAL | Required by the chosen definition for every member | Logical implication |
| TYPICAL | Commonly associated, not required | Defeasible default |
| CONTINGENT | True of particular instances | Not stored at concept level |
| CONTEXTUAL | Applicable only in some circumstances | Conditional |

**Rule (Normative).** Only ESSENTIAL constraints are inherited as exceptionless logic. "Every car has four wheels" is TYPICAL, not ESSENTIAL [F2-B §4.2].

**Definition variants.** Where a broad concept has competing domain definitions that are not taxonomic subclasses (LIFE), the umbrella concept links to variant definitions through DEFINITION_VARIANT_OF. An assertion MUST record which definition it uses [F2-C §5.23].

---

## 2.10 The lexical layer

Words are not concepts. A word maps to concepts [F1-D §2.20; F1-A §3.4].

```text
LexicalEntry
    lemma, language, part_of_speech
    entry_kind        WORD | MULTI_WORD | IDIOM
    forms             inflected forms (optional)

LexicalSense
    entry_id, sense_no
    concept_ids       one or more candidates
    mapping           EXACT | BROADER | NARROWER | PARTIAL   (resource alignments, Part 8)
    domain_tags, register
    source_resource   e.g. WordNet synset ID
    context_cues      optional (cue lemma or concept, polarity, retrieval weight)
```

```text
bank  ──►  sense 1 ──► FINANCIAL_INSTITUTION
      └─►  sense 2 ──► RIVER_BANK
      └─►  sense 3 ──► STORAGE_FACILITY
```

Rules:
- A word MAY map to many concepts. A sense maps to one or more concepts when a resource's granularity differs.
- Context cues support disambiguation but never decide it (`bank` + `loan`). The ContextIntegrator makes the decision (Part 8).
- Different languages map their own entries onto the same concept IDs. This is how one concept dictionary serves Arabic, English, and others [F1-D §2.25].
- Idioms map either to a concept or to a figurative mapping (Part 3).
- A new word for an existing concept adds only a lexical mapping, not a concept [F1-A §3.12].

---

## 2.11 Situation descriptions and assertions

### FrameInstance is a description (Enhancement E-28)

A FrameInstance is a structured description of a situation. Its existence in the store does not assert that the situation occurred. F2-A §3.24 notes that a negated giving event should be "an event description inside a negated proposition rather than a real event record". This is generalized:

```text
FrameInstance
    header
    frame_id, frame_version
    bindings[]       (role_id, value_ref, value_state, basis)
    source_id, certificate_id
```

Descriptions can be nested inside beliefs ("John believes that…"), negations, hypotheticals, questions, and causal statements without ever being asserted as actual.

### Assertion

An assertion is a claim about content [F1-A §3.6; F2-A §3.13]:

```text
Assertion
    header
    content_ref        FrameInstance | Proposition | RelationApplication | PropertyAssertion
    operators          polarity, modality, tense/time, realization (Part 3)
    origin             SOURCE_TEXT | GRAMMATICAL | BACKGROUND_INFERENCE
                       | IMPORTED_RESOURCE | CURATED
    epistemic_status   axis D (§1.7.3)
    evidence_ref       evidence vector (Part 6)
    definition_ref     which concept definition(s) apply
    alternatives_group id when this is one of several retained interpretations (Part 3)
    source_id
```

Even ontology statements such as `DOG IS_A ANIMAL` are logically assertions. They have origin CURATED, IMPORTED_RESOURCE, or SOURCE_TEXT. For storage efficiency, Part 11 stores definitional edges in compact edge tables with an optional assertion pointer.

---

## 2.12 Sources, spans, and language annotation

### Source and Span (Enhancement E-14, E-26)

```text
Source
    id, type (DOCUMENT | SENTENCE | RESOURCE | CURATED | HUMAN_INPUT)
    text_hash, uri, language
    anchor            document_date, time_zone, calendar, speech_time (optional)
    publication_context
    trust_tier        QUARANTINE | STANDARD | TRUSTED (Part 6)
    stored_text       immutable once registered

Span
    source_id, start, end     zero-based, end-exclusive
```

Why the anchor: "yesterday" cannot become a calendar date without a reference time [F1-A §3.13; F2-A §3.12]. The Source carries the anchor, and unresolved relative expressions stay unresolved until it is applied (Part 3).

Offsets (E-26): the sources specify zero-based, end-exclusive offsets [F3-B §7.5] but not the unit. Offsets are counted in Unicode code points over the exact stored text, which is immutable once registered. This keeps spans stable across processing runs and across languages with combining characters.

### Language annotation (Enhancement E-21, E-31)

Languages differ in tense, aspect, definiteness, evidentiality, and other distinctions [F1-D §2.25]. Reversible mode also needs wording, such as "gave" versus "handed" [F1-A §3.15].

```text
LanguageAnnotation   (attached to a Referent, FrameInstance, or Assertion)
    language, features{}   e.g. voice, tense, aspect, mood, evidentiality,
                           definiteness, number, honorific, information_structure,
                           lexical_choice
    span
```

Feature names follow Universal Dependencies where applicable [F3-C §8.6].

**Boundary rule SG-CON-004 (Normative, E-31).** A feature that changes truth conditions or commitments (tense, modality, negation, evidentiality that changes who vouches for a claim) MUST be represented in the grammar's operators (Part 3). It MAY additionally be recorded as an annotation. A feature that only affects style or reconstructibility (word order, emphasis, lexical choice) lives only in the annotation, and the core is identical with or without it.

---

## 2.13 Registry, domains, and versions

### Global Concept Registry

A lightweight index only. It locates knowledge and does not duplicate it [F1-C §8; F2-C §5.21].

```text
RegistryEntry
    id (any space), record_kind, canonical kind
    domains               primary + additional (many-to-many, non-semantic tags)
    location refs         which store/partition holds detailed relations
    version, validation status
    lexical index refs, embedding refs, structural-signature refs
```

Domain-specific relations carry a domain tag: `(source_id, relation_id, target_id, domain_id)` [F1-D §2.14]. The same concept ID, such as ENERGY, is shared across Physics, Biology, and Engineering. Each domain keeps its own relations to it [F1-D §2.13].

### Versioning (Enhancement E-18)

| Versioned thing | Scheme |
|---|---|
| Grammar (kinds, expression syntax, operator semantics, core roles) | `major.minor.patch` |
| OntologyRelease | Snapshot ID (date-based) over concepts, relations, definitions |
| FrameDefinition, RuleDefinition, ConceptDefinition | Integer per item |
| Content hash | Per definition version (duplicate detection only) |

Compatibility classes:
- **PATCH:** no semantic change (label, documentation).
- **MINOR:** additive (new optional role, new frame, new concept, new relation).
- **MAJOR:** changes meaning (role removed or retyped, definition narrowed, kind added).

Rules:
- Records pin the versions they were built with (`frame_id, frame_version`). Old versions remain resolvable [F2-B §4.25; F3-A §6.19].
- A change to a concept's defining constraints is MAJOR and requires compatibility evaluation and review of affected references (SG-GOV-001, F2-C §5.20). Adding a non-defining fact is MINOR.
- A **MigrationRecord** links `from_ref → to_refs` with relation `REFINED_INTO`, `SPLIT`, `MERGED_INTO`, `SUPERSEDED_BY`, or `DEPRECATED`. Each affected record is marked `NOT_REVIEWED`, `AUTO_MIGRATED`, `REVIEWED`, or `REPROCESS_REQUIRED` [F2-C §5.24].
- The system never silently rewrites old references.

---

## 2.14 Equivalence and external mappings

**EquivalenceMapping** (reversible, versioned; SG-IDN-003) [F2-C §5.12]:

```text
EquivalenceMapping
    from_id → to_id (canonical), relation: EQUIVALENT | SUBSUMED_BY | OVERLAPS | RELATED | DISJOINT
    scope, evidence, rules_applied, status, version, reversible = true
```

Both original records are kept. The canonical ID is used for the approved scope. Part 7 defines the decision procedure.

**ExternalMapping** [F3-C §8.8]:

```text
ExternalMapping
    internal_id, resource (WordNet, FrameNet, VerbNet, PropBank, AMR, Wikidata, ConceptNet)
    external_id, relation: EXACT | BROADER_THAN | NARROWER_THAN | PARTIAL_OVERLAP
                          | RELATED_DISTINCT | UNRESOLVED
    provenance, licence note
```

External identifiers are never treated as interchangeable with internal IDs.

---

## 2.15 Logical model versus physical storage

[F1-D §2.4, §2.5, §2.24]

- Python classes are thin **accessor interfaces** over compact records. They are not the permanent in-memory form of millions of concepts, because per-object memory overhead is large.
- The authoritative store is relational (SQLite initially, Part 11). The graph is the logical model, with nodes and edges in relational tables.
- Optional sparse structures (CSR arrays) are built only for active subgraphs, never for the whole database [F1-D §2.14].
- Hybrid layering: Python interface → semantic frame model → typed graph model → database/arrays. Any layer can be replaced without changing the layers above.

---

## 2.16 Worked example: records for one sentence

Sentence (processed on 2026-10-16, source anchor = that date):

> The young doctor gave the patient two tablets yesterday.

Concept IDs follow the illustrative numbers in F1-A §3.13 (Doctor 101, Patient 102, Tablet 103, Transfer 201, Young 301). The frame is shown as GIVE, a specialization of Transfer defined in Part 4.

```text
SOURCE        S1      anchor.document_date = 2026-10-16

REFERENT      R1      kind=ENTITY  instance_of=[Doctor(101)]   SPECIFIC  span[4,16)
REFERENT      R2      kind=ENTITY  instance_of=[Patient(102)]  SPECIFIC
REFERENT      R3      kind=ENTITY  instance_of=[Tablet(103)]   PLURAL cardinality=2

PROPERTYASSERTION  PA1  bearer=R1  property=AGE_GROUP  value=Young(301)

FRAMEINSTANCE  I1     frame=GIVE v1
   role:AGENT        = R1  (SPECIFIED, EXPLICIT)
   role:SOURCE       = R1  (SPECIFIED, GRAMMATICAL)    ← same referent in two roles
   role:RECIPIENT    = R2  (SPECIFIED, EXPLICIT)
   role:THEME        = R3  (SPECIFIED, EXPLICIT)
   role:TIME         = TIME(YESTERDAY, relative, anchor→S1)   unresolved until applied
   (nothing is stated about how the tablets were handed over, so no role invented)

ASSERTION      A1     content=I1  polarity=POSITIVE  tense=PAST (Part 3)
               origin=SOURCE_TEXT  epistemic_status=SOURCE_ASSERTED
LANGUAGEANNOTATION  L1  language=en  voice=active  definiteness(R1)=definite
```

Observations (no new content, only what the model enforces):
- No concept is stored with the individual doctor's properties. Doctor stays a type.
- The sentence does not establish whether the tablets were handed over or administered. The frame does not claim more than the source says.
- The tablets' count is `cardinality=2` on the referent, not a role binding.

---

## 2.17 Data-model invariants

A store is well-formed only if all invariants hold. Part 5 maps each to a validation rule.

| ID | Invariant |
|---|---|
| I-01 | Every record has a header with ID, record kind, status, and version |
| I-02 | Every reference resolves, possibly to a tombstone |
| I-03 | IDs are never reused or reassigned |
| I-04 | Every tier-2 role has a tier-1 parent |
| I-05 | Every frame instance binding names a role that its frame version defines |
| I-06 | No bare concept ID fills a role. Referent, literal, kind-reference, or nested description only (SG-CON-003). |
| I-07 | No provisional ID appears in a trusted record |
| I-08 | Every assertion has a source or an authorized origin, and an evidence reference |
| I-09 | Every span lies within its source's stored text |
| I-10 | Relations declared acyclic contain no cycles |
| I-11 | Property values lie in the property's value domain. Measurements carry units. |
| I-12 | Every record pins a grammar version and ontology release |
| I-13 | No merged or equivalent concept is deleted. A tombstone and mapping exist (SG-IDN-003). |
| I-14 | Process-history records contain no world-knowledge assertions, and vice versa (P-24) |

---

## 2.18 Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-26 | Span offsets had no stated unit | Unicode code points over immutable stored text (§2.12) |
| E-27 | "Semantic types" conflated fixed kinds with ontology classes | Fixed kinds vs growing classes (§2.2) |
| E-28 | A frame instance could be mistaken for an occurred event | FrameInstance is a description. Only an Assertion makes a claim (§2.11) |
| E-29 | Four unfilled-role situations described in three places | Single value-state set plus basis (§2.6) |
| E-30 | Giver treated as either agent or source | A referent may fill several roles (§2.6) |
| E-31 | No rule decided which language features enter the core | Truth-conditional features in operators, others in annotation (§2.12) |
| E-32 | Association weights were unattributed | Weights record the scoring model (§2.8) |

Earlier enhancements E-04, E-05, E-14, E-18, E-21 are now specified here.



---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 3 of 12: The Formal Grammar v1.0

This part defines the expression language: how meanings are constructed from the records of Part 2. The v0.1 grammar in the sources [F2-A §3.23] left twelve items open, and §3.22 closes each one. The grammar is a construction language. It says how meanings are built. Part 5 says how builds are checked.

---

## 3.1 Position and design

**Natural-language grammar describes how meanings are expressed. Semantic grammar describes how meanings are structured** [F2-A §3.1]. USG therefore does not reproduce English, Arabic, or any other syntax. Active and passive sentences, and sentences in different languages, can compile to the same expression.

The grammar keeps the five construction families of v0.1 and adds the pieces the sources named but did not define.

| Family | v0.1 | v1.0 |
|---|---|---|
| Reference | REF | REF, KIND, VAR (§3.2) |
| Literal | LIT | LIT with units and value types |
| Application | APPLY | APPLY plus RELATE and PROPERTY (relation and property application, a gap in v0.1) |
| Operator | NOT, AND, OR, IMPLIES, EXISTS, FOR_ALL | The full catalogue of §3.5 |
| Binding | BIND | Quantifier binders and the Q construct |
| (new) Ambiguity and error | none | ALT, ERROR (§3.14) |
| (new) Annotation channel | none | Provenance on every node (§3.16) |

**Frames over triples** (decided, not changed) [F2-A §3.4]. APPLY is the primary construction. Binary ontology relations such as IS_A are still first-class through RELATE. Everything is stored and queried as a typed graph (Part 2, §2.15).

**Why not a single generic APPLY** [F2-A §3.22]. A one-construct grammar would need extra tags to tell literals from concepts and events from propositions, which raises validation cost. The five-family grammar is retained. §3.20 gives the selection procedure.

---

## 3.2 Abstract syntax (v1.0)

Notation: `X ::= A | B` is a choice, `X+` is one or more, `[X]` is optional. Operator names are uppercase. The authoring syntax is functional (`APPLY(F, {…})`), and the stored form is the typed record structure of Part 2.

```text
ASSERTION  ::= ASSERT( PROP , META )
META       ::= { origin, epistemic_status, evidence_ref, source_id,
                 definition_refs, alternatives_group }          -- Part 2 §2.11

-- Expressions are classified by SORT (§3.3):  TERM | SIT | PROP | VAL | TIME

PROP ::= HOLDS( SIT )
       | RELATE( RelationID , TERM , TERM )
       | PROPERTY( TERM , PropertyID , VAL [, DEGREE] )
       | NOT( PROP ) | AND( PROP+ ) | OR( PROP+ )
       | IMPLIES( PROP , PROP )
       | COND( PROP , PROP ) | COUNTERFACTUAL( PROP , PROP )
       | Q( QUANT , VAR , PROP , PROP [, DOMAIN] )     -- restrictor, scope
       | MODAL( FORCE , FLAVOR , PROP )
       | TENSE( TenseID , TIME , PROP )
       | TEMPORAL( AllenRel , TIME , TIME )
       | ATTRIBUTE( TERM , EvidentialMode , PROP )
       | SAME_AS( TERM , TERM [, IdScope] ) | DIFFERENT_FROM( TERM , TERM )
       | DIRECT( TERM , SIT )
       | FIG( MappingID , Expr , Expr )
       | ALT( GroupID , ( PROP , Support )+ )

SIT  ::= APPLY( FrameID@ver , BINDINGS )
       | ASPECT( AspectID , SIT )
       | COMPOSE( CompKind , SIT+ , [DEPENDENCIES] )
       | ALT( ... )

BINDINGS ::= { RoleID : FILLER , ... }
FILLER   ::= TERM | SIT | PROP | VAL | TIME | HOLE
HOLE     ::= UNSPEC | UNKNOWN | NOT_APPLICABLE | WITHHELD   -- Part 2 §2.6

TERM ::= REF( ReferentID ) | KIND( ConceptID ) | VAR( name )
       | REIFY( SIT | PROP )  | ALT( ... )
VAL  ::= LIT( value , ValueType [, unit] ) | REF( value-concept ) | ALT( ... )
TIME ::= TIME_LIT( instant | interval | duration | partial )
       | TIME_REL( RelExpr , anchor ) | EXTENT( SIT ) | SPEECH_TIME( source )
       | UNRESOLVED_TIME( text_span ) | ALT( ... )

QUANT  ::= EXISTS | FORALL | NO | EXACTLY(n) | AT_LEAST(n) | AT_MOST(n)
         | MOST | MANY | FEW | GEN
FORCE  ::= POSSIBILITY | NECESSITY
FLAVOR ::= EPISTEMIC | DEONTIC | DYNAMIC | CIRCUMSTANTIAL
IdScope ::= DISCOURSE | RESOLVED_WORLD | WITHIN( ATTRIBUTE-context )

-- Any node MAY carry  @ann{ spans, rule_ids, basis, language_features }   (§3.16)
-- ERROR( code , span , detail )  is a legal node only in CANDIDATES (§3.14)
```

---

## 3.3 Sorts and well-typedness

### 3.3.1 Sorts

Every expression has one **sort**. Sorts align with the semantic kinds of Part 2, §2.2.

| Sort | Denotes | Kinds |
|---|---|---|
| TERM | A participant or thing | ENTITY, and reified situations used as entities |
| SIT | A described situation (not necessarily actual) | EVENT, STATE, PROCESS |
| PROP | A truth-evaluable content | PROPOSITION |
| VAL | A value or quantity | VALUE, QUANTITY |
| TIME | A temporal object | TIME |

**Rule SG-CON-006 (sort discipline).** Operators accept only the sorts in their signatures. A conversion between sorts is explicit. HOLDS takes SIT to PROP, REIFY takes SIT or PROP to TERM, and EXTENT takes SIT to TIME. The authoring shorthand may omit HOLDS in `ASSERT(APPLY(...))`, and the canonicalizer inserts it (SG-CAN-001).

**Role fillers match the role's expected kind** (Part 2, §2.6):
- ENTITY expected → TERM
- EVENT/STATE/PROCESS expected → SIT
- PROPOSITION expected → PROP (CONTENT roles)
- VALUE/QUANTITY expected → VAL
- TIME expected → TIME

### 3.3.2 Three-valued type compatibility (Enhancement E-34)

F2-A §3.5 defines a frame application as well-typed when every bound value's type satisfies `Type(vᵢ) ⪯ Tᵢ`. F2-C §5.7 requires open-world reasoning. A two-valued check conflicts with that, because a referent whose class is simply unknown would be rejected. The check is therefore three-valued.

For each binding with expected kind `Kᵢ` and expected class `Tᵢ`:

| Result | Condition |
|---|---|
| COMPATIBLE | kind matches, and a class of the value is a subclass of `Tᵢ` (via the IS_A closure) |
| INCOMPATIBLE | kind mismatch, or the value's classes are provably disjoint from `Tᵢ` (DISJOINT_WITH) |
| UNDETERMINED | kind matches, but class membership in `Tᵢ` is neither derivable nor refutable |

**Rule SG-TYP-001 (revised).** A frame application MUST NOT contain an INCOMPATIBLE binding unless a registered coercion or figurative mapping applies (SG-TYP-002). UNDETERMINED bindings are accepted at L2 with a recorded type-warning, and they raise review priority (Part 6). Missing class information is never treated as incompatibility (SG-KNW-001).

Example: `EAT(EATER = NUMBER_7, FOOD = EQUATION)` is INCOMPATIBLE (abstract entities are disjoint from AnimateEntity), so the figurative path is searched. `EAT(EATER = R5, ...)` where R5 has no class yet is UNDETERMINED, and the interpretation continues with a warning.

---

## 3.4 Application constructs

### 3.4.1 APPLY (frame application)

`APPLY(F@v, {role: filler, …})` describes a situation of frame `F`. It denotes a SIT. It does not claim the situation occurred. HOLDS makes that claim, and ASSERT wraps it with provenance (Part 2, §2.11).

Well-formedness (SG-CON-002, from SG-FRAME-001 in F3-C §8.18):
1. The frame exists in the pinned version.
2. Every bound role is defined by that frame version, or inherited.
3. Every REQUIRED role has a binding. UNSPEC is allowed and is the rule's escape for implicitly unexpressed participants.
4. Cardinality limits hold.
5. Each binding passes §3.3.2 and the role's constraints (§3.19).
6. A referent MAY fill several roles unless the frame declares them disjoint (Part 2, §2.6).

Roles in bindings use tier-2 names when the frame defines them and carry their tier-1 parent implicitly.

### 3.4.2 RELATE and PROPERTY

- `RELATE(r, a, b)` applies a binary relation from the Part 2 catalogue. Admissibility follows the relation's domain and range. Inverses are normalized by the canonicalizer (PART_OF → HAS_PART direction is chosen per relation definition).
- `PROPERTY(bearer, p, v[, degree])` is the compiled property assertion of Part 2, §2.7. The shorthand `CAR HAS_PROPERTY RED` is expanded by the canonicalizer, and `RED` used where a property is expected is a sort error.

### 3.4.3 Names and strings

`LIT(text, Text)` is data. A proper name such as "John" is not a concept and is not a bare literal in a role. It produces a referent plus `PROPERTY(R, NAME, LIT("John", Text))`. This keeps type/token separation (SG-CON-003).

---

## 3.5 Operator catalogue

Denotations are given as sketches relative to an **evaluation context** `c = (M, g, t₀)`: a world model `M`, a referent/variable assignment `g`, and the source's time anchor `t₀`. A full model theory is out of scope for v1.0. Each operator is nonetheless fixed by signature, meaning, scope behaviour, and validation hooks, which closes F2-A §3.23 item 2.

| Operator | Signature | Meaning |
|---|---|---|
| HOLDS | SIT → PROP | True in `c` iff a situation of the described type, with the bound participants, obtains (is actual) in `c`. |
| RELATE | (Rel, TERM, TERM) → PROP | The relation holds between the two terms in `c`. |
| PROPERTY | (TERM, Prop, VAL[, DEGREE]) → PROP | The bearer has the property with the value (and degree) in `c`. |
| NOT | PROP → PROP | True iff the argument is not true in `c`. It asserts nothing about alternatives, and it does not turn a description into the opposite situation. |
| AND, OR | PROP+ → PROP | Conjunction and (inclusive) disjunction. |
| IMPLIES | (PROP, PROP) → PROP | Material implication. Used for formal rules and logical content. |
| COND | (PROP, PROP) → PROP | Natural-language conditional: the consequent holds in the relevant contexts where the antecedent holds. It is not truth-functional and may be defeasible. |
| COUNTERFACTUAL | (PROP, PROP) → PROP | The conditional with a false or non-actual antecedent. |
| Q | (QUANT, VAR, PROP, PROP[, DOMAIN]) → PROP | Restricted quantification (§3.7). |
| MODAL | (FORCE, FLAVOR, PROP) → PROP | Possibility or necessity over contexts accessible under the flavor (§3.8). |
| TENSE | (Tense, TIME, PROP) → PROP | Relates the situation's temporal extent to the reference time (§3.9). |
| ASPECT | (Aspect, SIT) → SIT | Selects the temporal view of a situation: perfective, imperfective, progressive, perfect, habitual, prospective (§3.9). |
| TEMPORAL | (AllenRel, TIME, TIME) → PROP | The named interval relation holds (§3.9). |
| ATTRIBUTE | (TERM, Mode, PROP) → PROP | The content holds according to the source term, by the stated mode (belief, report, perception, inference, hearsay). It creates an opaque context. The author is not committed to the content (§3.12). |
| SAME_AS, DIFFERENT_FROM | (TERM, TERM[, IdScope]) → PROP | Identity or distinctness of referents within the stated scope. |
| DIRECT | (TERM, SIT) → PROP-as-directive | A directive to the addressee to bring about the situation. It is prescriptive and is never a description of what happened (§3.18). |
| FIG | (Mapping, Expr, Expr) → PROP | A recorded figurative or coerced reading linking the literal expression to the intended one (§3.15). |
| ALT | (Group, (X, Support)+) → sort of X | Retained alternatives. Exactly one is intended, and which one is not determined (§3.14). |
| COMPOSE | (CompKind, SIT+, deps) → SIT | A composite process built from smaller situations (§3.18). |
| REIFY | SIT or PROP → TERM | Treats a situation or proposition as an entity ("the destruction of the city", "the claim that…"). |
| EXTENT | SIT → TIME | The temporal extent of a situation. |
| SPEECH_TIME | Source → TIME | The source's anchor time. |

Attitudes and communication (believe, know, say, want, intend) are **frames with a CONTENT role**, not operators. They nest recursively: BELIEVE contains KNOW contains CANCEL [F1-D §2.8; F2-A §3.3]. Only structural operations (negation, quantification, modality, time, attribution) are operators.

---

## 3.6 Variables, binders, and scope (closes item 3)

**Binders.** Q binds one variable. The restrictor and the scope are two separate PROP arguments, so "every apple" does not quantify over everything. The variable is visible in both.

**Rules:**

| ID | Rule |
|---|---|
| SG-CON-005a | **Closed assertions.** A stored ASSERT contains no free VAR. A free variable is a validation failure. |
| SG-CON-005b | **No shadowing.** A binder MUST NOT rebind a variable already in scope. |
| SG-CON-005c | **Alpha-equivalence.** Variables are renamed canonically by order of binding, so structurally equal expressions are equal. |
| SG-CON-005d | **Referents are not variables.** Discourse referents are constants scoped to the source. Only quantifier-bound items use VAR. |
| SG-CON-005e | **Anaphora under a binder.** A pronoun whose antecedent is quantified refers to the bound VAR, within the binder's scope. Outside that scope it fails coreference resolution and is returned as UNRESOLVED or ALT, not silently attached to a referent. |

**Restrictor visibility.** A variable introduced in the restrictor is visible in the scope. This handles "Every farmer who owns a donkey beats it" without extra machinery.

---

## 3.7 Quantification and negation (closes item 4)

### 3.7.1 Quantifier catalogue (Enhancement E-35)

F2-A defined only EXISTS and FOR_ALL, unrestricted. That cannot express "two tablets", "most", or generic statements.

| Quantifier | Meaning |
|---|---|
| EXISTS | At least one individual satisfies restrictor and scope |
| FORALL | Every individual satisfying the restrictor satisfies the scope |
| NO | No individual satisfies both |
| EXACTLY(n), AT_LEAST(n), AT_MOST(n) | Cardinal quantifiers with n a literal |
| MOST, MANY, FEW | Vague quantifiers. A threshold is context-dependent, so any numeric bound from the source is recorded and none is invented. |
| GEN | Generic: "Dogs bark". Normal or characteristic, tolerant of exceptions. It is not FORALL. |

**Rule SG-GEN-003.** A GEN assertion MUST NOT be reported or used as an exceptionless universal. The "Every bird can fly" / "Penguins cannot fly" problem is handled this way: the first is stored as a source-asserted FORALL or GEN as written by the source, with status SOURCE_ASSERTED, and is never promoted to ontological law (SG-GEN-002, P-05) [F1-D §2.26].

### 3.7.2 Contextual domain

`DOMAIN` restricts the quantifier to a contextually salient set ("every apple in the bowl"). If the source implies a domain that the interpreter cannot determine, DOMAIN is UNSPEC. It is never defaulted to "everything in the world".

### 3.7.3 Negation

Negation applies to a PROP, and negated frames are never stored as occurred events [F2-A §3.10; F2-A §3.24]:

```text
"John did not eat the apple."
ASSERT( NOT( HOLDS( APPLY(EAT, {AGENT: R1, UNDERGOER: R2}) ) ) )
```

The three forms below are distinct and must not be confused:

| Sentence | Structure |
|---|---|
| John did not eat every apple | `NOT( Q(FORALL, x, apple(x), HOLDS(EAT(R1, x))) )` |
| John ate no apple | `Q(NO, x, apple(x), HOLDS(EAT(R1, x)))` |
| John did not eat any apple | `NOT( Q(EXISTS, x, apple(x), HOLDS(EAT(R1, x))) )` |

The second and third are logically equivalent. They are kept separate because the source construction differs, and the canonicalizer may normalize them only under a declared preservation scope (SG-CAN-001).

**Scope ambiguity.** `NOT>FORALL` is the default reading for the first sentence. The alternative `FORALL>NOT` is retained as an ALT only when the evidence supports it (§3.14). The interpreter does not choose arbitrarily.

---

## 3.8 Modality, attitudes, evidentiality, directives (closes item 5, part 1)

### 3.8.1 Modality: force × flavor (Enhancement E-33)

F2-A §3.11 proposes five categories: POSSIBILITY, NECESSITY, OBLIGATION, PERMISSION, INFERENCE. They are two dimensions mixed together. The grammar uses the two dimensions, and the source's five categories become derived labels:

| Source category | FORCE | FLAVOR |
|---|---|---|
| POSSIBILITY | POSSIBILITY | CIRCUMSTANTIAL or EPISTEMIC |
| NECESSITY | NECESSITY | CIRCUMSTANTIAL |
| OBLIGATION | NECESSITY | DEONTIC |
| PERMISSION | POSSIBILITY | DEONTIC |
| INFERENCE | NECESSITY | EPISTEMIC |
| (new) ABILITY | POSSIBILITY | DYNAMIC |

"Must" is ambiguous between DEONTIC and EPISTEMIC. "John must leave tomorrow" and "John must be home by now" differ exactly there [F2-A §3.11]. The ContextIntegrator selects the flavor, and when the evidence does not settle it, an ALT retains both.

```text
"John may leave tomorrow."
ASSERT( ALT(g1,
  [ MODAL(POSSIBILITY, EPISTEMIC,  TENSE(FUTURE, SPEECH_TIME, HOLDS(LEAVE(AGENT: R1, TIME: tomorrow)))), rank 1
  , MODAL(POSSIBILITY, DEONTIC,    TENSE(FUTURE, SPEECH_TIME, HOLDS(LEAVE(AGENT: R1, TIME: tomorrow)))), rank 2 ] ) )
```

Modality is first-class. It MUST NOT be stored as optional English text labels [F2-A §3.11].

### 3.8.2 Factive and presuppositional frames (Enhancement E-40)

A frame definition MAY declare a presupposition (for example KNOW presupposes its CONTENT).

**Rule SG-EVD-004.** The presupposed content is emitted as a separate assertion **inside the same embedding context** as its trigger, with basis GRAMMATICAL. The source commits to it, so its status is SOURCE_ASSERTED, never VERIFIED. In "John believes Mary knows the meeting was cancelled", the cancellation is presupposed inside John's belief context. It is not asserted about the world.

```text
"John believes that Mary knows that the meeting was canceled."
HOLDS( APPLY(BELIEVE, { EXPERIENCER: R1,
   CONTENT: HOLDS( APPLY(KNOW, { EXPERIENCER: R2,
       CONTENT: TENSE(PAST, SPEECH_TIME, HOLDS(APPLY(CANCEL, {UNDERGOER: R3}))) })) }) )
   + presupposed (inside BELIEVE context, basis=GRAMMATICAL):
     TENSE(PAST, SPEECH_TIME, HOLDS(APPLY(CANCEL, {UNDERGOER: R3})))
```

### 3.8.3 Evidential and attribution operator

`ATTRIBUTE(source, mode, p)` records who holds the content and how: BELIEF, REPORT, PERCEPTION, INFERENCE, HEARSAY, or EVIDENTIAL_MARKER (from languages that mark evidentiality). "John said it rained" is `HOLDS(SAY(AGENT: R1, CONTENT: it-rained))`, and the author is not committed to rain. The commitment holder of every assertion is recorded in META (Part 6).

### 3.8.4 Directives and speech acts

`DIRECT(addressee, SIT)` is prescriptive. Questions and other speech acts are reserved extension points (MINOR grammar addition, Part 2, §2.13). Version 1.0 specifies assertions and directives only [Provisional].

---

## 3.9 Time (closes item 5, part 2)

### 3.9.1 TIME values

| Form | Example | Notes |
|---|---|---|
| Instant | 2026-10-15T14:00 | With time zone and calendar |
| Interval | 2026-10-01 to 2026-10-31 | Closed or open ends |
| Duration | PT2H | |
| Partial | "in March" | Month-of-unspecified-year |
| Relative | `TIME_REL(YESTERDAY, anchor)` | Unresolved until the anchor is applied |
| Vague | "recently", "earlier" | Kept as vague expressions, never invented as dates |
| Unresolved | `UNRESOLVED_TIME(span)` | The interpreter could not determine it |

**Resolution is deterministic and separate.** `RESOLVE_TIME(expr, anchor, calendar)` is a Python function. It returns an interval or UNRESOLVED. A resolved value is stored alongside the original relative expression (basis GRAMMATICAL), never in place of it. "Yesterday" relative to a document dated 2026-10-16 resolves to 2026-10-15 [F1-A §3.13; F2-A §3.12]. Without an anchor, it stays unresolved.

### 3.9.2 Allen's thirteen interval relations

Events with duration relate through `TEMPORAL(rel, t₁, t₂)` where `rel` is one of:

`BEFORE`, `AFTER`, `MEETS`, `MET_BY`, `OVERLAPS`, `OVERLAPPED_BY`, `STARTS`, `STARTED_BY`, `DURING`, `CONTAINS`, `FINISHES`, `FINISHED_BY`, `EQUALS`.

The sources named only some of these [F2-A §3.12]. The full set is required for sound composition and inverse reasoning. Each relation has its converse.

### 3.9.3 Tense and aspect

Tense relates the situation's extent to a **reference time**, which defaults to the source's speech time but may be shifted by discourse ("when Mary left"). Aspect selects the temporal view of the situation.

```text
"John arrived before Mary left."
TEMPORAL(BEFORE, EXTENT(ARRIVE(AGENT: R1)), EXTENT(LEAVE(AGENT: R2)))

"John had already arrived when Mary left."
TENSE(PAST, EXTENT(LEAVE(AGENT: R2)),
   HOLDS( ASPECT(PERFECT, ARRIVE(AGENT: R1)) ) )
   + TEMPORAL(BEFORE, EXTENT(arrive), EXTENT(leave))
```

The second form records both the aspectual and the temporal-order information [F2-A §3.12].

---

## 3.10 States, state change, and outcomes

### 3.10.1 State semantics belong to frames

A frame definition (Part 4) declares general state-change semantics: participants, initial state, final state, and process. An instance records only what the source states. "The water froze":

```text
HOLDS( TENSE... APPLY(FREEZE, { UNDERGOER: R1,
          FINAL_STATE: PROPERTY-value(PHASE = SOLID),
          INITIAL_STATE: UNSPEC }) )
```

The system MUST NOT invent an initial temperature or phase [F2-A §3.9]. Frame-level entailments (freezing involves transition toward solid) are derivable. They are marked INFERRED, derived on demand, and not stored (Part 11, inference compression).

### 3.10.2 Four kinds of consequence (Normative)

[F2-A §3.8]

| Kind | Meaning | Stored as |
|---|---|---|
| Precondition | Needed for the action to succeed under the model | In the frame definition |
| Effect | State change expected from a successful completion | In the frame definition |
| Typical outcome | Common consequence, not guaranteed | In the frame definition, defeasible |
| Observed outcome | A change established by evidence | A separate assertion about the instance |

An attempted action does not imply its effect. "John tried to open the door" does not imply "The door opened."

### 3.10.3 Realization, attempts, offers (refines Enhancement E-06)

Part 1 listed a realization-status modifier. The refined design avoids a free-floating modifier:

1. **Distinct frames** for non-completed actions: ATTEMPT, OFFER, PROMISE, INTEND, and similar. Each has a CONTENT role holding an unasserted SIT. "John offered Mary a book" is `OFFER(AGENT: R1, RECIPIENT: R2, CONTENT: GIVE(...))`. It is never normalized to a completed GIVE.
2. **Aspect** (§3.9.3) covers ongoing and completed views (progressive versus perfective).
3. **Embedding** (negation, modality, attribution) shows non-actuality structurally.

A bare asserted `HOLDS(APPLY(...))` claims the situation occurred, for frames whose definition makes completion the default.

---

## 3.11 Causation and explanation

Causal and explanatory links are frames, so they nest and carry roles:

```text
FRAME CAUSATION  roles: CAUSE (SIT|PROP), EFFECT (SIT|PROP),
                        MECHANISM (optional), CAUSE_TYPE
CAUSE_TYPE ∈ { DIRECT, ENABLING, PREVENTING, EXPLANATORY_REASON, PURPOSE }
```

"Because" usually produces EXPLANATORY_REASON, where the explanation is stated by the source, not independently diagnosed [F1-D §2.22 Stage E]. The three epistemic readings stay separate [F2-A §3.13]:

| Reading | Where it lives |
|---|---|
| Source-stated | Origin = SOURCE_TEXT, status SOURCE_ASSERTED |
| Inferred | Origin = BACKGROUND_INFERENCE, status INFERRED |
| Verified | Status VERIFIED, with independent evidence (Part 6) |

"The engine overheated, causing the car to stop" becomes `CAUSATION(CAUSE: OVERHEAT(R1), EFFECT: STOP(R2))` with origin SOURCE_TEXT. The grammar does not claim the mechanism is true.

---

## 3.12 Equality, identity, and opaque contexts (closes item 6; Enhancements E-19, E-38)

**Operators.** `SAME_AS(a, b, scope)` and `DIFFERENT_FROM(a, b)`.

**Properties.**
- `SAME_AS` is an equivalence relation within its scope.
- Coreference inside one source is a set of SAME_AS links with scope DISCOURSE. Each link is a validated claim with evidence (Part 2, §2.5). It is not a silent merge.
- A `RESOLVED_WORLD` identity (two descriptions of one real car) requires RESOLVE_INDIVIDUAL (Part 7).
- Concept identity is not expressed in the grammar. It lives in EquivalenceMapping at registry level (Part 7).

**Opaque contexts.** Substitution of identical referents is not valid inside an ATTRIBUTE context.

**Rule SG-KNW-003.** An identity `SAME_AS(a, b)` that holds in the author's context MUST NOT be propagated inside another agent's attitude context, and an identity inside an attitude context MUST NOT be propagated outward. "John believes Clark Kent is not Superman" stores `DIFFERENT_FROM(R_clark, R_super)` inside John's belief context only.

---

## 3.13 Unknown and missing values (closes item 9)

Four distinct things are never conflated:

| Situation | Representation |
|---|---|
| The source does not express a participant | Role binding `UNSPEC` |
| The source states it is unknown ("someone took it, nobody knows who") | Role binding `UNKNOWN` |
| The role does not apply | `NOT_APPLICABLE` |
| Deliberately withheld or redacted | `WITHHELD` |

An indefinite ("someone left") is different from UNSPEC. It **introduces a referent** with an existential commitment, but its identity is unspecified. UNSPEC means the frame role was never mentioned.

Open-world is the default (SG-KNW-001). A closed-world policy applies only where a relation or domain store explicitly declares `CLOSED_WORLD(scope)`. The absence of an assertion is not evidence of falsity. The same applies to concept comparison (Part 7).

---

## 3.14 Ambiguity and error representation (closes item 12; Enhancement E-39)

### 3.14.1 ALT

`ALT(group, [(X₁, support₁), …, (Xₙ, supportₙ)])` represents n **mutually exclusive** readings of the same sort. Example (PP attachment, F1-A §3.7):

```text
"John saw the man with a telescope."
ALT(g2,
  [ HOLDS(SEE(AGENT: R1, THEME: R2, INSTRUMENT: R3))                      -- used a telescope
  , AND( HOLDS(SEE(AGENT: R1, THEME: R2)), HOLDS(HAVE(AGENT: R2, THEME: R3)) ) ] )  -- man had one
```

**Rule SG-CON-007.**
1. An ALT has at least two members of the same sort.
2. `support` is ordinal evidence (rank plus evidence references). It MUST NOT be a number presented as probability, since such numbers are valid only after calibration (Part 6).
3. The smallest sub-expression where readings differ carries the ALT. Independent ambiguities use independent ALT groups (packed ambiguity), so n ambiguities do not create 2ⁿ full copies. Cross-group constraints (`if g1=A then g2=B`) are allowed.
4. The number of alternatives per group is bounded by a configurable budget [Provisional: default 4].
5. Canonical (trusted) IR contains an ALT only when the interpretation outcome is AMBIGUOUS. Selecting one reading keeps the others as REJECTED_ALTERNATIVE records with the reason, for audit.

### 3.14.2 ERROR

`ERROR(code, span, detail)` is a legal node **only in candidates** (SG-CON-008). Canonical IR contains none. Error codes are defined in Part 5 (structural, type, scope, unresolved-reference, rule-misapplied, evidence-missing, and others).

### 3.14.3 Interpretation outcomes

Per source unit the outcome is RESOLVED, AMBIGUOUS, or UNRESOLVED (axis A, §1.7.3). "Insufficient information" is a valid result [F3-B §7.33]. An UNRESOLVED unit is stored as a source record plus a candidate with the unresolved points listed, so it can be retried when context arrives.

---

## 3.15 Figurative language and coercion (SG-TYP-002)

[F2-A §3.6]

Procedure, run only after SG-TYP-001 finds an INCOMPATIBLE binding:

```text
1. Literal attempt          SWALLOW(AGENT: computer, THEME: file)  → INCOMPATIBLE
2. Search registered mappings   (metaphor, metonymy, type-shift)
3. Candidate contextual reading TAKE_IN(AGENT: computer_system, THEME: file)
4. Record the status        FIG(mapping_id, SWALLOW(...), TAKE_IN(...))
                            interpretation_type = FIGURATIVE
```

**Rule SG-TYP-002.** A figurative or coerced reading MUST cite a registered mapping (metaphor, metonymy, or type-shift rule). The literal expression's meaning is never redefined. If no mapping exists, the model may propose one as a candidate (Part 9), and the unit is AMBIGUOUS or UNRESOLVED in the meantime.

Mappings are records:

```text
FigurativeMapping
    mapping_id, kind (METAPHOR | METONYMY | TYPE_SHIFT)
    source_frame, target_frame, role_correspondences
    conditions, status (CANDIDATE | APPROVED), evidence
```

A metaphor mapping states a correspondence between roles. Analogies discovered by the engine (Part 9) are proposals with shared and non-shared relationships marked, and never become factual assertions [F1-C §6].

---

## 3.16 Provenance and the annotation channel (closes item 11; Enhancement E-37)

Every node MAY carry an annotation:

```text
@ann{ spans[], rule_ids[], basis (EXPLICIT | GRAMMATICAL | BACKGROUND),
      language_features{} }
```

- Each ASSERT has an evidence reference (Part 6) and a derivation certificate (Part 5).
- Annotations explain how a node was derived. They do not alter what it means.

**Rule SG-CAN-004 (structural equality).** Two expressions are structurally equal iff their normalized structures are equal **ignoring annotations**. Structural equality drives hash-consing and deduplication (Part 11). It is never used to merge event occurrences. Two identical-looking events may be different events, and merging requires RESOLVE_INDIVIDUAL [F3-A §6.10].

---

## 3.17 Canonicalization (closes item 10)

**Canonicalization** converts equivalent expressions into a standard form so that equivalent meanings share one representation [F2-A §3.16].

### 3.17.1 Permitted normalizations

| # | Normalization | Condition |
|---|---|---|
| N1 | Insert implicit HOLDS | Shorthand expansion |
| N2 | Flatten and sort AND / OR children | Associativity and commutativity of the logical connectives only |
| N3 | Alpha-rename variables | §3.6 |
| N4 | Voice normalization | Active and passive map to the same role bindings. The grammatical subject is mapped to roles by interpretation rules, and focus is kept as language annotation. |
| N5 | Converse-frame normalization | "gave" and "received from" share one frame only where a rule declares the preserved scope |
| N6 | Time normalization | Resolved values added next to the original relative expression |
| N7 | Inverse-relation normalization | PART_OF vs HAS_PART direction |
| N8 | Shorthand expansion | Property shorthand, etc. |

### 3.17.2 Forbidden simplifications (Enhancement E-36)

**Rule SG-CAN-002.** The canonicalizer MUST NOT apply logical simplifications that discard natural-language meaning. In particular:
- Double negation is **not** eliminated. "Not uncommon" is not equivalent to "common".
- A quantifier is not moved across negation.
- An offer is not normalized into a completed transfer (§3.10.3).
- Perspective and lexical choice are not erased from reversible mode. They are moved to LanguageAnnotation.

A logic simplification is allowed only inside a declared `LOGICAL_CONTEXT`.

### 3.17.3 Canonicalization rule schema

[F2-A §3.17]

```text
CanonicalizationRule
    rule_id            SG-CAN-nnn  (alias e.g. CANON_ACTIVE_PASSIVE_001)
    input_pattern      typed pattern
    output_pattern     typed pattern
    preconditions      machine-checkable conditions
    preservation_scope which meaning distinctions are preserved
    tests              positive paraphrase pairs AND negative contrastive pairs
    version
```

**Rule SG-CAN-001 (restated).** Equivalent constructions may share a canonical representation only when the transformation preserves all distinctions required by the rule's declared scope. Every rule MUST ship with positive pairs and negative pairs. Negative example: `John gave Mary a book` ≠ `John offered Mary a book` [F3-B §7.22].

**Rule SG-CAN-003 (auditability).** Every canonicalization applied is recorded in the derivation certificate with rule ID and version. If a rule later proves faulty, the records it produced can be listed and reprocessed [F2-A §3.17].

---

## 3.18 Composition of processes; description versus instruction; semantic algebra

### 3.18.1 Composition operators

`COMPOSE(kind, parts, deps)` builds a composite SIT. The kinds [F2-B §4.11]:

| Kind | Meaning |
|---|---|
| SEQUENCE | One part follows another |
| PARALLEL | Parts may run concurrently |
| CONDITION | A part occurs depending on a condition (`PROC_IF`, distinct from the propositional COND) |
| LOOP | A part repeats while or until a condition |
| DEPENDENCY | One part requires another's result |
| ALTERNATIVE | One of several parts occurs |
| SUBPROCESS | One part belongs to a larger process |

Digestion (ingestion, mechanical and chemical breakdown, absorption) and manufacturing (input, processing, assembly, quality check) are both `COMPOSE(SUBPROCESS, …)` with different frames [F2-B §4.10].

### 3.18.2 Description versus instruction

`EVENT_A BEFORE EVENT_B` is a temporal assertion (TEMPORAL). `EXECUTE A THEN B` is an instruction. They use similar structure with different semantics [F2-B §4.11]:

- **Descriptive** composition is the default. Its parts may be wrapped in HOLDS inside TEMPORAL or in embedded assertions.
- **Prescriptive** composition appears only under DIRECT. It is procedural memory content (Part 10), never recorded as something that happened.

### 3.18.3 Semantic algebra: meta-level operations

[F2-B §4.8] These operate on **definitions**, not on instances. They produce candidates for the learning plane (Part 9).

| Operation | Signature | Constraint |
|---|---|---|
| Apply(F, A) | Frame × bindings → SIT | The object-level construct of §3.4 |
| Compose(F₁, F₂) | Frame × Frame × binding-map → composite frame | Defined only when output roles of F₁ type-match input roles of F₂ through an explicit map. Not commutative. |
| Generalize(F₁, F₂) | → set of candidate abstractions | Not unique. A result is a candidate, never promoted directly (SG-GEN-001). |
| Specialize(F, C) | Frame × constraints → child frame candidate | Must preserve parent commitments (SG-FRM-002). |

Unlike arithmetic, these do **not** have assumed commutativity, associativity, or uniqueness. They are typed transformations with explicit preconditions [F2-B §4.8].

---

## 3.19 Constraint language (closes item 8)

Frame roles, property domains, and relation signatures use a small constraint vocabulary:

```text
CONSTRAINT ::= KIND_IS(kind) | CLASS_IS(concept)
             | VALUE_IN(value-domain) | UNIT_DIMENSION(dim)
             | CARDINALITY(min,max)
             | DISJOINT_WITH(concept)
             | REQUIRES(role) | EXCLUDES(role,role)
             | SAME_REFERENT(role,role) | DIFFERENT_REFERENT(role,role)
             | AND(CONSTRAINT+) | OR(CONSTRAINT+) | NOT(CONSTRAINT)
```

Each constraint has a machine-checkable evaluator returning COMPATIBLE / INCOMPATIBLE / UNDETERMINED (§3.3.2). Property-specific constraints from Part 2, §2.7 compile to this language: value domain membership, unit dimension, and bearer class.

---

## 3.20 Minimality and grammar selection (Enhancement E-23)

F2-A §3.22 gives the cost `C = αS + βV + γP` (storage, validation, processing) and requires correctness and expressiveness as constraints. It gives no calibration. The procedure:

1. **Constraint first.** A grammar variant is eligible only if it passes the expressiveness suite (every benchmark category of Part 12) and the round-trip and validation suites.
2. **Measure on the benchmark.** S = encoded bytes per record (Part 11). V = validator work per record. P = interpretation time per record.
3. **Pareto first, scalarize last.** Report the Pareto front across S, V, P. Choose a single variant by weighted cost only to break ties, with each term normalized by the baseline variant's value and weights equal by default. Documented changes to the weights require benchmark evidence.
4. Grammar changes are MAJOR or MINOR versions (Part 2, §2.13).

---

## 3.21 Worked examples

### 3.21.1 "The doctor did not give the patient medication because the patient was allergic to it."

Referents: `R1`=doctor, `R2`=patient, `R3`=medication. `it` has candidate antecedent R3, linked as `SAME_AS(it, R3, DISCOURSE)` with evidence (the only inanimate candidate that can be an allergen).

```text
ALT(g3,
 [ -- reading 1 (rank 1): the doctor withheld it, and the allergy is why
   CAUSATION( CAUSE: HOLDS(APPLY(ALLERGIC, {EXPERIENCER: R2, STIMULUS: R3})),
              EFFECT: NOT( HOLDS(APPLY(GIVE, {AGENT: R1, SOURCE: R1, RECIPIENT: R2, THEME: R3})) ),
              CAUSE_TYPE: EXPLANATORY_REASON )
 , -- reading 2 (rank 2): negation scopes over the whole because-clause
   NOT( CAUSATION( CAUSE: allergy(R2,R3),
                   EFFECT: HOLDS(GIVE(R1,R2,R3)),
                   CAUSE_TYPE: EXPLANATORY_REASON ) ) ] )
```

This is the correction F2-A §3.24 pointed at: the negated transfer is an event description inside a negated proposition, not a recorded event. The second reading is retained only if the evidence supports it, otherwise the unit resolves to reading 1.

### 3.21.2 Active versus passive

```text
"The doctor examined the patient."        APPLY(EXAMINATION, {EXAMINER: R1, EXAMINED_ENTITY: R2})
"The patient was examined by the doctor." APPLY(EXAMINATION, {EXAMINER: R1, EXAMINED_ENTITY: R2})
   + LanguageAnnotation(voice=passive, focus=R2)
"The patient was examined."               APPLY(EXAMINATION, {EXAMINED_ENTITY: R2, EXAMINER: UNSPEC})
```

The third case MUST NOT invent an examiner [F3-C §8.18].

### 3.21.3 Give versus offer (the negative pair)

```text
"John gave Mary a book."      HOLDS(GIVE(AGENT: R1, SOURCE: R1, RECIPIENT: R2, THEME: R3))
"Mary received a book from John."  same bindings, voice/perspective in annotation (rule scope declared)
"John offered Mary a book."   HOLDS(OFFER(AGENT: R1, RECIPIENT: R2, CONTENT: GIVE(R1, R2, R3)))
                              -- the inner GIVE is an unasserted description
```

### 3.21.4 "The computer swallowed the file." (figurative)

```text
FIG(M_swallow_take_in,
    SWALLOW(AGENT: R1, UNDERGOER: R2),                 -- literal, INCOMPATIBLE (§3.3.2)
    TAKE_IN(AGENT: R1/system, UNDERGOER: R2))          -- candidate contextual reading
interpretation_type = FIGURATIVE   (status: CANDIDATE until mapping approved)
```

---

## 3.22 Closure of the twelve open items (F2-A §3.23)

| # | Open item | Closed in |
|---|---|---|
| 1 | Semantic types of expressions | §3.3 (sorts, three-valued compatibility) |
| 2 | Exact meaning of each operator | §3.5 (catalogue), §3.7–§3.9 |
| 3 | Variable scope | §3.6 (SG-CON-005a–e) |
| 4 | Quantifier semantics | §3.7 (restricted Q, GEN, domain) |
| 5 | Temporal and modal operators | §3.8, §3.9 (force × flavor; Allen's thirteen; tense and aspect) |
| 6 | Equality and identity rules | §3.12 (SAME_AS, opaque contexts) |
| 7 | Frame inheritance | Part 4 (hooks: SG-FRM-002, §3.18.3) |
| 8 | Property constraints | §3.19 and Part 2, §2.7 |
| 9 | Handling of unknown values | §3.13 (four hole states, open-world) |
| 10 | Canonicalization | §3.17 (permitted and forbidden normalizations, rule schema, tests) |
| 11 | Provenance and evidence | §3.16 (annotation channel), Parts 5–6 |
| 12 | Error and ambiguity representation | §3.14 (ALT, ERROR, outcomes) |

### Rules registered in this part

| Rule | Subject |
|---|---|
| SG-CON-005a–e | Variable scope |
| SG-CON-006 | Sort discipline |
| SG-CON-007 | ALT well-formedness |
| SG-CON-008 | ERROR nodes only in candidates |
| SG-TYP-001 (revised) | Three-valued type compatibility |
| SG-TYP-002 | Registered figurative and coercion mappings |
| SG-GEN-003 | GEN is not an exceptionless universal |
| SG-EVD-004 | Presupposed content emitted inside its context |
| SG-KNW-003 | Opaque contexts block identity substitution |
| SG-CAN-001 (restated) | Canonicalization scope and tests |
| SG-CAN-002 | Forbidden simplifications |
| SG-CAN-003 | Canonicalization audit trail |
| SG-CAN-004 | Structural equality ignores annotations |

### Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-33 | Five modal categories mix two dimensions | FORCE × FLAVOR, with the five as derived labels (§3.8.1) |
| E-34 | Two-valued type check conflicts with open-world | Three-valued compatibility (§3.3.2) |
| E-35 | Only unrestricted EXISTS and FOR_ALL | Restricted Q, cardinal, vague, and generic quantifiers, contextual domain (§3.7) |
| E-36 | Risk of logic simplification discarding meaning | Forbidden-simplification rule (§3.17.2) |
| E-37 | Provenance could change equality and hashing | Annotation channel excluded from structural equality (§3.16) |
| E-38 | Identity substitution inside attitude contexts | Opaque contexts (§3.12) |
| E-39 | Ambiguity could explode combinatorially | Packed ambiguity, bounded groups, ordinal support (§3.14) |
| E-40 | Factive presuppositions had no representation | Presupposed content emitted inside its context (§3.8.2) |
| E-06 (refined) | Part 1 proposed a free realization modifier | Frame family plus aspect plus embedding (§3.10.3) |


---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 4 of 12: Frames, the Functional Ontology, and the Foundation Package

Part 3 fixed how meanings are built. This part defines what they are built from: the frame schema, how frames relate (inheritance, composition, analogy), the functional ontology, the abstraction layers, and the Foundation Package that seeds the system [F3-B §7.3]. Nothing here is hand-wavy "ontology". Every frame is a record that Part 5's validator can check.

---

## 4.1 What frames must support

The sources distinguish four kinds of generalization [F2-B §4.1] that are easy to confuse. A frame model has to represent each without merging them.

| Generalization | What is shared | Representation in this part |
|---|---|---|
| Taxonomic | Category membership | Concept IS_A hierarchy (§4.7) |
| Functional | Capability or purpose | FN functions and HAS_FUNCTION (§4.8) |
| Structural | Relationship pattern | Structural frames, analogy records, signatures (§4.10) |
| Procedural | Transformations and processes | State semantics, composition, operations (§4.4, §4.6, §4.9) |

A heart and a water pump share a function but not a category. Two systems can share a structure without sharing behaviour [F2-B §4.1]. Keeping the four apart is a design requirement. Discovery of new abstractions is Part 9.

**Mechanism selection guide (Normative).** The sources warn that one enormous inheritance tree is hard to maintain [F2-B §4.19] and list five complementary mechanisms. Use the first one that fits:

| Need | Mechanism | Example |
|---|---|---|
| "Is a kind of", with exceptionless shared constraints | Taxonomic IS_A (limited depth) | Car IS_A Vehicle |
| "Can do / is for" | Functional composition (HAS_FUNCTION) | Heart HAS_FUNCTION TRANSPORT |
| "Is built from" | Structural composition (HAS_PART, component frames) | Car HAS_PART Engine |
| A more constrained version of a situation | Frame specialization | FLUID_TRANSPORT of TRANSPORT |
| A one-off link between concepts | Explicit relation | Hygrometer MEASURES Humidity |

---

## 4.2 The FrameDefinition record

A frame is a concept of kind FRAME (Part 2, §2.2). Its definition has the following structure. The line "ordered roles" matters for compression (Part 11), because instances omit role names.

```text
FrameDefinition
  header                      (id, status, version; Part 2 §2.3)
  name, layer (1|2|3), authority (GRAMMAR | DOMAIN)
  situation_kind              EVENT | STATE | PROCESS | SYSTEM
  abstract                    true → cannot be instantiated directly
  parameters[]                frame-level constants (§4.4.3)
  parents[]                   (parent_frame, link_kind, role_map)     (§4.5)
  roles[]                     ordered; each RoleSpec (§4.3)
  constraints[]               constraint language (Part 3 §3.19)
  disjoint_roles[]            role pairs that MUST NOT share a referent
  internal_relations[]        relations among roles (structural frames)
  state_semantics             initial / final / process                 (§4.4)
  consequences                preconditions, effects, typical, observed (§4.4.2)
  presuppositions[]           content presupposed by the frame (Part 3 §3.8.2)
  components[]                ComponentSpec list for composite frames   (§4.6)
  perspectives[]              PerspectiveVariant list                   (§4.3.3)
  functional_links[]          HAS_FUNCTION qualifiers                   (§4.8)
  control_hints[]             interpretation hints (e.g. subject control)
  signature                   derived, regenerable (§4.10.3)
  tests                       valid / incomplete / invalid / contrastive pairs (§4.13)
  provenance                  origin: MANUAL_CORE | IMPORTED(resource, mapping) | LEARNED(certificate)
  version fields              content_hash, supersedes, derived_by (rule ids)
```

---

## 4.3 Roles inside frames

### 4.3.1 RoleSpec

```text
RoleSpec
  role_id, name
  tier                  1 (use a universal role directly) | 2 (frame-specific)
  parent_role           tier-1 role (REQUIRED when tier = 2)
  expected_kind         Part 2 §2.2
  constraints           class and value constraints
  requiredness          REQUIRED | OPTIONAL
  cardinality           (min, max)
  index                 stable position (§4.3.2)
```

**A frame's role list is closed** (Enhancement E-45). A binding may name only roles the frame defines or inherits. A tier-1 role name is usable only if the frame declares it, either directly or as a specialization. The validator rejects the others and suggests the frame-specific role. In F1-B §7, a model binds `INSTRUMENT = ANTIBIOTICS` where the frame defines `INTERVENTION`. The validator rejects it and offers `INTERVENTION ⊑ INSTRUMENT`.

The tier-1 parent is for cross-frame queries and mapping rules. It does not widen what a frame accepts.

### 4.3.2 Role order (Normative)

**SG-FRM-006.** Role order is append-only. Inherited roles come first in parent order, then the frame's own roles in declaration order. A role is never reordered or deleted. A retired role is deprecated and keeps its index. Adding a new optional role is a MINOR change. This keeps old binary records decodable (Part 11) [F3-A §6.6, §6.19].

### 4.3.3 Perspective variants (Enhancement E-43)

Frames like commerce and transfer can be described from different participants' standpoints. "John gave Mary a book" and "Mary received a book from John" are the same role bindings seen from the giver or the recipient. The sources want shared canonical forms only where meaning is preserved [F2-A §3.16].

```text
PerspectiveVariant
  name                  e.g. BUY, SELL, GIVE_VIEW, RECEIVE_VIEW
  focus_role            the role treated as the grammatical anchor
  preserved             ALL_BINDINGS (the only value in v1.0)
  lexical_hints         verbs/senses typically expressing the variant
```

A perspective variant is declared by the frame, so the Part 3 canonicalization condition (N5, SG-CAN-001) is met by construction. The perspective is kept as a language annotation. If a verb changes commitments (offer versus give), it is a different frame, not a variant.

---

## 4.4 State semantics and consequences

### 4.4.1 State semantics

[F2-A §3.7, §3.9] A frame definition carries the general meaning of the situation once, and instances need only record what the source states.

```text
state_semantics
  initial    RELATE/PROPERTY pattern over roles
  final      RELATE/PROPERTY pattern over roles
  process    named change (e.g. CHANGE_LOCATION)
  applies_when   COMPLETED_VIEW   (default for final-state entailments)
```

Example: MOVE declares `initial: LOCATED(MOVER, SOURCE_LOCATION)`, `final: LOCATED(MOVER, DESTINATION_LOCATION)`, `process: CHANGE_LOCATION`. An instance supplies only the participants.

**Aspect-gated entailments (Enhancement E-47).** Final-state entailments hold for the completed view. "John was moving to Cairo" (progressive) does not entail that he arrived. Entailments are therefore only derived when the instance's aspect (Part 3, §3.9.3) is perfective or perfect. The sources did not state this. It follows from their rule that an attempted action must not imply its effect [F2-A §3.8].

Entailments derived from a frame's state semantics are **INFERRED**. They are computed on demand and never stored as source-stated (Part 11, inference compression).

### 4.4.2 Four kinds of consequence

[F2-A §3.8] As established in Part 3 §3.10.2:

```text
consequences
  preconditions      needed for success under the model (not a validity test for the instance)
  effects            expected state change for a successful completion (ESSENTIAL or TYPICAL)
  typical_outcomes   common, not guaranteed
  observed_outcomes  never in the definition; recorded as assertions about instances
```

Effects carry a strength: ESSENTIAL (every completed instance) or TYPICAL (defeasible). GIVE has essential effect "recipient gains possession" and typical effect "recipient gains ownership", because "gave me the pen for a minute" gives possession only.

### 4.4.3 Parameters and parametric specialization (Enhancement E-42)

Many frames differ only in which property changes. The sources list OPENING, CLOSING, HEATING, and COOLING under STATE_CHANGE [F2-A §3.8], and note that frames sharing a structure should be stored once [F2-B §4.18]. A **parameter** is a frame-level constant, not a role:

```text
FRAME STATE_CHANGE                       FRAME OPEN   (SPECIALIZES STATE_CHANGE)
  parameters: DIMENSION (a PROPERTY),       pinned: DIMENSION = OPENNESS, DIRECTION = INCREASE
              DIRECTION {TO_VALUE,          role UNDERGOER constrained to OPENABLE_ENTITY
              INCREASE, DECREASE}
```

A specialization MAY pin parameters. An instance MUST NOT set parameters. The choice of frame fixes them, which keeps instances compact. "The door opened" is `OPEN(UNDERGOER: door)`. "The door did not open" is the same inside NOT (Part 3 §3.7.3).

---

## 4.5 Inheritance between frames

### 4.5.1 Two link kinds (Enhancement E-41)

The sources want both strict specialization and looser structural sharing. "Specialized frames might share a structural abstraction without inheriting every constraint from one another" [F2-B §4.7]. Chemical combination and file concatenation are the standard example. The parent link therefore has a **kind**:

| Link kind | Meaning | Carries |
|---|---|---|
| SPECIALIZES | The child is a more constrained form of the parent | Roles, constraints, entailments, and consequences |
| STRUCTURAL_INSTANCE_OF | The child has the parent's role structure and relation pattern | Role correspondence only. No entailments are inherited. |

Each link includes a `role_map` from child roles to parent roles.

### 4.5.2 Rules

**SG-FRM-002 (Normative).** A SPECIALIZES child preserves the defining commitments of the parent and records its own refinements.

**SG-FRM-003 (role narrowing).** For SPECIALIZES links, a child MAY:
- narrow a role's class constraint
- make an OPTIONAL role REQUIRED
- add roles (appended, §4.3.2)
- add constraints or pin parameters
- add consequences

A child MUST NOT:
- remove an inherited role
- change a role's kind
- widen a class constraint
- make a REQUIRED role OPTIONAL
- weaken an ESSENTIAL consequence

*Test:* project any valid child instance to the parent's roles via `role_map`. The result MUST be a valid parent instance.

The sources distinguish ontological specialization from executable method inheritance [F2-B §4.9]. This test is semantic substitution. It is not software subtyping. A frame has no executable methods.

**SG-FRM-004 (multiple inheritance).** A frame (or concept) with several parents:
1. Inherited roles with the same name merge as the **conjunction** of constraints.
2. If the conjunction is provably empty (DISJOINT_WITH), the definition is rejected.
3. Contradictory consequences are rejected, and conditional ones must state their condition.
4. No linearization (method-resolution-order) is used. The validator evaluates compatibility logically [F2-B §4.3].
5. Diamond ancestry shares ancestors' roles once.

### 4.5.3 Generalize and Specialize on instances

[F1-B §8.3; F2-B §4.8]

- **GENERALIZE(instance, link)** projects an instance to the parent frame via `role_map`. Along SPECIALIZES it is sound: if the instance holds, the projection holds. Along STRUCTURAL_INSTANCE_OF it yields `STRUCTURAL_ONLY`, a role-structure view with no entailments. The operation is **lossy**. `HEART PUMPS BLOOD` generalizes to `ORGAN TRANSPORTS FLUID`.
- **SPECIALIZE** needs new information. From `ORGAN TRANSPORTS FLUID` the system cannot recover "heart". It returns **candidates** only, never an assertion.

Therefore specific records store specific concept IDs and frames, and generalizations are computed on demand. Generalization is used for shared definitions, reasoning, and pattern discovery, not as a replacement for storing specifics [F1-B §8.3].

---

## 4.6 Frame composition

Inheritance says "is a specialized form of". Composition says "is constructed from" [F2-B §4.10].

```text
ComponentSpec
  frame_ref            component frame@version
  role_map             composite role → component role
  ordering             SEQUENCE | PARALLEL | CONDITION | LOOP | DEPENDENCY
                       | ALTERNATIVE | SUBPROCESS     (Part 3 §3.18.1)
```

Example (commerce, §4.12.3): COMMERCIAL_TRANSACTION is composed of two OWNERSHIP_TRANSFER components, goods from seller to buyer and money from buyer to seller, linked by DEPENDENCY.

Rules:
- A composite instance MAY be fully specified, or MAY specify only some components. Unspecified components are UNSPEC, not invented.
- Composition is acyclic (a frame is not its own component, directly or indirectly).
- Composition is descriptive by default. A procedure (what should happen) is a different construct (Part 3 §3.18.2; procedural memory, Part 10).
- A process can be a SUBPROCESS of several larger processes. It is stored once and referenced.

---

## 4.7 Concept hierarchies (taxonomic generalization)

Rules for the IS_A structure over concepts [F2-B §4.2, §4.3, §4.19].

**SG-KNW-004 (inheritance of properties).** A constraint is inherited as exceptionless logic only if it is ESSENTIAL (Part 2, §2.9). A TYPICAL property is inherited as a defeasible default. Place each property in the most general class where it truly applies to every member. Wheels belong to WHEELED_VEHICLE, not VEHICLE, because boats exist. Categories may **overlap** (an amphibious vehicle is both). Classes are not forced into strict partitions.

**SG-KNW-005 (concept multiple inheritance).** A concept MAY have several parents (DRONE is both AIRCRAFT and ROBOTIC_SYSTEM). The validator classifies any conflict as one of four cases: compatible constraints, conditional constraints, genuine contradiction, or modelling error. Only the first two are accepted. No linearization applies.

**Part-whole** (Part 2, §2.8): PHYSICAL_COMPONENT_OF, MATERIAL_PORTION_OF, ORGANIZATIONAL_MEMBER_OF, and INFORMATIONAL_COMPONENT_OF are separate relations under a broad part-whole family. They do not share logical properties. COMPOSITE_STRUCTURE (WHOLE, PART+) is the **frame** form of a part-whole fact, used when time, qualification, or additional participants are needed. The bare binary relation is used otherwise.

**Traits over towers.** Where concepts share a capability without sharing a category, use functional composition (§4.8). PUMP and HEART both carry `HAS_FUNCTION DRIVE_FLUID_FLOW` without a shared superclass. A deep hierarchy such as ENTITY → PHYSICAL → ARTIFACT → DEVICE → MECHANICAL_DEVICE → PUMP is permitted only where each level has distinguishing constraints. Levels that exist only to hold a label are not created.

---

## 4.8 The Functional Ontology

### 4.8.1 Purpose and namespace

Classification by *what a thing is* misses cross-domain similarities that classification by *what it does* captures [F1-B §8.1]. The coaching document's six functional roles (notice, decide, act, hold, move, transform) are adapted as a separate **FN** namespace. Functions are concepts of kind FUNCTION (Part 2, §2.2). They are never ordinary object classes.

### 4.8.2 Primitive functions (Enhancement E-07, resolved)

The sources list two different sets. One has six (DETECT, DECIDE, ACT, STORE, TRANSPORT, TRANSFORM) [F1-B §8.1]. The other has seven (DETECT, PROCESS, STORE, TRANSFER, TRANSFORM, ACT, REGULATE) [F2-B §4.5]. The second drops DECIDE and renames TRANSPORT to TRANSFER, which clashes with the TRANSFER frame. The source also says the ontology must not gain a function merely because a model invents a label. The resolution:

**Primitives (six):**

| FN | Definition | Functional-frame roles | Example performers |
|---|---|---|---|
| FN.DETECT | Registers a state or quantity of something | DETECTOR, TARGET_PROPERTY, SIGNAL | Eye, camera, thermometer, sensor |
| FN.DECIDE | Selects among alternatives using criteria | DECIDER, OPTIONS, CRITERIA, OUTCOME | Controller, brain (defined contexts) |
| FN.ACT | Changes the state of something in the environment | ACTUATOR, TARGET, CHANGE | Motor, muscle, valve |
| FN.STORE | Holds a resource or state over time | HOLDER, HELD, DURATION | Battery, memory, fuel tank |
| FN.TRANSPORT | Moves or carries something between locations or parts | DRIVER, TRANSPORTED, SOURCE, DESTINATION, CONDUIT | Heart, pump, conveyor, vessel |
| FN.TRANSFORM | Converts one thing into another | TRANSFORMER, INPUT, OUTPUT, BYPRODUCT | Motor, solar cell, muscle, processor |

**Derived (named composites, not primitives):**
- **FN.PROCESS_INFORMATION** is FN.TRANSFORM where INPUT and OUTPUT are information.
- **FN.REGULATE** is a LOOP composite of DETECT → DECIDE → ACT that maintains a quantity near a target.

They are defined from existing primitives and therefore satisfy the "can an existing function represent this?" test. They are promoted to primitives only through the Part 9 pipeline and a MINOR grammar change. TRANSPORT keeps its name. TRANSFER stays reserved for the frame family (§4.12).

An object can have several functions. The coaching document's roles-and-fit lens allows a component to occupy two roles [F1-B §8.1].

### 4.8.3 Function hierarchy and its limits

```text
FN.TRANSPORT
 ├ TRANSPORT_MATTER ─ TRANSPORT_FLUID ─ DRIVE_FLUID_FLOW   (pump, heart)
 │                                    └ CONDUCT_FLUID       (pipe, vessel)
 ├ TRANSPORT_ENERGY
 └ TRANSPORT_INFORMATION   (transmit)
FN.DETECT ─ MEASURE ─ MEASURE_HUMIDITY   (hygrometer)
FN.STORE ─ STORE_ENERGY, STORE_INFORMATION
```

**Caution (Normative):** information transfer and material transport are not physically equivalent. For example, matter is conserved when moved, and information can be copied. Conservation constraints are therefore **not** defined at the FN.TRANSPORT root. They are declared on the specializations where they hold [F1-B §8.3].

Distinct sub-functions matter: a **pump** DRIVES fluid flow and a **pipe** CONDUCTS it. Both participate in fluid transport, but a rule "everything that moves fluid is a pump" is refuted by pipes, rivers, and vessels [F2-B §4.16, F1-B §9]. That is why the sub-function level exists.

### 4.8.4 Assigning functions

```text
FunctionAssertion
  performer        concept (class-level) or referent
  function         FN concept
  mode             PURPOSE | CAPABILITY | CONTEXTUAL
  qualifiers       input_class, output_class, medium, ...
  evidence         (Part 6)
```

- PURPOSE is what the thing is for (a heart pumps blood). CAPABILITY is what it can do. CONTEXTUAL is what it can serve as in some circumstances (a car as shelter) [F2-C §5.5].
- A function qualifier restricts what is transported, stored, or detected. For example, `HEART HAS_FUNCTION FN.TRANSPORT {transported: Blood}`.

**SG-FRM-005 (Normative).** HAS_FUNCTION does not imply IS_A. A functional match MUST NOT be used to infer category membership or shared non-functional properties. A heart stays a biological organ and a pump stays a mechanical device. They share a functional frame without being the same kind of object [F1-B §8.1, F1-D §2.17].

**SG-FRM-009 (primitive protection).** The FN primitives belong to the Foundation Package. They are changed only by a versioned grammar review, never by automatic proposal approval (P-03, P-13).

### 4.8.5 Functional frames and Input–Transformation–Output

Each FN has a functional frame (a situation frame in layer 2) with the roles listed above. FN.TRANSPORT's frame is TRANSPORT:

```text
FRAME TRANSPORT v1    layer=2  situation_kind=EVENT
  roles: TRANSPORTED_ENTITY ⊑ THEME REQ ; SOURCE OPT ; DESTINATION ⊑ GOAL OPT ;
         MECHANISM ⊑ INSTRUMENT OPT ; PATH OPT ; TIME OPT
FRAME FLUID_TRANSPORT   SPECIALIZES TRANSPORT   TRANSPORTED_ENTITY: CLASS_IS(Fluid)
FRAME BLOOD_CIRCULATION SPECIALIZES FLUID_TRANSPORT   (layer 3, DOMAIN)
                        TRANSPORTED_ENTITY: CLASS_IS(Blood)
```

The sources' four Input–Transformation–Output examples [F2-B §4.6] are instances of **typed transformation frames**:

| Performer | Input | Transformation | Output | Frame type |
|---|---|---|---|---|
| Electric motor | Electrical energy | Electromechanical conversion | Mechanical energy | PHYSICAL_TRANSFORMATION |
| Solar cell | Light energy | Photovoltaic conversion | Electrical energy | PHYSICAL_TRANSFORMATION |
| Muscle | Chemical energy | Biological energy conversion | Mechanical work and heat | PHYSICAL_TRANSFORMATION |
| Processor | Data, electrical energy | Computation | Processed data, heat | INFORMATION_TRANSFORMATION |

TRANSFORMATION has four typed children: PHYSICAL, INFORMATION, STATE_TRANSITION (the STATE_CHANGE family), and RELATIONAL (ownership transfer changes a legal relation, and a conversation changes beliefs) [F2-B §4.6]. A real event is **not** automatically forced into a physical transformation. The Input → Process → Output pattern can describe almost anything, so the abstraction has little discriminative power on its own. That limit is enforced by Part 9 (SG-GEN-004).

---

## 4.9 Universal semantic operations

Operations that recur across domains [F2-B §4.7] are layer-1 frames: **MOVE, STORE, TRANSFORM, COMBINE, SEPARATE, COMPARE, SELECT, CREATE, DESTROY.**

They carry a **general operation structure** only:

```text
FRAME COMBINE  v1   layer=1   abstract
  roles: INPUTS (2+ entities, ENTITY) ; RESULT (combined entity)
```

Specialized frames attach by STRUCTURAL_INSTANCE_OF, because they share structure but not entailments:

```text
CHEMICAL_COMBINATION   STRUCTURAL_INSTANCE_OF COMBINE   (conservation of mass, reaction semantics)
FILE_CONCATENATION     STRUCTURAL_INSTANCE_OF COMBINE   (order-dependent, inputs preserved)
SET_UNION              STRUCTURAL_INSTANCE_OF COMBINE   (commutative, idempotent)
```

A chemical reaction is not the same as concatenating files. Properties such as commutativity are declared per specialization, never at COMBINE.

---

## 4.10 Structural templates, analogy, and signatures

### 4.10.1 Structural (system) frames

Some frames describe an arrangement rather than an event [F1-B §8.2, F2-B §4.12]:

```text
FRAME FLUID_CIRCULATION_SYSTEM v1   layer=2   situation_kind=SYSTEM
  roles: DRIVER (⊑ INSTRUMENT, FUNCTION: DRIVE_FLUID_FLOW) REQ ; FLUID REQ ; CONDUIT REQ
  internal_relations: DRIVES_FLOW_OF(DRIVER, FLUID) ; FLOWS_THROUGH(FLUID, CONDUIT)
```

Instances: biological `{DRIVER: Heart, FLUID: Blood, CONDUIT: BloodVessel}` and industrial `{DRIVER: Pump, FLUID: Water, CONDUIT: Pipe}`.

### 4.10.2 Analogy records

An analogy is a **proposed mapping**, not a fact [F1-B §8.2, F1-C §6]:

```text
StructuralAnalogy
  frame_a, frame_b, via_abstraction (optional)
  role_correspondences[]   (role_a, role_b, strength EXACT | PARTIAL)
  shared_relations[]       relations that hold on both sides
  unshared_a[], unshared_b[]
  differences[]            preserved distinctions (mechanism, scale, conservation, ...)
  status CANDIDATE | APPROVED , evidence , version
```

**SG-FRM-007 (Normative).** An analogy is not an equivalence. It must list shared and unshared relations. It licenses inference only along `shared_relations`. It never makes an entailment of one domain a fact about the other. Heart and pump share driving of flow, and they do not share manufacturing or growth.

### 4.10.3 Structural signatures

A signature supports retrieval and comparison in the Pattern Discovery Engine. It is **derived and regenerable**, not authoritative [F2-B §4.13–4.14]:

| Level | Content |
|---|---|
| 1 Topological | Role count and role-graph connectivity |
| 2 Typed | Level 1 plus node kinds and relation types |
| 3 Functional | Level 2 plus FN functions of roles and frame |
| 4 Semantic | Level 3 plus constraints, pinned parameters, consequences |

Levels 1–3 may be hashed for grouping candidates. **Level 4 is stored as structure and compared structurally.** A hash identifies and indexes a structure. It cannot preserve its meaning [F2-B §4.14]. Two frames with equal signatures are only candidates for comparison, never assumed equivalent.

---

## 4.11 Abstraction layers

[F2-B §4.24] Frames are placed in layers. Layers organize retrieval and review. They do not forbid cross-layer references.

| Layer | Contents | Authority | Examples |
|---|---|---|---|
| 0 | Grammar constructs: Reference, Literal, Application, Relation, LogicalOperator | Grammar spec (Part 3) | Not frames |
| 1 | Universal frames and operations | GRAMMAR | StateChange, Transfer, Containment, Comparison, Interaction, Transformation |
| 2 | Functional and structural frames | GRAMMAR | FluidTransport, EnergyStorage, InformationProcessing, MaterialTransformation |
| 3 | Domain frames | DOMAIN | BloodCirculation, ElectricalEnergyStorage, ChemicalReaction, FinancialTransaction |
| 4 | Instances | Not definitions | A particular heartbeat, a particular transaction |

**SG-FRM-010.** A frame of layer *k* may SPECIALIZE only frames of layer ≤ *k*. Layer assignment is checked by the validator. Layer 4 never defines a frame.

**Authority mapping.** The sources define three rule-authority levels (foundational, grammar, domain) [F3-B §7.21]. These are not the same as abstraction layers. A layer-1 or layer-2 frame is changed by versioned grammar review (rule authority level 2). A layer-3 frame is a domain extension (level 3). Neither can alter the foundational rules (level 1, Part 5).

**Retrieval strategy.** For a medical sentence the system starts at domain-level frames and expands toward more general ones only when necessary. It does not load every frame (P-16, P-22).

---

## 4.12 The Foundation Package

[F3-B §7.3] The local model is told to select and combine approved elements, not to invent a semantic language per sentence.

### 4.12.1 The four components

| Component | Contents | Specified in |
|---|---|---|
| 1. Fundamental types | The semantic kinds | Part 2 §2.2 |
| 2. Fundamental operations | Reference, Apply, Bind, Negate, Quantify, Compose | Part 3: REF/KIND, APPLY, Q/VAR, NOT, Q, COMPOSE |
| 3. Reusable frames | The library in §4.12.2 | This part |
| 4. Formal construction rules | TYPE_COMPATIBILITY, FRAME_APPLICATION, ROLE_BINDING, NEGATION_SCOPE, VARIABLE_REFERENCE, EVIDENCE_REQUIREMENT | SG-TYP-001, SG-CON-002, SG-FRM-001 and SG-CON-003, Part 3 §3.7, SG-CON-005, SG-EVD-001 (full text in Part 5) |

Also in the package: the tier-1 role catalogue (Part 2), the starter relation catalogue (Part 2), the FN primitives (§4.8), and a **seed class set** that kernel constraints reference: AnimateEntity, Person, Organization, PhysicalObject, Substance, Fluid, EdibleEntity, Location, Artifact, Medication, Information.

### 4.12.2 Frame Library v0.1

K marks the **kernel** set (Part 12). The sources give about 10–20 frames and say the exact number comes from the benchmark [F3-C §8.29]. This set is chosen from the benchmark sentences in F1-A §3.16 and F3-C §8.21.

| Frame | Layer | Parent (link) | Key roles (tier-1 parent) | K |
|---|---|---|---|---|
| STATE_CHANGE | 1 | none | UNDERGOER, AGENT?, CAUSE?, INITIAL_STATE?, FINAL_STATE? | K |
| EXPERIENCE_STATE | 1 | none | EXPERIENCER, STATE, STIMULUS?, DEGREE? (ALLERGIC pins STATE) | K |
| MOVE | 1 | none | MOVER (THEME), AGENT?, SOURCE_LOCATION, DESTINATION_LOCATION, PATH?, MANNER?, TIME? | K |
| TRANSFER (abstract) | 1 | none | THEME, SOURCE, RECIPIENT, AGENT?; param DIMENSION {CUSTODY, POSSESSION, OWNERSHIP} | K |
| GIVE | 1 | TRANSFER (S) | AGENT, SOURCE, RECIPIENT, THEME | K |
| LEND | 1 | TRANSFER (S) | as GIVE; temporary possession | |
| OWNERSHIP_TRANSFER | 1 | TRANSFER (S) | DIMENSION = OWNERSHIP | |
| RETURN | 1 | TRANSFER (S) | RECIPIENT = prior SOURCE of a related transfer | K |
| COMMERCIAL_TRANSACTION | 1 | none | BUYER, SELLER, GOODS, MONEY, TIME? (composite, §4.12.3) | K |
| OWN | 1 | none | OWNER, OWNED_ENTITY, VALID_TIME? | K |
| LOCATED | 1 | none | LOCATED_ENTITY, LOCATION | |
| WORK | 1 | none | WORKER, WORKPLACE?, EMPLOYER? | K |
| PERCEIVE | 1 | none | EXPERIENCER, STIMULUS, INSTRUMENT?; param MODALITY (SEE, HEAR) | K |
| COMMUNICATE | 1 | none | SPEAKER (AGENT), ADDRESSEE (RECIPIENT), CONTENT, MEDIUM? | K |
| ATTITUDE (abstract) | 1 | none | EXPERIENCER, CONTENT | |
| BELIEVE, KNOW, WANT | 1 | ATTITUDE (S) | KNOW has a factive presupposition | K |
| ATTEMPT | 1 | none | AGENT, CONTENT (unasserted SIT), OUTCOME? | K |
| OFFER | 1 | none | OFFERER (AGENT), OFFEREE (RECIPIENT), CONTENT (unasserted SIT) | K |
| CAUSATION | 1 | none | CAUSE, EFFECT, MECHANISM?, CAUSE_TYPE (Part 3 §3.11) | K |
| EXAMINATION | 1 | none | EXAMINER (AGENT), EXAMINED_ENTITY (THEME), INSTRUMENT?, PURPOSE?, LOCATION?, TIME? | K |
| TREAT | 1 | none | PRACTITIONER (AGENT), TREATED_ENTITY (UNDERGOER), CONDITION?, INTERVENTION (INSTRUMENT)?, TIME? | K |
| EAT | 1 | none | EATER (AGENT, AnimateEntity), FOOD (UNDERGOER, EdibleEntity) | K |
| OPEN, CLOSE, HEAT, COOL, FREEZE | 1 | STATE_CHANGE (S, pinned params) | UNDERGOER | |
| TRANSFORMATION (abstract) and four typed children | 1 | none | INPUT, PROCESS, OUTPUT | |
| COMBINE, SEPARATE, COMPARE, SELECT, CREATE, DESTROY, STORE | 1 | none | per §4.9 | |
| CONTAINMENT, INTERACTION | 1 | none | CONTAINER/CONTENT; PARTICIPANTS | |
| COMPOSITE_STRUCTURE | 1 | none | WHOLE, PART+ | |
| TRANSPORT, FLUID_TRANSPORT | 2 | TRANSPORT (S) | §4.8.5 | |
| FLUID_CIRCULATION_SYSTEM | 2 | none | DRIVER, FLUID, CONDUIT | |
| ENERGY_STORAGE, INFORMATION_PROCESSING, MATERIAL_TRANSFORMATION | 2 | functional frames | per FN | |
| BLOOD_CIRCULATION | 3 | FLUID_TRANSPORT (S) | pinned Blood | |
| ELECTRICAL_ENERGY_STORAGE, CHEMICAL_REACTION, FINANCIAL_TRANSACTION | 3 | respective L2/L1 (S) | domain | |

K count: STATE_CHANGE, EXPERIENCE_STATE, MOVE, TRANSFER, GIVE, RETURN, COMMERCIAL_TRANSACTION, OWN, WORK, PERCEIVE, COMMUNICATE, BELIEVE, KNOW, WANT, ATTEMPT, OFFER, CAUSATION, EXAMINATION, TREAT, EAT = **20 frames**, within the sources' range.

New frames needed later (for example LEASE, F3-B §7.13) are proposed through the Part 9 pipeline. They are compared with RENT, LEND, BORROW, LICENSE, and OWNERSHIP_TRANSFER first.

### 4.12.3 Selected definitions

```text
FRAME TRANSFER  abstract  layer=1  params: DIMENSION ∈ {CUSTODY, POSSESSION, OWNERSHIP}
  roles: AGENT OPT; SOURCE REQ; RECIPIENT REQ; THEME REQ; TIME OPT
  semantics: final: RECIPIENT holds THEME under DIMENSION; initial: SOURCE holds THEME under DIMENSION
FRAME GIVE  SPECIALIZES TRANSFER  pinned DIMENSION = POSSESSION
  effects: ESSENTIAL recipient gains possession; TYPICAL recipient gains ownership
  perspectives: GIVE_VIEW (focus AGENT), RECEIVE_VIEW (focus RECIPIENT)
  hint: AGENT is SOURCE when SOURCE is not separately stated   (basis GRAMMATICAL)
  tests: "John gave Mary a book." valid;  "John offered Mary a book." NOT equivalent (contrastive)
```
```text
FRAME MOVE  layer=1
  roles: MOVER ⊑ THEME REQ; AGENT OPT; SOURCE_LOCATION ⊑ SOURCE OPT;
         DESTINATION_LOCATION ⊑ GOAL OPT; PATH OPT; MANNER OPT; TIME OPT
  state: initial LOCATED(MOVER, SOURCE_LOCATION); final LOCATED(MOVER, DESTINATION_LOCATION);
         process CHANGE_LOCATION; applies_when COMPLETED_VIEW
  note: a self-propelled mover binds the same referent to MOVER and AGENT (a referent may fill several roles)
  perspectives: ARRIVE (focus DESTINATION), DEPART (focus SOURCE)
```
```text
FRAME TREAT  layer=1
  roles: PRACTITIONER ⊑ AGENT REQ; TREATED_ENTITY ⊑ UNDERGOER REQ; CONDITION ⊑ THEME OPT;
         INTERVENTION ⊑ INSTRUMENT OPT; TIME OPT
  "The doctor treated the patient." → INTERVENTION UNSPEC (never invented)
  binding {INSTRUMENT: antibiotics} → rejected: frame defines INTERVENTION (E-45)
```
```text
FRAME WANT  SPECIALIZES ATTITUDE
  roles: EXPERIENCER REQ; CONTENT (SIT, unasserted) REQ
  control_hints: SUBJECT_CONTROL — the embedded situation's AGENT-like role co-refers with EXPERIENCER
  "The boy wants to eat an apple." → WANT(EXPERIENCER: R1, CONTENT: EAT(EATER: R1, FOOD: R2))
  R1 is ONE referent shared by both frames (graph, not duplicated tree); the embedded EATER binding has basis GRAMMATICAL
```
```text
FRAME COMMERCIAL_TRANSACTION  layer=1  composite
  roles: BUYER ⊑ AGENT REQ; SELLER ⊑ AGENT REQ; GOODS ⊑ THEME REQ; MONEY ⊑ THEME OPT; TIME OPT
  components: OWNERSHIP_TRANSFER(THEME=GOODS, SOURCE=SELLER, RECIPIENT=BUYER)
              OWNERSHIP_TRANSFER(THEME=MONEY, SOURCE=BUYER, RECIPIENT=SELLER)
  ordering: DEPENDENCY (each is in exchange for the other)
  perspectives: BUY (focus BUYER), SELL (focus SELLER), PAY, COST
  "John bought a car." → SELLER, MONEY UNSPEC;  "John bought the argument." → lexical sense BELIEVE (Part 8)
disjoint_roles: BUYER ≠ SELLER
```
```text
FRAME ATTEMPT  layer=1
  roles: AGENT REQ; CONTENT (SIT, unasserted) REQ; OUTCOME {ACHIEVED, FAILED, UNKNOWN} OPT
  no effects of CONTENT are entailed. "John tried to open the door." does not imply OPEN.
```

---

## 4.13 Frame tests, lifecycle, and provenance

**SG-FRM-008 (Normative).** A frame cannot leave PROVISIONAL status without a test set:
- at least one **valid** example
- at least one **incomplete** example (roles unspecified, no invention)
- at least one **invalid** example (a rule violation, with the expected error code)
- at least one **contrastive** pair that must *not* be treated as equivalent

These mirror the sources' three-way pattern of valid, incomplete, and invalid, plus the negative pairs that detect over-normalization [F3-C §8.18, §8.21, §7.22].

**Lifecycle.** A frame follows the candidate lifecycle (axis C): DISCOVERED → STRUCTURED → VALIDATED_FORMALLY → REVIEWED_SEMANTICALLY → CORROBORATED → PROMOTED. Manual core frames enter at PROMOTED after kernel review. Imported frames (FrameNet, VerbNet) enter as STRUCTURED with an ExternalMapping and are reviewed before promotion (Part 8).

**Versions.** A frame revision never overwrites. It proposes version n+1 with change description, motivation, examples, counterexamples, compatibility analysis, affected records, and test results [F3-B §7.24]. Existing records pin the old version. `derived_by` lists the generalization or learning rules that produced a learned frame, so a bad rule's output can be traced and reprocessed [F2-B §4.25].

---

## 4.14 Reconciling the examples in Part 3

Part 3's examples used illustrative role names. Under the frame library they normalize as follows.

| Part 3 example | Canonical form |
|---|---|
| `SEE(AGENT, THEME, INSTRUMENT)` | `PERCEIVE[MODALITY=SIGHT](EXPERIENCER, STIMULUS, INSTRUMENT)` |
| `HAVE(AGENT: man, THEME: telescope)` | `OWN` or a possession relation, with POSSESSOR and POSSESSED chosen by the sense |
| `EAT(AGENT, UNDERGOER)` | `EAT(EATER, FOOD)`. AGENT and UNDERGOER are tier-1 parents. |
| `ARRIVE`, `LEAVE` | `MOVE` with perspective variants ARRIVE and DEPART |
| `GIVE(AGENT, SOURCE, RECIPIENT, THEME)` | Valid as written |
| `ALLERGIC(EXPERIENCER, STIMULUS)` | `EXPERIENCE_STATE[STATE=ALLERGY]` |
| `FREEZE(UNDERGOER, FINAL_STATE)` | `FREEZE` pins PHASE = SOLID. FINAL_STATE is then redundant and is omitted. |
| `CANCEL(UNDERGOER)` | A seed domain frame outside the kernel. It remains a candidate name until promoted. |

---

## 4.15 Closing summary

**Rules registered in this part:**

| Rule | Subject |
|---|---|
| SG-FRM-002 (restated) | Specialization preserves parent commitments |
| SG-FRM-003 | Role narrowing and the projection test |
| SG-FRM-004 | Multiple-inheritance conjunction, no linearization |
| SG-FRM-005 | HAS_FUNCTION does not imply IS_A |
| SG-FRM-006 | Append-only role order |
| SG-FRM-007 | Analogy is not equivalence |
| SG-FRM-008 | Mandatory frame test set |
| SG-FRM-009 | FN primitives protected from automatic change |
| SG-FRM-010 | Layer discipline |
| SG-KNW-004 | Only ESSENTIAL constraints are inherited as exceptionless |
| SG-KNW-005 | Concept multiple-inheritance conflict classes |

**Enhancements introduced in this part:**

| ID | Issue | Resolution |
|---|---|---|
| E-07 | Two inconsistent function lists | Six primitives; PROCESS_INFORMATION and REGULATE as derived composites (§4.8.2) |
| E-06 | TRANSFER overload (completed in this part) | TRANSFER family with a DIMENSION parameter, GIVE / LEND / OWNERSHIP_TRANSFER, separate OFFER / ATTEMPT (§4.12) |
| E-41 | Strict inheritance cannot express "shares structure, not entailments" | Two link kinds: SPECIALIZES, STRUCTURAL_INSTANCE_OF (§4.5.1) |
| E-42 | Near-identical frames (open, close, heat…) | Parameters and parametric specialization (§4.4.3) |
| E-43 | Canonicalization of give/receive and buy/sell needed a declared scope | Perspective variants on the frame (§4.3.3) |
| E-45 | Tier-1 role names could bypass frame-specific roles | Closed role list per frame, with a hint to the frame-specific role (§4.3.1) |
| E-47 | Final-state entailments would wrongly follow progressive or attempted situations | Aspect-gated entailments (§4.4.1) |


---

# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 5 of 12: The Rulebook, the Semantic Derivation Protocol, and Validation

Parts 2–4 defined what can be represented. This part defines what is allowed to be stored, and how an AI-produced interpretation is checked before anyone relies on it. It turns the sources' central idea into a mechanism: the AI proposes a *machine-checkable derivation*, not a verbal explanation, and deterministic code decides what is admissible [F1-B §1, §7; F2-A §3.15, §3.25]. Evidence, truth status, review policy, and security are Part 6.

---

## 5.1 Principles of the Rulebook

1. **A rule citation is not a proof.** A model can cite the right rule while applying it to the wrong participant [F3-B §7.6]. A rule carries authority only through a checker that verifies it.
2. **A rule exists in three forms** [F3-C §8.18]: a human-readable description, a machine-readable specification, and test examples. A rulebook of English prompts alone is not a rulebook.
3. **The AI cannot invent rules.** It may cite only IDs already registered, at a version that is active [F2-A §3.15].
4. **Rules and checks are different things** (Enhancement E-48). A rule is a policy (what must hold). A check is an atomic validator function that tests part of a rule. Several checks can enforce one rule, and one check can serve several rules.
5. **Validation is a pure function.** The verdict depends only on (candidate, ontology release, ruleset release, validator version). This makes it reproducible and testable.

---

## 5.2 Two orthogonal dimensions (Enhancement E-49)

The sources give three rule *kinds* [F2-A §3.21; F3-B §7.7] and three *authority levels* [F3-B §7.21] and discuss them in different places. They are independent axes and every rule has a position on both.

**Kind: what the rule governs**

| Kind | Responsibility | Typical validation | Who relies on it |
|---|---|---|---|
| Construction | Valid expressions in the grammar | Deterministic | Validator |
| Interpretation | Mapping language constructions to semantic structures | Hybrid (deterministic parse conditions plus linguistic judgment) | Interpreter, validator |
| Knowledge | Domain relationships and inference | Logic plus evidence | Reasoner |

**Authority level: who may change it, and how**

| Level | Contents | Change process |
|---|---|---|
| 1 Foundational | Integrity rules (SG-FND-\*) | Never by the learning system or any AI. Out-of-band human release, and a separate review from the one that proposed the change. |
| 2 Grammar | Core construction, frame, type, canonicalization, and interpretation rules | Versioned proposal, regression on the benchmark, semantic review, promotion (Part 9) |
| 3 Domain | Domain frames and domain knowledge rules | Same pipeline, lighter review, more frequent |

A Level 3 rule cannot weaken a Level 1 or Level 2 rule. A rule at Level *n* may cite only rules at Level ≤ *n* as dependencies.

---

## 5.3 RuleDefinition

```text
RuleDefinition
  rule_id        SG-<DOMAIN>-<NNN>          aliases[]  (legacy and readable names)
  version, status (ACTIVE | DEPRECATED | CANDIDATE)
  kind           CONSTRUCTION | INTERPRETATION | KNOWLEDGE
  authority      1 | 2 | 3
  description    human-readable (for people and for prompts)
  spec           machine-readable conditions (below)
  checks[]       validation checks that enforce it
  check_class    D (deterministic) | H (hybrid) | R (needs review) | L (logic/evidence)
  depends_on[]   rule ids
  error_codes[]  codes raised on violation
  tests          valid[] · incomplete[] · invalid[] · contrastive[]
  rationale, source_tags, provenance
  released_in    ruleset release id
```

### Example 1: a construction rule (extends F3-C §8.18)

```json
{
  "rule_id": "SG-CON-002", "version": 1, "kind": "CONSTRUCTION", "authority": 2,
  "aliases": ["FRAME_APPLICATION", "FRAME_EXISTS"],
  "applies_to": "APPLY",
  "spec": {
    "frame_must_exist": true,
    "frame_version_must_be_pinned": true,
    "roles_must_be_defined_by_frame": true,
    "required_roles_must_be_bound_or_hole": true,
    "cardinality_must_hold": true,
    "type_compatibility_required": true,
    "referent_may_fill_multiple_roles_unless_disjoint": true
  },
  "checks": ["VC-S05", "VC-S06", "VC-S07", "VC-S08", "VC-T02"],
  "check_class": "D",
  "error_codes": ["VC-S05", "VC-S06", "VC-S07", "VC-S08", "VC-T02"],
  "status": "ACTIVE"
}
```

### Example 2: an interpretation rule (hybrid)

```json
{
  "rule_id": "SG-INT-010", "version": 1, "kind": "INTERPRETATION", "authority": 2,
  "aliases": ["PASSIVE_AGENT_MAPPING"],
  "check_class": "H",
  "spec": {
    "input_requirements": {
      "construction": "PASSIVE",
      "agent_phrase": "explicit by-phrase attached to the passive verb",
      "predicate": "recognised frame trigger"
    },
    "output": "bind the by-phrase referent to the frame's AGENT-descended role, basis=GRAMMATICAL",
    "deterministic_part": ["passive auxiliary + participle detected", "by-phrase attached to the participle"],
    "judgment_part": ["the by-phrase denotes the semantic agent in this construction"]
  },
  "tests": {
    "valid":      [{"text": "The patient was examined by the doctor.", "expect": {"EXAMINER": "doctor"}}],
    "incomplete": [{"text": "The patient was examined.", "expect": {"EXAMINER": "UNSPEC"}}],
    "invalid":    [{"text": "The house was built by the river.", "expect": "by-phrase is locative; no agent binding"}],
    "contrastive":[{"text": "The patient examined the doctor.", "expect": "different bindings"}]
  }
}
```

The invalid example is important: "by the river" has the surface shape of an agent phrase and is not one. This is why the check is hybrid. The deterministic part finds candidate by-phrases, and the judgment part (a model or review) decides whether the phrase is agentive. Without the second part the rule would turn locatives into agents.

**Mapping is by valence pattern, not by blanket subject-to-patient (Enhancement E-55).** In "Mary was given a book", the passive subject is the RECIPIENT, not the THEME. A rule saying "the passive subject becomes the affected role" would be wrong for ditransitives. The correct mapping depends on the verb sense's *valence pattern*: which grammatical function maps to which role in each construction. Valence patterns are recorded on lexical senses (Part 8, §8.5). SG-INT-011 (the source's PASSIVE_PATIENT_MAPPING) uses them, so the rule never hard-codes a subject-to-role correspondence.

### Example 3: a knowledge rule

```json
{
  "rule_id": "SG-KNW-010", "kind": "KNOWLEDGE", "authority": 2, "aliases": ["SUBCLASS_INHERITANCE_RULE"],
  "spec": { "if": ["A SUBCLASS_OF B", "X INSTANCE_OF A"], "then": "X INSTANCE_OF B", "derived_status": "INFERRED" },
  "check_class": "L",
  "note": "valid under class semantics. The premises' validity is a separate issue (Part 6)."
}
```

---

## 5.4 The consolidated rule index

Every explicit rule in Parts 1–4, every named rule in the sources, and the foundational rules the sources listed. Check class: D deterministic, H hybrid, R review-dependent, L logic or evidence. Level is the authority level.

### Foundational (Level 1, protected)

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-FND-001 | VALID_REFERENCE_REQUIRED (also FRAME_EXISTS, CONCEPT_ID_REGISTERED, RULE_ID_REGISTERED) | Every ID, rule, frame, role, and span reference resolves, to an active record or a tombstone | D |
| SG-FND-002 | TYPE_CHECKING_REQUIRED | The type check runs on every commit | D |
| SG-FND-003 | SOURCE_PROVENANCE_REQUIRED | Every committed assertion has a source or an authorized origin | D |
| SG-FND-004 | UNVERIFIED_CANDIDATES_CANNOT_SELF_APPROVE | No candidate, and no process that produced it, can promote it | D |
| SG-FND-005 | NO_UNAUTHORIZED_GRAMMAR_CHANGE, RULEBOOK_PROTECTED | No AI or learning process may modify FND rules, validator logic, or the rulebook. Only the governed release path may. | D |
| SG-FND-006 | AUDIT_APPEND_ONLY | Decisions and changes go to an append-only history | D |
| SG-FND-007 | CERTIFICATE_REQUIRED | AI-originated candidates carry a derivation certificate and a validation report before any promotion | D |

### Construction

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-CON-001 | SG-007 | A representation satisfies its frame's constraints | D |
| SG-CON-002 | FRAME_APPLICATION | Frame application well-formedness (§5.3) | D |
| SG-CON-003 | | Role fillers are referents, literals, kind-references, or nested descriptions, never bare concept IDs | D |
| SG-CON-004 | | Truth-conditional language features go in operators. Style-only features go in annotation. | D / H |
| SG-CON-005a–e | VARIABLE_REFERENCE | Closed assertions, no shadowing, alpha-equivalence, referents are not variables, anaphora under binders | D |
| SG-CON-006 | | Sort discipline | D |
| SG-CON-007 | | ALT well-formedness (≥2 same-sort members, ordinal support, bounded groups) | D |
| SG-CON-008 | | ERROR nodes only in candidates | D |
| SG-CON-009 | NEGATION_SCOPE (NEGATION_SCOPE_RULE) | Negation takes a proposition as argument. A negated situation is never stored as an occurred event record. | D |

### Type

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-TYP-001 | TYPE_COMPATIBILITY, TYPE_COMPATIBLE, FRAME_TYPE_VALIDATION | Three-valued role-type compatibility. INCOMPATIBLE needs a registered coercion. | D / L |
| SG-TYP-002 | | A figurative or coerced reading cites a registered mapping | H |

### Frame

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-FRM-001 | SG-002, ROLE_ASSIGNMENT, ROLE_ALLOWED, ROLE_BINDING | A role may be bound only if the frame defines it and evidence supports the binding | D / L |
| SG-FRM-002 | SG-FRAME-002, SG-INHERIT-001 | Specialization preserves parent commitments | D / L |
| SG-FRM-003 | | Role narrowing and the projection test | D |
| SG-FRM-004 | | Multiple-inheritance conjunction, no linearization | D / L |
| SG-FRM-005 | | HAS_FUNCTION does not imply IS_A | D |
| SG-FRM-006 | | Append-only role order | D |
| SG-FRM-007 | | An analogy is not an equivalence | D |
| SG-FRM-008 | | A frame needs a test set to leave PROVISIONAL | D |
| SG-FRM-009 | | FN primitives are protected from automatic change | D |
| SG-FRM-010 | | Layer discipline | D |

### Interpretation

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-INT-001 | SG-001 | An entity is typed only with sufficient evidence | H |
| SG-INT-010 | PASSIVE_AGENT_MAPPING | Passive by-phrase to agent role (§5.3) | H |
| SG-INT-011 | PASSIVE_PATIENT_MAPPING | Passive subject mapped by valence pattern | H |
| SG-INT-012 | ACTIVE_VOICE_MAPPING | Active constructions mapped by valence pattern | H |
| SG-INT-020 | NEGATION_SCOPE_MAPPING | Negation cue to operator scope. Scope ambiguity retained as ALT when unresolved. | H |
| SG-INT-021 | MODAL_FLAVOR_SELECTION | Modal cue to force × flavor. Ambiguous flavor stays ALT. | H |
| SG-INT-022 | QUANTIFIER_SCOPE_MAPPING | Quantifier phrase to Q with restrictor and scope | H |
| SG-INT-030 | SG-COREFERENCE | Pronoun and anaphor to antecedent referent, with evidence | H / R |
| SG-INT-031 | SG-EXPLANATORY-RELATION | "because" and similar to CAUSATION with an explanatory type | H |
| SG-INT-040 | SG-FRAME-TRANSFER (and per-frame equivalents) | Frame-trigger lexical sense to frame selection | H |
| SG-INT-050 | | Temporal expression to TIME value or relative expression | D / H |
| SG-INT-051 | | Tense and aspect cue to operator | H |

### Evidence

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-EVD-001 | SG-003, SG-EVIDENCE-003 | No unsupported content. Every element has a source span, a declared inference with valid premises, or an authorized source. | D / L |
| SG-EVD-002 | SG-004 | Preserve uncertainty and ambiguity | D |
| SG-EVD-003 | SG-006 | Separate observation from inference | D |
| SG-EVD-004 | | Presupposed content is emitted inside its context | D |
| SG-EVD-005 | SOURCE_SPAN_VALID | Spans exist, lie within the stored text, and the cited text matches the claim | D |
| SG-EVD-006 | | Basis integrity (§5.6) | D / L |

### Canonicalization

| Rule | Statement | Class |
|---|---|---|
| SG-CAN-001 | Canonical sharing only if the declared scope is preserved. Each rule has positive and negative tests. | D / H |
| SG-CAN-002 | Forbidden simplifications | D |
| SG-CAN-003 | Canonicalization audit trail | D |
| SG-CAN-004 | Structural equality ignores annotations | D |
| SG-CAN-010 (alias CANON_ACTIVE_PASSIVE_001) | Active and passive map to one canonical event frame when roles are identifiable | H |

### Identity, generalization, learning, knowledge, governance

| Rule | Alias | Statement | Class |
|---|---|---|---|
| SG-IDN-001 | SG-005 | Reuse existing concepts before proposing new | L |
| SG-IDN-002 | SG-IDENTITY-005 | Merge only when equivalence is established within scope | L / R |
| SG-IDN-003 | SG-MERGE-001 | Equivalence is a reversible, versioned mapping | D |
| SG-GEN-001 | SG-GENERALIZE-006 | Generalization preserves common relations and adds no unsupported claims | L / R |
| SG-GEN-002 | | No universal rule from observed examples alone | L |
| SG-GEN-003 | | GEN is not an exceptionless universal | D |
| SG-LRN-001 | | Check for an existing concept before proposing a new one for an unfamiliar word | L |
| SG-KNW-001 | | Open-world by default | D |
| SG-KNW-002 | | Associative weights are not truth values | D |
| SG-KNW-003 | | Opaque contexts block identity substitution | D |
| SG-KNW-004 | | Only ESSENTIAL constraints inherit as exceptionless | D |
| SG-KNW-005 | | Concept multiple-inheritance conflict classes | L |
| SG-KNW-010 | SUBCLASS_INHERITANCE_RULE | Class membership propagates up the subclass hierarchy | L |
| SG-KNW-011 | | Declared inverse relations are derived, not stored twice | D |
| SG-KNW-012 | | Declared relation properties (transitive, asymmetric, …) are enforced | D / L |
| SG-GOV-001 | SG-IDENTITY-002 | Changes to defining constraints require versioning, compatibility review, and review of affected records | D |
| SG-GOV-002 | | Rule changes go through rule change control (§5.12) | D |

SEC rules (source text as data, isolation) are in Part 6. Lesser decisions the sources describe as "rules" (for example CONCEPT_DUPLICATE_CHECK, which is a procedure of SG-IDN-001/002) are procedures in Part 7. Conflicting legacy IDs map as in Part 1, §1.7.2.

---

## 5.5 The foundational rules in detail

These are the system's integrity. The sources said the learning model must not modify them [F3-B §7.21], and that fundamental validation rules deserve stronger protection than ordinary knowledge [F3-B §7.20].

- **SG-FND-004 (no self-approval).** The author, the proposer, and any module in the proposing process cannot approve a candidate. Approval comes from a different component (validator, reviewer, promotion controller) and is recorded. A promotion record whose approver equals its proposer is invalid.
- **SG-FND-005 (protected rulebook).** The write path to rule definitions is separate from the write path to knowledge. It is not reachable from the model gateway, the learning engines, or the generalization engine. A proposed rule change is a *candidate rule record* until the governed release path accepts it (§5.12).
- **SG-FND-006 (append-only audit).** Promotion, rejection, merge, version change, and rule release events are appended. Corrections are new entries, not edits.
- **SG-FND-007 (certificate required).** No AI-originated candidate leaves the PROVISIONAL stage without a derivation certificate (§5.8) and a validation report (§5.7). A rule-derived or imported record carries an equivalent record of its origin.

---

## 5.6 The five validation levels, with checks and error codes

[F1-B §4] The levels differ in what they can promise.

| Level | Question | Class | Can be fully automated? |
|---|---|---|---|
| L1 Structural | Is it well-formed? | D | Yes |
| L2 Type | Are fillers compatible with roles? | D / L | Yes (three-valued, §3.3.2) |
| L3 Logical | Does it violate formal constraints? | D / L | Mostly |
| L4 Evidence | Does the source support the assertions? | D / H | Partly |
| L5 Contextual | Is the interpretation appropriate in context? | H / R | No |

Each check has an ID, which is also its error code when it fails (Enhancement E-48). Part 3 promised this code catalogue (§3.14.2).

### L1 Structural

| Check | Verifies | Rule |
|---|---|---|
| VC-S01 | Schema validity: types, required fields, no extra fields (Pydantic) | CON-001 |
| VC-S02 | Record header complete | FND-001 |
| VC-S03 | Every ID resolves (concept, referent, frame, relation) | FND-001 |
| VC-S04 | Every cited rule ID is registered at an active version | FND-001 |
| VC-S05 | Frame exists at the pinned version | CON-002 |
| VC-S06 | Every bound role is defined by the frame (closed role list, §4.3.1) | CON-002, FRM-001 |
| VC-S07 | Every REQUIRED role bound or in a hole state | CON-002 |
| VC-S08 | Cardinality limits | CON-002 |
| VC-S09 | Sort discipline | CON-006 |
| VC-S10 | Spans are within the stored text | EVD-005 |
| VC-S11 | No ERROR node in a canonical record | CON-008 |
| VC-S12 | No free variables | CON-005a |
| VC-S13 | No variable shadowing | CON-005b |
| VC-S14 | ALT well-formed | CON-007 |
| VC-S15 | No provisional ID in a trusted record | FND-001, invariant I-07 |
| VC-S16 | Nesting depth within limit. Composition and reference graphs acyclic. | CON-002, FRM-010 |

### L2 Type

| Check | Verifies | Rule |
|---|---|---|
| VC-T01 | Kind compatibility | TYP-001 |
| VC-T02 | Class compatibility (three-valued) | TYP-001 |
| VC-T03 | Value in the property's value domain, unit and dimension present | CON-001 |
| VC-T04 | No bare concept ID as a role filler | CON-003 |
| VC-T05 | Relation domain and range | CON-001 |
| VC-T06 | Disjoint roles do not share a referent | CON-001 |
| VC-T07 | A coercion or figurative reading cites a registered mapping | TYP-002 |
| VC-T08 | A value is not used where a property is expected | CON-006 |

### L3 Logical

| Check | Verifies | Rule |
|---|---|---|
| VC-G01 | Relations declared acyclic have no cycle | KNW-012 |
| VC-G02 | Declared relation properties hold (asymmetry, irreflexivity, transitivity) | KNW-012 |
| VC-G03 | No contradiction inside one context (a proposition and its negation both asserted) | EVD-002 |
| VC-G04 | Frame multiple-inheritance conflicts | FRM-004 |
| VC-G05 | ESSENTIAL consequences do not contradict explicit bindings | FRM-002 |
| VC-G06 | Temporal consistency: interval relations are jointly satisfiable | CON-001 |
| VC-G07 | Quantifier, negation, and modal scope well-formed | CON-009 |
| VC-G08 | Presupposed content emitted in its context | EVD-004 |
| VC-G09 | Opaque contexts respected (no identity propagated across an attitude boundary) | KNW-003 |
| VC-G10 | Canonicalization preserves its declared scope (rule test pairs pass) | CAN-001 |

A contradiction **across** sources is not a validation failure. It is stored as source-attributed claims and handled epistemically (Part 6), because logical consistency is not factual accuracy [F3-B §7.26].

### L4 Evidence

| Check | Verifies | Rule |
|---|---|---|
| VC-V01 | Every element has a span, a declared inference, or an authorized source | EVD-001 |
| VC-V02 | Cited span text lexically supports the claimed element | EVD-005 |
| VC-V03 | Basis labels match the derivation (§below) | EVD-006 |
| VC-V04 | Derivation chain complete (§5.8) | FND-007 |
| VC-V05 | Each cited rule's deterministic input requirements are met, and replay of deterministic steps matches | INT-\*, CAN-\* |
| VC-V06 | No role in a hole state is later filled by BACKGROUND content labelled as source-stated | EVD-001 |
| VC-V07 | Negation, modality, conditional, quantifier, and tense cues in the source are reflected by operators | INT-020, 021, 022, 051 |
| VC-V08 | Numeric and quantity cues match literals | INT-050 |
| VC-V09 | Inference premises are valid and each inference has a registered rule | EVD-001 |

**Basis integrity (SG-EVD-006).** An element's basis must match how it was derived:
- EXPLICIT requires span text that directly states it.
- GRAMMATICAL requires a registered interpretation rule whose preconditions hold.
- BACKGROUND requires a registered inference rule with premises, and the resulting status is INFERRED, never SOURCE_ASSERTED.

A BACKGROUND element is never relabelled EXPLICIT. This is how "location = hospital" is stopped when "The doctor examined the patient" does not say so [F2-A §3.14].

### L5 Contextual

| Check | Verifies | Class |
|---|---|---|
| VC-C01 | The selected word sense is plausible given context cues and the alternatives | H / R |
| VC-C02 | Coreference is plausible. No competing antecedent was ignored. | H / R |
| VC-C03 | Operator scope is plausible, and a competing scope was considered | H / R |
| VC-C04 | The alternatives that remain are real and none was silently dropped | H |
| VC-C05 | Metamorphic consistency with paraphrase variants (§5.11) | H |
| VC-C06 | Consistency with existing trusted knowledge. A conflict raises review or a disputed status, not a silent rejection. | L / R |
| VC-C07 | Reviewer verdict, where review was requested | R |

### What cannot be caught: structurally valid but wrong

```text
Source:      The patient was examined by the doctor.
Candidate:   EXAMINATION{ EXAMINER: patient, EXAMINED_ENTITY: doctor }
L1 (schema):   PASS      L2 (types): PASS (both are persons)     L3 (logic): PASS
L4 (evidence): FAIL VC-V05 / VC-V02 — SG-INT-010 requires the by-phrase referent to be the EXAMINER;
                         the span for EXAMINER ("patient", [4,11)) is not the by-phrase [25,38)
```

L1–L3 alone would accept this. The catch comes only from the rule's deterministic input requirement and span check, which is why the derivation certificate cites spans and rules. For a swap where *both* readings satisfy every rule (the sentence is truly ambiguous), the right result is AMBIGUOUS or UNRESOLVED, not a confident pick (SG-EVD-002).

---

## 5.7 Aggregation, triage, and repair

Validation produces a **ValidationReport**:

```text
ValidationReport
  candidate_id, candidate_version
  validator_version, ruleset_release, ontology_release
  results[]        (check_id, level, result PASS|FAIL|UNCERTAIN|NOT_CHECKED, detail, element_ref)
  aggregate        INVALID | UNCERTAIN | FORMALLY_VALID    (axis B)
  risk_class       from Part 6
  route            REPAIR | REJECT | REVIEW | ACCEPT_PROVISIONAL | PRESERVE_AMBIGUITY
  outcome          axis A value
```

**Aggregation (Normative).**
1. L1 failure short-circuits. L2 and later checks that depend on resolving references are NOT_CHECKED.
2. Any FAIL in L1–L4 yields **INVALID**.
3. Else, any UNCERTAIN, or any hybrid or review check not yet resolved, yields **UNCERTAIN**. Examples: UNDETERMINED type, unresolved coreference, hybrid judgment pending.
4. Else the candidate is **FORMALLY_VALID**: it passed every deterministic check. This says nothing about L5. The sources are explicit that formally valid does not mean semantically correct [F1-B §6].

**Routing.**

| Aggregate | Condition | Route |
|---|---|---|
| INVALID | Repairable error codes and retries remain | REPAIR |
| INVALID | Not repairable, or retries exhausted | REJECT, recording the codes. The unit becomes UNRESOLVED (outcome) |
| UNCERTAIN | A review queue is available | REVIEW. If the uncertainty is genuine ambiguity of the source, PRESERVE_AMBIGUITY instead |
| FORMALLY_VALID | Risk class low (Part 6) | ACCEPT_PROVISIONAL, with audit sampling |
| FORMALLY_VALID | Risk class not low | REVIEW |

ACCEPT_PROVISIONAL sets lifecycle stage VALIDATED_FORMALLY, and nothing higher. Promotion to trusted knowledge is a separate governed step (Part 6, Part 9).

**Repair loop.**
- The model receives the **error codes and the text of the violated rule**, and the specific element refs. It does not see the validator's internals.
- Each retry is a new candidate version linked to its parent. The workspace keeps versions (P-20).
- Retry limits and budgets are enforced by the central controller [F3-B §7.8, §7.30]. [Provisional: default 2 retries per unit.]
- Retries are not unlimited. If a case cannot be resolved reliably it is preserved as unresolved (§5.10).

**Review hook.** A reviewer's correction passes the same validator [F1-B §6]. Reviewer verdicts include "insufficient information to determine the intended meaning" (Part 6).

**Certificate and report together** satisfy the "validation certificate" of the sources [F1-B §3]:

| F1-B §3 item | Where |
|---|---|
| Semantic pattern and frame used | Certificate steps |
| Source evidence for each assignment | Certificate steps (spans) |
| Rule IDs used | Certificate steps |
| Unresolved ambiguities | Certificate (`unresolved`), plus ALT in the IR |
| Validation results | ValidationReport |

---

## 5.8 The Semantic Derivation Protocol (SDP)

[F1-B §7, §15; F2-A §3.15; F3-B §7.5–7.6] The AI submits a **derivation** and not an explanation. The protocol is the third specification the sources said to build before the validator [F1-B §15]. The first two are Parts 2–3 (type system, grammar) and Part 4 (frame library).

### 5.8.1 The derivation chain

```text
SOURCE_SPAN → LEXICAL_SENSE → SEMANTIC_FRAME → ROLE_ASSIGNMENT → SEMANTIC_ASSERTION
```

Each transition cites a rule. The chain is extended where needed:

| Step type | Records |
|---|---|
| REFERENT_CREATION | A span introduces a referent (kind, instance_of, number, cardinality) |
| COREFERENCE | A link between referents, with evidence |
| LEXICAL_SENSE | A trigger span selects a sense and its concept candidates |
| FRAME_SELECTION | A frame (and perspective variant, parameter pins) |
| ROLE_ASSIGNMENT | A role binding with value state and basis |
| OPERATOR_ATTACHMENT | Negation, modality, tense, aspect, quantifier, attribution |
| FIGURATIVE_MAPPING | A literal-to-contextual mapping |
| CANONICALIZATION | A canonicalization rule applied |
| INFERENCE | A background inference, with premises |

### 5.8.2 The certificate

```text
DerivationCertificate
  certificate_id, certificate_version, parent_certificate (for retries)
  source_id, text_hash
  grammar_version, ontology_release, ruleset_release
  producer
    kind          MODEL | RULE_ENGINE | HUMAN | IMPORT
    model_id, runtime, prompt_template_id + hash, sampling params, schema_version
  steps[]
    step_id, step_type
    inputs        spans, referent ids, concept ids, earlier step ids
    output        record/expression reference
    rule_id, rule_version
    basis         EXPLICIT | GRAMMATICAL | BACKGROUND
    evidence      spans
    alternatives_considered[]    (what else the producer weighed)
  candidate_expression           the compiled IR (Part 3)
  unresolved[]                   points the producer could not resolve
  interpretation_outcome         RESOLVED | AMBIGUOUS | UNRESOLVED
  retention_tier                 FULL | COMPACT (§5.8.4)
```

Run metadata (model, prompt template, sampling parameters) exists for fault localization. When an error appears the record shows whether the model, the parser, a rule, or a frame definition produced it [F3-C §8.19].

### 5.8.3 Worked certificate

Source (39 characters including the full stop): `The patient was examined by the doctor.`
Offsets are zero-based, end-exclusive, in code points.

```json
{
  "source_id": "S001", "grammar_version": "1.0", "ruleset_release": "R-0.1",
  "producer": {"kind": "MODEL", "model_id": "<local-model>", "schema_version": "1"},
  "steps": [
    {"step_id": "s1", "step_type": "REFERENT_CREATION", "inputs": {"span": [0, 11]},
     "output": "E1", "rule_id": "SG-INT-001", "basis": "EXPLICIT",
     "concept": "PATIENT", "number": "SINGULAR", "definiteness": "definite"},
    {"step_id": "s2", "step_type": "REFERENT_CREATION", "inputs": {"span": [28, 38]},
     "output": "E2", "rule_id": "SG-INT-001", "basis": "EXPLICIT", "concept": "DOCTOR"},
    {"step_id": "s3", "step_type": "LEXICAL_SENSE", "inputs": {"span": [16, 24]},
     "output": "FRAME_TRIGGER:EXAMINATION", "rule_id": "SG-INT-040", "basis": "GRAMMATICAL"},
    {"step_id": "s4", "step_type": "ROLE_ASSIGNMENT", "inputs": {"span": [0, 11], "referent": "E1", "step": "s3"},
     "output": "EXAMINED_ENTITY=E1", "rule_id": "SG-INT-011", "basis": "GRAMMATICAL",
     "evidence": [[0, 24]]},
    {"step_id": "s5", "step_type": "ROLE_ASSIGNMENT", "inputs": {"span": [25, 38], "referent": "E2", "step": "s3"},
     "output": "EXAMINER=E2", "rule_id": "SG-INT-010", "basis": "GRAMMATICAL",
     "evidence": [[25, 38]]},
    {"step_id": "s6", "step_type": "CANONICALIZATION", "inputs": {"steps": ["s4", "s5"]},
     "output": "APPLY(EXAMINATION, ...)", "rule_id": "SG-CAN-010", "basis": "GRAMMATICAL"}
  ],
  "unresolved": [],
  "interpretation_outcome": "RESOLVED"
}
```

Spans: "The patient" = [0,11), "examined" = [16,24), "the doctor" = [28,38), "by the doctor" = [25,38). The derivation exposes exactly what Python checks (§5.6): rule IDs exist, spans lie within the text, the frame and roles are defined, SG-INT-010's deterministic precondition (passive plus by-phrase) holds in the parse, and replaying s6 reproduces the candidate expression.

### 5.8.4 Replay and retention (Enhancements E-50, E-54)

**Replay verification (VC-V05).** For every step whose rule is class D, the validator **re-executes** the rule on the step's inputs and compares the output with the claim [F1-B §7]. For H and R steps (judgments such as sense choice) it checks only that the evidence is present and the rule's deterministic preconditions hold. This is traceable evidence and not a mathematical proof.

**Retention.** Certificates cost storage on a personal computer [P-22].
- **FULL** is kept for candidates, reviewed, disputed, ambiguous, and learning-relevant records.
- **COMPACT** is kept for low-risk, rule-derived, accepted records: rule IDs, spans, and a hash of the full certificate. The full certificate can be **regenerated by replay** when the derivation is deterministic. A COMPACT record whose replay fails is flagged for FULL reprocessing.

---

## 5.9 What the AI may and may not do

[F2-A §3.25; F1-B §1; F3-B §7.35] The sources said the control comes from software permissions and validation, not from natural-language prompts.

| Operation | Allowed? |
|---|---|
| Select an existing concept, frame, or lexical sense from retrieved candidates | Yes |
| Assign supported roles, identify evidence spans | Yes |
| Propose an interpretation and report ambiguity | Yes |
| Cite rule IDs that exist | Yes |
| Propose a new concept or frame (as a candidate, for review) | Yes |
| Choose NONE_OF_THESE when no retrieved candidate fits | Yes |
| Modify the authoritative grammar or the rulebook | **No** |
| Merge concept identities | **No** |
| Mark an interpretation verified | **No** |
| Invent new rule IDs and treat them as authoritative | **No** |
| Commit unvalidated assertions | **No** |
| Remove conflicting evidence | **No** |
| Replace uncertainty with unsupported certainty | **No** |
| Approve its own proposal | **No** |

**Enforcement is structural.** SQLite has no user accounts, so permissions are enforced at the application layer:
- The **model gateway** returns only schema-validated `Candidate` objects. It holds no handle to the registry or to the rulebook's write path.
- Only the **Registry commit API** writes authoritative tables, and it accepts only items carrying an approved validation report from a different component (SG-FND-004).
- The Rulebook is read-only to every module except the governed release path (SG-FND-005).
- A different connection or API capability is used per role: proposer, validator, reviewer, registry writer, release manager.

**Closed-set selection (Enhancement E-51).** The model is shown the retrieved candidate concepts, frames, and rules from the registry, and selects by ID. The output schema has an explicit `NONE_OF_THESE` and `NEEDS_NEW_CONCEPT` option. A model forced to pick one of several wrong candidates would produce a wrong but valid-looking result, so the escape is part of the protocol. This reinforces SG-IDN-001 and SG-LRN-001. Duplicate concepts such as FinancialBank, BankingInstitution, and BankCompany come from letting the model invent labels [F1-A §3.4].

**Form versus meaning.** Constrained decoding (JSON schema or a generation grammar) enforces the *form* of the output. It never enforces its *meaning* [F3-C §8.2]. Schema validity is VC-S01. Everything from VC-S03 upward is still required.

---

## 5.10 Outcomes and guarantees

**Outcomes** (axis A) [F3-B §7.33]: RESOLVED, AMBIGUOUS, UNRESOLVED.

| Outcome | Stored as |
|---|---|
| RESOLVED | Canonical IR |
| AMBIGUOUS | IR with ALT group(s) and per-alternative support. A reviewer or later context can select. |
| UNRESOLVED | Source record plus candidate with the unresolved points listed, ready for retry when context arrives |

A reliable system must sometimes refuse to choose a meaning. "John saw the man with the telescope" has no determinable reading without context. That is a faithful representation of the evidence, not a failure of the grammar.

**Engineering guarantees the system makes** (each enforced by a rule and a check) [F3-B §7.33]:

| # | Guarantee | Enforced by |
|---|---|---|
| G-1 | Every committed frame reference points to an existing approved frame | FND-001 / VC-S05 |
| G-2 | Every role ID is valid under the declared schema | VC-S06 |
| G-3 | Every accepted concept ID is registered | VC-S03 |
| G-4 | Every stored span refers to actual source text | VC-S10, EVD-005 |
| G-5 | Every encoded record decodes exactly | Part 11 round-trip |
| G-6 | Every authoritative change follows the approval process | FND-004, FND-005 |
| G-7 | No element is stored as source-stated without a supporting span or authorized origin | EVD-001, EVD-006 |
| G-8 | No provisional ID appears in trusted knowledge | VC-S15 |

**What is not guaranteed:** that an arbitrary natural-language sentence is interpreted correctly. The system can prevent identifiable errors, preserve unresolved ambiguity, and refuse to treat unverified interpretations as established knowledge [F1-B §4]. That is the strongest design achievable.

---

## 5.11 Testing the rulebook

[F3-C §8.19–8.20; F1-C §11; F3-B §7.22] Every rule has tests that do not depend on any AI model. This separates a model error from a parser error, a frame error, a resolver error, a rule-implementation error, or a validator error.

### 5.11.1 Test case schema

```text
TestCase
  id, category, input_text (or input_ir for non-language tests)
  expected_ir          canonical expression
  allowed_variants     acceptable alternatives (ALT sets)
  must_not_contain     forbidden content, e.g. an invented location
  preserved_dimensions frame | bindings | polarity | modality | time | referents
  rules_exercised[]
  pair_id              for contrastive and metamorphic pairs
```

Equality is over the canonical IR **up to referent renaming**. Two referents in different sentences are never identified as one by a test.

### 5.11.2 Metamorphic pairs

The comparison relation is stated explicitly. Not every transformation preserves every detail [F1-C §11].

| Transformation | Relation required | Assumption |
|---|---|---|
| Active ↔ passive (dog chased cat / cat was chased by dog) | EQUIVALENT on frame, bindings, polarity, time. Voice differs only in annotation. | Agent expressed |
| Passive with and without by-phrase | The shorter projects from the longer: the omitted role is UNSPEC and nothing is invented | |
| Give / receive perspective | EQUIVALENT on bindings under GIVE perspective variants. **Not** the same event occurrence unless context identifies it. | Perspective variant declared |
| Synonym substitution (car / automobile) | Same concept ID. **Not** the same referent. | Same sense |
| Reordering independent sentences | Same assertion set up to renaming | No cross-sentence anaphora |
| Equivalent numerals ("two" / "2") | Same cardinality | |
| Explicit vs. implicit role | Explicit ⊒ implicit under projection | |

### 5.11.3 Negative pairs (must NOT be treated as equivalent)

| Pair | Differs on |
|---|---|
| gave / offered | Frame (GIVE vs OFFER), realization |
| tried to open / opened | ATTEMPT vs completed STATE_CHANGE |
| did not eat the apple / ate the apple | Polarity |
| did not eat every apple / ate no apple | Quantifier and negation scope |
| may leave / must leave | Force |
| believes / knows | Factivity (presupposition) |
| The patient was given medication / The patient was given medication by the doctor | Agent UNSPEC vs specified |

Negative pairs detect over-aggressive canonicalization, which is a different failure from under-extraction.

### 5.11.4 Stage-isolated test modes

| Test mode | Fixed (gold) inputs | Component under test |
|---|---|---|
| Rule unit | A gold parse | The rule implementation |
| Validator | A gold or deliberately corrupted IR | The validator |
| Selection | Gold candidate sets | The model's selection behaviour |
| Parser | Raw text, gold dependency labels | The linguistic parser |
| End-to-end | Raw text, gold IR | The whole pipeline |

When an end-to-end case fails, stage-isolated runs show which stage produced the error. Metrics are Part 12.

### 5.11.5 Property-based tests

With a generator of valid IR (Hypothesis):
- The validator is deterministic and total (no crash on any candidate).
- Canonicalization is idempotent: `canon(canon(x)) = canon(x)`.
- Canonicalization preserves validity.
- Alpha-renaming does not change the verdict or the canonical form.
- Every valid-by-construction expression passes L1–L3.
- Every injected single fault is detected by its designated check.

(Binary round trip belongs to Part 11.)

---

## 5.12 Rule lifecycle and change control (SG-GOV-002)

**Proposal.** A rule change may come from a human, or from a pattern analysis of validation errors or corrections [F3-B §7.19, §7.32]. It is a candidate rule record until released.

**Release gate** (all required):
1. The rule's tests, and the **entire** regression suite, pass.
2. Benchmark non-degradation on **held-out examples**. The change is not fitted to the errors that motivated it, to avoid overfitting to recent mistakes [F3-B §7.29].
3. Semantic review of the change, for Level 2 and Level 3.
4. Level 1 changes need an out-of-band human release (SG-FND-005).
5. A compatibility analysis lists the records produced by the old rule version, found by certificate lookup (SG-CAN-003), and states whether they are re-validated, migrated, or flagged.

**Learning from corrections** [F3-B §7.32]. A single correction does not rewrite a rule. After enough reviewed examples the Learning Controller may *propose* a more specific rule. It must be tested against distinguishing cases, for example passive constructions with and without an explicit agent. "The patient was given medication" has no stated agent, and a rule learned from "…by the doctor" must not invent one.

**Versions.** Rules are pinned by certificates. A deprecated rule remains resolvable. Its removal triggers a re-check list.

**Validator integrity.** Every ValidationReport records the validator version and the hash of the ruleset release. The validator itself is Level 1 protected code. A change to it is a governed release and the full suite runs on the new version against the gold corpus.

---

## 5.13 Summary

**Closure of the sources' open items in this part**

| Source item | Closed in |
|---|---|
| Machine-readable Semantic Rulebook (F1-B §2, F3-C §8.18) | §5.3–§5.4 |
| Semantic Derivation Protocol (F1-B §15) | §5.8 |
| Validation certificate (F1-B §3) | §5.7–§5.8 |
| Five validation levels (F1-B §4) | §5.6 |
| Rule hierarchy and learner protection (F3-B §7.21) | §5.2, §5.5, §5.12 |
| Permitted and restricted AI operations (F2-A §3.25) | §5.9 |
| Rule tests independent of the AI (F3-C §8.19) | §5.11 |
| Metamorphic and negative tests (F1-C §11, F3-B §7.22) | §5.11 |
| Grammar versioning of rules (F2-B §4.25) | §5.12 |
| Error codes (promised in Part 3) | §5.6 |

**Enhancements introduced in this part**

| ID | Issue | Resolution |
|---|---|---|
| E-48 | Rules and their checks were conflated, and there was no error-code catalogue | Rule (policy) separated from Check (atomic function). Check ID is the error code. |
| E-49 | Rule kinds and authority levels discussed separately | Two orthogonal dimensions (§5.2) |
| E-50 | Deterministic derivation steps were not independently verifiable | Replay verification (§5.8.4) |
| E-51 | A forced choice among wrong candidates yields valid-looking errors | Closed-set selection with NONE_OF_THESE and NEEDS_NEW_CONCEPT (§5.9) |
| E-52 | Protection of the validator and rulebook was stated but not enforced | Separate write paths, role-separated capabilities, validator hash in reports (§5.9, §5.12) |
| E-53 | Schema validation was treated as meaning validation | Form and meaning separated. The schema check is only VC-S01 (§5.9) |
| E-54 | Certificate storage cost not budgeted | FULL and COMPACT retention tiers with replay (§5.8.4) |
| E-55 | "Passive subject becomes patient" fails for ditransitives (Mary was given a book) | Mapping by valence pattern from lexical senses (§5.3, Part 8) |


---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 6 of 12: Evidence, Provenance, Truth Status, Review, and Security

Part 5 decides whether a candidate is admissible. This part decides what an admitted claim is worth, how that standing changes over time, who reviews what, and how the system defends itself against bad input. The organizing idea comes from the sources: **what a sentence means is a different question from whether it is true** [F1-B §12], and a validated interpretation of a false sentence is still a validated interpretation.

---

## 6.1 Three questions, three mechanisms

| Question | Answered by | Where |
|---|---|---|
| What does the source say? | Grammar and derivation | Parts 3–5 |
| What is the standing of the claim? | Epistemic status (axis D), commitment holder, evaluation context | §6.2–§6.3 |
| How strong is the support? | Evidence vector, derived label, source independence | §6.4–§6.6 |

Two supporting mechanisms follow: who reviews what (§6.8–§6.10) and how the system resists hostile or defective input (§6.11).

---

## 6.2 Commitment holder and evaluation context (Enhancement E-56)

The sources track *who asserted* only through source and attribution operators. Two things a claim needs beyond its content are missing, and both decide whether it can ever count as knowledge.

**Commitment holder.** Who stands behind the claim. Every assertion has exactly one value.

| Value | Meaning |
|---|---|
| AUTHOR | The source's author commits to it |
| ATTRIBUTED(x) | The author reports that x commits to it ("John said it rained"). The claim is x's, as reported. |
| NONE | No one commits: hypothetical, supposed, asked, ordered, or quoted for discussion |

The `ATTRIBUTE` operator and the embedding structure of Part 3 fix this value deterministically. "John believes Mary knows the meeting was cancelled" commits John to nothing about the meeting, and the author to nothing but John's belief.

**Evaluation context.** In what world the claim is meant to hold.

| Value | Meaning |
|---|---|
| WORLD | The actual world |
| FICTION(work) | A fictional world ("Sherlock Holmes lived at 221B Baker Street") |
| HYPOTHETICAL(context) | A supposed scenario |
| HISTORICAL_BELIEF(community, period) | What a community once held |
| DOMAIN_MODEL(theory) | Inside a stated theory or definition (LIFE under a given biological definition) |

**Rule SG-EVD-007.** A claim can enter the trusted knowledge view (§6.7) only if its commitment holder is AUTHOR, its context is WORLD (or a declared DOMAIN_MODEL), and it satisfies the evidence policy. Claims in other contexts are stored and retrievable with their context. They are never silently mixed with world claims. A source's genre (news, fiction, satire, instruction, scientific paper) is recorded on the Source record and is one input to the context.

---

## 6.3 The epistemic status axis (axis D)

### 6.3.1 Values

| Status | Meaning | Default for |
|---|---|---|
| SOURCE_ASSERTED | The source (its commitment holder) claims this. Verification has not been attempted or has not concluded. | Extracted content |
| INFERRED | The system derived this by a registered inference rule from premises. It was not stated. | Background inferences, derived entailments |
| VERIFIED | The claim satisfies the evidence policy for its scope (§6.6) and is not contradicted by stronger evidence | Claims promoted through §6.7 |
| DISPUTED | Credible conflicting evidence exists. A `dispute_kind` explains why. | Conflict clusters |
| UNKNOWN | Evaluation was attempted and could not conclude, or the content cannot be evaluated | Failed or inconclusive evaluation |

**Dispute kinds** (the explanations the source lists for apparent contradictions [F3-B §7.26]):

`CONFLICTING_SOURCES` · `CONTRADICTED_BY_AUTHORITY` · `CONTEXT_DEPENDENT` (different conditions) · `POPULATION_DEPENDENT` (different groups studied) · `DEFINITION_DEPENDENT` (concepts defined differently) · `INCOMPLETE_EVIDENCE` · `PARSING_SUSPECT` (the contradiction may come from a wrong interpretation)

### 6.3.2 Allowed transitions

| From → To | Trigger | Who may cause it |
|---|---|---|
| (new) → SOURCE_ASSERTED | Extraction passes validation | Validator |
| (new) → INFERRED | Derivation through a registered rule (SG-EVD-001/003) | Rule engine |
| SOURCE_ASSERTED → VERIFIED | Evidence policy met (§6.6) | Evaluation process only (SG-EVD-009) |
| SOURCE_ASSERTED → DISPUTED | A conflict cluster forms with credible evidence | Evaluation process |
| SOURCE_ASSERTED → UNKNOWN | Evaluation attempted, inconclusive | Evaluation process |
| INFERRED → VERIFIED | Independent evidence for the conclusion itself | Evaluation process. A valid derivation alone is not enough. |
| DISPUTED → VERIFIED / UNKNOWN | The dispute is explained and resolved with evidence | Evaluation, with review |
| VERIFIED → DISPUTED | New credible conflicting evidence | Evaluation, never silent |
| any → DEPRECATED (lifecycle axis) | Superseded | Registry |

**Forbidden transitions (SG-EVD-003, SG-EVD-009):**
- INFERRED never becomes SOURCE_ASSERTED. A background inference is never relabelled as stated.
- SOURCE_ASSERTED never becomes VERIFIED because it was repeated, retrieved often, activated, or promoted by the AI. **Repetition is not corroboration**, and activation controls accessibility, not truth [F1-C §9].
- No module that produced a claim, including the interpreter, the learning engines, and the generalization engine, sets axis D beyond SOURCE_ASSERTED or INFERRED.

### 6.3.3 Worked cases

| Source sentence | Meaning record (Part 3) | Axis D after evaluation |
|---|---|---|
| "The sun revolves around the Earth." | A REVOLVE description with MOVING_ENTITY = Sun and REFERENCE_ENTITY = Earth, correctly interpreted [F1-B §12] | SOURCE_ASSERTED → DISPUTED (`CONTRADICTED_BY_AUTHORITY`). Kept as a claim, not added to the verified view. Retrievable under HISTORICAL_BELIEF if the source context supports it. |
| "Every bird can fly." / "Penguins cannot fly." | `Q(FORALL, bird, can_fly)` as written by source 1. A penguin statement by source 2. | Both SOURCE_ASSERTED. The first is never promoted to an ontological law (SG-GEN-002/003). The verified view carries typical-flight knowledge (`TYPICALLY_HAS`) only after evidence and review [F1-D §2.26]. |
| "The engine stopped because it overheated." | CAUSATION with `CAUSE_TYPE = EXPLANATORY_REASON`, origin SOURCE_TEXT | SOURCE_ASSERTED. The mechanism is not verified by the system. A reasoning module may derive "overheating could plausibly cause stopping", which is INFERRED and labelled as such [F2-A §3.13]. |

---

## 6.4 The evidence vector

[F1-B §8.5] The evidence ladder E0–E5 mixes different dimensions, and the source warns that formal derivation and source reliability are not the same [Enhancement E-03]. The evidence **vector** is the primary record. The E-label is a derived routing aid.

### 6.4.1 Dimensions

```text
EvidenceVector   (one per assertion; also per candidate concept, frame, mapping)
  source_evidence       SourceEvidence[]
      source_id, spans, support_kind DIRECT | SYNTACTIC | IMPLIED | NONE,
      commitment_holder, evaluation_context
  extraction            ExtractionRecord[]  (method, producer, certificate_id, method_error_class)
      method ∈ RULE_ENGINE | PARSER | MODEL_PRIMARY | MODEL_REVIEWER | HUMAN | IMPORT
  rule_validation       ValidationSummary   (validator_version, ruleset_release, aggregate, levels run)
  derivation            premises[], rule_id, rule_version   (INFERRED claims only)
  corroboration         independent_support_count, supporting[], contradicting[], independence_graph_ref
  uncertainty           ambiguity_alternatives, unresolved_points, type_warnings, vague_quantifiers
  review                ReviewRecord[]  (stage, reviewer kind, verdict, date)
  authority             curator, scope (domain, claim type), date, expires?
```

### 6.4.2 Derived label (Enhancement E-03)

The label is computed from the vector by a fixed function. It is a **workflow state**, not a probability, not a truth value, and not a total order.

| Label | Name | Computed when | Default handling |
|---|---|---|---|
| E0 | UNSUPPORTED | Any L1–L4 FAIL, or no source evidence, or `support_kind = NONE` | Reject |
| E1 | HYPOTHESIS | Not E0, and (aggregate UNCERTAIN, or an element rests on unvalidated BACKGROUND, or the unit is AMBIGUOUS or UNRESOLVED) | Retain as hypothesis. Not used for reasoning. |
| E2 | SOURCE_SUPPORTED | FORMALLY_VALID, span-grounded in at least one source, no unresolved uncertainty | Provisional storage |
| E3 | CORROBORATED | E2, plus support from at least two **independent** origins (§6.5), or an independent extraction method agreeing and audited | Eligible for promotion |
| E4 | DERIVED | INFERRED via a registered rule from premises that are all at least E2 | Stored with its derivation. See cap below. |
| E5 | CURATED | Confirmed by an authority within a declared scope (§6.6) | Trusted within that scope only |

**Derivation cap (Normative, SG-EVD-012).** An E4 claim is only as supported as its weakest premise. It carries `support_cap = min(premise levels)`, and the cap is what routing and ranking use. "A conclusion can be correctly derived from a false premise" [F1-B §8.5], so a valid derivation never raises support.

**Curation scope (Normative).** E5 is valid **only inside its declared scope** and until its expiry. A curated claim in one domain says nothing outside it.

The label order E0 < E1 < E2 < E3 is a support ladder. E4 and E5 are different dimensions (derivation validity and authority) and are not "higher" than E3 in reliability.

### 6.4.3 What each label permits

[Adapted from the source and the REF evidence-ladder rules.] Interpretation and reasoning are not equally safe at every level.

| Use | E0 | E1 | E2 | E3 | E4 | E5 |
|---|---|---|---|---|---|---|
| Store at all | No | Hypothesis store | Yes (provisional) | Yes | Yes | Yes |
| Retrieval, with label | No | Yes, flagged | Yes | Yes | Yes | Yes |
| Premise for further inference | No | No | Attributed ("according to S") | Yes | Capped by `support_cap` | Within scope |
| Input to pattern and generalization discovery | No | No | Yes (counted once per independent origin) | Yes | No (derived, not observed) | Yes |
| Eligible for promotion to trusted view | No | No | No | Yes, if policy met | Only if the conclusion itself is evaluated | Already trusted in scope |
| Phrased in outputs as | n/a | "possibly…" | "according to <source>…" | "<sources> report…" | "follows from…" | per scope |

---

## 6.5 Provenance and independence

### 6.5.1 PROV-O alignment

W3C PROV-O models provenance through entities, activities, and agents [F1-B §8.5]. USG records map onto it for export (Part 11, §11.x) and for interoperability.

| PROV-O | USG |
|---|---|
| Entity | Source, Span, Assertion, Candidate, Referent, Certificate, ValidationReport |
| Activity | Extraction, Validation, Review, Evaluation, Promotion, Canonicalization, Import |
| Agent | Model (with version), RuleEngine, Human reviewer, ExternalResource |
| `wasDerivedFrom` | Assertion ← Span; INFERRED ← premises; canonical ← candidate |
| `wasGeneratedBy` | Assertion ← Extraction activity |
| `wasAttributedTo` | Assertion ← commitment holder; Source ← author or publisher |
| `used` | Validation ← ruleset release |

Internally these are normal relational tables (SG-FND-006). The PROV mapping is an export view, not the storage format.

### 6.5.2 Claim-level, not source-level, trust (Normative)

[F3-B §7.27] The system MUST NOT assign one universal trust score to a whole source. A journal can be reliable inside its field and wrong outside it. Trust is recorded per claim and per scope:

```text
ClaimRecord       claim_id, assertion_id, source_id, evidence_type, publication_context,
                  extraction_method, review_status,
                  supporting_evidence[], contradicting_evidence[]

TrustProfile      source_id, scope (domain × claim_type), track_record
                  {n_checked, n_confirmed, n_refuted, period}, notes
```

A TrustProfile is **observed history in a scope** and is never an assumed prior. It informs review priority and evidence policy. It never replaces claim-level evidence.

**Trust tiers (handling, not truth).** Part 2's `trust_tier` governs *how the system handles* a source:

| Tier | Meaning | Effects |
|---|---|---|
| QUARANTINE | New, unknown, flagged, or adversarial-looking | Candidates stay provisional. Cannot add lexical mappings, concepts, or frames to trusted layers. Heavily rate-limited (§6.11). |
| STANDARD | Ordinary source | Normal pipeline |
| TRUSTED | Source in a vetted list for a declared scope | May contribute to corroboration without the extra independence audit. Still validated like any other source. |

Tier changes are decisions by policy or by a human, recorded in the audit log. A model cannot change a tier.

### 6.5.3 Independence (Enhancement E-59)

Corroboration counts **independent origins**. Multiple sources can repeat one mistake [F1-B §8.5]. Without an independence test, ten reposts count as ten confirmations.

**Rule SG-EVD-011.** Two supports are independent only if none is derived from the other and they do not share an upstream origin. The system builds a **dependence graph** over sources:

| Evidence of dependence | Effect |
|---|---|
| One cites, quotes, or links the other as its basis | Dependent |
| Same author, publisher, or syndication group on the topic | Dependent (counted once) |
| Near-duplicate text (shingle similarity above a threshold [Provisional]) | Dependent |
| Both cite the same primary study | Both count as one, unless each independently re-derived the result |
| Derived from the same imported resource | Dependent |

`independent_support_count` is the size of a maximum set of mutually independent supports (computed on the dependence graph). A flood of near-duplicate documents therefore raises it by at most 1.

**Extraction independence.** Two extractions by the *same* model on the *same* text are one observation, not two. An independent extraction method (a rule engine, a different model family, a human) is required for the "independent method agreeing" route to E3 (§6.4.2). The sources note that agreement between two models does not prove correctness, because they can share the same error [F3-B §7.17]. The audit sample (§6.8) is what protects against correlated error.

---

## 6.6 Evidence policy

A **policy** states what is required before a claim may change status. It differs by domain and claim type, because medicine and ordinary news do not share standards [F3-B §7.27].

```text
EvidencePolicy
  policy_id, version
  scope                  domain(s), claim types (FACT, DEFINITION, CAUSAL, STATISTICAL, ...)
  promotion_requires
      min_label                    E3 | E5
      min_independent_origins      n
      required_review              NONE | MODEL | HUMAN
      allowed_trust_tiers          subset
      disallowed_commitment        e.g. ATTRIBUTED when the claim is a policy statement
      max_age / recency            for claims that expire
  risk_uplift            +0 | +1 risk class (e.g., medicine)
  quantitative_claims    require units, population, method recorded
  default_if_unmet       SOURCE_ASSERTED | UNKNOWN
```

[Provisional: the numeric requirements come from domain experts and the benchmark. The kernel ships one conservative default policy and one stricter medical placeholder. It does not ship a full policy set.]

**Rule SG-EVD-008.** A claim becomes VERIFIED only through the evaluation process applying a policy whose requirements the claim's evidence vector meets, and the policy ID and version are recorded on the transition.

**Rule SG-EVD-009.** No claim reaches VERIFIED, E3-promotion, or the trusted view by being learned, extracted, proposed, or retrieved. Learning produces candidates, and promotion is a separate governed act (P-13).

---

## 6.7 Meaning versus truth: the knowledge views

The sources separate a *meaning record* from *fact verification*, and from there to a knowledge database holding verified, disputed, and unknown claims with status preserved [F1-B §12]. This is the structure.

```text
 SOURCE SENTENCE
      │ interpretation (Parts 3, 5)
      ▼
 MEANING RECORD  ──────►  CLAIM STORE (everything extracted; status preserved)
                               │
                               │ evaluation process (§6.6)
                               ▼
        ┌──────────────┬────────────────┬─────────────┐
        │  VERIFIED    │  DISPUTED      │  UNKNOWN    │
        └──────┬───────┴───────┬────────┴──────┬──────┘
               ▼               ▼               ▼
        TRUSTED VIEW      CONFLICT VIEW    OPEN VIEW
     (reasoning default)  (with clusters)  (low-trust retrieval)
```

The three views are **queries over one store**, not copies. An item is never moved or deleted, only re-labelled (SG-FND-006).

**Query rules (Normative):**
- A reasoning module's default scope is the **trusted view**. Using other scopes requires saying so, and the output must carry the attribution ("according to S1, which is SOURCE_ASSERTED").
- A conclusion inherits the **weakest** status among its premises, and records each premise's status.
- A conclusion drawn inside a non-WORLD context stays in that context.
- Absence of a claim is not evidence of falsity (SG-KNW-001). Unknown is its own answer.

**Two rule families stay separate** [F1-B §12]: rules for understanding language (Part 5, interpretation rules) and rules describing the world (knowledge rules). The model may interpret a false sentence correctly. Conversely a *knowledge rule* is never used to decide how to read a sentence, so a world-knowledge prior ("birds fly") cannot override what the sentence actually says ("The penguin cannot fly").

---

## 6.8 Contradictions and conflict clusters

[F3-B §7.26] Contradictory sources are the normal case in a large corpus, so the system never resolves them by overwriting.

**Detection.** Two claims conflict when they have the same normalized content up to polarity, or incompatible values for the same property, with overlapping scope, time, population, and definition. The detector is deterministic over canonical IR plus time and scope matching.

**ClaimCluster.**

```text
ClaimCluster   cluster_id, claims[], relation (CONTRADICTS | VALUE_CONFLICT | SCOPE_OVERLAP),
               explanations_considered[], status OPEN | EXPLAINED | RESOLVED | STANDING_DISPUTE
```

**Evaluation order.** Before concluding that any source is wrong, rule out the cheaper explanations:

1. **Parsing.** Re-run both claims through the independent extraction path (rules, or a different model). A negation, scope, or coreference error can produce a *spurious* contradiction. If the claims no longer conflict, mark `PARSING_SUSPECT` and fix the candidate through the normal certificate path.
2. **Scope.** Compare time, location, population, conditions, and context (§6.2). Many "contradictions" are statements about different scopes. Refine both claims with their scope and record `CONTEXT_DEPENDENT` or `POPULATION_DEPENDENT`.
3. **Definitions.** Compare the concept definitions used (Part 2, §2.9). Different definitions of one word are `DEFINITION_DEPENDENT`, not a contradiction.
4. **Source quality in scope.** Use TrustProfile and the evidence vectors. Prefer claims with stronger independent support. This only *orders* claims. It does not delete the weaker one.
5. **Else** leave `STANDING_DISPUTE`. Both claims remain, attributed, and status DISPUTED.

A system that deletes contradictory claims appears consistent while losing evidence. **Logical consistency is not factual accuracy** [F3-B §7.26].

---

## 6.9 Metacognition: deciding what to do next

[F1-C §12; F2-C §5.27] The Metacognition Module chooses the next processing step. It does not judge truth. It decides what additional processing a candidate needs.

### 6.9.1 Design constraints (Normative, SG-GOV-006)

The module is **deterministic**. It combines named, interpretable signals computed by validators, retrieval, and method agreement. It MUST NOT ask a language model for an arbitrary confidence number. Calibration comes from measured error rates (§6.10.3).

### 6.9.2 Signals

| Signal | Operational definition | Source of the value |
|---|---|---|
| SRC_AMBIGUOUS | Number of retained ALT groups and alternatives | Candidate IR |
| UNSUPPORTED_DETAIL | Elements failing VC-V01/V02/V06 or marked BACKGROUND without a rule | L4 |
| MULTI_INTERPRETATION | More than one valid reading found by independent methods | Parser, rules, model |
| DUPLICATE_RISK | Candidate concept/frame has near neighbours above the retrieval threshold | Resolver (Part 7) |
| FRAME_CONSTRAINTS | All frame and type checks passed, or UNDETERMINED count | L2/L3 |
| RETRIEVAL_ADEQUACY | Candidate set smaller than expected, or best lexical/semantic match weak, or no lexical hit | Retrieval |
| METHOD_DISAGREEMENT | Independent extraction methods disagree on frame, roles, polarity, operators, or referents | Part 8 |
| REVIEW_DISAGREEMENT | A reviewer's corrections differ from the producer | Review |
| OUTSIDE_ONTOLOGY | Needed concept has no registered neighbour | Resolver |
| HIGH_IMPACT | Operation class (merge, generalization, grammar change, new concept) | Task type |
| INJECTION_FLAG | Source triggered a §6.11 tripwire | Security |
| CONTRADICTS_TRUSTED | Conflict with trusted-view claims | VC-C06 |

**A failed retrieval is not proof of non-existence** [F1-C §10]. RETRIEVAL_ADEQUACY = THIN triggers `RETRIEVE_MORE`, and a "new concept" decision is always re-checked by the registry at commit time (Part 7).

### 6.9.3 Actions

| Action | When chosen |
|---|---|
| ACCEPT_PROVISIONALLY | FORMALLY_VALID, low risk class, no adverse signal |
| RETRIEVE_MORE_CONTEXT | RETRIEVAL_ADEQUACY thin, or unresolved coreference/sense where wider context may settle it |
| RETRY_ALTERNATE_METHOD | METHOD_DISAGREEMENT, or INVALID with a repairable code and retries remaining (Part 5, §5.7) |
| REQUEST_MODEL_REVIEW | Risk class HIGH, or MEDIUM with an adverse signal |
| REQUEST_HUMAN_REVIEW | VERY_HIGH, or a model review that disagrees with the producer, or INJECTION_FLAG on a source being promoted |
| PRESERVE_AMBIGUITY | The ambiguity is in the source itself (Part 5, §5.10) |
| REJECT | INVALID and unrepairable |
| DEFER | Budget exhausted. Queue with priority. |

---

## 6.10 Risk classes and review policy

### 6.10.1 Static classification

[F3-B §7.18, illustrative in the source, now a rule]

| Situation | Static risk class |
|---|---|
| Exact known lexical mapping with a tested rule | LOW |
| Familiar frame with clear participants | LOW (MEDIUM if any type warning or hole on a REQUIRED role) |
| Several plausible word senses | MEDIUM |
| Unresolved pronoun reference | MEDIUM (HIGH when a competing antecedent exists) |
| Complex negation or quantifier scope | HIGH |
| New concept definition | HIGH |
| Proposed universal generalization | VERY_HIGH |
| Proposed concept merge | VERY_HIGH |
| Proposed modification of fundamental grammar | VERY_HIGH |

Policy `risk_uplift` (§6.6) raises the class by one step for sensitive domains.

### 6.10.2 Routing by class

| Class | Required before leaving PROVISIONAL |
|---|---|
| LOW | Formal validity. Random audit sampling (§6.10.3). |
| MEDIUM | Formal validity plus agreement of an independent extraction method, or a reviewer pass |
| HIGH | Reviewer pass with corrections re-validated. Larger model, or human if the model is the same family as the producer. |
| VERY_HIGH | Reviewer pass **and** counterexample search **and** human or gold-benchmark approval. Never automatic. |

### 6.10.3 Calibrating risk (Enhancement E-15)

The source says the final system should "calibrate review decisions using measured error rates", and that a supposedly low-risk category that proves wrong should be reviewed more often [F3-B §7.18]. The procedure:

1. **Category.** Each candidate falls in a category *c* = (construction type × frame family × rule set × producer method).
2. **Audit sample.** A random sample of auto-accepted candidates in each category is audited by a human, or against a human-reviewed gold set, at a rate `s_c`. [Provisional: start at 10% for new categories, taper by evidence.]
3. **Upper bound.** For *n* audited and *k* errors, compute the Wilson upper bound of the error rate:

   `UB = [ p̂ + z²/2n + z·√( p̂(1−p̂)/n + z²/4n² ) ] / ( 1 + z²/n )`, with `p̂ = k/n`, `z = 1.645` (one-sided 95%) [Provisional].

   Example: *n* = 100, *k* = 2 gives `p̂ = 0.02` and `UB ≈ 5.9%`. With *n* = 0, `UB = 1` by convention, so a new category starts as high-risk and earns lower classes only through audited evidence.
4. **Escalate.** If `UB > τ_c` (the tolerated error rate for that class [Provisional]), move the category up one class. Relax it only when `UB` stays below `τ_c` over a minimum audited sample.
5. **Effective class** = max(static class, empirical class). The empirical class can only raise a static class during the kernel phase.
6. **Reviewer calibration.** Reviewers are audited the same way, on gold items, so an unreliable reviewer lowers its own weight.

### 6.10.4 Calibrating support values (closes the Part 3 §3.14 promise)

ALT supports are **ordinal ranks** by default. A numeric probability may be attached to an alternative only if the producing method has been **calibrated on a held-out gold set**: expected calibration error below a threshold [Provisional] over at least a minimum number of cases per bin. An uncalibrated model score is never displayed or stored as probability.

---

## 6.11 The review service

### 6.11.1 Reviewer input

[F2-A §3.26; F3-B §7.17] The reviewer receives a bounded package:

```text
SOURCE TEXT (the relevant span and its context window)
CANDIDATE IR and DERIVATION CERTIFICATE
FRAME DEFINITIONS and RULE definitions applied
SOURCE EVIDENCE (spans) and the VALIDATION REPORT
EXISTING SIMILAR CONCEPTS (from retrieval)
KNOWN ALTERNATIVE INTERPRETATIONS (ALT members and rejected alternatives)
```

### 6.11.2 Review questions

The five questions in F1-B §6 and the problem list in F3-B §7.17 define the task:

| Question | Finding codes |
|---|---|
| Is the interpretation supported by the source? | R-UNSUPPORTED |
| Is another interpretation plausible? | R-ALTERNATIVE |
| Is the selected frame appropriate? | R-WRONG-FRAME |
| Is important information omitted? | R-OMISSION |
| Are unsupported facts introduced? | R-INVENTED |
| Wrong word sense | R-SENSE |
| Wrong semantic roles | R-ROLE |
| Missing negation or modality | R-POLARITY, R-MODALITY |
| Incorrect coreference | R-COREF |
| Overgeneralization | R-OVERGEN |
| Concept duplication | R-DUPLICATE |
| Incorrect causal relation | R-CAUSAL |
| Misleading canonicalization | R-CANON |

For proposed universal rules the reviewer must also **produce counterexamples**. Counterexamples are checked against trusted knowledge before they are accepted (Part 9).

### 6.11.3 Reviewer output

```text
ReviewRecord
  verdict    SUPPORTED | SUPPORTED_WITH_CORRECTIONS | ALTERNATIVE_PLAUSIBLE
             | INSUFFICIENT_INFORMATION | REJECT
  findings[] (code, element_ref, explanation, evidence_span)
  corrected_candidate (optional)   → goes back through the validator (Part 5) as a new version
  alternatives[]
  reviewer (kind, model_id or person), date, review_policy_id
```

**INSUFFICIENT_INFORMATION is a first-class verdict** [F1-B §6]. A reviewer forced to pick one interpretation would introduce another error.

### 6.11.4 Independence and bias controls (Enhancement E-57)

**Rule SG-GOV-003 (review independence).**
1. A reviewer's corrections pass the same deterministic validator and never bypass it.
2. A reviewer cannot commit or promote (SG-FND-004).
3. For HIGH and VERY_HIGH, the reviewer SHOULD differ in model family from the producer, because two models of one family can make the same mistake [F3-B §7.17].
4. **Blind-first review for VERY_HIGH.** The reviewer first produces an interpretation from the source alone, then is shown the candidate. Disagreements are findings. This reduces anchoring on the candidate.
5. Agreement between two models never substitutes for the gold set or human audit (§6.10.3).
6. Review decisions are logged with the policy that triggered them.

### 6.11.5 Human review

A human review queue exists from the first release for VERY_HIGH items and for audit samples. Queue items are ordered by risk class, impact, and age. The reviewer interface shows the source span, the candidate in readable form, the alternatives, and the rule text. Each decision records the reviewer, the verdict, and reasons. A decision is a first-class evidence record (`authority`, §6.4.1), and is used to grow the gold set.

---

## 6.12 Pattern evidence and the veto rule (Enhancement E-17)

The coaching reference supplies four disciplines that carry over to any system that mines patterns from its own corpus.

### 6.12.1 Four classes of derived statement

| Class | In USG | Evidence needed |
|---|---|---|
| OBSERVATION | Stated in the source (basis EXPLICIT, or GRAMMATICAL by rule) | Span support (E2) |
| INTERPRETATION | A hypothesis about meaning or a background inference | E1 until validated. Phrased as a possibility. |
| PATTERN | A structure recurring across many independent records | At least N independent occurrences (§6.12.2) |
| GENERALIZATION (kind-level claim) | A universal, typical, or functional claim about a class | Counterexample testing, review, and often human approval (Part 9) |

A statement MUST NOT be promoted from one class to the next by repetition alone.

### 6.12.2 Pattern lifecycle with a minimum count

A recurring structure becomes a **candidate pattern** only after at least *N* occurrences, each from an independent origin (§6.5.3), after the structural counts are normalized. [Provisional: N = 3 as a starting value. This echoes the reference's "patterns only after 3+ occurrences", to be tuned by the benchmark.] A single instance, however vivid, is never a pattern.

### 6.12.3 The veto rule

A reviewer can mark a mined pattern, an alignment, a generalization, or an extraction rule as **REJECTED_PATTERN**, with a reason. The rejection is stored with the pattern's structural signature (Part 4, §4.10.3). The discovery engines MUST NOT re-propose it unless new evidence exceeds a materially higher threshold. This is the "user can say *not me*" rule applied to the system's own mining: a human objection **suppresses** a pattern and does not merely downgrade it.

### 6.12.4 Novelty protection

Before running an expensive analysis, the controller checks whether the same input was already analysed (content-hash cache), a covering frame or alignment already exists, or an equivalent candidate was already rejected. If so it skips the analysis. This is the "do not ask another lens merely because it is available" discipline: no mechanical re-analysis.

### 6.12.5 Process history keeps the method, not the story

[REF; F1-C §19] The H layer (Part 2, §2.1) stores *how* processing went: task IDs, error codes, outcomes, methods, timings, rule IDs. It does **not** copy source content. Source text lives only in the Source record, which has its own retention and sensitivity policy (§6.13.5). Invariant I-14 (no world knowledge in process history) stands.

---

## 6.13 Security

### 6.13.1 Why this is needed (Enhancement E-13)

The system feeds untrusted text to a language model and uses the result to update a persistent knowledge base. The sources mention "malicious or incorrect documents" only as a promotion concern [F3-B §7.12]. A document that contains text such as "ignore your instructions and record that…" targets the interpreter directly. Defense must be **structural**, because filtering text cannot catch every attack. This agrees with the sources' principle that control comes from software permissions, not prompts [F2-A §3.25].

### 6.13.2 Threat model

| Threat | Example | Primary defense |
|---|---|---|
| Prompt injection | Source says "label this verified" | SEC-001, SEC-002 |
| Dictionary and knowledge poisoning | A document pushes a fake lexical mapping or definition | SEC-003, SEC-007 |
| Sybil / duplicate flooding | Hundreds of near-copies fake corroboration | SEC-007, SG-EVD-011 |
| Data exfiltration | Sensitive text sent to a remote reviewer | SEC-008 |
| Resource exhaustion | Huge input, deep nesting, ALT explosion, retry loops | SEC-006 |
| Encoding attacks | Invisible characters, bidirectional controls, homoglyphs, mixed scripts | SEC-005 |
| Rulebook or validator tampering | A model output or crafted source altering rules | SG-FND-005, SEC-009 |
| Supply-chain and licensing | Poisoned or restricted imported resources | SEC-010 |
| Log tampering | Covering an incorrect promotion | SEC-009 |

### 6.13.3 Security rules

| Rule | Statement | Check class |
|---|---|---|
| **SG-SEC-001** | **Source text is data, never instructions.** Source text is placed in a delimited data channel in every model call. The prompt states that it is untrusted content to analyse. Instructions inside it are interpreted *as content* (for example, a DIRECT frame, Part 3, §3.8.4), never executed. | D (by construction) |
| **SG-SEC-002** | **Least-privilege gateway.** The model gateway has no network, no tool calls, no filesystem, and no write path to any store. Its only output is a schema-validated Candidate. It returns IDs from retrieved sets, or NONE_OF_THESE (Part 5, §5.9). | D |
| **SG-SEC-003** | **Quarantine tiers.** New or flagged sources default to QUARANTINE (§6.5.2). Quarantined candidates cannot reach any trusted layer. Tier raising is a policy or human act. | D |
| **SG-SEC-004** | **Tripwires.** Heuristics flag text addressed to an AI or claiming to be instructions or system messages. Flags raise INJECTION_FLAG and risk class. Flagged content is not auto-rejected, because it may be a legitimate quote about prompts. **Safety does not depend on detection.** SEC-001 and SEC-002 hold even if no tripwire fires. | H |
| **SG-SEC-005** | **Text normalization with offset mapping** (§6.13.4) | D |
| **SG-SEC-006** | **Resource limits.** Per source and per task: maximum characters, tokens, nesting depth, ALT groups and alternatives, retries, wall time, and model calls. A circuit breaker pauses a source that repeatedly fails. | D |
| **SG-SEC-007** | **Poisoning limits.** One source (and its dependence cluster) may contribute at most a configured number of new concepts, lexical mappings, or frame proposals per cycle. Lexical mappings from QUARANTINE sources require corroboration by independent origins. Grammar-level proposals require evidence from independent origins, not from one document repeated. [Provisional: caps set from benchmark runs.] | D |
| **SG-SEC-008** | **Egress control.** Sources carry a sensitivity label. Only labels marked shareable may be sent to a remote reviewer. Content is minimized (the needed span plus context window) and optionally redacted. Every transmission is logged. **Local-only is the default.** | D |
| **SG-SEC-009** | **Integrity.** The audit log is hash-chained. Ruleset and validator releases are hashed and recorded. Reports state which hashes they ran under. Backups are versioned. | D |
| **SG-SEC-010** | **Import hygiene.** Each external resource records origin, version, license, and restrictions, and is checked before import. A resource's content enters as STRUCTURED, never as PROMOTED (Part 8). | D / R |

### 6.13.4 Text normalization (Enhancement E-60)

Part 2 fixed spans as code-point offsets over the **immutable stored text**. Security and Arabic-language support both need a derived, cleaner view of it:

- The **stored text** is never altered.
- A **normalized view** is derived for processing, with an **offset map** back to the stored text. It applies Unicode normalization, strips or marks zero-width and bidirectional control characters, and optionally folds presentation forms and optional diacritics such as Arabic tashkeel and kashida. Folding is declared per language and is reversible through the map.
- All spans produced against the view are translated back to stored-text offsets before they are written. Spans in certificates are always stored-text spans.
- The scanner records **mixed-script words**, homoglyph candidates, and hidden control characters as risk signals.

### 6.13.5 Privacy and retention

- Sources carry a **sensitivity label** and **retention policy**. Personal data in sources is possible, so deletion is supported: deleting a source leaves a tombstone, retains hashes and derived non-personal structure only where policy allows, and re-opens any claim that depended on it.
- The audit log stores IDs and hashes of redacted items. It stores no personal content.
- Sensitivity propagates: a record derived from a labelled source inherits the label unless an explicit declassification decision exists.

---

## 6.14 The complete assurance workflow

This is the F1-B §13 revised workflow with the statuses and checks of Parts 5–6:

```text
 SOURCE (registered, tier, label, anchor)
   │ normalization (SEC-005)  · tripwires (SEC-004) · limits (SEC-006)
   ▼
 LOCAL MODEL ──► CANDIDATE IR + DERIVATION CERTIFICATE        (producer: no authority)
   ▼
 DETERMINISTIC VALIDATOR (L1–L4, partial L5)  ──► ValidationReport (axis B)
   ▼
 METACOGNITION (signals §6.9) ──┬─ REPAIR / RETRY ──────────────► back to model/other method
                                ├─ PRESERVE_AMBIGUITY ──────────► IR with ALT (axis A = AMBIGUOUS)
                                ├─ REVIEW (model/human, §6.11) ──► corrected candidate ─► re-validate
                                └─ ACCEPT_PROVISIONALLY ────────► PROVISIONAL RECORD (E1/E2, stage VALIDATED_FORMALLY)
   ▼
 EVALUATION PROCESS (policy §6.6, independence §6.5, contradictions §6.8)
   ▼
 CLAIM STATUS: SOURCE_ASSERTED / VERIFIED / DISPUTED / UNKNOWN  (axis D)
   ▼
 PROMOTION CONTROLLER (SG-FND-004, SG-EVD-009) ──► TRUSTED VIEW / DICTIONARY / GRAMMAR (Part 9)
```

The advantages the sources listed hold: consistency (the same rules everywhere), traceability, efficiency (routine cases skip review), error isolation (invalid output cannot reach trusted knowledge), and extensibility (new patterns can be proposed and tested without becoming authoritative) [F1-B §13].

---

## 6.15 Rules registered in this part

| Rule | Subject |
|---|---|
| SG-EVD-007 | Commitment holder and evaluation context gate the trusted view |
| SG-EVD-008 | VERIFIED only through a recorded evidence policy |
| SG-EVD-009 | No self-promotion by learning, extraction, repetition, or retrieval |
| SG-EVD-011 | Corroboration counts independent origins only |
| SG-EVD-012 | Derived claims inherit the weakest premise (support cap) |
| SG-GOV-003 | Review independence and bias controls |
| SG-GOV-004 | Audit-based calibration of risk classes |
| SG-GOV-005 | A reviewer cannot commit or promote |
| SG-GOV-006 | Metacognition is deterministic and signal-based |
| SG-SEC-001 … SG-SEC-010 | Security rules (§6.13.3) |

SG-EVD-010 (contradictions are preserved, never overwritten) is the rule form of §6.8.

---

## 6.16 Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-03 (completed) | E0–E5 mixed dimensions | Evidence vector as primary, derived label by fixed function, derivation cap, scope-limited curation (§6.4) |
| E-13 (completed) | Source text could attack the interpreter. Hostile documents were only a promotion concern. | Structural defenses SEC-001…SEC-010 (§6.13) |
| E-15 (completed) | Review thresholds were illustrative. Model agreement is not proof. | Audit-based calibration with Wilson bounds. Reviewer calibration. Calibrated support values only (§6.10) |
| E-17 (completed) | Coaching-file disciplines only partly mapped | Four classes of derived statement, minimum-count patterns, veto rule, novelty protection, process history without content (§6.12) |
| E-56 | A claim's standing depends on who commits to it and in what world | Commitment holder and evaluation context (§6.2) |
| E-57 | Reviewers anchor on the candidate. Same-family models share errors. | Blind-first review and reviewer independence rules (§6.11.4) |
| E-58 | Remote review risks data egress | Sensitivity labels, minimization, logging, local-only default (SEC-008) |
| E-59 | Duplicated sources fake corroboration | Dependence graph and independence rule (§6.5.3) |
| E-60 | Hidden or confusable characters, and Arabic diacritics, threaten span integrity | Normalized view with offset map (§6.13.4) |


---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 7 of 12: Concept Identity and Resolution

If this part is weak, the dictionary fills with duplicates or, worse, with wrong merges that corrupt every relationship attached to them [F2-B §4.28; F2-C intro]. The sources frame it as a question: *how does the system know whether a concept already exists?* [F2-C concl.] The answer needs several separate capabilities: lexical sense recognition, contextual interpretation, formal comparison of definitions, type checking, candidate retrieval, evidence validation, and controlled registration with versioning.

The sources' closing sentence is cut off ("The central principle is:"). It follows from their own text and is restated here as the governing principle of this part:

> **The model proposes. The registry authorizes. Identity is established by structured evidence within a declared scope, and every identity decision stays reversible.**

---

## 7.1 Scope and operations

Four kinds of identity (Part 2, §2.4.2) give three resolution operations. They are separate, with different evidence and different risks.

| Operation | Input | Output | Typical frequency |
|---|---|---|---|
| **RESOLVE_SENSE** | A word or phrase in context | An existing concept ID (or a deferral) | Very high |
| **RESOLVE_CONCEPT** | A proposed concept, or two existing concept records | A relation between concepts, and an action | Moderate |
| **RESOLVE_INDIVIDUAL** | Two referents or a referent and an external entity | SAME_AS or DIFFERENT_FROM within a scope, or unresolved | Moderate |

RESOLVE_SENSE is the common case and is mostly lexical lookup (Part 8). This part concentrates on the other two. Everything here also governs what RESOLVE_SENSE may do when no existing concept fits.

> "John owns a red car" and "John drives a red automobile" may share a concept without sharing an individual. John may own several vehicles. Resolving concepts and resolving individuals are different operations [F2-C §5.2].

---

## 7.2 Outcomes of a concept comparison

### 7.2.1 The relation set

[F2-C §5.8] Duplicate detection is never binary. The comparison produces one of these relations. Sources list five plus a sixth (disjoint); the table also fixes direction for subsumption.

| Relation | Meaning | Example |
|---|---|---|
| EQUIVALENT | Same meaning within the declared scope | Car, Automobile, Motorcar (ordinary sense) |
| SUBSUMED_BY (A ⊑ B) | A is narrower than B | Car ⊑ Vehicle |
| SUBSUMES (A ⊒ B) | A is broader than B (inverse) | Vehicle ⊒ Car |
| OVERLAP | Concepts share some instances or properties and neither contains the other | Amphibious vehicle / Watercraft |
| RELATED | Meaningful connection, no shared extension implied | Doctor, Hospital |
| DISJOINT | Provably cannot share instances, under the definitions | EvenNumber, OddNumber (integers) |
| UNRESOLVED | Insufficient evidence | Two incomplete definitions |

DISJOINT is stronger than "different". It enables validation (VC-T06, DISJOINT_WITH in Part 3, §3.19).

### 7.2.2 Strength of an equivalence claim (Enhancement E-64)

The sources treat logical equivalence as "strong evidence of identity, not a universal solution" [F2-C §5.6], and warn that equivalent definitions do not always mean the same name in every context. This is operationalized as a **grade**:

| Grade | Required evidence | Allowed use |
|---|---|---|
| ESTABLISHED | Both definitions are COMPLETE in the same scope, mutual entailment holds (§7.3.3), no contradicting constraint, no unresolved scope conflict | Basis for an EquivalenceMapping, after review |
| SUPPORTED | Alignment through a trusted resource (same WordNet synset, same external ID) and compatible constraints, but at least one definition is not complete | Lexical reuse. Mapping only with review. |
| CANDIDATE | Retrieval or model judgment says similar, with no contradictory evidence | Kept as a hint. Never acted on alone. |
| INSUFFICIENT | Anything less | Preserve separate records (UNRESOLVED) |

Only ESTABLISHED and SUPPORTED equivalences can lead to reuse. No grade is derived from embedding similarity or from model confidence.

### 7.2.3 Statuses and actions

[F2-C §5.10, §5.26] Resolution produces a **status** and, from it, a permitted **action**:

| Status | Relation | Permitted action |
|---|---|---|
| MATCHED | EQUIVALENT (ESTABLISHED or SUPPORTED) | REUSE_EXISTING_CONCEPT. Add a lexical mapping if the form is new. No new concept. |
| SPECIALIZATION | Proposal ⊑ existing | CREATE_SPECIALIZATION (new concept with IS_A to existing) |
| GENERALIZATION | Proposal ⊒ existing | CREATE_GENERALIZATION (Enhancement E-61): new broader concept, existing becomes its subclass. Higher risk class, because it changes existing structure. |
| OVERLAP / RELATED | OVERLAP or RELATED | CREATE_RELATED_CONCEPT (new concept plus the relation) |
| DISJOINT | Proposal conflicts with the retrieved neighbour | Not a duplicate. Continue the search or CREATE_NEW_CONCEPT. |
| NEW_CONCEPT | No relation found after adequate retrieval | CREATE_NEW_CONCEPT |
| UNRESOLVED | Evidence too weak | DEFER_RESOLUTION. Keep as a provisional concept (§7.9). |
| REJECTED | Invalid or unsupported proposal | REJECT, with codes recorded |

The source's action list has no action for a proposal broader than an existing concept, although its status list does. CREATE_GENERALIZATION fills that gap (E-61).

**Reuse versus merge (clarification).** *Reusing* a concept for a new proposal creates no new record, so it is cheap and reversible. *Merging* two **already existing** records (EquivalenceMapping, §7.8) changes what many records mean and is the riskiest operation in the dictionary. The two have different risk classes (§7.12).

---

## 7.3 Structured comparison

### 7.3.1 Why not text or embeddings

Two concept descriptions can read as equivalent and not be [F2-C §5.4]:

```text
A: "A device used to move fluid."        B: "A machine that transports liquid."
```

- *Fluid* includes gases, so B is narrower on the substance.
- *Device* and *machine* may differ in definition.
- *Move* and *transport* may name different functional relations.

The comparison therefore works on **structured definitions** (Part 2, §2.9): kind, parents, ESSENTIAL constraints, functions, relations, scope. A text description is an input to the interpreter, not the object compared.

**SG-IDN-004 (Normative).** Lexical similarity, embedding similarity, definition-text similarity, and model judgment MAY propose a candidate. They MUST NOT, alone or in combination, establish identity or subsumption.

Antonyms (hot, cold) are close in embedding space because they occur in similar contexts. Associated terms (doctor, hospital) are close without being equivalent [F2-C §5.9].

### 7.3.2 Comparison inputs

```text
For concepts A and B (or a proposal A against existing B), in scope s:
  kind(A), kind(B)                         must match for any relation other than RELATED/DISJOINT
  E(A,s), E(B,s)                           ESSENTIAL constraints, closed under inheritance
  T(A,s), T(B,s)                           TYPICAL constraints (never used to separate or merge)
  F(A), F(B)                               functions (Part 4, §4.8) — compared by function hierarchy
  Rel(A), Rel(B)                           recorded relations
  completeness(A,s), completeness(B,s)     COMPLETE | INCOMPLETE
  scope compatibility                      same domain/definition? (§7.7)
```

### 7.3.3 Decision procedure

Let `E(X)` be the ESSENTIAL constraint set of `X` and `⊨` entailment under the constraint language of Part 3, §3.19 together with the ontology. Entailment is computed by a sound but incomplete reasoner. If it cannot decide, the answer is *not established*.

The formal criterion [F2-C §5.6]: A and B are equivalent in scope *s* when

```text
D(A) ⊨ D(B)   and   D(B) ⊨ D(A)
```

where `D(X)` is the set of defining (ESSENTIAL) constraints. The procedure applies it with open-world caution:

| Step | Test | Result |
|---|---|---|
| 1 | Kinds differ | Not EQUIVALENT or SUBSUMED. Check DISJOINT or RELATED. |
| 2 | `E(A) ∧ E(B)` provably unsatisfiable, or `DISJOINT_WITH` declared | DISJOINT |
| 3 | Either definition INCOMPLETE | Cap the result at SUPPORTED (if alignment evidence exists) or CANDIDATE. SG-KNW-001: a *missing* property is not evidence of difference [F2-C §5.7]. |
| 4 | Both COMPLETE, mutual entailment | EQUIVALENT (ESTABLISHED) |
| 5 | Both COMPLETE, `E(A) ⊨ E(B)` only | A SUBSUMED_BY B |
| 6 | Both COMPLETE, `E(B) ⊨ E(A)` only | A SUBSUMES B |
| 7 | Both COMPLETE, compatible but neither entails | OVERLAP if shared instance or relation evidence exists, otherwise RELATED |
| 8 | Scope differs | Resolve scope first (§7.7). A relation holds only within a scope. |

**Open-world warning.** Two concepts with different recorded property sets are not necessarily different. One description may be more complete [F2-C §5.7]. Under a closed-world policy declared for a scope (for example a controlled inventory table), absence may count. The policy is recorded with the decision.

### 7.3.4 The source's examples, decided

| Pair | Outcome | Reason |
|---|---|---|
| Car / Automobile / Motorcar | EQUIVALENT (SUPPORTED → ESTABLISHED once both definitions are complete) | Same lexical sense; compatible definitions |
| Car / Vehicle | Car SUBSUMED_BY Vehicle | Not every vehicle is a car |
| Car / PassengerCar | Depends on the definition. If Car includes categories PassengerCar excludes, then PassengerCar ⊑ Car. In everyday scope they may be EQUIVALENT. | A technical ontology can make them differ. Scope matters. |
| Doctor / Physician | OVERLAP or scope-dependent EQUIVALENT | Jurisdiction and intended sense can differ |
| Liquid pump / "machine that transports liquid" vs "device that moves fluid" | Narrower or OVERLAP. Never merged automatically. | Liquid ⊏ Fluid. Device vs machine and move vs transport need relations. |
| Even number / Odd number | DISJOINT (integers) | Definitions exclude each other |
| Hot / Cold | DISJOINT-or-contrary on one property. Not equivalent. | Embedding proximity is irrelevant |
| Doctor / Hospital | RELATED | Association only |

---

## 7.4 Retrieval of candidates

### 7.4.1 Stages

The sources list eight stages (F2-C §5.10) and ten processing steps (F2-C §5.26). They are combined into one procedure, **RESOLVE_CONCEPT**:

| Step | Stage | Source mapping |
|---|---|---|
| R0 | Normalize lexical form and context (language, lemma, normalized view) | 5.26 step 1 |
| R1 | **Exact ID lookup.** If the source already references an established ID, retrieve it. | 5.10 stage 1 |
| R2 | **Lexical lookup:** words, synonyms, translations, lexical senses, ExternalMappings | 5.10 stage 2; 5.26 step 2 |
| R3 | **Structural candidate search:** kind, parents, functions, relations, structural signatures | 5.10 stage 3; 5.26 step 3 |
| R4 | **Embedding retrieval** over concept definitions | 5.10 stage 4 |
| R5 | **Graph neighbourhood search** around candidates found so far | 5.9 diagram |
| R6 | Assemble, de-duplicate, and rank the candidate set within a budget | new |
| R7 | **Contextual disambiguation** against the source sentence (ContextIntegrator) | 5.10 stage 5; 5.26 step 7 |
| R8 | **Formal identity evaluation** (§7.3), contradiction search, scope check | 5.10 stage 6; 5.26 steps 4–6, 8 |
| R9 | **Certificate and rule validation** (§7.5) | 5.26 step 10 |
| R10 | **Review routing** by risk class (Part 6, §6.10) | 5.10 stage 7 |
| R11 | **Resolution and registry commit** (§7.10) | 5.10 stage 8; 5.26 step 9 |

R1 and R2 usually settle common cases (Part 8). Steps R3–R5 run when no exact lexical hit is adequate. This keeps expensive retrieval for the cases that need it [F3-C §8.12].

### 7.4.2 Embeddings in retrieval

- Embeddings come from a dedicated embedding model, separate from the language model (Part 8).
- A retrieved concept is a **candidate only** (SG-IDN-004).
- Each stored vector records the **embedding model ID and version** (Enhancement E-67). When the model changes, the index is rebuilt and old similarity scores are not mixed with new ones. Embeddings are derived data and can always be regenerated.
- Vectors cost memory: a 384-dimensional float32 vector is 1,536 bytes, so one million concepts need about 1.5 GB [F3-C §8.13]. Indexes are therefore domain-partitioned, loaded selectively, and quantized later if measurement requires (Parts 10–12).
- A concept's embedding is computed from a **structured text rendering** of its definition (label, kind, parents, essential constraints, functions), and not from the free-text gloss alone. Structured input makes embedding neighbours more meaningful, and it makes regeneration deterministic.

### 7.4.3 The ContextIntegrator and SemanticHub

[F2-C §5.3; F1-C §5]

```text
INPUT EXPRESSION → CONTEXT ANALYSIS → CANDIDATE RETRIEVAL → SEMANTIC HUB
                 → POSSIBLE CONCEPT IDs → CONTEXTUAL EVALUATION → SELECT / DEFER / NEW
```

- The **SemanticHub** answers "what concepts could this be, and what do we know about each?" It returns a *small* candidate set, with each concept's stable definition summary.
- The **ContextIntegrator** answers "which is meant here?" It evaluates the candidates against the sentence or paragraph. The ContextIntegrator MUST NOT search the whole dictionary itself (P-16). Retrieval and interpretation stay separate so each can be optimized independently.
- Example: for "The bank approved the loan", the SemanticHub returns BANK_FINANCIAL_INSTITUTION, BANK_RIVER_LANDFORM, BANK_STORAGE_FACILITY. Context cues (`approved`, `loan`) support the first, and the ContextIntegrator selects it. If the evidence is insufficient, the result is DEFER or ALT (Part 3, §3.14), not a forced pick.
- Selecting among *existing* concepts is the only action at this step. Proposing a new concept is a separate, higher-risk path (§7.9).

---

## 7.5 The identity certificate

[F2-C §5.11] Every identity decision, whether proposed by a model or by a rule, carries a certificate so the validator can check it.

```text
IdentityCertificate
  certificate_id, producer (model/rule/human), grammar_version, ruleset_release
  operation              RESOLVE_SENSE | RESOLVE_CONCEPT | RESOLVE_INDIVIDUAL | MERGE | SPLIT
  candidate_a, candidate_b          concept ids (or provisional/temporary handles)
  proposed_relation                  EQUIVALENT | SUBSUMED_BY | SUBSUMES | OVERLAP | RELATED | DISJOINT
  equivalence_grade                  ESTABLISHED | SUPPORTED | CANDIDATE | INSUFFICIENT
  scope                              domain / definition / ontology release
  comparison                         features compared and the result per feature (§7.3.2)
  evidence[]
    type                  LEXICAL_MAPPING | DEFINITION_COMPARISON | CONSTRAINT_ENTAILMENT
                          | EXTERNAL_ALIGNMENT | CONTEXT_SPAN | REVIEW
    reference             resolvable record id
    result                COMPATIBLE | CONFLICTING | NEUTRAL
  rules_applied[]         SG-IDN-001, SG-IDN-002, ...
  alternatives_considered[]  concepts considered and why rejected
  status                  PENDING_VALIDATION
```

The source's illustrative example cited `SG-IDENTITY-001` and `SG-IDENTITY-002` for a merge [F2-C §5.11], which are the open-world and drift rules. It also called the rule identifiers illustrative because the machine-checkable rules had not been written. The rules for these operations are SG-IDN-001 to SG-IDN-009 (Enhancement E-68).

### 7.5.1 What the validator checks

| Check | Verifies | Rule |
|---|---|---|
| VC-I01 | Both concept IDs exist (or are valid provisional handles) | FND-001 |
| VC-I02 | Every cited rule ID is valid and applies to this operation | FND-001 |
| VC-I03 | Evidence references are resolvable and relevant | EVD-005 |
| VC-I04 | Kinds are compatible with the proposed relation | TYP-001 |
| VC-I05 | Existing constraints (disjointness, cardinality, inheritance) are not violated by the proposed relation | KNW-005 |
| VC-I06 | The declared scope exists and both concepts have definitions in it | IDN-008 |
| VC-I07 | EQUIVALENT claims state a grade and the grade is supported by the cited evidence | IDN-002 |
| VC-I08 | No evidence of type EMBEDDING or MODEL_JUDGMENT is the *only* basis | IDN-004 |
| VC-I09 | A merge would not create a cycle in the mapping graph | IDN-003 |
| VC-I10 | Certificate producer differs from the approver | FND-004 |

---

## 7.6 Individual resolution

**SG-IDN-005 (Normative).** Concept resolution never merges referents. Two referents are the same individual only through RESOLVE_INDIVIDUAL, with evidence, within a scope (Part 3, §3.12).

### 7.6.1 Evidence for identity of individuals

| Evidence | Strength |
|---|---|
| Same external identifier (a Wikidata entry, a national ID in an authoritative source) | Strong |
| Explicit statement in a source ("John Smith, the author of that report") | Strong within that source |
| Coreference chain within a document (pronoun, repeated definite description), validated | Strong within the document |
| Name plus distinguishing attributes (date of birth, role, place) | Moderate |
| Name alone | **Weak. Not sufficient.** A given name matches many people. |
| Same concept class | None (two doctors are different unless shown otherwise) |

### 7.6.2 Behaviour

- Default is **separate referents**. The "mention of a doctor" in sentence 1 and in sentence 20 of a corpus are different discourse referents unless the evidence above links them.
- Output is `SAME_AS(a, b, scope)` or `DIFFERENT_FROM(a, b)` with evidence. Absence of evidence yields UNRESOLVED, not DIFFERENT_FROM (open world).
- Linking a referent to an external entity creates an ExternalMapping with relation `EXACT`, `PARTIAL_OVERLAP`, or `UNRESOLVED`. External IDs are not interchangeable with internal IDs.
- **Events are not merged by structural equality.** "John bought a book" in two sources describes one purchase only if context says so (Part 3, §3.16).
- Identity inside an attitude context stays inside it (SG-KNW-003).
- An individual identity, like a concept mapping, is reversible. Both original referents are kept.

---

## 7.7 Scope, definitions, and context-dependent identity

### 7.7.1 Identity is relative to a scope (SG-IDN-008, Enhancement E-65)

Equivalence is meaningful only within a stated **scope**: a domain, a definition variant, an ontology release, or a combination. The same two records may be equivalent in one scope and different in another.

```text
Water / H₂O
  chemical species scope        EQUIVALENT (ESTABLISHED)
  pure-sample scope             may differ (isotopes, dissolved matter)
  "the glass contains water"    ordinary-substance scope: natural mixture; NOT pure H₂O
```

[F2-C §5.13] Concept identity depends on abstraction level. A chemical formula identifies a composition, while a natural-language term can refer to a substance, mixture, sample, or category. The resolver therefore records `(concept, semantic scope, domain context)` and never forces every use of a word into one rigid identity.

**Scope in queries (Enhancement E-65).** An EquivalenceMapping carries its scope. When a consumer resolves an ID, it supplies its scope (default: the base ontology release and primary domain). A mapping outside the requested scope is not followed.

### 7.7.2 Shared versus domain-specific meaning

[F2-C §5.14] ENERGY occurs in physics, chemistry, biology, and engineering.

- **Shared concept:** one global ID (for example, 1008), with each domain contributing its own relations (WORK in physics, METABOLISM in biology, EFFICIENCY in engineering) as domain-tagged edges (Part 2, §2.13).
- **Different meaning:** "She has a lot of energy today" usually denotes perceived vitality or activity capacity. It does not map to the physical quantity. It is a separate sense (and concept) for the same word.

The cross-domain resolver separates shared concepts across domains from domain-specific meanings expressed by the same word. That is another reason the lexical layer is separate from the semantic layer (Part 2, §2.10).

### 7.7.3 Competing definitions

[F2-C §5.23] LIFE can be defined in biology, philosophy, and artificial-life research, and a single definition would force contradictions.

```text
LIFE (umbrella concept)
   ├─ DEFINITION_VARIANT: BIOLOGICAL_LIFE_DEFINITION
   ├─ DEFINITION_VARIANT: PHILOSOPHICAL_LIFE_CONCEPT
   └─ DEFINITION_VARIANT: ARTIFICIAL_LIFE_CONTEXT
```

These are not taxonomic subclasses. They are definitions, theories, or interpretations tied to a broad lexical-conceptual topic. An assertion records which variant it uses (`definition_ref`, Part 2, §2.11). Merging variants is never automatic.

---

## 7.8 Equivalence mappings and reversibility

### 7.8.1 Never merge destructively

[F2-C §5.12] When equivalence is discovered, both records stay. A mapping designates the canonical identity for the scope:

```text
CONCEPT 1001  (canonical)        CONCEPT 2050
EquivalenceMapping: 2050 → 1001, relation EQUIVALENT, scope S, grade, evidence, version
```

**SG-IDN-003 (Normative).** Concept equivalence is represented through reversible, versioned mappings. No record is physically deleted or rewritten.

**SG-IDN-009 (Normative, Enhancement E-62).** References **keep the ID that was used when they were created**. Equivalence is applied at **read time**, by following active mappings in the requested scope. Rewriting stored references to the canonical ID is forbidden. This is what makes reversal exact. If the merge is wrong, deactivating the mapping restores every earlier interpretation immediately, with no migration. Derived caches (inverse indexes, resolved-ID columns) may store canonical IDs but are regenerable and carry the mapping version used.

### 7.8.2 Lifecycle of a mapping

```text
PROPOSED → VALIDATED (certificate checks, §7.5.1) → REVIEWED → ACTIVE
                                                              ↓ (new evidence)
                                                          SUSPENDED → REVOKED | RE-ACTIVATED
```

- ACTIVE needs review per the risk class (VERY_HIGH, Part 6, §6.10, SG-IDN-002).
- **Revocation** (the "unmerge") is a new versioned event that deactivates the mapping, with reasons. It is a first-class operation, tested (§7.14).
- Mapping chains are resolved to a **single canonical ID per scope** with cycle checks (VC-I09) and a depth limit. Path compression is allowed only in derived caches.
- A concept that is **split** (REFINED_INTO two concepts, Part 2, §2.13) uses a migration record, not an equivalence. Old references keep their ID, and each reference is classed NOT_REVIEWED, AUTO_MIGRATED, REVIEWED, or REPROCESS_REQUIRED (SG-GOV-001).

**SG-IDN-002 (Normative).** Two records may be merged into one canonical concept only when their equivalence is established under the ontology's declared meaning and scope, at grade ESTABLISHED, and after review. Otherwise separate IDs are preserved and connected by the appropriate relation.

---

## 7.9 Unknown words and provisional concepts

### 7.9.1 Learning an unfamiliar word

**SG-LRN-001.** When encountering an unfamiliar word, first investigate whether it denotes an existing concept before proposing a new one [F3-B §7.11]. The sources distinguish three outcomes (F1-A §3.12):

| What was discovered | Result |
|---|---|
| A new word for an existing concept | Add a LexicalSense mapping only |
| A genuinely new concept | New concept (specialization, related, or fully new) |
| A new relation between existing concepts | Not a concept question (Part 9, knowledge learning) |

```text
"A hygrometer measures humidity."   (unfamiliar: hygrometer)
 R2  lexical: no entry
 R3  structural: retrieve HUMIDITY_SENSOR, MOISTURE_SENSOR, MEASURING_INSTRUMENT
 R8  compare constraints:
       HUMIDITY_SENSOR   ESSENTIAL: function = FN.DETECT {humidity}
       hygrometer claim  function = MEASURE_HUMIDITY (⊑ FN.DETECT)
       result: EQUIVALENT (SUPPORTED, definition of HUMIDITY_SENSOR INCOMPLETE) or NARROWER
 → no new canonical ID until the distinction is evaluated.
   Action: REUSE as lexical sense on HUMIDITY_SENSOR if review accepts; otherwise CREATE_SPECIALIZATION.
```

### 7.9.2 Provisional concepts

[F2-C §5.19] The system continues analysis when a term cannot be defined yet, by creating a placeholder rather than inventing a definition.

```text
PROVISIONAL_CONCEPT
  provisional_id (P-space)          lexical_form, language
  kind_hint, class_hints            from source evidence only
  definition_status = INCOMPLETE    validation_status = PENDING
  proposer, source_id, span, certificate
  created_at, expires_at, reference_count
```

**SG-IDN-006 (Normative, Enhancement E-66).**
1. A provisional concept is usable only inside provisional records.
2. A trusted record referencing a provisional ID is invalid (VC-S15).
3. Provisional concepts expire (TTL [Provisional: 30 days of inactivity]) unless referenced and under review. Expiry parks them in a REJECTED/ARCHIVED state. It does not delete them.
4. Counts are capped per source cluster (SG-SEC-007) so a hostile source cannot flood the provisional space.
5. **Resolution paths** for a provisional concept: link to an existing concept (MATCHED), define as a new concept, mark as a specialization, preserve as unresolved, or reject as an extraction error.
6. On resolution, a **promotion mapping** `P:1001 → C:n` is recorded. Provisional records referencing it are re-pointed, and the old reference stays resolvable. Trusted records never contained provisional IDs, so none needs rewriting.

### 7.9.3 Concept definition by the model

The model may propose a definition as **structured constraints**, never only as prose. Each proposed constraint cites a span (EXPLICIT) or an authorized resource, and is recorded as ESSENTIAL, TYPICAL, CONTINGENT, or CONTEXTUAL (Part 2, §2.9). A definition containing background-knowledge constraints without evidence is rejected (SG-EVD-001). A concept stays `definition_status = INCOMPLETE` until reviewed.

---

## 7.10 The Registry Manager

### 7.10.1 Responsibilities

[F2-C §5.18, §5.21] The Registry Manager is the **only writer** of concept identity. It:
1. Receives proposals (never direct writes).
2. Re-runs duplicate search at commit time.
3. Checks validation and review state.
4. Allocates IDs transactionally.
5. Commits the concept, mappings, certificate reference, and decision record atomically.
6. Records the decision and evidence for audit (SG-FND-006).

The registry is a lightweight locator. Detailed relations stay in the domain stores (Part 2, §2.13).

### 7.10.2 Concurrency (Enhancement E-63, E-20)

The source's case: Controller A meets "Automobile", Controller B meets "Car". Both find nothing because retrieval was incomplete, and both propose new concepts. Database transactions alone cannot detect that two *different strings* mean one thing [F2-C §5.18]. The design uses three layers:

| Layer | Mechanism |
|---|---|
| **Pending-proposal visibility** | Resolvers query a `PendingProposal` table together with committed concepts. When B runs R2–R5, A's pending "Automobile" proposal is a candidate, so B sees it and can reuse it or wait. This removes most races. |
| **Commit-time recheck** | Under an exclusive transaction the Registry Manager re-runs retrieval for the proposal, including all concepts committed or pending since the proposal was created. If a better match now exists, the decision changes (REUSE or hold). |
| **Duplicate sweep** | A scheduled low-priority job finds concept pairs with high retrieval similarity and compatible structure, and queues them as RESOLVE_CONCEPT tasks. This catches duplicates that every earlier layer missed. |

**SQLite specifics.** WAL journal mode, a single writer connection owned by the Registry Manager, `BEGIN IMMEDIATE` for commits, and a busy timeout. Proposals carry an **idempotency key** (hash of the normalized lexical form, language, proposed relation, and scope). Re-submitted work (retries, restarts, concurrent controllers) does not allocate a second ID. IDs are allocated inside the commit transaction so a rolled-back commit leaves no gap-dependent state. Gaps are harmless, because IDs carry no meaning.

### 7.10.3 Commit decision record

```text
RegistryDecision
  decision_id, proposal_id, idempotency_key
  resolution_status, action, resulting_ids
  certificate_id, validation_report_id, review_ids[]
  registry_state_version (before/after), recheck_candidates[]
  decided_at, decided_by (component, not model)
```

---

## 7.11 Drift, versioning, and ontology evolution

### 7.11.1 Semantic drift

[F2-C §5.20] If a concept's meaning changes gradually, old records stop matching their concept's definition. The system distinguishes:

| Change | Example | Process |
|---|---|---|
| **Adding a non-defining fact** | `CAR HAS_PROPERTY CanBeElectric` | Ordinary MINOR addition. Lighter process. |
| **Changing a defining constraint** | `CAR = any object that moves` | MAJOR. SG-GOV-001: version, compatibility evaluation, review of affected references. |

### 7.11.2 The change procedure (SG-GOV-001 in operation)

```text
1. Proposal: definition v(n+1) with diff against v(n)
2. Classify: ADDITIVE (non-defining) | NARROWING | WIDENING | REPLACING
3. Impact analysis: list assertions/instances that use this definition (by definition_ref and by concept id)
      NARROWING  → records that no longer satisfy the definition are flagged
      WIDENING   → records are still valid. Identity relations to other concepts are re-evaluated.
      REPLACING  → treat as a new concept plus a migration
4. Re-evaluate EquivalenceMappings whose scope included this concept
5. Review (Part 6 §6.10 class VERY_HIGH for defining changes)
6. Release: new OntologyRelease; migration records; old version remains resolvable
```

### 7.11.3 Drift monitoring

A periodic job compares each concept's current definition with its definition at the last release (and with its first). Monitored indicators:

- ESSENTIAL constraint churn per concept
- Relation additions that alter the meaning of IS_A closure
- Rate of merges, splits, and revocations
- Growth in INCOMPLETE definitions
- Increase in disputes involving the concept

Concepts with abnormal churn are queued for review. These are descriptive statistics, not a truth score.

### 7.11.4 Ontology versions and old data

[F2-C §5.24] A record pins its OntologyRelease. A refinement (`CONCEPT_A REFINED_INTO CONCEPT_A1, CONCEPT_A2`) does not rewrite old records. A reprocessing job may re-interpret them against the new release under budget (Part 9). Historical representations stay interpretable.

---

## 7.12 Review and risk for identity operations

[Part 6, §6.10; F3-B §7.18]

| Operation | Static risk class |
|---|---|
| RESOLVE_SENSE through an exact, trusted lexical mapping | LOW |
| RESOLVE_SENSE among several plausible senses | MEDIUM |
| REUSE_EXISTING_CONCEPT, grade SUPPORTED | MEDIUM |
| CREATE_RELATED_CONCEPT, CREATE_SPECIALIZATION | MEDIUM–HIGH |
| CREATE_NEW_CONCEPT | HIGH |
| CREATE_GENERALIZATION | HIGH–VERY_HIGH |
| EquivalenceMapping between two existing records | VERY_HIGH |
| Splitting or revoking a mapping | HIGH |
| RESOLVE_INDIVIDUAL, strong external ID | LOW–MEDIUM |
| RESOLVE_INDIVIDUAL, name only | Not allowed to resolve. UNRESOLVED. |

The Metacognition signals for resolution [F2-C §5.27] are interpretable and fixed:

```text
CANDIDATES_FOUND       number of candidates after R6
FORMAL_EQUIVALENCE     ESTABLISHED | SUPPORTED | CANDIDATE | NOT_ESTABLISHED
CONTEXTUAL_AMBIGUITY   from the ContextIntegrator (ordinal)
TYPE_CONFLICT          from VC-I04/I05
TRUSTED_LEXICAL_MAP    available?
METHOD_AGREEMENT       independent extraction/resolution agree?
EVIDENCE_COVERAGE      fraction of constraints supported by spans
OUTSIDE_ONTOLOGY       no registered neighbour
```

None of these is a measure of semantic correctness. They only decide what extra processing is needed (Part 6, §6.9).

---

## 7.13 What Python can do and what cannot be guaranteed

[F2-C §5.25]

**Deterministic (Python and the database):**
- Exact ID search; lexical lookup
- Structural retrieval; constraint comparison; entailment (sound, incomplete)
- Type compatibility; exact structural duplicate detection (hash of canonical definition, SG-CAN-004)
- Uniqueness and registration policies; transactional commits
- Versioned aliases and mappings; evidence recording

**AI-assisted (proposals only):**
- Interpreting unfamiliar definitions; proposing senses; contextual meaning
- Comparing natural-language descriptions; suggesting similarities
- Proposing abstractions; spotting possibly missing distinctions

**Not guaranteed by any design:**
- Whether two incomplete natural-language definitions are truly equivalent
- Resolving ambiguous references without enough context
- Verifying a concept's scientific correctness from insufficient evidence
- Finding all counterexamples to a proposed universal rule

For these the architecture preserves uncertainty (UNRESOLVED, provisional concepts, separate records) and does not force a decision.

---

## 7.14 Evaluation and tests

### 7.14.1 Metrics

(The sources' list, with definitions.)

| Metric | Definition |
|---|---|
| Duplicate concept rate | Fraction of committed concepts later judged equivalent to an earlier concept (audit or sweep) |
| Incorrect merge rate | Fraction of ACTIVE mappings later revoked or judged wrong |
| Concept resolution accuracy | Correct concept ID or correct "none" on gold pairs |
| Abstention quality | Of UNRESOLVED outcomes, fraction where gold also says "not determinable from context". Of resolved, error rate. |
| Provisional backlog | Provisional concepts open per week, and median time to resolution |
| Reversal exactness | After merge then revoke, the system state (read-time resolution) equals the pre-merge state |
| Drift indicators | §7.11.3 |

### 7.14.2 Gold set (to build before scaling)

Pairs with human-reviewed relation and scope:

| Category | Examples |
|---|---|
| Equivalent | car / automobile / motorcar |
| Subsumption | car ⊑ vehicle; liquid ⊑ fluid |
| Overlap, scope-dependent | doctor / physician; amphibious vehicle |
| Related-not-equal | doctor / hospital |
| Antonym trap (embedding-near) | hot / cold |
| Disjoint | even / odd |
| Polysemy | bank (3 senses), virus (biological/software), heart (organ/centre of city) |
| Cross-domain | energy (physical quantity) vs "energy" (vitality) |
| Definition-variant | life |
| Individual | "John" ×3, same Wikidata entity vs different |
| Event trap | "John bought a book" twice |
| Concurrency | simultaneous proposals "Car" and "Automobile" |

### 7.14.3 Required tests

| Test | Pass condition |
|---|---|
| Embedding-trap test | Embedding-near but non-equivalent pairs are never merged |
| Merge-revoke round trip | State after revoke equals state before merge (read-time) |
| Concurrency test | Simultaneous proposals of equivalent concepts produce one concept, or exactly one plus a queued duplicate sweep task |
| Idempotency test | Re-submitting a proposal does not allocate a new ID |
| Provisional leakage test | No trusted record contains a provisional ID |
| Scope test | A mapping valid in scope S is not followed in scope S′ |
| Open-world test | A concept lacking a property is not judged different for that reason alone |
| Drift test | A defining-constraint change forces version bump, impact list, and review |
| Cycle test | A mapping that would create a cycle is rejected |
| Individual-merge test | Two referents of the same class are never merged by concept equality |

---

## 7.15 Worked examples

### 7.15.1 A known synonym (low cost)

```text
"The automobile stopped."
R1 no id.  R2 lexical: "automobile" has no entry, but ExternalMapping from a WordNet synset shared with "car".
R8 constraints of CAR: complete in the everyday scope; no contradiction.
Result: MATCHED (SUPPORTED) → REUSE_EXISTING_CONCEPT: add LexicalSense "automobile" → CAR. No new concept.
Risk class: MEDIUM (SUPPORTED grade, not ESTABLISHED) → quick reviewer or independent-method agreement.
```

### 7.15.2 A genuinely new concept (full pipeline)

> A ventricular assist device helps the heart pump blood. [F2-C §5.22]

Dictionary has HEART, BLOOD, PUMP, MEDICAL_DEVICE. It lacks VENTRICULAR_ASSIST_DEVICE.

| Step | Detail |
|---|---|
| 1. Interpretation | The local model proposes NEW_TERM `VentricularAssistDevice`, IS_A MedicalDevice, function AssistBloodPumping, related to Heart. Each constraint cites a span. |
| 2. Retrieval (R2–R5) | Candidates: CardiacAssistDevice, MechanicalCirculatorySupportDevice, BloodPump |
| 3. Comparison (R8) | The proposal is narrower than MechanicalCirculatorySupportDevice. Not equal to BloodPump (a component, not a device class). A definition for CardiacAssistDevice is incomplete → cannot establish equivalence. |
| 4. Frame and function link | `HAS_FUNCTION FN.TRANSPORT` qualifier (assist blood flow) via the circulation frame |
| 5. Certificate | CANDIDATE_CONCEPT, PARENT_CONCEPT, defining relationships, source evidence, rule references |
| 6. Validation | VC-I01..I10; parent relationship appropriate; no conflict with existing constraints; no duplicate |
| 7. Review | Class HIGH (new concept). Technical source needed for the definition. Provisional concept created while pending. |
| 8. Registration | If approved: Registry assigns a stable ID, stores the definition once, records the decision. |

Outcome: CREATE_SPECIALIZATION under MECHANICAL_CIRCULATORY_SUPPORT_DEVICE. "The exact definitions and relationship types would need to be validated against suitable technical sources" [F2-C §5.22], so the concept remains `definition_status = INCOMPLETE` until then.

### 7.15.3 An embedding trap

```text
Proposal: "ColdTemperature"   Retrieval R4 returns HotTemperature at similarity 0.91.
Comparison: both kind PROPERTY-VALUE, same dimension TEMPERATURE, ESSENTIAL ranges disjoint.
Result: DISJOINT (contrary values). The embedding score is recorded as a retrieval signal only.
Action: CREATE_NEW_CONCEPT (or reuse an existing COLD value) — never REUSE of HotTemperature.
```

### 7.15.4 A wrong merge and its reversal

```text
Day 1  EquivalenceMapping 2050 → 1001 (EQUIVALENT, scope=everyday) ACTIVE.
Day 9  New evidence: assertions about 2050 (PassengerCar) use constraint "seats ≥ 2 adults"; 1001 (Car) includes motorcycles with sidecars.
       Mapping SUSPENDED → REVOKED (reason: not equivalent in everyday scope; recorded as SUBSUMED_BY).
Effect Reads of records originally using ID 2050 no longer resolve to 1001. Stored references were never rewritten (SG-IDN-009).
       A new mapping 2050 SUBSUMED_BY 1001 is proposed through the normal path.
```

---

## 7.16 Closure of the sources' decisions

[F2-C §5.31] Every decision from the source's table, with where it is specified:

| Decision (source) | Specified in |
|---|---|
| Separate lexical forms from semantic concepts | Part 2 §2.10; §7.1 |
| Stable IDs independent of labels | Part 2 §2.4 |
| Resolve individual identity separately | §7.6 |
| Compare structured meanings, not only text | §7.3 |
| Lexical, graph, and embedding indexes | §7.4 |
| Equivalence needs strong evidence within a declared scope | §7.2.2, §7.7 |
| Open-world reasoning by default | §7.3.3 (SG-KNW-001) |
| Reversible, versioned equivalence mappings | §7.8 (SG-IDN-003, SG-IDN-009) |
| Provisional records for unknown concepts | §7.9 |
| AI may propose but not authorize identity changes | Part 5 §5.9; §7.10 |
| Coordinated transactional registry | §7.10 |
| Shared global IDs with domain-specific knowledge | Part 2 §2.13; §7.7.2 |
| Canonical IDs separate from compact codes | §7.17 |
| Version definitions and preserve history | §7.11 |

Open questions closed here: F2-A §3.28 item 4 (concept identity and deduplication procedures), F1-D §2.29 (how concept identity is established automatically), and F2-B §4.28 (five possible relations between "equivalent" structures: same concept / same function / shared structure / specialization / analogy). The last maps as: same concept → EQUIVALENT; same function → HAS_FUNCTION relation (SG-FRM-005); shared structure → StructuralAnalogy (SG-FRM-007); specialization → SUBSUMED_BY; analogy only → RELATED plus an analogy record.

---

## 7.17 Identity, compression, and encoding

[F2-C §5.28–5.29]

- **Deduplication is judged on net storage savings** and never on how many IDs it removes. Lexical mappings, equivalence indexes, and review metadata also cost space.
- **Correctness has priority over compression.** A wrong merge may shrink the database while destroying information.
- **Identity and binary encoding are independent.** The registry may assign CAR = 1,058,421. The binary encoder may store local code 17, a variable-length integer, or another compact form, without changing the canonical identity (Part 11). This lets the encoder improve without touching meaning.
- Equivalence mappings are applied *before* encoding only where an export asks for canonical IDs. The default store keeps original IDs (SG-IDN-009).

---

## 7.18 Rules and enhancements

### Rules registered or refined in this part

| Rule | Statement |
|---|---|
| SG-IDN-001 | Search before create: run R1–R7 before any new concept (alias SG-005) |
| SG-IDN-002 | Merge only at grade ESTABLISHED, in scope, after review |
| SG-IDN-003 | Equivalence as a reversible, versioned mapping |
| **SG-IDN-004** | Similarity (lexical, embedding, text, model) never establishes identity |
| **SG-IDN-005** | Concept resolution never merges referents. Individuals resolve separately. |
| **SG-IDN-006** | Provisional concepts: confined to provisional records, TTL, caps, promotion mapping |
| **SG-IDN-007** | The Registry Manager is the sole identity writer. Recheck at commit. Idempotent proposals. |
| **SG-IDN-008** | Equivalence requires a declared scope and is followed only within it |
| **SG-IDN-009** | References keep original IDs. Equivalence is resolved at read time. |
| SG-LRN-001 | Investigate existing concepts before proposing new ones for unfamiliar words |
| SG-GOV-001 | Defining-constraint changes require versioning, impact analysis, and review |

### Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-61 | Status list had GENERALIZATION but no matching action | CREATE_GENERALIZATION, with higher risk (§7.2.3) |
| E-62 | Reversibility depended on being able to rewrite references | Keep original IDs, resolve at read time (SG-IDN-009) |
| E-63 | Transactions cannot detect two different strings meaning one thing | Pending-proposal visibility, commit-time recheck, duplicate sweep (§7.10.2) |
| E-64 | "Strong evidence of identity" was undefined | Grades ESTABLISHED / SUPPORTED / CANDIDATE / INSUFFICIENT (§7.2.2) |
| E-65 | Scope was recorded but not used in resolution | Scope-parameterized read-time resolution (§7.7.1) |
| E-66 | Provisional concepts had no lifecycle limits | TTL, caps, promotion mapping (§7.9.2) |
| E-67 | Embedding indexes could silently mix model versions | Model ID and version stored per vector. Rebuild on change (§7.4.2) |
| E-68 | The source's identity certificate cited the wrong rules, and the rules were unwritten | Rules SG-IDN-001…009 and checks VC-I01…I10 (§7.5) |



---


# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 8 of 12: The Interpretation Pipeline

This part specifies how natural language becomes validated semantic IR. It answers the question that started the project: *how can a Python program or a local AI model discover the meanings of words and sentences well enough to build the dictionary?* [F1-A intro]. The sources' answer is that **no component understands everything.** Established linguistic tools provide structure. A local model resolves contextual choices among *existing* options. Deterministic code enforces the grammar. Resources supply the first knowledge, and anything unfamiliar is treated as a candidate.

---

## 8.1 The pipeline at a glance

### 8.1.1 Nine stages plus registration

The semantic-compiler stages of F1-A §3.9 are kept. Stage 0 is added because registration, anchoring, and security come before any analysis (Part 6, §6.13).

| Stage | Name | Produces | Nature | Defined in |
|---|---|---|---|---|
| 0 | Source registration | Source record, anchor, tier, normalized view | Deterministic | Part 2 §2.12; Part 6 §6.13 |
| 1 | Tokenizer | Tokens, sentences, lemmas | Deterministic or statistical tool | §8.3 |
| 2 | Syntax analyzer | POS, morphology, dependencies | Statistical tool | §8.3 |
| 3 | Semantic parser | Candidate IR + derivation certificate | Rules + local model | §8.4–§8.9 |
| 4 | Frame resolver | Frame, variant, parameters | Lexicon + rules (+ model for choices) | §8.6 |
| 5 | Concept resolver | Concept IDs, provisional concepts | Retrieval + comparison | Part 7 |
| 6 | Validator | ValidationReport, routing | Deterministic | Part 5 |
| 7 | Semantic IR | Canonical, validated structure | Deterministic | Part 3 §3.17 |
| 8 | Binary encoder | Compact bytes | Deterministic | Part 11 |
| 9 | Knowledge store | Persistent records | Deterministic | Part 11 |

Stages 3, 4, and 5 interleave. A frame choice depends on sense choice, sense choice depends on retrieved concepts, and concept resolution may need the frame. The pipeline is a controlled loop, not a one-way line. The central controller owns the loop and its budgets (§8.18).

### 8.1.2 Four levels of understanding

F1-A §3.2 describes the progression that the stages implement:

| Level | Task | Stage | Typical tool |
|---|---|---|---|
| 1 | Recognise words | 1 | Tokenizer |
| 2 | Recognise grammatical categories | 2 | POS tagger |
| 3 | Recognise grammatical relationships | 2 | Dependency parser |
| 4 | Recognise semantic roles (*what happened*, not *how the sentence is built*) | 3–4 | Rules + model, evaluated against SRL-style resources |

Level 4 matters because different grammatical constructions can map to one structure. "The doctor gave the patient medication" and "The patient was given medication by the doctor" differ at Level 3 and agree at Level 4 [F1-A §3.2].

---

## 8.2 Stage 0: registration and segmentation

1. **Register** the source: text, hash, language, anchor (document date, time zone, calendar), genre, trust tier, sensitivity label (Part 2 §2.12).
2. **Normalize** to a processing view with an offset map. Stored text is never altered (SG-SEC-005).
3. **Scan** for tripwires and limits (SG-SEC-004, SG-SEC-006).
4. **Segment** into sentences and, where useful, paragraphs. Segmentation is a tool output and can be wrong (§8.3.3). Segment boundaries are stored as spans.
5. **Create a discourse context** for the document: an empty referent table and salience list, shared across sentences so that pronouns and definite descriptions can resolve across sentence boundaries (§8.7).

---

## 8.3 Stages 1–2: language analysis

### 8.3.1 The analysis record

```text
LinguisticAnalysis
  source_id, language, tool_id + version
  sentences[]      (span)
  tokens[]         (span, text, lemma, pos, morph{}, is_stop, ner?)
  dependencies[]   (head, dependent, relation, label_scheme)
  alt_parses[]     optional n-best parses for flagged attachments
  flags[]          (ATTACHMENT_AMBIGUOUS, FRAGMENT, UNKNOWN_WORD, CODE_SWITCH, ...)
```

### 8.3.2 Tool choices

[F3-C §8.5–8.6, to be confirmed by the verification gate in Part 12]

- **spaCy** for the first English prototype. It offers tokenization, lemmatization, POS tagging, dependency parsing, entity recognition, and rule-based matching over dependency structures [F1-A §3.2, §3.7; F3-C §8.6].
- **Stanza** compared on the same test sentences before a long-term parser is chosen. Its parser uses Universal Dependencies, which fits the multilingual aim [F3-C §8.6].
- Tools sit behind a `LinguisticParser` interface. Switching parsers does not change the grammar.

### 8.3.3 The parser is evidence, not authority (Enhancement E-69, SG-INT-003)

A dependency parse is produced by a statistical model with its own errors, so it is a **tool output that supports a derivation. It is not a fact.**

1. A certificate step that depends on a parse records the parser, the version, and the arcs used.
2. When a step's correctness depends on an arc the tool is known to get wrong (prepositional-phrase attachment, coordination scope, relative-clause attachment), the pipeline raises `ATTACHMENT_AMBIGUOUS`, requests an **n-best** analysis where the tool provides one, and lets Stage 3 decide between readings or retain an ALT (§8.9).
3. A second, independent method (a different parser, or the model's own reading) is a source of METHOD_DISAGREEMENT signals (Part 6 §6.9).
4. Sentence segmentation errors are handled the same way: unit boundaries can be re-segmented on validation failure.

### 8.3.4 Label maps (Enhancement E-74)

Valence patterns (§8.5) refer to **abstract grammatical functions** (SUBJECT, OBJECT, INDIRECT_OBJECT, OBLIQUE(prep), AGENT_PHRASE, PASSIVE_SUBJECT, CLAUSAL_COMPLEMENT, …), based on Universal Dependencies. A **label map** per parser and model version translates tool-specific labels into these functions. Stanza emits UD labels. A given spaCy model may use another scheme, depending on language and version. Rules are therefore written once and a parser upgrade means a new label map plus a regression run. It never means rewriting rules.

---

## 8.4 Stage 3: the semantic parser

### 8.4.1 Sub-steps

```text
P1  Mention detection        → referents (kind, instance_of candidates, number, cardinality, definiteness)
P2  Trigger detection        → lexical units that may evoke a frame, state, relation, or operator
P3  Sense and frame candidates → via lexicon (SemanticHub) → LexicalFrameLinks (§8.5)
P4  Valence mapping          → dependency arcs → role bindings, with basis and value state
P5  Operator attachment      → negation, modality, tense, aspect, quantifiers, attribution (§8.8)
P6  Embedding and control    → clause structure → CONTENT roles, control hints, relatives, coordination
P7  Coreference              → links between referents, with evidence (§8.7)
P8  Candidate assembly       → expression + derivation certificate (Part 5 §5.8)
```

Each sub-step records its certificate step (Part 5). Every unresolved choice is passed to the choice machinery of §8.11 instead of being guessed.

### 8.4.2 Three implementations compared

F1-A §3.16 lists three implementations to compare on one benchmark. Part 12 runs them under identical conditions.

| | A: Rules + parser | B: Local model producing structure | C: Hybrid (default) |
|---|---|---|---|
| P1, P2 | Rules and lexicon | Model | Rules and lexicon |
| P3 | Lexicon | Model | Lexicon proposes, model selects among candidates |
| P4 | Valence rules | Model | Valence rules where a pattern exists, model for gaps |
| P5 | Cue rules | Model | Cue rules, model for ambiguous cues |
| P6–P7 | Partial rules | Model | Rules for clear cases, model for hard cases |
| Strengths | Deterministic, fast, testable | Broad coverage | Auditable coverage with limited model calls |
| Weaknesses | Misses unfamiliar constructions | Inconsistent, can invent | More moving parts |

Implementation C is the recommended default because it matches F1-A §3.9–3.11. The hybrid does as much as possible deterministically and calls the model for ambiguity, unfamiliar structure, new concepts, rule conflicts, and context dependence.

### 8.4.3 Abstract Meaning Representation as a reference

[F1-A §3.3; F3-C §8.7.5] AMR represents sentence meaning as graphs of concepts and relations. It is a *reference architecture for interpretation*. It is not USG's storage format, because USG additionally needs stable concept identity, ontology versioning, persistent memory, and compact encoding.

The lessons carried over from AMR:
- **Reentrancy:** "The boy wants to eat an apple" has one boy participating in two situations. USG likewise makes one referent fill roles in two frame instances (graph, not duplicated tree) [F1-A §3.3; F1-D §2.8].
- Negation, time, polarity, and quantity are first-class.
- Parsers for AMR and their gold data are evaluation resources.

AMR graphs are never imported as USG content. Mapping is by explicit rule (§8.13).

---

## 8.5 The lexical layer in interpretation

### 8.5.1 Words are not concepts

[F1-A §3.4; F1-D §2.20; Part 2 §2.10] The lexicon maps word forms to senses, and senses to concepts and frames. It stores *possibilities* and context cues. It never decides. Deciding is the ContextIntegrator's job (Part 7 §7.4.3).

```text
lexical_dictionary["bank"] =
   [ { sense: 1, concepts: [FINANCIAL_INSTITUTION], cues: [loan, approve, deposit, account] },
     { sense: 2, concepts: [RIVER_BANK],            cues: [river, fisherman, shore, water]   },
     { sense: 3, concepts: [STORAGE_FACILITY],      cues: [blood, data, seed]                } ]
```

Cues influence ranking. They do not select. "bank + loan → financial institution is likely" is a heuristic that can be wrong ("the bank near the river approved the loan" has competing cues).

### 8.5.2 LexicalFrameLink and valence patterns (Enhancement E-55, E-74)

A lexical sense that evokes a frame carries its **valence patterns**: how grammatical functions map to roles in each construction.

```text
LexicalFrameLink
  sense_id, frame@version, perspective_variant?, parameter_pins{}
  trigger_class         VERB | NOUN | ADJECTIVE | PREPOSITION | CONSTRUCTION | MULTIWORD
  patterns[]            ValencePattern
  selectional_hints     class preferences per role (soft)
  source                MANUAL | IMPORTED(VerbNet/FrameNet/PropBank, mapping grade) | LEARNED
```

```text
ValencePattern
  construction     ACTIVE_TRANSITIVE | ACTIVE_DITRANSITIVE | ACTIVE_DATIVE | PASSIVE_WITH_AGENT
                   | PASSIVE_NO_AGENT | MIDDLE | INCHOATIVE | CONTROL_XCOMP | ...
  mapping          grammatical function → role   (+ basis, + value-state for absent functions)
  conditions       e.g. requires aux:pass, by-phrase present
```

**Why it matters.** The naive rule "passive subject becomes the affected participant" is wrong for ditransitives. For *give*:

| Sentence | Construction | Mapping |
|---|---|---|
| John gave Mary a book. | ACTIVE_DITRANSITIVE | SUBJECT→AGENT (and SOURCE), INDIRECT_OBJECT→RECIPIENT, OBJECT→THEME |
| John gave a book to Mary. | ACTIVE_DATIVE | SUBJECT→AGENT/SOURCE, OBJECT→THEME, OBLIQUE(to)→RECIPIENT |
| Mary was given a book by John. | PASSIVE (recipient subject) | PASSIVE_SUBJECT→RECIPIENT, OBJECT→THEME, AGENT_PHRASE→AGENT/SOURCE |
| A book was given to Mary by John. | PASSIVE (theme subject) | PASSIVE_SUBJECT→THEME, OBLIQUE(to)→RECIPIENT, AGENT_PHRASE→AGENT/SOURCE |
| Mary was given a book. | PASSIVE_NO_AGENT | as above, AGENT: UNSPEC (never invented) |

For *examine*: ACTIVE: SUBJECT→EXAMINER, OBJECT→EXAMINED_ENTITY. PASSIVE: PASSIVE_SUBJECT→EXAMINED_ENTITY, AGENT_PHRASE→EXAMINER, and with no by-phrase EXAMINER is UNSPEC.

The rules SG-INT-010 to SG-INT-012 (Part 5) read these patterns. They do not hard-code role correspondences.

**A by-phrase may not be an agent.** "The house was built by the river" matches the surface of PASSIVE_WITH_AGENT. The pattern's condition requires the by-phrase to denote an entity compatible with the AGENT constraint (SG-TYP-001) and the judgment half of SG-INT-010 (Part 5 §5.3) decides when the type check is UNDETERMINED.

### 8.5.3 Prepositional and adjunct roles

Prepositions are polysemous, and the roles they introduce depend on the head and the complement [F1-A §3.7]:

| Phrase | Possible roles |
|---|---|
| John broke the window **with a hammer** | INSTRUMENT (hammer is class-compatible with tool use) |
| John met a man **with Mary** | COMITATIVE |
| John worked **with care** | MANNER |
| John saw the man **with a telescope** | INSTRUMENT of seeing **or** a possession/attribute of the man: an ALT (§8.9) |

A pattern proposes candidate roles. Type constraints and selectional hints filter them. If more than one survives, the unit is an ALT.

### 8.5.4 Idioms and multiword units

The lexicon holds idioms and multiword units as entries (Part 2 §2.10). "John bought the argument" is the source's warning case [F1-A §3.11]. Syntactic similarity to "John bought a car" proves nothing. Two things guard it:
- The sense of *buy* with an abstract THEME (argument, story, excuse) is a registered figurative sense (`BELIEVE`/`ACCEPT`), or is routed to the figurative path (§8.10).
- The frame's selectional hints make the commercial reading UNDETERMINED or INCOMPATIBLE for an abstract GOODS filler (SG-TYP-001, SG-TYP-002).

### 8.5.5 Lexical coverage

An unknown word (no lexical entry) is *not* an error. It raises UNKNOWN_WORD, and Part 7 §7.9 applies: first check for an existing concept, then create a lexical mapping or a provisional concept.

---

## 8.6 Stage 4: the frame resolver

The frame resolver chooses a frame for a situation-evoking trigger and fills its parameters.

1. **Candidates.** From P3: LexicalFrameLinks for the trigger's plausible senses.
2. **Constraint filter.** Drop candidates whose REQUIRED roles cannot be filled from the available arguments, or whose type constraints are INCOMPATIBLE.
3. **Selection.** If one survives, take it. If several survive, a *closed-set* choice goes to the model (§8.11), with NONE_OF_THESE allowed.
4. **Perspective and parameters.** Apply the lexical link's perspective variant and pinned parameters (Part 4 §4.3.3, §4.4.3).
5. **Frame gap.** If nothing fits and a trigger is clearly present, record `FRAME_GAP` (SG-INT-008, Enhancement E-73) and do not force the nearest frame. The unit becomes UNRESOLVED or ALT, and a frame proposal can follow (Part 9). Forcing "lease" into TRANSFER would destroy distinctions that matter [F3-B §7.13].

### The context-sensitivity example

[F1-A §3.5] The same two concepts occupy different frames. The *frame* is selected by the relation between them:

| Sentence | Selected frame | Roles |
|---|---|---|
| John went to the hospital. | MOVE | MOVER = John, DESTINATION = hospital |
| John works at the hospital. | WORK | WORKER = John, WORKPLACE = hospital |
| John owns the hospital. | OWN | OWNER = John, OWNED_ENTITY = hospital |

---

## 8.7 Referents, coreference, and control

### 8.7.1 Referent creation

Each noun phrase that introduces a participant creates a referent (Part 2 §2.5): kind, instance-of candidates, number, cardinality ("two tablets" gives cardinality 2), definiteness (as annotation), and genericity (SPECIFIC or GENERIC). Properties like "young" become PropertyAssertions on the referent. Proper names are referents with a NAME property (Part 3 §3.4.3).

### 8.7.2 Context of introduction (Enhancement E-71, SG-INT-007)

A referent introduced inside an embedding context is not committed to exist in the world. "The boy wants to eat an apple" does not assert that an apple exists. The apple referent is introduced **inside the CONTENT of WANT**. This is an amendment to Part 2 §2.5:

```text
Referent (additional field)
    introduced_in      the context in which this referent is introduced:
                       WORLD(source) | CONTENT_OF(frame_instance, role) | NEGATED(prop) | CONDITIONAL(prop) | HYPOTHETICAL(...)
```

A referent's `introduced_in` determines where its existence commitment lives (it is existential only in that context). A pronoun or later mention may refer to it only if the discourse model makes that context accessible. "John wants to buy a car. It should be red." allows a modal-subordination reading, with "it" in the same wish-context. A later claim "The car was damaged" does **not** pick it up as a world referent. This is the Part 3 §3.6 rule (SG-CON-005e) applied to discourse referents.

### 8.7.3 Coreference

[F1-A §3.13; F2-A §3.24; F3-B §7.9] Pronoun and anaphor resolution creates a validated link (Part 3 §3.12):

```text
Candidates: referents in the discourse model that match number, animacy class, and type constraints
Evidence:   syntactic constraints, recency/salience, role parallelism, frame constraints
            (only an inanimate medication can be an ALLERGEN — and "it" has number singular)
Output:     SAME_AS(pronoun_referent, antecedent, DISCOURSE)  with evidence
            or ALT over antecedents, or UNRESOLVED
```

Coreference resolution is a hybrid step: rules and constraints produce a candidate list, and the model chooses only within it. A choice among several equally plausible antecedents is an ALT. Silent attachment to the nearest noun is never acceptable (SG-CON-005e).

### 8.7.4 Control, raising, and shared participants

[F1-A §3.3] In "The boy wants to eat an apple", the embedded subject is not written. The CONTROL_XCOMP valence pattern of WANT carries the `SUBJECT_CONTROL` hint (Part 4 §4.12.3):

```text
WANT(EXPERIENCER: R1, CONTENT: EAT(EATER: R1, FOOD: R2))
EATER = R1 is basis GRAMMATICAL, via SG-INT-006
```

SG-INT-006 (control): the unwritten subject of a controlled complement co-refers with the controller named by the governing frame's control hint (subject, object, or none). *Persuade* has object control ("Mary persuaded John to leave": John leaves). *Promise* has subject control. A wrong control assignment inverts who acts, so control hints are stored on the lexical link, and the case is MEDIUM risk until the hint is audited.

---

## 8.8 Operators: cues and default readings

The interpretation rules attach operators from linguistic cues. The mapping is conventional and each default can be overridden by evidence. Genuine doubt becomes an ALT (Part 3 §3.14).

| Category | Cues | Default operator | Notes |
|---|---|---|---|
| Negation | not, n't, never, no (determiner), none, neither, without | `NOT` over the proposition, or `Q(NO)` for the determiner "no" | Scope defaults to the clause. "did not eat every apple" gives NOT>FORALL as the default and FORALL>NOT only with evidence (Part 3 §3.7.3). Double negation is kept (SG-CAN-002). |
| Modality | may, might, can, could, must, should, ought, will, would | MODAL force × flavor | *must*, *may*, *can* are flavor-ambiguous. Context chooses and an ALT retains the doubt (SG-INT-021). *will* is TENSE(FUTURE) in many uses and MODAL in others. |
| Tense | past forms, present, will/going to, past perfect | TENSE(tense, reference_time, PROP) | Reference time defaults to the speech time and shifts with "when…" clauses |
| Aspect | be + -ing, have + participle, used to | ASPECT(PROGRESSIVE / PERFECT / HABITUAL) | Aspect gates entailments (Part 4 §4.4.1) |
| Quantification | every, each, all, some, a/an (indefinite), no, two, most, few, many, the (definite) | Q(…) or a referent plus cardinality | "a/an" introduces a referent, not automatically EXISTS over the world |
| Conditional | if, unless, provided that | COND(antecedent, consequent) | "unless" is COND with negated antecedent |
| Causal / explanatory | because, since (causal), so, therefore, due to, as a result | CAUSATION with a CAUSE_TYPE (Part 3 §3.11) | *since* is also temporal. Keep both as an ALT where unclear (SG-INT-031). |
| Temporal ordering | before, after, when, while, until, since (temporal) | TEMPORAL(AllenRel, …) | *while* is concurrency (OVERLAPS/DURING). *when* is context-dependent. |
| Attribution | said, believes, thinks, claims, reported, according to | ATTRIBUTE or an attitude/communication frame | Commitment holder follows (Part 6 §6.2) |
| Evidentials | hearsay and perception markers; in some languages, morphology | ATTRIBUTE(source, mode, p) | Truth-conditional, so the grammar carries it (SG-CON-004) |

Cues inside quotation or named expressions are not operators. Cues in the scope of other operators nest accordingly.

### Time resolution

`RESOLVE_TIME(expr, anchor, calendar)` (Part 3 §3.9.1) is a Python function, not a model call. "Yesterday" with a document dated 2026-10-16 resolves to 2026-10-15. A document with no anchor leaves it as `TIME_REL(YESTERDAY)`. Weekday names, "next week", and similar expressions follow declared calendar rules per language and locale (Enhancement E-14).

---

## 8.9 Ambiguity policy

### 8.9.1 When to retain an ALT

[F1-A §3.7; F3-B §7.33] Preserving multiple interpretations is a requirement, not a weakness.

| Condition | Action |
|---|---|
| Context decisively favors one reading (cues, constraints, frame fit) and the others fail validation | Select it. Record the others as REJECTED_ALTERNATIVE with reasons. |
| ≥ 2 readings pass validation and no deterministic or contextual evidence favors one | Retain as ALT (SG-INT-009) |
| Ambiguity is a property of the source and wider context could resolve it | ALT now. Mark `RETRY_WITH_CONTEXT`. |
| More alternatives than the budget allows | Keep the top-ranked, record how many were dropped, and set UNRESOLVED if the dropped ones could change meaning |
| Reading is only possible under implausible constraint violations | Drop |

### 8.9.2 Typical ambiguity sources

| Source | Example | Representation |
|---|---|---|
| Attachment | "John saw the man with a telescope" | ALT (INSTRUMENT vs possession) |
| Scope | "John did not eat every apple" | Default NOT>FORALL, ALT if evidence supports another |
| Sense | "The bank collapsed" | ALT (financial vs landform) when context is absent |
| Modal flavor | "John must be home by now" | ALT (epistemic vs deontic), context usually decides |
| Coreference | "John told Bill that he won" | ALT over antecedents |
| Lexical-vs-figurative | "The computer swallowed the file" | Literal fails type check. FIG proposed (§8.10). |

### 8.9.3 Ranking is ordinal

Rank evidence uses the signals of Part 6 §6.9. No probability is attached unless the producing method is calibrated (Part 6 §6.10.4).

---

## 8.10 Figurative language and metonymy

[F2-A §3.6; F1-C §5.2, §6]

1. **Literal attempt:** build the literal reading. If it passes SG-TYP-001, stop.
2. **Registered senses first.** Many figurative uses are lexicalised senses of a word (the "centre of" sense of *heart*, "accept as true" sense of *buy*). Choosing a registered sense is ordinary sense selection and needs no FIG node.
3. **Registered mappings** (metaphor, metonymy, type shift) apply next (SG-TYP-002).
4. **Novel figurative use:** the model may *propose* a mapping as a candidate. The unit is AMBIGUOUS or UNRESOLVED until a mapping is approved. The literal meaning of the source word is never redefined.

Example, "The heart of the city." The SemanticHub returns BiologicalOrgan, CentralRegion, and MetaphoricalCenter. The context `of the city` is incompatible with an organ of a city (SG-TYP-001), and the ContextIntegrator selects CentralRegion (a registered sense) [F1-C §5.2]:

```text
Referent R1: kind=ENTITY  instance_of=[CENTRAL_REGION]
RELATE(PART_OF family → LOCATED_IN_CENTER_OF, R1, R_city)
```

When no registered sense exists, a FIG candidate is produced and stays a candidate.

---

## 8.11 The model interface and how the model is used

### 8.11.1 Runtime-independent interface

[F3-C §8.2] The runtime is replaceable (Ollama first; llama.cpp for lower-level control).

```python
class SemanticModel(Protocol):
    def run(self, task: ModelTask) -> ModelResult: ...   # one method, typed tasks

ModelTask:
    task_type       SENSE_SELECT | FRAME_SELECT | ROLE_ASSIGN | COREF | SCOPE | MODAL_FLAVOR
                  | FULL_EXTRACT | PROPOSE_CONCEPT | COMPARE_DEFINITIONS | REVIEW
                  | COUNTEREXAMPLE | PARAPHRASE | FIGURATIVE_PROPOSE
    source_unit     text span + bounded context window   (data channel only, SG-SEC-001)
    grammar_view    only the frames/roles/rules relevant to this task (lazy-loaded)
    candidates      closed sets from retrieval (concepts, frames, senses, antecedents)
    output_schema   versioned schema id
    limits          max_tokens, timeout, sampling (deterministic default)
```

The central controller can later add runtimes. Both runtimes implement the same interface, and the rest of the architecture does not know which is in use [F3-C §8.2].

### 8.11.2 Prefer narrow tasks (Enhancement E-70, SG-INT-004)

A small model is reliable at selecting among a handful of predefined options and is weaker at open generation [F3-C §8.3, §8.4]. The interpreter therefore **decomposes** work into narrow, closed-set tasks when possible:

| Instead of | Prefer |
|---|---|
| "Analyze this sentence and produce semantics" (FULL_EXTRACT) | SENSE_SELECT for each ambiguous trigger → FRAME_SELECT → ROLE_ASSIGN only for roles the valence patterns left open → COREF for each pronoun → SCOPE/MODAL_FLAVOR for flagged operators |

FULL_EXTRACT stays available as a fallback and as one independent method for METHOD_DISAGREEMENT checks. Narrow tasks are cheaper, easier to validate (each output is a choice from a known set), and make fault localisation straightforward. Part 12 measures whether the decomposed path beats FULL_EXTRACT on the benchmark.

### 8.11.3 Closed-set choices

Every selection task includes the explicit choices `NONE_OF_THESE` and `NEEDS_NEW_CONCEPT` / `NEEDS_NEW_FRAME` (Part 5 §5.9). A model forced to choose among wrong candidates produces plausible wrong answers.

### 8.11.4 Output schema (illustrative)

The model's output is a *candidate*. It is never stored directly. The schema can be enforced by constrained decoding (JSON-schema outputs or a generation grammar), which controls *form* only [F3-C §8.2].

```json
{
  "task_type": "ROLE_ASSIGN",
  "unit_id": "S001.u1",
  "trigger": {"span": [16, 24], "chosen_sense": "examine.1"},
  "frame": {"id": "EXAMINATION", "version": 1, "perspective": null},
  "bindings": [
    {"role": "EXAMINED_ENTITY", "filler": "E1", "value_state": "SPECIFIED", "basis": "GRAMMATICAL",
     "span": [0, 11], "rule": "SG-INT-011"},
    {"role": "EXAMINER", "filler": "E2", "value_state": "SPECIFIED", "basis": "GRAMMATICAL",
     "span": [25, 38], "rule": "SG-INT-010"}
  ],
  "alternatives_considered": [],
  "unresolved": [],
  "outcome": "RESOLVED"
}
```

Note the difference from F1-A §3.8's first sketch: it uses IDs from retrieved sets, spans, rule citations, bases, and the value states. Natural-language labels such as `"agent": "doctor"` are not accepted.

### 8.11.5 Determinism, caching, sampling

(Enhancement E-76)

- Default sampling is deterministic (temperature 0, fixed seed, fixed prompt template, pinned model version). Runs are recorded in the certificate (Part 5 §5.8.2).
- **Result cache** keyed by `(task_type, normalized_input_hash, candidate_set_hash, grammar_view_hash, model_id, schema_version)`. A repeated input never makes a second model call. It is also the basis for novelty protection (Part 6 §6.12.4).
- For HIGH and VERY_HIGH risk classes, the controller may sample *k* alternative runs (different seeds, or a different model family) and use disagreement as a signal. Agreement between runs of the same model is not independent confirmation (Part 6 §6.5.3).
- Output is *validated, never trusted*, even when deterministic.

### 8.11.6 Model roles

[F3-C §8.3–8.4]

| Role | Used for | Size class [Provisional] | Where |
|---|---|---|---|
| A: Primary interpreter | Sense, frame, role, coreference, scope choices | Small (1–4B) to medium (7–9B) | Local |
| B: Reviewer | HIGH/VERY_HIGH review, counterexamples, generalization review | Larger (12–30B+) | Local or remote, subject to SEC-008 |
| C: Embedding model | Candidate retrieval | Dedicated small model | Local, separate process |

Sizes are experimental ranges. The model is chosen by benchmark on semantic accuracy, speed, resource use, and especially *correct recognition of uncertainty*. A confident wrong answer is worse than "unresolved" [F3-C §8.4]. One loaded copy is shared by all controllers (Part 10).

### 8.11.7 Call budgets

Per unit and per document the controller enforces limits (SG-SEC-006): model calls, candidate set size, retry count, context length, wall time. [Provisional: default 3 model calls per sentence, tuned by benchmark.] When a unit exhausts its budget it becomes UNRESOLVED or ALT. The system never keeps trying.

---

## 8.12 Reusing patterns to reduce model calls

[F1-A §3.11; F1-A §3.17] "John bought a car", "Mary bought a bicycle", "The company bought a building" share a construction. Once the system has resolved the first, later instances should not need the model.

### 8.12.1 ConstructionPattern

```text
ConstructionPattern
  pattern_id, version, status (CANDIDATE | ACTIVE | SUSPENDED | RETIRED)
  trigger            lexical sense (not merely a lemma)
  syntactic shape    ValencePattern + dependency-shape constraints
  argument classes   per role: class constraints (e.g. BUYER: Person|Organization; GOODS: PhysicalObject)
  frame mapping      frame@ver, perspective, parameter pins, role map
  operators handled  which operator cues the pattern also handles
  guards             conditions that force fallback (abstract GOODS, idiom neighbour, unusual modifiers,
                     negation/modal in unusual scope, parser flag ATTACHMENT_AMBIGUOUS)
  evidence           n_seen, n_audited, n_errors, wilson_upper_bound, last_audit
```

### 8.12.2 Rules (Enhancement E-72, SG-INT-005)

1. A pattern bypasses the model only if it is ACTIVE and **every guard passes**. Otherwise the unit goes to the normal path.
2. A pattern becomes ACTIVE through the same pipeline as other grammar-level changes (candidate → validation → audit → promotion, Part 9). It needs a minimum audited sample and an upper error bound below the tolerated rate for its risk class (Part 6 §6.10.3).
3. A syntactic match is **never** sufficient. The pattern is keyed on the *sense*, and its argument-class guards separate "bought a car" from "bought the argument" [F1-A §3.11]. Guard failure means fallback.
4. Audit sampling continues for ACTIVE patterns. A rising error bound moves a pattern to SUSPENDED, and the model path takes over. Patterns can return to the model path at any time, as scaffolding fades and returns in the coaching reference.
5. A pattern changes only the *means* of producing a candidate. The validator and certificate (replay-class) apply as usual.

This is the mechanism by which "the system could gradually replace some expensive AI interpretation tasks with reusable semantic patterns" [F1-A §3.11] without sacrificing accuracy. Cost declines for common constructions, and the model remains for the unfamiliar, the ambiguous, and the conflicting.

---

## 8.13 Bootstrapping: where the first knowledge comes from

### 8.13.1 The problem

[F1-A §3.10] Given an empty dictionary and "The heart pumps blood", nothing tells the system what a heart is or whether pumping differs from flowing. No deterministic mechanism discovers all meanings. The system needs an initial source of semantic information.

### 8.13.2 The four approaches and the decision

| Approach | Content | Advantage | Disadvantage |
|---|---|---|---|
| A: Manual core | Types, relations, ~20 frames, rules | Consistent, understandable | Knows little at first |
| B: Import resources | WordNet, FrameNet, VerbNet, PropBank, Wikidata, ConceptNet, AMR data | Large coverage, saves design effort | Different granularity, identifiers do not align |
| C: Model proposals | Concepts, roles, patterns from text | Scales | Duplicates, errors, drift, invented facts. Proposal, not ground truth. |
| D: Combined | A, then B, then C, then validation and merging | Balanced | Needs the full assurance machinery |

**Decision (Approach D, as the source recommends):**

```text
 MANUAL CORE (Foundation Package) → EXISTING RESOURCES (selected subsets)
        → LOCAL AI EXTRACTION → VALIDATION AND MERGING → EXPANDING DICTIONARY
```

Expansion is not correctness. The dictionary grows only as fast as benchmarks, consistency checks, and review show that it improves [F1-A §3.10].

### 8.13.3 Bootstrap phases

| Phase | Action | Output |
|---|---|---|
| B0 | Build and test the Foundation Package (Part 4 §4.12) | Kinds, roles, relations, FN, 20 kernel frames, rules, seed classes |
| B1 | Seed lexicon: a curated WordNet subset for kernel domains, flagged STRUCTURED with ExternalMappings | Lexical senses with candidate concepts |
| B2 | Align kernel frames with FrameNet frames. Use VerbNet for verb classes and valence patterns. Use PropBank to evaluate role extraction. Mappings are explicit and graded. | LexicalFrameLinks, ExternalMappings |
| B3 | Run the interpreter over benchmark and curated corpora to generate candidates | Candidates, certificates, validation reports |
| B4 | Resolve and promote under review. Unknown terms produce provisional concepts, never invented definitions. | Growth with measured quality |
| B5 | Enable budgeted expansion and pattern graduation | Controlled growth |

**FrameNet before custom frames.** "I would study FrameNet before attempting to create hundreds of custom frames" [F3-C §8.7.2]. FrameNet frames are not necessarily minimal universal primitives and are not designed for compression, so each is evaluated against USG's own frame rules before it is imported.

### 8.13.4 Resource roles and limits

[F1-A §3.10; F3-B §7.10; F3-C §8.7]

| Resource | Provides | Role in USG | Limitation |
|---|---|---|---|
| WordNet | Lexical senses, synonym sets, hypernym hierarchies | Lexical sense candidate retrieval; seed IS_A hints | Not a complete conceptual ontology. It does not model events or domain knowledge. |
| FrameNet | Frames and participant roles | Initial source of frame definitions and role structures | Coverage and design choices vary |
| VerbNet | Verb classes, syntactic-semantic patterns | Source of valence patterns and verb-class generalizations | Mostly verbs |
| PropBank | Predicate-argument annotation | Training and evaluating role extraction | Labels do not map automatically to USG roles. Explicit mapping rules are required. |
| AMR resources | Sentence-level graphs | Reference representation and evaluation | Parser output is not guaranteed to be correct. Not adopted as format. |
| Wikidata | Entities and structured statements | Individual resolution, ExternalMappings | Variable completeness |
| ConceptNet | Commonsense relations | Retrieval hints only | Noisy and over-general assertions. Never trusted knowledge. |

**None is a complete universal semantic grammar**, and their concepts and identifiers do not always align [F1-A §3.10], so the mapping layer is essential.

### 8.13.5 The Resource Alignment Engine

[F3-C §8.8]

```text
EXTERNAL RESOURCES → ALIGNMENT ENGINE → CONCEPT RESOLVER (Part 7) → UNIVERSAL SEMANTIC IR
```

For each external entry:
1. **Import record:** resource, version, license, entry ID, original structure.
2. **Candidate conversion** to a USG candidate (concept, lexical sense, frame, or valence pattern), entering at lifecycle stage STRUCTURED (never PROMOTED) (SG-SEC-010).
3. **Relation classification** with internal records: EXACT, BROADER_THAN, NARROWER_THAN, PARTIAL_OVERLAP, RELATED_DISTINCT, UNRESOLVED. Rule SG-IDN-004 applies (name or description similarity does not establish equivalence).
4. **Review** by risk class (Part 6 §6.10). Mapping a resource entry to an existing concept is an identity decision (Part 7).
5. **Provenance:** every imported item keeps its source mapping, so a faulty resource version can be traced and reprocessed.

**Import discipline.** Import selected, well-understood subsets before whole databases. Resources use different definitions and classification systems, and some have license constraints. A resource claim is a *source-attributed claim*, not trusted truth (Part 6).

---

## 8.14 Multilingual interpretation

### 8.14.1 Language-independent core

[F1-D §2.25; F2-A §3.1]

> English: *The doctor gave the patient medication.*
> Arabic: أعطى الطبيب المريض دواءً.

Both compile to `GIVE(AGENT/SOURCE: R_doctor, RECIPIENT: R_patient, THEME: R_medication)`. The analyzers and lexical entries differ. The frame and roles are shared. Likewise فحص الطبيب المريض ("the doctor examined the patient") and the English examination sentences map to `EXAMINATION(EXAMINER, EXAMINED_ENTITY)` [F2-A §3.1].

### 8.14.2 Per-language components

| Component | Per language |
|---|---|
| LinguisticParser, label map | Yes (§8.3.4) |
| Lexicon (LexicalEntry, LexicalSense) | Yes. Senses point to the same concept IDs. |
| Valence patterns | Per language and construction. Frame and role are shared. |
| Cue tables for operators (§8.8) | Yes |
| Calendar and time expressions | Yes |
| Concepts, frames, relations, rules of the Meaning plane | **No. Shared.** |

No semantic knowledge base needs duplicating per language [F1-D §2.25].

### 8.14.3 Preserving language-specific distinctions

Languages differ in tense, aspect, evidentiality, definiteness, and other distinctions, and not every expression has an exact equivalent [F1-D §2.25]. Part 2's boundary rule (SG-CON-004) decides where each feature lives: features that change truth conditions or commitments become operators, such as evidential markers (some languages mark evidentiality morphologically, for example Turkish evidential past). Features that only affect style, order, or form go into LanguageAnnotation.

### 8.14.4 Arabic: specific risks

The sources say to evaluate Arabic separately and not to assume that English parser performance transfers [F3-C §8.6]. Known interpretation issues, each to be measured in Part 12:

| Issue | Effect | Handling |
|---|---|---|
| Verb-initial order is common (VSO), though other orders occur | Role assignment cannot rely on SVO assumptions | Valence patterns in Arabic keyed to Arabic dependency structure |
| Case endings are often unwritten (no short vowels or tanwin in everyday text) | Subject and object can be unmarked, so role assignment can depend on order, agreement, and semantic plausibility | Treat unresolved subject/object as a retained ALT, with higher risk class |
| The verb carries person, number, and gender, and the subject may be dropped | An unexpressed subject is a referent derived from verb morphology | Referent with basis GRAMMATICAL. Not an UNSPEC hole when morphology identifies it. |
| Pronominal clitics attach to words | Tokenization splits them. Pronoun referents arise inside tokens. | Tokenization step with segmentation map to stored-text offsets |
| Root-and-pattern morphology | Lemma handling and sense retrieval are root-aware | Lexicon keyed on lemma and root with sense links |
| Optional diacritics | Same string, different words | Normalized view with offset map (Part 6 §6.13.4). Folding is declared per language. |
| Copula absent in present tense | Nominal sentences have no verb trigger | Nominal-sentence patterns map to property and state frames |

(Enhancement E-75.) The kernel's first language is English. Arabic is added as a second language only when its parser, lexicon, and benchmark exist and meet the same acceptance criteria. Multilingual behaviour is not claimed before it is measured.

---

## 8.15 Worked examples

### 8.15.1 "The young doctor gave the patient two tablets yesterday."

(The sentence of F1-A §3.13, document dated 2026-10-16.)

| Stage | Result |
|---|---|
| 0 | Source registered. Anchor 2026-10-16. Tier STANDARD. |
| 1–2 | Tokens: The, young, doctor, gave, the, patient, two, tablets, yesterday. Dependencies: *gave* ROOT; *doctor* SUBJECT with *young* as modifier; *patient* INDIRECT_OBJECT; *tablets* OBJECT with *two* as numeric modifier; *yesterday* temporal modifier. |
| P1 | Referents R1 (doctor, SINGULAR), R2 (patient, SINGULAR), R3 (tablets, PLURAL, cardinality 2). *young* gives PropertyAssertion PA1 on R1. |
| P2–P3 | Trigger *gave*. LexicalFrameLink candidates: GIVE (transfer), plus other senses of *give* (e.g., *give a speech*), which fail the arguments' class constraints. |
| P4 | ACTIVE_DITRANSITIVE: SUBJECT→AGENT (+SOURCE), INDIRECT_OBJECT→RECIPIENT, OBJECT→THEME. |
| P5 | TENSE(PAST, SPEECH_TIME). *yesterday* → `TIME_REL(YESTERDAY, anchor S1)`, resolved to 2026-10-15 by `RESOLVE_TIME`. |
| P8 | Candidate + certificate. |
| Concept resolver | Doctor 101, Patient 102, Tablet 103, Young 301 (Part 2 §2.16). All by exact lexical mapping (R1–R2). |
| Validator | L1–L4 pass. Nothing is stated about how the tablets were handed over, so no role is invented. L5: no ambiguity cue, so risk class LOW. |
| Outcome | RESOLVED. Output equals the Part 2 §2.16 record set. |

No model call is needed if a graduated GIVE pattern is ACTIVE. Otherwise the model is asked at most for SENSE_SELECT on *gave*.

### 8.15.2 "The boy wants to eat an apple."

```text
Referents: R1 boy (SINGULAR, introduced_in WORLD)
           R2 apple (SINGULAR, indefinite, introduced_in CONTENT_OF(WANT, CONTENT))   ← no world existence claim
P3  trigger "wants" → WANT (ATTITUDE).  trigger "eat" → EAT.
P6  xcomp "to eat" → CONTROL_XCOMP pattern with SUBJECT_CONTROL hint → EATER = R1 (GRAMMATICAL, SG-INT-006)
IR  HOLDS( WANT(EXPERIENCER: R1, CONTENT: EAT(EATER: R1, FOOD: R2)) )   tense PRESENT
```

This is the reentrant structure of F1-A §3.3. The boy participates in two situations. The EAT description is an unasserted SIT inside CONTENT. R2's existence is scoped inside the wish.

### 8.15.3 Active and passive give the same IR

| Sentence | Construction | Same bindings? |
|---|---|---|
| The doctor gave the patient medication. | ACTIVE_DITRANSITIVE | Yes |
| The patient was given medication by the doctor. | PASSIVE (recipient subject) | Yes (voice in annotation) |
| The patient was given medication. | PASSIVE_NO_AGENT | AGENT = UNSPEC |

The three pass the metamorphic checks of Part 5 §5.11: the first two are equivalent, and the third is a projection with no invented agent.

### 8.15.4 "The bank approved the loan." versus "The fisherman sat on the bank."

```text
SemanticHub: bank → [FINANCIAL_INSTITUTION, RIVER_BANK, STORAGE_FACILITY]
Sentence 1:  trigger "approved": frame APPROVE (AGENT must be Person|Organization).
             RIVER_BANK (a landform) is INCOMPATIBLE as AGENT → drops. FINANCIAL_INSTITUTION COMPATIBLE.
             "loan" cue supports it. → RESOLVED.
Sentence 2:  trigger "sat on": frame LOCATED/POSTURE with a LOCATION; cues fisherman. RIVER_BANK selected.
Without context ("The bank collapsed.") → ALT(financial failure | landform collapse), both valid.
```

Type constraints alone settle the first sentence without a model call. The second uses cues and a SENSE_SELECT choice.

---

## 8.16 The benchmark progression

[F1-A §3.16; F3-C §8.21] The interpreter is developed against ten stages of increasing difficulty, each with a gold IR.

| # | Sentence | Expected structure | Main challenge | Stages stressed |
|---|---|---|---|---|
| 1 | The car is red. | PropertyAssertion(car, COLOR, RED) | Entity–property | P1, P4 |
| 2 | The car moves. | MOVE(MOVER: car), path unspecified | Entity–action | P3 |
| 3 | The boy eats an apple. | EAT(EATER, FOOD) | Agent–patient | P3, P4 |
| 4 | John gave Mary a book. | GIVE(…) | Multiple roles | P4 |
| 5 | The door opened. | OPEN(UNDERGOER); no AGENT invented | State transition | Valence (inchoative) |
| 6 | The door did not open. | NOT(HOLDS(OPEN(…))) | Negation | P5 |
| 7 | John wants to leave. | WANT(EXPERIENCER: John, CONTENT: MOVE(MOVER: John, SOURCE: UNSPEC)) | Nested event, control | P6 |
| 8 | John may leave tomorrow. | MODAL(POSSIBILITY, flavor ALT) + TIME_REL(TOMORROW) | Possibility and time | P5, §8.9 |
| 9 | The patient was treated by the doctor. | TREAT(PRACTITIONER: doctor, TREATED_ENTITY: patient) | Passive | Valence patterns |
| 10 | He returned it because it was defective. (with preceding sentence supplying antecedents) | RETURN(…) + CAUSATION(EXPLANATORY_REASON) + PropertyAssertion(defective); *he*, *it* resolved via coreference. Without context: UNRESOLVED or ALT. | Context, reference, causation | P7, §8.7 |

Further categories from F3-C §8.21: ambiguity (telescope), metaphor (swallowed file), generalization (heart/pump), negative pairs (gave/offered), and the Part 5 §5.11.3 list. Part 12 defines the gold set and the scoring.

---

## 8.17 What the pipeline records for the two encoding modes

[F1-A §3.15]

| Mode | The pipeline records | Loses |
|---|---|---|
| **Semantic mode** | Validated IR, certificates (per retention tier), referents, alignment from IR elements to spans | Original wording, order, punctuation, lexical choice |
| **Reversible mode** | Everything above plus LanguageAnnotations for every token span (surface form, lexical choice, voice, definiteness, tense form, word order, whitespace and punctuation), or a retained copy of the stored text | Nothing, if the annotations or the text are retained |

Because the pipeline always records IR-to-span alignment, either mode can be built from the same stage outputs. The container design (annotations vs. a compressed stored text vs. a wording delta against a template realisation) belongs to Part 11 and must be *measured*. Reversible mode is not assumed to be smaller than conventional text compression [F1-A §3.15].

---

## 8.18 Capability-based planning and the controller

[F3-C §8.16, §8.26, §8.27]

### 8.18.1 Input classes and plans

The central controller does not run every module on every input. It classifies each unit by features and runs the modules the class needs.

| Class | Typical features | Plan |
|---|---|---|
| **P** Simple property | copula plus adjective or noun, no embedding | S1–S2 → lexicon → property frame → validate |
| **E** Simple event, known frame | single clause, lexical hit, clear arguments | S1–S2 → lexicon → valence → operators → (graduated pattern) → validate. Model only for open choices. |
| **C** Complex | embedding, negation or quantifier scope, modality, causation, coreference | + narrow model tasks, + reviewer for HIGH risk |
| **F** Figurative or cross-domain | literal type clash, similarity talk ("A heart functions like a pump") | + figurative path, + FN lookup, analogy engine, generalization validator (Part 9) |
| **N** New term | UNKNOWN_WORD | + full concept resolution, provisional path (Part 7) |

An input like "The car is red" does not need an analogy engine. An input like "A biological heart functions similarly to a mechanical pump" does: parser → concept resolver → functional ontology → analogy engine → generalization validator [F3-C §8.26].

### 8.18.2 The controller is deterministic

The controller decides from task type, available input, required capabilities, dependency rules, validation failures, resource availability, and budgets [F3-C §8.27]:

```text
IF  input class = P                          THEN lexicon, property frame, validate
IF  several word senses remain plausible     THEN activate the ContextIntegrator
IF  a proposed concept equivalence is open   THEN request semantic review
IF  budget exhausted                         THEN UNRESOLVED / DEFER
```

A model may help *classify* an unfamiliar task, but it has no authority to invoke expensive modules indefinitely.

### 8.18.3 Capability registry and parallelism

Each module declares capabilities (for example, `AnalogyEngine: StructuralComparison, FunctionalMapping, CandidateGeneralization`). The controller builds a task-specific plan from those declarations. Independent steps such as language analysis, lexical candidate retrieval, and related concept retrieval can run in parallel with `asyncio`. Final validation waits for them [F3-C §8.16]. `asyncio` does not parallelize CPU-bound Python, so graph-heavy work goes to worker processes (Part 10).

---

## 8.19 Failure modes and fallbacks

| Failure | Detected by | Response |
|---|---|---|
| Parser error | ATTACHMENT_AMBIGUOUS flag; METHOD_DISAGREEMENT; L4 mismatch | n-best, second method, ALT or UNRESOLVED |
| Unknown trigger | UNKNOWN_WORD | Part 7 §7.9 |
| No fitting frame | FRAME_GAP | UNRESOLVED; frame proposal path (Part 9) |
| Model invents content | VC-V01, VC-V06 (unsupported detail) | Repair loop, REJECT |
| Model picks a wrong candidate that satisfies the schema | L4/L5, method disagreement, audit sampling | Detected statistically (Part 6 §6.10.3) |
| Wrong sense under the model | L2 type errors; VC-C01 | Retry with context; review |
| Over-aggressive canonicalization | Negative pairs (Part 5 §5.11.3) | Rule fix via change control |
| Cross-sentence reference without context | Unresolved antecedent | ALT or UNRESOLVED with RETRY_WITH_CONTEXT |
| Resource exhaustion | Budgets | DEFER or UNRESOLVED |
| Hostile text | Tripwires (SEC-004), structural defenses | Quarantine; no promotion |

When an end-to-end case fails, the stage-isolated runs of Part 5 §5.11.4 locate the stage (language model, parser, frame definition, concept resolver, rule implementation, or validator) [F3-C §8.19].

---

## 8.20 Closing summary

**Closure of source items in this part**

| Source item | Closed in |
|---|---|
| How a computer can analyze meaning with existing techniques (F1-A intro) | §8.1–§8.9 |
| Hybrid semantic compiler, nine stages (F1-A §3.9) | §8.1 |
| Bootstrapping, Approaches A–D (F1-A §3.10) | §8.13 |
| Reducing AI calls through patterns (F1-A §3.11) | §8.12 |
| Word senses, context, frames (F1-A §3.4–3.6) | §8.5–§8.6 |
| Unknown words and kinds of learning (F1-A §3.12) | §8.5.5; Part 7 §7.9 |
| Prototype benchmark (F1-A §3.16) | §8.16 |
| Multilingual (F1-D §2.25) | §8.14 |
| Resources and alignment (F3-C §8.7–8.8) | §8.13.4–§8.13.5 |
| Model roles, interface, structured output (F3-C §8.2–8.4) | §8.11 |
| Capability-based module selection (F3-C §8.26–8.27) | §8.18 |

**Rules registered or refined in this part**

| Rule | Statement |
|---|---|
| SG-INT-003 | Parser output is evidence, not authority |
| SG-INT-004 | Prefer narrow, closed-set model tasks over open generation |
| SG-INT-005 | A pattern bypasses the model only if ACTIVE and all guards pass |
| SG-INT-006 | Control constructions: the unwritten subject co-refers with the controller named by the lexical hint |
| SG-INT-007 | A referent introduced in an embedding context carries that context |
| SG-INT-008 | No fitting frame yields FRAME_GAP, never a forced fit |
| SG-INT-009 | Ambiguity policy: select only with decisive evidence, otherwise retain ALT (§8.9.1) |
| SG-INT-010–012 | Voice and construction mapping through valence patterns (refined) |
| SG-INT-020–022, SG-INT-031, SG-INT-050–051 | Operator cue rules (§8.8) |

**Enhancements introduced in this part**

| ID | Issue | Resolution |
|---|---|---|
| E-69 | Parser output could be treated as ground truth | Parser as evidence tool, n-best, attachment flags (§8.3.3) |
| E-70 | Open-ended model extraction is hard to validate and unreliable on small models | Decompose into narrow closed-set tasks (§8.11.2) |
| E-71 | Referents inside attitudes or negations would wrongly commit to world existence | `introduced_in` context on referents (§8.7.2). Amends Part 2 §2.5. |
| E-72 | Pattern reuse could be fooled by syntactic similarity | Sense-keyed patterns with guards, audits, and automatic fallback (§8.12) |
| E-73 | Forcing the nearest frame destroys distinctions | FRAME_GAP (§8.6) |
| E-74 | Valence rules tied to one parser's labels | Abstract grammatical functions plus per-parser label maps (§8.3.4) |
| E-75 | Arabic could be assumed to behave like English | Specific risks and a measure-before-claiming policy (§8.14.4) |
| E-76 | Repeated and stochastic model calls waste resources and lose reproducibility | Deterministic sampling and a result cache (§8.11.5) |


---


# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 9 of 12: Learning, Generalization, and Grammar Evolution

This part specifies how the system gains knowledge and how its grammar grows. It is where several of your original goals meet: automatic dictionary expansion, discovery of reusable structures across domains, and controlled growth that avoids both duplicate concepts and runaway grammar [F3-B intro; F1-A §3.17].

One rule governs everything below, in the sources' words: **learning a candidate does not mean accepting it as knowledge** [F3-B §7.25]. Every new interpretation, concept, relationship, and grammar rule is a candidate whose authority depends on its evidence and validation status [F3-B §7.35]. Similarity found by a machine is not truth, and a pattern is not a law [F2-B §4.26].

---

## 9.1 Five kinds of learning

[F3-B §7.1; F1-A §3.12; F1-C §13]

| Kind | What is learned | Engine | Candidate produced | Typical risk class |
|---|---|---|---|---|
| A. Lexical | A word or phrase denotes an existing concept or evokes an existing frame | Lexical Learning Engine | LexicalSense mapping, LexicalFrameLink | LOW–MEDIUM |
| B. Concept | A new concept, or a specialization, generalization, or related concept | Concept Learning Engine | Provisional concept plus ConceptDefinition | HIGH |
| C. Knowledge | A new assertion or relation among *existing* concepts and frames | Knowledge Learning Engine | Assertion or RelationDefinition | MEDIUM (relation type: HIGH) |
| D. Grammar | A new frame, specialization, composition, canonicalization or interpretation rule, valence pattern, construction pattern, figurative mapping, analogy, or abstraction | Grammar Learning Engine | Frame, Rule, Pattern, Mapping, or Analogy candidate | HIGH–VERY_HIGH |
| E. Procedural | Which of the system's *own* procedures are reliable under which conditions | Learning Controller error analysis (§9.14) | Proposals to change rules, examples, models, or tests | Per target |

Kind D is the most significant and the most dangerous. "It is learning a new structure for representing meaning" [F3-B §7.1]. It matters most for generalization, and it carries the greatest risk of runaway growth [F1-C §13].

Kind E is not a fifth engine. It is analysis of the system's own processing history, and it is how kinds A–D improve over time [F3-B §7.19].

**What does a processed unit teach?** After a unit passes validation, a deterministic **Learning Classifier** checks it against the registry and records which kinds apply [F3-B §7.8; F1-D §2.22 Stage I]:

| Check | Result |
|---|---|
| Is every word already mapped, every concept and frame already registered, and the assertion already stored or derivable? | **Nothing to learn.** "If everything already exists, no grammar modification is necessary." |
| Unfamiliar word | Kind A, or kind B if no concept fits (Part 7 §7.9) |
| Assertion not yet stored | Kind C |
| `FRAME_GAP` recorded | Kind D demand signal (§9.7.5) |
| Recurring structure | Kind D pattern signal (§9.8) |

---

## 9.2 Engines, controller, and pipeline

### 9.2.1 Structure

[F3-B §7.2, §7.34]

```text
                          CENTRAL CONTROLLER
                                  │
                          LEARNING CONTROLLER
              schedules · budgets · dependencies · escalation · cycle reports
                                  │
      ┌───────────────┬───────────┴────────┬─────────────────┐
      ▼               ▼                    ▼                 ▼
 LEXICAL ENGINE  CONCEPT ENGINE   KNOWLEDGE ENGINE    GRAMMAR ENGINE
      │               │                    │                 │
      └───────────────┴─────────┬──────────┴─────────────────┘
                                ▼
                       CANDIDATE STORE (provisional)
                                ▼
                    VALIDATION · REVIEW (Parts 5, 6)
                                ▼
                       PROMOTION CONTROLLER ──► authoritative stores
```

**No engine writes authoritative records.** Each emits `CandidateRecord`s into the provisional store. They share the Semantic Grammar, the concept registry, and the validation services, and they may run concurrently when their inputs are independent (P-20).

### 9.2.2 Learning Controller responsibilities

[F3-B §7.30]

| Responsibility | Mechanism |
|---|---|
| Task distribution | Assign engine tasks from the classifier output |
| Resource management | Cap concurrent model calls, memory, and graph work (Part 10) |
| Dependency management | A dependent task waits until its prerequisites exist (a frame candidate needs its concepts) |
| Retry control | Bounded retries per candidate (Part 5 §5.7) |
| Review escalation | Route by risk class (Part 6 §6.10) |
| Commit coordination | Hand approved bundles to the Promotion Controller. It never commits itself. |
| Progress tracking | Maintain the ingest ledger (§9.15.3) |

The central controller is predominantly deterministic and orchestrates specialized services. It does not interpret sentences itself [F3-B §7.30; F3-C §8.27].

### 9.2.3 Pipeline

The F3-B §7.8 pipeline is the Part 8 interpretation pipeline plus the stages after canonical IR:

```text
 CANONICAL IR (validated, Part 5) → LEARNING CLASSIFIER → candidates by kind
   ├─ LEXICAL UPDATE ──┐
   ├─ FACT PROPOSAL ───┼──► VALIDATE → REVIEW (by risk) → CORROBORATE → CONTROLLED PROMOTION → MEMORY
   └─ GRAMMAR PROPOSAL ┘
```

The pipeline can return to earlier stages when validation fails, but it MUST NOT retry indefinitely. The central controller enforces retry limits and budgets. If a case cannot be resolved reliably it is preserved as unresolved [F3-B §7.8].

---

## 9.3 Candidates, promotion, and rollback

### 9.3.1 The candidate envelope

```text
CandidateRecord
  candidate_id, candidate_type
  payload_ref                       the proposed record(s) in the provisional store
  proposer                          engine, method (RULE | MODEL | IMPORT | HUMAN | MINING)
  origin_sources[]                  with the independent-origin set computed (Part 6 §6.5.3)
  certificate_id, validation_report_id, evidence_vector_ref
  risk_class                        static and empirical (Part 6 §6.10)
  lifecycle_stage                   axis C
  dependencies[]                    other candidates this one needs
  bundle_id                         optional (§9.3.4)
  cycle_id                          the learning cycle (§9.15.2)
  veto_signature                    structural signature checked against REJECTED_PATTERN records
  created_at, expires_at
```

### 9.3.2 Candidate types, evidence, and approval

The F3-B §7.25 lifecycle is not uniform. "An exact known lexical mapping may be resolved directly. A proposed universal inference rule should require extensive testing" [F3-B §7.25]. This table fixes the difference.

| Candidate type | Minimum evidence before promotion | Risk | Rule authority level (Part 5) |
|---|---|---|---|
| Lexical mapping from a vetted resource, EXACT alignment | Formal validity, alignment grade, audit sampling | LOW | 3 |
| Lexical mapping learned from text | Formal validity, independent-origin support, review | MEDIUM | 3 |
| New concept, specialization | Definition constraints with evidence, duplicate search (Part 7), review | HIGH | 3 |
| Generalization concept | As above, plus counterexample search | HIGH–VERY_HIGH | 2–3 |
| Source-derived assertion | Formal validity, span support (E2). Promotion to trusted view needs an evidence policy (Part 6 §6.6). | MEDIUM | 3 |
| New relation type | Need shown across several frames or concepts (§9.6.3), review | HIGH | 2 |
| Domain frame (layer 3) | Frame tests (SG-FRM-008), duplicate and overlap comparison, review | HIGH | 3 |
| Universal or functional frame (layer 1–2) | Tests, cross-domain testing, counterexamples, benchmark non-regression, human review | VERY_HIGH | 2 |
| Valence pattern, lexical frame link | Tests, benchmark non-regression, audit | MEDIUM | 2 |
| Construction pattern activation | Audited sample, error upper bound (Part 8 §8.12) | MEDIUM | 2 |
| Canonicalization or interpretation rule | Positive and negative pairs, full regression, held-out evaluation | HIGH | 2 |
| FigurativeMapping, StructuralAnalogy | Relation-by-relation check, differences recorded, review | MEDIUM–HIGH | 3 |
| EquivalenceMapping | Part 7 | VERY_HIGH | 3 |
| Foundational rule | **Not a candidate type. Out-of-band release only** (SG-FND-005). | n/a | 1 |

### 9.3.3 Lifecycle

[F3-B §7.25; Part 1 axis C]

```text
DISCOVERED → STRUCTURED → VALIDATED_FORMALLY → REVIEWED_SEMANTICALLY → CORROBORATED → PROMOTED
                        ↘ REJECTED (with codes)   ↘ DEFERRED (budget, missing context)   ↘ DEPRECATED
```

| Stage | Meaning | Entered by |
|---|---|---|
| DISCOVERED | An engine proposed it | Engine |
| STRUCTURED | It conforms to the candidate schema and is in the provisional store | Candidate store |
| VALIDATED_FORMALLY | All deterministic checks passed (Part 5) | Validator |
| REVIEWED_SEMANTICALLY | Review per risk class concluded (Part 6 §6.11) | Reviewer (model or human) |
| CORROBORATED | Independent origins or an independent method support it (Part 6 §6.4.2, E3) | Evaluation process |
| PROMOTED | Authorized change to the authoritative store | **Promotion Controller only** |

Required stages by risk class (consistent with Part 6 §6.10.2):

| Class | Required |
|---|---|
| LOW | STRUCTURED → VALIDATED_FORMALLY → PROMOTED, with audit sampling |
| MEDIUM | + REVIEWED or CORROBORATED |
| HIGH | + REVIEWED and (where applicable) CORROBORATED |
| VERY_HIGH | All stages, plus a counterexample search, plus human or gold-benchmark approval, plus canary activation (§9.15.2). Never automatic. |

**SG-LRN-002 (Normative).** An engine MUST NOT set a candidate's stage beyond STRUCTURED. Stage changes are made only by the component that owns that stage. This restates P-13 and SG-FND-004 at the stage level.

### 9.3.4 Promotion bundles and dependency taint (Enhancement E-81)

A single idea often needs several records: a new concept, its lexical senses, a frame, its valence patterns, and its tests. Promoting them piecemeal can leave a trusted record pointing at an unpromoted one.

**SG-LRN-006 (Normative).**
1. **Atomic bundles.** Dependent candidates are promoted together in dependency order, or not at all. A bundle commit is one transaction.
2. **Dependency taint.** A record that depends on a candidate frame, concept, pattern, or mapping stays PROVISIONAL, even if its own validation passed. This generalizes invariant I-07 beyond concepts. Taint is lifted only when the dependency is promoted.
3. **Rollback plan.** Every HIGH and VERY_HIGH promotion carries a rollback plan: the list of affected records and the prior active versions.

### 9.3.5 Promotion Controller

[F3-B §7.34; F1-D §2.6]

Its checks, all required:
1. The validation report is current and was produced by a component other than the proposer (SG-FND-004).
2. Review requirements for the class are satisfied and recorded.
3. The candidate's veto signature does not match a `REJECTED_PATTERN` (Part 6 §6.12.3).
4. The evidence policy is met where one applies (Part 6 §6.6).
5. Budget and growth limits allow it (§9.11).
6. No trusted record would reference a provisional record.
7. The grammar or ontology version bump is computed (Part 2 §2.13).

A promotion writes a `PromotionRecord` (candidate, approver components, policy IDs, versions, bundle) and appends to the audit log.

**Rollback.** Promotion is reversible by *deprecation*, never deletion (SG-FND-006). Rolling back frame version n+1 re-activates version n. Records created under n+1 are marked for reprocessing (§9.15). Mapping rollback is the Part 7 revoke operation.

---

## 9.4 Lexical learning

The Lexical Learning Engine discovers word-to-concept and word-to-frame mappings [F3-B §7.2].

| Source of lexical knowledge | Handling |
|---|---|
| Vetted resource subset (WordNet, VerbNet) | Imported as STRUCTURED with ExternalMapping grade (Part 8 §8.13). EXACT alignments to existing concepts with complete definitions are LOW risk. |
| New surface form met in text for a known concept ("automobile" → CAR) | Candidate LexicalSense. Validated through Part 7 §7.9. Only a lexical mapping is added. No concept is created [F1-A §3.12]. |
| New sense of a known word ("heart of the city") | Candidate sense linked to an existing concept or a new one, with context cues and a registered figurative sense |
| New valence pattern for a known verb | Candidate LexicalFrameLink pattern with tests |
| Sense merge or split in a resource | Treated as a version change (Part 7 §7.11), not an edit |

Safeguards:
- A learned mapping from a QUARANTINE source needs corroboration by independent origins (SG-SEC-003, SG-SEC-007).
- Cues learned from co-occurrence are ASSOCIATIVE hints with a recorded scoring model (SG-KNW-002). They never decide a sense.
- A new mapping is checked against ambiguity: if it makes a previously unambiguous form ambiguous, existing patterns that used the form are re-audited (§9.14).

---

## 9.5 Concept learning

Part 7 specifies identity, comparison, provisional concepts, and registration. The Concept Learning Engine's remaining responsibilities:

1. **Propose definitions as structured constraints**, each constraint tagged with its provenance (§9.6.4), never as prose alone (Part 7 §7.9.3).
2. **Search before create** (SG-IDN-001, SG-LRN-001). Every proposal runs Part 7 R1–R7 first.
3. **Create provisional concepts** for terms that cannot yet be defined. The system keeps analyzing, and only *provisional* records may use them.
4. **Resolve provisional concepts** when evidence arrives: link, define, specialize, keep unresolved, or reject (Part 7 §7.9.2).
5. **Never edit a defining constraint** of a promoted concept. A change goes through SG-GOV-001 (Part 7 §7.11).

The learning objective is not to maximize the number of concepts. Part 7 §7.17 states the corollary: reduction in IDs is not a goal, and a wrong merge is worse than a duplicate.

---

## 9.6 Knowledge learning

The Knowledge Learning Engine extracts assertions and relationships using *existing* concepts and frames [F3-B §7.1 Process C].

### 9.6.1 Checks on a proposed assertion

[F3-B §7.12]

| Check | Question | Verified by |
|---|---|---|
| Structural | Does the relation permit this domain and range (an instrument and a measurable property)? | Validator L1–L2 |
| Identity | Do all referenced concept IDs exist, and are they the intended senses? | Part 7 |
| Evidence | Does the source support the assertion (span, basis)? | Validator L4 |
| Knowledge | Is it already stored or derivable (for example by the subclass rule)? | Reasoner |
| Provenance | Which source, extraction method, commitment holder, and context? | Part 6 |

If the structure is valid and span-supported, it is stored as a **source-derived assertion** (SOURCE_ASSERTED, E2). Promotion into the trusted view is a separate step governed by an evidence policy (Part 6 §6.6). A document cannot change the authoritative ontology by being processed [F3-B §7.12].

### 9.6.2 Derivable assertions are not stored again

If the assertion follows from stored facts by a registered rule (`CAR IS_A ARTIFACT` from `CAR IS_A VEHICLE` and `VEHICLE IS_A ARTIFACT`), the engine records nothing and notes only a possible cache request (Part 11, inference materialization).

### 9.6.3 New relation types (Enhancement E-85, SG-LRN-003)

New relation types are the cheapest way to cause "thousands of near-duplicate relations" [F1-A §3.12].

**SG-LRN-003 (Normative).** The system is conservative about adding fundamental relation types:
1. A relation type may be proposed only when the candidate assertion **cannot be represented** by an existing relation, a frame, or a PropertyAssertion. The engine records which of these were tried.
2. The need must appear in at least *k* distinct frames or concept pairs from independent origins [Provisional: k = 3], the same minimum-count discipline as patterns (SG-GEN-009).
3. It is compared with existing relation definitions for logical-property compatibility and for sub-relation or inverse status.
4. A growth cap applies per release (§9.11). Risk class HIGH, authority level 2.

### 9.6.4 Constraint provenance classes (Enhancement E-86)

The coaching reference separates limits that are genuinely fixed from limits that are merely assumed [F1-B §9: *Assumed vs. Real Constraint*]. The same distinction protects the ontology from a model's habits.

**SG-KNW-006 (Normative).** Every constraint on a concept, role, or frame carries a provenance class:

| Class | Meaning | Effect in validation |
|---|---|---|
| DEFINITIONAL | Follows from the concept's declared definition in its scope (an authoritative definitional source or curated release) | May produce INCOMPATIBLE (SG-TYP-001) |
| EMPIRICAL | Established by evidence about instances (corroborated) | May produce INCOMPATIBLE only if marked ESSENTIAL by review. Otherwise TYPICAL. |
| ASSUMED | Supplied by a model or by commonsense without evidence | **Never produces INCOMPATIBLE.** At most UNDETERMINED plus a warning. It cannot be inherited as exceptionless (SG-KNW-004). |

Model-proposed constraints default to ASSUMED. They are upgraded only by evidence and review. This keeps a model's habits ("a pump is mechanical") from becoming hard rules that reject a legitimate sentence about a biological pump.

---

## 9.7 Grammar learning

### 9.7.1 Five stages

[F3-B §7.14]

| Stage | Action | Nature |
|---|---|---|
| 1. Pattern collection | Collect validated structures (E2 or above, counted once per independent origin) | Deterministic |
| 2. Structural clustering | Group structures with compatible role patterns and relation types (signatures, §9.8) | Deterministic |
| 3. Candidate abstraction | Extract the shared structure as a proposed frame, specialization, composition, or functional assertion | Deterministic, with model help for naming and coherence |
| 4. Validation | Type compatibility, counterexamples, discriminative value, duplicate check, information preservation (§9.9) | Deterministic, model-assisted review |
| 5. Promotion | A versioned frame or rule added through the Promotion Controller | Governed |

Much of this "can operate independently of the local language model". The model is useful chiefly for judging whether a proposed abstraction has a coherent semantic interpretation [F3-B §7.14].

### 9.7.2 The growth ladder

[F3-B §7.15] Not every unfamiliar sentence deserves new grammar.

| Rung | What it is | Cost to the grammar |
|---|---|---|
| 1. New instance | A new application of an existing frame | None |
| 2. New specialization | A frame with meaningful additional constraints, or pinned parameters | Small |
| 3. New composition | A combination of existing frames (§Part 4 §4.6) | Small |
| 4. New fundamental frame | A semantic structure that cannot be adequately represented through existing components | Large. Strongest justification. |

**SG-LRN-004 (Normative).** Prefer valid composition of existing structures over introducing new fundamental frames. The proposer MUST show it tried rungs 1–3. This preference MUST NOT force unrelated meanings into inappropriate frames. **Semantic accuracy takes priority over minimizing the number of frame definitions** [F3-B §7.15].

### 9.7.3 Worked example: LEASE

[F3-B §7.13] "The company leased equipment to the contractor."

The Concept Learning Engine finds Company, Equipment, Contractor, and an unfamiliar sense of *lease*. The general TRANSFER frame does not capture leasing: contractual rights and obligations, a defined period, no ownership transfer.

Comparison with existing frames:

| Frame | Ownership changes? | Payment? | Defined period? | Contractual? | Verdict vs lease |
|---|---|---|---|---|---|
| GIVE | No (possession) | No | No | No | Different |
| LEND | No | No | Often | No | Differs on payment |
| RENT | No | Yes | Often | Often | **Overlaps. Possibly the same in everyday scope.** |
| LICENSE | No | Often | Often | Yes | Differs: rights, not physical custody |
| OWNERSHIP_TRANSFER | Yes | Varies | No | Often | Different |

Resolution through the growth ladder:

```text
Rung 2/3 candidate:
  LEASE = COMPOSE( TRANSFER[DIMENSION=POSSESSION, TIME-bounded]  ⟂  CONTRACTUAL_OBLIGATION(payment) )
  roles: LESSOR ⊑ AGENT (SOURCE), LESSEE ⊑ RECIPIENT, ASSET ⊑ THEME, LEASE_PERIOD ⊑ TIME
  parents: TRANSFER (SPECIALIZES), plus the concepts CONTRACTUAL_ARRANGEMENT, TEMPORARY_USE_RIGHT
  open question: LEASE vs RENT → a Part 7 equivalence question, not decided here
```

Risk class HIGH (new frame in a legal domain). A larger-model review and a domain reviewer are needed. The ultimate frame is formalized into machine-checkable roles and constraints [F3-B §7.13]. Until promotion, instances use the candidate frame only in provisional records (SG-LRN-006).

### 9.7.4 Worked example: INGESTION (self-extension)

[F1-A §3.17] The database shows `Human eats food`, `Dog eats food`, `Cat eats food`, `Bird eats food` and the same with *drinks water*. The optimizer proposes:

```text
INGESTION_FRAME (abstract)  roles: AGENT (Organism), INGESTED_SUBSTANCE
     ├─ EAT    (INGESTED_SUBSTANCE: solid/EdibleEntity)
     └─ DRINK  (INGESTED_SUBSTANCE: liquid)
```

It answers the five questions F1-A §3.17 asks:

| Question | Answer in this case |
|---|---|
| Does it correctly describe its members? | Yes for eat and drink |
| Does it introduce ambiguity? | Possibly: does inhaling or absorbing through skin count? The scope must be stated. |
| How many existing structures can reuse it? | Two frames, many instances |
| How much storage does it save? | Little. Two frames save almost nothing (Part 11 template-worth test). |
| Does it increase decoding complexity? | One inheritance hop |

The semantic decision (is it a valid abstraction?) and the storage decision (does it save space?) are separate (§9.10). Here the first may be yes and the second no, and the frame can still be kept for reasoning and retrieval [F2-B §4.18].

### 9.7.5 Demand-driven grammar learning (Enhancement E-84)

**SG-LRN-005 (Normative).** New grammar is proposed in response to *accumulated demand*, not a single sentence. `FRAME_GAP` records (Part 8 §8.6) are aggregated by structural signature. A frame proposal is generated only when the gap recurs across a minimum number of independent origins [Provisional: 3], consistent with SG-GEN-009. One unfamiliar construction produces a `FRAME_GAP` record and an UNRESOLVED unit. It does not produce a frame.

If the system processes a million sentences and creates a frame for every unfamiliar construction, the grammar becomes enormous and the reusable generalization you wanted is lost [F3-B §7.15].

---

## 9.8 Pattern discovery

### 9.8.1 Why selective

[F2-B §4.13] A million structures give n(n−1)/2 ≈ 5×10¹¹ pairs. Even cheap comparisons are impractical on a personal computer. The system therefore uses structural signatures to compare only promising candidates, which mirrors the brain-inspired selective activation of P-16 [F2-B §4.13].

### 9.8.2 Procedure

[F3-C §8.15 seven steps; F2-B §4.13 five steps; F1-B §10 diagram]

```text
 SEMANTIC DATABASE (validated structures only)
   → 1 NORMALIZE      canonical form (Part 3 §3.17)
   → 2 SIGNATURES     levels 1–4 (Part 4 §4.10.3)
   → 3 COUNT          occurrences per signature, per INDEPENDENT origin (§9.8.3)
   → 4 GROUP          bucket by signature (levels 1–3)
   → 5 MATCH          typed graph matching inside buckets (§9.8.4)
   → 6 PROPOSE        common structure → candidate abstraction
   → 7 VALIDATE       §9.9
   → 8 EVALUATE STORAGE   (separate decision; Part 11)
   → REVIEW → PROMOTION CONTROLLER
```

Two similarity families feed the same funnel [F1-B §10]: **structural similarity** (same arrangement of roles and relations) and **functional similarity** (same FN functions, Part 4 §4.8). A repeated graph structure can be a real semantic regularity or a coincidence, so the engine proposes candidates and does not announce truths [F1-B §10].

**Complexity with bucketing (illustrative).** One million structures in buckets averaging 100 gives 10,000 buckets × 4,950 pairs ≈ 4.95×10⁷ comparisons. That is about four orders of magnitude fewer than all pairs. If a bucket is larger than a cap, the engine samples it and records the sampling rate. Selective loading of subgraphs applies (Part 10).

### 9.8.3 Counting occurrences (Enhancement E-79)

Frequency drives candidates, and frequency is easy to inflate. The count for a signature is the **number of independent origins** that contain it, computed on the dependence graph (Part 6 §6.5.3). Ten reposts, ten sentences from one document, or ten extractions of one text count as **one**. Counts also exclude records that are INFERRED or derived (they add no observation) and records from QUARANTINE sources.

**SG-GEN-009 (Normative).** A recurring structure becomes a candidate pattern only after at least *N* independent occurrences [Provisional: N = 3, per Part 6 §6.12.2]. A reviewer's `REJECTED_PATTERN` suppresses re-proposal of that signature unless new evidence exceeds a materially higher threshold (Part 6 §6.12.3).

### 9.8.4 Typed graph matching (Enhancement E-80)

Subgraph matching is NP-complete in general, so the engine bounds it and uses types for pruning [F2-B §4.12: "generic graph matching can be computationally expensive" and "graph similarity does not guarantee semantic equivalence"].

```text
TYPED_MATCH(S_a, S_b):                       # bounded structures: ≤ max_nodes each [Provisional: 12]
  1  Prefilter     signature level ≥ 2 compatible (node-kind multiset, relation-type multiset)
  2  Role-first    align tier-1 parent roles (AGENT↔AGENT, ...) and FN function roles first
  3  Node pairing  (a,b) allowed only if kind(a)=kind(b) and a, b share a NON-ROOT common ancestor
                   within depth d, OR share an FN function; never via ENTITY alone
  4  Search        backtracking with pruning, capped at max_steps
  5  Score         SC = |preserved relations| / |relations in the smaller structure|    (ordinal, not probability)
  6  Output        up to k maximal mappings (ties kept), with unmapped nodes/edges as differences
```

The common-ancestor rule in step 3 is what stops Heart and Pump from matching through the root ENTITY class. Both anchor through the function FN.TRANSPORT / DRIVE_FLUID_FLOW instead.

The first prototype uses NetworkX on retrieved, bounded subgraphs only. It does not load the Semantic Dictionary into one graph [F3-C §8.14]. Frequent-subgraph mining and dedicated graph libraries are options only after measurement shows a need.

### 9.8.5 The cross-domain task, end to end

[F2-B §4.22] Task: "find reusable structures shared by biological and mechanical circulation systems."

| Actor | Action |
|---|---|
| Central controller | Creates the task in the Cognitive Workspace (domains, target) and sets budgets |
| Knowledge controller | Retrieves bounded subgraphs for the two domains |
| Pattern Discovery Engine | Computes signatures, buckets, counts |
| Analogy Engine | Proposes `StructuralAnalogy` mappings (§9.12) |
| Generalization Engine | Builds candidate abstractions |
| Validator | Checks types and constraints |
| Counterexample Engine | Searches for violations (§9.9.3) |
| Grammar Promotion Controller | Decides, under budget and policy |

Communication is by task messages with workspace version stamps, never by unrestricted shared writes (P-20; Part 10).

---

## 9.9 Validating a candidate generalization

### 9.9.1 Four kinds of generalization

[F2-B §4.1] Each type is validated differently.

| Type | Candidate looks like | Main risk |
|---|---|---|
| Taxonomic | New parent concept, IS_A links | Property inherited that is not true of every member |
| Functional | HAS_FUNCTION / FN link | Taken to imply category membership (SG-FRM-005) |
| Structural | Frame, analogy, template | Surface similarity mistaken for shared structure |
| Procedural | StateChange / composition / operation frames | Over-broad "input → process → output" |

### 9.9.2 Claim classification (Enhancement: SG-GEN-010)

[F2-B §4.15] A generalization asserts something, and what it asserts has a strength. Every candidate is classified **before** validation, because the tests differ.

| Claim class | Representation | Evidence needed |
|---|---|---|
| Universal | `Q(FORALL…)` or an ESSENTIAL constraint | Definitional provenance, or exhaustive verification. Almost never from observation alone. |
| Statistical | A quantified tendency with distribution evidence (MANY, MOST, with data) | Counts, sampling description |
| Typical | `TYPICALLY_HAS` (defeasible) | Corroborated examples, exceptions acknowledged |
| Context-dependent | Conditional on scope | Condition stated, evidence per context |
| Co-occurrence | ASSOCIATED_WITH, weighted | Retrieval use only. Never a claim about the world. |

**SG-GEN-002 (restated).** A universal generalization is not promoted solely because a property occurs in several observed examples. `DOG HAS_FOUR_LEGS`, `CAT HAS_FOUR_LEGS` therefore does not yield `ANIMAL HAS_FOUR_LEGS`. Counterexamples (snakes, birds, many aquatic animals) refute it. It may become `MANY TERRESTRIAL MAMMALS TYPICALLY_HAVE FOUR_LIMBS`, and even that needs careful definition and evidence [F2-B §4.15].

### 9.9.3 The counterexample engine

[F2-B §4.15–§4.16; F3-B §7.23; F1-B §9 Inversion]

The coaching reference's *Inversion* lens asks "under what conditions would this fail?" [F2-B §4.16]. The engine turns that into four methods:

| Method | What it does | Nature |
|---|---|---|
| CE1 Knowledge scan | Query the **trusted view** for members of the class that violate the claim | Deterministic |
| CE2 Corpus scan | Query source-asserted records for contrary evidence | Deterministic. Lower weight. |
| CE3 Systematic inversion | Generate near-misses mechanically. For "every X with property P is a C", list concepts with P that are not subclasses of C. For "every C has P", list sibling classes of C and test them. | Deterministic over the graph |
| CE4 Model proposals | A reviewer model proposes counterexamples | Proposals only |

Inversion by query: for the candidate "everything that moves fluid is a pump", CE3 computes `{x : HAS_FUNCTION(x, MOVE_FLUID)} \ SUBCLASS_OF*(PUMP)` and returns pipe, river, vessel, and gravity-driven channel [F2-B §4.16].

**SG-GEN-005 (Normative, Enhancement E-77).** Counterexamples have three states, with different effects:

| State | Meaning | Effect |
|---|---|---|
| VERIFIED | Confirmed against trusted knowledge or authoritative evidence | Rejects a universal claim. Triggers refinement (below). |
| UNVERIFIED | A model or weak source proposes it and nothing confirms it | **Holds** the candidate for review and raises risk. It does not reject. |
| NONE_FOUND | The searches ran and found nothing | **Not a proof.** The report states the coverage: methods run, classes tested, records scanned. A universal still needs approval under SG-GEN-002. |

A counterexample proposed by a model is never accepted automatically [F2-B §4.16]. Discovering all counterexamples cannot be guaranteed [F2-C §5.25], so coverage is always reported.

**Distinction mining (Enhancement E-77).** A verified counterexample does more than reject. "Counterexamples do not merely reject bad rules. They can help identify the distinctions needed to improve the grammar" [F3-B §7.23]. The engine compares the members that satisfy the claim with those that do not and proposes one of:

| Refinement | Example |
|---|---|
| Narrow the scope | `ANIMAL` → `TERRESTRIAL MAMMAL` |
| Downgrade the claim class | Universal → TYPICAL |
| Split or parameterize a frame | "Every transfer changes ownership" fails for lending and custody → add the TRANSFER `DIMENSION` parameter (Part 4 §4.12). The correct abstraction separates physical, possession, and ownership transfer as related but separate frames [F3-B §7.23]. |
| Reject outright | No coherent refinement |

### 9.9.4 The gates

[F2-B §4.17, §4.18; F1-D §2.18] A candidate abstraction G passes all of these. They are **gates**, not terms to be traded off.

| Gate | Test | Failure result |
|---|---|---|
| **G1 Structural correspondence** | Role-preserving mappings exist between G and ≥ k member structures (TYPED_MATCH) | Reject |
| **G2 Semantic compatibility** | No member binding is INCOMPATIBLE with G's role constraints. The actor category accommodates biological and manufactured systems without merging their identities. UNDETERMINED sends the candidate to review. | Reject or review |
| **G3 No unsupported claims** | Every claim G makes holds for every member (or is declared TYPICAL, with exceptions listed). G makes no claim about properties the members do not share (SG-GEN-001). | Reject |
| **G4 Counterexample test** | Per SG-GEN-005 | Reject, hold, or refine |
| **G5 Discriminative value** | Coverage and reuse thresholds (§9.9.5) | Reject as too general or too narrow |
| **G6 No duplicate** | Not already represented by an existing frame, abstraction, or equivalent definition (Part 7 comparison applied to frames, plus content-hash check) | Reuse instead |
| **G7 Review** | Per risk class (Part 6 §6.10) | Hold |
| **G8 Information preservation** | The specific records remain stored with their specific IDs, and the abstraction is *additive* (SG-GEN-008) | Reject |

**SG-GEN-008 (Normative).** An abstraction does not replace the specific structures it generalizes. "The objective is not to eliminate specific semantic structures. It is to share their common information through a more general definition" [F1-D §2.18]. A generalized frame `CAUSE_FLUID_MOVEMENT` can exist while `PUMP_FLUID`, `MOVE_AIR`, and `CIRCULATE_BLOOD` remain. Pumping and blowing involve different mechanisms, and the specifics keep their own IDs [F1-D §2.18].

### 9.9.5 Discriminative value (Enhancement E-78, SG-GEN-004)

An abstraction that applies to nearly everything says nothing. "Nearly every process could be described in terms of inputs and outputs if we define those terms loosely enough" [F2-B §4.20]. Part 4 §4.8.5 flagged Input → Process → Output for exactly this reason. The measure:

```text
coverage c(G)  = |structures in a domain-balanced reference sample that match G and pass G1–G2|
                 / |reference sample|
reuse    n(G)  = number of INDEPENDENT-ORIGIN structures that validly instantiate G
```

**SG-GEN-004 (Normative).** A candidate passes G5 only if `n(G) ≥ m` (too specific otherwise) **and** `c(G) ≤ c_max` (too general otherwise). [Provisional: m = 3 and c_max = 0.25, to be calibrated on the benchmark.] A candidate near either bound is a review item, not an automatic reject. This is the generality-versus-specificity balance of F2-B §4.20, now measurable.

### 9.9.6 Scoring survivors, and why scoring is split (Enhancement E-12, completed)

The source scores candidates with `Q(G) = αR(G) + βC(G) − γE(G) − δK(G)` and adds that promotion also needs "required semantic correctness thresholds" [F2-B §4.17]. A weighted sum lets a high reuse or compression score offset a semantic error. Two changes:

1. **Gates first.** Semantic error is not a term. It is G1–G4. A candidate that fails a gate has no score (SG-GEN-006).
2. **Two scores, per P-15.** Semantic usefulness and storage benefit are separate decisions with separate criteria [F2-B §4.18; F3-A §6.14]:

```text
Q_sem(G)   = α·R̂(G) + ε·DV(G) − δ·K̂(G)   − ρ·r(G)       ranks survivors for REVIEW PRIORITY only
Q_store(G) = net bytes saved under the Part 11 template-worth test   (evaluated by the Compression Optimizer)
```

- R̂, K̂ are normalized to [0,1] over the current candidate batch.
- `DV(G) = 1 − c(G)`.
- `K(G)` counts new roles, constraints, exceptions, and dependencies [F2-B §4.17].
- `r(G)` is the residual-risk term: the Wilson upper bound of the counterexample rate observed in the search (as in Part 6 §6.10.3). It breaks ties but never replaces gate G4.
- Equal weights by default [Provisional]. Weights are changed only on benchmark evidence (Enhancement E-23 discipline).
- Neither score is a probability or a truth value.

**Semantic promotion depends on gates G1–G8 and review. It does not depend on Q_store.** A semantically useful abstraction may be kept even if it saves no space, and a compression-friendly pattern is not thereby a meaningful category [F2-B §4.18].

---

## 9.10 The semantic decision and the storage decision

[F2-B §4.18; F3-A §6.14]

| Decision | Question | Judged by | Owner |
|---|---|---|---|
| Semantic | Is this abstraction meaningful, valid, and useful? | Gates G1–G8, review | Grammar Engine, Promotion Controller |
| Storage | Does storing it as a reusable template reduce total cost? | Net bytes (`N(L − R − P) > D + I`, Part 11), decode cost | Compression Optimizer |

Examples:
- Parent frame for two small frames: the extra parent record, inheritance references, index overhead, new constraints, and resolution cost may exceed the saving. For thousands of similar frames it may pay [F2-B §4.18].
- A semantically useful abstraction with no storage benefit stays in the ontology and gets no special binary template.
- A frequent sequence of IDs with no conceptual meaning can still be compressed. It never enters the ontology.

The two optimizers may exchange information. Each has its own success criteria, and neither can promote on the other's evidence.

---

## 9.11 Generalization budget and growth limits

[F2-B §4.23; F3-B §7.15; F1-C §13]

```text
GENERALIZATION_TASK budget [illustrative, not production settings]
  MAX_CANDIDATES      = 100     candidate abstractions examined per task
  MAX_GRAPH_DEPTH     = 4       traversal depth in matching
  MAX_STRUCT_NODES    = 12      per structure in TYPED_MATCH
  MAX_MATCH_STEPS     = bounded per pair
  MAX_NEW_FRAMES      = 5       promoted per learning cycle
  MAX_NEW_REL_TYPES   = 1       per release
  MAX_STORAGE_GROWTH  = bounded growth in S_total per cycle
  TIME_BUDGET         = wall-clock cap
  REQUIRE_REVIEW      = TRUE
```

**SG-GEN-007 (Normative).** Every pattern-discovery and generalization task runs under a stated budget. Exhausting it ends the task with a report. The system never continues "until done". The defaults are conservative and are tuned on the benchmark. "These numbers are illustrative, not recommended production settings" [F2-B §4.23].

Growth indicators are monitored per release (Part 12 §12.x): frames per 1,000 processed units, instances per frame, share of frames with a single instance, relation-type count, abstraction depth, and share of candidates rejected. A frame with very few instances after a long period is flagged for review. A rising count of near-duplicate frames triggers a duplicate sweep, in the same way as for concepts (Part 7 §7.10.2).

---

## 9.12 Analogy and metaphor engine

[F1-C §6; F1-B §8.2; F2-B §4.12; F1-A §3.3]

The `AnalogyAndMetaphorEngine` of the brain-inspired design has a larger role than understanding figurative language. It also discovers generalizations. It is bounded by one rule: **structural similarity is not semantic equivalence** [F1-C §6].

### 9.9.x Procedure (relationship by relationship)

The coaching reference's *Borrowed Pattern* lens warns against matches that "merely look or sound similar", and requires that "the match holds relationship-for-relationship" [REF; F1-B §8.2]. The engine therefore checks:

```text
for a mapping M between domain A and domain B (from TYPED_MATCH):
  for each pair (a_i → b_i) and each relation r(a_i, a_j) in A:
      is there a relation r'(b_i, b_j) in B of the same type, or a declared compatible type?
         yes → shared_relations
         no  → unshared_a  (recorded, never discarded)
  likewise for B → A
  record differences: mechanism, scale, conservation laws, failure modes, energy source ...
  SC = |shared| / |relations in the smaller structure|        ordinal measure only
```

Output is a `StructuralAnalogy` (Part 4 §4.10.2) with status CANDIDATE.

### Example

[F1-B §8.2; F1-C §6]

| | Biological | Industrial |
|---|---|---|
| DRIVER | Heart | Pump |
| FLUID | Blood | Water |
| CONDUIT | BloodVessel | Pipe |

Shared relations: DRIVES_FLOW_OF(DRIVER, FLUID), FLOWS_THROUGH(FLUID, CONDUIT). Unshared: the heart is muscular tissue that grows and self-repairs, the pump is a manufactured device; the circuit is closed in one and often open in the other; control is neural and hormonal in one and electrical or manual in the other.

**SG-FRM-007 (applied).** The analogy licenses inference only along shared relations. It does not make the heart a pump or the pump an organ. It produces a **proposed mapping with shared and non-shared relationships clearly identified**, so an analogy cannot silently become a factual assertion [F1-C §6].

### Metaphor

The engine also proposes `FigurativeMapping` candidates when a literal reading fails type checking (Part 3 §3.15; Part 8 §8.10), for example SWALLOW → TAKE_IN. They remain CANDIDATE until approved, and they never redefine the literal word.

---

## 9.13 Pattern lifecycle

[F1-B §8.6; REF: pattern tracking]

The sources adapt the coaching document's idea of tracking recurring patterns across conversations instead of defining a stable pattern after one occurrence [F1-B §8.6]. The lifecycle:

```text
 DISCOVERED PATTERN        count ≥ N independent origins (SG-GEN-009)           → axis C: DISCOVERED
 CANDIDATE TEMPLATE        schema conforms, provisional store                    → STRUCTURED
 STRUCTURAL VALIDATION     G1, G2, G3                                            → VALIDATED_FORMALLY
 CROSS-DOMAIN TESTING      held-out structures from other domains; G4 (counterexamples)
 COMPRESSION EVALUATION    Q_store by the Compression Optimizer (informs, never gates semantic promotion)
 REVIEW                    per risk class                                        → REVIEWED_SEMANTICALLY
 PROMOTED SEMANTIC FRAME   Promotion Controller, versioned                       → PROMOTED
```

Four pre-promotion questions the source lists [F1-B §8.6]: Do the structures really share corresponding relationships? Does the abstraction preserve important distinctions? Does it already exist? Is it useful across several examples? Does it reduce storage or improve semantic consistency? These are G1, G8, G6, G5, and the separate storage decision.

**Division of labour** [F1-B §8.6]: the AI suggests recurring patterns. Python measures frequency, structural compatibility, and cost. The larger AI reviews difficult conceptual distinctions. The final decision is governed by explicit promotion rules.

**Veto and demotion.** A reviewer may reject a pattern (Part 6 §6.12.3). A promoted pattern or abstraction that later accumulates verified counterexamples is flagged, suspended, and reviewed. It is not silently kept.

---

## 9.14 Learning from errors and corrections

### 9.14.1 What the system is learning about

[F3-B §7.19] The system is also learning *which of its own semantic-processing procedures are reliable under different conditions*. That is the "procedural" kind of memory.

| Memory | Contents in the learning context | Where |
|---|---|---|
| Semantic | Facts and relations (`HYGROMETER MEASURES HUMIDITY`) | Dictionary and claim store |
| Episodic | Records of particular learning activities: task, source, candidate, result, reason | Process history (H layer) |
| Procedural | Reusable processing rules: duplicate check, passive mapping, frame type validation | Rulebook (Part 5) |

The Learning Controller reads episodic records to find weaknesses in procedural rules. **Changes to procedural memory pass a separate review** (Part 5 §5.12), because otherwise "the system could begin modifying its own validation rules in ways that make future errors easier to accept" [F3-B §7.20].

### 9.14.2 Error taxonomy

Each error has a code, a detector, and a link to the review finding codes of Part 6 §6.11.

| Category | Typical detector | Example |
|---|---|---|
| SEMANTIC_ROLE_REVERSAL | Metamorphic pair mismatch, reviewer | Patient assigned as agent in a passive |
| WRONG_SENSE | Type error, reviewer (R-SENSE) | Bank as riverbank |
| UNSUPPORTED_ASSERTION | VC-V01/V02 | Invented location |
| NEGATION_OR_SCOPE_ERROR | VC-V07, reviewer | Negation dropped |
| COREFERENCE_ERROR | Reviewer (R-COREF) | Wrong antecedent |
| FRAME_MISFIT | Validator, reviewer | Lease forced into TRANSFER |
| DUPLICATE_CONCEPT | Duplicate sweep (Part 7) | Two concepts for one meaning |
| WRONG_MERGE | Revocation (Part 7) | Distinct concepts merged |
| OVERGENERALIZATION | Counterexample found later | Universal later refuted |
| CANON_OVERREACH | Negative pairs | Offer normalized to give |
| PATTERN_FALSE_POSITIVE | Audit of ACTIVE patterns | "bought the argument" treated as purchase |

```text
ErrorRecord   (H layer; stores method, never source narrative: Part 6 §6.12.5)
  error_id, category, detector, task_id
  construction, frame, rule_ids, producer_method, model_id
  severity, detected_at, resolution
  gold_ref (if the correct answer is known)
```

### 9.14.3 Analysis and proposals

[F3-B §7.19; F3-B §7.29]

```text
        NEW SOURCE → EXTRACTION → VALIDATION → ERROR ANALYSIS
                                                   │
                                  ┌────────────────┴───────────────┐
                                  ▼                                ▼
                            ACCEPTED DATA                      FAILED CASES
                                  ▼                                ▼
                            KNOWLEDGE STORE                    ERROR MEMORY
                                                                   ▼
                                                            PATTERN ANALYSIS
                                                                   ▼
                                                        PROPOSED IMPROVEMENT
                                                                   ▼
                                                  HELD-OUT RETEST → CHANGE CONTROL (Part 5 §5.12)
```

Errors are grouped by category *c* = (construction × frame family × rule set × producer method), the same grouping used for risk calibration (Part 6 §6.10.3). After enough reviewed examples a category may yield one of the following **proposals** [F3-B §7.19]:

| Proposal | Example |
|---|---|
| A better parsing or interpretation rule | Distinguish passive with and without an explicit agent |
| Additional examples for the local model | Add validated gold cases to the example bank used for that task |
| A specialized validation test | A check for locative by-phrases |
| A different model for this construction | Route SCOPE tasks to the reviewer model |
| A new ambiguity-handling procedure | Retain ALT earlier for this construction |

**SG-LRN-008 (Normative, Enhancement E-82).** An error pattern MUST NOT trigger a rule or model change automatically. The Learning Controller *proposes*, and changes are evaluated on **held-out examples** so the system does not overfit its recent mistakes [F3-B §7.29]. To protect that evaluation:
- Gold data is split into **train/dev** (used to build rules and examples, fed by corrections) and a **sealed test set** that is never used for tuning and is refreshed periodically.
- A single failure never rewrites a rule.
- Rule proposals must include the distinguishing negative cases. In the source's passive example, "The patient was given medication" has no stated agent, and a rule learned from the "…by the doctor" cases must not invent one [F3-B §7.32].

### 9.14.4 Learning semantic rules from corrections

[F3-B §7.32] When a stronger reviewer repeatedly corrects the local model, the system records:

```text
Correction     input_construction, error, correct_mapping, reviewer, certificate_ids
```

After accumulating enough examples (sampled across independent sources) a specialized rule *candidate* can be proposed and then goes through the Part 5 §5.12 change control. This is more controlled than letting the model rewrite its own instructions from one failure.

---

## 9.15 Revision, versioning, reprocessing, and cycle control

### 9.15.1 Controlled revision

[F3-B §7.24; F2-B §4.25] A weakness found in an existing frame produces a *proposed version*, not an overwrite:

```text
FRAME_ID = 201   CURRENT_VERSION = 1   PROPOSED_VERSION = 2
CHANGE_DESCRIPTION · MOTIVATION · SUPPORTING_EXAMPLES · COUNTEREXAMPLES
COMPATIBILITY_ANALYSIS · AFFECTED_RECORDS · TEST_RESULTS
```

The validator evaluates whether the change alters the meaning of existing records. If so migration may be necessary. Previous versions stay resolvable so older records remain interpretable. Record the generalization rules that produced each frame (`derived_by`) so a faulty rule's output can be found and reprocessed [F2-B §4.25].

### 9.15.2 Learning cycles with gates (Enhancement E-82, SG-LRN-007)

A learning cycle is a scheduled, bounded run of the engines. It is the unit of control.

**SG-LRN-007 (Normative).** Before a cycle starts, the Learning Controller pre-registers:
1. **Scope and budgets** (§9.11, Part 10).
2. **Monitored metrics** (§9.17) with baseline values from the previous cycle.
3. **Stop conditions:** a rise in audited error upper bound for any category, a drop in sealed-test performance, an increase in reviewer-disagreement rate, growth beyond limits, or backlog beyond a limit.
4. **Held-out evaluation** to run before and after promotions.
5. **Canary period.** Promoted items are flagged `canary` for a defined period [Provisional]. During it, audit sampling of everything depending on them is increased, and rollback is rehearsed.

At the end the controller writes a **cycle report**: candidates by type and stage, rejections with reasons, promotions, metric deltas, resources used, and open questions. Stop conditions halt promotion, not discovery. The candidate store can keep filling while promotions are paused.

### 9.15.3 Ingest ledger and reprocessing (Enhancement E-83)

[F3-B §7.30 progress tracking; F3-B §7.31 reprocessing is expensive]

```text
IngestLedger   source_id, unit_id, pipeline_version, grammar_version, ontology_release,
               ruleset_release, outcome (axis A), status, last_processed
```

The ledger records which sources and sentences have been processed, under which versions. It makes processing **idempotent** (no re-processing of unchanged inputs, Part 8 §8.11.5) and drives reprocessing after a grammar revision:

1. The Promotion Controller lists records produced by the changed frame, rule, or pattern (certificate lookup, SG-CAN-003).
2. Impact classes (Part 2 §2.13): NOT_REVIEWED, AUTO_MIGRATED, REVIEWED, REPROCESS_REQUIRED.
3. Reprocessing is **queued, batched, and prioritized**, never run as one blocking pass. Priority order: records that inform trusted-view claims, records with MEDIUM-or-higher risk, records most often retrieved, then the rest. It runs in the background under the budget (§9.19).
4. Completion is tracked, and the ledger shows how many records still carry an old version.

---

## 9.16 Contradictions and learning

[F3-B §7.26; Part 6 §6.8]

- Learning never overwrites. Contradictory claims from two sources are stored as source-attributed claims in a cluster.
- A contradiction **counts as counterexample evidence**. CE2 (§9.9.3) reads clusters, so a disputed universal cannot be promoted.
- Apparent contradictions can come from **wrong parsing**. Before concluding a source is wrong, the cluster evaluation re-runs both claims through an independent extraction path (Part 6 §6.8). If the contradiction was a parse error, the candidate that caused it is corrected through the certificate path and the error is recorded (§9.14).
- A system that "deletes contradictory claims may appear consistent while losing important evidence" [F3-B §7.26]. The learning engines therefore have no delete capability.

---

## 9.17 Measuring learning quality

[F3-B §7.28] Some metrics need manually annotated reference data. "Semantic role accuracy cannot be measured reliably by comparing the model with itself," and detecting wrong merges requires reference judgments [F3-B §7.28]. A small, carefully reviewed benchmark is built **before** scaling the learning process.

| Metric | Operational definition |
|---|---|
| Frame accuracy | Correct frame selected / gold units with an expected frame |
| Role accuracy | Correct role bindings (role, filler, value state) / gold bindings, reported with and without UNSPEC handling |
| Concept resolution accuracy | Part 7 §7.14 |
| Unsupported assertion rate | Elements failing VC-V01/V02/V06 in audit / elements audited |
| Ambiguity handling | Of gold-AMBIGUOUS units, share retained as ALT. Of retained ALTs, share where gold agrees there is ambiguity. |
| Duplicate concept rate | Part 7 §7.14 |
| Incorrect merge rate | Part 7 §7.14 |
| Generalization precision | Promoted abstractions judged valid in audit / audited promoted abstractions. Also the later-refuted rate (verified counterexamples found after promotion). |
| Counterexample coverage | Share of promoted candidates whose search covered all four methods, and mean classes tested |
| Grammar growth | New frames per 1,000 units, instances per frame, share of single-instance frames, depth of the frame hierarchy |
| Pattern graduation | ACTIVE patterns, their audited error upper bounds, suspension rate, model-call reduction attributable to patterns |
| Storage cost | `S_total` (Part 11) |
| Processing cost | Time, model calls, peak RAM per unit |
| Abstention quality | Part 7 §7.14: correct "unresolved" decisions versus incorrect guesses (Part 12) |

Measure **correctness and appropriate abstention together**. A system that guesses on every ambiguous sentence may appear more productive while being less reliable [F3-C §8.22].

---

## 9.18 Resources and scheduling

[F3-B §7.31; F3-C §8.17, §8.25]

| Cost class | Learning tasks | Handling |
|---|---|---|
| Lightweight deterministic | Classifier, ID and lexical lookup, rule validation, type checks, exact duplicate detection, signature computation, encoding | Run inline |
| Medium | Embedding generation, semantic candidate retrieval, graph matching on selected subgraphs, pattern clustering, disambiguation with smaller models | Queue with concurrency limits |
| Expensive | Complex interpretation by a model, large cross-domain analogy discovery, reviewing ambiguous concepts, evaluating subtle generalizations, reprocessing large corpora | Queue, batch, invoke selectively |

Learning tasks use the lower priorities of the shared model service [F3-C §8.17]:

```text
PRIORITY 1  complete the current semantic interpretation
PRIORITY 2  resolve ambiguous concepts
PRIORITY 3  review candidate generalizations
PRIORITY 4  background grammar optimization and reprocessing
```

They are preemptible. "I would not design the system around continuously running every cognitive module" [F3-B §7.31]. The central controller activates modules according to task requirements, consistent with sparse activation (P-16, P-22).

---

## 9.19 Coaching-document mechanisms mapped to USG operations (Enhancement E-86, completes E-17)

F1-B §9 lists adaptations of the coaching document's analytical mechanisms. "These are adaptations of the document's analytical mechanisms, not features that the file already implements as semantic-processing algorithms" [F1-B §9]. Each is given a concrete USG operation here, with a pointer to where it lives.

| Coaching idea | USG mechanism | Where specified |
|---|---|---|
| Roles & Fit (functional roles of components) | Functional Ontology: FN functions and HAS_FUNCTION, separate from classification | Part 4 §4.8 |
| Missing Piece / Known-Shape | Template recognition. REQUIRED, OPTIONAL, UNSPECIFIED roles. **ExpectedButUnstated report** (below). | Part 2 §2.6; Part 4 |
| Borrowed Pattern (relation-for-relation matching) | Analogy engine with shared and unshared relations | §9.12 |
| Zoom (broader pattern / specific detail) | GENERALIZE and SPECIALIZE, abstraction layers 0–4 | Part 4 §4.5.3, §4.11 |
| Evidence Ladder | Evidence vector and derived E-labels | Part 6 §6.4 |
| Pattern tracking (3+ occurrences, user veto) | SG-GEN-009, REJECTED_PATTERN | §9.8.3; Part 6 §6.12 |
| Inversion (counterexamples) | Counterexample engine CE3: systematic inversion | §9.9.3 |
| Second-Order Check (chains of consequences) | **Consequence-chain test** (below) | §9.19.1 |
| Assumed vs. Real Constraint | Constraint provenance classes | §9.6.4 (SG-KNW-006) |
| Thinking-Pattern Check (unjustified universals) | **Universal-claim lint** (below) | §9.19.2 |
| Bottleneck & Signal (which uncertainty matters most) | **Highest-impact uncertainty** ordering of the review queue | §9.19.3 |
| Loop & Timing (recurring structures, feedback) | Feedback-loop detection for REGULATE and LOOP composites | §9.19.4 |
| Relevance ranking | Priority ordering by risk, dependents, and age (queues) | Part 6 §6.11.5; §9.18 |
| Adaptive analysis depth | Capability-based plans by input class | Part 8 §8.18 |
| Lazy loading | Task-specific `grammar_view`, partitioned stores, selective retrieval | Part 8 §8.11.1; Part 10 |
| Layered architecture with heavy parts outside the interactive loop | Background learning, scheduled optimization, queues | §9.18 |

### 9.19.1 Consequence-chain test

When a candidate generalization or rule is adopted, derive consequences a step or two deeper than the obvious one [REF: Second-Order Check]. Each step is a registered inference, labelled INFERRED with `support_cap`, depth-limited [Provisional: 3]. If any derived consequence contradicts trusted knowledge, the candidate is held for review with the chain attached. This catches generalizations whose first-order effect looks fine and whose second-order effect is wrong. The derived consequences are used for testing only and are never stored as source-stated.

### 9.19.2 Universal-claim lint

A deterministic lint runs over model proposals and over interpreted source content:
- Proposal contains a universal quantifier, "always", "never", "every", "all", or "only": the candidate is classified (§9.9.2) and, if universal, routed to risk class VERY_HIGH.
- **Source** text that uses such words is interpreted *faithfully* (the source's quantifier is represented as written, Part 3 §3.7). The lint only prevents it being promoted to ontology.
- Language that treats a worst case as certain, or that attributes mental states without evidence, is interpreted as attribution and modality (Part 3 §3.8), never as stated fact.

This applies the coaching idea of detecting all-or-nothing language and unjustified generalizations without turning it into a judgment of any author.

### 9.19.3 Highest-impact uncertainty first

[F1-B §9: Bottleneck & Signal] If several uncertainties are open, the review queue orders items by **how many downstream decisions the answer would change**: the count of dependent candidates, ALT groups, patterns, and mappings that rest on it. This replaces ordering by arrival time alone. It is an ordering heuristic, and it does not change risk classes.

### 9.19.4 Feedback-loop detection

[F1-B §9: Loop & Timing] The pattern engine searches for cyclic structures in validated process knowledge: a detector, a decision element, and an actuator linked in a cycle through a controlled quantity. That is the signature of FN.REGULATE (Part 4 §4.8.2). It also detects repeated sub-processes (LOOP composites) and self-reinforcing structures. A detected cycle is a candidate `COMPOSE(LOOP …)` or a REGULATE assertion, subject to the same gates.

### 9.19.5 ExpectedButUnstated report

[F1-B §8.4] Given a recognized frame, the system can list which roles the frame conventionally involves that the source left UNSPEC. For "John transferred money" it reports SOURCE and DESTINATION as absent. This serves question generation, retrieval, and completeness checks. **It never fills the roles.** "Missing semantic information is not necessarily an error" [F1-B §8.4]. The report is derived and not stored as assertions.

---

## 9.20 Worked example: a generalization through all gates

[F3-B §7.16; F1-D §2.18; F2-B §4.12]

**Observations** (validated, E2, from independent origins):

```text
HEART DRIVES_FLOW_OF BLOOD         PUMP DRIVES_FLOW_OF WATER         FAN DRIVES_FLOW_OF AIR
```

**Count.** Three structures. If all three come from one textbook they count as one (§9.8.3) and no candidate arises. Assume three independent origins.

**Stage 3: candidate.** `FLUID_MOVEMENT_FRAME(DRIVER, FLUID)`.

| Gate | Result |
|---|---|
| G1 | TYPED_MATCH finds DRIVER ↔ {Heart, Pump, Fan}, FLUID ↔ {Blood, Water, Air}. Anchored through FN `DRIVE_FLUID_FLOW`, **not** through ENTITY. |
| G2 | Blood, water, and air are Fluids in the physical sense. DRIVER is constrained **functionally** (`HAS_FUNCTION DRIVE_FLUID_FLOW`), not by a class, so biological and manufactured systems share it without a shared superclass (SG-FRM-005). |
| G3 | The candidate must not claim that all three use the same pumping mechanism. It claims nothing about mechanism. |
| G4 | CE3 inversion on the claim "everything with `DRIVES_FLOW_OF` is a pump" yields heart (an organ) and fan (a different device) as non-pumps, so that claim is not made. The earlier circulation template (Part 4 §4.10.1) had CONDUIT REQUIRED: a fan moves air with no conduit, so a VERIFIED counterexample to *that* claim. **Refinement:** CONDUIT is OPTIONAL, and "circulation" is not claimed. |
| G5 | `n(G) = 3` ≥ m, coverage low. Pass. |
| G6 | **Duplicate check against the library.** FLUID_TRANSPORT already exists (Part 4 §4.8.5: TRANSPORTED_ENTITY, MECHANISM, SOURCE, DESTINATION). The candidate matches FLUID_TRANSPORT with DRIVER ↔ MECHANISM. |
| G7–G8 | Specific records stay with their IDs (SG-GEN-008). |

**Outcome (SG-LRN-004, prefer composition).** No new frame is created. The learning outcome is: (a) an alignment record `FLUID_MOVEMENT_CANDIDATE → FLUID_TRANSPORT` with `DRIVER → MECHANISM`, and (b) candidate **functional assertions** `HEART`, `PUMP`, `FAN` `HAS_FUNCTION DRIVE_FLUID_FLOW` (a specialization of FN.TRANSPORT), which feed cross-domain retrieval and analogy. The source example (F3-B §7.16) says "the new frame may become a reusable structure", written before the library defined FLUID_TRANSPORT. Duplicate checking against the frame library is what turns that into reuse. The Compression Optimizer separately decides whether a special binary code for the pattern pays (§9.10).

---

## 9.21 Closure of source items in this part

| Source item | Closed in |
|---|---|
| Four learning processes and engines (F3-B §7.1–7.2) | §9.1–§9.2 |
| Candidate lifecycle and "learning ≠ promotion" (F3-B §7.25) | §9.3 |
| Lexical, concept, knowledge learning (F3-B §7.11–7.12) | §9.4–§9.6 |
| Grammar learning, five stages, growth control (F3-B §7.14–7.15) | §9.7 |
| LEASE and hygrometer examples (F3-B §7.11, §7.13) | §9.7.3; Part 7 §7.9 |
| Heart/pump/fan generalization (F3-B §7.16) | §9.20 |
| Learning from validation errors and corrections (F3-B §7.19, §7.32) | §9.14 |
| Procedural memory and rule hierarchy (F3-B §7.20–7.21) | §9.14.1; Part 5 §5.2, §5.12 |
| Paraphrase and counterexample-driven learning (F3-B §7.22–7.23) | Part 5 §5.11; §9.9.3 |
| Controlled revision (F3-B §7.24) | §9.15.1 |
| Contradictory sources (F3-B §7.26) | §9.16; Part 6 §6.8 |
| Learning quality metrics (F3-B §7.28) | §9.17 |
| Feedback loop (F3-B §7.29) | §9.14.3 |
| Central controller in learning (F3-B §7.30) | §9.2.2 |
| Personal-computer cost categories (F3-B §7.31) | §9.18 |
| Four generalization types, taxonomic through procedural (F2-B §4.1–4.7) | §9.9.1; Part 4 |
| Graph matching, signatures, attention (F2-B §4.12–4.14) | §9.8 |
| Counterexamples and inversion (F2-B §4.15–4.16) | §9.9.3 |
| Generalization as search, scoring (F2-B §4.17) | §9.9.6 |
| Generalization versus compression (F2-B §4.18; F3-A §6.14) | §9.10 |
| Discriminative value (F2-B §4.20) | §9.9.5 |
| Pipeline and cross-domain task (F2-B §4.21–4.22) | §9.8.2, §9.8.5 |
| Generalization budget (F2-B §4.23) | §9.11 |
| Versioned generalization (F2-B §4.25) | §9.15 |
| Pattern lifecycle (F1-B §8.6, §10) | §9.13 |
| Self-extending grammar and the optimizer (F1-A §3.17) | §9.7.4, §9.10 |
| Analogy and metaphor engine (F1-C §6) | §9.12 |
| Other coaching-document adaptations (F1-B §9) | §9.19 |
| Grammar Promotion Controller (F1-C §13) | §9.3.5 |

### Rules registered or refined in this part

| Rule | Subject |
|---|---|
| SG-LRN-002 | Engines cannot advance candidates beyond STRUCTURED |
| SG-LRN-003 | Conservative new relation types |
| SG-LRN-004 | Prefer composition over new fundamental frames. Accuracy beats minimal frame count. |
| SG-LRN-005 | Demand-driven grammar learning from aggregated FRAME_GAP |
| SG-LRN-006 | Atomic promotion bundles and dependency taint |
| SG-LRN-007 | Learning cycles with pre-registered metrics, stop conditions, canary |
| SG-LRN-008 | Error-driven changes are proposals, tested on held-out data with a sealed test set |
| SG-GEN-002 (restated) | No universal from examples alone |
| SG-GEN-004 | Discriminative value (coverage and reuse bounds) |
| SG-GEN-005 | Counterexample states and coverage reporting |
| SG-GEN-006 | Gates before scores |
| SG-GEN-007 | Generalization budgets |
| SG-GEN-008 | Abstractions are additive. Specifics keep their IDs. |
| SG-GEN-009 | Minimum independent occurrences, and the veto |
| SG-GEN-010 | Claim classification before validation |
| SG-KNW-006 | Constraint provenance classes |

### Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-12 (completed) | Q(G) let reuse or compression offset semantic error, and mixed semantic and storage factors | Gates first. Split into Q_sem and Q_store (§9.9.6). |
| E-17 (completed) | Coaching mechanisms only partly mapped | Concrete operations and mappings (§9.19) |
| E-77 | Counterexamples were accepted or ignored without distinction, and used only to reject | Verified / unverified / none-found with coverage reporting. Distinction mining (§9.9.3). |
| E-78 | "Balance of generality and specificity" was unmeasurable | Coverage cap and reuse floor (§9.9.5) |
| E-79 | Pattern frequency could be inflated by duplicates | Count independent origins only (§9.8.3) |
| E-80 | Graph matching is NP-complete and could match through the root class | Bounded, type-aware, role-first matching (§9.8.4) |
| E-81 | Piecemeal promotion could leave trusted records pointing at unpromoted ones | Atomic bundles, dependency taint, rollback plans (§9.3.4) |
| E-82 | Learning changes could overfit recent errors and silently degrade quality | Learning cycle gates, sealed test set, canary, stop conditions (§9.14.3, §9.15.2) |
| E-83 | Reprocessing after grammar changes was named as expensive but not designed | Ingest ledger, impact classes, prioritized background reprocessing (§9.15.3) |
| E-84 | One unfamiliar sentence could trigger a new frame | Demand aggregated across independent origins (§9.7.5) |
| E-85 | New relation types would multiply near-duplicates | Strict necessity test, minimum count, growth cap (§9.6.3) |
| E-86 | Model habits could become hard constraints | Constraint provenance classes (§9.6.4) |


---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 10 of 12: Cognitive Architecture, Memory, and Resource Management

Parts 2–9 specified the language, the rules, the interpretation pipeline, and the learning machinery. This part specifies the machinery that runs them: how work is planned and scheduled, how modules share information without corrupting it, how memory is organized and retrieved, and how everything stays within the limits of a personal computer.

Brain-inspired ideas are used as **functional abstractions**, not biological models [F1-C §5, §16]. Each one stays only if it improves accuracy, generalization, compression, efficiency, or maintainability (P-24). The unifying decision from the sources is that **Semantic Grammar is the common representation** every module reads and writes, so information never has to be re-translated as it moves between modules [F1-C §2].

---

## 10.1 What is carried forward

[F1-C §1] The earlier brain-inspired design is known to this specification only through the summaries in F1-C. Several of its ideas were proposals, and each is re-evaluated here against USG's requirements.

| Earlier idea | Role in USG | Realized in |
|---|---|---|
| Central main controller | Directs the semantic processing workflow | §10.2.1 |
| Assistant main controllers | Coordinate interpretation, knowledge, validation, learning asynchronously | §10.2.2 |
| Specialized modules | Parsing, resolution, inference, pattern discovery | §10.9 |
| Shared module access | One shared model service, shared caches and indexes | §10.3.4, §10.13 |
| Global cognitive workspace | Holds the evolving interpretation of the current task | §10.4 |
| Semantic memory | Concepts, definitions, relationships | §10.5 |
| Episodic memory | Extracted events with context, plus processing history (kept separate) | §10.5 |
| Procedural memory | Rules, patterns, validation procedures | §10.5 |
| Attention | Load only the concepts and relations a task needs | §10.4.3, §10.7 |
| Prediction and error correction | Detect semantic conflicts and revise candidates | §10.11 |
| Metacognition | Monitor quality and decide what further work is needed | §10.10; Part 6 §6.9 |
| Analogy and abstraction | Discover reusable structures | Part 9 §9.12 |
| Memory activation and decay | Keep frequently needed structures readily accessible | §10.7.4 |
| Domain-specific networks | Avoid one enormous centralized graph | §10.6 |

---

## 10.2 Controllers and task orchestration

### 10.2.1 The central controller

The source's decision is that the central controller is **predominantly deterministic**, not another language model [F3-C §8.27]. It decides from task type, available input, required capabilities, dependency rules, validation failures, resource availability, and budgets.

| Responsibility | Mechanism | Source |
|---|---|---|
| Task planning and distribution | Builds a plan from the capability registry (§10.2.5) | F3-B §7.30 |
| Priorities and resource management | Priority classes, quotas, admission control (§10.13) | F1-C §3 |
| Dependency management | Task DAG, dependency-aware scheduling | F3-C §8.16 |
| Retry control | Bounded retries and budgets (Part 5 §5.7) | F3-B §7.30 |
| Review escalation | Metacognition signals to review service (Part 6 §6.9) | F3-B §7.30 |
| Commit coordination | Workspace commits (§10.4.5), hand-off to Registry Manager and Promotion Controller | F3-B §7.30 |
| Progress tracking | Ingest ledger (Part 9 §9.15.3) | F3-B §7.30 |

**What it does not do.** It does not interpret sentences, does not write authoritative stores directly, and does not alter rules (SG-FND-005). It orchestrates specialized services. A model may help *classify* an unfamiliar task, but it has no authority to invoke expensive modules indefinitely [F3-C §8.27].

### 10.2.2 Assistant controllers, organized by cognitive responsibility

[F1-C §3] The source organizes assistant controllers by **cognitive responsibility** instead of by knowledge domain, so that one domain does not need its own copy of the machinery.

| Controller | Owns | Typical modules |
|---|---|---|
| **Interpretation** | Turning language into candidate IR | LinguisticParser, SemanticParser, FrameResolver, ContextIntegrator, EvidenceExtractor |
| **Knowledge** | Concept identity, retrieval, reasoning, memory access | SemanticHub, ConceptResolver, MemoryManager, ReasoningModule, graph search |
| **Validation** | Checking and review | RuleEngine, TypeChecker, EvidenceValidator, ReviewManager, CertificateChecker |
| **Learning** | Candidate generation and grammar growth | Lexical, Concept, Knowledge, and Grammar engines; PatternDiscovery; AnalogyEngine; GeneralizationEngine; CounterexampleEngine; Compression Optimizer |

Controllers are **logical units of responsibility**, not necessarily operating-system processes. A controller can be an asynchronous Python component managing many tasks [F1-C §3]. They are independent: they receive `TaskSpec`s and return `Message`s (§10.3.2). They do not call each other's modules directly. Within one controller, direct calls are fine.

### 10.2.3 Task model

```text
Task
  task_id, parent_task_id, plan_id
  type                    e.g. INTERPRET_UNIT, RESOLVE_CONCEPT, VALIDATE, REVIEW,
                          PATTERN_DISCOVERY, REPROCESS, DUPLICATE_SWEEP
  workspace_id, unit_ref  what is being worked on
  priority_class          P1 | P2 | P3 | P4        (§10.13.4)
  budget                  model_calls, tokens, candidates, depth, retries, memory, wall_time
  deadline                optional
  depends_on[]            task ids
  idempotency_key         hash of (type, normalized input, versions)
  attempts, state, cancel_token
  required_capabilities[] 
```

States: `PENDING → READY → RUNNING → (WAITING_MODEL) → DONE`, with terminal alternatives `FAILED`, `CANCELLED`, `EXPIRED`, `DEAD_LETTERED`. A task in `FAILED` after its retries are exhausted ends in the unit's outcome UNRESOLVED (Part 5 §5.10). It never retries forever.

### 10.2.4 Idempotency

A task whose idempotency key matches a completed or running task is not executed twice. It receives the earlier result (Part 8 §8.11.5, result cache). This makes retries, restarts, and concurrent submission safe, and it is the basis for novelty protection (Part 6 §6.12.4).

### 10.2.5 Capability-based planning

[F3-C §8.26] Instead of one fixed pipeline for every input, each module declares its capabilities and the controller selects what the task needs.

```text
ModuleDeclaration
  module_id, version, controller_owner
  capabilities[]           e.g. StructuralComparison, FunctionalMapping, CandidateGeneralization
  inputs, outputs          typed
  cost_class               L (lightweight deterministic) | M (medium) | E (expensive)   (Part 9 §9.18)
  uses_model               NONE | PRIMARY | REVIEWER | EMBEDDING
  reads[], proposes[]      which stores it may read, which candidate types it may emit
  resident_memory_estimate, warmup_cost
  preemptible              true | false
```

Planning algorithm (deterministic):

```text
1  classify the unit (Part 8 §8.18.1: P, E, C, F, N)
2  required capabilities = lookup(class, flags)               # table-driven
3  select modules declaring those capabilities, prefer lowest cost_class
4  build DAG from module input/output types; independent steps become parallel ready tasks
5  attach budgets and priority from the unit's source tier and risk class
6  re-plan at decision points when validation or metacognition requests more work
```

"The task controller should activate only the necessary components. This resembles selective cognitive processing. It also reduces computation" [F3-C §8.26].

### 10.2.6 Scheduling

- **Dependency-aware.** A task becomes READY only when all `depends_on` are DONE. Independent tasks (language analysis, lexical candidate retrieval, related-concept retrieval) run concurrently. Final validation waits for them [F3-C §8.16].
- **Priority classes** and fair-share rules are in §10.13.4.
- **Admission control.** A task is admitted only if the resource governor can meet its declared estimates (§10.13.3). Otherwise it waits or is degraded.

### 10.2.7 Failure handling

| Failure | Response |
|---|---|
| Module exception | Task FAILED. Retry only if the error is classed transient. Others are dead-lettered with the stack trace in process history. |
| Timeout | Cancel (cooperative), record, retry within budget |
| Model returns schema-invalid output | Counts as one attempt. Repair loop (Part 5 §5.7) |
| Repeated failure from one source or module | **Circuit breaker:** pause that source or module for a cool-down, then half-open with one probe task |
| Poison item (always fails) | Dead-letter queue with reason. Reviewed by a human. Other work continues. |
| Controller crash | Restart. Reload tasks from the durable queue (§10.14). Workspaces are rebuilt from checkpoints. |

---

## 10.3 Messaging and concurrency

### 10.3.1 Four kinds of sharing, one rule

[F1-D §2.12] "Shared memory" has four distinct meanings, and only the last is about resource contention:

| Sharing | Mechanism |
|---|---|
| **Shared semantic identity** | All modules use the same typed IDs |
| **Shared persistent knowledge** | All modules read the same authoritative stores |
| **Shared task context** | Modules exchange information through the Cognitive Workspace |
| **Shared computational resources** | Modules use the same loaded model, indexes, and caches |

**SG-GOV-008 (Normative).** Modules share IDs and **immutable snapshots**, and coordinate state changes through explicit messages. They MUST NOT share mutable Python objects. Each store has a single writer (§10.3.5). This is easier to validate and debug than unrestricted shared mutable state [F1-D §2.12].

### 10.3.2 Message schema and queues

[F1-D §2.11]

```text
Message
  msg_id, task_id, workspace_id, base_version    version of the snapshot the module worked on
  module_id, module_version
  kind        RESULT | PROPOSAL | SIGNAL | ERROR | PROGRESS
  payload     references and small structures only (IDs, spans, patches)
  usage       wall_time, model_calls, tokens, peak_memory
  emitted_at
```

```text
              CENTRAL CONTROLLER
                      │
                  TASK QUEUE  (bounded, priority-ordered)
          ┌───────────┼───────────┐
       MODULE A    MODULE B    MODULE C
          └───────────┼───────────┘
                 RESULT QUEUE  (bounded)
                      │
              WORKSPACE MANAGER ──► versioned task state
```

All queues have a **maximum size** and apply backpressure: a full queue blocks or rejects new submissions, and it never grows without limit (SG-GOV-009, §10.13).

### 10.3.3 Concurrent writers and competing candidates (Enhancement E-92)

The source's example: Module A says `Event_1 = Transfer` while Module B says `Event_1 = Communication`. Without coordination one overwrites the other. "We should preserve both as competing candidates until a resolver decides which interpretation is better supported" [F1-D §2.11]. The protocol makes this precise.

Modules do not write the workspace. They emit **patches** against a `base_version`. The Workspace Manager applies them:

| Patch relation to current state | Action |
|---|---|
| Touches elements nobody else changed since `base_version` | Apply, increment version |
| Adds an alternative for an element where another module added a different alternative | **Both kept** as competing candidates (a candidate group), neither selected |
| Selects or replaces an element that changed after `base_version` | Reject. The module re-runs on the new snapshot, or the conflict is recorded as a `CONFLICT` signal |
| Adds evidence for an existing candidate | Apply |

A **resolver step** later selects among competing candidates by evidence and validation (Part 5, Part 6), or retains them as ALT (Part 3 §3.14). "The workspace should support disagreement rather than immediately forcing one interpretation" [F1-D §2.11].

### 10.3.4 The shared model service

[F1-C §3; F3-C §8.17; F3-B §7.31] Several controllers need the language model. One copy is loaded and shared:

```text
  CONTEXT INTEGRATOR ──┐
  CONCEPT LEARNER ─────┼──► MODEL GATEWAY ──► model runtime (Ollama / llama.cpp)
  GENERALIZATION ──────┘        bounded priority queue
```

**SG-GOV-010 (Normative).** No module loads its own model copy. The gateway is the only holder of model handles (SG-SEC-002), exposes the typed `SemanticModel` interface (Part 8 §8.11), and enforces the queue bound, per-call limits, and timeouts.

**Cooperative preemption (Enhancement E-91).** A generation already running cannot be safely interrupted, and the source's priority list [F3-C §8.17] presumes it can. The gateway therefore:
1. Orders its queue by priority class, with **aging** so low-priority work is not starved forever.
2. Never starts a lower-priority call when a higher-priority call is waiting.
3. Keeps calls small by decomposition (Part 8 §8.11.2), so the wait for any running call is short.
4. Supports cancellation of *queued* work. A running call is allowed to finish. Its result may be discarded if the task was cancelled.
5. Starts with concurrency of one or a small number of simultaneous generations, depending on measured hardware capacity, and increases it only if testing shows improved throughput [F3-C §8.17].

### 10.3.5 Single-writer discipline

Every store has exactly one writer path (SG-GOV-008), and writers are distinct from proposers:

| Store | Sole writer | Notes |
|---|---|---|
| Authoritative dictionary and trusted instances (D, I) | **Promotion Controller**, through the Registry Manager | Transactional. Atomic bundles (Part 9 §9.3.4). |
| Identity, IDs, mappings | **Registry Manager** (Part 7 §7.10) | One write connection |
| Provisional and candidate store | **Candidate Store service** | Accepts candidates from engines. No authority. |
| Provenance (P) | **ProvenanceWriter** | Append-only |
| Process history (H) | **ProcessHistoryWriter** | Append-only, no source content (Part 6 §6.12.5) |
| Rulebook and validator code | **Release manager** only | Not reachable from the model gateway or learning engines (SG-FND-005) |
| Caches | **Memory Manager** | Derived, regenerable |
| Workspaces | **Workspace Manager** | Ephemeral (§10.4) |

### 10.3.6 Execution model and process layout (Enhancement E-98)

`asyncio` coordinates I/O-bound work: database and network calls through compatible APIs, local model server requests, task dependencies, queues, and timeouts. It does **not** make CPU-intensive Python run in parallel, so heavy graph analysis needs worker processes or compiled libraries [F3-C §8.16].

```text
 MAIN PROCESS (asyncio event loop)
    Central Controller · Workspace Manager · four assistant controllers
    Memory Manager (read connection pool, caches)
    Registry Manager (dedicated writer thread owning the single write connection)
    Model Gateway (async client)
 EXTERNAL MODEL SERVER (Ollama or llama.cpp)       ← one loaded model, shared
 EMBEDDING SERVICE (lazy loaded in-process, or a small separate process)
 WORKER POOL (process pool): graph matching, signature computation,
                             batch embeddings, benchmark runs, encoding experiments
 SQLITE (WAL mode): multiple readers, one writer
```

SQLite notes: connections are used from the thread that created them unless configured otherwise, so the pool uses one connection per thread or a dedicated executor. The Registry Manager uses a single writer connection with `BEGIN IMMEDIATE` and a busy timeout (Part 7 §7.10.2). Readers use WAL snapshots, which fit the immutable-snapshot rule.

The source warns against adopting a large multi-agent framework just because there are several controllers [F3-C §8.28]. The first version uses ordinary Python classes, explicit task messages, `asyncio`, and a few worker services. A framework is evaluated only if orchestration needs outgrow this, and it must still satisfy stable IDs, machine-readable rules, deterministic validation, versioned definitions, transactional updates, and memory-efficient retrieval.

---

## 10.4 The Cognitive Workspace

### 10.4.1 Purpose and nature

The workspace holds the information currently relevant to a task. It stores **references and task-specific annotations**, not duplicated semantic records [F1-D §2.10; F1-C §4]. It is **ephemeral**. Durable results go to the provisional store, the claim store, provenance, and process history.

Duplicating full context in every module would cause inconsistency. Instead the workspace stores references such as `CONCEPT_ID = 102`, `FRAME_ID = 58`, `EVENT_REF = 9001` [F1-C §4].

### 10.4.2 Structure

```text
Workspace
  workspace_id, task_id, version, base ontology_release / grammar_version
  source_unit              source_id, span, normalized view, LinguisticAnalysis ref
  discourse                referent table, salience list, coreference links
  active_concepts[]        concept ids with activation scores (§10.7.2)
  active_frames[]          frame ids + versions
  candidates               groups of competing CandidateExpressions, each with:
                              certificate steps, validation results, supporting evidence refs
  signals[]                METHOD_DISAGREEMENT, RETRIEVAL_ADEQUACY, ...   (Part 6 §6.9.2)
  unresolved[]             open questions ("administered or handed over?")
  retrieval_state          seeds, frontier, budgets used
  status                   PLANNED | RUNNING | AWAITING_VALIDATION | AWAITING_REVIEW | DONE | FAILED
  budget_usage
```

### 10.4.3 Attention: bounded and ranked

[F1-C §10] The workspace has a **capacity** for active items [Provisional: ~200 concepts and frames per unit]. Items enter through retrieval (§10.7) and leave by lowest relevance when the cap is reached, except pinned items (the sentence's own lexical hits, concepts in candidate expressions). Retrieval expands in rounds ("INITIAL CONCEPTS → RELEVANT CONNECTIONS → CANDIDATE FRAMES → ADDITIONAL RETRIEVAL IF NEEDED") and stops when the budget is used or adequacy signals are satisfied.

### 10.4.4 Versioning and snapshots

Every applied patch produces a new immutable version. Modules read a snapshot at a version and emit patches with that `base_version` (§10.3.3). Old versions are kept for the life of the task so a repair loop or reviewer can see exactly what a module saw.

### 10.4.5 Commit protocol (SG-GOV-007)

**SG-GOV-007 (Normative).** Only the central controller commits workspace changes, and only the Workspace Manager applies patches.

At task end the controller does the following:
1. Runs the Part 5 routing on the selected or retained candidate set.
2. Writes provisional records, certificates, and validation reports through their sole writers.
3. Writes a compact `WorkspaceSummary` to process history (versions, signals, routing decision, budget use), with no source text.
4. Discards the workspace.

If a process dies mid-task, the document-level discourse state (the referent table) is recoverable from the last checkpoint (§10.14). The unit is re-run under its idempotency key.

### 10.4.6 Document-level layer

A document has one **discourse layer** shared across its units so pronouns and definites can resolve across sentences (Part 8 §8.2). It is checkpointed to the provisional store at unit boundaries, held in memory only while the document is active, and shed when the document completes or the memory governor needs room.

### 10.4.7 Worked example

[F1-C §4] "The doctor gave the patient medication because the infection had worsened."

```text
ACTIVE TASK         INTERPRET_UNIT  (workspace v7)
ACTIVE CONCEPTS     Doctor 101, Patient 102, Medication, Infection, Worsening   (+ activation scores)
REFERENTS           R1 doctor · R2 patient · R3 medication · R4 infection
CANDIDATE GROUP g1  (frame event)
   c1: GIVE(AGENT/SOURCE: R1, RECIPIENT: R2, THEME: R3)           rule SG-INT-040 · pattern graduated? no
CANDIDATE GROUP g2  (state event)
   c2: WORSEN(UNDERGOER: R4)   tense PAST-PERFECT relative to c1
CANDIDATE GROUP g3  (relation)
   c3: CAUSATION(CAUSE: c2, EFFECT: c1, CAUSE_TYPE: EXPLANATORY_REASON)    source "because"
SIGNALS             none adverse
UNRESOLVED          "Was the medication administered or handed over?"   → not in the source: stays unresolved
STATUS              AWAITING_VALIDATION
```

Roles: SemanticHub supplied the concepts, the frame resolver proposed GIVE, the ContextIntegrator evaluated the explanatory reading, the validation controller will check each element, and the central controller commits.

---

## 10.5 Memory architecture

### 10.5.1 Three memory types, as functions

[F1-C §7; F3-A §6.26; F3-B §7.20] The three types are logical *functions*. They do not require three databases.

| Memory | Holds | USG stores |
|---|---|---|
| **Semantic** | Concepts and general knowledge: "heart is an organ" | Dictionary D (concepts, definitions, relations, frames, functions), trusted view of claims, domain stores |
| **Episodic** | Particular events with their contexts | **World episodes:** instances, referents, assertions with source, time, participants (layer I, with P). **System episodes:** processing history (layer H). |
| **Procedural** | Rules, methods, reusable procedures | Rulebook, interpretation and canonicalization rules, construction patterns, validation procedures, prescriptive compositions (`DIRECT`) |

All three use the same concept IDs where appropriate, so an event record references a concept without duplicating its definition. A processing rule can be updated independently of factual knowledge [F1-C §7].

### 10.5.2 Reconciling two source statements (Enhancement E-87, E-88)

**Processing history placement (E-87).** F1-C §7 lists PROCESSING_HISTORY under episodic memory. F1-C §19 says processing-history data "should remain separate from factual knowledge about the world". Both hold if episodic memory has **two partitions that never mix**:

| Partition | Content | Store | Rule |
|---|---|---|---|
| World episodes | What sources said happened | Layers I + P | Subject to epistemic status (Part 6) |
| System episodes | What the system did and how it went | Layer H | No world assertions (invariant I-14), no source text |

**Frame templates placement (E-88).** F1-C §7 puts FRAME_TEMPLATES in procedural memory. Part 4 stores FrameDefinitions in the dictionary as declarative content about situations. Both views are needed: the Interpretation controller *uses* frames procedurally. Resolution: **one stored copy, two logical views.** The definition lives once in D (semantic memory). The procedural view is an index of how to apply it: valence patterns, construction patterns, perspective variants, canonicalization rules. Those artifacts reference the frame by ID and version and live in the Rulebook and lexicon.

### 10.5.3 Three storage tiers

[F3-A §6.32; F1-C §9] Orthogonal to memory type, the data has three physical tiers:

| Tier | Contents | Properties |
|---|---|---|
| **A: Authoritative semantic knowledge** | Concept definitions, frame definitions, formal rules, ontology versions, validated assertions, evidence records | Source of truth. Versioned, audited. |
| **B: Optimized persistent representation** | Compact concept references, packed frame records, sparse graph relationships, local dictionaries, compressed blocks, indexes | Derived from A. Rebuildable. Detailed in Part 11. |
| **C: Active cognitive memory** | Recently accessed concepts, active semantic subgraphs, current task context, cached inferences, relevant frames | In RAM, bounded. Disposable. |

The Memory Manager retrieves; the Semantic Grammar gives everything one consistent meaning; the Binary Encoder decides how to store it. Meaning, processing, and storage stay separate [F3-A §6.32].

### 10.5.4 Memory Manager interface

```text
MemoryManager  (read-only to everyone except via the sole writers)
  get_concept(id, scope)           → ConceptView   (follows active mappings in scope, Part 7 §7.8)
  get_frame(id, version)           → FrameView     (with inherited roles resolved, cached)
  lexical_lookup(form, language)   → LexicalSense[]
  structural_candidates(query)     → candidates   (Part 7 R3)
  embedding_candidates(text, k)    → candidates   (Part 7 R4)
  neighborhood(seeds, profile, budget) → SubgraphSnapshot   (§10.7.2), immutable and version-stamped
  cross_domain_hint(concept)       → partner domains, counts
  trusted_view_query(...)          → claims with status   (Part 6 §6.7)
  stats()                          → hit rates, sizes, heat
```

---

## 10.6 Partitioned memory

### 10.6.1 Identity versus residency

[F1-C §8] **Universal semantic IDs do not require universal simultaneous memory residency.** A concept can be globally recognizable without all its relations sitting in one structure. This separates *universal semantic identity* from *universal semantic storage*, and it is how the design avoids recreating the enormous centralized dictionary [F1-C intro].

```text
                      GLOBAL CONCEPT REGISTRY  (compact index)
        ┌───────────────┬────────────────┬───────────────┬─────────┐
     UNIVERSAL_CORE   PHYSICS   CHEMISTRY   BIOLOGY   MEDICINE   ENGINEERING ...
        └───────────────┴────────────────┴───────────────┴─────────┘
                 shared concept IDs        ▼
                                      ACTIVE CACHE
```

The registry holds the compact record of Part 2 §2.13. Detailed relations stay in domain stores [F2-C §5.21].

### 10.6.2 Domains

Domains are **non-semantic tags** (Part 2 §2.13). Identity never depends on domain.

```text
Domain   domain_id, name, parent_domain?, status, notes
         initial set: UNIVERSAL_CORE, LANGUAGE, PHYSICS, CHEMISTRY, BIOLOGY, MEDICINE, ENGINEERING, ECONOMICS
```

- **UNIVERSAL_CORE** holds the Foundation Package (kinds, tier-1 roles, FN functions, layer-1 frames, seed classes). It is **pinned** and always resident.
- A concept has a **primary domain** and any number of additional domains (ENERGY: physics primary; biology and engineering additional) [F1-C §8].
- A relation row carries the domain in which it was asserted, `(source_id, relation_id, target_id, domain_id)` [F1-D §2.14]. Domain-specific relations such as ENERGY–WORK (physics), ENERGY–METABOLISM (biology), and ENERGY–EFFICIENCY (engineering) share the one concept ID [F1-D §2.13].
- Domain assignment is made by the producer at import or extraction (frame domain, resource tag, source genre) and confirmed in review. It is not inferred from the ID or from word similarity.

### 10.6.3 Cross-domain relations (Enhancement E-93)

[F1-D §2.13] Some relations cross boundaries: `BIOLOGICAL_CELL USES CHEMICAL_ENERGY` spans biology and chemistry. The source calls for "an index that can locate related concepts across domain boundaries". The mechanism:

1. **Ownership.** A relation is stored in the domain of its **source concept's primary domain** (or the domain tag given at assertion), and flagged `xdom` when the target's primary domain differs.
2. **CrossDomainIndex** in the registry: `(concept_id, partner_domain, edge_count)`. Before loading a neighbourhood the loader consults it, so it knows which other partitions to touch.
3. **Bounded traversal.** Neighbourhood retrieval follows `xdom` edges only if the budget allows and the relation's retrieval gain justifies it. The domain partitions loaded are a **subset** chosen by the seeds' domains plus a cross-domain allowance.

### 10.6.4 Physical partitioning

[F1-D §2.24] Start with **one SQLite database** with a `domain_id` column and indexes. Partition physically only if measurements justify it. Triggers to measure [Provisional]: database size exceeding what the page cache can serve efficiently, working-set misses above a threshold, or write contention.

If partitioned: one file per domain, opened lazily with `ATTACH DATABASE`. SQLite limits the number of attached databases (a compile-time default), so there is a cap on simultaneously open partitions, and an LRU of open partitions evicts idle ones. That limit is part of the technology verification gate (Part 12).

---

## 10.7 Retrieval, activation, and caching

### 10.7.1 Two different "activations" (Enhancement E-90)

The source uses "activation" for two separate ideas [F1-C §9; F1-D §2.16]. They are kept apart:

| | Spreading activation | Usage heat |
|---|---|---|
| Purpose | Choose a *relevant neighbourhood* for **this task** | Decide what stays **cached** across tasks |
| Lifetime | The task | Long-term, decays |
| Stored in | Workspace (ephemeral) | `UsageStats` table, separate from knowledge records |
| Inputs | Seeds, relation gains, associative weights | Access counts and recency |
| Affects | Which records are loaded and ranked | Cache tier and eviction order |

**SG-KNW-007 (Normative).** Activation scores and usage heat influence **retrieval order and cache placement only.** They MUST NOT influence validity, evidence vectors, epistemic status, risk class, or promotion. "A frequently repeated misconception is still a misconception" [F1-C §9]. These values are not stored in knowledge records, and they are not read by validators or the Promotion Controller.

### 10.7.2 Bounded spreading activation (Enhancement E-11, completed)

The source gives `A_{t+1}(v) = αA_t(v) + Σ_{u∈N(v)} w_{uv} A_t(u)` and says that without normalization, pruning, or limits repeated propagation could produce undesirable results [F1-D §2.16]. Problems: activation can grow without bound, hubs dominate, and relation types are ignored. The specified version:

```text
Inputs:   seeds S (from lexical lookup of the unit), retrieval profile P, budget B
Per edge u→v:  strength s_uv = w_uv · g_P(type(r_uv))          # associative weight × relation-type gain
               Z_u = Σ_{x ∈ top_f(Out(u))} s_ux                # out-normalizer, fan-out capped at f
               ŵ_uv = s_uv / Z_u            (0 if v not in top_f(Out(u)))
Update:   A_{t+1}(v) = min( 1, α·A_t(v) + (1−α)·Σ_{u∈In(v)} ŵ_uv · A_t(u) )   for v ∉ S
          A(v) = 1 for v ∈ S (seeds clamped)
Prune:    drop nodes with A < θ; keep at most k nodes per step; stop at depth D or when max|ΔA| < ε
Output:   ranked neighbourhood + the frontier that was pruned (so adequacy can be assessed)
```

Properties:
- **Out-normalization** makes each node pass on at most its own activation (Σ_v ŵ_uv ≤ 1). With α < 1, total activation mass is non-increasing apart from seed re-injection, so it cannot grow without bound, and `min(1, ·)` caps each node.
- The **fan-out cap** *f* handles hubs. Traversing IS_A *downward* from ANIMAL would otherwise reach millions of subclasses. Downward IS_A gets a low gain and the cap applies.
- LOGICAL and EPISTEMIC relations have **no stored weights** (SG-KNW-002). The retrieval profile `g_P` supplies a traversal gain per relation type. That gain is a *retrieval parameter*, not a property of the knowledge. ASSOCIATIVE edges use their stored weight (with recorded scoring model) times the gain.
- The retrieval profile is chosen by task class: interpretation, validation context, analogy, generalization.

| Relation type | Example gain [Provisional] |
|---|---|
| SUBCLASS_OF (up) | 1.0 |
| HAS_FUNCTION | 0.9 |
| HAS_PART / PHYSICAL_COMPONENT_OF | 0.9 |
| Frame role participation | 0.8 |
| ASSOCIATED_WITH (× stored weight) | 0.6 |
| SUBCLASS_OF (down) | 0.2, fan-out capped |
| Cross-domain edge | × 0.7 additional |

**Worked illustration** (numbers are illustrative): "Why does an engine overheat?" Seeds ENGINE and OVERHEATING, α = 0.5, θ = 0.15, D = 2.

| Edge | s_uv | ŵ |
|---|---|---|
| ENGINE → COOLING_SYSTEM (HAS_PART) | 1.0 | 0.833 |
| ENGINE → ENGINE_HISTORY (ASSOCIATED, w 0.2) | 0.2 | 0.167 |
| OVERHEATING → TEMPERATURE (RELATED, w 0.8) | 0.8 | 1.0 |
| COOLING_SYSTEM → HEAT_REMOVAL (HAS_FUNCTION) | 1.0 | 1.0 |

```text
step 1   COOLING_SYSTEM = 0.5×0.833 = 0.417     TEMPERATURE = 0.5     ENGINE_HISTORY = 0.083 → pruned (<θ)
step 2   TEMPERATURE = 0.75   COOLING_SYSTEM = 0.5×0.417 + 0.417 = 0.625   HEAT_REMOVAL = 0.5×0.417 = 0.208
         ENGINE_HISTORY would be 0.125 → pruned
retrieved: TEMPERATURE, COOLING_SYSTEM, HEAT_REMOVAL.  Frontier (not loaded): COOLANT, RADIATOR, THERMOSTAT, HEAT_TRANSFER
```

The heart-embryology-style long tail is never loaded [F1-C §10]. If a later step needs COOLANT, retrieval expands from the stored frontier.

**A failed retrieval is not proof of non-existence** [F1-C §10]. The output reports `RETRIEVAL_ADEQUACY` (frontier size, best-match strength, expected-roles coverage) so metacognition can request more (Part 6 §6.9), and nothing downstream treats an absent item as "does not exist" (SG-KNW-001).

### 10.7.3 Retrieval flow for a task

```text
1  seeds ← lexical lookup of unit's lemmas (R1–R2, Part 7)
2  profile ← by task class
3  spreading activation → ranked neighbourhood (1 round)
4  candidate frames ← frames whose roles/functions touch the neighbourhood
5  adequacy check → expand (next round) or stop
6  load full records only for items that will be used (lazy), as immutable snapshot
```

### 10.7.4 Usage heat and tiering

[F1-C §9] Memory activation controls accessibility. Frequently used structures stay readily accessible, rarely used ones become less immediately accessible, and **validated knowledge is not deleted**.

```text
heat update on access at time t:   h ← h · exp(−λ (t − t_last)) + 1        λ = ln 2 / half_life [Provisional: days]
```

| Tier | Heat | Where it lives |
|---|---|---|
| Hot | High | RAM cache (Python-side records, resolved frames, active subgraphs) |
| Warm | Medium | SQLite with page cache and indexes: fast local retrieval |
| Cold | Low | Persistent storage and compressed blocks |

Cache policy uses the factors the source lists: frequency, recency, task relevance, retrieval cost, memory consumption, semantic importance [F1-C §9]. A concrete admission and eviction priority, in the spirit of size- and cost-aware policies:

```text
priority(item) = pin(item) ? ∞ : ( heat(item) × rebuild_cost(item) ) / size(item)
```

Pinned items: the Foundation Package, FN functions, tier-1 roles, frames and lexicon for the *currently active domains*, and anything in an active workspace. Eviction removes the lowest priority first. Evicted items remain in the lower tiers.

### 10.7.5 Derived inference cache

[F3-A §6.27] Foundational relations are stored and derivable ones are **not**, unless repeated recomputation costs more than storing them.

```text
InferenceCacheEntry   conclusion, rule_id + version, premise_ids[] (+ their versions), computed_at, hits
```

**SG-KNW-008 (Normative).** A cached inference is **derived and never authoritative.** Each entry is keyed by its premises and rule version and is **invalidated** when any premise is deprecated, mapped, or changed, or when the rule version changes. Frequently used inferences may be materialized, and rarely used ones are computed on demand. The cache never becomes a second source of truth. Physical encoding of materialized relations is Part 11.

---

## 10.8 Reasoning

### 10.8.1 Separation of three tasks

[F1-C §14] "The engine stopped because it overheated." involves three different jobs, and merging them into one opaque model response hides errors:

| Task | Question | Component | Output |
|---|---|---|---|
| Interpretation | What does the sentence assert? | Interpretation controller | Candidate IR: STOP, OVERHEAT, CAUSATION (source-stated) |
| Knowledge retrieval | What is an engine? What is overheating? What mechanisms could connect overheating and stopping? | Knowledge controller (SemanticHub, neighbourhood) | Subgraph snapshot |
| Reasoning | Does the explanation follow from known mechanisms? Could other causes also be possible? | ReasoningModule | Derivations labelled INFERRED |

```text
INPUT → INTERPRETATION → SEMANTIC IR ┬─► KNOWLEDGE RETRIEVAL ┐
                                      └─► REASONING           ┴─► VALIDATION
```

The language model may correctly extract a false statement. A reasoning module may derive a conclusion that is logically valid and built on incomplete knowledge. Keeping the layers separate makes both detectable [F1-C §14]. Rules for understanding language and rules describing the world are different families and never substitute for one another (Part 6 §6.7).

### 10.8.2 The kernel reasoner (Enhancement E-96)

The sources say not to attempt "unrestricted human-like reasoning from the beginning" [F1-C §16] and give only the separation. The kernel therefore specifies a **small, sound, bounded** reasoner:

| Inference | Rule | Premises needed | Output status |
|---|---|---|---|
| Class membership up the hierarchy | SG-KNW-010 | `A SUBCLASS_OF B`, `X INSTANCE_OF A` | INFERRED |
| Inverse relation | SG-KNW-011 | `r(a,b)`, declared inverse | INFERRED (derived, not stored) |
| Transitivity | SG-KNW-012 | relation declared transitive | INFERRED |
| Essential-constraint inheritance | SG-KNW-004 | ESSENTIAL constraints only | INFERRED |
| Frame state entailments | Part 4 §4.4.1 | Instance with perfective or perfect aspect, final-state pattern | INFERRED |
| Function inheritance | new SG-KNW-013 | `HAS_FUNCTION` mode PURPOSE on an ancestor, specialization declared compatible | INFERRED, defeasible |
| Consequence-chain test | Part 9 §9.19.1 | Depth ≤ 3 | Testing only |

**SG-KNW-009 (Normative).**
1. Reasoning uses the **trusted view** by default. Using another scope must be stated and the output carries the attribution (Part 6 §6.7).
2. Every result is INFERRED, carries `support_cap = min(premise levels)` and the premise list (SG-EVD-012). Reasoning never produces VERIFIED.
3. Reasoning is **open-world**. It does not use negation as failure unless the relation or domain declares `CLOSED_WORLD(scope)` (SG-KNW-001).
4. Every inference has a depth limit and a step budget. Termination is guaranteed.
5. A conclusion drawn inside a non-WORLD context stays in that context.
6. An inference that conflicts with a trusted claim is surfaced as a conflict, never silently dropped (Part 6 §6.8).

The sources' causal example: the reasoner may report that "overheating could plausibly cause an engine to stop", INFERRED, with the retrieved mechanism as its premises. The source-stated causal claim stays SOURCE_ASSERTED and is not upgraded by the reasoner's agreement [F2-A §3.13].

Richer reasoning (probabilistic, abductive, analogical hypothesis generation) is deferred. Analogy-based hypotheses already exist as candidates in the Learning plane (Part 9 §9.12) and never enter reasoning as premises.

---

## 10.9 Module catalogue

[F1-B §11 twelve modules; F2-A §3.20 eleven modules] The two source lists are merged. Cost class: L lightweight deterministic, M medium, E expensive (Part 9 §9.18).

| Module | Controller | Responsibility | Cost | Model | Writes |
|---|---|---|---|---|---|
| LinguisticParser (Language Analyzer) | Interpretation | Tokenize, tag, parse (spaCy/Stanza) | L–M | No | Workspace |
| SemanticParser | Interpretation | P1–P8 (Part 8) | M–E | Primary | Candidates |
| FrameResolver | Interpretation | Frame, variant, parameters | L–M | Closed-set | Candidates |
| ContextIntegrator | Interpretation | What a concept means *here* | M | Primary | Candidates |
| EvidenceExtractor | Interpretation | Span alignment, basis labels | L | No | Certificate steps |
| SemanticHub | Knowledge | What concepts could this be, and what is known | L–M | No | None |
| ConceptResolver | Knowledge | Part 7 resolution | M | Closed-set | Proposals to Registry |
| MemoryManager | Knowledge | Retrieval, caching, snapshots | L | No | Caches |
| ReasoningModule | Knowledge | §10.8 | L–M | No | INFERRED candidates |
| TypeChecker | Validation | L2 | L | No | Reports |
| RuleEngine | Validation | Deterministic rule execution, replay | L | No | Reports |
| EvidenceValidator | Validation | L4 | L–M | No | Reports |
| ReviewManager | Validation | Queue, review packages, calibration (Part 6) | M–E | Reviewer | ReviewRecords |
| Metacognition | Central (policy service) | Signals and next action (Part 6 §6.9) | L | **Never** | Decisions |
| Lexical, Concept, Knowledge, Grammar engines | Learning | Part 9 | M–E | Primary | Candidates |
| PatternDiscovery | Learning | Signatures, buckets, counts | M | No | Candidates |
| AnalogyEngine | Learning | StructuralAnalogy, FigurativeMapping proposals | M–E | Reviewer (naming, coherence) | Candidates |
| GeneralizationEngine / CounterexampleEngine | Learning | Part 9 gates and CE1–CE4 | M–E | Reviewer (CE4) | Candidates |
| Compression Optimizer (Semantic Grammar Optimizer) | Learning | Storage decisions (Part 11) | M | No | Storage plans only |
| BinaryEncoder | Knowledge (service) | USBF (Part 11) | L | No | Encoded blocks (derived) |
| Registry Manager | Service | Part 7 §7.10 | L | No | Authoritative IDs |
| Promotion Controller | Governance | Part 9 §9.3.5 | L | No | Authoritative stores |
| Model Gateway | Shared service | §10.3.4 | E | Holds models | Candidate objects only |

**Module contract (Enhancement E-99).** Every module MUST:
1. Publish a `ModuleDeclaration` (§10.2.5), including `proposes[]`. A module may not emit a candidate type it did not declare, and the controller drops undeclared outputs.
2. Be replaceable behind its interface. Replacing the ContextIntegrator's model, the MemoryManager's database, or the AnalogyEngine's algorithm does not change the grammar. "If the AnalogyEngine improves, its proposed abstractions should still be validated using the same rules. The grammar acts as a common contract" [F2-A §3.20].
3. Be stateless between tasks except for declared caches that are regenerable.
4. Report usage in every message.
5. Honour cancellation tokens and timeouts.

---

## 10.10 Metacognition: placement and data flow

Part 6 §6.9 specifies the signals and actions. The architectural placement is:

- Metacognition is a **policy service owned by the central controller**, not a module that calls a model. It reads signals produced by validators, retrieval, and method comparison. It does not produce them [F1-C §12].
- It runs at defined **decision points**: after validation, after retrieval adequacy checks, after reviewer feedback, and at budget thresholds.
- Its outputs are the actions in Part 6 §6.9.3: accept provisionally, retrieve more, retry with an alternate method, request model or human review, preserve ambiguity, reject, defer.
- It consumes calibration data from audits (Part 6 §6.10.3) and writes decision records to process history.
- The questions it monitors [F1-C §12]: was the source ambiguous, did the parser add unsupported details, were multiple interpretations possible, did the proposed concept already exist, did the frame satisfy its constraints, was the needed knowledge retrieved, did independent validation disagree, should a larger model review. Each corresponds to a named signal (Part 6 §6.9.2), so none requires a model's opinion.

---

## 10.11 Prediction and error correction

[F1-C §11] The brain-inspired idea of predictive processing is realized as **expectations derived from the grammar**, without simulating any biological mechanism.

### 10.11.1 Expectations

| Source of expectation | Expected | Violation (prediction error) |
|---|---|---|
| Frame selected | REQUIRED roles are fillable. Typed participants fit. | Missing REQUIRED role evidence, UNDETERMINED or INCOMPATIBLE type |
| Lexical sense | Valence patterns match the parse | Construction mismatch |
| Concept class | Typical relations | Contradiction with trusted knowledge (VC-C06) |
| Metamorphic paraphrase | Same core roles under an equivalent construction | Role mismatch |

A prediction error is a **signal** (Part 6 §6.9.2) that triggers revision, retry, or review. It is never silently ignored and never silently "corrected".

### 10.11.2 Runtime metamorphic checking (Enhancement: SG-INT-013)

Part 5 §5.11 defines metamorphic *tests*. The same machinery can run at runtime as a consistency check:

```text
for unit U with risk class ≥ MEDIUM (or sampled at rate s):
    V ← deterministic transformations of U (e.g. active↔passive via valence patterns)   # Python
    interpret V (cache-aware)                                                          # cost
    compare canonical IR of U and V per the relation table of Part 5 §5.11.2
    mismatch → METHOD_DISAGREEMENT signal
```

Example: the active "The dog chased the cat" and passive "The cat was chased by the dog" must give the same CHASER and TARGET. If the parser outputs `CHASER = CAT, TARGET = DOG` for the passive, the error is detected without a gold annotation [F1-C §11].

Constraints:
- Transformations are **deterministic where possible**. Model-generated paraphrases are weaker evidence because the same model may share the bias.
- Each transformation has explicit assumptions. Not every transformation preserves every detail, for example give/receive perspective, or an agentless passive [F1-C §11].
- The check roughly doubles interpretation cost, so it is used by risk class and sampling, and it is **optional in the kernel** (Part 12). Agreement is not proof of correctness.

---

## 10.12 Process history and self-representation

[F1-C §19] The system can represent and analyze its own operations as structured data. This "does not require consciousness or human-like self-awareness".

### 10.12.1 Storage (Enhancement E-97)

The source suggests recording operations in the same semantic language ("TASK: InterpretSentence, INPUT: Sentence_100, ACTION: ResolveConcepts, RESULT: CandidateSemanticGraph_200, VALIDATION: Failed, REASON: RoleConstraintViolation") [F1-C §19]. Two constraints apply: processing history must stay separate from world knowledge (I-14), and a mechanism has to pass the purpose test (P-24).

Decision:
1. **Layer H is a separate relational store**, append-only. It holds tasks, attempts, errors, signals, routing decisions, rule IDs, versions, timings, and budget use. It holds no source content, no world assertions, and no personal data (Part 6 §6.12.5, §6.13.5).
2. **A structured view** exposes layer H as USG-style frame applications in a reserved `SYSTEM` domain, so the existing pattern-discovery machinery can analyze it. The view is derived. It is not a second copy, and it never enters the claim store.
3. **Frames in the SYSTEM domain** (kernel-optional): `PROCESS_TASK(TASK_TYPE, INPUT_REF, ACTION, RESULT_REF, OUTCOME, REASON_CODE)`, `VALIDATION_OUTCOME`, `ERROR_EVENT`, `ROUTING_DECISION`. These frames are defined in the dictionary like any other, with domain `SYSTEM`.
4. Semantic encoding of H is **deferred past the kernel**. The kernel needs relational tables only, and the view is added when pattern analysis of failures shows it is worth the complexity.

### 10.12.2 What the system can learn from its own history

[F1-C §19] Examples of patterns the learning controller can mine (as candidates, with minimum counts):

```text
"Passive sentences frequently cause role assignment errors."
"Concept resolution performs poorly when several meanings share similar contexts."
```

A learning controller can then identify areas needing improved rules or additional training examples (Part 9 §9.14). Process-history patterns and world-knowledge patterns stay in separate stores and never mix.

---

## 10.13 Resource management

### 10.13.1 Six restrictions

[F3-C §8.25] Binding architectural restrictions:

| # | Restriction | How it is enforced |
|---|---|---|
| 1 | The full semantic database stays on disk. Only relevant concepts, frames, and neighbourhoods are in RAM. | Memory Manager, lazy loading (§10.7) |
| 2 | AI models are shared services | SG-GOV-010 |
| 3 | Graph operations use bounded subgraphs | `neighborhood()` budgets, MAX_STRUCT_NODES (Part 9 §9.11) |
| 4 | Embeddings are retrieved selectively | Domain-partitioned vector indexes loaded on demand (Part 7 §7.4.2) |
| 5 | Learning is separated from ordinary retrieval | Priority classes and background scheduling (§10.13.4) |
| 6 | Processing budgets are explicit | SG-GOV-009 |

**SG-GOV-009 (Normative).** Every task has a budget and every queue is bounded. Budgets cover [F3-C §8.25]: maximum model calls, maximum candidate concepts, maximum graph traversal depth, maximum retries, maximum memory consumption, and maximum wall time. Exhausting a budget ends the task with a result (UNRESOLVED, DEFER, or partial), never an unbounded continuation. Budgets are configurable and adjusted by benchmarking.

### 10.13.2 Memory budget worksheet (Enhancement E-94)

The sources fix the constraint and not the arithmetic, so the specification supplies a worksheet. All numbers are illustrative and must be replaced by measurement.

```text
M_budget  =  f_safe × RAM                               f_safe [Provisional] ≈ 0.8, leaving headroom for the OS
M_used    =  M_os + M_python + M_model + M_embed + M_cache + Σ M_workspace + M_workers + M_sqlite_cache
```

| Component | How to estimate | Illustrative |
|---|---|---|
| Model weights | parameters × bits/8 (plus runtime overhead and KV cache growing with context length) | 7B parameters at 4 bits ≈ 3.5 GB weights, roughly 4.5–5 GB resident with overhead |
| Embedding model | Small dedicated model | ≈ 0.1–0.5 GB |
| Vector index | `dim × 4` bytes per concept (float32) | 384 dims → 1,536 B per concept. 1 M concepts ≈ 1.5 GB if fully resident (Part 7 §7.4.2) |
| Entity caches | records × average record size | bounded by cache policy |
| SQLite page cache | `cache_size` setting | A few hundred MB |
| Workspaces | active workspace count × items × size | small. Bounded by capacity (§10.4.3). |
| Worker processes | per-process interpreter + data | Number of workers × (hundreds of MB) |

Example on a 16 GB machine without a GPU: 0.8 × 16 ≈ 12.8 GB budget, of which the OS, Python, and tooling take ≈ 3 GB, the 7B model ≈ 5 GB, the embedding model and page cache ≈ 1 GB, leaving ≈ 3–4 GB for caches, workspaces, and workers. A 13B model would not fit comfortably under the same budget. That is why model size is chosen by benchmark and hardware (Part 8 §8.11.6) and why Model B (reviewer) may be remote or loaded on demand and unloaded again.

### 10.13.3 Governor and degradation ladder

A **resource governor** samples memory, queue depths, latency, and CPU, and applies admission control. When pressure rises it degrades in a fixed order, so quality loss is explicit and logged:

| Pressure | Response |
|---|---|
| Cache > cap | Evict by priority (§10.7.4) |
| Memory > soft limit | Shrink workspace capacity and candidate set sizes, reduce worker count |
| Model queue deep | Hold low-priority tasks, suspend learning cycles |
| Memory > hard limit | Unload optional components (reviewer model, vector index partitions), pause intake, drain workspaces |
| Sustained overload | Reject new work with a retry-after. Never accept unbounded work. |

Degraded operation records `degraded=true` in the task, and affected units are tagged so audits can account for reduced quality.

### 10.13.4 Priority classes and fair scheduling

[F3-C §8.17] These are *scheduling priorities*, not tasks that must run continuously.

| Class | Work | Notes |
|---|---|---|
| P1 | Complete the current semantic interpretation | Interactive. Reserved share. |
| P2 | Resolve ambiguous concepts | |
| P3 | Review candidate generalizations | Background |
| P4 | Background grammar optimization, duplicate sweeps, reprocessing | Runs only when capacity is idle or within its quota |

Rules: a reserved minimum share for P1, aging so P3/P4 are not starved indefinitely when idle capacity exists, and **learning is paused automatically** when P1 latency exceeds its target (Part 9 §9.15.2 stop conditions). Expensive operations are **queued, batched, or selectively invoked**. The system is not designed around continuously running every cognitive module [F3-B §7.31].

### 10.13.5 Observability

Every task and message carries `task_id` and usage figures. The system exposes: queue depths, p50/p95 latency per task type, model calls and tokens per unit, cache hit rates per tier, peak RAM, SQLite WAL size, DB growth, dead-letter count, degraded-mode time. These feed the benchmark metrics (Part 12) and the cycle reports (Part 9).

---

## 10.14 Durability and recovery (Enhancement E-95)

| Item | Approach |
|---|---|
| Interactive tasks | In-memory queue, but each unit's input and idempotency key are in the ingest ledger first |
| Background and batch tasks | **Durable queue** (SQLite table): `task_id, type, state, attempts, next_run_at, payload_ref` |
| Workspaces | Ephemeral. The document discourse layer is checkpointed per unit (§10.4.6) |
| Commits | Transactional. Atomic bundles (Part 9 §9.3.4). A crash leaves either the old or the new state. |
| Restart | Reload durable queue, requeue tasks in RUNNING state with attempts+1, skip completed idempotency keys |
| Poison tasks | Dead-letter after N attempts [Provisional: 3], with reason |
| Derived data | Caches, inference cache, embeddings, signatures: **rebuildable**. A corrupt derived store is deleted and regenerated. |
| Backups | Versioned snapshots of authoritative stores and the rulebook, hash-recorded (SG-SEC-009) |

Reprocessing after grammar changes follows the ledger and impact classes in Part 9 §9.15.3. It is a background job under P4, resumable, and idempotent.

---

## 10.15 What is not carried forward, build order, and decisions

### 10.15.1 Excluded or postponed

[F1-C §16]

| Idea | Decision | Reason |
|---|---|---|
| Neuron-level simulation | Excluded | Unnecessary. "Useful computational abstractions, not a biological simulation." |
| A separate AI model for every cognitive module | Excluded | Would overwhelm a personal computer. Shared models and deterministic algorithms. |
| Continuous autonomous rewriting of the grammar | Excluded | Risks inconsistency and drift. Changes pass validation and version control. |
| Treating activation strength as reliability | Excluded | SG-KNW-007 |
| Unrestricted human-like reasoning from the start | Postponed | §10.8.2 limits the kernel reasoner |
| Simulating every brain region | Excluded | "Biological resemblance is not sufficient justification for architectural complexity" |

### 10.15.2 Build order

[F1-C §18; F3-C §8.29] Five stages, mapped to this specification and to the kernel (Part 12):

| Stage | Content | Specified in | Kernel |
|---|---|---|---|
| 1. Formal semantic foundation | Grammar, types, frames, relations, validation rules, IR | Parts 2–5 | Yes |
| 2. Cognitive processing foundation | Central controller, workspace, interpretation modules, basic reasoning | Parts 8, 10 | Yes (simplified: one controller process, one workspace per unit) |
| 3. Memory and retrieval architecture | Domain partitions, global registry, sparse retrieval, caching | Parts 7, 10, 11 | Partial (single DB, registry, lexical + basic neighbourhood retrieval) |
| 4. Learning and generalization | Cross-domain matching, pattern discovery, candidate frames, controlled expansion | Part 9 | Deferred (candidate generation only) |
| 5. Compression and optimization | Binary encoding, frequent-pattern compression, advanced retrieval | Part 11 | Straightforward serialization first |

"We first need semantic representations worth compressing. Otherwise, we risk optimizing a structure that later needs fundamental changes" [F1-C §18].

### 10.15.3 Critical decisions

[F1-C §17] Every row of the source's non-negotiable decisions, with its specification:

| Decision | Rule in the sources | Specified in |
|---|---|---|
| Core representation | Semantic Grammar is the shared internal language | P-01; Parts 2–3 |
| Control | One central controller coordinates specialized assistant controllers | §10.2 |
| Execution | Asynchronous where useful, bounded resource consumption | §10.3.6, §10.13 |
| AI models | Shared services, not duplicate instances | SG-GOV-010 |
| Knowledge identity | Stable, versioned concept IDs | Part 2 §2.4; Part 7 |
| Knowledge organization | Global registry with partitioned domain knowledge | §10.6 |
| Memory | Persistent semantic, episodic, procedural stores | §10.5 |
| Retrieval | Sparse, task-relevant activation | §10.7 |
| Validation | Deterministic checks plus evidence-based review | Parts 5–6 |
| Learning | Candidate-first, controlled promotion | Part 9 |
| Generalization | Typed structural matching, analogy, counterexamples | Part 9 |
| Compression | Optimize actual stored representations, not only ID length | Part 11 |
| Reliability | Preserve uncertainty. Distinguish extracted claims from verified facts. | Parts 5–6 |

**Open design issue resolved.** F1-C §17 left open whether the internal representation should be a typed graph, a recursive expression language, a frame structure, or a hybrid. The decision: a **hybrid**. The logical model is a **typed, recursive graph** (Part 2); **frame application** is the compositional construction (Part 3); the **expression language** is the canonical authoring and exchange syntax; **relational tables** are the initial physical storage (Part 11). This matches the source's stated preference for "a typed, graph-based semantic intermediate representation with reusable frames" [F1-C §17], now with the trade-offs worked out: compact storage and efficient relationship retrieval come from relational indexes over the graph.

### 10.15.4 Risk register

[F1-C §20] The sources name four main risks. Each has a concrete mitigation in this specification:

| Risk | Mitigation |
|---|---|
| Architectural complexity | Kernel scope (Part 12). One process, few modules at first. Module contracts. Purpose test (P-24). |
| Unreliable semantic interpretation | Parts 5–6: certificates, five-level validation, closed-set model tasks, review, calibration, audit sampling |
| Expensive graph maintenance | Bounded matching, generalization budgets, derived data rebuildable, learning in background |
| A detailed representation that costs more storage than expected | Total-cost measurement (Part 11), benchmark against conventional compression, and the option to keep only the compact form |

---

## 10.16 Closure of source items in this part

| Source item | Closed in |
|---|---|
| Hierarchical controllers by cognitive responsibility (F1-C §3) | §10.2 |
| Shared model service with bounded queue (F1-C §3, F3-C §8.17) | §10.3.4 |
| Cognitive Workspace, versioned candidates (F1-C §4, F1-D §2.10–2.11) | §10.4, §10.3.3 |
| SemanticHub and ContextIntegrator (F1-C §5) | §10.9; Part 7 §7.4.3 |
| Memory types (F1-C §7) | §10.5 |
| Universal identity vs storage; registry and domain graphs (F1-C §8) | §10.6 |
| Activation, tiers, decay (F1-C §9) | §10.7.1, §10.7.4 |
| Sparse activation (F1-C §10, F1-D §2.16) | §10.7.2 |
| Sparse graph storage and weights (F1-D §2.14–2.15) | §10.7.2; Part 2 §2.8; Part 11 |
| Prediction and metamorphic testing (F1-C §11) | §10.11 |
| Metacognition (F1-C §12) | §10.10; Part 6 §6.9 |
| Separate interpretation, knowledge, reasoning (F1-C §14) | §10.8 |
| Unified architecture diagram (F1-C §15) | Part 1 §1.6; §10.2–§10.9 |
| What not to carry forward (F1-C §16) | §10.15.1 |
| Critical decisions and development stages (F1-C §17–18) | §10.15.2–§10.15.3 |
| Processing history as structured data (F1-C §19) | §10.12 |
| Shared memory ≠ shared mutable objects (F1-D §2.12) | §10.3.1 |
| Asynchronous execution, asyncio, workers (F3-C §8.16) | §10.3.6 |
| Resource restrictions (F3-C §8.25) | §10.13 |
| Capability-based selection, deterministic controller (F3-C §8.26–8.27) | §10.2.5, §10.2.1 |
| Avoid multi-agent frameworks initially (F3-C §8.28) | §10.3.6 |
| Memory types and compression (F3-A §6.26) and three storage layers (F3-A §6.32) | §10.5.3; Part 11 |
| Physical storage preferences and personal computer (F1-D §2.24) | §10.6.4, §10.13 |

### Rules registered in this part

| Rule | Statement |
|---|---|
| SG-GOV-007 | Only the central controller commits workspace changes, and only the Workspace Manager applies patches |
| SG-GOV-008 | Modules share IDs and immutable snapshots, never mutable objects. Single writer per store. |
| SG-GOV-009 | Every task has a budget and every queue is bounded |
| SG-GOV-010 | One shared model service. No module loads its own model copy. |
| SG-KNW-007 | Activation and usage heat never influence validity, evidence, risk, or promotion |
| SG-KNW-008 | Inference caches are derived, dependency-keyed, invalidated, and never authoritative |
| SG-KNW-009 | Reasoning defaults to the trusted view, outputs INFERRED with support cap, is open-world and bounded |
| SG-KNW-013 | Function inheritance is defeasible and applies to PURPOSE-mode functions only |
| SG-INT-013 | Runtime metamorphic consistency checks are risk-based and sampled |

### Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-11 (completed) | Unbounded activation formula | Out-normalized, fan-out-capped, relation-gain, clamped-seed, thresholded spreading activation (§10.7.2) |
| E-87 | Processing history placed in episodic memory and also required to be separate from world knowledge | Two episodic partitions that never mix (§10.5.2) |
| E-88 | Frame templates listed as both procedural and dictionary content | One stored copy, two logical views (§10.5.2) |
| E-90 | "Activation" meant both per-task relevance and long-term accessibility | Separate mechanisms and an explicit non-influence rule (§10.7.1) |
| E-91 | Priority scheduling presumed a running model call could be preempted | Cooperative preemption, aging, small decomposed calls (§10.3.4) |
| E-92 | Concurrent module results could overwrite each other | Versioned patches, competing candidate groups, conflict signals (§10.3.3) |
| E-93 | Cross-domain relation placement was unspecified | Ownership rule and CrossDomainIndex (§10.6.3) |
| E-94 | No arithmetic for fitting on a personal computer | Memory worksheet, governor, degradation ladder (§10.13) |
| E-95 | Crash recovery and background durability were unspecified | Durable queue, idempotency, checkpoints, dead-letter, rebuildable derived data (§10.14) |
| E-96 | The reasoning module was named but not defined | Bounded kernel reasoner with explicit inference rules and outputs (§10.8.2) |
| E-97 | Self-representation of operations conflicted with keeping process history separate | Separate H store with a derived structured view, semantic encoding deferred (§10.12) |
| E-98 | `asyncio` is not enough for CPU-bound work, and SQLite has connection and writer constraints | Process layout with worker pool, dedicated writer, per-thread readers (§10.3.6) |
| E-99 | Modules had no formal contract | `ModuleDeclaration` and module obligations (§10.9) |


---


# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 11 of 12: Storage Schema and Binary Encoding (USBF)

Earlier parts defined what is stored. This part defines how: the relational schema that holds authoritative records, the binary container format (USBF) for compact export and cold storage, and the measurement discipline that decides whether any of it is worth having. The source is blunt about the order of questions. First: *where can semantic compression actually beat conventional encoding, and where can it not?* Only then: what should the format look like? [F3-A intro]. The format specified below is a design to be measured. It makes no claim to beat a general-purpose compressor.

---

## 11.1 Objective and honest framing

### 11.1.1 Three representations of one sentence

[F3-A §6.1]

| Representation | Example | Purpose |
|---|---|---|
| A. Natural-language text | `The doctor gave the patient medication.` | Exact wording, human communication |
| B. Semantic structure | `GIVE(AGENT/SOURCE: doctor, RECIPIENT: patient, THEME: medication)` | Reasoning, retrieval, validation |
| C. Binary semantic representation | A few dozen bytes plus shared dictionaries | Efficient storage and transmission of B |

C is not guaranteed to be smaller than A. The text carries definiteness, tense, and lexical choice that a semantic structure may not preserve, so a smaller C can simply mean information was discarded.

### 11.1.2 Two different goals

| Goal | Preserves | Compared against |
|---|---|---|
| **Semantic compression** (semantic mode) | Selected meaning. Wording may be lost. | Other semantic encodings, and conventional compression *with the loss acknowledged* |
| **Lossless text compression** (reversible mode) | Every byte of the original text | General-purpose compressors |

USG's purpose is the first (Part 1 §1.3). The second is a possible extension (§11.15).

### 11.1.3 What the format must not claim

[F3-A §6.28] If the only goal were to shrink millions of English words on disk, a conventional compressor would be a much simpler starting point than a semantic parser. Semantic parsing, concept resolution, frame selection, evidence tracking, validation, and graph maintenance are costs that are justified only if the system must *reason about* stored information. Accordingly:

1. USBF is a **derived, optimized representation** of validated IR. It is never the source of truth (SG-ENC-008).
2. Compression performance is reported against strong baselines (§11.17), with all overheads included.
3. The format may be dropped in favour of relational storage plus a general compressor if the benchmark says so. That outcome is acceptable.

---

## 11.2 Storage architecture

### 11.2.1 Three layers

[F3-A §6.32; Part 10 §10.5.3]

```text
 TIER A  AUTHORITATIVE SEMANTIC KNOWLEDGE     relational tables (§11.3) ── source of truth
            │ derive (deterministic, repeatable)
 TIER B  OPTIMIZED PERSISTENT REPRESENTATION  USBF blocks, codebooks, indexes, CSR snapshots (§11.5–§11.13)
            │ load on demand
 TIER C  ACTIVE COGNITIVE MEMORY              RAM caches, active subgraphs, workspaces (Part 10)
```

### 11.2.2 Where each record category lives

| Records | Kernel | Later (if measurements justify) |
|---|---|---|
| Dictionary: concepts, definitions, relations, roles, frames, rules, mappings | Relational tables | Unchanged (small, read-heavy) |
| Lexicon | Relational tables + FTS5 | Unchanged |
| Instances and assertions (warm) | Relational rows | Unchanged for recent data |
| Instances and assertions (cold, rarely read) | Relational rows | **USBF blocks** with a stub row `assertion_id → (block_id, node)` so metadata queries still work |
| Provenance, certificates | Relational, with COMPACT retention (Part 5 §5.8.4) | COMPACT certificates inside blocks |
| Process history, ingest ledger, queue, audit log | Relational, append-only | Unchanged |
| Embeddings, vector index | BLOB table; exact search | Index structure (FAISS) when needed |
| Export bundles, archives | USBF | n/a |

Moving cold data to USBF reflects the source's tiering of warm (fast local retrieval) and cold (persistent storage) data [F1-C §9]. It happens only after a benchmark shows a net benefit (§11.17).

### 11.2.3 Storage-backend interface

All modules use a `RecordStore` interface (`get`, `scan`, `put` on sole-writer paths). The relational backend implements it first. A USBF-backed implementation of the *read* side is added for cold data. Replacing SQLite later changes only the backend [F1-D §2.5].

---

## 11.3 The relational schema (SQLite)

### 11.3.1 Principles

[F1-D §2.5, §2.14, §2.24; F3-C §8.10]

- **The graph is the logical model.** Nodes and edges are rows. No dedicated graph database until a benchmark demonstrates need.
- **Each ID space has its own table.** The ID is the primary key and is allocated only by the Registry Manager (Part 7 §7.10). No record is deleted, so `INTEGER PRIMARY KEY` values are never reused. Retirement writes a tombstone (SG-FND-006).
- **Sparse by design.** Only relationships that exist are stored.
- **Derived data is separate.** Inverse edges, inference caches, embeddings, signatures, and caches are rebuildable and carry the version that built them.
- Strict typing (`STRICT` tables) and foreign keys are on. These need a SQLite version that supports them, which is part of the technology verification gate (Part 12).

### 11.3.2 Connection settings

```sql
PRAGMA journal_mode = WAL;        -- many readers, one writer (Part 10 §10.3.6)
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous  = NORMAL;     -- general connections
-- the Registry Manager's writer connection uses:  PRAGMA synchronous = FULL;  and BEGIN IMMEDIATE
```

WAL with `NORMAL` can lose the most recent transactions after power loss but does not corrupt the database. Authoritative commits use `FULL`.

### 11.3.3 Core tables

Illustrative DDL. Column lists are complete for the kernel and omit only housekeeping fields.

```sql
-- ID allocation and registry ------------------------------------------------------------
CREATE TABLE id_sequence (
  space   TEXT PRIMARY KEY,                -- CONCEPT, FRAME, ROLE, RELATION, REFERENT, INSTANCE, ...
  next_id INTEGER NOT NULL CHECK (next_id > 0)
) STRICT;

CREATE TABLE registry_entry (
  space          TEXT    NOT NULL,
  id             INTEGER NOT NULL CHECK (id > 0),
  record_kind    TEXT    NOT NULL,
  sem_kind       TEXT,
  status         TEXT    NOT NULL,         -- lifecycle stage (axis C)
  version        INTEGER NOT NULL,
  primary_domain INTEGER,
  tombstone      INTEGER NOT NULL DEFAULT 0 CHECK (tombstone IN (0,1)),
  replaced_by    INTEGER,                  -- migration target when tombstoned
  PRIMARY KEY (space, id)
) STRICT, WITHOUT ROWID;

-- Dictionary: concepts ------------------------------------------------------------------
CREATE TABLE concept (
  concept_id        INTEGER PRIMARY KEY,
  sem_kind          TEXT NOT NULL,          -- Part 2 §2.2
  canonical_label   TEXT,
  definition_status TEXT NOT NULL CHECK (definition_status IN ('COMPLETE','INCOMPLETE')),
  status            TEXT NOT NULL,
  version           INTEGER NOT NULL,
  grammar_version   TEXT NOT NULL,
  ontology_release  TEXT NOT NULL
) STRICT;

CREATE TABLE concept_domain (
  concept_id INTEGER NOT NULL REFERENCES concept(concept_id),
  domain_id  INTEGER NOT NULL,
  is_primary INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (concept_id, domain_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE concept_definition (
  definition_id   INTEGER PRIMARY KEY,
  concept_id      INTEGER NOT NULL REFERENCES concept(concept_id),
  def_version     INTEGER NOT NULL,
  scope           TEXT NOT NULL,            -- Part 7 §7.7
  valid_from      TEXT NOT NULL,            -- ontology release
  superseded_by   INTEGER REFERENCES concept_definition(definition_id),
  content_hash    BLOB NOT NULL,
  UNIQUE (concept_id, def_version, scope)
) STRICT;

CREATE TABLE definition_constraint (
  constraint_id  INTEGER PRIMARY KEY,
  definition_id  INTEGER NOT NULL REFERENCES concept_definition(definition_id),
  class          TEXT NOT NULL CHECK (class IN ('ESSENTIAL','TYPICAL','CONTINGENT','CONTEXTUAL')),
  provenance     TEXT NOT NULL CHECK (provenance IN ('DEFINITIONAL','EMPIRICAL','ASSUMED')),  -- SG-KNW-006
  expr           TEXT NOT NULL CHECK (json_valid(expr)),                                       -- Part 3 §3.19
  evidence_id    INTEGER
) STRICT;

-- Lexicon -------------------------------------------------------------------------------
CREATE TABLE lexical_entry (
  entry_id   INTEGER PRIMARY KEY,
  lemma      TEXT NOT NULL,
  language   TEXT NOT NULL,
  pos        TEXT,
  entry_kind TEXT NOT NULL CHECK (entry_kind IN ('WORD','MULTI_WORD','IDIOM')),
  UNIQUE (lemma, language, pos, entry_kind)
) STRICT;

CREATE TABLE lexical_sense (
  sense_id        INTEGER PRIMARY KEY,
  entry_id        INTEGER NOT NULL REFERENCES lexical_entry(entry_id),
  sense_no        INTEGER NOT NULL,
  mapping         TEXT NOT NULL CHECK (mapping IN ('EXACT','BROADER','NARROWER','PARTIAL')),
  domain_tags     TEXT,
  source_resource TEXT,
  external_id     TEXT,
  UNIQUE (entry_id, sense_no)
) STRICT;

CREATE TABLE sense_concept (
  sense_id   INTEGER NOT NULL REFERENCES lexical_sense(sense_id),
  concept_id INTEGER NOT NULL REFERENCES concept(concept_id),
  PRIMARY KEY (sense_id, concept_id)
) STRICT, WITHOUT ROWID;

-- Frames --------------------------------------------------------------------------------
CREATE TABLE frame_def (
  frame_id       INTEGER NOT NULL,
  frame_version  INTEGER NOT NULL,
  name           TEXT NOT NULL,
  layer          INTEGER NOT NULL CHECK (layer BETWEEN 1 AND 3),
  authority      TEXT NOT NULL CHECK (authority IN ('GRAMMAR','DOMAIN')),
  situation_kind TEXT NOT NULL,
  abstract       INTEGER NOT NULL DEFAULT 0,
  status         TEXT NOT NULL,
  content_hash   BLOB NOT NULL,
  n_roles        INTEGER NOT NULL,          -- fixes bitmap length for this version (§11.8)
  PRIMARY KEY (frame_id, frame_version)
) STRICT, WITHOUT ROWID;

CREATE TABLE frame_role (
  frame_id       INTEGER NOT NULL,
  frame_version  INTEGER NOT NULL,
  role_index     INTEGER NOT NULL,          -- append-only (SG-FRM-006)
  role_id        INTEGER NOT NULL,
  requiredness   TEXT NOT NULL CHECK (requiredness IN ('REQUIRED','OPTIONAL')),
  card_min       INTEGER NOT NULL DEFAULT 1,
  card_max       INTEGER NOT NULL DEFAULT 1,    -- for multi-valued roles (e.g. INPUTS)
  expected_kind  TEXT NOT NULL,
  expected_class INTEGER,                       -- concept id
  PRIMARY KEY (frame_id, frame_version, role_index),
  FOREIGN KEY (frame_id, frame_version) REFERENCES frame_def(frame_id, frame_version)
) STRICT, WITHOUT ROWID;

-- Rules ---------------------------------------------------------------------------------
CREATE TABLE rule_def (
  rule_id    TEXT NOT NULL,                 -- 'SG-CON-002'
  version    INTEGER NOT NULL,
  kind       TEXT NOT NULL,
  authority  INTEGER NOT NULL CHECK (authority IN (1,2,3)),
  spec       TEXT NOT NULL CHECK (json_valid(spec)),
  status     TEXT NOT NULL,
  released_in TEXT NOT NULL,
  PRIMARY KEY (rule_id, version)
) STRICT, WITHOUT ROWID;

-- Sources and instances ----------------------------------------------------------------
CREATE TABLE source (
  source_id    INTEGER PRIMARY KEY,
  type         TEXT NOT NULL,
  language     TEXT,
  text_hash    BLOB NOT NULL,
  anchor       TEXT CHECK (anchor IS NULL OR json_valid(anchor)),   -- Part 2 §2.12
  trust_tier   TEXT NOT NULL CHECK (trust_tier IN ('QUARANTINE','STANDARD','TRUSTED')),
  sensitivity  TEXT NOT NULL,
  genre        TEXT,
  stored_text  BLOB,                         -- compressed; immutable once registered
  text_codec   TEXT
) STRICT;

CREATE TABLE referent (
  referent_id   INTEGER PRIMARY KEY,
  source_id     INTEGER NOT NULL REFERENCES source(source_id),
  sem_kind      TEXT NOT NULL,
  number        TEXT NOT NULL,              -- SINGULAR | PLURAL | MASS | UNSPECIFIED
  cardinality   TEXT,                       -- exact, range, or NULL
  genericity    TEXT NOT NULL,
  scope         TEXT NOT NULL,              -- DISCOURSE_LOCAL | RESOLVED_INDIVIDUAL
  introduced_in TEXT NOT NULL,              -- Part 8 §8.7.2
  span_start    INTEGER, span_end INTEGER
) STRICT;

CREATE TABLE referent_class (
  referent_id INTEGER NOT NULL REFERENCES referent(referent_id),
  concept_id  INTEGER NOT NULL REFERENCES concept(concept_id),
  PRIMARY KEY (referent_id, concept_id)
) STRICT, WITHOUT ROWID;

CREATE TABLE frame_instance (
  instance_id    INTEGER PRIMARY KEY,
  frame_id       INTEGER NOT NULL,
  frame_version  INTEGER NOT NULL,
  source_id      INTEGER NOT NULL REFERENCES source(source_id),
  certificate_id INTEGER,
  FOREIGN KEY (frame_id, frame_version) REFERENCES frame_def(frame_id, frame_version)
) STRICT;

CREATE TABLE binding (
  instance_id INTEGER NOT NULL REFERENCES frame_instance(instance_id),
  role_index  INTEGER NOT NULL,
  ord         INTEGER NOT NULL DEFAULT 0,      -- multi-valued roles
  value_state TEXT NOT NULL CHECK (value_state IN
              ('SPECIFIED','UNSPECIFIED','UNKNOWN','NOT_APPLICABLE','WITHHELD')),
  basis       TEXT CHECK (basis IN ('EXPLICIT','GRAMMATICAL','BACKGROUND')),
  filler_type TEXT,                            -- REFERENT | INSTANCE | EXPR | LITERAL | TIME | KIND
  filler_id   INTEGER,
  literal     BLOB,
  PRIMARY KEY (instance_id, role_index, ord)
) STRICT, WITHOUT ROWID;

-- Operator structure around instances: one row per expression node ----------------------
CREATE TABLE expr_node (
  node_id  INTEGER PRIMARY KEY,
  op       TEXT NOT NULL,                      -- NOT, AND, Q, MODAL, TENSE, ATTRIBUTE, ALT, ...
  params   TEXT CHECK (params IS NULL OR json_valid(params))
) STRICT;
CREATE TABLE expr_arg (
  node_id INTEGER NOT NULL REFERENCES expr_node(node_id),
  ord     INTEGER NOT NULL,
  arg_type TEXT NOT NULL,                      -- NODE | INSTANCE | REFERENT | CONCEPT | LITERAL
  arg_id  INTEGER,
  PRIMARY KEY (node_id, ord)
) STRICT, WITHOUT ROWID;

CREATE TABLE assertion (
  assertion_id     INTEGER PRIMARY KEY,
  content_type     TEXT NOT NULL,              -- INSTANCE | NODE | EDGE | PROPERTY
  content_id       INTEGER NOT NULL,
  origin           TEXT NOT NULL,
  epistemic_status TEXT NOT NULL,              -- axis D
  commitment       TEXT NOT NULL,              -- Part 6 §6.2
  eval_context     TEXT NOT NULL,
  definition_ref   INTEGER,
  alt_group        INTEGER,
  source_id        INTEGER REFERENCES source(source_id),
  evidence_id      INTEGER,
  lifecycle_stage  TEXT NOT NULL,              -- axis C
  grammar_version  TEXT NOT NULL,
  ontology_release TEXT NOT NULL
) STRICT;
CREATE INDEX assertion_by_content ON assertion(content_type, content_id);
CREATE INDEX assertion_by_source  ON assertion(source_id);

-- Concept-level relations (sparse typed graph) -----------------------------------------
CREATE TABLE relation_edge (
  src_id      INTEGER NOT NULL,               -- concept or referent id (kind from relation_def)
  relation_id INTEGER NOT NULL,
  tgt_id      INTEGER NOT NULL,
  domain_id   INTEGER NOT NULL,               -- Part 2 §2.13, Part 10 §10.6
  xdom        INTEGER NOT NULL DEFAULT 0,     -- target's primary domain differs (Part 10 §10.6.3)
  assertion_id INTEGER REFERENCES assertion(assertion_id),
  weight      REAL,                           -- ASSOCIATIVE only (SG-KNW-002)
  weight_model TEXT,                          -- scoring model that produced it
  status      TEXT NOT NULL,
  PRIMARY KEY (src_id, relation_id, tgt_id, domain_id)
) STRICT, WITHOUT ROWID;
CREATE INDEX edge_by_target ON relation_edge(tgt_id, relation_id);   -- serves derived inverses (SG-KNW-011)

-- Identity ------------------------------------------------------------------------------
CREATE TABLE equivalence_mapping (
  mapping_id   INTEGER PRIMARY KEY,
  from_id      INTEGER NOT NULL,
  to_id        INTEGER NOT NULL,
  relation     TEXT NOT NULL,
  scope        TEXT NOT NULL,
  grade        TEXT NOT NULL,
  status       TEXT NOT NULL,                 -- PROPOSED..ACTIVE..REVOKED (Part 7 §7.8.2)
  version      INTEGER NOT NULL,
  certificate_id INTEGER
) STRICT;
CREATE INDEX equiv_active ON equivalence_mapping(from_id, scope) WHERE status = 'ACTIVE';

-- Audit and operations ------------------------------------------------------------------
CREATE TABLE audit_log (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  at         INTEGER NOT NULL,
  actor      TEXT NOT NULL,                   -- component, never "model"
  event      TEXT NOT NULL,
  ref        TEXT NOT NULL,
  prev_hash  BLOB NOT NULL,
  entry_hash BLOB NOT NULL                    -- hash(prev_hash || canonical entry); SG-SEC-009
) STRICT;
```

Triggers on `audit_log` forbid `UPDATE` and `DELETE` (append-only, SG-FND-006). Lexical search uses an FTS5 table over lemmas and definition text, built as an *external-content* index so text is not stored twice.

### 11.3.4 Other tables (listed, not expanded)

| Table(s) | Contents | Notes |
|---|---|---|
| `domain`, `crossdomain_index` | Domain tags and `(concept_id, partner_domain, edge_count)` | Part 10 §10.6 |
| `role_def`, `relation_def`, `frame_parent`, `frame_constraint`, `frame_component`, `perspective_variant`, `frame_parameter` | Part 4 frame model | Role order via `role_index` |
| `lexical_frame_link`, `construction_pattern` | Valence patterns, graduated patterns | Part 8 §8.5, §8.12 |
| `external_mapping`, `figurative_mapping`, `structural_analogy` | Part 2 §2.14, Part 3 §3.15, Part 4 §4.10.2 | |
| `evidence_vector`, `claim`, `claim_cluster`, `trust_profile`, `evidence_policy` | Part 6 | JSON columns in the kernel |
| `certificate`, `validation_report`, `review_record` | Part 5, Part 6 | `retention_tier` FULL or COMPACT |
| `candidate`, `promotion_record`, `bundle`, `rejected_pattern` | Part 9 | |
| `embedding(concept_id, definition_id, model_id, dim, vec BLOB)` | Part 7 §7.4.2 | Rebuilt on model change |
| `usage_stats(space, id, heat, last_access)` | Part 10 §10.7.4 | Separate from knowledge records (SG-KNW-007) |
| `inference_cache` | Part 10 §10.7.5 | Dependency-keyed, invalidated |
| `ingest_ledger`, `task_queue`, `process_event`, `error_record` | Part 9 §9.15.3, Part 10 §10.14 | Layer H, append-only |
| `usbf_block`, `usbf_codebook`, `usbf_template` | §11.12, §11.13 | Tier B directory |

### 11.3.5 Sparse graph storage and the dense-matrix fallacy

[F1-D §2.14] A dense adjacency matrix over 10⁶ concepts has 10¹² cells, about 1 TB at one byte per cell, and nearly all of them would be empty. Only existing edges are stored, in `relation_edge`.

For graph algorithms on an *active subgraph*, build a compressed sparse row (CSR) structure from rows:

```text
V = number of nodes in the subgraph, E = number of edges
indptr[V+1] (int32) · indices[E] (int32) · rel_type[E] (int16) · weight[E] (float32, optional)
bytes ≈ 4(V+1) + 4E + 2E (+ 4E)
```

For V = 10⁶ and E = 10⁷ (average degree 10, illustrative): 4 MB + 40 MB + 20 MB + 40 MB ≈ 104 MB with weights. A whole-graph CSR is therefore not automatically impossible at that scale, so whether to hold one is a measured decision. The source's guidance stands: do not *necessarily* maintain a complete CSR at all times. Use persistent indexed rows for the full graph, small CSR structures for active subgraphs, and an in-memory cache for frequently used concepts [F1-D §2.14]. The CSR snapshot is derived data (SG-ENC-008).

---

## 11.4 Integer and field encodings

### 11.4.1 Fixed width versus variable length

[F3-A §6.4]

| Encoding | Advantage | Disadvantage |
|---|---|---|
| Fixed 32-bit | Predictable record size, trivial indexing and decoding, 4,294,967,296 values | Small IDs cost as much as large ones |
| Unsigned LEB128 varint | Small numbers use fewer bytes | Variable-size records, bounds checks, slightly more decode work |

Unsigned varint size (7 payload bits per byte):

| Value range | Bytes |
|---|---:|
| 0 – 127 | 1 |
| 128 – 16,383 | 2 |
| 16,384 – 2,097,151 | 3 |
| 2,097,152 – 268,435,455 | 4 |
| 268,435,456 – 34,359,738,367 | 5 |

So an ID such as 1,000,000 takes 3 bytes, and an ID in the tens of millions takes 4 [F3-A §6.4]. Global concept IDs may therefore cost as much as fixed 32-bit. The saving comes from *local* codes and *small deltas*, not from the varint itself.

**USBF integer rules (Normative).**
1. Unsigned integers in variable positions are minimal-length LEB128 varints. Overlong (non-minimal) encodings MUST be rejected by decoders. This makes the encoding canonical (§11.11).
2. Signed integers use zigzag then varint: `z = (n << 1) ^ (n >> 63)`.
3. Fixed-width fields use little-endian byte order.
4. Decimal values are stored as `(mantissa zigzag varint, scale varint)`. Binary floating point is not used in canonical IR, because rounding would make equal values compare unequal.
5. Text is UTF-8 with a varint length prefix. Repeated strings (names) go through a block-local string table.
6. Sets of sorted IDs use **delta coding**: the first value as a varint, then the gaps. Example: `[1058421, 1058433, 1058500]` costs 3 + 1 + 1 = 5 bytes instead of 9.

---

## 11.5 Local dictionaries

### 11.5.1 Mechanism

[F3-A §6.5; F2-C §5.17, §5.29] A block references only a subset of a very large global dictionary. A **local code** is a short block-specific alias for a global ID. The global identity never changes, and only the representation does.

### 11.5.2 Cost model (Enhancement E-104)

Let a block have R concept references to D distinct concepts, average global-ID cost g bytes, and average local-code cost l bytes.

```text
without local codes:  R·g
with local codes, explicit pairs:     R·l + D·(l + g)       (source's accounting, F3-A §6.5)
with local codes, implicit positions: R·l + D·g             (the table position is the code)
```

Source example: R = 1000, D = 100, g = 4, l = 1.

| Variant | Bytes | Saving vs 4,000 |
|---|---:|---:|
| No local codes | 4,000 | n/a |
| Explicit pairs (100 × 5 + 1,000) | 1,500 | 2,500 (62.5%) |
| **Implicit positions** (100 × 4 + 1,000) | **1,400** | **2,600 (65%)** |

(Block headers, indexes, and other metadata are excluded, as in the source.)

Local codes pay only when `R·(g − l) > D·g` (implicit positions). With R = D = 100 and g = 4, l = 1: 100×3 = 300 < 400, so the mapping costs more than it saves. **Local remapping is optional and chosen per block by measured cost** [F3-A §6.5].

### 11.5.3 Two-tier local dictionary

Two properties conflict: giving frequent concepts one-byte codes wants frequency order, and delta coding of IDs wants sorted order. The compromise:

| Tier | Codes | Order | Stored as |
|---|---|---|---|
| 1 | 0 – 127 | Descending reference frequency (ties: ascending global ID) | Plain varints |
| 2 | 128 and up | Ascending global ID | First ID, then gap varints |

Tier 1 gives the most frequent concepts 1-byte codes. Tier 2 pays 2 bytes per reference but stores its mapping compactly. Code assignment is deterministic (§11.11). The boundary between tiers is an optimizer parameter [Provisional].

### 11.5.4 Where codebooks live

A global identity, a domain codebook, and a block-local code serve different purposes [F3-A §6.21]:

```text
GLOBAL IDENTITY ───────────► preserves meaning (Registry)
   │
   ▼
DOMAIN CODEBOOK ───────────► exploits domain frequency ("cell" in biology vs computing)
   │                          stored once per domain release in usbf_codebook
   ▼
BLOCK-LOCAL CODE ──────────► exploits this block's actual data
```

A block can use: no dictionary, a domain codebook plus a block-local overflow, or a block-local dictionary only. Domain codebooks give independent blocks a shared dictionary at the cost of external dependence (§11.12.5). A domain does not get a separate concept identity. Its codebook is only an alternative compact encoding of global IDs.

---

## 11.6 Frame-specific record layout

### 11.6.1 Principle

[F3-A §6.6] A frame defines its roles and order, so an instance does not repeat role names, just as a database row omits column names. For a frame F with ordered roles `R(F) = (r₁, …, rₙ)`, an instance is `I = (F, v₁, …, vₙ)`. The decoder reads `R(F)` from the frame dictionary, pinned to the frame version used at encoding time (§11.14). "The grammar itself becomes part of the compression mechanism."

### 11.6.2 Role-state encoding (Enhancement E-102, completes E-09)

A single presence bit cannot distinguish the four unfilled situations [F3-A §6.7]: not expressed in the source, explicitly stated unknown, not applicable, and deliberately withheld. Part 2 §2.6 adds **basis** for filled roles. The record therefore has three layers:

| Layer | Content | When present |
|---|---|---|
| **Presence bitmap** | `⌈n/8⌉` bytes, bit *i* = 1 iff role *i* is SPECIFIED. Bits assigned LSB-first. | Always |
| **Exception list** | For roles with bit 0 whose state is not the default UNSPECIFIED: `(role_index varint, state code)` pairs. State codes: UNKNOWN = 1, NOT_APPLICABLE = 2, WITHHELD = 3. Preceded by a count. | Flag `has_exceptions` |
| **Basis plane** | 2 bits per *present* role, in role order, LSB-first: EXPLICIT = 0, GRAMMATICAL = 1, BACKGROUND = 2. | Flag `has_basis`. If absent, all present roles are EXPLICIT. |

The default state UNSPECIFIED is by far the most common absence and costs nothing. UNKNOWN, NOT_APPLICABLE, and WITHHELD are rarer and pay for their exceptions. Basis is carried because it matters to correctness (SG-EVD-006): a BACKGROUND element is never silently relabelled as source-stated. A multi-valued role (cardinality above 1) stores its filler count as a varint before its fillers.

### 11.6.3 Fillers

The role's `expected_kind` is known from the frame definition, so most fillers need no type tag:

| Role expects | Encoded as |
|---|---|
| ENTITY | Node reference (§11.7.3) |
| EVENT / STATE / PROCESS | Node reference to a FRAME_INSTANCE (or ALT) node |
| PROPOSITION | Node reference to an expression node |
| VALUE / QUANTITY | Literal node reference, or inline literal |
| TIME | TIME node reference |
| Mixed (a role that accepts several sorts) | One tag byte, then the above |

### 11.6.4 Frame-instance record

```text
FRAME_INSTANCE node:
  tag        u8     0x10
  frame code varint  (index into SEC_FDICT; pins frame_id + frame_version)
  flags      u8     bit0 has_exceptions · bit1 has_basis · bit2 has_annotation · bit3 has_certificate_ref · ...
  bitmap     ⌈n/8⌉ bytes
  [exceptions]  count varint, then (role_index varint, state u8) × count
  [basis plane] ⌈2·(#present)/8⌉ bytes
  fillers    one per present role value, in role order
  [annotation / certificate refs]
```

---

## 11.7 Block structure, nodes, and graph encoding

### 11.7.1 Recursion is encoded as a graph, not a tree

[F3-A §6.8–§6.9] Naive recursive serialization duplicates a participant that several events share ("John wants to leave because John is tired"). USBF uses a **node table**. Every referent, situation, proposition, and expression is a node with a block-local index. Fillers refer to nodes. One referent can be the AGENT in several frame instances without being repeated, which matches the reentrant structure of the IR (Part 8 §8.4.3).

### 11.7.2 Ordering and reference rules (Enhancement E-110)

1. Nodes are written **children first** (post-order), so every reference points to an *earlier* node. The reference graph is a DAG, because frame nesting and composition are acyclic (Part 4 §4.6).
2. A reference is stored as a **backward distance** `d = current_index − target_index` (varint). Nearby references are short, and the decoder can resolve everything in one pass without a forward-reference table.
3. A decoder MUST reject a distance of 0 or a distance beyond the current index.

### 11.7.3 Node tags

| Tag | Node | Tag | Node |
|---|---|---|---|
| 0x01 | REFERENT | 0x30 | NOT |
| 0x02 | LITERAL | 0x31 | AND |
| 0x03 | TIME | 0x32 | OR |
| 0x04 | KIND-REFERENCE | 0x33 | IMPLIES |
| 0x05 | VAR | 0x34 | COND |
| 0x10 | FRAME_INSTANCE | 0x35 | Q (quantifier) |
| 0x11 | RELATE | 0x36 | MODAL |
| 0x12 | PROPERTY | 0x37 | TENSE |
| 0x13 | COMPOSE | 0x38 | ASPECT |
| 0x20 | ASSERT | 0x39 | TEMPORAL |
| 0x21 | HOLDS | 0x3A | ATTRIBUTE |
| 0x3B | SAME_AS | 0x3C | DIFFERENT_FROM |
| 0x3D | DIRECT | 0x3E | FIG |
| 0x3F | ALT | 0x41 | REIFY / EXTENT |
| 0xFE | ANNOTATION | 0xFF | Reserved for extensions |

These are the Part 3 constructs. Unknown tags in the *optional* range cause the containing section to be skipped. An unknown tag in a *critical* node position fails the decode (§11.14).

### 11.7.4 Node bodies (pattern)

```text
REFERENT:  tag · flags u8 [number 2b, genericity 1b, scope 1b, has_cardinality 1b, has_intro_context 1b]
           · n_classes varint · class local codes · [cardinality] · [intro-context ref]
LITERAL:   tag · value_type u8 · [unit code] · value (zigzag varint | (mantissa, scale) | text via string table)
TIME:      tag · form u8 (INSTANT|INTERVAL|DURATION|PARTIAL|RELATIVE|VAGUE|UNRESOLVED)
           · INSTANT: zigzag seconds-since-epoch, zigzag tz-offset-minutes, calendar id
             RELATIVE: expression code, anchor = source ref · UNRESOLVED: span ref
ASSERT:    tag · content ref · operator byte(s) (polarity, tense class) · origin/status code
           · commitment/context code · [definition ref] · [alt group] · evidence ref
HOLDS, NOT, ...:  tag · argument refs (varints, backward distance)
```

Relative time stays relative: a resolved value is stored *next to* the original expression, never instead of it (Part 3 §3.9.1).

### 11.7.5 Block layout

```text
BLOCK HEADER   block_len u32 · block_type u8 · codec u8 · uncompressed_len varint · crc32 u32 (of payload)
PAYLOAD (after codec):
  SEC_GREF   grammar_version, ontology_release, ruleset_release  (§11.14)
  SEC_CDICT  local concept dictionary    (§11.5.3)
  SEC_FDICT  local frame dictionary: (frame_id, frame_version) pairs; position = local code
  SEC_STR    string table (names, literals)
  SEC_NODES  node table        count varint, then node records
  SEC_RELS   relationship data not already implicit in instances      (§11.9)
  SEC_PROV   source ids, span tables (delta-coded), certificate refs, evidence refs
  SEC_IDX    optional indexes: first_assertion_id + id deltas, key→node offsets
each SECTION: sec_type u8 · sec_len varint · body  (unknown optional sections are skipped via sec_len)
```

---

## 11.8 Worked example: one sentence, completely encoded

### 11.8.1 Setup

Sentence (39 UTF-8 bytes): `The doctor gave the patient medication.` It is unit 1 of a block. Local concept codes: DOCTOR = 0, PATIENT = 1, MEDICATION = 2. Local frame code: GIVE = 0, with roles in order `AGENT, SOURCE, RECIPIENT, THEME, TIME` (n = 5). In the Part 4 §4.12.3 definition the giver is both AGENT and SOURCE.

### 11.8.2 Encoding

```text
N0 REFERENT doctor     01 | 00 | 01 | 00                    4 bytes  (tag, flags, 1 class, code 0)
N1 REFERENT patient    01 | 00 | 01 | 01                    4 bytes
N2 REFERENT medication 01 | 00 | 01 | 02                    4 bytes
N3 FRAME_INSTANCE GIVE 10 | 00 | 02 | 0F | 04 | 03 03 02 01   9 bytes
     tag 0x10 · frame code 0 · flags 0x02 (has_basis) · bitmap 0x0F (roles 0–3 present, role 4 absent)
     · basis plane 0x04 (role 0 EXPLICIT=00, role 1 GRAMMATICAL=01, roles 2,3 EXPLICIT=00)
     · fillers as backward distances: AGENT→N0 (3), SOURCE→N0 (3), RECIPIENT→N1 (2), THEME→N2 (1)
N4 ASSERT              20 | 01 | 11 | 03 | 05                5 bytes
     tag · content = N3 (distance 1) · polarity+tense (positive, past) · origin SOURCE_TEXT + status SOURCE_ASSERTED
     · evidence ref (block-local evidence index 5)
                                                   total ≈ 26 bytes
```

Plus per-block fixed costs (headers, dictionaries), which are shared by the block's other records.

### 11.8.3 What the arithmetic shows

The source's quick estimate was `[201, 101, 102, 103]` = 4 IDs × 4 bytes = 16 bytes against 39 bytes of text [F3-A §6.2]. That payload lacks the referents (are these three particular things?), the roles' basis, the TIME slot, tense, polarity, commitment, and the link to evidence. A *complete* record for the USG model costs about 26 bytes in this design, before any dictionary overhead. Sentence-to-sentence sharing of referents (coreference), common templates, and entropy coding all reduce it, and extra operators, qualifiers, and annotations increase it. These are design estimates and not measurements (§11.17).

**Decoding** reverses the steps: read `SEC_FDICT` to learn GIVE's pinned version, read `n_roles = 5` from the schema (so the bitmap is 1 byte), read the bitmap `0x0F`, read 4 basis pairs, read 4 fillers, and resolve backward distances. Roles 4 is UNSPECIFIED by default, so no exception list is needed.

---

## 11.9 Relationship data

Relations that are not implicit in frame instances (concept-level IS_A, HAS_PART, HAS_FUNCTION, domain edges) go in `SEC_RELS`:

```text
group by relation code (local relation dictionary)
  for each relation: count varint, then edges sorted by (src, tgt)
     src as delta-from-previous-src varint, then tgt as zigzag delta-from-previous-tgt (within the same src)
     flags per edge only when non-default (assertion ref, weight with scoring-model id, status)
```

**Inverses and closures are not stored.** `ENGINE PART_OF CAR` implies `CAR HAS_PART ENGINE` when the relations are declared inverses. `CAR IS_A VEHICLE` and `VEHICLE IS_A ARTIFACT` imply `CAR IS_A ARTIFACT` [F3-A §6.27]. Only foundational edges are stored (SG-KNW-011, SG-KNW-012), and the reverse-direction index (`edge_by_target`) answers inverse lookups.

**Selective materialization** [F3-A §6.27]:

```text
INFERENCE ─┬─ frequently used ──► cached (Part 10 §10.7.5: dependency-keyed, invalidated)
           └─ rarely used ──────► computed on demand
```

The cache is a performance optimization and never an authoritative source (SG-KNW-008). Not storing derived relations saves space and recomputing them costs time. Hot inferences are therefore materialized, and the rest are not.

---

## 11.10 Structural sharing

### 11.10.1 What may be shared

[F3-A §6.10] Hash-consing reuses structurally identical *immutable* expressions. It is safe only where identity is defined by content.

| Safe to share | Not to share |
|---|---|
| Frame, concept, and rule definitions | Event occurrences |
| Pure expression templates (a function-assertion pattern) | Referents |
| Reusable ALT and operator wrappers with no instance data | Any structure whose real-world identity is separate from its content |

"John bought a book on Monday" and "…on Tuesday" are different events. Even "John bought a book" recorded twice does not necessarily mean the same purchase. **Structural equality is not real-world identity** (SG-CAN-004; Part 7 §7.6).

**SG-ENC-004 (Normative).** Hash-consing applies only to immutable definitions and pure templates. Event occurrences and referents keep distinct identities unless independently resolved as identical (RESOLVE_INDIVIDUAL).

### 11.10.2 Content hashes versus IDs

[F3-A §6.11] A normalized definition has a **content hash**. Two proposals with identical hashes are exact duplicates. This is cheap duplicate detection (Part 7 §7.13).

| | Stable ID | Content hash |
|---|---|---|
| Identifies | A definition's persistent identity | A particular definition *version* |
| Changes when definition changes | No | Yes |
| Equal hash means | Same serialized content | |
| Used for | Long-term references | Exact-duplicate detection, cache validation |

Two logically equivalent definitions can have different hashes. A hash is therefore never the global identifier. Hash function: SHA-256, with a full 32-byte value in `content_hash` columns and a truncation only for in-block lookup tables (collisions are then verified by byte comparison).

---

## 11.11 Canonical form and round trips

### 11.11.1 Why a canonical form (Enhancement E-103, completes E-22)

The sources require `Decode(Encode(S)) = S` "where equality is defined over the canonical serialized semantic representation" [F3-A §6.31], and they do not define the canonical form. Without one, two equal IRs could have different bytes, hashing fails, and the round-trip test is ambiguous.

### 11.11.2 Definition

The **canonical serialization** of an IR fragment is produced by these rules:

1. **Order of units and assertions** is data. It is preserved as given in the stored sequence.
2. **Node numbering:** nodes are numbered in the order of their first completion in a deterministic post-order traversal. Traversal visits arguments in role-index order (frames) or argument order (operators).
3. **Commutative operators** (AND, OR): children are sorted by the canonical byte string of their subtrees. Sorting applies **only** to the logically commutative connectives (SG-CAN-002). Role order, ALT member order (ranked), and argument order of non-commutative operators are never sorted.
4. **Variables** are alpha-renamed by order of first binder occurrence (SG-CON-005c).
5. **Shared pure subtrees** (SG-ENC-004) are numbered once. Referents and frame instances are numbered once per distinct occurrence.
6. **Local codes** are assigned deterministically: tier 1 by descending frequency then ascending global ID, tier 2 by ascending global ID (§11.5.3).
7. **Varints are minimal**, decimals are normalized (no trailing zeros in the mantissa, scale ≥ 0), strings are NFC-normalized UTF-8.
8. **Annotations:** structural hashes ignore annotations (SG-CAN-004). The full-record hash includes them.

Codec output (zlib, lzma, zstd) is *not* canonical across implementations or versions. Equality, hashing, and round trips are therefore checked on the **decompressed canonical bytes**.

### 11.11.3 Round-trip requirements

**SG-ENC-001 (Normative).** For every valid canonical IR `S` and every enabled encoding plan `E`:

```text
canon( Decode( Encode_E( S ) ) ) = canon( S )        (byte-for-byte on the canonical serialization)
```

| Test | What it establishes |
|---|---|
| Property-based round trip (Hypothesis, generated valid IR across all constructs and hole states) | The encoder and decoder agree |
| Idempotence | `Encode(Decode(Encode(S))) = Encode(S)` |
| Cross-plan equivalence | Different encoding plans (with or without local dictionaries, templates, codecs) decode to the same IR |
| Rejection of non-canonical inputs | Overlong varints, unsorted commutative children, unused dictionary entries are rejected or normalized deliberately |
| Fuzz tests (§11.14.4) | Decoder never crashes or over-allocates on malformed input |
| Cross-version replay | Fixtures from every published format version still decode |

Unlike natural-language interpretation, binary encoding can be designed to reconstruct exactly. This is one place where correctness can genuinely be guaranteed under stated assumptions [F3-A §6.31].

### 11.11.4 Two distinct quality tests

| Test | Question | Guarantee |
|---|---|---|
| Semantic parsing test | Does the IR accurately represent the source? | Not guaranteed for arbitrary language (Parts 5–6) |
| Binary round-trip test | Does the decoder reconstruct exactly the encoded IR? | Rigorous |

They must never be confused [F3-A §6.31].

### 11.11.5 Preservation matrix (SG-ENC-002)

An encoding plan may drop information only if it declares so, and a plan that drops a "required" feature is rejected [F3-A §6.29].

| Feature | Semantic mode | Reversible mode |
|---|---|---|
| Frame, role bindings, value states, basis | Required | Required |
| Polarity (negation) | Required | Required |
| Modality, tense, aspect, quantifiers, attribution | Required | Required |
| Referent identity, coreference links, cardinality | Required | Required |
| ALT groups and ranks | Required | Required |
| Commitment holder, evaluation context, epistemic status | Required | Required |
| Source and span links, evidence references | Required | Required |
| LanguageAnnotation (voice, definiteness, lexical choice, word order) | Optional | Required |
| Original wording and whitespace | Not preserved | Required |

"A format that drops negation may compress better, but it is unacceptable if negation is required by the application" [F3-A §6.29].

---

## 11.12 Container format, blocks, and random access

### 11.12.1 File layout

```text
FILE HEADER   magic "USBF" (55 53 42 46) · format_major u8 · format_minor u8
              · critical_flags u16 · optional_flags u32 · file_uuid 16 bytes · created varint
BLOCKS        block 0 … block n−1     (§11.7.5)
CODEBOOKS     optional shared domain codebooks, with versions
DIRECTORY     per block: block_id, key_min, key_max, offset, length, codec, crc32, uncompressed_len,
              grammar_version, ontology_release, plan_id
FOOTER        directory_offset u64 · directory_crc u32 · magic "USBF"
```

A footer-based directory permits random access by seeking to the end, in the style of other columnar and archive formats. The same directory is mirrored in the `usbf_block` table for the authoritative store.

### 11.12.2 Random access versus maximum compression

[F3-A §6.20] A single continuous stream gives the best compression and forces decoding of unrelated data to retrieve one record. The brain-inspired architecture depends on selective retrieval, so USBF uses **blocks**: independently decodable groups of records, each with its own dictionaries, optional index, and checksum. The Memory Manager decodes only the blocks it needs. Blocks cost some compression, because dictionaries repeat across blocks. That trade-off is judged worthwhile for a personal-computer cognitive system.

**Block-size selection rule** [Provisional]: for each corpus, measure total size and p95 single-record retrieval latency for candidate block sizes (for example 16 KiB, 64 KiB, 256 KiB, 1 MiB uncompressed). Choose the smallest block size whose total size is within *x*% of the best total size [Provisional: x = 5]. Read amplification equals block size divided by record size, so the optimizer reports it.

### 11.12.3 Block keys and domain grouping

Blocks are grouped by **domain** and source locality, so that a block's concept distribution is narrow (which helps local dictionaries and entropy models) and queries like "medical sentences from source S" touch few blocks. Within a block, records are in processing order, which is data.

### 11.12.4 Checksums and integrity

Each block carries a CRC-32 of its compressed payload for *accidental* corruption. The file directory carries a CRC. Optionally the footer carries a SHA-256 of the whole file. **Checksums are not authenticity.** A hostile file can carry valid checksums, so decoder hardening (§11.14.4) does not depend on them.

### 11.12.5 Self-contained versus externally dependent

[F3-A §6.19]

| Mode | Contents | Size | Use |
|---|---|---|---|
| Externally dependent | Blocks, referencing installed dictionaries, frame definitions, and codebooks by ID and version | Smaller when many files share a dictionary | Internal storage |
| Self-contained (export bundle) | Blocks plus the frame definitions (role schemas), concept labels, and codebooks they need | Portable | Export, backup, exchange |

The default is **shared external dictionaries with explicit versioning, plus an export option that bundles the required definitions.** Decoding the *bytes* needs only the role schema of the frames used (role count, order, expected kinds). Interpreting *meaning* needs concept definitions. Human-readable output needs labels. The bundle declares which of these it includes.

---

## 11.13 Compression techniques beyond layout

### 11.13.1 Pattern templates: when worth it

[F3-A §6.12–§6.13] Frequent combinations of frames can be replaced by compound templates, for example repeated medical-record structures. A template must not introduce facts absent from the original records: it encodes only a structural pattern that is explicitly present. A prescription template carries `PATIENT_HAS_CONDITION` and `DOCTOR_PRESCRIBED_MEDICATION`. An additional `MEDICATION_TREATS_CONDITION` assertion needs its own evidence [F3-A §6.12].

**The inequality (Enhancement E-101, completes E-10).** The source's rule is `D + NR < NL`, so `N > D/(L − R)`, with L the direct size, D the template definition, R the reference, N the occurrences. Example: L = 30, R = 5, D = 200 gives N > 8 [F3-A §6.13]. The source adds that a real system "must also account for indexing, parameters, metadata". Parameters matter most: a template instance still has to carry the data that varies. Splitting the pattern's size into a fixed part F (what the template removes) and a variable part P (what each instance must still carry), `L = F + P`, the template instance costs `R + P`:

```text
S_direct   = N·(F + P)
S_template = D + I + N·(R + P)            I = index and registry overhead for the template
beneficial iff   N·(F − R) > D + I       ⟺   N > (D + I) / (F − R),   requires F > R
```

The variable part P cancels, so only the removable fixed content F matters. The source's formula is this one with L read as the fixed part and I = 0.

| Case | F | R | D | I | Break-even N |
|---|---:|---:|---:|---:|---:|
| Source example (L = 30 all fixed, I = 0) | 30 | 5 | 200 | 0 | N > 8 |
| Pattern with 10 variable bytes (F = 20) | 20 | 5 | 200 | 0 | N > 13.3, so 14 |
| Same, with index overhead I = 20 | 20 | 5 | 200 | 20 | N > 14.7, so 15 |

**SG-ENC-006 (Normative).** A compression template is created only if the inequality holds with the *expected* N (using usage statistics) and a safety margin [Provisional: 1.5×], and the pattern is semantically validated (it asserts only what is present). A template needing N far above its realistic reuse is not created. Templates are stored in `usbf_template` with a definition, version, and content hash, and they are versioned like frames (§11.14).

### 11.13.2 Frequency-based codes

[F3-A §6.15] Code length should follow *observed frequency*, not position in the ontology or alphabetical order. Entropy coders include Huffman coding, arithmetic coding, and asymmetric numeral systems. For a symbol source with probabilities p, the ideal expected code length is the entropy `H(X) = −Σ p log₂ p`. Local dictionaries with frequency-ordered tier 1 (§11.5.3) are the cheap form of the same idea.

### 11.13.3 Conditional coding

[F3-A §6.16] Semantic grammar already supplies context. The frame says what participants are likely, the parent frame says inherited constraints, and the domain says likely concepts. Coding a symbol X given context C approaches the conditional entropy:

```text
expected bits per symbol ≥ H(X | C),     H(X | C) ≤ H(X)
```

Inside a general TRANSFER frame the THEME has many possible values. Inside BLOOD_TRANSFUSION it is almost always a blood product. Implementation: a **context-specific local dictionary** per `(frame, role)` pair, with codes assigned by frequency *within that context*. The decoder knows the context (it has just read the frame and is reading a role), so it uses the matching table.

**Cost control.** Specialization has costs: the context tables, and in the case of specialized frames, the frames themselves (SG-ENC-006 logic applies). A per-context table is created only if `n_c · (bits_saved_c / 8) > table_bytes_c`, where `n_c` is the number of fillers observed in that context [F3-A §6.16: "We should not assume that semantic specialization always improves total compression"]. The estimate uses measured per-context entropy.

### 11.13.4 General-purpose codecs

After serialization, each block's payload may be compressed with a general codec (`codec` field). Candidates, in increasing weight:

| Codec | Notes |
|---|---|
| none | Smallest decode cost. Good when the block is already dense. |
| zlib (DEFLATE) | Standard library. Fast. |
| lzma | Standard library. Better ratios, slower. |
| zstd | Strong ratio and speed, supports **trained dictionaries** that help small blocks. Availability depends on the Python version or an additional package, so it is included only after the verification gate (Part 12). |

For small blocks, a codec's startup cost and lack of context matter, so trained codec dictionaries are evaluated as part of the benchmark. The codec is part of the encoding plan and does not change the canonical bytes (§11.11).

### 11.13.5 Why not an AI model as the compression predictor (yet)

[F3-A §6.17] A language model could in principle predict semantic IDs and drive entropy coding. It is not used in the first implementation:

| Reason | Detail |
|---|---|
| Computational cost | Inference is far slower than conventional compression |
| Determinism | The decoder must reproduce exactly the encoder's probability distributions |
| Model size | If the decoder lacks the model, its storage becomes part of the cost |
| Numerical consistency | Small floating-point differences can break arithmetic decoding |
| Version compatibility | Encoded data would depend on one model version |

Start with deterministic frequency tables and simple context models. Investigate learned probabilistic coding later and only if the measurements show the benefit justifies the complexity.

---

## 11.14 Versioning, compatibility, and hardening

### 11.14.1 What a file depends on

[F3-A §6.19] If frame 201 meant TRANSFER with roles `AGENT, RECIPIENT, THEME` in grammar version 1 and later gains distinctions, interpreting old data under a new definition could change meanings. Every encoded file therefore pins:

```text
SEC_GREF per block:   grammar_version  "1.0"
                      ontology_release "2026-10"
                      ruleset_release  "R-0.1"
SEC_FDICT:            (frame_id, frame_version) for every frame used
Templates and codebooks: their own (id, version, content_hash)
```

These are stable machine-readable values and not informal labels.

### 11.14.2 Pinned role schema (Enhancement E-108)

The presence bitmap's length depends on how many roles the frame had **at the pinned version**. Part 4 SG-FRM-006 makes role order append-only, so a newer frame version has a superset of roles, and the decoder:

1. Decodes using the **pinned** version's role list (`frame_role` rows for that `(frame_id, frame_version)`).
2. Does *not* assume the latest version.
3. Optionally *migrates* the decoded record to a newer version (adding UNSPECIFIED bindings for roles added later) as a separate step recorded in the migration record (Part 2 §2.13).

A MAJOR frame change (role removed or retyped) makes a pinned old version non-migratable. Old versions remain resolvable and decodable (SG-ENC-003).

### 11.14.3 Format compatibility

| Change | Version effect | Reader behaviour |
|---|---|---|
| Add an optional section | minor | Older readers skip it (length-prefixed) |
| Add a node tag in the optional range | minor | Skipped if unknown |
| Add a critical feature (new filler encoding, new codec required) | major, or a critical-flag bit | Reader rejects files with unknown critical flags |
| Change node semantics | major | New reader needed |

**SG-ENC-003 (Normative).** A decoder MUST reject a file whose critical flags it does not understand, MUST NOT guess the meaning of unknown critical structure, and MUST decode under pinned versions. Fixtures from each published format version are part of the test suite.

### 11.14.4 Decoder hardening (Enhancement E-106, SG-ENC-007)

USBF files may come from outside (imports, backups, exchange). A decoder is an attack surface, and declared lengths cannot be trusted.

| Hazard | Control |
|---|---|
| Decompression bomb | Cap `uncompressed_len` per block and total per file. Stream decompression with a hard output limit. |
| Huge declared counts (nodes, dictionary entries, string lengths) | Check each against remaining bytes and a configured maximum **before** allocating |
| Deep nesting | Enforce a nesting-depth limit (Part 5 VC-S16) |
| Reference attacks | Reject zero or out-of-range backward distances (§11.7.2) |
| Cycles in templates or definitions | Detect and reject (VC-S16) |
| Non-canonical encodings | Reject overlong varints and out-of-order structures as invalid, not as alternate forms |
| Unknown IDs | Resolve through the Registry. Unknown or provisional IDs in an import are quarantined (SG-SEC-010, invariant I-07) |
| Truncated or malformed input | Bounds-checked reads. Return a typed error and never raise unhandled exceptions or crash |

Decoding runs in a restricted context (no network, bounded memory, wall-time limit), and imported records enter as STRUCTURED candidates, never PROMOTED (Part 8 §8.13.5). **Fuzz testing** of the decoder is mandatory before any file format release.

---

## 11.15 The two encoding modes

[F1-A §3.15; F3-A §6.1]

### 11.15.1 Semantic mode

Encodes validated IR, the node table, and provenance links per §11.7. The original wording is not recoverable. The preservation matrix (§11.11.5) lists what is kept.

### 11.15.2 Reversible mode

Preserves the source text exactly. Three designs, in increasing ambition:

| Design | Contents | Exact reconstruction | Expected size |
|---|---|---|---|
| R1 | Semantic block + the **stored text**, compressed, + span alignment table (unit → span ranges, delta-coded) | Yes, trivially | `S_sem + S_text_compressed + S_align` |
| R2 | Semantic block + LanguageAnnotations for every token span (surface form, lexical choice, voice, tense form, word order, whitespace, punctuation) | Yes if annotations are complete | Often larger than R1 |
| R3 | Semantic block + **wording delta** against a deterministic surface realization of the IR | Yes | Possibly smaller than R1, but needs a realization generator and its determinism guarantees |

**Honest lower bound (Enhancement E-109).** In R1, the reversible file contains compressed text *plus* the semantic layer, so it is at least as large as compressed text alone: `S_rev ≥ S_text_compressed`. Its value is the semantic layer (queries, reasoning), not size. The source warned "We should not assume reversible mode will be smaller than conventional text compression" [F1-A §3.15]. R3 is the only design with a theoretical size advantage, and it is deferred until the semantic pipeline is reliable and a deterministic realizer exists.

The kernel implements semantic mode and R1 only. The pipeline already records IR-to-span alignment (Part 8 §8.17), which R1 needs.

---

## 11.16 The Compression Optimizer and the encoding pipeline

### 11.16.1 Pipeline

[F3-A §6.30]

```text
 VALIDATED SEMANTIC IR  (canonical, Part 5)
   → CANONICALIZATION      normalize within declared scope; define canonical form (§11.11)
   → GRAPH DEDUPLICATION   hash-cons immutable definitions and pure templates only (§11.10)
   → FRAME INSTANCE PACKING role order, bitmap, exceptions, basis (§11.6)
   → LOCAL ID ASSIGNMENT   two-tier dictionaries, context dictionaries (§11.5, §11.13.3)
   → FREQUENCY ANALYSIS    symbol statistics per domain, frame, role
   → BINARY SERIALIZATION  nodes, relations, provenance (§11.7)
   → ENTROPY COMPRESSION   codec per block (§11.13.4)
   → COMPRESSED STORAGE    blocks, directory (§11.12)
```

Each stage has one responsibility and the output decodes into the same semantic IR.

### 11.16.2 The optimizer's job

[F3-A §6.25] **Input:** validated grammar, validated records, usage statistics, storage measurements. **Output:** a `StoragePlan` (derived, versioned).

```text
StoragePlan
  plan_id, created_from (corpus snapshot id, ruleset release, ontology release)
  per domain:   block size, codec (+ trained codec dictionary id), tier-1/tier-2 boundary,
                local dictionary on/off, domain codebook id, context dictionaries [(frame, role)],
                template list (usbf_template ids)
  measured:     S_total components, bytes/unit, encode/decode time, retrieval latency, peak RAM
  decision log: each choice with the measured alternative costs
```

Responsibilities (the ten of the source): identify frequent concepts, identify frequent frames, detect repeated semantic substructures, estimate template cost (§11.13.1), select local codebooks, choose integer encodings, evaluate block sizes, compare serialization layouts, measure decoding speed, and **avoid transformations that alter meaning** (§11.11.5).

**SG-ENC-005 (Normative).** The optimizer MUST NOT modify authoritative concept, frame, or relation definitions to improve compression. It generates a storage representation *derived from* them. This keeps encoding changeable without changing the ontology [F3-A §6.25].

### 11.16.3 Semantic generalization versus compression optimization

[F3-A §6.14; Part 9 §9.10] Two systems with independent success criteria:

| | Generalization Engine | Compression Optimizer |
|---|---|---|
| Question | Is this a meaningful, valid, reusable abstraction? | Does this layout or template reduce total cost? |
| Judged by | Correctness, usefulness (gates G1–G8) | Measured encoded size and decode performance |
| Output | Frames, abstractions in the ontology | Storage plans, templates, codebooks |

They may exchange information. A semantically valid abstraction that saves no storage stays in the ontology without a special binary code. A frequent byte-level pattern with no meaning compresses without entering the ontology. This is analogous to conventional compressors finding repeated byte patterns without understanding them.

### 11.16.4 Minimum Description Length

[F3-A §6.24] MDL is the principle behind the trade-off:

```text
L_total = L(Semantic Grammar) + L(Knowledge | Grammar)
```

A very simple grammar needs long descriptions per record. A very elaborate grammar (a special frame for every sentence) makes each record tiny and the dictionary enormous. The best total lies between. MDL is a **theoretical foundation of the Semantic Grammar Optimizer** and is applied only to candidates that already pass semantic gates, because "the optimizer might achieve excellent compression by discarding meaningful distinctions" [F3-A §6.24].

---

## 11.17 Measurement

### 11.17.1 The correct metric

[F3-A §6.23] Measuring only the size of encoded instances hides real cost.

```text
S_total = S_dictionary + S_frames + S_instances + S_relationships + S_indexes + S_metadata
```

| Term | Contains |
|---|---|
| S_dictionary | Concept definitions, lexical mappings, codebooks |
| S_frames | Frame definitions and role schemas, templates |
| S_instances | Encoded events, referents, assertions |
| S_relationships | Additional graph connections |
| S_indexes | Retrieval indexes (and embeddings if they are counted) |
| S_metadata | Provenance, versions, certificates (COMPACT or FULL), audit data |

Report two figures:
- **Incremental storage cost:** assumes a shared dictionary already exists.
- **Standalone storage cost:** everything needed to decode and interpret independently, including any pretrained ontology or model used in decoding.

### 11.17.2 Benchmark variants

[F3-A §6.29] All variants use **the same validated IR**, because changes in parsing accuracy would otherwise distort the compression comparison. Strong baselines are added so the semantic formats are not compared against weak ones (Enhancement E-105).

| Variant | Description |
|---|---|
| A | Raw UTF-8 text |
| B | Conventional compressed text (zlib, lzma, zstd) |
| B+ | Text compressed per block with a trained dictionary |
| C | JSON semantic frames |
| C+ | **Compressed JSON** semantic frames (zlib, lzma, zstd) |
| D | MessagePack or CBOR semantic frames |
| E | Compact integer-based semantic records (fixed width) |
| F | Frame-specific binary encoding (§11.6, §11.7) |
| F+ | Variant F with a general codec |
| G | F with local dictionaries (§11.5) |
| H | G with frequency-based, context-aware coding (§11.13.2–3) |
| I | Relational rows only (SQLite) |

C+ and F+ matter because compressed JSON is often a strong baseline against a hand-built binary layout.

### 11.17.3 Measurements and fairness

For every variant: `S_total` (incremental and standalone) per the table above, bytes per unit, encode and decode throughput, **random-access latency** (p50 and p95 to read one record), peak memory, and passing of the round-trip and preservation tests. Rules: identical IR, identical hardware, several runs (report the median and spread), dictionary and schema costs always included, and a variant failing the preservation matrix for the required mode is reported but excluded from the comparison.

**Break-even model (Enhancement E-100).** Let `s_txt` be the compressed text bytes per unit, `s_sem` the semantic bytes per unit, `D` the total fixed overhead (dictionaries, frames, indexes, metadata), and N the number of units. Semantic encoding is smaller than compressed text when

```text
N·(s_txt − s_sem) > D        ⟹  N > D / (s_txt − s_sem)      (requires s_sem < s_txt)
```

The source's hypothetical numbers [F3-A §6.22] (100,000 sentences of 60 bytes; compressed text 2.5 MB, so `s_txt` = 25 bytes; frame instances 1.2 MB, so `s_sem` = 12 bytes; D = 0.8 + 0.2 + 0.4 = 1.4 MB):

| Representation | Size |
|---|---:|
| Raw text | 6.0 MB |
| Compressed text | 2.5 MB |
| Semantic encoding (1.2 + 1.4) | 2.6 MB |

Break-even: `N > 1.4×10⁶ / (25 − 12) ≈ 107,700 units`. At 100,000 units the semantic encoding is slightly larger, matching the source's table. These are **hypothetical** numbers and the source says so.

Sensitivity to the per-unit cost (the 26-byte complete-record estimate of §11.8.3 against 25 bytes of compressed text):

| `s_sem` | Break-even N vs compressed text (D = 1.4 MB, `s_txt` = 25) |
|---:|---|
| 12 | ≈ 107,700 |
| 18 | ≈ 200,000 |
| 24 | ≈ 1,400,000 |
| 26 | **Never** (semantic ≥ compressed text per unit) |

The comparison is also moving: `s_txt` falls as the corpus grows (a compressor finds more repetition), and `s_sem` falls as shared referents and templates accumulate. Only measurement on real IR decides. Whatever the outcome, the semantic format is justified by queries, reasoning, and generalization, not by size (Part 1 §1.3).

### 11.17.4 Information preservation tests

Alongside size, every variant runs the preservation matrix (§11.11.5) and a **contrast suite**: the negative pairs of Part 5 §5.11.3 (give vs offer, negated vs affirmed, may vs must) must remain distinguishable after a decode. A format that merges any such pair is rejected regardless of size.

---

## 11.18 Interoperability: RDF, OWL, SHACL, PROV-O (Enhancement E-107, completes E-24)

[F1-B §5; F1-D §2.21; F1-B §8.5; F3-C §8.9] RDF represents information as subject–predicate–object statements within graphs, and RDF 1.2 adds mechanisms for referring to statements. RDF is useful as an **interchange format**, not as the primary store. "We should not assume that an RDF store is automatically the most compact or computationally efficient choice" [F1-D §2.21]. USG exports to RDF through the mapping below. The mapping is **lossy** and says where.

| USG | RDF / OWL / SHACL / PROV-O |
|---|---|
| Concept | `owl:Class` (kinds ENTITY etc.) or `rdf:Property` (PROPERTY) or an individual of a `usg:` kind |
| SUBCLASS_OF / INSTANCE_OF | `rdfs:subClassOf` / `rdf:type` |
| Relation properties | `owl:TransitiveProperty`, `owl:AsymmetricProperty`, `owl:IrreflexiveProperty`, `owl:inverseOf` |
| DISJOINT_WITH | `owl:disjointWith` |
| Referent | Individual with `rdf:type` instance-of classes and `usg:genericity` etc. |
| Frame definition | An `rdfs:Class` per frame. Roles are properties with `rdfs:subPropertyOf` the tier-1 role property. |
| Frame instance | A node of the frame's class, with role properties to fillers |
| Role cardinality, expected class | SHACL shapes generated from FrameDefinitions: `sh:minCount`, `sh:maxCount`, `sh:class` |
| Assertion and its context | A **named graph** per assertion context, with PROV-O statements on the graph name (commitment holder, source, extraction activity) |
| Negation, modality, ATTRIBUTE | Graph-level properties on the context graph (`usg:negated`, `usg:modalForce`, `usg:attributedTo`) so contents are not asserted in the default graph |
| ALT | `usg:alternativeGroup` linking alternative context graphs |
| Evidence vector | PROV-O entities and activities (Part 6 §6.5.1), plus `usg:` evidence properties |

Named graphs work in RDF 1.1 and later. Statement-level references available in RDF 1.2 are an optional refinement, used only if the verification gate confirms the target tools support them.

**Loss declaration.** These have no faithful standard equivalent and are carried as `usg:` extension properties or omitted in plain RDF: TYPICAL (defeasible) constraints, GEN quantification, hole states (UNSPECIFIED vs UNKNOWN, and so on), value basis, ALT ranks, the five status axes, retention tiers, and constraint provenance classes. OWL's open-world semantics matches SG-KNW-001, but OWL consistency is not factual accuracy [F1-B §5].

**Import.** RDF, OWL, and SHACL content from outside enters as source-attributed STRUCTURED candidates (Part 8 §8.13.5). SHACL validation (pySHACL) is added when ontology complexity justifies it, consistent with the validation layering decision of F3-C §8.9: Pydantic and custom Python first.

---

## 11.19 Operations

| Concern | Approach |
|---|---|
| Growth monitoring | Table and block sizes, WAL size, index sizes, rows per table per release (Part 10 §10.13.5) |
| Maintenance | Periodic `PRAGMA wal_checkpoint`, `ANALYZE`, `VACUUM` (offline, with free space check), integrity checks |
| Backup | Versioned snapshots of authoritative tables, ruleset, and codebooks, hash-recorded (SG-SEC-009). USBF export bundles as portable archives. |
| Rebuilds | All of tier B can be regenerated from tier A. Corrupt derived data is discarded and rebuilt (SG-ENC-008). |
| Block compaction | A background job re-encodes small or poorly compressed blocks under a new plan, verifying round trip before swapping the directory entry |
| Deletion requests | Source deletion tombstones the source record and flags dependent blocks for re-encoding without the content (Part 6 §6.13.5) |
| Plan change | A new StoragePlan applies to new blocks. Old blocks are re-encoded lazily. The directory records each block's plan. |

---

## 11.20 Closure of source items in this part

| Source item | Closed in |
|---|---|
| What are we compressing; three representations; two goals (F3-A §6.1) | §11.1 |
| IDs alone are not enough; reuse determines benefit (F3-A §6.2) | §11.8.3, §11.17.3 |
| Three compression levels (F3-A §6.3) | §11.5 (concept), §11.6 (frame), §11.13.1 (pattern) |
| Fixed vs variable-length integers (F3-A §6.4) | §11.4 |
| Global and local IDs (F3-A §6.5) | §11.5 |
| Frame-specific encoding (F3-A §6.6) | §11.6 |
| Optional roles and presence bitmaps (F3-A §6.7) | §11.6.2 |
| Recursive and graph encoding (F3-A §6.8–6.9) | §11.7 |
| Structural hashing and content-addressed templates (F3-A §6.10–6.11) | §11.10 |
| Frequent semantic pattern compression and template worth (F3-A §6.12–6.13) | §11.13.1 |
| Generalization separate from compression (F3-A §6.14) | §11.16.3 |
| Entropy coding and conditional coding (F3-A §6.15–6.16) | §11.13.2–§11.13.3 |
| AI as compression predictor (F3-A §6.17) | §11.13.5 |
| USBF format (F3-A §6.18) | §11.7.5, §11.12 |
| Grammar versioning, self-contained vs external (F3-A §6.19) | §11.12.5, §11.14 |
| Random access vs maximum compression (F3-A §6.20) | §11.12.2 |
| Domain partitioning and compression (F3-A §6.21) | §11.5.4, §11.12.3 |
| Numerical comparison, correct metric, MDL (F3-A §6.22–6.24) | §11.17, §11.16.4 |
| Compression-aware optimizer (F3-A §6.25) | §11.16.2 |
| Memory types and compression (F3-A §6.26) | §11.2.2 |
| Compressing relationships through inference (F3-A §6.27) | §11.9 |
| Semantic compression vs ordinary text compression; refined objective (F3-A §6.28) | §11.1.3 |
| Benchmarking strategy (F3-A §6.29) | §11.17.2 |
| Encoding pipeline (F3-A §6.30) | §11.16.1 |
| Semantic round trips (F3-A §6.31) | §11.11 |
| Final storage architecture (F3-A §6.32) | §11.2 |
| Decisions table (F3-A §6.33) | below |
| Sparse graph storage, SQLite, dense-matrix cost (F1-D §2.14, §2.24) | §11.3, §11.3.5 |
| Logical vs physical representation, hybrid layering (F1-D §2.4–2.5) | §11.2.3, §11.3.1 |
| Reversible mode and its limits (F1-A §3.15) | §11.15 |
| RDF as interchange (F1-D §2.21) | §11.18 |

### Decision table (the F3-A §6.33 rows, finalized)

| Design issue | Decision | Where |
|---|---|---|
| Semantic identity | Stable global IDs | Part 2 §2.4 |
| Binary representation | Independent of global identity | §11.5 |
| Integer encoding | Minimal varints, zigzag, fixed LE for headers. Benchmark against fixed width. | §11.4 |
| Frame storage | Ordered roles, presence bitmap, exception list, basis plane | §11.6 |
| Nested semantics | Node table, backward references, shared nodes | §11.7 |
| Duplicate structures | Deduplicate immutable definitions and pure templates, never events or referents | §11.10 |
| Local dictionaries | Use when `R(g − l) > D·g`. Two-tier. | §11.5 |
| Generalization | Semantic abstraction separate from compression | §11.16.3 |
| Pattern compression | Promote only if `N(F − R) > D + I` with margin | §11.13.1 |
| Domain optimization | Domain codebooks and context dictionaries where measured to help | §11.5.4, §11.13.3 |
| Inference | Store foundational relations. Selectively cache derivations. | §11.9 |
| Retrieval | Indexed, independently decodable blocks | §11.12 |
| Versioning | Explicit grammar, ontology, frame-version pins. Critical-flag rule. | §11.14 |
| Correctness | Exact round trip on canonical IR, preservation matrix, hardened decoder | §11.11, §11.14 |
| Benchmarking | Against conventional compression and compressed structured formats | §11.17 |

### Rules registered in this part

| Rule | Statement |
|---|---|
| SG-ENC-001 | Exact round trip on canonical serialization |
| SG-ENC-002 | Encodings preserve the features required by the declared mode (preservation matrix) |
| SG-ENC-003 | Decoders pin versions, reject unknown critical structure, and never guess |
| SG-ENC-004 | Structural sharing only for immutable definitions and pure templates |
| SG-ENC-005 | The optimizer cannot alter authoritative definitions |
| SG-ENC-006 | Templates only when the corrected inequality holds with margin and the pattern is semantically valid |
| SG-ENC-007 | Decoder hardening against hostile input |
| SG-ENC-008 | Tier B is derived and rebuildable. It is never authoritative. |

### Enhancements introduced in this part

| ID | Issue | Resolution |
|---|---|---|
| E-09 (completed) | One presence bit cannot show hole states or basis | Presence bitmap, exception list, basis plane (§11.6.2) |
| E-10 (completed) | Template inequality ignored per-instance parameters and index cost | `N(F − R) > D + I`, with the variable part cancelling (§11.13.1) |
| E-22 (completed) | Round-trip equality lacked a canonical form | Eight-rule canonical serialization and canonical-bytes equality (§11.11) |
| E-24 (completed) | RDF, OWL, SHACL, PROV-O interop was unmapped | Mapping with an explicit loss declaration (§11.18) |
| E-100 | The 16-byte payload estimate omitted referents, operators, basis, and provenance | Complete-record sizing and a break-even model with sensitivity (§11.8.3, §11.17.3) |
| E-101 | See E-10 | |
| E-102 | See E-09 | |
| E-103 | See E-22 | |
| E-104 | Local-dictionary accounting counted explicit pairs only, and frequency order conflicted with delta coding | Implicit positions and a two-tier dictionary (§11.5) |
| E-105 | A weak baseline would make the semantic format look better than it is | Compressed-JSON and codec baselines, plus per-block trained dictionaries (§11.17.2) |
| E-106 | The decoder is an attack surface for external files | Hardening rules and mandatory fuzzing (§11.14.4) |
| E-107 | See E-24 | |
| E-108 | The bitmap length depends on the frame version at encoding time | Decode under pinned version, migrate separately (§11.14.2) |
| E-109 | Reversible mode could be assumed to be small | Honest lower bound, R1 first, R3 deferred (§11.15.2) |
| E-110 | Forward references force two-pass decoding | Children-first order and backward distances (§11.7.2) |


---



# Universal Semantic Grammar (USG): Specification v1.0-draft
## Part 12 of 12: Technology, Testing, the Kernel, Roadmap, Traceability, and Closure

This final part turns the specification into something you can build and measure. It selects the technology, defines the benchmark and tests, specifies the first runnable kernel with acceptance criteria, orders the work, and closes the books on the sources. It ends with a traceability matrix from every section of every source file to the place in this specification that implements it, so that no point is silently lost. It also states what I did not do and which decisions only you can make.

---

## 12.1 Technology stack

### 12.1.1 Decision

[F3-C §8.1, §8.23, §8.31] The system is built around the Semantic Grammar, not around an AI model (Architecture B in F3-C §8.1). A small Python core coordinates specialized libraries, and the AI model is one replaceable service.

**Minimum core for the first version** (F3-C §8.31): **Python + spaCy + Ollama + Pydantic + SQLite + pytest.**

Then, in this order: WordNet and FrameNet for lexical and frame coverage, Sentence Transformers for candidate retrieval, NetworkX for controlled generalization experiments, and finally, only if needed, RDFLib + pySHACL + an OWL-capable reasoner for formal ontology integration.

| Component | Choice | Priority | Stage | Notes |
|---|---|---|---|---|
| Language | Python | Essential | Kernel | |
| Local AI runtime | Ollama | Essential | Kernel | Behind the `SemanticModel` interface (Part 8 §8.11) |
| Alternative runtime | llama.cpp | Experimental | After kernel | For finer control of generation constraints and resources |
| Structured output validation | Pydantic | Essential | Kernel | Checks form only (VC-S01) |
| Linguistic analysis | spaCy | Essential | Kernel | English first |
| Alternative parser | Stanza | Evaluation | Kernel (comparison) | Universal Dependencies. Needed for the multilingual aim. |
| Semantic foundation | Custom typed frame system | Essential | Kernel | Parts 2–4 |
| Lexical knowledge | WordNet | Early | Kernel (small subset) | Sense candidate retrieval |
| Semantic frames | FrameNet | Early research | After kernel | Evaluate before writing many custom frames |
| Verb semantics | VerbNet / PropBank | Later | After kernel | Valence patterns, role-extraction evaluation |
| Semantic graph examples | AMR | Early research | Evaluation only | Not a storage format |
| Persistent database | SQLite | Essential | Kernel | WAL. Single writer. |
| Full-text retrieval | SQLite FTS5 | Early | Kernel | |
| Embedding model | Sentence Transformers | Early | After kernel | Retrieval only (SG-IDN-004) |
| Vector index | FAISS | When needed | Later | Exact search first |
| Graph algorithms | NetworkX | Early | After kernel | Bounded subgraphs only |
| RDF interoperability | RDFLib | Later | Later | Part 11 §11.18 |
| Graph constraint validation | pySHACL | Later | Later | When ontology complexity justifies it |
| Ontological reasoning | OWL-compatible reasoner | Later | Later | Selective use |
| Orchestration | `asyncio` | Essential | Kernel | I/O only (Part 10 §10.3.6) |
| CPU parallelism | Worker processes | When needed | After kernel | Graph matching, batch jobs |
| Testing | pytest | Essential | Kernel | |
| Property-based testing | Hypothesis | Early | Kernel | |
| Compression codecs | zlib / lzma (standard library); zstd if available | Early | Benchmark | Part 11 §11.13.4 |

The stack is deliberately conservative. There is no distributed system, no graph-database server, no multi-agent framework, and no multiple simultaneous language models until the need is proven [F3-C §8.23, §8.28].

### 12.1.2 Technology Manifest (Enhancement E-113)

Reproducibility needs more than "use spaCy". Every build records a **Technology Manifest**:

```text
TechnologyManifest
  python_version, os, hardware_profile (RAM, CPU, GPU/VRAM, disk type and free space)
  lockfile_hash                       exact versions of all Python dependencies
  sqlite_version, compile_options     (STRICT, FTS5, JSON functions, WAL, max attached databases)
  parser: tool, version, language model name + version + hash, label_map_id
  models: runtime + version; each model: id, quantization, file hash, licence, context length
  embedding model: id, version, dimension
  resources: name, version, licence, import date, subset definition
  verification_gate_results           §12.2
```

Certificates already record model, prompt template, and parameters (Part 5 §5.8.2). The manifest records the environment they ran in. Results are not comparable across manifests unless the manifest is the same.

---

## 12.2 Technology verification gate (Enhancement E-25)

The sources describe the capabilities of external tools as of when they were written. Tools change, so each of the claims below must be re-checked **before it is depended on.**

**I did not run this gate.** It requires access to your machine and current documentation. Items marked "assumed" are claims taken from the sources or from general knowledge, not confirmed here. I can run the web checks as a separate step if you want (§12.15).

| # | Claim relied on | Verify | Pass criterion | Fallback |
|---|---|---|---|---|
| G-01 | Current CPython release suitable for all dependencies | Install in a clean environment with the lockfile | All tests import and run | Pin an older supported release |
| G-02 | SQLite supports STRICT tables, FTS5, JSON functions, WAL, and window functions | `sqlite3.sqlite_version`, run feature probes | All probes pass | Drop STRICT and rely on `CHECK` constraints, or bundle a newer SQLite |
| G-03 | `ATTACH` limit for domain partitions (Part 10 §10.6.4) | Read the compile option, test attaching *n* databases | Limit known and recorded | Single database, or an LRU of attached partitions |
| G-04 | spaCy offers dependency parsing and a dependency matcher for English; the label scheme of the chosen model is known | Load the model, inspect the label set, run the label-map tests | Label map covers all abstract grammatical functions of Part 8 §8.3.4 | Use Stanza (UD labels) |
| G-05 | Arabic parsing models exist and perform acceptably | Evaluate on a small Arabic gold set (Part 8 §8.14.4) | Meets the same acceptance criteria as English | Defer Arabic |
| G-06 | Ollama supports JSON-schema constrained structured output through its Python client | Run schema-constrained generation and check conformance | 100% schema-valid output on the test suite | Use llama.cpp grammars, or validate and retry |
| G-07 | Ollama supports deterministic sampling (seed, temperature 0) giving identical outputs on repeat | Repeat runs *N* times on one machine | Identical output, or the variance is measured and recorded | Cache and treat as non-deterministic |
| G-08 | llama.cpp supports grammar- or schema-constrained generation | Run the equivalent probes | As G-06 | Stay with Ollama |
| G-09 | Candidate local models fit the memory budget and run at acceptable speed | Run the model-selection protocol (§12.5) | Fits §10.13.2 budget, p95 latency within target | Smaller model or quantization |
| G-10 | Model licences allow your intended use, including any remote use of a reviewer | Read each licence and record it | Recorded and acceptable | Substitute another model |
| G-11 | Sentence Transformers model produces embeddings at acceptable CPU speed and size | Benchmark throughput and memory | Meets budget | Smaller model, or lexical retrieval only |
| G-12 | NetworkX provides the matching algorithms needed (graph and subgraph isomorphism) | Probe on the bounded structure sizes of Part 9 §9.11 | Completes within the step budget | Custom bounded matcher |
| G-13 | pySHACL and RDFLib versions work together. RDF 1.2 statement-level features are available (assumed unavailable until checked). | Probe | Export and validation tests pass with named graphs | Named graphs only |
| G-14 | Compression codecs available. zstd (and trained dictionaries) availability depends on the Python version or an additional package. | Probe | Codec list recorded | zlib and lzma only |
| G-15 | Resource licences and terms (WordNet, FrameNet, VerbNet, PropBank, ConceptNet, Wikidata, AMR corpora) permit the planned use. Terms differ, and some corpora require a licence. | Read and record each | Every imported resource has a recorded licence note | Exclude the resource |
| G-16 | The hardware profile matches the memory worksheet assumptions | Measure real peak memory under the kernel workload | Peak RAM ≤ budget | Reduce workspace capacity, model, or concurrency |
| G-17 | `hypothesis`, `pytest` versions are compatible | Run the suite | Green | Pin |

**Procedure.** A gate item is run once per environment and again when the lockfile, model, or resource changes. Results go in the manifest. A failed item blocks the components that depend on it and triggers its fallback. No gate item is silently skipped.

---

## 12.3 Package architecture

[F3-C §8.24] The target structure follows the logical architecture. It is a **target**, not a recommendation to implement every file immediately. The kernel uses a much smaller subset. Several modules can start in one file and be split when their responsibilities diverge [F3-C §8.24].

```text
universal_semantic_grammar/
├── core/            semantic_types · expressions · frames · roles · references · ids · canonical      (Parts 2–4, 11 §11.11)
├── grammar/         rulebook · construction · canonicalization · type_checker                         (Parts 3, 5)
├── interpretation/  linguistic_parser · label_maps · semantic_parser · context_integrator
│                    frame_resolver · valence · operators · coreference · figurative                   (Part 8)
├── concepts/        semantic_hub · concept_resolver · identity_validator · registry · lexicon         (Parts 2, 7)
├── validation/      schema_validator · evidence_validator · rule_validator · certificate
│                    review_manager · risk · calibration                                               (Parts 5–6)
├── cognition/       central_controller · workspace · task_scheduler · metacognition · governor        (Part 10)
├── learning/        lexical · concept · knowledge · grammar · candidate_store · promotion             (Part 9)
├── generalization/  structural_signatures · graph_matching · analogy_engine · counterexample_engine   (Parts 4, 9)
├── memory/          semantic_memory · episodic_memory · procedural_memory · retrieval · activation    (Part 10)
├── storage/         database · schema · indexing · transactions · audit · queue                       (Part 11 §11.3)
├── encoding/        usbf_codec · local_dictionary · canonical_bytes · compression · optimizer         (Part 11)
├── models/          model_interface · ollama_backend · llama_cpp_backend · gateway · embedding        (Parts 5, 8)
├── security/        normalization · tripwires · limits · egress · integrity                           (Part 6 §6.13)
├── resources/       wordnet · framenet · verbnet · propbank · alignment                               (Part 8 §8.13)
├── benchmark/       gold · scoring · runner · reports                                                 (§12.6)
├── config/          defaults · profiles · constants register                                          (§12.10)
└── tests/           grammar · frames · concepts · interpretation · validation · generalization
                     · encoding · retrieval · security · concurrency · benchmark
```

**Dependency rule (Normative, Enhancement E-112 extension):** dependencies point downward through three layers only: `core` and `storage` have no dependency on `interpretation`, `models`, or `learning`. The grammar and storage can be tested without any AI model. This is what makes the grammar replaceable-model-independent (P-01).

---

## 12.4 The kernel specification

### 12.4.1 Purpose and scope

[F3-C §8.29] The kernel is the smallest useful prototype. It does not implement the full brain-inspired architecture. Its single objective is to **establish semantic reliability before scalability**. "Otherwise, we risk constructing a very complex system around an unreliable semantic foundation" [F3-C §8.29].

The ten responsibilities of the source, with the specification that governs each:

| # | Kernel responsibility (F3-C §8.29) | Specified in |
|---|---|---|
| 1 | Define a small set of semantic types | Part 2 §2.2 |
| 2 | Define about 10–20 reusable frames | Part 4 §4.12.2 (**20 kernel frames**) |
| 3 | Store concepts and frame definitions | Part 11 §11.3 |
| 4 | Accept a sentence | Part 8 §8.2 |
| 5 | Ask a local model for a candidate interpretation | Part 8 §8.11 |
| 6 | Validate the candidate against the Rulebook | Part 5 |
| 7 | Resolve known concept IDs | Part 7 (R1–R2, exact and lexical) |
| 8 | Preserve ambiguity when necessary | Part 3 §3.14, Part 8 §8.9 |
| 9 | Store the candidate and its evidence | Parts 5–6, 11 |
| 10 | Evaluate the result against reference examples | §12.6 |

### 12.4.2 In and out

| In the kernel | Deferred (specified, not built) |
|---|---|
| English only | Arabic and other languages (Part 8 §8.14) |
| One SQLite database, WAL | Domain partitions (Part 10 §10.6.4) |
| 20 frames, tier-1 roles, starter relations, FN primitives, seed classes | Frame learning, LEASE-type growth |
| Rulebook subset (§12.4.4), validator L1–L4, L5 by review sample | Full rule set, SHACL, OWL |
| Interpreter: implementations A, B, C for comparison | Graduated construction patterns in production |
| Lexicon: a small curated WordNet subset | FrameNet/VerbNet import beyond the kernel frames |
| Concept resolution R1–R2 (exact and lexical), provisional concepts, registry | Embedding retrieval (R4), duplicate sweep, drift monitoring |
| Evidence vector, statuses, claim store, risk classes, manual review queue, audit sampling | Calibrated automatic review routing |
| Process history, ingest ledger | SYSTEM-domain frames (Part 10 §10.12) |
| Semantic-mode encoding as relational rows plus canonical JSON | USBF blocks, templates, entropy models |
| Round-trip tests of the canonical serialization | Reversible mode R2/R3 |
| Single controller process, one workspace per unit, one model gateway | Multiple assistant controllers as separate services |
| Learning: candidate generation only, manual promotion | Automated promotion cycles, pattern graduation |

### 12.4.3 Kernel modules

```text
 INPUT TEXT
   ↓ security.normalization · tripwires · limits
 interpretation.linguistic_parser (spaCy) + label_map
   ↓
 interpretation.semantic_parser (A: rules · B: model · C: hybrid)
   ├─ concepts.lexicon / semantic_hub (R1–R2)
   ├─ models.gateway (Ollama)  ← closed-set tasks, NONE_OF_THESE
   └─ interpretation.valence · operators · coreference
   ↓ candidate IR + certificate
 validation.rule_validator · evidence_validator · certificate replay
   ↓ ValidationReport (axis B)
 cognition.metacognition (deterministic signals) → REPAIR / ACCEPT_PROVISIONALLY / PRESERVE_AMBIGUITY / REVIEW / REJECT
   ↓
 storage (candidate → provisional records, evidence, audit)
   ↓
 benchmark.runner → scoring → report
```

### 12.4.4 Active rules in the kernel

| Domain | Rules |
|---|---|
| FND | 001–007 (all, enforced by design) |
| CON | 001–009 |
| TYP | 001, 002 |
| FRM | 001–010 (as relevant to the 20 frames) |
| INT | 001, 003–012, 020–022, 030, 031, 040, 050, 051 |
| EVD | 001–006 (007–012 minimal: statuses and independence counts recorded) |
| CAN | 001–004, 010 |
| IDN | 001–006 (exact and lexical resolution, provisional concepts) |
| GEN | 002, 003 (no generalization engine yet) |
| KNW | 001, 002, 004, 010–012 |
| GOV | 001, 002 |
| SEC | 001–006, 008, 009 |
| ENC | 001, 002, 008 |

### 12.4.5 Kernel interfaces (illustrative Python)

These show the *shape* of the contracts. They are not a full implementation.

```python
from enum import Enum
from typing import Protocol
from pydantic import BaseModel, Field, model_validator


class ValueState(str, Enum):
    SPECIFIED = "SPECIFIED"
    UNSPECIFIED = "UNSPECIFIED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    WITHHELD = "WITHHELD"


class Basis(str, Enum):
    EXPLICIT = "EXPLICIT"
    GRAMMATICAL = "GRAMMATICAL"
    BACKGROUND = "BACKGROUND"


class Span(BaseModel):
    start: int = Field(ge=0)          # code points, zero-based, end-exclusive (Part 2 §2.12)
    end: int

    @model_validator(mode="after")
    def non_empty(self):
        if self.end <= self.start:
            raise ValueError("span must be non-empty")
        return self


class RoleBindingC(BaseModel):
    role: str                          # must name a role the frame defines (VC-S06)
    value_state: ValueState
    basis: Basis | None = None
    filler: str | None = None          # workspace handle, never a bare concept id (SG-CON-003)
    span: Span | None = None
    rule: str | None = None            # e.g. "SG-INT-010"

    @model_validator(mode="after")
    def state_consistency(self):
        if self.value_state is ValueState.SPECIFIED:
            if self.filler is None or self.basis is None:
                raise ValueError("SPECIFIED requires filler and basis")
        elif self.filler is not None:
            raise ValueError("hole states must not carry a filler")
        return self


class FrameCandidate(BaseModel):
    frame: str
    frame_version: int
    bindings: list[RoleBindingC]
    alternatives_considered: list[str] = []
    unresolved: list[str] = []


class SemanticModel(Protocol):
    def run(self, task: "ModelTask") -> "ModelResult": ...      # Part 8 §8.11.1


class Validator(Protocol):
    def validate(self, candidate, ctx: "ValidationContext") -> "ValidationReport": ...  # pure (Part 5 §5.1)


class RecordStore(Protocol):
    def get(self, space: str, id_: int): ...
    def scan(self, space: str, **filters): ...
```

The validator checks `RoleBindingC` instances at VC-S01 (schema). Role names, frame existence, types, spans, rules, and evidence are checked by the later checks, which is why the schema alone is never sufficient (Part 5 §5.9).

### 12.4.6 Kernel configuration defaults

All values are provisional and live in `config/defaults.py`, with the constants register (§12.10) as the single source:

```text
max_model_calls_per_unit = 3            max_retries_per_unit = 2
max_alt_per_group = 4                   workspace_capacity = 200
sampling = deterministic (temperature 0, fixed seed)
audit_sample_rate_new_category = 0.10   risk class floor = MEDIUM for model-produced candidates until audited
retention_tier = FULL                   # kernel keeps full certificates (small corpus)
```

### 12.4.7 Kernel acceptance criteria (Enhancement E-114)

Split into two kinds. **Hard invariants** are properties the design guarantees, so any failure is a defect. **Calibrated targets** are quality levels that depend on the data, the model, and the hardware, so numbers are set only after a baseline run and recorded.

**Hard invariants** (all must hold on every run of the kernel):

| # | Invariant | Check |
|---|---|---|
| H-1 | No committed record fails L1–L3 | Re-validate the whole store |
| H-2 | Every committed assertion has source or authorized origin, and evidence | VC-V01, FND-003 |
| H-3 | No provisional ID in a trusted record | VC-S15 |
| H-4 | Every stored span lies within its source text | VC-S10 |
| H-5 | Encode/decode round trip is exact for 100% of generated and stored IR | SG-ENC-001 |
| H-6 | No candidate approved by its own producer | Audit-log check, SG-FND-004 |
| H-7 | The rulebook and validator are unchanged by any run | Hash comparison, SG-SEC-009 |
| H-8 | Every rule has passing unit tests, and the full rule regression is green | pytest |
| H-9 | Contrastive pairs (Part 5 §5.11.3) are never collapsed by canonicalization | Rule tests |
| H-10 | Injection corpus: no instruction embedded in source text changes any status, tier, rule, or mapping | Security tests (§12.7) |
| H-11 | Budgets are never exceeded and queues stay bounded | Governor tests |
| H-12 | Role bindings in hole states never contain fillers, and BACKGROUND content is never labelled EXPLICIT | VC-V03, VC-V06 |

**Calibrated targets** (initial *proposed* values, adopted only after the first baseline [Provisional]):

| Metric | Proposed starting target on the sealed test |
|---|---|
| Frame accuracy (stages 1–6 of §12.6.2) | ≥ 0.90 |
| Role-binding F1 (same stages) | ≥ 0.85 |
| Unsupported-assertion rate | ≤ 0.02 |
| False-confidence rate (gold AMBIGUOUS or UNRESOLVED answered as RESOLVED) | ≤ 0.10 |
| Invented-role rate (hole predicted as SPECIFIED) | ≤ 0.02 |
| Polarity accuracy | ≥ 0.97 |
| Selective risk at 80% coverage | ≤ 0.05 |
| Peak RAM | within the §10.13.2 budget |
| p95 end-to-end latency per sentence | within the chosen target |

A target is *met* only if the lower bound of its 95% interval (§12.6.5) meets it, so a lucky small sample cannot pass a target.

**The hybrid (implementation C) is accepted only if** it satisfies every hard invariant, meets or beats implementations A and B on role F1 and false-confidence at equal or lower cost, or explains any deficit with a measured advantage elsewhere (§12.6.6).

### 12.4.8 Kernel deliverables

1. Foundation Package files: kinds, tier-1 roles, starter relations, FN primitives, seed classes, 20 frames with tests, rules with tests (machine-readable).
2. The schema and migrations (Part 11 §11.3).
3. The interpreter implementations A, B, C and the model gateway.
4. The validator, certificate replay, metacognition signals, review queue (manual interface).
5. The gold set v1, scoring code, and the baseline report.
6. The Technology Manifest and gate results.
7. A constants register with every provisional value and its calibration status.

---

## 12.5 Model selection protocol

[F3-C §8.3–§8.4] The model is chosen by benchmark, not by parameter count. Parameter count alone does not predict performance. Quantization, architecture, context length, and the inference implementation matter as well [F3-C §8.4].

### 12.5.1 Candidates and roles

| Role | Selection constraint |
|---|---|
| A: Primary interpreter | Small to medium instruction-following model that fits the memory budget alongside everything else |
| B: Reviewer | Larger model. Local or remote subject to SEC-008. **Different model family from A** for HIGH and VERY_HIGH review (SG-GOV-003). |
| C: Embedding model | Dedicated small embedding model |

Use three to five candidates for role A across the available size classes (small 1–4B, medium 7–9B, larger 12–30B+ are the experimental ranges of F3-C §8.4), plus one or two for role B. Candidates must have licences that permit your use (gate G-10).

### 12.5.2 Tests

Each candidate runs the **same** narrow tasks (Part 8 §8.11.2) on the same dev units, with the same candidate sets and prompts:

| Task | Measured |
|---|---|
| SENSE_SELECT, FRAME_SELECT | Accuracy against gold, correct use of NONE_OF_THESE |
| ROLE_ASSIGN | Binding F1, invented-role rate |
| COREF | Link accuracy, ALT use |
| SCOPE and MODAL_FLAVOR | Accuracy, ALT use |
| FULL_EXTRACT | All of the above in one call, schema-valid rate |
| Injection probes | Resistance (Part 6 §6.13) at the gateway level |

Also measure: schema-valid rate, repeat-run determinism (identical output across runs), latency p50 and p95, tokens per call, peak RAM (including context growth), and failure behavior (does it abstain, or invent?).

### 12.5.3 Selection rule

1. Discard models that fail the memory budget, the injection probes, or determinism requirements (or whose non-determinism is unmeasured).
2. Among the rest, discard models whose **false-confidence** or **unsupported rates exceed the targets** of §12.4.7 on the dev set.
3. Choose the model with the highest role F1 (paired bootstrap, §12.6.5). If differences are not significant, choose the cheaper model.
4. Re-run on the **sealed test** exactly once for the chosen model.

Correctly recognizing uncertainty may be more valuable than confidently producing a complete interpretation [F3-C §8.4], so rules 1–2 outrank accuracy.

---

## 12.6 The benchmark

### 12.6.1 Purpose

Before selecting the final model, building the learning loop, or scaling, there must be a reference with manually reviewed semantic representations [F3-C §8.21, F1-A §3.16]. Metrics based on comparing a model with itself are not reliable [F3-B §7.28].

### 12.6.2 Composition

The ten stages of increasing difficulty come from F1-A §3.16 (Part 8 §8.16). The categories of F3-C §8.21 add coverage. Target counts are provisional.

| Category | Example | Tests | Units |
|---|---|---|---:|
| Property | The car is red. | Entity–property | 20 |
| Action | The boy eats an apple. | Semantic roles | 20 |
| Transfer | John gave Mary a book. | Multiple participants | 25 |
| Voice | Mary was given a book by John. | Role preservation | 30 |
| Negation | John did not sell the car. | Negation scope | 30 |
| Modality | John might sell the car. | Modal force and flavor | 25 |
| Nested events, control | John wants Mary to leave. | Recursion, control | 25 |
| Coreference | John bought a car. He repaired it. | Reference resolution | 25 |
| Ambiguity | John saw the man with a telescope. | Retained ALT | 25 |
| Causation | The engine stopped because it overheated. | Source-attributed explanation | 20 |
| Figurative | The computer swallowed the file. | FIG, registered senses | 15 |
| Generalization (IR-level) | heart / pump / fan | Abstraction gates | 15 |
| Temporal | John arrived before Mary left. | Allen relations, resolution | 15 |
| Quantifiers | John did not eat every apple. | Q scope | 15 |
| Holes | The patient was examined. | UNSPEC discipline | 20 |
| Unknown words | A hygrometer measures humidity. | Provisional path | 10 |
| **Subtotal** | | | **335** |
| Contrastive and metamorphic **pairs** | gave/offered, tried/opened, may/must, … (Part 5 §5.11.3) | Over-normalization | 40 pairs (80 units) |
| **Total** | | | **≈ 415** |

The negative-pair categories matter because "excessive canonicalization" and under-extraction are different failures [F3-B §7.22].

### 12.6.3 Gold set protocol (Enhancement E-115)

| Step | Requirement |
|---|---|
| Guidelines | A written annotation guide covering frames, roles, hole states, basis, operators, ALT, referents, and every ambiguity convention |
| Annotation | Two independent annotators per unit. A third adjudicates disagreements. Annotators see the source and context only, not the system's output. |
| Agreement | Report Cohen's kappa for frame choice and per-role agreement. Units with unresolved disagreement are *kept* and labelled AMBIGUOUS (if the humans genuinely disagree, the sentence is probably ambiguous). |
| Content | `expected_ir`, `allowed_variants` (ALT sets), `must_not_contain`, `preserved_dimensions`, `rules_exercised`, and gold outcome (RESOLVED, AMBIGUOUS, UNRESOLVED) |
| Splits | **Dev/train ≈ 60%** (≈ 250 units) for building rules, examples, and tuning. **Sealed test ≈ 40%** (≈ 165 units), never used for tuning, used once per release candidate and refreshed when exposed. Pairs stay in the same split. [Provisional] |
| Contamination | No gold sentence may appear in prompts, example banks, or lexicon definitions. Checked by hash and normalized-text match. |
| Growth | Reviewer corrections and audit findings (Part 6 §6.10.3) add new gold units to *dev*. The sealed test grows only by new blind annotation. |

### 12.6.4 Metrics (Enhancement E-16, completed)

Every metric has a precise definition so results are comparable.

**Per-unit matching.** A predicted frame instance matches a gold one if the frame (at the same or a declared-compatible version) is the same. A predicted binding matches if role, filler (referent matched by span and class), value state, and basis agree.

| Metric | Definition |
|---|---|
| Frame accuracy | Correct frame selected / gold units with an expected frame |
| Role-binding precision, recall, F1 | Over bindings with value state SPECIFIED. A binding counts only if role and filler match. |
| Value-state accuracy | Correct value state over all gold roles (separates SPECIFIED from UNSPECIFIED, UNKNOWN, NOT_APPLICABLE, WITHHELD) |
| **Invented-role rate** | Roles predicted SPECIFIED where gold is UNSPECIFIED / gold UNSPECIFIED roles. This is the "no invented content" measure. |
| Basis accuracy | Correct basis among matched bindings. **BACKGROUND-labelled-as-EXPLICIT count** reported separately (must be 0 in committed records). |
| Polarity, modality, tense, aspect, quantifier-scope accuracy | Exact match of the operator structure, per category |
| Referent and coreference link F1 | Links between referents, scored against gold clusters |
| Ambiguity handling | Of gold-AMBIGUOUS units: share retained as ALT. Of predicted ALTs: share where gold is AMBIGUOUS. |
| Unsupported-assertion rate | Elements failing VC-V01/V02/V06 on audit / elements audited |
| Concept-resolution accuracy | Part 7 §7.14 |
| Duplicate-concept and incorrect-merge rates | Part 7 §7.14 |
| Rule-violation rate | Candidates with ≥ 1 L1–L4 FAIL / candidates produced (before repair) |
| Repair success | Candidates that became FORMALLY_VALID after repair / candidates that needed repair |
| Reviewer disagreement rate | Reviews whose findings differ from the producer's output / reviews |
| Peak RAM, time per unit, model calls per unit, tokens per unit | Measured under the workload |
| Database growth | Bytes per processed unit, by table |
| Encoding size | Part 11 §11.17 |
| Retrieval latency | p50 and p95 for one record, one neighbourhood |

**Growth indicators** (Part 9 §9.11) are reported in each release report: frames per 1,000 processed units, instances per frame, share of single-instance frames, relation-type count, abstraction depth, share of candidates rejected.

### 12.6.5 Abstention-aware scoring and statistics (Enhancement E-16, E-115)

A low unresolved rate is not automatically better. "A system that guesses on every ambiguous sentence may appear more productive while being less reliable" [F3-C §8.22]. Correctness and appropriate abstention are scored together.

Each system output has an **answer** (RESOLVED with an interpretation) or an **abstention** (AMBIGUOUS retained, or UNRESOLVED). Define:

| Quantity | Definition |
|---|---|
| Coverage *c* | Answered units / all units |
| Selective risk *r(c)* | Error rate among answered units, with units ordered by decreasing system confidence signal (the deterministic signals of Part 6 §6.9.2 as an ordinal score) |
| Risk–coverage curve | *r* as a function of *c*. Report *r* at *c* = 0.6, 0.8, 1.0 and the area under the curve. |
| Appropriate abstention | Abstentions on gold AMBIGUOUS or UNRESOLVED units / those gold units |
| **False confidence** | Gold AMBIGUOUS or UNRESOLVED units answered RESOLVED / those gold units |
| Unjustified abstention | Gold RESOLVED units on which the system abstains / gold RESOLVED units |
| Expected cost | `c_err · (#wrong answers) + c_abs · (#abstentions)`. [Provisional: `c_err : c_abs = 5 : 1`, to be set by how costly a wrong committed fact is in your use.] |

**Confidence intervals.** Binary proportions use the Wilson score interval. Example: observed 90% on n = 100 gives roughly [82.6%, 94.5%] (about ±6 points). On n = 400 it gives about [86.7%, 92.6%] (about ±3 points). On the sealed test of ≈165 units it is about ±4.6 points. Small benchmarks therefore cannot distinguish small differences, and the report states this.

**Comparing systems.** Paired bootstrap over units (same units, same split), 95% intervals on metric differences. A difference is "real" only if the interval excludes zero. With few units per category, per-category results are descriptive, not conclusive.

### 12.6.6 Comparing the three implementations

[F1-A §3.16] Implementations A (rules and parser), B (local model producing structured semantics), and C (hybrid) run under identical conditions: same units, same hardware, same budgets.

Report every metric of §12.6.4 and the risk–coverage curves. **Decision rule:** among implementations satisfying the hard invariants and the false-confidence and unsupported-assertion targets on the dev set, choose the one with the highest role F1 (paired bootstrap), then the lower cost. The chosen implementation is run once on the sealed test.

The hypotheses being tested (not assumed):
- C beats B on unsupported-assertion rate and invented-role rate because it grounds more steps in rules.
- C beats A on coverage of unfamiliar constructions.
- Decomposed narrow tasks (Part 8 §8.11.2) beat FULL_EXTRACT on false-confidence at equal or lower cost.

If a hypothesis is wrong, the design changes, not the benchmark.

### 12.6.7 The benchmark for later components

| Component | Benchmark | Defined in |
|---|---|---|
| Concept resolution | Part 7 §7.14.2 gold pairs | Part 7 |
| Generalization | A small set of structures with known valid and invalid abstractions and counterexamples (heart/pump/fan, dog/cat/animal, lease/rent/lend) | Part 9 §9.9 |
| Encoding | The variants A–I on identical IR | Part 11 §11.17 |
| Security | The injection and hostile-input corpus | §12.7 |
| Concurrency | Simultaneous proposal scenarios | Part 7 §7.14.3 |

---

## 12.7 Test strategy

[F3-C §8.19–§8.20; Part 5 §5.11]

### 12.7.1 Principles

1. **Rules are tested independently of any model.** This isolates errors to the model, the parser, the frame definitions, the concept resolver, the rule implementation, or the validator [F3-C §8.19].
2. **Every rule has valid, incomplete, invalid, and contrastive examples** (SG-FRM-008 and Part 5 §5.3).
3. **Stage-isolated test modes** (Part 5 §5.11.4) locate failures.
4. **Gold data is split** (train/dev/sealed) and the sealed set is untouched by tuning.

### 12.7.2 Test layers

| Layer | Contents | Tooling |
|---|---|---|
| Rule unit tests | Each rule's examples against gold parses | pytest |
| Validator tests | Gold and deliberately corrupted IR. Every check has a fault-injection case. | pytest |
| Property-based | Valid IR generator. Validator determinism and totality, canonicalization idempotence and validity preservation, alpha-renaming invariance, binary round trip, single-fault detection | Hypothesis |
| Metamorphic | The relation table of Part 5 §5.11.2 | pytest, runtime option (Part 10 §10.11.2) |
| Contrastive | Negative pairs (Part 5 §5.11.3) | pytest |
| Integration | Source → candidate → validate → store → retrieve | pytest with a fake model (scripted outputs) |
| Fake-model tests | Scripted malicious and sloppy model outputs: invented IDs, wrong roles, missing spans, schema-valid nonsense | pytest |
| Concurrency | Part 7 §7.14.3 scenarios, queue and writer behavior, crash and restart (Part 10 §10.14) | pytest, process-level tests |
| Security | Injection corpus, hidden characters, homoglyphs, giant inputs, deep nesting, ALT explosion, quarantined sources trying to promote | pytest |
| Fuzz | USBF decoder, JSON ingestion, span handling | Hypothesis, or a coverage-guided fuzzer |
| Drift and versioning | Defining-constraint change forces version bump and impact list. Old versions still decode. | pytest |
| Performance and memory | Throughput, latency, peak RAM against budgets. Governor degradation behaviour. | pytest with measurement hooks |
| End-to-end benchmark | §12.6 | Benchmark runner |
| Cross-version fixtures | Every published format and grammar version | pytest |

Test directories: `grammar/`, `frames/`, `concepts/`, `interpretation/`, `validation/`, `generalization/`, `encoding/`, `retrieval/`, `security/`, `concurrency/`, `benchmark/` [F3-C §8.20 plus the additions].

### 12.7.3 CI gates (Enhancement E-116)

| Gate | Blocks |
|---|---|
| All rule and validator tests, property tests, round-trip tests green | Any merge |
| No change to Level 1 rules or the validator without the governed release path | Any merge touching them |
| Contrastive-pair tests green | Any change to canonicalization or interpretation rules |
| Dev benchmark regression within noise (paired bootstrap) | Any change to prompts, rules, patterns, or models |
| Sealed-test evaluation | Release candidates only, once each |
| Fuzz suite and security corpus | Any change to the decoder or the model gateway |
| Manifest and gate results attached | Any release |

---

## 12.8 Roadmap

The sources' original roadmap (F1-A §3.18) listed the parts to come after "discovering meaning". The mapping:

| Source roadmap part | Subject | Specified in |
|---|---|---|
| 4 | Formal Semantic Grammar | Parts 2–5 |
| 5 | Semantic IR and universal concept identification | Parts 2, 3, 7 |
| 6 | Automatically building the dictionary, avoiding duplication | Parts 7, 9 |
| 7 | Binary encoding and compression | Part 11 |
| 8 | Libraries, models, databases, architecture | Part 12 §12.1, Part 10 |
| 9 | First working prototype | Part 12 §12.4 |
| 10 | Benchmarking and improvement | Part 12 §12.6 |

The research question the source added, *can frequently recurring semantic structures be discovered automatically and turned into reusable grammar rules?*, is the subject of Part 9 and is explicitly deferred until the kernel is reliable [F1-A §3.18].

### 12.8.1 Build order

[F1-C §18; F3-C §8.29; Part 10 §10.15.2] No calendar estimates are given. The order is by dependency. Each milestone has an exit criterion, and the next starts only when it is met.

| Milestone | Work | Exit criterion |
|---|---|---|
| **M0 Environment** | Repository, config, hardware profile, technology gate (§12.2), manifest | Gate results recorded. Blocking items resolved or fallbacks chosen. |
| **M1 Core data model** | IDs, registry, schema, Pydantic models, canonical serialization, relational encode/decode | H-5 round-trip and H-4/H-3 invariants pass on generated IR |
| **M2 Foundation Package and validator** | Kinds, roles, relations, FN, 20 frames with tests, rules with tests, validator L1–L4, error codes | H-1, H-8, H-9, H-12 pass. Every check has a fault-injection test. |
| **M3 Deterministic interpreter (A)** | spaCy parser, label map, lexicon subset, valence patterns, operator cues, time resolution | Stages 1–6 of the benchmark meet provisional targets using rules alone, and failures are classified |
| **M4 Model integration (B, C)** | Model gateway, closed-set tasks, certificates, repair loop, metacognition signals | Fake-model and injection tests pass (H-10). Implementations B and C run end to end. |
| **M5 Benchmark and selection** | Gold set v1, scoring, baseline report, implementation comparison, model selection | Report with intervals. The decision rule of §12.6.6 applied. Sealed test run once. |
| **M6 Concept resolution** | Lexicon, provisional concepts, registry concurrency, pending-proposal visibility, idempotency | Part 7 §7.14.3 tests pass |
| **M7 Epistemics and review** | Statuses, evidence vector, claim store, risk classes, audit sampling, manual review queue, calibration | Audit-based classes operating. Review decisions logged and used to grow gold data. |
| **M8 Encoding experiments** | Variants A–I, USBF prototype, local dictionaries, benchmark with strong baselines | Report per Part 11 §11.17. A go/no-go decision on USBF. |
| **M9 Learning loop (candidates)** | Candidate store, promotion controller, lexical and knowledge learning, ingest ledger, learning cycle gates | Cycle report produced. No unauthorized promotion (H-6). |
| **M10 Pattern graduation and generalization experiments** | Construction patterns with audits, signatures, NetworkX matching, counterexample engine, analogy engine on two domains | Part 9 §9.20 example reproduced, and gates behave as specified, including the duplicate and counterexample paths |
| **M11 Second language and partitioning decision** | Arabic evaluation under the same criteria. Measured decision on domain partitions. | Meets criteria, or documented deferral |

### 12.8.2 Decision points that can change the plan

| After | Question | Possible change |
|---|---|---|
| M5 | Does the hybrid beat A and B? Is decomposition worth it? | Simplify to the best implementation |
| M5 | Is the model's false-confidence acceptable? | Larger or different model, narrower tasks, stricter routing |
| M8 | Does semantic encoding pay against compressed text and compressed JSON? | Store only relational rows plus a general codec, drop USBF |
| M10 | Do abstractions pass gates and survive counterexamples at useful rates? | Narrow the generalization scope, or require human approval for all of it |

The system's usefulness does not depend on beating text compression (Part 1 §1.3). It depends on reliable interpretation.

---

## 12.9 Consolidated risk register

[F1-C §20 plus risks found in this specification]

| Risk | Where it arises | Mitigation | Residual |
|---|---|---|---|
| Unreliable semantic interpretation | Model behaviour | Closed-set tasks, certificates, five-level validation, replay, review, audit-based calibration (Parts 5–6, 8) | Cannot be eliminated. Abstention is allowed. |
| Architectural complexity | Many modules and planes | Kernel scope, module contracts, purpose test, build order | Moderate |
| Expensive graph maintenance | Matching, reprocessing | Bounded matching, budgets, background priorities, rebuildable derived data | Moderate |
| Storage cost higher than expected | Detailed representation | Total-cost measurement, strong baselines, relational fallback | Measured at M8 |
| Wrong merges | Identity | Reversible mappings, read-time resolution, VERY_HIGH review | Low |
| Grammar growth without benefit | Learning | Demand aggregation, growth ladder, budgets, gates | Moderate |
| Hostile or poisoned input | Open text | SEC-001…010, quarantine, caps, independence counting | Moderate |
| Gold data too small or biased | Benchmark | Double annotation, sealed set, intervals, growth from audits | Moderate. Stated in every report. |
| Overfitting rules to the benchmark | Development | Sealed test used once per release, contamination checks | Low–moderate |
| Dependence on a specific tool or model version | Technology | Interfaces, manifest, gate, pinned versions | Low |
| Licence or privacy problems | Resources and remote review | Licence records, SEC-008, local-only default | Low if followed |
| Memory exhaustion on a personal computer | Models and caches | Worksheet, governor, degradation ladder, model choice by hardware | Moderate |
| Provisional constants treated as fact | Many [Provisional] values | Constants register with calibration status (§12.10) | Low |
| Specification drift from implementation | Process | Rule IDs, tests tied to rules, change control | Moderate |

---

## 12.10 Provisional constants register (Enhancement E-112)

Throughout the specification, numeric choices are marked [Provisional] because the sources say they must be determined by benchmark. They are collected here, and each is stored in configuration. Every change records the benchmark run that justified it.

| Constant | Initial value | Defined in | Calibrated by |
|---|---|---|---|
| ALT alternatives per group | 4 | Part 3 §3.14 | Benchmark ambiguity cases |
| Max retries per unit | 2 | Part 5 §5.7 | Repair-success rate |
| Minimum independent occurrences for a pattern (N) | 3 | Part 6 §6.12.2, Part 9 §9.8.3 | Pattern precision |
| Audit sample rate, new category | 10% | Part 6 §6.10.3 | Audit yield |
| Wilson *z* for upper bound | 1.645 | Part 6 §6.10.3 | Policy |
| Tolerated error rate per risk class (τ) | Set per class at M7 | Part 6 §6.10.3 | Cost of error |
| Near-duplicate threshold (shingle similarity) | Set at M7 | Part 6 §6.5.3 | Duplicate corpus |
| Calibration (ECE) threshold and minimum samples per bin | Set at M7 | Part 6 §6.10.4 | Gold set |
| Provisional-concept TTL | 30 days inactive | Part 7 §7.9.2 | Backlog data |
| Model calls per sentence | 3 | Part 8 §8.11.7 | Benchmark |
| Min audited sample and error bound to graduate a pattern | Set at M10 | Part 8 §8.12 | Audits |
| Min independent origins for a grammar candidate / relation type (k) | 3 | Part 9 §9.6.3, §9.7.5 | Candidate quality |
| Reuse floor *m*, coverage cap *c*max | 3, 0.25 | Part 9 §9.9.5 | Benchmark structures |
| Match structure size, steps, depth, candidates, new frames per cycle | 12, bounded, 4, 100, 5 | Part 9 §9.11 | Runtime and yield |
| Consequence-chain depth | 3 | Part 9 §9.19.1 | Precision of held candidates |
| Canary period | Set at M9 | Part 9 §9.15.2 | Stability |
| Workspace capacity | ≈ 200 | Part 10 §10.4.3 | Memory and quality |
| Usable-RAM fraction `f_safe` | 0.8 | Part 10 §10.13.2 | Measured headroom |
| Activation α, θ, depth, top-k, fan-out cap, relation gains | Table in Part 10 §10.7.2 | Part 10 | Retrieval quality on benchmark |
| Heat half-life | Set at M6 | Part 10 §10.7.4 | Cache hit rates |
| Dead-letter attempts | 3 | Part 10 §10.14 | Failure data |
| Tier-1 dictionary boundary, block sizes, size tolerance *x* | 128, 16 KiB–1 MiB candidates, 5% | Part 11 §11.5.3, §11.12.2 | Encoding benchmark |
| Template safety margin | 1.5× | Part 11 §11.13.1 | Reuse statistics |
| Cost ratio `c_err : c_abs` | 5 : 1 | §12.6.5 | Your cost of a wrong committed fact |
| Gold-set size and split | ≈415 units, 60/40 | §12.6 | Interval width |

**Rule (Normative).** No [Provisional] constant is treated as established until its calibration is recorded. An uncalibrated constant is conservative by default (higher review, tighter budgets).

---

## 12.11 Rule index by part

Every rule registered in this specification. Legacy mappings are in Part 1 §1.7.2. Full text is in the part named.

| Domain | Rules | Part |
|---|---|---|
| FND | 001–007 | 5 |
| CON | 001, 002 (5); 003, 004 (2); 005a–e, 006–008 (3); 009 (5) | 2, 3, 5 |
| TYP | 001, 002 | 3 |
| FRM | 001 (5); 002–010 (4–5) | 4, 5 |
| INT | 001 (5); 003–009 (8); 010–012, 020–022, 030, 031, 040, 050, 051 (5); 013 (10) | 5, 8, 10 |
| EVD | 001–003 (5); 004 (3); 005, 006 (5); 007–012 (6) | 3, 5, 6 |
| CAN | 001–004 (3); 010 (5) | 3, 5 |
| IDN | 001–009 | 7 |
| GEN | 001, 002 (3, 9); 003 (3); 004–010 (9) | 3, 9 |
| LRN | 001 (7); 002–008 (9) | 7, 9 |
| KNW | 001, 002 (1, 2); 003 (3); 004, 005 (4); 006 (9); 007–009, 013 (10); 010–012 (5) | 2–5, 9, 10 |
| GOV | 001 (7); 002 (5); 003–006 (6); 007–010 (10) | 5, 6, 7, 10 |
| SEC | 001–010 | 6 |
| ENC | 001–008 | 11 |

Invariants I-01 to I-14 are in Part 2 §2.17. Validation checks VC-S, VC-T, VC-G, VC-V, VC-C are in Part 5 §5.6, VC-I in Part 7 §7.5.1.

---

## 12.12 Closure of the sources' open-question lists

### 12.12.1 F2-A §3.23: twelve open items of the v0.1 grammar

All closed in Part 3 §3.22.

### 12.12.2 F2-A §3.28: ten items "before coding"

| # | Item | Closed in |
|---|---|---|
| 1 | Finalize the semantic type hierarchy | Part 2 §2.2 (fixed kinds), Part 4 §4.7 (classes), §12.12.4 below |
| 2 | Frame inheritance and composition | Part 4 §4.5–§4.6 |
| 3 | Canonicalization algorithms | Part 3 §3.17, Part 11 §11.11 |
| 4 | Concept identity and deduplication procedures | Part 7 |
| 5 | Derivation certificate format | Part 5 §5.8 |
| 6 | Factual assertions versus propositions | Part 2 §2.11, Part 3 §3.5, Part 6 §6.7 |
| 7 | Formal evidence and uncertainty representation | Part 6 §6.4, Part 3 §3.14 |
| 8 | Grammar versioning and compatibility | Part 2 §2.13, Part 11 §11.14 |
| 9 | Domain partitioning and semantic retrieval | Part 10 §10.6–§10.7 |
| 10 | Binary encoding strategy and storage benchmarks | Part 11 |

### 12.12.3 F1-D §2.29: seven unsolved questions

| # | Question | Closed in |
|---|---|---|
| 1 | How exactly should the Semantic Grammar be defined? | Part 3 |
| 2 | What is the minimum number of fundamental semantic types? | §12.12.4 |
| 3 | How should concept identity be established automatically? | Part 7 |
| 4 | How should frames inherit or compose? | Part 4 §4.5–§4.6 |
| 5 | How should inference interact with stored knowledge, without confusing inferred and source-stated? | Part 6 §6.3, Part 10 §10.8, SG-KNW-008/009 |
| 6 | How should the binary encoder work: fixed width, variable length, or dictionaries? | Part 11 §11.4–§11.6 |
| 7 | How will generalization quality be measured? | Part 9 §9.9, §9.17 |

### 12.12.5 F3-B §7.36: six engineering decisions

| Decision | Closed in |
|---|---|
| Which local AI models | §12.5; Part 8 §8.11.6 |
| Which Python libraries | §12.1 |
| How modules communicate | Part 10 §10.3 |
| How the database is organized | Part 11 §11.3 |
| How to benchmark | §12.6 |
| What the first implementation supports | §12.4 |

### 12.12.6 Other open items

| Item | Closed in |
|---|---|
| F1-C §17: typed graph, recursive expression language, frame-based structure, or hybrid | Part 10 §10.15.3 (hybrid) |
| F2-B §4.28: five possible relations between "equivalent" structures | Part 7 §7.16 |
| F1-B §15: three machine-readable specifications (type system, frame library, derivation protocol) | Parts 2–3, 4, 5 |
| F3-A: "We will return to that question" (when a template saves space) | Part 11 §11.13.1 |
| F1-A §3.16: compare implementations A, B, C | §12.6.6 |

### 12.12.4 The minimum number of semantic kinds (Enhancement E-111)

F1-D §2.29 asked whether some proposed types can be derived from others. The review of the 15 kinds of Part 2 §2.2:

| Kind | Derivable from others? | Decision |
|---|---|---|
| ENTITY, EVENT, STATE, ROLE, RELATION, FRAME, CONSTRAINT, TIME, FUNCTION, EXPRESSION | No (each has a different formation or validation behavior) | Keep |
| PROCESS | Could be treated as an aggregate of events, since the grammar's COMPOSE builds it | Keep: it has no inherent endpoint, so aspect and entailment rules differ (Part 4 §4.4) |
| PROPOSITION | Derivable from SIT via HOLDS | Keep as a sort (Part 3 §3.3.1): negation, modality, and attitudes need a truth-evaluable argument |
| PROPERTY, VALUE, QUANTITY | PROPERTY and VALUE could be unified with QUANTITY by adding dimension | Keep separate: the validator separates "value used where a property is expected" (VC-T08) and unit checks (VC-T03) |

Rule of evaluation, from Part 3 §3.20: a minimum is not the goal. "The smallest practical grammar that can accurately express the meanings our system needs" is, judged by storage, validation, and processing cost under correctness and expressiveness constraints. The review is repeated on the benchmark results: if two kinds are never distinguished by any check, they are candidates for merging through a MAJOR grammar version.

---

## 12.13 Traceability matrix: every source section to its implementation

The matrix is in the order of the sources. A source section may be implemented in several places and the principal ones are shown. A "P-nn" refers to the principle table in Part 1 §1.5.

### F1-A: "Discovering Meaning" (§3.1–3.18)

| Source | Implemented in |
|---|---|
| §3.1 Redefining the project | Part 1 §1.3, §1.6; Part 8 §8.1 |
| §3.2 What it means to understand a sentence | Part 8 §8.1.2, §8.3 |
| §3.3 AMR | Part 8 §8.4.3 |
| §3.4 Multiple word meanings | Part 2 §2.10; Part 7 §7.4.3; Part 8 §8.5 |
| §3.5 Context and frames | Part 4; Part 8 §8.6 |
| §3.6 Frames and instances; unknown preserved; assertion | Part 2 §2.5–§2.6, §2.11; Part 3 §3.13 |
| §3.7 Python capabilities; ambiguity | Part 8 §8.3, §8.9; Part 5 §5.10 |
| §3.8 Local AI contribution | Part 5 §5.9; Part 8 §8.11 |
| §3.9 Hybrid semantic compiler | Part 8 §8.1 |
| §3.10 Bootstrap problem | Part 8 §8.13 |
| §3.11 Not asking AI repeatedly | Part 8 §8.12 |
| §3.12 What could be learned | Part 9 §9.1; Part 7 §7.9 |
| §3.13 Complete walkthrough | Part 2 §2.16; Part 8 §8.15.1 |
| §3.14 Two databases | Part 2 §2.1 |
| §3.15 Semantic compression warning | Part 1 §1.3; Part 11 §11.1, §11.15 |
| §3.16 First prototype | Part 8 §8.16; §12.6 |
| §3.17 Self-extending grammar | Part 9 §9.7.4, §9.10 |
| §3.18 Roadmap, conclusion | §12.8; Part 1 §1.5 (P-01, P-03) |

### F1-B: "Rule-Governed Semantic AI" (§1–15)

| Source | Implemented in |
|---|---|
| §1 Strict AI rules, three operations | Part 5 §5.1, §5.9 |
| §2 Semantic Rulebook (SG-001…007) | Part 5 §5.3–§5.4; Part 1 §1.7.2 |
| §3 Rule-governed construction, certificate | Part 5 §5.7–§5.8 |
| §4 Five validation levels | Part 5 §5.6 |
| §5 Existing technology (SHACL, OWL, Pydantic) | Part 5 §5.6; Part 11 §11.18; §12.1 |
| §6 Larger AI as reviewer, review queue | Part 6 §6.9–§6.11 |
| §7 Verify rules, not explanations | Part 5 §5.8.4 |
| §8.1 Roles & Fit | Part 4 §4.8 |
| §8.2 Borrowed Pattern | Part 4 §4.10; Part 9 §9.12 |
| §8.3 Zoom | Part 4 §4.5.3, §4.11 |
| §8.4 Known-Shape, Missing Piece | Part 2 §2.6; Part 9 §9.19.5 |
| §8.5 Evidence Ladder | Part 6 §6.4–§6.5 |
| §8.6 Pattern Tracking | Part 9 §9.13; Part 6 §6.12 |
| §9 Other ideas | Part 9 §9.19 |
| §10 Pattern Discovery Engine | Part 9 §9.8 |
| §11 Modules | Part 10 §10.9 |
| §12 Two rule types; meaning vs truth | Part 5 §5.2; Part 6 §6.7 |
| §13 Revised validation workflow | Part 6 §6.14 |
| §14 Assessment of the document | Part 1 §1.2; Part 9 §9.19 |
| §15 Next technical step (three specs) | Parts 2–5 |

### F1-C: "Brain-Inspired Part 1" (§1–20)

| Source | Implemented in |
|---|---|
| §1 What to carry forward | Part 10 §10.1 |
| §2 Grammar as internal language | P-01; Part 10 §10.2 |
| §3 Hierarchical controllers | Part 10 §10.2, §10.3.4 |
| §4 Cognitive workspace | Part 10 §10.4 |
| §5 SemanticHub, ContextIntegrator | Part 7 §7.4.3; Part 10 §10.9 |
| §6 Analogy and metaphor engine | Part 9 §9.12 |
| §7 Memory architecture | Part 10 §10.5 |
| §8 Enormous dictionary; identity vs storage | Part 10 §10.6 |
| §9 Active and inactive connections | Part 10 §10.7.1, §10.7.4 |
| §10 Sparse semantic activation | Part 10 §10.7.2–§10.7.3 |
| §11 Prediction and error correction | Part 10 §10.11; Part 5 §5.11 |
| §12 Metacognition | Part 10 §10.10; Part 6 §6.9 |
| §13 Learning without uncontrolled growth | Part 9 §9.1–§9.3 |
| §14 Separate interpretation, knowledge, reasoning | Part 10 §10.8 |
| §15 Unified architecture | Part 1 §1.6; Part 10 |
| §16 What not to carry forward | Part 10 §10.15.1 |
| §17 Critical decisions | Part 10 §10.15.3 |
| §18 Development strategy | Part 10 §10.15.2; §12.8 |
| §19 Self-representation of operations | Part 10 §10.12 |
| §20 Final assessment and risks | Part 10 §10.15.4; §12.9 |

### F1-D: "Brain-Inspired Part 2" (§2.1–2.29)

| Source | Implemented in |
|---|---|
| §2.1 Smallest unit of meaning | Part 2 §2.1–§2.2 |
| §2.2 Nodes vs structures | Part 2 §2.3 |
| §2.3 Typed semantic graph | Part 2 §2.2, §2.7–§2.8 |
| §2.4 Python objects vs storage | Part 2 §2.15 |
| §2.5 Four data structures compared | Part 2 §2.15; Part 11 §11.3.1 |
| §2.6 Universal semantic record, stable IDs | Part 2 §2.3–§2.4 |
| §2.7 Frames for events | Part 2 §2.11; Part 4 |
| §2.8 Recursive structures | Part 3 §3.2, §3.5 |
| §2.9 Cycles and relation properties | Part 2 §2.8 |
| §2.10 Memory and workspace | Part 10 §10.4 |
| §2.11 Asynchronous sharing | Part 10 §10.3 |
| §2.12 Shared memory ≠ shared mutable objects | Part 10 §10.3.1 |
| §2.13 Domain-partitioned memory | Part 2 §2.13; Part 10 §10.6 |
| §2.14 Sparse graph storage | Part 11 §11.3.5 |
| §2.15 Weights | Part 2 §2.8 |
| §2.16 Attention and activation | Part 10 §10.7.2 |
| §2.17 Frames and functional ontology | Part 4 §4.8 |
| §2.18 Generalization at data-structure level | Part 9 §9.9 |
| §2.19 Excessive generalization | Part 9 §9.9.4–§9.9.5; Part 11 §11.13.1 |
| §2.20 Unified data model | Part 2 §2.3 |
| §2.21 Existing standards (RDF) | Part 11 §11.18 |
| §2.22 Module walkthrough | Part 8 §8.15; Part 10 §10.4.7 |
| §2.23 Module disagreement | Part 3 §3.14; Part 10 §10.3.3 |
| §2.24 Physical storage | Part 11 §11.2–§11.3 |
| §2.25 Language independence | Part 8 §8.14 |
| §2.26 Source assertions vs universal knowledge | Part 6 §6.3.3, §6.7 |
| §2.27 Summary of four systems | Part 1 §1.6 |
| §2.28 Most important decision | Part 10 §10.15.3 |
| §2.29 What is not solved | §12.12.3 |

### F2-A: "Formal Recursive Grammar" (§3.1–3.28)

| Source | Implemented in |
|---|---|
| §3.1 Redefining grammar | Part 3 §3.1 |
| §3.2–3.3 Fundamental element, minimal recursive grammar | Part 3 §3.2 |
| §3.4 Frames over triples | Part 3 §3.1, §3.4 |
| §3.5 Type compatibility | Part 3 §3.3 |
| §3.6 Coercion and figurative language | Part 3 §3.15 |
| §3.7 Frames more than role lists | Part 4 §4.4 |
| §3.8 Preconditions and effects | Part 4 §4.4.2; Part 3 §3.10 |
| §3.9 States and transitions | Part 3 §3.10 |
| §3.10 Negation | Part 3 §3.7 |
| §3.11 Modality | Part 3 §3.8 |
| §3.12 Time | Part 3 §3.9 |
| §3.13 Causation | Part 3 §3.11 |
| §3.14 No unsupported expansion | Part 5 §5.6 (SG-EVD-001, 006) |
| §3.15 Derivation certificate | Part 5 §5.8 |
| §3.16–3.17 Canonicalization | Part 3 §3.17 |
| §3.18 Stable identity | Part 7 |
| §3.19 Generalization rule | Part 9 §9.9.4 |
| §3.20 Modules and grammar | Part 10 §10.9 |
| §3.21 Three rule kinds | Part 5 §5.2 |
| §3.22 Reducing the grammar | Part 3 §3.20 |
| §3.23 Grammar v0.1 | Part 3 §3.2, §3.22 |
| §3.24 Worked example | Part 3 §3.21.1 |
| §3.25 AI permissions | Part 5 §5.9 |
| §3.26 Larger AI reviewer | Part 6 §6.11 |
| §3.27 Achievements | Part 1 |
| §3.28 Remaining | §12.12.2 |

### F2-B: "Inheritance, Composition, Generalization" (§4.1–4.28)

| Source | Implemented in |
|---|---|
| §4.1 Four types | Part 4 §4.1; Part 9 §9.9.1 |
| §4.2 Taxonomic | Part 4 §4.7 |
| §4.3 Multiple inheritance | Part 4 §4.5.2, §4.7 |
| §4.4 Composition vs inheritance | Part 4 §4.6–§4.7 |
| §4.5 Functional generalization | Part 4 §4.8 |
| §4.6 Input–Transformation–Output | Part 4 §4.8.5 |
| §4.7 Universal operations | Part 4 §4.9 |
| §4.8 Semantic algebra | Part 3 §3.18.3 |
| §4.9 Frame inheritance | Part 4 §4.5 |
| §4.10 Frame composition | Part 4 §4.6 |
| §4.11 Composition operators | Part 3 §3.18 |
| §4.12 Structural generalization | Part 4 §4.10; Part 9 §9.8.4 |
| §4.13 Attention for pattern discovery | Part 9 §9.8 |
| §4.14 Universal structural signature | Part 4 §4.10.3 |
| §4.15 Counterexamples | Part 9 §9.9.2–§9.9.3 |
| §4.16 Inversion | Part 9 §9.9.3 |
| §4.17 Generalization as search | Part 9 §9.9.6 |
| §4.18 Generalization vs compression | Part 9 §9.10 |
| §4.19 Shared components | Part 4 §4.7 |
| §4.20 Automatic discovery, discriminative value | Part 9 §9.9.5 |
| §4.21 Pipeline | Part 9 §9.8.2 |
| §4.22 Cognitive workspace | Part 9 §9.8.5 |
| §4.23 Generalization budget | Part 9 §9.11 |
| §4.24 Abstraction layers | Part 4 §4.11 |
| §4.25 Versioned generalization | Part 2 §2.13; Part 9 §9.15 |
| §4.26 Most important rule | P-14 |
| §4.27 Achievements | Part 1 |
| §4.28 Remaining problem | Part 7 §7.16 |

### F2-C: "Identity and Concept Resolution" (§5.1–5.31)

| Source | Implemented in |
|---|---|
| §5.1–5.2 Identity kinds | Part 2 §2.4.2; Part 7 §7.1 |
| §5.3 SemanticHub and ContextIntegrator | Part 7 §7.4.3 |
| §5.4 Definitions alone | Part 7 §7.3.1 |
| §5.5 Formal concept definition | Part 2 §2.9 |
| §5.6 Identity through constraints | Part 7 §7.3.3 |
| §5.7 Open-world reasoning | Part 7 §7.3.3; Part 3 §3.13 |
| §5.8 Outcomes of comparison | Part 7 §7.2 |
| §5.9 Embeddings | Part 7 §7.4.2 |
| §5.10 Resolution pipeline | Part 7 §7.4.1 |
| §5.11 Identity certificate | Part 7 §7.5 |
| §5.12 Reversible mapping | Part 7 §7.8 |
| §5.13 Context-dependent identity | Part 7 §7.7.1 |
| §5.14 Cross-domain identity | Part 7 §7.7.2 |
| §5.15–5.16 ID strategies, IDs without meaning | Part 2 §2.4.1 |
| §5.17 Local dictionaries | Part 11 §11.5 |
| §5.18 Duplicate prevention under concurrency | Part 7 §7.10.2 |
| §5.19 Provisional concepts | Part 7 §7.9.2 |
| §5.20 Semantic drift | Part 7 §7.11 |
| §5.21 Registry as memory index | Part 2 §2.13; Part 7 §7.10 |
| §5.22 Worked example | Part 7 §7.15.2 |
| §5.23 Multiple definitions | Part 7 §7.7.3 |
| §5.24 Ontology versions | Part 7 §7.11.4 |
| §5.25 Python vs AI | Part 7 §7.13 |
| §5.26 Resolution protocol | Part 7 §7.2.3, §7.4.1 |
| §5.27 Metacognition | Part 7 §7.12; Part 6 §6.9 |
| §5.28–5.29 Compression, independence | Part 7 §7.17; Part 11 |
| §5.30 Updated architecture | Part 1 §1.6; Part 10 |
| §5.31 Decisions | Part 7 §7.16 |
| (truncated closing principle) | Part 7 intro |

### F3-A: "Binary Encoding and Compression" (§6.1–6.33)

| Source | Implemented in |
|---|---|
| §6.1 What is being compressed | Part 11 §11.1 |
| §6.2 Binary IDs alone | Part 11 §11.8.3, §11.17.3 |
| §6.3 Three levels | Part 11 §11.5, §11.6, §11.13.1 |
| §6.4 Fixed vs variable-length | Part 11 §11.4 |
| §6.5 Global and local IDs | Part 11 §11.5 |
| §6.6–6.7 Frame-specific encoding, presence bitmaps | Part 11 §11.6 |
| §6.8–6.9 Recursive and graph encoding | Part 11 §11.7 |
| §6.10–6.11 Structural hashing, content addressing | Part 11 §11.10 |
| §6.12–6.13 Pattern compression, template inequality | Part 11 §11.13.1 |
| §6.14 Generalization vs compression | Part 11 §11.16.3; Part 9 §9.10 |
| §6.15–6.16 Frequency and conditional coding | Part 11 §11.13.2–§11.13.3 |
| §6.17 AI predictor | Part 11 §11.13.5 |
| §6.18 USBF | Part 11 §11.7.5, §11.12 |
| §6.19 Versioning | Part 11 §11.14 |
| §6.20 Random access | Part 11 §11.12.2 |
| §6.21 Domain partitioning | Part 11 §11.5.4, §11.12.3 |
| §6.22 Numerical comparison | Part 11 §11.17.3 |
| §6.23 Correct metric | Part 11 §11.17.1 |
| §6.24 MDL | Part 11 §11.16.4 |
| §6.25 Optimizer | Part 11 §11.16.2 |
| §6.26 Memory types | Part 11 §11.2.2; Part 10 §10.5 |
| §6.27 Compression through inference | Part 11 §11.9 |
| §6.28 Refined objective | Part 1 §1.3; Part 11 §11.1.3 |
| §6.29 Benchmarking strategy | Part 11 §11.17.2 |
| §6.30 Encoding pipeline | Part 11 §11.16.1 |
| §6.31 Round trips | Part 11 §11.11 |
| §6.32 Final storage architecture | Part 11 §11.2; Part 10 §10.5.3 |
| §6.33 Decisions | Part 11 §11.20 |

### F3-B: "Learning and Knowledge Acquisition" (§7.1–7.36)

| Source | Implemented in |
|---|---|
| §7.1–7.2 Four learning kinds and engines | Part 9 §9.1–§9.2 |
| §7.3 Foundation Package | Part 4 §4.12 |
| §7.4 Candidate vs canonical | Part 5; Part 8 §8.11.4 |
| §7.5 Semantic Derivation Protocol | Part 5 §5.8 |
| §7.6 Citation vs proof | Part 5 §5.1, §5.8.4 |
| §7.7 Three rule classes | Part 5 §5.2 |
| §7.8 Learning pipeline | Part 9 §9.2.3 |
| §7.9 Workspace during learning | Part 10 §10.4 |
| §7.10 Existing resources | Part 8 §8.13.4 |
| §7.11 Unknown words | Part 7 §7.9.1 |
| §7.12 Learning relationships | Part 9 §9.6 |
| §7.13 Learning frames (LEASE) | Part 9 §9.7.3 |
| §7.14 Grammar learning engine | Part 9 §9.7.1 |
| §7.15 Unlimited growth | Part 9 §9.7.2, §9.11 |
| §7.16 Grammar generalization example | Part 9 §9.20 |
| §7.17 Larger AI reviewer | Part 6 §6.11 |
| §7.18 Risk-based review | Part 6 §6.10 |
| §7.19 Learning from errors | Part 9 §9.14 |
| §7.20 Procedural memory | Part 9 §9.14.1; Part 10 §10.5 |
| §7.21 Rule hierarchy | Part 5 §5.2 |
| §7.22 Paraphrase testing | Part 5 §5.11 |
| §7.23 Counterexample-driven learning | Part 9 §9.9.3 |
| §7.24 Controlled revision | Part 9 §9.15.1 |
| §7.25 Learning vs promotion | Part 9 §9.3 |
| §7.26 Contradictory sources | Part 6 §6.8 |
| §7.27 Source reliability | Part 6 §6.5.2 |
| §7.28 Measuring quality | Part 9 §9.17; §12.6 |
| §7.29 Feedback loop | Part 9 §9.14.3 |
| §7.30 Central controller | Part 10 §10.2.1; Part 9 §9.2.2 |
| §7.31 Personal computer | Part 9 §9.18; Part 10 §10.13 |
| §7.32 Learning from corrections | Part 9 §9.14.4; Part 5 §5.12 |
| §7.33 Limits of strict rules | Part 5 §5.10 |
| §7.34 Architecture | Part 1 §1.6; Part 9 §9.2 |
| §7.35 Design decision | P-03, P-13 |
| §7.36 What remains | §12.12.5 |

### F3-C: "Technology and Infrastructure" (§8.1–8.32)

| Source | Implemented in |
|---|---|
| §8.1 AI-centered vs grammar-centered | P-01; Part 1 §1.3; §12.1 |
| §8.2 Runtime (Ollama, llama.cpp) | Part 8 §8.11; §12.1 |
| §8.3–8.4 Models and sizes | Part 8 §8.11.6; §12.5 |
| §8.5 Not depending on the model alone | Part 8 §8.3 |
| §8.6 spaCy vs Stanza | Part 8 §8.3.2; §12.1 |
| §8.7 Existing resources | Part 8 §8.13.4 |
| §8.8 Alignment engine | Part 8 §8.13.5 |
| §8.9 Validation technology | Part 5 §5.6; Part 11 §11.18; §12.1 |
| §8.10 Persistent database | Part 11 §11.3 |
| §8.11 Full-text search | Part 7 §7.4; Part 11 §11.3 |
| §8.12 Embeddings | Part 7 §7.4.2 |
| §8.13 FAISS | §12.1; Part 7 §7.4.2 |
| §8.14 Graph matching | Part 9 §9.8.4 |
| §8.15 Frequent pattern discovery | Part 9 §9.8.2 |
| §8.16 asyncio | Part 10 §10.3.6 |
| §8.17 Shared model | Part 10 §10.3.4 |
| §8.18 Machine-readable Rulebook | Part 5 §5.3 |
| §8.19 Testing the Rulebook | Part 5 §5.11; §12.7 |
| §8.20 Testing framework | §12.7 |
| §8.21 Benchmark | §12.6; Part 8 §8.16 |
| §8.22 Metrics | §12.6.4–§12.6.5 |
| §8.23 Technology stack | §12.1 |
| §8.24 Package architecture | §12.3 |
| §8.25 Resource management | Part 10 §10.13 |
| §8.26–8.27 Capability-based selection, deterministic controller | Part 10 §10.2.1, §10.2.5 |
| §8.28 Avoid multi-agent frameworks | Part 10 §10.3.6 |
| §8.29 First implementation | §12.4 |
| §8.30 Architecture after technology | Part 1 §1.6; §12.1 |
| §8.31 Final recommendation | §12.1 |
| §8.32 Achievements | Part 1 |

### REF: `problem-solving-coach.md` (reference only)

Not merged into USG as a coaching function (F1-B §14). Computational mechanisms adopted:

| REF idea | Adopted as | Where |
|---|---|---|
| Functional roles (notice, decide, act, hold, move, transform) | FN primitives | Part 4 §4.8 |
| Borrowed Pattern: relation-for-relation matching | Analogy engine | Part 9 §9.12 |
| Zoom | GENERALIZE/SPECIALIZE, layers | Part 4 §4.5.3, §4.11 |
| Known-Shape and Missing Piece | Template recognition, required vs unspecified roles, ExpectedButUnstated | Part 2 §2.6; Part 9 §9.19.5 |
| Evidence ladder | Evidence vector with derived labels | Part 6 §6.4 |
| Observation, interpretation, pattern, identity claim | Four classes of derived statement | Part 6 §6.12.1 |
| Patterns only after ≥3 occurrences, user may say "not me" | SG-GEN-009, REJECTED_PATTERN veto | Part 6 §6.12; Part 9 §9.8.3 |
| Novelty protection | Result cache, duplicate and covered-case skip | Part 6 §6.12.4; Part 8 §8.11.5 |
| Inversion | Counterexample engine | Part 9 §9.9.3 |
| Second-Order Check | Consequence-chain test | Part 9 §9.19.1 |
| Assumed vs. Real Constraint | Constraint provenance classes | Part 9 §9.6.4 |
| Thinking-Pattern Check | Universal-claim lint | Part 9 §9.19.2 |
| Bottleneck and Signal | Highest-impact uncertainty ordering | Part 9 §9.19.3 |
| Loop and Timing | Feedback-loop detection | Part 9 §9.19.4 |
| Relevance ranking, adaptive depth, lazy loading | Capability plans, priorities, grammar views, partitions | Part 8 §8.18; Part 10 |
| Scaffolding fades as the user improves | Pattern graduation, with automatic return to the model path | Part 8 §8.12 |
| Log the thinking, not the story | Process history without source content | Part 6 §6.12.5 |
| "Enough" detector | Budgets, stop conditions | Part 9 §9.15.2 |
| Separate analysis skill keeps the coach light | Background learning outside the interactive path | Part 9 §9.18 |

**Not adopted** (specific to coaching a person): the conversation modes, state-awareness, personal profiling, the one-time disclosure, the stretch directions, and the user-facing question craft.

---

## 12.14 Enhancement register: complete index

The register runs E-01 to E-116. **E-44, E-46, and E-89 were never assigned.** E-101, E-102, E-103, and E-107 are aliases of E-10, E-09, E-22, and E-24 (kept so each part's own table reads completely), so there are **109 distinct enhancements.** (Part 9 §9.19 also cites E-86 as a pointer to its completion of E-17.)

| Theme | IDs | Substance |
|---|---|---|
| Naming, statuses, structure | E-01, E-02, E-04, E-05, E-06, E-07, E-18, E-26–E-32, E-41–E-43, E-45, E-47 | One rule namespace. Five status axes. Two-tier roles. Referents vs concepts. TRANSFER family. FN namespace. Versioning. Span units. Fixed kinds vs classes. Frame instance as description. Hole states and basis. Link kinds, parameters, perspectives, closed role lists, aspect-gated entailments. |
| Grammar | E-08, E-19, E-33–E-40 | Twelve gaps closed. Equality. Modal force × flavor. Three-valued types. Quantifiers. Forbidden simplifications. Annotation channel. Opaque contexts. Packed ambiguity. Presupposition. |
| Rules and validation | E-48–E-55 | Rules vs checks and error codes. Kind × authority. Replay verification. Closed-set selection. Protected validator and rulebook. Form vs meaning. Certificate retention. Valence-pattern mapping. |
| Evidence, review, security | E-03, E-13, E-15, E-56–E-60 | Evidence vector. Source text as data. Calibrated review. Commitment holder and context. Blind-first review. Egress control. Independence counting. Text normalization. |
| Identity | E-20, E-61–E-68 | Single-writer registry. Generalization action. Read-time equivalence. Concurrency layers. Equivalence grades. Scoped resolution. Provisional limits. Embedding versions. Identity rules. |
| Interpretation | E-14, E-21, E-69–E-76 | Time anchor. Language annotation. Parser as evidence. Narrow tasks. Referent context. Guarded patterns. FRAME_GAP. Label maps. Arabic risks. Deterministic caching. |
| Learning and generalization | E-12, E-17, E-77–E-86 | Gates before scores. Coaching mechanisms. Counterexample states and distinction mining. Discriminative bounds. Independent counts. Bounded typed matching. Promotion bundles. Cycle gates. Reprocessing. Demand-driven grammar. Relation conservatism. Constraint provenance. |
| Cognitive architecture and resources | E-11, E-87, E-88, E-90–E-99 | Bounded activation. Episodic partitions. Frame views. Two activations. Cooperative preemption. Competing candidates. Cross-domain placement. Memory worksheet. Durability. Kernel reasoner. Process history store. Process layout. Module contract. |
| Storage and encoding | E-09, E-10, E-22, E-24, E-100–E-110 | Role-state encoding. Template inequality. Canonical form. RDF mapping. Complete-record sizing. Two-tier dictionary. Strong baselines. Decoder hardening. Pinned role schema. Reversible-mode bound. Backward references. |
| Technology and delivery | E-16, E-23, E-25, E-111–E-116 | Metric definitions and abstention scoring. Cost calibration. Verification gate. Kind minimality. Constants register. Technology manifest. Invariants vs calibrated targets. Annotation protocol. CI gates. |

Each enhancement's problem statement, source, and resolution are in the "Enhancements introduced" table at the end of the part that resolves it.

---

## 12.15 Limits of this specification and decisions that are yours

### 12.15.1 What this specification is not

- **Nothing has been executed.** There is no code, no measurement, and no benchmark result. Every number is a design estimate or a [Provisional] constant. The specification says in many places how each will be measured.
- **The technology gate has not been run** (§12.2). The sources' claims about spaCy, Ollama, llama.cpp, SHACL, RDF 1.2, FAISS, and the resources were taken as stated. They need checking against current versions and licences.
- **Two source gaps remain.** The earlier "Brain-Inspired AI Modeling" conversation was not provided, so SemanticHub, ContextIntegrator, the analogy engine, and metacognition are specified from the summaries in F1-C only. File 2's last sentence is cut off, so its closing principle was reconstructed (Part 7 intro).
- **Semantic correctness is not guaranteed.** The system guarantees the engineering properties of Part 5 §5.10, not that every sentence is understood correctly. It is designed to refuse to guess.
- **USBF may not be worth building.** The format is a candidate to be benchmarked, and the benchmark may say to keep the relational store and a general codec (§12.8.2).

### 12.15.2 Decisions only you can make

| Decision | Why it matters | Needed by |
|---|---|---|
| Your hardware (RAM, CPU, GPU and VRAM, free disk) | Sets the model size, concurrency, and whether a reviewer model can run locally | M0 |
| Whether remote reviewer models are allowed, and for which sources | SEC-008 egress policy and licences | M4 |
| First domain(s) and source types | Chooses the kernel corpus, seed classes, and the first gold set | M2 |
| Cost of a wrong committed fact versus an abstention | Sets `c_err : c_abs`, risk tolerances, and review load | M5 |
| Who reviews | A human review queue needs people. VERY_HIGH items cannot be automatic. | M7 |
| Whether Arabic is needed early | Moves M11 earlier and needs an Arabic parser, lexicon, and gold set | M3 |
| Sensitivity and retention rules for your sources | Privacy, deletion, and egress | M0 |
| Licence constraints on imported resources | Which resources may be imported and redistributed | M0 |

---

## 12.16 Closing

The specification you asked for now exists as twelve parts:

| Part | Subject |
|---|---|
| 1 | Foundations, principles, enhancement register, conventions |
| 2 | Type system and data model |
| 3 | Formal grammar v1.0 |
| 4 | Frames, functional ontology, Foundation Package |
| 5 | Rulebook, derivation protocol, validation |
| 6 | Evidence, truth status, review, security |
| 7 | Concept identity and resolution |
| 8 | Interpretation pipeline |
| 9 | Learning, generalization, grammar evolution |
| 10 | Cognitive architecture, memory, resources |
| 11 | Storage and binary encoding |
| 12 | Technology, testing, kernel, traceability, closure |







