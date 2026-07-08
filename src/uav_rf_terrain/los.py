"""Pure Python DSM-based line-of-sight analysis for Task 005.

This module analyzes LOS line height and DSM clearance over a TerrainProfile. It does
not compute Fresnel radius, Fresnel clearance, final scoring, color-map classes, map
layers, or real communication-quality metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .profile import TerrainProfile, TerrainProfileSample


class LineOfSightError(ValueError):
    """Raised when DSM LOS analysis inputs are invalid."""


@dataclass(frozen=True)
class LineOfSightSample:
    """DSM LOS analysis result for a single terrain profile sample."""

    sample_index: int
    terrain_sample: TerrainProfileSample
    ratio: float
    los_line_msl: float
    dsm_clearance_m: float
    is_blocked: bool


@dataclass(frozen=True)
class LineOfSightAnalysis:
    """DSM LOS analysis over an ordered terrain profile."""

    scenario_name: str
    launch_antenna_msl: float
    drone_flight_msl: float
    samples: tuple[LineOfSightSample, ...]
    dsm_los_score: float

    @property
    def sample_count(self) -> int:
        """Return the number of LOS samples."""

        return len(self.samples)

    @property
    def blocked_count(self) -> int:
        """Return the number of DSM-blocked LOS samples."""

        return sum(1 for sample in self.samples if sample.is_blocked)

    @property
    def is_clear(self) -> bool:
        """Return whether no DSM sample blocks the LOS line."""

        return self.blocked_count == 0

    @property
    def min_clearance_m(self) -> float:
        """Return the minimum DSM clearance along the profile."""

        _ensure_los_samples(self.samples)
        return min(sample.dsm_clearance_m for sample in self.samples)


def analyze_dsm_los(
    profile: TerrainProfile,
    *,
    launch_antenna_msl: float,
    drone_flight_msl: float,
) -> LineOfSightAnalysis:
    """Analyze DSM-based LOS clearance over a terrain profile.

    The LOS line is the straight MSL-height interpolation from launch antenna MSL to
    drone flight MSL. DSM blocks LOS when ``terrain_sample.dsm_msl >= los_line_msl``.
    The default component score follows the strict LOS cap rule: any blocked sample
    yields 0.0; otherwise the score is 100.0.
    """

    if not isfinite(launch_antenna_msl):
        raise LineOfSightError("launch_antenna_msl must be finite.")
    if not isfinite(drone_flight_msl):
        raise LineOfSightError("drone_flight_msl must be finite.")
    _ensure_profile_samples(profile.samples)

    los_samples: list[LineOfSightSample] = []
    for terrain_sample in profile.samples:
        ratio = _sample_ratio(terrain_sample)
        los_line_msl = launch_antenna_msl + ratio * (drone_flight_msl - launch_antenna_msl)
        dsm_clearance_m = los_line_msl - terrain_sample.dsm_msl
        los_samples.append(
            LineOfSightSample(
                sample_index=terrain_sample.sample_index,
                terrain_sample=terrain_sample,
                ratio=ratio,
                los_line_msl=los_line_msl,
                dsm_clearance_m=dsm_clearance_m,
                is_blocked=terrain_sample.dsm_msl >= los_line_msl,
            )
        )

    dsm_los_score = 0.0 if any(sample.is_blocked for sample in los_samples) else 100.0
    return LineOfSightAnalysis(
        scenario_name=profile.scenario_name,
        launch_antenna_msl=launch_antenna_msl,
        drone_flight_msl=drone_flight_msl,
        samples=tuple(los_samples),
        dsm_los_score=dsm_los_score,
    )


def _sample_ratio(sample: TerrainProfileSample) -> float:
    total_distance_m = sample.distance_from_start_m + sample.distance_to_end_m
    if total_distance_m <= 0:
        raise LineOfSightError("profile sample total distance must be positive.")
    ratio = sample.distance_from_start_m / total_distance_m
    if not isfinite(ratio) or ratio < 0.0 or ratio > 1.0:
        raise LineOfSightError("profile sample ratio must be finite and within [0, 1].")
    return ratio


def _ensure_profile_samples(samples: tuple[TerrainProfileSample, ...]) -> None:
    if not samples:
        raise LineOfSightError("terrain profile must contain at least one sample.")


def _ensure_los_samples(samples: tuple[LineOfSightSample, ...]) -> None:
    if not samples:
        raise LineOfSightError("LOS analysis must contain at least one sample.")
