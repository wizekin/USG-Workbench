# Phase 6 Step 6.6 — Independent Semantic-Gold Dataset Feasibility Audit

**Date:** 2026-11-11  
**Status:** research completed; independent bilingual semantic-gold gate remains open  
**Decision:** do not treat syntactic treebanks, automatically projected SRL labels, or frame inventories as independent semantic-role gold.

## 1. Question

Can the current Step 6.6 nominal/property/modifier interpreter be accepted using independently annotated English and Modern Standard Arabic (MSA) semantic-role or relation data that can be audited and legally used?

The Phase 6 roadmap requires construction-specific positive, negative, and ambiguous cases in both language profiles. The existing candidate lexicon was derived from the development fixtures, and the v0.4.3 held-out set recombines known lexical entries. Those are useful development checks, but neither is independent linguistic gold.

## 2. Findings

| Resource | What it actually supplies | Suitability for Step 6.6 | Decision |
|---|---|---|---|
| SemEval-2007 Task 4 (English nominal relations) | Official trial, training, and test data plus scoring files for classification of semantic relations between nominals | Directly relevant external English nominal-relation challenge set, but its label inventory is not identical to USG's five modifier constructions; exact data license and redistribution terms still need verification | Candidate external English test source; pin and audit before use |\n| SemEval-2007 Task 18 / Pilot Arabic PropBank (MSA) | Published MSA semantic-role dataset with 8,402 training, 886 development, and 902 test sentences; 95 frequent verbs and 21,194/1,725/1,661 argument instances respectively | Genuine independently annotated MSA predicate-argument gold. Includes complex nominal argument spans (the paper explicitly discusses iḍāfa NP boundary detection), but does not annotate internal nominal modifier relation labels such as possession vs. lexicalized compound | Strong candidate for independent Arabic argument-span/NP-boundary evaluation; not sufficient by itself for all Step 6.6 nominal relation semantics. Verify data files and LDC/ATB rights before access or redistribution |\n| English/Arabic Universal Dependencies PUD | Human-annotated morphology and syntactic dependency relations; 1,000 test sentences per language | Useful independent syntactic evidence for head attachment and spans, but not semantic relation labels such as possession, authorship, part-whole, or event-time scope | Keep as structural audit only; never score semantic correctness from UD labels |
| Universal Proposition Bank 2.0 | Multilingual predicate/argument layers for 23 languages, generated largely by cross-lingual projection and bootstrapping; a small hand-annotated gold subset is reported for English, Polish, and Portuguese | Useful external SRL reference/weak diagnostic where exact language and split are present; Arabic hand-gold is not established by the cited release/paper | Do not call Arabic labels gold; record split-level provenance before any use |
| Universal Proposition Bank 1.0 | Multilingual projected predicate/argument labels for seven languages; inherits each source treebank's license and is mostly automatically generated | Not a source of Arabic independently annotated gold; projected labels have known quality limitations | Not an Arabic gold acceptance source |
| Arabic PropBank public project | Arabic PropBank frame files and documentation/papers | The public GitHub repository describes itself as hosting frame files; it does not provide a distributable sentence-level annotated corpus in that repository | Frames may inform label definitions; not an evaluation corpus |
| Arabic PropBank / LDC resources | Published Arabic PropBank annotation work and related licensed corpora | Access and redistribution rights for the sentence-level annotated data must be verified independently; public frame files do not prove corpus availability | Do not assume public corpus access or redistribute restricted data |
| UD Arabic-PADT | Large Arabic morphological/syntactic treebank | Useful structural/morphology diagnostics, but its treebank license is CC BY-NC-SA 3.0 and it is not semantic-role gold | Optional non-commercial structural study only; not Step 6.6 semantic acceptance |
| Arabic NYUAD UD annotations | CATiB/UD syntactic annotations; underlying Penn Arabic Treebank text is not included and must be obtained separately | Syntax only; source text access is separately restricted | Not semantic gold; do not attempt text reconstruction without lawful access |

## 3. Primary source notes

1. **Universal Proposition Bank 2.0 project:** the release describes predicate senses and argument head/span annotations, multilingual coverage, and distinguishes automatically generated UP data from hand-annotated `GOLD_` subsets. Its release description states that gold data exists only for a subset of languages.  
   - Project: https://universalpropositions.github.io/  
   - Paper: https://aclanthology.org/2022.lrec-1.181/  
   - Paper PDF: https://aclanthology.org/2022.lrec-1.181.pdf

