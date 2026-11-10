"""Autonomy policy — the replacement for every human decision in the spec.

With no human in the loop, each action the specification routed to a reviewer
gets exactly one of four modes:

  AUTOMATIC    deterministic gates only (low risk).
  GATED        activation requires an *Automated Verification Panel* (AVP)
               quorum of independent verifier classes, a canary period and an
               automatic-rollback plan. Any hard-failing verifier VETOES.
  SHADOW_ONLY  the candidate is recorded and analysed but is never activated.
               (Used where the spec said "VERY_HIGH, never automatic" and no
               deterministic proof is possible.)
  FORBIDDEN    never possible at runtime (sealed code / install-time only).

The conservative direction is deliberate: removing the human makes the system
LESS willing to change itself, not more.

This module is SEALED (see seal.py): changing it at runtime is impossible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..config import Config
from ..core.values import RiskClass
from ..errors import PolicyDenied


class AutonomyMode(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    GATED = "GATED"
    SHADOW_ONLY = "SHADOW_ONLY"
    FORBIDDEN = "FORBIDDEN"


class VerifierClass(str, Enum):
    """Independence classes of automated verifiers. A quorum counts DISTINCT classes."""

    DETERMINISTIC_REPLAY = "DETERMINISTIC_REPLAY"  # re-execute deterministic steps, re-check spans/rules
    INDEPENDENT_METHOD = "INDEPENDENT_METHOD"  # a second, differently-built extraction/derivation path
    METAMORPHIC = "METAMORPHIC"  # paraphrase/voice transformations must preserve required structure
    COUNTEREXAMPLE = "COUNTEREXAMPLE"  # systematic search for violating cases
    REGRESSION_SUITE = "REGRESSION_SUITE"  # all existing rule/validator/contrastive tests still pass
    SYNTHETIC_HELDOUT = "SYNTHETIC_HELDOUT"  # programmatically generated held-out gold (known by construction)
    LOCAL_MODEL_SECOND_OPINION = "LOCAL_MODEL_SECOND_OPINION"  # optional, different family if available
    STATISTICAL_AUDIT = "STATISTICAL_AUDIT"  # error-bound from automated audit oracle (Wilson)


class ActionClass(str, Enum):
    ASSERTION_STORE_PROVISIONAL = "ASSERTION_STORE_PROVISIONAL"
    ASSERTION_PROMOTE_TRUSTED = "ASSERTION_PROMOTE_TRUSTED"
    LEXICAL_MAPPING_EXACT = "LEXICAL_MAPPING_EXACT"
    LEXICAL_MAPPING_LEARNED = "LEXICAL_MAPPING_LEARNED"
    CONCEPT_NEW = "CONCEPT_NEW"
    CONCEPT_SPECIALIZATION = "CONCEPT_SPECIALIZATION"
    CONCEPT_RELATED = "CONCEPT_RELATED"
    CONCEPT_GENERALIZATION = "CONCEPT_GENERALIZATION"
    EQUIVALENCE_ESTABLISHED = "EQUIVALENCE_ESTABLISHED"
    EQUIVALENCE_OTHER = "EQUIVALENCE_OTHER"
    PHYSICAL_MERGE = "PHYSICAL_MERGE"
    FRAME_DOMAIN = "FRAME_DOMAIN"
    FRAME_SPECIALIZATION = "FRAME_SPECIALIZATION"
    FRAME_COMPOSITION = "FRAME_COMPOSITION"
    FRAME_FUNDAMENTAL = "FRAME_FUNDAMENTAL"
    RELATION_TYPE_NEW = "RELATION_TYPE_NEW"
    VALENCE_PATTERN = "VALENCE_PATTERN"
    CONSTRUCTION_PATTERN_ACTIVATE = "CONSTRUCTION_PATTERN_ACTIVATE"
    CANON_RULE = "CANON_RULE"
    INTERP_RULE = "INTERP_RULE"
    FIGURATIVE_MAPPING = "FIGURATIVE_MAPPING"
    ANALOGY_RECORD = "ANALOGY_RECORD"
    UNIVERSAL_CLAIM = "UNIVERSAL_CLAIM"
    TYPICAL_CLAIM = "TYPICAL_CLAIM"
    FOUNDATIONAL_RULE_CHANGE = "FOUNDATIONAL_RULE_CHANGE"
    VALIDATOR_CHANGE = "VALIDATOR_CHANGE"
    FN_PRIMITIVE_CHANGE = "FN_PRIMITIVE_CHANGE"
    TRUST_TIER_TO_STANDARD = "TRUST_TIER_TO_STANDARD"
    TRUST_TIER_TO_TRUSTED = "TRUST_TIER_TO_TRUSTED"
    TRUST_TIER_LOWER = "TRUST_TIER_LOWER"
    ROLLBACK = "ROLLBACK"
    ISSUE_FINDING = "ISSUE_FINDING"  # analysis result; may only RAISE scrutiny (see IssueEffect)


@dataclass(frozen=True)
class GateRequirement:
    action: ActionClass
    mode: AutonomyMode
    risk: RiskClass
    required_verifiers: frozenset[VerifierClass]
    min_verifier_classes: int
    needs_canary: bool
    needs_rollback_plan: bool
    min_independent_origins: int
    spec_ref: str
    rationale: str = ""


_V = VerifierClass
_M = AutonomyMode
_R = RiskClass


def _req(action, mode, risk, verifiers=(), n=0, canary=False, rollback=False, origins=0, spec="", why=""):
    return GateRequirement(action, mode, risk, frozenset(verifiers), n, canary, rollback, origins, spec, why)


_RULE_VERIFIERS = (_V.DETERMINISTIC_REPLAY, _V.REGRESSION_SUITE, _V.SYNTHETIC_HELDOUT)
_CONCEPT_VERIFIERS = (_V.DETERMINISTIC_REPLAY, _V.INDEPENDENT_METHOD)

_TABLE: dict[ActionClass, GateRequirement] = {
    r.action: r
    for r in (
        _req(ActionClass.ASSERTION_STORE_PROVISIONAL, _M.AUTOMATIC, _R.LOW, spec="Part 6 §6.4",
             why="storing a validated, span-supported claim as SOURCE_ASSERTED changes no knowledge"),
        _req(ActionClass.ASSERTION_PROMOTE_TRUSTED, _M.GATED, _R.MEDIUM,
             (_V.DETERMINISTIC_REPLAY, _V.INDEPENDENT_METHOD), 3, False, True, 2, "Part 6 §6.6",
             why="VERIFIED needs an evidence policy met by independent origins; never by repetition"),
        _req(ActionClass.LEXICAL_MAPPING_EXACT, _M.AUTOMATIC, _R.LOW, spec="Part 9 §9.4",
             why="EXACT alignment of a vetted resource entry to an existing concept with a COMPLETE definition"),
        _req(ActionClass.LEXICAL_MAPPING_LEARNED, _M.GATED, _R.MEDIUM, _CONCEPT_VERIFIERS, 3, True, True, 2,
             "Part 9 §9.4"),
        _req(ActionClass.CONCEPT_NEW, _M.GATED, _R.HIGH, _CONCEPT_VERIFIERS, 3, True, True, 2, "Part 7 §7.9"),
        _req(ActionClass.CONCEPT_SPECIALIZATION, _M.GATED, _R.HIGH, _CONCEPT_VERIFIERS, 3, True, True, 2,
             "Part 7 §7.2.3"),
        _req(ActionClass.CONCEPT_RELATED, _M.GATED, _R.MEDIUM, _CONCEPT_VERIFIERS, 3, True, True, 2, "Part 7 §7.2.3"),
        _req(ActionClass.CONCEPT_GENERALIZATION, _M.SHADOW_ONLY, _R.VERY_HIGH, spec="Part 7 §7.2.3",
             why="restructures existing concepts; no deterministic proof available without a human"),
        _req(ActionClass.EQUIVALENCE_ESTABLISHED, _M.GATED, _R.VERY_HIGH,
             (_V.DETERMINISTIC_REPLAY, _V.COUNTEREXAMPLE, _V.REGRESSION_SUITE), 4, True, True, 0, "Part 7 §7.8",
             why="only grade ESTABLISHED: both definitions COMPLETE with definitional provenance and mutual entailment; "
                 "applied at read time so it is exactly reversible (SG-IDN-009)"),
        _req(ActionClass.EQUIVALENCE_OTHER, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 7 §7.2.2",
             why="SUPPORTED/CANDIDATE grades only yield lexical reuse or RELATED/SUBSUMED relations"),
        _req(ActionClass.PHYSICAL_MERGE, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 7 §7.8",
             why="records are never merged or deleted (SG-IDN-003)"),
        _req(ActionClass.FRAME_DOMAIN, _M.GATED, _R.HIGH, _RULE_VERIFIERS + (_V.COUNTEREXAMPLE,), 4, True, True, 3,
             "Part 9 §9.3.2"),
        _req(ActionClass.FRAME_SPECIALIZATION, _M.GATED, _R.HIGH, _RULE_VERIFIERS + (_V.COUNTEREXAMPLE,), 4, True,
             True, 3, "Part 9 §9.7.2"),
        _req(ActionClass.FRAME_COMPOSITION, _M.GATED, _R.HIGH, _RULE_VERIFIERS + (_V.COUNTEREXAMPLE,), 4, True, True,
             3, "Part 9 §9.7.2"),
        _req(ActionClass.FRAME_FUNDAMENTAL, _M.SHADOW_ONLY, _R.VERY_HIGH, spec="Part 9 §9.7.2 rung 4",
             why="a new layer-1/2 frame cannot be proven safe without human judgement; recorded as FRAME_GAP demand"),
        _req(ActionClass.RELATION_TYPE_NEW, _M.GATED, _R.HIGH, _RULE_VERIFIERS + (_V.COUNTEREXAMPLE,), 4, True, True,
             3, "Part 9 §9.6.3"),
        _req(ActionClass.VALENCE_PATTERN, _M.GATED, _R.MEDIUM, _RULE_VERIFIERS, 3, True, True, 0, "Part 8 §8.5.2"),
        _req(ActionClass.CONSTRUCTION_PATTERN_ACTIVATE, _M.GATED, _R.MEDIUM,
             _RULE_VERIFIERS + (_V.STATISTICAL_AUDIT,), 4, True, True, 0, "Part 8 §8.12"),
        _req(ActionClass.CANON_RULE, _M.GATED, _R.HIGH, _RULE_VERIFIERS + (_V.METAMORPHIC,), 4, True, True, 0,
             "Part 3 §3.17"),
        _req(ActionClass.INTERP_RULE, _M.GATED, _R.HIGH, _RULE_VERIFIERS + (_V.METAMORPHIC,), 4, True, True, 0,
             "Part 5 §5.12"),
        _req(ActionClass.FIGURATIVE_MAPPING, _M.GATED, _R.MEDIUM, _RULE_VERIFIERS, 3, True, True, 0, "Part 3 §3.15"),
        _req(ActionClass.ANALOGY_RECORD, _M.GATED, _R.MEDIUM, (_V.DETERMINISTIC_REPLAY, _V.COUNTEREXAMPLE), 3, False,
             True, 0, "Part 9 §9.12"),
        _req(ActionClass.UNIVERSAL_CLAIM, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 9 §9.9.2",
             why="SG-GEN-002 strengthened: with no human to confirm, only TYPICAL / GENERIC / STATISTICAL claims"),
        _req(ActionClass.TYPICAL_CLAIM, _M.GATED, _R.HIGH, (_V.DETERMINISTIC_REPLAY, _V.COUNTEREXAMPLE), 3, True, True,
             3, "Part 9 §9.9.2"),
        _req(ActionClass.FOUNDATIONAL_RULE_CHANGE, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 5 §5.5",
             why="sealed at install; only a new package release changes it (SG-FND-005)"),
        _req(ActionClass.VALIDATOR_CHANGE, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 5 §5.12", why="sealed at install"),
        _req(ActionClass.FN_PRIMITIVE_CHANGE, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 4 §4.8.2 SG-FRM-009",
             why="FN primitives are part of the sealed Foundation Package"),
        _req(ActionClass.TRUST_TIER_TO_STANDARD, _M.GATED, _R.MEDIUM, (_V.STATISTICAL_AUDIT, _V.DETERMINISTIC_REPLAY),
             2, False, True, 0, "Part 6 §6.5.2", why="automatic probation: N clean units from this source"),
        _req(ActionClass.TRUST_TIER_TO_TRUSTED, _M.FORBIDDEN, _R.VERY_HIGH, spec="Part 6 §6.5.2",
             why="the TRUSTED list is install-time configuration, never inferred"),
        _req(ActionClass.TRUST_TIER_LOWER, _M.AUTOMATIC, _R.LOW, spec="Part 6 §6.5.2",
             why="lowering trust only increases scrutiny"),
        _req(ActionClass.ROLLBACK, _M.AUTOMATIC, _R.LOW, spec="Part 9 §9.3.5",
             why="restoring the previous active version is always the safe direction"),
        _req(ActionClass.ISSUE_FINDING, _M.AUTOMATIC, _R.LOW, spec="Autonomy",
             why="analysis output; effects restricted to raising scrutiny (IssueEffect)"),
    )
}


class AutonomyPolicy:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def requirement(self, action: ActionClass) -> GateRequirement:
        base = _TABLE[action]
        if base.mode is AutonomyMode.GATED:
            floor = int(self.config.get("avp_min_verifier_classes_gated"))
            if base.min_verifier_classes < floor:
                return GateRequirement(base.action, base.mode, base.risk, base.required_verifiers, floor,
                                       base.needs_canary, base.needs_rollback_plan, base.min_independent_origins,
                                       base.spec_ref, base.rationale)
        return base

    def mode(self, action: ActionClass) -> AutonomyMode:
        return _TABLE[action].mode

    def may_activate(self, action: ActionClass) -> bool:
        return _TABLE[action].mode in (AutonomyMode.AUTOMATIC, AutonomyMode.GATED)

    def assert_may_activate(self, action: ActionClass) -> GateRequirement:
        req = self.requirement(action)
        if req.mode is AutonomyMode.FORBIDDEN:
            raise PolicyDenied(f"{action.value} is FORBIDDEN at runtime: {req.rationale}", "SG-FND-005")
        if req.mode is AutonomyMode.SHADOW_ONLY:
            raise PolicyDenied(f"{action.value} is SHADOW_ONLY: recorded but never activated ({req.rationale})",
                               "SG-FND-004")
        return req

    @staticmethod
    def all_actions() -> list[ActionClass]:
        return list(ActionClass)

    @staticmethod
    def table() -> list[GateRequirement]:
        return [_TABLE[a] for a in ActionClass]


# ---------------------------------------------------------------------------
# Big (remote) model policy: it may only set GENERAL RULES or analyse GENERAL ISSUES
# ---------------------------------------------------------------------------
class BigModelTask(str, Enum):
    GENERAL_RULE_PROPOSAL = "GENERAL_RULE_PROPOSAL"
    GENERAL_ISSUE_ANALYSIS = "GENERAL_ISSUE_ANALYSIS"


BIG_MODEL_PRODUCES: dict[BigModelTask, frozenset[ActionClass]] = {
    BigModelTask.GENERAL_RULE_PROPOSAL: frozenset(
        {ActionClass.INTERP_RULE, ActionClass.CANON_RULE, ActionClass.VALENCE_PATTERN, ActionClass.FIGURATIVE_MAPPING}
    ),
    BigModelTask.GENERAL_ISSUE_ANALYSIS: frozenset({ActionClass.ISSUE_FINDING}),
}


def big_model_may_produce(task: BigModelTask, action: ActionClass) -> bool:
    """A remote model can never produce concepts, assertions, mappings, trust or
    anything about an individual sentence: only general rules and issue findings."""
    return action in BIG_MODEL_PRODUCES.get(task, frozenset())


class IssueEffect(str, Enum):
    """What an ISSUE_FINDING may cause. Every allowed effect RAISES scrutiny or
    schedules work; none can relax any check."""

    RAISE_RISK_FLOOR = "RAISE_RISK_FLOOR"
    PRIORITISE_REPROCESSING = "PRIORITISE_REPROCESSING"
    REQUEST_RULE_PROPOSAL = "REQUEST_RULE_PROPOSAL"
    INCREASE_AUDIT_RATE = "INCREASE_AUDIT_RATE"
    # relaxing effects (never allowed; listed so they can be rejected explicitly)
    LOWER_RISK = "LOWER_RISK"
    SKIP_VALIDATION = "SKIP_VALIDATION"
    RAISE_TRUST = "RAISE_TRUST"
    DISABLE_CHECK = "DISABLE_CHECK"


RELAXING_EFFECTS = frozenset(
    {IssueEffect.LOWER_RISK, IssueEffect.SKIP_VALIDATION, IssueEffect.RAISE_TRUST, IssueEffect.DISABLE_CHECK}
)


def issue_effect_is_safe(effect: IssueEffect) -> bool:
    return effect not in RELAXING_EFFECTS
