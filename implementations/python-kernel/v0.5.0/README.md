# USG automated reference system 0.5

A local, standard-library Python implementation built from `SPECIFICATION.md`
(the user-provided `Universal-Semantic-Grammar-creation.md`). It runs without
models, API keys, downloads, paid plans, or human approval queues.

This is an end-to-end **bounded reference system**, not a claim of complete
understanding of every language or unrestricted autonomous ontology discovery.
The formal representation is broader than the deterministic text parser. See
`IMPLEMENTATION-v04.md` for the seven workstreams, exact coverage and remaining limitations.

## Run on this Windows machine

The launcher finds the bundled Python runtime automatically; the existing
`python` launcher on this machine points to a missing installation.

```powershell
.\run-usg.ps1 run --db usg.db --input examples
.\run-usg.ps1 ingest --db usg.db --text "The doctor gave the patient medication." --compact
.\run-usg.ps1 query --db usg.db --frame GIVE
.\run-usg.ps1 verify --db usg.db
```

For an unattended local inbox, put UTF-8 `.txt` or `.md` documents in a directory:

```powershell
.\run-usg.ps1 run --db usg.db --input D:\my-inbox --watch --interval 30
```

The worker automatically initializes a new database, ingests new/changed files,
resumes jobs after crashes, validates and stores claims, records abstentions,
mines shadow candidates, stages eligible rule proposals, monitors canaries,
rolls back regressions, and audits the store. Repeated scans are idempotent.
Poison jobs stop after bounded retries. Ambiguity and unsupported input are
retained as data; they do not block processing or request a person.

On another machine with Python 3.11+ use `python -m usg ...`. The core has no
third-party runtime dependencies. `pip install .` adds the `usg` entry point;
installation is optional when running from this folder. The release wheel is
`dist/usg-0.5.0-py3-none-any.whl`.

## Commands

```text
init / status / verify / policy / reseal
  Installation, observability and integrity. Reseal is a package-release action;
  the worker never accepts changed enforcement code automatically.
ingest --text TEXT | --file PATH [--language en|ar] [--anchor-date YYYY-MM-DD]
  Compile source units; use --compact for concise results.
query [--frame GIVE] [--role RECIPIENT] [--label patient] [--concept Patient]
      [--view source|trusted|all] [--limit 50]
  Retrieve whole source assertions, with their operators and provenance.
inspect --candidate 1
  Inspect the IR, certificate, mentions, decision and validation results.
reason [--view trusted|source]
  Bounded subclass/inverse/transitive reasoning with premise IDs.
learn [--proposal proposal.json]
  Mine patterns and test/stage declarative proposals without a human queue.
issues [--analyze]
  Inspect aggregated issue codes; optional general remote analysis.
run --input DIRECTORY [--watch] [--interval 30]
  Durable inbox processing and maintenance.
export --output knowledge.usbf [--mode reversible|semantic] [--format usbf|json]
import --file knowledge.usbf
  Reversible exports retain exact source Unicode and derivations. Imports
  re-interpret source records in quarantine; archive statuses have no authority.
backup --output snapshot.db
  SQLite consistent snapshot; existing files are never overwritten.
benchmark [--split test|dev] [--output report.json]
  Independent expected roles/operators, contrastive tests and codec measurements.
```

Database commands accept `--db PATH` (default `usg.db`). New ingestion initializes
it automatically. Query output is JSON. Source-supported claims remain
`SOURCE_ASSERTED`; formal validity never upgrades them to world truth. The
trusted view is empty until an independent evidence policy establishes a claim.
Reasoning over the source view returns `INFERRED` results capped by source support.

## Optional models: all off by default

| Setting | Effect |
|---|---|
| `USG_LOCAL_MODEL` | Enables an Ollama closed-set advisory selector |
| `USG_LOCAL_URL` | Literal loopback endpoint, default `http://127.0.0.1:11434` |
| `USG_BIG_ENABLED=1` | Explicit remote opt-in, also requiring URL and model |
| `USG_BIG_URL` | HTTPS OpenAI-compatible base URL, including `/v1` if required |
| `USG_BIG_MODEL` | Model offered by your provider |
| `USG_BIG_API_KEY` | Optional credential; never persisted |

Remote models receive **issue-code counts only**, never document text, source
examples, assertions or credentials. They can analyze general issues or propose
rules in a closed declarative DSL. They cannot interpret individual sentences,
execute code, approve output, change the validator, grant trust or raise budgets.
Requests are reserved transactionally before sending: at most 3/day, 1/hour,
12,000 reserved tokens/day, with deduplication, timeouts and failure backoff.
These are application limits, not a promise about any provider's free quota.
Offline operation is complete when a model is disabled, exhausted or unavailable.

The local model is advisory, not an unrestricted alternative parser. The remote
model does not acquire a general grammar-learning capability just by agreeing
with itself. Unvetted semantics are automatically deferred. Vetted literal verb
aliases still require replay, regression, constructed gold, contrastive and
metamorphic tests, then live canary observations and automatic rollback.

## Verify

```powershell
# Or use a working Python 3.11+ executable directly.
$usgPython = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $usgPython -m unittest discover -s tests -t .
.\run-usg.ps1 benchmark --output benchmark-baseline.json
```

