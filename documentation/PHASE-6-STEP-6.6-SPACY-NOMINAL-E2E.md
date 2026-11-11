# Phase 6 Step 6.6 — spaCy-to-USG Nominal End-to-End Evaluation v0.1

**Status:** candidate-only end-to-end structural evaluation; not semantic acceptance.

## Purpose

The UD nominal adapter works when supplied with gold dependency trees. This
experiment measures the errors introduced when the graph comes from a
pretrained English parser instead.

## Pipeline

1. Run en_core_web_sm 3.8.0 on PUD's gold pre-tokenized word sequence.
2. Normalize common spaCy/ClearNLP head conventions for prepositions and
   coordination into UD-style head arcs.
3. Map selected relation labels (including prep/pobj, poss, dobj, passive
   subject/auxiliary, and temporal npadvmod) into the UD labels consumed by
   the nominal adapter.
4. Run the same dependency-driven USG candidate adapter on predicted and gold
   graphs.
5. Compare construction, head/dependent token IDs, role spans, and marker
   spans; report structural precision/recall/F1 and exact-span agreement.

## Interpretation limits

The reference is the gold UD graph projected through the same adapter. This
measures parser-plus-adapter structural extraction, not semantic truth.
The spaCy-to-UD mapping is partial; no dependency LAS or semantic-role F1 is
claimed. PUD is a news/wiki evaluation set, and training-data overlap cannot
be ruled out. All outputs remain candidate-only.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_spacy_nominal_e2e.py' -v
python -m tools.phase6_spacy_nominal_e2e_v0_1.evaluation
```

## Observed English PUD results (2026-11-11)

The end-to-end run evaluated all 1,000 English PUD sentences using the
pretrained spaCy parser and the dependency-driven nominal adapter. Candidate
counts below include alternatives emitted for ambiguous constructions.

| Measure | Result |
|---|---:|
| Predicted candidate hypotheses | 3,583 |
| Gold-UD candidate hypotheses | 3,303 |
| Structural edge precision | 77.81% |
| Structural edge recall | 84.41% |
| Structural edge F1 | 80.98% |
| Exact candidate + source-span precision | 77.42% |
| Exact candidate + source-span recall | 83.98% |
| Exact candidate + source-span F1 | 80.57% |
| Exact span agreement given a structural match | 99.50% |

Per-construction exact candidate F1:

| Construction | F1 |
|---|---:|
| Attribute modifier | 88.53% |
| Compound modifier | 69.37% |
| Genitive relation | 87.97% |
| Possession | 95.10% |
| Prepositional nominal modifier | 67.02% |
| Temporal adverbial | 69.23% |

This is a useful end-to-end result: the parser-plus-adapter can recover many
gold-UD-derived nominal structures, and when the structural edge is correct,
the original source spans are almost always exact. Compound and prepositional
modifiers remain the weakest families and need better relation conversion
before any runtime use.

**Decision:** retain the pipeline as a candidate-only English prototype.
Do not promote constructions or integrate it into the USG runtime yet. The
gold reference is a syntactic UD projection through the same adapter, not
independent semantic-role adjudication. Step 6.6 remains unaccepted.

Report artifact:
[workflow run 42995500663](https://github.com/wizekin/USG-Workbench/actions/runs/42995500663).

## Observed English PUD results (2026-11-11)

The end-to-end run evaluated all 1,000 English PUD sentences with the
pretrained spaCy parser. Candidate counts include alternatives for ambiguous
constructions.

| Measure | Result |
|---|---:|
| Predicted candidate hypotheses | 3,583 |
| Gold-UD candidate hypotheses | 3,303 |
| Structural edge precision | 77.81% |
| Structural edge recall | 84.41% |
| Structural edge F1 | 80.98% |
| Exact candidate + source-span precision | 77.42% |
| Exact candidate + source-span recall | 83.98% |
| Exact candidate + source-span F1 | 80.57% |
| Exact span agreement given a structural match | 99.50% |

Per-construction exact candidate F1:

| Construction | F1 |
|---|---:|
| Attribute modifier | 88.53% |
| Compound modifier | 69.37% |
| Genitive relation | 87.97% |
| Possession | 95.10% |
| Prepositional nominal modifier | 67.02% |
| Temporal adverbial | 69.23% |

The parser-plus-adapter recovers many UD-derived nominal structures, and
source spans are highly reliable when the structural edge is correct.
Compound and prepositional modifiers remain the weakest families and need
better relation conversion before runtime consideration.

**Decision:** retain this as a candidate-only English prototype. The gold
reference is a syntactic UD projection through the same adapter, not
independent semantic-role adjudication. Do not promote constructions or
integrate this pipeline into the USG runtime. Step 6.6 remains unaccepted.

Report artifact:
[workflow run 42995500663](https://github.com/wizekin/USG-Workbench/actions/runs/42995500663).
