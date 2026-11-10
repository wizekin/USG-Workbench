# Structured Query Benchmark 1.0.0

This query benchmark reuses complete canonical USG-SEM/1.0 documents from the
frozen Step 2.6 executor benchmark and the Step 2.7 evidence-assessment
benchmark. Fixture references are exact benchmark IDs and fixture IDs; they
are resolved by the regression suite without altering either source corpus.

Coverage includes direct source assertions, deterministic derived candidates,
open-world no-match, exact-scope conflicts, context and attribution isolation,
disputed/unknown/ambiguous/unresolved goals, resource interruption, unsupported
rules, and unresolved goal references.

The expected result checks distinguish COMPLETE from INCOMPLETE, UNSUPPORTED,
AMBIGUOUS, and UNRESOLVED. The benchmark never treats absence as false or a
source assertion/derived candidate as verified truth.
