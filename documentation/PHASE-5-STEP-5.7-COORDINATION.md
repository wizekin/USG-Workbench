# Phase 5 — Step 5.7A: Clause Coordination Composition

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Contract:** `USG-INTERPRET/0.2.0`  
**Expression graph:** `USG-INTERPRET-EXPRESSION-GRAPH/0.2.0`

## 1. Scope

This first Step 5.7 gate composes explicitly segmented clause-level coordination into typed expression-graph nodes. English `and`, `or`, `but` and standalone MSA Arabic `و`, `أو`, `لكن` are represented as AND, OR, or CONTRAST nodes. The connective marker and its exact source span remain attached to the node.

## 2. Composition rules

- Each clause is first interpreted independently using the accepted predicate frames.
- A clause-level coordination node has two proposition-set operands.
- Three or more coordinated clauses are grouped left-associatively, with every intermediate node retained.
- Contrast remains a distinct CONTRAST relation and is not rewritten as logical AND.
- Semicolon, temporal, causal, conditional, and complement links remain candidate clause groups; they are not silently treated as boolean coordination.
- Unknown or unresolved clauses continue to produce partial compositions rather than being dropped.

## 3. Acceptance tests

Tests cover English AND/OR/CONTRAST, standalone Arabic conjunction `و`, three-clause left-associative grouping, and the distinction between boolean coordination and temporal/sequence candidate groups. The prior Step 5.5 semantic composition, Steps 5.2–5.6, and Phase 4 regressions remain required.

## 4. Explicit boundary

This gate implements clause-level coordination only. Coordinated predicates and coordinated arguments (shared subject/object structures inside one clause) remain unsupported and are separated into the next Step 5.7B gate. Arabic conjunction clitics attached to words, such as `وكتب`, remain unsupported; the marker must be a separate token.
