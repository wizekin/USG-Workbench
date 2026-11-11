# OW-6 — First broad randomized pilot

**Status:** OW-6 pilot workflow implementation  
**Random generator:** 1.0.1  
**Diagnostic importer:** 1.0.0  
**Scorer:** 1.0.0  
**Campaign report:** 1.0.0

## Pilot populations

The first campaign combines two populations and explicitly leaves the third unpopulated until a naturalistic dataset passes license/privacy review:

1. **Unconstrained random:** 1,000 base prompts by default, with each exact prompt routed across Phase 4 v0.1.0, Phase 5 v0.2.0, and JavaScript Semantic Workbench v0.5.4. This creates 3,000 target-specific case records. The JavaScript target is deliberately recorded as `not_executed` until browser automation exists; it is not scored as a USG crash or semantic failure.
2. **Controlled diagnostic:** the six Phase 4 v0.1.0 fixtures and 100 Phase 5 v0.2.1 fixtures. Their expected completion statuses, Phase 4 expression counts, Phase 5 constructions, role bindings, and source spans are imported into the scenario oracle field and scored separately.
3. **Naturalistic:** empty in this first pilot. No third-party corpus is imported until exact license, redistribution, provenance, and privacy requirements are verified. The report therefore remains **partial**, even if every generated case is executed.

The random prompt generator 1.0.1 adds Arabic-only prompts alongside English and English/Arabic mixed-language instructions. Language hints and any Phase 4/5 fallback mapping remain recorded.

## Diagnostic gold provenance

The controlled corpus import is repository-authored and version-pinned:
- Phase 4: `benchmarks/phase4-interpretation/v0.1.0/fixtures.json` (six bounded cases).
- Phase 5: `benchmarks/phase5-interpretation-v0.2.1/corpus.json` (100 simple-transitive English/MSA Arabic cases).

The expected fields are kept in each diagnostic scenario. The score adapter compares only those explicitly annotated fields. The source data is independent of the runtime execution path but is not an external third-party human-annotation study; the campaign report preserves this limitation.

Random requests have no expected semantic output. They receive structural/source-integrity checks only; they do not enter the semantic accuracy denominator.

## Execution matrix and safety

The workflow runs one fresh OW-3 worker per case. Phase 4 and Phase 5 use their actual Python service APIs. The browser-only JavaScript target is preserved as not executed. Per-case time/resource budgets and result hashes remain in the records. Test input is data and never shell code.

Default size is 3,000 unconstrained-random attempts plus 106 controlled diagnostic cases (3,106 case records). Use `workflow_dispatch` to select 1–2,000 base random prompts. Target matrix mode multiplies that number by three.

## Published artifacts

After execution and scoring, the workflow:
1. Builds the campaign JSON and Markdown reports.
2. Creates a write-once campaign bundle with all cases, all results, all scores, source manifests, and a SHA-256 bundle manifest.
3. Uploads the bundle as a workflow artifact.
4. Creates a new pull request that adds the complete bundle under `evaluations/open-world/campaigns/<campaign-id>/`.

The report pull request is separate from the implementation PR. It preserves failures and partial outcomes without overwriting previous campaigns. A published campaign report should be merged only after its bundle manifest and population totals are checked.

## Interpretation rule

A passing pilot workflow means the **campaign ran and its evidence was preserved**. It does not mean that USG passed the pilot. A report with many unsupported requests, ambiguous results, invalid outputs, or unexecuted interfaces is still a valid and useful result.
