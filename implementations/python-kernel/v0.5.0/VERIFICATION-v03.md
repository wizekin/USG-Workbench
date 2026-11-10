# Verification: USG 0.3.0

Date: 2026-10-24 (Africa/Cairo).

- 389 unittest cases passed in the final regression run. See `test-results-v03.txt`.
- New compact-codec tests cover all hole states, absent roles, repeated event
  descriptions, unknown-frame fallback, Unicode, truncation and 300 mutations.
- Evidence-policy tests cover independent signed support, forged/repeated/stale
  receipts, verified promotion and contradiction-driven dispute.
- Frame-effect tests distinguish completed possession transfer from typical
  ownership and keep negated/intended effects out of achieved-state inference.
- Domain snapshots were tested for immutability, older-version reads and reopen.
- Codec/block optimization checks both codecs and exact semantic round trips.
- The fresh CLI inbox, export, quarantine import and MEDICINE partition workflow
  passed. The source and re-import databases passed complete integrity checks.
- The offline wheel built successfully:
  `dist/usg-0.3.0-py3-none-any.whl`.

No real language-model or remote-provider call was needed for these checks.
Passing these tests establishes the tested mechanisms, not complete compliance
with all requirements in the twelve-part specification. Remaining work is
listed in `IMPLEMENTATION-v03.md`. The normative-statement inventory is a
traceability starting point, not a completed conformance assessment.
