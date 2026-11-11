# OW-9+ — Expanding coverage ledger and scope intake

**Status:** OW-9+ foundation implementation  
**Coverage ledger:** 1.0.0

## Why this stage exists

The repository contains more USG modules than the current randomized runner can execute. OW-0 found distinct Python kernel snapshots, model-only record packages, adapters, structured semantic reasoning services, canonical storage, Phase 4/5 interpreters, Phase 6 candidate analyzers, and the browser-based Semantic Workbench. A report that says “USG coverage” without showing this mismatch would overstate what was tested.

OW-9+ adds an inventory-backed coverage ledger. It maps each campaign's actual case and execution records to the versioned OW-0 inventory and the current target-profile registry.

## Coverage states

Each inventoried component is assigned one of the following entry-point states:
- `not_registered_in_open_world_target_profiles`
- `registered_but_not_sampled`
- `sampled_but_not_executed`
- `not_executed_only`
- `entrypoint_exercised`

The ledger counts inventory components, registered targets, targeted cases, execution attempts, tested versions, interfaces, and outcome classes. It also records capability counts and explicitly states `not_assessed_by_entrypoint_sampling`. Testing one entry point does not establish that every capability or every interface in that component was tested.

## Open-scope observations

The ledger retains:
- all observed taxonomy labels and their counts;
- the number of unclassified cases;
- generator-family hints from generation traces;
- languages and target IDs;
- labels, families, and target IDs not found in prior coverage ledgers.

A candidate-new label or generator family is an observation requiring review, not an automatic promotion into the permanent taxonomy. The evaluator never rewrites test cases to assign a new semantic category on its own.

## Scope gaps revealed by the first inventory

The current target registry only contains Phase 4, Phase 5, and the JavaScript Semantic Workbench. The ledger therefore surfaces, among others:
- Python native model generations v0.6.0–v1.4.0 as not registered as open-world targets;
- Python reference kernel snapshots v0.4.0/v0.5.0 as not registered;
- Python document adapters as not registered;
- Phase 2 structured reasoning services as not registered;
- Phase 3 storage/query interfaces as not registered;
- Phase 6 candidate analyzers as not registered;
- JavaScript Workbench browser entry point as registered but not executable by the present OW-3 runner.

Those gaps become explicit scope-expansion work items. Each new target needs a real adapter, its own resource/time budget, an interface contract, structural validators, and independent gold where semantic claims are intended.

## Report and workflow publication permissions

The first OW-6 run showed that this repository's Actions setting does not permit `GITHUB_TOKEN` to create pull requests. The workflow successfully uploaded its artifact and pushed the report branch, but its PR-creation action failed. The workflow is updated to treat the unavailable PR-creation permission as a publication warning rather than a failed evaluation. The branch and artifact remain available; a maintainer can create the report PR manually or enable the repository setting that allows Actions to create pull requests.

## Limits and next expansions

OW-9+ does not claim a final scope. It provides a ledger and repeatable intake rules for adding new target profiles. It does not implement a hidden sample vault, a third-party naturalistic corpus, a browser automation adapter, or a hardened native-code sandbox. These remain explicit outstanding requirements.
