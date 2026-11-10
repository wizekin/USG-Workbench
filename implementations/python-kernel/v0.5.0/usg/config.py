"""Constants register (spec Part 12 §12.10) with *automatic* calibration.

Every numeric choice the specification marked [Provisional] lives here with:
  * its initial (conservative) value,
  * hard bounds inside which automatic calibration may move it,
  * a calibration status.

There is no human to tune these, so calibration is performed by code
(`Config.calibrate`) from measured run results, and is only accepted inside
the declared bounds. Anything not yet calibrated keeps its conservative
default (higher scrutiny, tighter budgets), as the spec requires.
"""

from __future__ import annotations

import os
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .errors import InvariantViolation


class Calibration(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    CALIBRATED = "CALIBRATED"
    PINNED = "PINNED"  # never auto-calibrated (safety-relevant)


@dataclass(frozen=True)
class ConstantSpec:
    name: str
    value: Any
    defined_in: str
    lo: float | None = None
    hi: float | None = None
    pinned: bool = False
    note: str = ""


def _c(name, value, defined_in, lo=None, hi=None, pinned=False, note=""):
    return ConstantSpec(name, value, defined_in, lo, hi, pinned, note)


# ---------------------------------------------------------------------------
# The register. Names are stable identifiers used across the code base.
# ---------------------------------------------------------------------------
REGISTER: tuple[ConstantSpec, ...] = (
    # --- grammar / interpretation ---
    _c("alt_max_per_group", 4, "Part 3 §3.14", 2, 8),
    _c("max_retries_per_unit", 2, "Part 5 §5.7", 0, 5),
    _c("model_calls_per_sentence", 3, "Part 8 §8.11.7", 1, 8),
    _c("workspace_capacity", 200, "Part 10 §10.4.3", 50, 2000),
    _c("max_nesting_depth", 12, "Part 5 VC-S16", 4, 32, pinned=True),
    _c("max_source_chars", 200_000, "Part 6 SEC-006", 1_000, 5_000_000, pinned=True),
    _c("max_unit_chars", 2_000, "Part 6 SEC-006", 100, 20_000, pinned=True),
    _c("max_units_per_source", 2000, "Part 6 SEC-006", 10, 10000, pinned=True),
    # --- evidence, risk, audit (automated replacement of human audit) ---
    _c("pattern_min_independent_origins", 3, "Part 6 §6.12.2", 2, 10),
    _c("audit_sample_rate_new_category", 0.10, "Part 6 §6.10.3", 0.02, 0.5),
    _c("wilson_z", 1.645, "Part 6 §6.10.3", 1.0, 3.0, pinned=True),
    _c("tau_low", 0.10, "Part 6 §6.10.3", 0.01, 0.30),
    _c("tau_medium", 0.05, "Part 6 §6.10.3", 0.005, 0.20),
    _c("tau_high", 0.02, "Part 6 §6.10.3", 0.001, 0.10),
    _c("near_duplicate_threshold", 0.85, "Part 6 §6.5.3", 0.5, 0.99),
    _c("ece_threshold", 0.10, "Part 6 §6.10.4", 0.02, 0.25),
    _c("ece_min_samples_per_bin", 30, "Part 6 §6.10.4", 10, 500),
    # --- identity ---
    _c("provisional_concept_ttl_days", 30, "Part 7 §7.9.2", 1, 365),
    # --- learning / generalization ---
    _c("pattern_graduation_min_audited", 30, "Part 8 §8.12", 10, 1000),
    _c("pattern_graduation_max_error_ub", 0.05, "Part 8 §8.12", 0.005, 0.2),
    _c("min_origins_grammar_candidate", 3, "Part 9 §9.6.3", 2, 10),
    _c("reuse_floor_m", 3, "Part 9 §9.9.5", 2, 20),
    _c("coverage_cap", 0.25, "Part 9 §9.9.5", 0.05, 0.6),
    _c("match_max_nodes", 12, "Part 9 §9.11", 4, 24),
    _c("match_max_steps", 20_000, "Part 9 §9.11", 1_000, 1_000_000),
    _c("match_max_depth", 4, "Part 9 §9.11", 2, 8),
    _c("gen_max_candidates", 100, "Part 9 §9.11", 10, 1000),
    _c("max_new_frames_per_cycle", 5, "Part 9 §9.11", 0, 20),
    _c("max_new_rel_types_per_release", 1, "Part 9 §9.11", 0, 5),
    _c("consequence_chain_depth", 3, "Part 9 §9.19.1", 1, 5),
    _c("canary_units", 200, "Part 9 §9.15.2", 20, 5000),
    # --- cognitive architecture / resources ---
    _c("usable_ram_fraction", 0.8, "Part 10 §10.13.2", 0.5, 0.9, pinned=True),
    _c("activation_alpha", 0.5, "Part 10 §10.7.2", 0.1, 0.9),
    _c("activation_theta", 0.15, "Part 10 §10.7.2", 0.01, 0.5),
    _c("activation_depth", 2, "Part 10 §10.7.2", 1, 5),
    _c("activation_top_k", 50, "Part 10 §10.7.2", 5, 500),
    _c("activation_fan_out_cap", 20, "Part 10 §10.7.2", 3, 200),
    _c("heat_half_life_days", 7.0, "Part 10 §10.7.4", 0.5, 90.0),
    _c("dead_letter_attempts", 3, "Part 10 §10.14", 1, 10),
    # --- encoding ---
    _c("tier1_boundary", 128, "Part 11 §11.5.3", 16, 255),
    _c("size_tolerance_pct", 5.0, "Part 11 §11.12.2", 0.5, 25.0),
    _c("template_safety_margin", 1.5, "Part 11 §11.13.1", 1.0, 4.0),
    # --- benchmark scoring ---
    _c("cost_ratio_err_abs", 5.0, "Part 12 §12.6.5", 1.0, 50.0),
    # --- autonomy (replaces human review; see DESIGN.md) ---
    _c("avp_min_verifier_classes_gated", 3, "Autonomy", 2, 6, pinned=True),
    _c("avp_veto_enabled", True, "Autonomy", pinned=True),
    _c("canary_error_ub_max", 0.05, "Autonomy", 0.005, 0.2),
    _c("auto_rollback_on_regression", True, "Autonomy", pinned=True),
    _c("probation_clean_units", 50, "Autonomy", 10, 5000),
    _c("shadow_candidate_ttl_days", 60, "Autonomy", 1, 730),
    # --- big model (remote, free-plan) budgets: deliberately tiny ---
    _c("bm_enabled", False, "Autonomy", pinned=True),
    _c("bm_max_calls_per_day", 3, "Autonomy", 0, 50, pinned=True),
    _c("bm_max_calls_per_hour", 1, "Autonomy", 0, 10, pinned=True),
    _c("bm_max_tokens_per_day", 12_000, "Autonomy", 0, 200_000, pinned=True),
    _c("bm_max_input_tokens", 2_500, "Autonomy", 200, 20_000, pinned=True),
    _c("bm_max_output_tokens", 1_000, "Autonomy", 100, 8_000, pinned=True),
    _c("bm_min_interval_s", 1_800, "Autonomy", 0, 86_400, pinned=True),
    _c("bm_cooldown_base_s", 600, "Autonomy", 10, 86_400, pinned=True),
    _c("bm_cooldown_max_s", 86_400, "Autonomy", 60, 604_800, pinned=True),
    _c("bm_digest_dedup_s", 7 * 86_400, "Autonomy", 3_600, 90 * 86_400, pinned=True),
    _c("bm_min_issue_evidence", 20, "Autonomy", 5, 10_000),
    _c("bm_digest_max_items", 40, "Autonomy", 5, 200),
    _c("bm_stale_reservation_s", 900, "Autonomy", 60, 7_200, pinned=True),
)

_BY_NAME = {c.name: c for c in REGISTER}


@dataclass
class CalibrationEvent:
    name: str
    old: Any
    new: Any
    run_id: str
    evidence: str


class Config:
    """Runtime view of the constants register.

    * `get` returns the current value.
    * `calibrate` moves a value inside its bounds, recording an event.
      Pinned constants can never be calibrated (safety-relevant).
    * `override` is for *installation-time* configuration (e.g. enabling the
      remote model). It is not used by any runtime process.
    """

    def __init__(self, overrides: dict[str, Any] | None = None):
        self._values: dict[str, Any] = {c.name: c.value for c in REGISTER}
        self._status: dict[str, Calibration] = {
            c.name: (Calibration.PINNED if c.pinned else Calibration.UNCALIBRATED) for c in REGISTER
        }
        self.history: list[CalibrationEvent] = []
        for k, v in (overrides or {}).items():
            self.override(k, v)

    # -- access ------------------------------------------------------------
    def get(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError as e:
            raise KeyError(f"unknown constant {name!r}") from e

    __getitem__ = get

    def status(self, name: str) -> Calibration:
        return self._status[name]

    def spec(self, name: str) -> ConstantSpec:
        return _BY_NAME[name]

    # -- changes -----------------------------------------------------------
    def override(self, name: str, value: Any) -> None:
        """Install-time configuration. Bounds are still enforced."""
        spec = _BY_NAME.get(name)
        if spec is None:
            raise KeyError(f"unknown constant {name!r}")
        self._check_bounds(spec, value)
        self._values[name] = value

    def calibrate(self, name: str, value: Any, run_id: str, evidence: str = "") -> CalibrationEvent:
        spec = _BY_NAME.get(name)
        if spec is None:
            raise KeyError(f"unknown constant {name!r}")
        if spec.pinned:
            raise InvariantViolation(f"constant {name!r} is pinned and cannot be auto-calibrated", "CONFIG-PINNED")
        self._check_bounds(spec, value)
        old = self._values[name]
        self._values[name] = value
        self._status[name] = Calibration.CALIBRATED
        ev = CalibrationEvent(name, old, value, run_id, evidence)
        self.history.append(ev)
        return ev

    @staticmethod
    def _check_bounds(spec: ConstantSpec, value: Any) -> None:
        if isinstance(spec.value, bool):
            if not isinstance(value, bool):
                raise InvariantViolation(f"{spec.name} must be bool", "CONFIG-TYPE")
            return
        if isinstance(spec.value, (int, float)):
            if type(value) not in (int, float) or not math.isfinite(value):
                raise InvariantViolation(f"{spec.name} must be a finite number", "CONFIG-TYPE")
            if type(spec.value) is int and type(value) is not int:
                raise InvariantViolation(f"{spec.name} must be an integer", "CONFIG-TYPE")
        if spec.lo is not None and value < spec.lo:
            raise InvariantViolation(f"{spec.name}={value} below lower bound {spec.lo}", "CONFIG-BOUNDS")
        if spec.hi is not None and value > spec.hi:
            raise InvariantViolation(f"{spec.name}={value} above upper bound {spec.hi}", "CONFIG-BOUNDS")

    # -- reports -----------------------------------------------------------
    def uncalibrated(self) -> list[str]:
        return sorted(n for n, s in self._status.items() if s is Calibration.UNCALIBRATED)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._values)


# ---------------------------------------------------------------------------
# Backend configuration (models). Read from the environment at install time.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LocalModelConfig:
    """Local model (Ollama-compatible HTTP API). Disabled unless configured."""

    backend: str = "none"  # "none" | "ollama"
    base_url: str = "http://127.0.0.1:11434"
    model: str = ""
    timeout_s: float = 60.0
    seed: int = 7

    @staticmethod
    def from_env(env: dict[str, str] | None = None) -> "LocalModelConfig":
        e = env if env is not None else os.environ
        model = e.get("USG_LOCAL_MODEL", "")
        return LocalModelConfig(
            backend="ollama" if model else "none",
            base_url=e.get("USG_LOCAL_URL", "http://127.0.0.1:11434"),
            model=model,
            timeout_s=float(e.get("USG_LOCAL_TIMEOUT", "60")),
        )


@dataclass(frozen=True)
class BigModelConfig:
    """Remote 'big' model, OpenAI-compatible chat-completions endpoint.

    Disabled by default. Enabling it only *permits* calls; the ledger
    (usg.autonomy.ledger) still enforces the caps in the constants register.
    The API key is never stored: only the *name* of the environment variable
    that holds it.
    """

    enabled: bool = False
    base_url: str = ""
    model: str = ""
    api_key_env: str = "USG_BIG_API_KEY"
    timeout_s: float = 90.0

    @staticmethod
    def from_env(env: dict[str, str] | None = None) -> "BigModelConfig":
        e = env if env is not None else os.environ
        url = e.get("USG_BIG_URL", "")
        model = e.get("USG_BIG_MODEL", "")
        return BigModelConfig(
            enabled=bool(url and model and e.get("USG_BIG_ENABLED", "0") == "1"),
            base_url=url,
            model=model,
            api_key_env=e.get("USG_BIG_API_KEY_ENV", "USG_BIG_API_KEY"),
            timeout_s=float(e.get("USG_BIG_TIMEOUT", "90")),
        )


@dataclass(frozen=True)
class IngestConfig:
    """Install-time policy for sources supplied through the API."""

    default_trust_tier: str = "STANDARD"  # operator-supplied corpora; imports are QUARANTINE
    default_sensitivity: str = "INTERNAL"  # never sent to remote models unless PUBLIC
    default_language: str = "en"
