"""Universal Semantic Grammar (USG) — fully automated reference implementation.

Design constraints of this implementation (see DESIGN.md):
  * No human review or intervention at runtime. Every decision that the
    specification assigned to a person is replaced by a deterministic,
    machine-checkable mechanism, or the action is forbidden/shadow-only.
  * Big (remote) AI models are used sparingly and only to propose *general
    rules* or analyse *general issues* from aggregated digests. Every proposal
    is verified automatically before it can have any effect.
  * Standard library only for the core. spaCy / Ollama / remote endpoints are
    optional adapters.
"""

GRAMMAR_VERSION = "1.0"
ONTOLOGY_RELEASE = "0.2"
RULESET_RELEASE = "R-0.2"
__version__ = "0.5.0"