2. **UP2.0 annotation quality boundary:** the paper describes the target-language propbanks as automatically generated and says the manually annotated subset in that release is for English, Polish, and Portuguese. The Arabic-language presence of a projected UP file, if confirmed for a particular release, must not be confused with Arabic human gold.  
   - https://aclanthology.org/2022.lrec-1.181/

3. **Universal Dependencies:** UD annotations standardize morphology and syntactic dependencies, not semantic roles. The Arabic PUD treebank is a 1,000-sentence news/wiki treebank licensed CC BY-SA 3.0. It is a valid independent syntactic audit source but not an oracle for semantic relation labels.  
   - https://universaldependencies.org/treebanks/ar_pud/index.html  
   - https://universaldependencies.org/introduction.html

4. **Arabic PropBank public project:** the GitHub repository says it hosts the current Arabic PropBank frames. The public repository contains frame resources/documentation, not a sentence-level gold corpus suitable for this benchmark. The project page is CC BY-SA 4.0, which applies to that hosted work; it does not grant rights to unrelated underlying LDC corpora.  
   - https://github.com/timjogorman/ArabicPropbank  
   - https://timjogorman.github.io/ArabicPropbank/

5. **UD licensing:** individual treebanks have distinct licenses; some are non-commercial. Each source treebank's own LICENSE and metadata must be checked before inclusion or redistribution.  
   - https://universaldependencies.org/contributing/licensing.html

## 4. What can be used now

- Continue using English and Arabic PUD as **syntactic structural** references for token alignment, dependency attachment, and source-span diagnostics.
- Use UP2.0 only as a separately labeled **projected/weak SRL reference** after pinning the exact release, language, source treebank, split, and license. Do not merge projected labels into the gold denominator.
- Use Arabic PropBank frame files as a frame-definition reference, not as instance-level labels.
- Keep all candidate outputs disabled and candidate-only. No Step 6.6 construction is promoted by this audit.

## 5. Required path to close the gap

The remaining acceptance path is explicit:

1. Pin the exact English and MSA Arabic source datasets and their license/redistribution terms.
2. Obtain sentence-level independently annotated semantic-role or nominal-relation labels for both languages. For Arabic, this requires either a verified accessible Arabic PropBank instance corpus or a separately annotated MSA evaluation set with documented annotation guidelines and provenance.
3. Keep the gold split isolated from the candidate lexicon and all development fixtures.
4. Have annotations independently checked under a documented adjudication protocol; preserve disagreements and unresolved cases as ambiguity rather than forcing a unique label.
5. Meet the Phase 6 per-language/per-construction minimums: 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary examples for each construction profile.
6. Score exact source spans, head/attachment, relation labels, ambiguity/abstention, and construction detection independently.
7. Only after the frozen independent benchmark passes the roadmap thresholds may Step 6.6 be accepted and Step 6.7 unblocked.

If an openly licensed, independently annotated MSA semantic corpus cannot be verified, the correct next step is a small, explicitly authored MSA gold set with transparent annotation guidelines and independent review. Until that review exists, label it **provisional author-annotated**, not adjudicated gold, and do not use it to claim full Step 6.6 acceptance.

## 6. Explicit non-decisions

This audit does not:
- claim that no Arabic semantic-role corpus exists anywhere;
- claim that every Arabic PropBank resource is inaccessible;
- authorize use of LDC material without checking its current license and access terms;
- treat machine-projected UP2.0 Arabic labels as human gold;
- change the USG runtime, lexical resources, grammar rules, SQLite schema, Phase 5 behavior, or `USG-SEM/1.0`;
- enable any nominal construction or unblock Step 6.7.

**Updated outcome:** independent MSA semantic-role gold does exist in the published SemEval-2007 Task 18 / Pilot Arabic PropBank release, and an English nominal-relation gold task exists in SemEval-2007 Task 4. These are promising new evaluation sources, not yet integrated or rights-cleared. The remaining work is to verify their exact data files and licensing, align their annotation units to the Step 6.6 construction inventory, and fill the internal nominal-relation gap—especially for MSA—without pretending predicate-argument labels annotate every modifier relation. The Step 6.6 gate therefore remains open, but the data search has identified stronger concrete candidates than the initial audit.
