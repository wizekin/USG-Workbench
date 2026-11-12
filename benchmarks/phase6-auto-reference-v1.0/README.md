# Phase 6 automatic synthetic reference benchmark v1.0.0

The deterministic generator in `tools/phase6_auto_reference_v1_0/` creates the benchmark from a meaning graph and original project lexical seeds, then independently realizes the source text in English or Modern Standard Arabic.

- 500 cases in total.
- Ten language/construction profiles.
- Per profile: 20 positive, 20 negative, and 10 ambiguous/boundary cases.
- Reference labels and source spans are derived from the generated semantic graph and realization record.
- No human annotations, LLM labels, development fixtures, candidate lexicon, or external corpora are used.
- Corpus and generated reference lexicon are released under CC0-1.0; see `LICENSE.txt`.

This is a controlled synthetic benchmark. It does not establish naturalistic language accuracy or unrestricted English/MSA coverage. The candidate recognizer remains candidate-only; this benchmark alone does not promote runtime constructions.