`benchmark-baseline.json` contains the measured baseline. Its small constructed
corpus measures the documented subset, not general language accuracy. Tests also
exercise hostile/truncated files, failed transactions, model quotas, queue
leases, code tampering, unsupported text, scope and rollback. No real model
request is required by the test suite.

USBF supports the legacy JSON profile and the new experimental compact frame
profile. Both pin versions, use independently compressed checksummed blocks,
and enforce bounded decoding. Codec selection is measured; no compression
advantage over ordinary compressed JSON is assumed.

## Additional services in 0.3

Compact frame exports are now the default for USBF. `--codec json` preserves the
older JSON payload profile; `--codec auto` measures both codecs and three block
sizes, verifies exact decoding, and selects the smallest block within the size
tolerance. The compact profile carries local dictionaries, pinned frame-role
schemas, three-bit role states, canonical varints and bounded typed payloads.
It is experimental and does not claim interoperability with a finalized standard.

`evaluate --config policy.json --receipts receipts.json` applies an evidence
policy to authenticated attestations. Policy configuration maps each authority
to an independent origin cluster and an environment-variable name containing its
key; keys are never stored. Unsigned or stale receipts, duplicate origins and
ambiguous interpretations cannot promote a claim. Authenticated contradictions
mark a claim disputed. Set `USG_EVIDENCE_CONFIG` and `USG_EVIDENCE_RECEIPTS` to run
this evaluator during unattended maintenance. No authorities are trusted by default.

`partition --directory output/domains --domain MEDICINE --version 1` writes a
content-verified, immutable domain snapshot. Global IDs remain unchanged. The
partition reader loads a bounded number of shards and supports pinned older
versions. These snapshots are derived physical storage, not a second truth store.

Completed perfect/perfective frame descriptions now expose inherited final
states and ESSENTIAL effects in `reason` output under `state_entailments`.
Negation, intentions, future descriptions and typical outcomes do not license
those achieved effects.


## Seven-workstream release

Version 0.4 adds scoped definition versioning, L5 contextual reports and conflict
handling, persisted calibration/drift monitoring, offline dependency analyses and
lexical resources, expanded Arabic handling, typed generalization and automated
alias discovery, rollback-driven reprocessing, measured resource scheduling,
function/definition inference, template compression and linked-data exchange.
No paid service or model is needed for these features.

```powershell
.\run-usg.ps1 acceptance --full --output acceptance-v04.json
.\run-usg.ps1 traceability --output requirements-traceability.json
.\run-usg.ps1 run --db usg.db --input examples --lexicon examples\lexicon.json
.\run-usg.ps1 ingest --db usg.db --file examples\dependency-source.txt --conllu examples\dependency-analysis.conllu
.\run-usg.ps1 define --db usg.db --file examples\definition.json
.\run-usg.ps1 reason --db usg.db --view source --scope example-medicine
.\run-usg.ps1 calibration --db usg.db --category extraction
.\run-usg.ps1 export --db usg.db --output knowledge.jsonld --format jsonld
.\run-usg.ps1 export --db usg.db --output knowledge.trig --format trig
.\run-usg.ps1 export --db usg.db --output knowledge.usbf --codec template
.\run-usg.ps1 upgrade --db usg.db --backup before-upgrade.db
```

The upgrade command is an unattended release operation with acceptance checks,
a fresh backup, migrations, seal publication and automatic restoration on failure.
Stop the inbox process during upgrades. Definitions remain scoped meanings;
formal validation and frequent observations never establish world truth.

See `IMPLEMENTATION-v04.md`, `VERIFICATION-v04.md` and `acceptance-v04.json`.
The traceability inventory covers all twelve parts and explicitly records which
claims remain unproven. Full specification conformance is not claimed.


## Native semantic constructors in 0.5.0

This release adds typed native constructors for `PREDICATE_APP`, `CONNECTIVE`,
and `QUANTIFIER` without changing the 0.4.0 baseline.

- `PREDICATE_APP` has result sort SIT. Ordered argument roles align one-to-one
  with operands; it is not a guessed frame application and does not assert occurrence.
- `CONNECTIVE` has result sort PROP. Its identity and named operand roles remain
  explicit and ordered. Conditional antecedent/consequent order is validated.
  WHEN, EXCEPTION, CONCESSIVE, CONTRAST and unknown identities are not normalized
  into Boolean operators.
- `QUANTIFIER` has result sort PROP and one proposition-valued body. Its binder
  has a stable identity; restrictor and binding descriptors are preserved as
  canonical JSON metadata and are not silently converted to legacy `Q`.
- Structured source metadata can be recovered with `metadata_value(node, field)`.
- Binder utilities provide free-variable occurrence reporting, alpha-equivalence,
  and identity-aware substitution. The existing scope API recognizes stable
  binder identities as well as legacy name-bound `Q` variables.
- `OPAQUE` and `UNRESOLVED_REF` are distinct preservation-only nodes. Both
  remain sort `ANY` and are excluded from inference eligibility.

The release intentionally does not infer registered frames or connective
truth conditions from lexical labels. Exact conversion to legacy `APPLY` or
`Q` remains a separate proof obligation.
