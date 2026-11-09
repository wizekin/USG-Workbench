# USG Archive Inventory and Baseline Verification

Inspection date: 2026-11-09 (UTC)
Repository: `wizekin/USG-Workbench`
Branch: `main`

## Original archives

| Archive | Release | Size (bytes) | ZIP entries | Files | Directories | SHA-256 | Git blob SHA | Integrity |
|---|---:|---:|---:|---:|---:|---|---|---|
| `archives/workbench/USG_Semantic_Workbench_v0.5.4.zip` | Workbench 0.5.4 | 237116 | 60 | 56 | 4 | `9c76280ad000abaf14b52545bf6de9d25656744428f1257519c2c09ebff434a9` | `f5cc110016bec328fdb8e60edf890190e122b973` | Passed |
| `archives/python-kernel/usg-semantic-kernel-corrected.zip` | Python package 0.4.0 | 1192402 | 173 | 152 | 21 | `de3c4466b61ac1d09f23761b7c31faa0f685fdf3bfb148e7e60f132552e1095e` | `7c4338657bdd9c8c2a697975f968b6b62c349a0b` | Passed |

SHA-256 was calculated from the exact archive bytes retrieved from GitHub. Both ZIPs passed `zipfile.testzip()` with no damaged member. The original archive blobs were relocated without rewriting their contents.

## Workbench 0.5.4

- `VERSION.txt` confirms version 0.5.4.
- JavaScript/browser research workbench with local Node bridge and optional local Ollama model proposals.
- The package documents a finite English source-composition grammar and explicitly states that deterministic structural checks do not prove entailment or objective truth.
- Test command: `bash tests/run_all_tests.sh`.
- Fresh run: exit code 0; 329 individual PASS lines, plus a separately reported 44 semantic-foundation tests passed, 0 failed. Combined runner accounting: 373 passed, 0 failed.
- `TEST_RESULTS.md` reports 329 assertions and omits the separate 44-test semantic-foundation count from that aggregate. Both numbers are recorded rather than silently changing the packaged report.
- Existing README documents human review before knowledge-base acceptance. Preserved unchanged in this baseline.

## Python reference system 0.4.0

- `pyproject.toml` confirms package `usg`, version 0.4.0, Python >=3.11, and no third-party runtime dependencies declared.
- Main entry points include `usg.runtime.USG`, `usg.cli`, `usg.__main__`, and `run-usg.ps1`.
- Fresh command: `python -m unittest discover -s tests -t .`.
- Fresh run under Python 3.13.18: exit code 0; 436 tests passed.
- The run emitted ResourceWarnings about unclosed SQLite connections; no test failures occurred. Record for later cleanup; not changed during baseline setup.
- Packaged historical logs record 430 and 375 tests, respectively. The fresh run against the archived source is 436.
- `acceptance-v04-kindfix.json` records a passing 13-check acceptance run. Its benchmark uses 49 constructed samples, 40 supported; its own scope explicitly says constructed subset and consistency proxies, not open-domain correctness. No model was used in that recorded benchmark.

## Scope and limitations

These checks establish archive integrity, source extraction feasibility, and successful execution of each package's own test suite in the inspection environment. They do not establish unrestricted English or Arabic understanding, general semantic accuracy, or full interoperability between the implementations.

The two projects have different internal representations, runtime environments, version histories, and documented review/acceptance policies. They remain distinct baselines. No semantic mappings or cross-implementation compatibility are claimed.


## Extraction and repository verification

Both archives have now been extracted into the versioned implementation directories:

- Workbench 0.5.4: 56 files in implementations/semantic-workbench-js/v0.5.4/.
- Python kernel 0.4.0: 152 files in implementations/python-kernel/v0.4.0/.

The final recursive Git tree was checked after commit: exactly 56 Workbench files and 152 Python-kernel files are present. No test-generated Python bytecode was committed. The original ZIPs remain in archives/ and their SHA-256 values were rechecked during the extraction workflow.

A GitHub Actions run on 2026-11-09 completed successfully after performing fresh tests against the extracted copies:
- Workbench test command: bash tests/run_all_tests.sh — passed.
- Python kernel test command: python -m unittest discover -s tests -t . — passed.

The extracted source is a preserved baseline, not a merged application. No source code was changed as part of this extraction; repository-level README and navigation documentation were added separately.
