# Phase 4 — Step 4.13: Integrated Exit Acceptance

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Accepted profile:** `USG-INTERPRET/0.1.0`  
**Release scope:** bounded offline demonstrator

## Exit gate

The integrated workflow:

1. Compiles all versioned Phase 4 packages.
2. Runs every `test_phase4_*.py` automated test.
3. Runs the frozen six-case v0.1.0 interpretation benchmark.
4. Runs a machine-readable Phase 4 exit evaluator.
5. Confirms the normative `USG-SEM/1.0` schema and archived/historical Python kernel implementations are unchanged.
6. Runs alongside the repository's Phase 1–3 integrated regression, packaging, local API, and Kernel Lab workflows triggered by the same pull request.
7. Publishes benchmark and exit-acceptance JSON artifacts.

## Acceptance boundary

The release is accepted only as a **bounded demonstrator**. The included lexicon is intentionally tiny. The enabled grammar covers explicit three-word English SVO and Modern Standard Arabic SVO/VSO patterns. Multi-sentence composition, nested syntax, broad lexical/morphological coverage, negation/modality/tense/aspect scope, coordination, general pronoun resolution, and implicit discourse inference remain unsupported.

The system preserves exact source text, reports unknown or unsupported content, persists valid USG-SEM/1.0 documents in the existing SQLite store, and keeps assertion/evidence statuses conservative. Repeated names are not identity proof; exact quotation alignment is not semantic support; no truth promotion occurs.

This acceptance does not establish unrestricted language understanding, general reasoning, AGI, objective truth determination, broad multilingual coverage, or production/security certification. Expanding coverage requires new versioned resources, construction-specific gold/partial fixtures, and a later benchmark/profile acceptance.
