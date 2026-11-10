"""Rule definitions and enforcement registry.

* A RULE is a policy (what must hold); a CHECK (checks.py) is an atomic
  validator function that tests part of a rule. One rule may need several
  checks and one check may serve several rules (E-48).
* Every rule sits on two independent axes (E-49): KIND (what it governs) and
  AUTHORITY LEVEL (who may change it). Level 1 (foundational, SG-FND-*) is
  SEALED: no runtime process can change it; a Level n rule may depend only on
  rules of level <= n.
* Rule ids are ``SG-<DOMAIN>-<NNN>`` (E-01). Legacy ids of the source material
  resolve through ``resolve_rule_id``.
* A rule is ACTIVE only when every check that enforces it is implemented in the
  running validator; otherwise it is SPECIFIED (documented, enforced by a later
  module). The AI can cite only registered ids; inventing one fails VC-S04.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from ..errors import InvariantViolation
from ..util import canonical_json, sha256_hex


class RuleKind(str, Enum):
    CONSTRUCTION = "CONSTRUCTION"
    INTERPRETATION = "INTERPRETATION"
    KNOWLEDGE = "KNOWLEDGE"


DOMAINS = ("FND", "CON", "TYP", "FRM", "INT", "EVD", "CAN", "IDN", "GEN", "LRN", "KNW", "ENC", "GOV", "SEC")
_ID = re.compile(r"^SG-(" + "|".join(DOMAINS) + r")-(\d{3})([a-e]?)$")


@dataclass(frozen=True)
class RuleDef:
    rule_id: str
    kind: RuleKind
    authority: int  # 1 foundational (sealed) | 2 grammar | 3 domain
    check_class: str  # D deterministic, H hybrid, R review-dependent, L logic/evidence (may combine: "D/H")
    description: str
    aliases: tuple[str, ...] = ()
    enforced_by: tuple[str, ...] = ()  # check ids (VC-...) that enforce it
    part: str = ""  # specification reference
    version: int = 1

    def __post_init__(self):
        if not _ID.match(self.rule_id):
            raise InvariantViolation(f"malformed rule id {self.rule_id!r}", "SG-GOV-002")
        if self.authority not in (1, 2, 3):
            raise InvariantViolation("authority must be 1, 2 or 3", "SG-GOV-002")
        if self.rule_id.startswith("SG-FND-") != (self.authority == 1):
            raise InvariantViolation("exactly the SG-FND-* rules have authority level 1", "SG-FND-005")

    @property
    def domain(self) -> str:
        return self.rule_id.split("-")[1]

    def to_json(self) -> dict:
        return {"rule_id": self.rule_id, "kind": self.kind.value, "authority": self.authority, "check_class": self.check_class,
                "description": self.description, "aliases": list(self.aliases), "enforced_by": list(self.enforced_by),
                "part": self.part, "version": self.version}


C, I, K = RuleKind.CONSTRUCTION, RuleKind.INTERPRETATION, RuleKind.KNOWLEDGE


def _r(rid, kind, auth, cls, desc, aliases=(), checks=(), part=""):
    return RuleDef(rid, kind, auth, cls, desc, tuple(aliases), tuple(checks), part)


RULES: tuple[RuleDef, ...] = (
    # ---- foundational (Level 1, sealed) ------------------------------------------------------------
    _r("SG-FND-001", C, 1, "D", "Every id, rule, frame, role and span reference resolves to an active record or a tombstone",
       ("VALID_REFERENCE_REQUIRED", "FRAME_EXISTS", "CONCEPT_ID_REGISTERED", "RULE_ID_REGISTERED"), ("VC-S03", "VC-S04"), "Part 5 §5.4"),
    _r("SG-FND-002", C, 1, "D", "The type check runs on every commit", ("TYPE_CHECKING_REQUIRED",), ("VC-T01", "VC-T02"), "Part 5 §5.4"),
    _r("SG-FND-003", C, 1, "D", "Every committed assertion has a source or an authorized origin", ("SOURCE_PROVENANCE_REQUIRED",), ("VC-V01",), "Part 5 §5.4"),
    _r("SG-FND-004", C, 1, "D", "No candidate, and no process that produced it, can promote it (no self-approval; models are never decision actors)",
       ("UNVERIFIED_CANDIDATES_CANNOT_SELF_APPROVE",), (), "Part 5 §5.5"),
    _r("SG-FND-005", C, 1, "D", "No AI or learning process may modify FND rules, validator logic or the rulebook (sealed at install)",
       ("NO_UNAUTHORIZED_GRAMMAR_CHANGE", "RULEBOOK_PROTECTED"), (), "Part 5 §5.5"),
    _r("SG-FND-006", C, 1, "D", "Decisions and changes go to an append-only audit history", ("AUDIT_APPEND_ONLY",), (), "Part 5 §5.5"),
    _r("SG-FND-007", C, 1, "D", "AI-originated candidates carry a derivation certificate and a validation report before any promotion",
       ("CERTIFICATE_REQUIRED",), ("VC-V04",), "Part 5 §5.5"),
    # ---- construction -----------------------------------------------------------------------------------
    _r("SG-CON-001", C, 2, "D", "A representation satisfies its frame's constraints", ("SG-007",), ("VC-T05", "VC-T06"), "Part 3"),
    _r("SG-CON-002", C, 2, "D", "Frame application: frame exists at the pinned version, roles defined, REQUIRED roles bound or explicit holes, cardinality, types",
       ("FRAME_APPLICATION",), ("VC-S05", "VC-S06", "VC-S07", "VC-S08", "VC-T02"), "Part 3 §3.4"),
    _r("SG-CON-003", C, 2, "D", "Role fillers are referents, literals, kind-references or nested descriptions - never bare concept ids", (), ("VC-T04",), "Part 2 §2.5"),
    _r("SG-CON-004", C, 2, "D/H", "Truth-conditional language features belong to operators; style-only features to annotations", (), (), "Part 2 §2.12"),
    _r("SG-CON-005a", C, 2, "D", "Closed assertions: no free variable", ("VARIABLE_REFERENCE",), ("VC-S12",), "Part 3 §3.6"),
    _r("SG-CON-005b", C, 2, "D", "A binder never shadows a variable already in scope", (), ("VC-S13",), "Part 3 §3.6"),
    _r("SG-CON-005c", C, 2, "D", "Variables are alpha-renamed canonically (v0, v1, ...)", (), (), "Part 3 §3.6"),
    _r("SG-CON-005d", C, 2, "D", "Discourse referents are constants, not variables", (), ("VC-T04",), "Part 3 §3.6"),
    _r("SG-CON-005e", C, 2, "D", "Anaphora under a binder refers to the bound variable within its scope", (), (), "Part 3 §3.6"),
    _r("SG-CON-006", C, 2, "D", "Sort discipline: operators accept only the sorts in their signature", (), ("VC-S09",), "Part 3 §3.3"),
    _r("SG-CON-007", C, 2, "D", "ALT: at least two same-sort members, ordinal ranks, bounded group size", (), ("VC-S14",), "Part 3 §3.14"),
    _r("SG-CON-008", C, 2, "D", "ERROR nodes exist only in candidates, never in canonical expressions", (), ("VC-S11",), "Part 3 §3.14"),
    _r("SG-CON-009", C, 2, "D", "Negation takes a proposition; a negated situation is never stored as an occurred event", ("NEGATION_SCOPE", "NEGATION_SCOPE_RULE"), ("VC-S09",), "Part 3 §3.7"),
    # ---- types -----------------------------------------------------------------------------------------------
    _r("SG-TYP-001", C, 2, "D/L", "Three-valued role-type compatibility; INCOMPATIBLE needs a registered coercion",
       ("TYPE_COMPATIBILITY", "TYPE_COMPATIBLE", "FRAME_TYPE_VALIDATION"), ("VC-T02",), "Part 3 §3.3.2"),
    _r("SG-TYP-002", C, 2, "H", "A figurative or coerced reading cites a registered mapping", (), ("VC-T07",), "Part 3 §3.15"),
    # ---- frames ----------------------------------------------------------------------------------------------
    _r("SG-FRM-001", C, 2, "D/L", "A role may be bound only if the frame defines it and evidence supports the binding",
       ("SG-002", "ROLE_ASSIGNMENT", "ROLE_ALLOWED", "ROLE_BINDING"), ("VC-S06",), "Part 4 §4.3"),
    _r("SG-FRM-002", C, 2, "D/L", "A specialization preserves the defining commitments of its parent", ("SG-FRAME-002", "SG-INHERIT-001"), (), "Part 4 §4.5"),
    _r("SG-FRM-003", C, 2, "D", "Role narrowing only; the projection test", (), (), "Part 4 §4.5"),
    _r("SG-FRM-004", C, 2, "D/L", "Multiple-inheritance conjunction; no linearization", (), (), "Part 4 §4.5"),
    _r("SG-FRM-005", C, 2, "D", "HAS_FUNCTION does not imply IS_A", (), (), "Part 4 §4.8"),
    _r("SG-FRM-006", C, 2, "D", "Role order is append-only", (), (), "Part 4 §4.3"),
    _r("SG-FRM-007", C, 2, "D", "An analogy is not an equivalence", (), (), "Part 4 §4.10"),
    _r("SG-FRM-008", C, 2, "D", "A frame needs a valid/incomplete/invalid/contrastive test set", (), (), "Part 4 §4.13"),
    _r("SG-FRM-009", C, 2, "D", "FN primitives are protected from automatic change", (), (), "Part 4 §4.8"),
    _r("SG-FRM-010", C, 2, "D", "Layer discipline and authority by layer", (), (), "Part 4 §4.11"),
    # ---- interpretation (enforced by the interpreter, Part 7) ---------------------------------------------------
    _r("SG-INT-001", I, 2, "H", "An entity is typed only with sufficient evidence", ("SG-001",), (), "Part 5"),
    _r("SG-INT-003", I, 2, "D", "Parser output is evidence, not authority", (), (), "Part 8 §8.3.3"),
    _r("SG-INT-004", I, 2, "D", "Prefer narrow closed-set model tasks over open generation", (), (), "Part 8 §8.11.2"),
    _r("SG-INT-005", I, 2, "D", "A pattern bypasses the model only if ACTIVE and every guard passes", (), (), "Part 8 §8.12"),
    _r("SG-INT-006", I, 2, "H", "Control: the unwritten subject co-refers with the controller named by the lexical hint", (), (), "Part 8 §8.7.4"),
    _r("SG-INT-007", I, 2, "D", "A referent introduced in an embedding context carries that context", (), (), "Part 8 §8.7.2"),
    _r("SG-INT-008", I, 2, "D", "No fitting frame yields FRAME_GAP, never a forced fit", (), (), "Part 8 §8.6"),
    _r("SG-INT-009", I, 2, "D", "Ambiguity policy: select only with decisive evidence, otherwise retain ALT", (), (), "Part 8 §8.9"),
    _r("SG-INT-010", I, 2, "H", "Passive by-phrase maps to the agent role", ("PASSIVE_AGENT_MAPPING",), (), "Part 5 §5.3"),
    _r("SG-INT-011", I, 2, "H", "Passive subject mapped by valence pattern", ("PASSIVE_PATIENT_MAPPING",), (), "Part 5 §5.3"),
    _r("SG-INT-012", I, 2, "H", "Active constructions mapped by valence pattern", ("ACTIVE_VOICE_MAPPING",), (), "Part 5 §5.4"),
    _r("SG-INT-013", I, 2, "H", "Runtime metamorphic consistency checks are risk-based and sampled", (), (), "Part 10 §10.11"),
    _r("SG-INT-020", I, 2, "H", "Negation cue to operator scope; scope ambiguity retained as ALT", ("NEGATION_SCOPE_MAPPING",), ("VC-V07",), "Part 5 §5.4"),
    _r("SG-INT-021", I, 2, "H", "Modal cue to force x flavor; ambiguous flavor stays ALT", ("MODAL_FLAVOR_SELECTION",), ("VC-V07",), "Part 5 §5.4"),
    _r("SG-INT-022", I, 2, "H", "Quantifier phrase to Q with restrictor and scope", ("QUANTIFIER_SCOPE_MAPPING",), ("VC-V07",), "Part 5 §5.4"),
    _r("SG-INT-030", I, 2, "H/R", "Pronoun/anaphor to antecedent referent, with evidence", ("SG-COREFERENCE",), (), "Part 5 §5.4"),
    _r("SG-INT-031", I, 2, "H", "'because' and similar to CAUSATION with an explanatory type", ("SG-EXPLANATORY-RELATION",), (), "Part 5 §5.4"),
    _r("SG-INT-040", I, 2, "H", "Frame-trigger lexical sense to frame selection", ("SG-FRAME-TRANSFER",), (), "Part 5 §5.4"),
    _r("SG-INT-050", I, 2, "D/H", "Temporal expression to TIME value or relative expression; resolved bounds recomputed deterministically", (), ("VC-V05",), "Part 5 §5.4"),
    _r("SG-INT-051", I, 2, "H", "Tense and aspect cue to operator", (), ("VC-V07",), "Part 5 §5.4"),
    # ---- evidence -------------------------------------------------------------------------------------------------
    _r("SG-EVD-001", K, 2, "D/L", "No unsupported content: every element has a span, a declared inference with valid premises, or an authorized source",
       ("SG-003", "SG-EVIDENCE-003"), ("VC-V01", "VC-V09"), "Part 5 §5.4"),
    _r("SG-EVD-002", K, 2, "D", "Preserve uncertainty and ambiguity", ("SG-004",), (), "Part 5 §5.4"),
    _r("SG-EVD-003", K, 2, "D", "Separate observation from inference; inference is never relabelled source-stated", ("SG-006",), ("VC-V06",), "Part 5 §5.4"),
    _r("SG-EVD-004", K, 2, "D", "Presupposed content is emitted inside its context", (), ("VC-G08",), "Part 3 §3.8.2"),
    _r("SG-EVD-005", K, 2, "D", "Spans exist, lie within the stored text, and the cited text matches the claim", ("SOURCE_SPAN_VALID",), ("VC-S10", "VC-V02"), "Part 5 §5.4"),
    _r("SG-EVD-006", K, 2, "D/L", "Basis integrity: EXPLICIT needs a span, GRAMMATICAL a registered rule, BACKGROUND a registered inference", (), ("VC-V03",), "Part 5 §5.6"),
    _r("SG-EVD-007", K, 2, "D", "Commitment holder and evaluation context gate the trusted view", (), (), "Part 6 §6.2"),
    _r("SG-EVD-008", K, 2, "D", "VERIFIED only through a recorded evidence policy", (), (), "Part 6 §6.6"),
    _r("SG-EVD-009", K, 2, "D", "No self-promotion by learning, extraction, repetition or retrieval", (), (), "Part 6 §6.6"),
    _r("SG-EVD-010", K, 2, "D", "Contradictions are preserved, never overwritten", (), (), "Part 6 §6.8"),
    _r("SG-EVD-011", K, 2, "D", "Corroboration counts independent origins only", (), (), "Part 6 §6.5.3"),
    _r("SG-EVD-012", K, 2, "D", "Derived claims inherit the weakest premise (support cap)", (), (), "Part 6 §6.4.2"),
    # ---- canonicalization --------------------------------------------------------------------------------------------
    _r("SG-CAN-001", C, 2, "D/H", "Canonical sharing only if the declared meaning scope is preserved; every rule ships positive and negative tests", (), ("VC-G10",), "Part 3 §3.17"),
    _r("SG-CAN-002", C, 2, "D", "Forbidden simplifications: no double-negation elimination, no quantifier/negation swap, no duplicate removal", (), ("VC-G10",), "Part 3 §3.17"),
    _r("SG-CAN-003", C, 2, "D", "Every canonicalization applied is recorded with rule id and version", (), (), "Part 3 §3.17"),
    _r("SG-CAN-004", C, 2, "D", "Structural equality ignores annotations", (), (), "Part 3 §3.16"),
    _r("SG-CAN-010", C, 2, "H", "Active and passive map to one canonical event frame when roles are identifiable", ("CANON_ACTIVE_PASSIVE_001",), (), "Part 5 §5.4"),
    _r("SG-CAN-020", C, 2, "D", "Flatten and sort AND/OR children (associativity and commutativity only)", ("FLATTEN_SORT",), ("VC-G10",), "Part 3 §3.17"),
    _r("SG-CAN-021", C, 2, "D", "Alpha-rename bound variables", ("ALPHA_RENAME",), ("VC-G10",), "Part 3 §3.17"),
    _r("SG-CAN-022", C, 2, "D", "Time normalization: resolved bounds alongside the relative expression", ("TIME_NORMALIZATION",), ("VC-G10",), "Part 3 §3.17"),
    _r("SG-CAN-023", C, 2, "D", "Inverse-relation normalization", ("INVERSE_RELATION",), ("VC-G10",), "Part 3 §3.17"),
    _r("SG-CAN-024", C, 2, "D", "Symmetric argument ordering", (), ("VC-G10",), "Part 3 §3.17"),
    # ---- identity ---------------------------------------------------------------------------------------------------------
    _r("SG-IDN-001", K, 2, "L", "Search before create: reuse an existing concept before proposing a new one", ("SG-005",), (), "Part 7"),
    _r("SG-IDN-002", K, 2, "L/R", "Merge only at grade ESTABLISHED, in scope", ("SG-IDENTITY-005",), (), "Part 7"),
    _r("SG-IDN-003", K, 2, "D", "Equivalence is a reversible, versioned mapping", ("SG-MERGE-001",), (), "Part 7"),
    _r("SG-IDN-004", K, 2, "D", "Similarity (lexical, embedding, text, model) never establishes identity", (), (), "Part 7"),
    _r("SG-IDN-005", K, 2, "D", "Concept resolution never merges referents; individuals resolve separately", (), (), "Part 7"),
    _r("SG-IDN-006", K, 2, "D", "Provisional concepts: confined to provisional records, TTL, caps, promotion mapping", (), (), "Part 7"),
    _r("SG-IDN-007", K, 2, "D", "The Registry Manager is the sole identity writer; recheck at commit; idempotent proposals", (), (), "Part 7"),
    _r("SG-IDN-008", K, 2, "D", "Equivalence requires a declared scope and is followed only within it", (), (), "Part 7"),
    _r("SG-IDN-009", K, 2, "D", "References keep their original ids; equivalence is resolved at read time", (), (), "Part 7"),
    # ---- generalization --------------------------------------------------------------------------------------------------
    _r("SG-GEN-001", K, 2, "L/R", "Generalization preserves common relations and adds no unsupported claims", ("SG-GENERALIZE-006",), (), "Part 9"),
    _r("SG-GEN-002", K, 2, "L", "No universal rule from observed examples alone", (), (), "Part 9"),
    _r("SG-GEN-003", K, 2, "D", "GEN is not an exceptionless universal", (), (), "Part 3 §3.7"),
    _r("SG-GEN-004", K, 2, "D", "Discriminative value: coverage cap and reuse floor", (), (), "Part 9"),
    _r("SG-GEN-005", K, 2, "D", "Counterexample states and coverage reporting", (), (), "Part 9"),
    _r("SG-GEN-006", K, 2, "D", "Gates before scores", (), (), "Part 9"),
    _r("SG-GEN-007", K, 2, "D", "Generalization budgets", (), (), "Part 9"),
    _r("SG-GEN-008", K, 2, "D", "Abstractions are additive; specifics keep their ids", (), (), "Part 9"),
    _r("SG-GEN-009", K, 2, "D", "Minimum independent occurrences, and the veto", (), (), "Part 9"),
    _r("SG-GEN-010", K, 2, "D", "Claim classification before validation", (), (), "Part 9"),
    # ---- learning ---------------------------------------------------------------------------------------------------------
    _r("SG-LRN-001", K, 2, "L", "Investigate an existing concept before proposing a new one for an unfamiliar word", (), (), "Part 7"),
    _r("SG-LRN-002", K, 2, "D", "Engines cannot advance candidates beyond STRUCTURED", (), (), "Part 9"),
    _r("SG-LRN-003", K, 2, "D", "Conservative new relation types", (), (), "Part 9"),
    _r("SG-LRN-004", K, 2, "D", "Prefer composition over new fundamental frames", (), (), "Part 9"),
    _r("SG-LRN-005", K, 2, "D", "Demand-driven grammar learning from aggregated FRAME_GAP", (), (), "Part 9"),
    _r("SG-LRN-006", K, 2, "D", "Atomic promotion bundles and dependency taint", (), (), "Part 9"),
    _r("SG-LRN-007", K, 2, "D", "Learning cycles with pre-registered metrics, stop conditions, canary", (), (), "Part 9"),
    _r("SG-LRN-008", K, 2, "D", "Error-driven changes are proposals tested on held-out data", (), (), "Part 9"),
    # ---- knowledge / inference ---------------------------------------------------------------------------------------------
    _r("SG-KNW-001", K, 2, "D", "Open world by default: missing is not incompatible", (), (), "Part 3 §3.13"),
    _r("SG-KNW-002", K, 2, "D", "Associative weights are not truth values and record their scoring model", (), (), "Part 2 §2.8"),
    _r("SG-KNW-003", K, 2, "D", "Opaque contexts block identity substitution", (), ("VC-G09",), "Part 3 §3.12"),
    _r("SG-KNW-004", K, 2, "D", "Only ESSENTIAL constraints inherit as exceptionless", (), (), "Part 4 §4.7"),
    _r("SG-KNW-005", K, 2, "L", "Concept multiple-inheritance conflict classes", (), (), "Part 4 §4.7"),
    _r("SG-KNW-006", K, 2, "D", "Constraint provenance classes; ASSUMED constraints never reject", (), (), "Part 9"),
    _r("SG-KNW-007", K, 2, "D", "Activation and usage heat never influence validity or promotion", (), (), "Part 10"),
    _r("SG-KNW-008", K, 2, "D", "Inference caches are derived, dependency-keyed and never authoritative", (), (), "Part 10"),
    _r("SG-KNW-009", K, 2, "D", "Reasoning defaults to the trusted view, outputs INFERRED, open-world, bounded", (), (), "Part 10"),
    _r("SG-KNW-010", K, 2, "L", "Class membership propagates up the subclass hierarchy", ("SUBCLASS_INHERITANCE_RULE",), (), "Part 5"),
    _r("SG-KNW-011", K, 2, "D", "Declared inverse relations are derived, not stored twice", (), (), "Part 5"),
    _r("SG-KNW-012", K, 2, "D/L", "Declared relation properties (transitive, asymmetric, ...) are enforced", (), ("VC-G01", "VC-G02"), "Part 5"),
    _r("SG-KNW-013", K, 2, "D", "Function inheritance is defeasible and applies to PURPOSE-mode functions only", (), (), "Part 10"),
    # ---- encoding ---------------------------------------------------------------------------------------------------------------
    _r("SG-ENC-001", C, 2, "D", "Exact round trip on canonical serialization", (), (), "Part 11"),
    _r("SG-ENC-002", C, 2, "D", "Encodings preserve the features required by the declared mode", (), (), "Part 11"),
    _r("SG-ENC-003", C, 2, "D", "Decoders pin versions, reject unknown critical structure, never guess", (), (), "Part 11"),
    _r("SG-ENC-004", C, 2, "D", "Structural sharing only for immutable definitions and pure templates", (), (), "Part 11"),
    _r("SG-ENC-005", C, 2, "D", "The optimizer cannot alter authoritative definitions", (), (), "Part 11"),
    _r("SG-ENC-006", C, 2, "D", "Templates only when the corrected inequality holds with margin", (), (), "Part 11"),
    _r("SG-ENC-007", C, 2, "D", "Decoder hardening against hostile input", (), (), "Part 11"),
    _r("SG-ENC-008", C, 2, "D", "Tier B is derived and rebuildable, never authoritative", (), (), "Part 11"),
    # ---- governance ----------------------------------------------------------------------------------------------------------------
    _r("SG-GOV-001", K, 2, "D", "Defining-constraint changes require versioning, impact analysis and review", ("SG-IDENTITY-002",), (), "Part 7"),
    _r("SG-GOV-002", K, 2, "D", "Rule changes go through rule change control", (), (), "Part 5 §5.12"),
    _r("SG-GOV-003", K, 2, "D", "Review independence and bias controls (automated panel)", (), (), "Part 6"),
    _r("SG-GOV-004", K, 2, "D", "Audit-based calibration of risk classes", (), (), "Part 6"),
    _r("SG-GOV-005", K, 2, "D", "A reviewer cannot commit or promote", (), (), "Part 6"),
    _r("SG-GOV-006", K, 2, "D", "Metacognition is deterministic and signal-based", (), (), "Part 6"),
    _r("SG-GOV-007", K, 2, "D", "Only the central controller commits workspace changes", (), (), "Part 10"),
    _r("SG-GOV-008", K, 2, "D", "Modules share ids and immutable snapshots; single writer per store", (), (), "Part 10"),
    _r("SG-GOV-009", K, 2, "D", "Every task has a budget and every queue is bounded", (), (), "Part 10"),
    _r("SG-GOV-010", K, 2, "D", "One shared model service; no module loads its own model copy", (), (), "Part 10"),
    # ---- security ---------------------------------------------------------------------------------------------------------------------
    _r("SG-SEC-001", K, 2, "D", "Source text is data, never instructions", (), (), "Part 6 §6.13"),
    _r("SG-SEC-002", K, 2, "D", "Least-privilege model gateway", (), (), "Part 6 §6.13"),
    _r("SG-SEC-003", K, 2, "D", "Quarantine tiers for new or flagged sources", (), (), "Part 6 §6.13"),
    _r("SG-SEC-004", K, 2, "H", "Injection tripwires raise risk; safety does not depend on detection", (), (), "Part 6 §6.13"),
    _r("SG-SEC-005", K, 2, "D", "Text normalization with offset mapping", (), (), "Part 6 §6.13"),
    _r("SG-SEC-006", K, 2, "D", "Per-source and per-task resource limits", (), (), "Part 6 §6.13"),
    _r("SG-SEC-007", K, 2, "D", "Poisoning limits per source cluster", (), (), "Part 6 §6.13"),
    _r("SG-SEC-008", K, 2, "D", "Egress control: local-only by default, PUBLIC material only", (), (), "Part 6 §6.13"),
    _r("SG-SEC-009", K, 2, "D", "Hash-chained audit log, hashed ruleset and validator releases", (), (), "Part 6 §6.13"),
    _r("SG-SEC-010", K, 2, "D/R", "Import hygiene: origin, licence and version recorded; imports enter as STRUCTURED", (), (), "Part 6 §6.13"),
)

# Legacy ids found in the source material -> canonical ids (Part 1 §1.7.2). Aliases cover readable names.
LEGACY_IDS: dict[str, str] = {
    "SG-001": "SG-INT-001", "SG-002": "SG-FRM-001", "SG-003": "SG-EVD-001", "SG-004": "SG-EVD-002", "SG-005": "SG-IDN-001",
    "SG-006": "SG-EVD-003", "SG-007": "SG-CON-001", "SG-TYPE-001": "SG-TYP-001", "SG-FRAME-002": "SG-FRM-002",
    "SG-INHERIT-001": "SG-FRM-002", "SG-EVIDENCE-003": "SG-EVD-001", "SG-CANON-004": "SG-CAN-001",
    "SG-IDENTITY-005": "SG-IDN-002", "SG-GENERALIZE-006": "SG-GEN-001", "SG-IDENTITY-001": "SG-KNW-001",
    "SG-IDENTITY-002": "SG-GOV-001", "SG-MERGE-001": "SG-IDN-003", "SG-LEARN-001": "SG-LRN-001",
    "SG-ROLE-001": "SG-FRM-001", "SG-FRAME-001": "SG-CON-002",
}
# NOTE: the legacy id SG-GEN-001 of Part 4 (no universal from examples) is SG-GEN-002 in the unified scheme.


class Rulebook:
    """The registry of rule definitions plus the knowledge of which checks are implemented."""

    def __init__(self, rules: Iterable[RuleDef] = RULES, implemented_checks: Iterable[str] = ()):
        self._rules: dict[str, RuleDef] = {}
        self._alias: dict[str, str] = {}
        for r in rules:
            if r.rule_id in self._rules:
                raise InvariantViolation(f"duplicate rule id {r.rule_id}", "SG-GOV-002")
            self._rules[r.rule_id] = r
        for r in self._rules.values():
            for a in r.aliases:
                if a in self._alias or a in self._rules:
                    raise InvariantViolation(f"alias {a!r} is not unique", "SG-GOV-002")
                self._alias[a] = r.rule_id
        self.implemented = frozenset(implemented_checks)

    # -- lookup ---------------------------------------------------------------------------
    def __contains__(self, rule_id: str) -> bool:
        return self.resolve(rule_id) is not None

    def resolve(self, name: str) -> str | None:
        """Canonical id for a canonical id, an alias or a legacy id; None if unknown."""
        if name in self._rules:
            return name
        if name in self._alias:
            return self._alias[name]
        legacy = LEGACY_IDS.get(name)
        return legacy if legacy in self._rules else None

    def get(self, name: str) -> RuleDef:
        rid = self.resolve(name)
        if rid is None:
            raise KeyError(f"unknown rule {name!r}")
        return self._rules[rid]

    def all(self) -> list[RuleDef]:
        return list(self._rules.values())

    def by_domain(self, domain: str) -> list[RuleDef]:
        return [r for r in self._rules.values() if r.domain == domain]

    def level1(self) -> list[RuleDef]:
        return [r for r in self._rules.values() if r.authority == 1]

    # -- status -----------------------------------------------------------------------------
    def is_active(self, rule_id: str) -> bool:
        r = self.get(rule_id)
        return bool(r.enforced_by) and all(c in self.implemented for c in r.enforced_by)

    def active(self) -> list[RuleDef]:
        return [r for r in self._rules.values() if self.is_active(r.rule_id)]

    def specified_only(self) -> list[RuleDef]:
        return [r for r in self._rules.values() if not self.is_active(r.rule_id)]

    def rules_for_check(self, check_id: str) -> list[RuleDef]:
        return [r for r in self._rules.values() if check_id in r.enforced_by]

    # -- integrity -----------------------------------------------------------------------------
    def content_hash(self) -> str:
        return sha256_hex(canonical_json([r.to_json() for r in self._rules.values()]))

    def consistency_issues(self, known_checks: Iterable[str] = ()) -> list[str]:
        """Static checks of the rulebook itself."""
        out: list[str] = []
        known = set(known_checks)
        for r in self._rules.values():
            for c in r.enforced_by:
                if known and c not in known:
                    out.append(f"{r.rule_id}: enforced_by unknown check {c}")
        for legacy, new in LEGACY_IDS.items():
            if new not in self._rules:
                out.append(f"legacy id {legacy} maps to unknown rule {new}")
        # a rule of level n may depend only on rules of level <= n: enforced here as 'level-1 rules are exactly SG-FND-*'
        for r in self._rules.values():
            if (r.authority == 1) != r.rule_id.startswith("SG-FND-"):
                out.append(f"{r.rule_id}: authority/domain mismatch")
        return out