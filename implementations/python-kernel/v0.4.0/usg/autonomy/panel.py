"""Independent verifier classes, hard vetoes, and conservative risk calibration."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from .policy import AutonomyMode, AutonomyPolicy, VerifierClass


def wilson_upper(errors: int, n: int, z: float = 1.645) -> float:
    if n < 0 or errors < 0 or errors > n:
        raise ValueError("invalid audit counts")
    if not n:
        return 1.0
    p = errors / n
    return (p + z*z/(2*n) + z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / (1+z*z/n)


@dataclass(frozen=True)
class Verdict:
    verifier: VerifierClass
    passed: bool
    evidence_hash: str
    detail: str = ""
    hard_failure: bool = False


@dataclass(frozen=True)
class PanelReport:
    approved: bool
    reason: str
    verdicts: tuple[Verdict, ...]

    def to_json(self):
        return asdict(self)


class AutomatedPanel:
    """Verifiers are registered code callbacks, never votes supplied by a model."""
    def __init__(self, verifiers=None, policy=None):
        self.verifiers = dict(verifiers or {})
        self.policy = policy or AutonomyPolicy()

    def evaluate(self, action, candidate, *, origins=0, rollback_plan=False, canary_complete=False):
        req = self.policy.requirement(action)
        if req.mode in {AutonomyMode.FORBIDDEN, AutonomyMode.SHADOW_ONLY}:
            return PanelReport(False, req.mode.value, ())
        verdicts = []
        for cls, fn in self.verifiers.items():
            try:
                v = fn(candidate)
                if not isinstance(v, Verdict) or v.verifier != cls or not v.evidence_hash:
                    raise ValueError("invalid verifier result")
            except Exception as exc:
                v = Verdict(cls, False, "unavailable", type(exc).__name__, True)
            verdicts.append(v)
        if any(v.hard_failure or not v.passed for v in verdicts):
            return PanelReport(False, "VETO", tuple(verdicts))
        passed = {v.verifier for v in verdicts if v.passed}
        if not req.required_verifiers <= passed or len(passed) < req.min_verifier_classes:
            return PanelReport(False, "INSUFFICIENT_INDEPENDENT_CHECKS", tuple(verdicts))
        if origins < req.min_independent_origins:
            return PanelReport(False, "INSUFFICIENT_ORIGINS", tuple(verdicts))
        if req.needs_rollback_plan and not rollback_plan:
            return PanelReport(False, "ROLLBACK_REQUIRED", tuple(verdicts))
        if req.needs_canary and not canary_complete:
            return PanelReport(False, "CANARY_REQUIRED", tuple(verdicts))
        return PanelReport(True, "APPROVED", tuple(verdicts))
