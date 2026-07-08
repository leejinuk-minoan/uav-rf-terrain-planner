"""Pure Python scoring integration for Task 007.

This module integrates DSM LOS, DSM Fresnel, and operating-radius distance reserve
components into candidate-level scores. It does not create color-map classes, ranked
Top-N launch-site output, real DEM/DSM loading, GIS integration, UI, or real link
quality validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .config import DISTANCE_WEIGHT, DSM_FRESNEL_WEIGHT, DSM_LOS_WEIGHT, SHIELDING_WEIGHT

_SCORE_TOLERANCE: float = 1e-9


class ScoringError(ValueError):
    """Raised when candidate score inputs or weights are invalid."""


@dataclass(frozen=True)
class ScoreComponentWeights:
    """Normalized component weights for Task 007 scoring integration.

    The default values are imported from ``config.py`` so the Task 007 scoring module
    stays aligned with the baseline project configuration.
    """

    shielding_weight: float = SHIELDING_WEIGHT
    distance_weight: float = DISTANCE_WEIGHT
    dsm_los_weight: float = DSM_LOS_WEIGHT
    dsm_fresnel_weight: float = DSM_FRESNEL_WEIGHT

    def validate(self) -> None:
        """Validate that all weights are finite, non-negative, and normalized."""

        for field_name, value in (
            ("shielding_weight", self.shielding_weight),
            ("distance_weight", self.distance_weight),
            ("dsm_los_weight", self.dsm_los_weight),
            ("dsm_fresnel_weight", self.dsm_fresnel_weight),
        ):
            if not isfinite(value):
                raise ScoringError(f"{field_name} must be finite.")
            if value < 0.0:
                raise ScoringError(f"{field_name} must be non-negative.")

        if abs((self.shielding_weight + self.distance_weight) - 1.0) > _SCORE_TOLERANCE:
            raise ScoringError("shielding_weight and distance_weight must sum to 1.0.")
        if abs((self.dsm_los_weight + self.dsm_fresnel_weight) - 1.0) > _SCORE_TOLERANCE:
            raise ScoringError("dsm_los_weight and dsm_fresnel_weight must sum to 1.0.")


@dataclass(frozen=True)
class CandidateScore:
    """Candidate launch-cell score result.

    This dataclass is score-only. It intentionally has no color classification, Top-N
    ranking field, or real-link metric field such as RSSI, SINR, or packet loss.
    """

    distance_3d_m: float
    operating_radius_m: float
    dsm_los_score: float
    dsm_fresnel_score: float
    distance_score: float
    shielding_stability_score: float
    overall_score: float


def clamp_score(value: float) -> float:
    """Clamp a finite score-like value to the [0, 100] range."""

    if not isfinite(value):
        raise ScoringError("score value must be finite.")
    return max(0.0, min(100.0, value))


def compute_distance_score(
    *,
    distance_3d_m: float,
    operating_radius_m: float,
) -> float:
    """Compute operating-radius distance reserve score.

    This is a distance reserve proxy, not an RF link-quality measurement.
    """

    if not isfinite(distance_3d_m):
        raise ScoringError("distance_3d_m must be finite.")
    if not isfinite(operating_radius_m):
        raise ScoringError("operating_radius_m must be finite.")
    if distance_3d_m < 0.0:
        raise ScoringError("distance_3d_m must be non-negative.")
    if operating_radius_m <= 0.0:
        raise ScoringError("operating_radius_m must be positive.")

    raw_distance_score = 100.0 * (1.0 - distance_3d_m / operating_radius_m)
    return clamp_score(raw_distance_score)


def compute_shielding_stability_score(
    *,
    dsm_los_score: float,
    dsm_fresnel_score: float,
    weights: ScoreComponentWeights = ScoreComponentWeights(),
) -> float:
    """Compute DSM LOS/Fresnel shielding stability score with strict LOS cap."""

    weights.validate()
    _validate_component_score("dsm_los_score", dsm_los_score)
    _validate_component_score("dsm_fresnel_score", dsm_fresnel_score)

    if dsm_los_score == 0.0:
        return 0.0

    raw_shielding_score = (
        dsm_los_score * weights.dsm_los_weight
        + dsm_fresnel_score * weights.dsm_fresnel_weight
    )
    return clamp_score(raw_shielding_score)


def compute_overall_score(
    *,
    shielding_stability_score: float,
    distance_score: float,
    weights: ScoreComponentWeights = ScoreComponentWeights(),
) -> float:
    """Compute final candidate score from shielding and distance components."""

    weights.validate()
    _validate_component_score("shielding_stability_score", shielding_stability_score)
    _validate_component_score("distance_score", distance_score)

    raw_overall_score = (
        shielding_stability_score * weights.shielding_weight
        + distance_score * weights.distance_weight
    )
    return clamp_score(raw_overall_score)


def compute_candidate_score(
    *,
    distance_3d_m: float,
    operating_radius_m: float,
    dsm_los_score: float,
    dsm_fresnel_score: float,
    weights: ScoreComponentWeights = ScoreComponentWeights(),
) -> CandidateScore:
    """Compute all score components for one candidate launch cell."""

    weights.validate()
    distance_score = compute_distance_score(
        distance_3d_m=distance_3d_m,
        operating_radius_m=operating_radius_m,
    )
    shielding_stability_score = compute_shielding_stability_score(
        dsm_los_score=dsm_los_score,
        dsm_fresnel_score=dsm_fresnel_score,
        weights=weights,
    )
    overall_score = compute_overall_score(
        shielding_stability_score=shielding_stability_score,
        distance_score=distance_score,
        weights=weights,
    )
    return CandidateScore(
        distance_3d_m=distance_3d_m,
        operating_radius_m=operating_radius_m,
        dsm_los_score=dsm_los_score,
        dsm_fresnel_score=dsm_fresnel_score,
        distance_score=distance_score,
        shielding_stability_score=shielding_stability_score,
        overall_score=overall_score,
    )


def _validate_component_score(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise ScoringError(f"{field_name} must be finite.")
    if value < 0.0 or value > 100.0:
        raise ScoringError(f"{field_name} must be within [0, 100].")
