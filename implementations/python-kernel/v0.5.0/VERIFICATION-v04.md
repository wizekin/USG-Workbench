# USG 0.4 verification

Verified on 2026-10-24 with Python 3.12.14, SQLite 3.53.1, Windows 11.

- Full regression suite: **430 tests passed** in 21.932 seconds.
- End-to-end acceptance: **13 checks passed**, including the full suite and unchanged release-file verification.
- Constructed benchmark: 49 cases; 40 supported structural gold cases; no false confident resolutions, validation failures or collapsed contrast pairs in this corpus.
- Standalone installed wheel: all 12 packaged acceptance checks passed from outside the source directory.
- CLI integration: 17 commands passed, including lexical resources, CoNLL-U, definitions, scoped inference, calibration reporting, exports, imports, inbox processing and store verification.
- A copy of the actual 0.3 database upgraded through migrations 5, 6 and 7 with a pre-upgrade snapshot; all six existing assertions passed the new audit.
- Upgrade failure restoration, lease crash recovery, rollback/reprocessing, current-view supersession, source offsets, Arabic vocalization/negation, unknown syntax, evidence independence, contextual uncertainty, calibration drift and malformed codecs have executable regression coverage.
- Core runtime dependencies: Python standard library. Models used: **0**. Human review needed: **no**.

Source and wheel code-manifest digest:
`fc7c7171ab7fc2e5d5ec5462e0e23c51489365c412e9ff5fe0a4863c9cc18c42`

Wheel: `dist/usg-0.4.0-py3-none-any.whl` (224254 bytes).
SHA-256: `f5b7850bdf78bb6dfd76cd5a425071ae9c6ba1d4a722dd0ca30702dd7cc7f737`.

Evidence files: `acceptance-v04.json`, `test-results-v04.txt`,
`requirements-traceability.json`, `output/package-v04-acceptance.json`,
`output/cli-verification-v04.json`.

The source trace inventories 423 normative/rule statements and 562 sections from all twelve parts. Text references are not counted as passed semantic requirements. Full conformance remains explicitly unproven.

These results establish the documented bounded mechanisms. They do not establish open-domain language accuracy, correct autonomous discovery of arbitrary ontology meanings, or production-scale distributed storage. The 49-case benchmark is constructed, and its parser latency excludes storage, models and I/O. See `IMPLEMENTATION-v04.md` for the remaining capabilities and interchange losses.
