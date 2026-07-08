"""Configuration constants for offline shielding-risk proxy scoring.

The default score model is intentionally limited to DSM-based LOS and DSM-based
Fresnel clearance proxy values. It does not require or infer RSSI, SINR, packet
loss, actual communication success, or real drone operation records.
"""

from __future__ import annotations

from dataclasses import dataclass

DSM_LOS_WEIGHT: float = 0.40
"""Weight for DSM-based line-of-sight score inside shielding stability score."""

DSM_FRESNEL_WEIGHT: float = 0.60
"""Weight for DSM-based Fresnel clearance score inside shielding stability score."""

SHIELDING_WEIGHT: float = 0.80
"""Weight for shielding stability score inside overall launch-area score."""

DISTANCE_WEIGHT: float = 0.20
"""Weight for distance score inside overall launch-area score."""

DEFAULT_LOS_CAP_MODE: str = "strict_zero"
"""Default rule: if DSM LOS score is 0, shielding stability score is forced to 0."""

DEFAULT_OUTPUT_MODE: str = "color_launch_area_map"
"""Default product output: color-class launch-area map layer, not a Top-N point list."""

PROHIBITED_REQUIRED_LINK_METRICS: tuple[str, ...] = ("rssi", "sinr", "packet_loss")
"""Metrics that must not be required in MVP input schemas without actual link data."""


@dataclass(frozen=True)
class ScoreWeights:
    """Baseline score weights for offline terrain/surface-obstacle risk proxy scoring.

    All score components are interpreted on a 0-100 scale where 100 is favorable
    and 0 is unfavorable. These weights are MVP heuristic defaults, not verified
    communication-quality coefficients.
    """

    dsm_los: float = DSM_LOS_WEIGHT
    dsm_fresnel: float = DSM_FRESNEL_WEIGHT
    shielding: float = SHIELDING_WEIGHT
    distance: float = DISTANCE_WEIGHT
    los_cap_mode: str = DEFAULT_LOS_CAP_MODE

    def shielding_component_sum(self) -> float:
        """Return the DSM LOS + DSM Fresnel weight sum."""

        return self.dsm_los + self.dsm_fresnel

    def overall_component_sum(self) -> float:
        """Return the shielding + distance weight sum."""

        return self.shielding + self.distance

    def validate(self) -> None:
        """Validate that baseline weights are normalized.

        Raises:
            ValueError: If the shielding or overall component weights do not sum to 1.0.
        """

        tolerance = 1e-9
        if abs(self.shielding_component_sum() - 1.0) > tolerance:
            raise ValueError("DSM LOS and DSM Fresnel weights must sum to 1.0.")
        if abs(self.overall_component_sum() - 1.0) > tolerance:
            raise ValueError("Shielding and distance weights must sum to 1.0.")
        if self.los_cap_mode not in {"strict_zero", "soft_cap"}:
            raise ValueError("los_cap_mode must be either 'strict_zero' or 'soft_cap'.")


DEFAULT_SCORE_WEIGHTS = ScoreWeights()
DEFAULT_SCORE_WEIGHTS.validate()
