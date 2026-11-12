# Phase 6 Integrated Interpreter and Bridge Validation

## Purpose

This guide describes the shared bilingual Phase 6 candidate interpretation operation introduced for Steps 6.7–6.14. It replaces a workflow that required manually supplying a candidate graph for composition or relying solely on a closed-template extractor.

## Run it

API request:

\`\`\`json
{
  "source": "Ada writes code and Ben reads reports.",
  "language": "en",
  "persist": false
}
\`\`\`

Send to \`POST /v3/phase6/interpret\`.

CLI:

\`\`\`bash
usg-workbench phase6-interpret source.txt --language en --no-persist
\`\`\`

Kernel Lab exposes the same operation as **Run integrated Phase 6 interpretation** in the Phase 6 panel.

## Pipeline reuse

The integrated interpreter reuses the established \`Phase5InterpretationService\` and its lexical, segmentation, syntax, semantic composition, operator, and discourse artifacts. It does not create another parser or a second resource catalogue. The conversion layer:
- retains predicate candidates and their candidate IDs;
- represents AGENT/ACTION/PATIENT roles with exact source spans;
- carries explicit conjunction and subordination boundaries to typed candidate relations;
- carries operator candidates with their exact marker spans and targets;
- carries mention/antecedent candidates without resolving referent identity;
- uses strict Phase 6 templates only when the Phase 5 stages produced no predicate candidate.

A missing candidate does not cause a guess. Diagnostics explain when a clause boundary has no two predicate candidates, an operator target is missing, or a discourse marker cannot be represented by a registered relation.

## Status and evidence

The integrated result remains \`CANDIDATE_ONLY\`. The new bridge benchmark runs over the frozen 100-case Phase 5 v0.2.1 corpus and verifies that Phase 6 graph conversion preserves already accepted Phase 5 results. It is deliberately named a bridge regression, not a Phase 6 accuracy benchmark. The result includes the exact corpus digest and case-level rows.

Run:

\`\`\`bash
python -m tools.phase6_broader_semantics_v0_1.integrated_benchmark
python -m unittest discover -s tests -p 'test_phase6_integrated_interpreter.py' -v
\`\`\`

## Canonical preservation

The integration offers a preservation-only adapter to \`USG-SEM/1.0\`. It stores the full candidate payload as an \`OPAQUE\` expression and as a namespaced extension, includes exact source evidence, and records an unresolved item. It emits no assertions or referents. The API returns the preview only when the unchanged canonical validator accepts it.

Do not interpret \`LOSSLESS_PRESERVATION_ONLY\` as a claim that the semantic graph has been mapped into canonical semantic assertions. The existing \`project_loss_aware\` semantic guard continues to return \`NOT_PROJECTABLE\` for candidate relations/features that do not have a verified assertion-level mapping.

## Non-goals and limitations

No unrestricted English/Arabic parsing, broad passive/imperative recognition, productive phrase coordination, general argument-gap resolution, unique discourse identity resolution, or naturalistic Phase 6 accuracy claim is established. All additional Phase 6 construction output stays candidate-only pending independent per-language acceptance evidence. No human annotation or runtime review is required.
