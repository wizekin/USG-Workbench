# Phase 5 — Step 5.8: Multi-Sentence Discourse and Reference Candidates

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Analyzer:** `discourse-analysis/0.2.0`  
**Lexical resource:** `usg-en-ar-discourse-lexicon@0.3.0`

## 1. Deliverables

- Source-grounded mention detection for nominal, proper-name, and pronominal tokens.
- Versioned English/MSA Arabic pronoun entries and selected plural nominal forms.
- Backward-only antecedent candidate generation using registered number, gender, and person features.
- Explicit unresolved pronoun records when no antecedent passes the conservative compatibility rules.
- Sentence-initial temporal, causal, consequence, and contrast relation candidates with exact marker spans.
- Immutable source ID/digest and exact token spans on all mention/reference artifacts.

## 2. Reference policy

A reference candidate is not a resolved identity. The analyzer does not merge mentions, infer a person from a name, or select the nearest mention as truth. It rejects known feature mismatches. Gendered pronouns require a compatible registered gender feature; if the lexicon does not provide that evidence, the reference remains unresolved. Number-compatible candidates can remain ambiguous when several prior mentions match.

Only preceding nominal/proper mentions are considered; pronoun chains, cataphora, bridging references, world knowledge, semantic-role salience, and unrestricted coreference are not implemented.

## 3. Discourse relation policy

The initial sentence-initial markers are English then/however/therefore/because and MSA Arabic ثم/لكن/لذلك/لأن. A relation candidate links the preceding sentence's final clause to the marked sentence's first clause. It records textual evidence and sequence position but does not claim full discourse semantics or causal truth.

## 4. Acceptance tests

Tests cover singular/plural compatibility, ambiguous antecedents, gendered-pronoun abstention, Arabic plural/gender matching, sentence-initial relation links, candidate budgets, source identity, and non-merging of mention identities. Phase 4 and Phase 5 Steps 5.2–5.7 regressions must pass.

## 5. Explicit limitations

This is a conservative reference-candidate system, not general coreference resolution. It does not resolve identities, pronoun chains, cataphora, implicit arguments, bridging, discourse deixis, or arbitrary Arabic clitic/pronoun morphology. Unsupported cases remain unresolved.
