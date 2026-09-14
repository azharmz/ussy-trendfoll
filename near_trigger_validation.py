"""Frozen one-shot validator for the NEAR_TRIGGER 0.60 ATR shadow candidate.

This module encodes the pre-registered forward-validation governance in
``docs/NEAR_TRIGGER_RESEARCH.md``. It does not tune thresholds and does not
change production alert or entry semantics.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping, Any


MIN_EPISODES = 150
MIN_UNIQUE_SYMBOLS = 75
MIN_BREAKOUTS_5D = 40
MIN_ONSET_RATE_3D = 0.20
MIN_ONSET_RATE_5D = 0.30
MIN_LIFT_3D = 1.50
MIN_LIFT_5D = 1.50

STATUS_ACCUMULATING = "FORWARD VALIDATION ACCUMULATING / NO VERDICT"
STATUS_PASS = "PRODUCTION-VALIDATED FOR ALERTABILITY"
STATUS_DEFERRED = "DEFERRED / NOT PRODUCTION-VALIDATED"


@dataclass(frozen=True)
class ValidationVerdict:
    status: str
    evidence_ready: bool
    primary_pass: bool | None
    shadow_episodes: int
    unique_symbols: int
    breakouts_5d: int
    shadow_onset_rate_3d: float
    shadow_onset_rate_5d: float
    control_onset_rate_3d: float
    control_onset_rate_5d: float
    lift_3d: float | None
    lift_5d: float | None
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _lift(shadow_rate: float, control_rate: float) -> float | None:
    if control_rate <= 0:
        return None if shadow_rate <= 0 else float("inf")
    return shadow_rate / control_rate


def evaluate_near_trigger_validation(metrics: Mapping[str, int]) -> ValidationVerdict:
    """Evaluate already-aggregated untouched forward-validation metrics.

    Required keys:
      shadow_episodes
      unique_symbols
      shadow_breakouts_3d
      shadow_breakouts_5d
      control_episodes
      control_breakouts_3d
      control_breakouts_5d

    The caller is responsible for constructing *independent shadow episodes*
    and complete forward windows according to the frozen protocol.
    """
    shadow_episodes = int(metrics.get("shadow_episodes", 0))
    unique_symbols = int(metrics.get("unique_symbols", 0))
    shadow_breakouts_3d = int(metrics.get("shadow_breakouts_3d", 0))
    shadow_breakouts_5d = int(metrics.get("shadow_breakouts_5d", 0))
    control_episodes = int(metrics.get("control_episodes", 0))
    control_breakouts_3d = int(metrics.get("control_breakouts_3d", 0))
    control_breakouts_5d = int(metrics.get("control_breakouts_5d", 0))

    shadow_rate_3d = _rate(shadow_breakouts_3d, shadow_episodes)
    shadow_rate_5d = _rate(shadow_breakouts_5d, shadow_episodes)
    control_rate_3d = _rate(control_breakouts_3d, control_episodes)
    control_rate_5d = _rate(control_breakouts_5d, control_episodes)
    lift_3d = _lift(shadow_rate_3d, control_rate_3d)
    lift_5d = _lift(shadow_rate_5d, control_rate_5d)

    evidence_failures = []
    if shadow_episodes < MIN_EPISODES:
        evidence_failures.append(f"shadow_episodes<{MIN_EPISODES}")
    if unique_symbols < MIN_UNIQUE_SYMBOLS:
        evidence_failures.append(f"unique_symbols<{MIN_UNIQUE_SYMBOLS}")
    if shadow_breakouts_5d < MIN_BREAKOUTS_5D:
        evidence_failures.append(f"shadow_breakouts_5d<{MIN_BREAKOUTS_5D}")
    if control_episodes <= 0:
        evidence_failures.append("control_episodes<=0")

    if evidence_failures:
        return ValidationVerdict(
            status=STATUS_ACCUMULATING,
            evidence_ready=False,
            primary_pass=None,
            shadow_episodes=shadow_episodes,
            unique_symbols=unique_symbols,
            breakouts_5d=shadow_breakouts_5d,
            shadow_onset_rate_3d=shadow_rate_3d,
            shadow_onset_rate_5d=shadow_rate_5d,
            control_onset_rate_3d=control_rate_3d,
            control_onset_rate_5d=control_rate_5d,
            lift_3d=lift_3d,
            lift_5d=lift_5d,
            failures=tuple(evidence_failures),
        )

    primary_failures = []
    if shadow_rate_3d < MIN_ONSET_RATE_3D:
        primary_failures.append(f"shadow_onset_rate_3d<{MIN_ONSET_RATE_3D:.2f}")
    if shadow_rate_5d < MIN_ONSET_RATE_5D:
        primary_failures.append(f"shadow_onset_rate_5d<{MIN_ONSET_RATE_5D:.2f}")
    if lift_3d is None or lift_3d < MIN_LIFT_3D:
        primary_failures.append(f"lift_3d<{MIN_LIFT_3D:.2f}")
    if lift_5d is None or lift_5d < MIN_LIFT_5D:
        primary_failures.append(f"lift_5d<{MIN_LIFT_5D:.2f}")

    primary_pass = not primary_failures
    return ValidationVerdict(
        status=STATUS_PASS if primary_pass else STATUS_DEFERRED,
        evidence_ready=True,
        primary_pass=primary_pass,
        shadow_episodes=shadow_episodes,
        unique_symbols=unique_symbols,
        breakouts_5d=shadow_breakouts_5d,
        shadow_onset_rate_3d=shadow_rate_3d,
        shadow_onset_rate_5d=shadow_rate_5d,
        control_onset_rate_3d=control_rate_3d,
        control_onset_rate_5d=control_rate_5d,
        lift_3d=lift_3d,
        lift_5d=lift_5d,
        failures=tuple(primary_failures),
    )
