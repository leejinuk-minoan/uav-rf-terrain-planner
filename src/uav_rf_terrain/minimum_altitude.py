"""Minimum required altitude scaffold for synthetic terrain profiles.

Task 015 estimates a minimum endpoint MSL that satisfies an offline DSM-based
LOS/Fresnel clearance proxy over an existing ``TerrainProfile``. It does not load
real DEM/DSM files, render maps, control vehicles, or validate field link behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .fresnel import first_fresnel_radius_m, wavelength_m
from .profile import TerrainProfile, TerrainProfileSample

DEFAULT_REQUIRED_FRESNEL_CLEARANCE_RATIO: float = 0.6
"""Default MVP proxy threshold for first Fresnel clearance, not a field guarantee."""

DEFAULT_ALTITUDE_EPSILON: float = 1e-9
"""Default epsilon for skipping the launch endpoint in endpoint-altitude inversion."""


class MinimumAltitudeError(ValueError):
    """Raised when minimum altitude calculation inputs are invalid."""


@dataclass(frozen=True)
class MinimumAltitudeConfig:
    """Configuration for the minimum required altitude proxy calculation.

    ``required_fresnel_clearance_ratio`` is an MVP clearance proxy threshold for
    synthetic profile analysis. It is not a real link-success condition.
    """

    frequency_hz: float
    required_fresnel_clearance_ratio: float = DEFAULT_REQUIRED_FRESNEL_CLEARANCE_RATIO
    epsilon: float = DEFAULT_ALTITUDE_EPSILON

    def __post_init__(self) -> None:
        if not isfinite(self.frequency_hz) or self.frequency_hz <= 0.0:
            raise MinimumAltitudeError("frequency_hz must be finite and positive.")
        if (
            not isfinite(self.required_fresnel_clearance_ratio)
            or self.required_fresnel_clearance_ratio < 0.0
        ):
            raise MinimumAltitudeError(
                "required_fresnel_clearance_ratio must be finite and non-negative."
            )
        if not isfinite(self.epsilon) or self.epsilon < 0.0:
            raise MinimumAltitudeError("epsilon must be finite and non-negative.")


@dataclass(frozen=True)
class AltitudeRequirementSample:
    """Per-sample endpoint altitude required by the DSM/Fresnel proxy."""

    sample_index: int
    distance_from_launch_m: float
    distance_to_target_m: float
    path_ratio: float
    dem_msl_m: float
    dsm_msl_m: float
    fresnel_radius_m: float
    required_clearance_m: float
    required_los_msl_m: float
    required_drone_msl_m: float


@dataclass(frozen=True)
class MinimumAltitudeResult:
    """Minimum endpoint MSL and DEM-referenced AGL conversions."""

    minimum_required_msl_m: float
    minimum_required_agl_over_highest_dem_m: float
    minimum_required_agl_over_target_dem_m: float
    display_agl_over_highest_dem_m: float
    display_agl_over_target_dem_m: float
    highest_dem_msl_m: float
    target_dem_msl_m: float
    launch_antenna_msl_m: float
    frequency_hz: float
    required_fresnel_clearance_ratio: float
    limiting_sample_index: int
    sample_requirements: tuple[AltitudeRequirementSample, ...]


def compute_minimum_required_altitude(
    profile: TerrainProfile,
    *,
    launch_antenna_msl_m: float,
    frequency_hz: float,
    required_fresnel_clearance_ratio: float = DEFAULT_REQUIRED_FRESNEL_CLEARANCE_RATIO,
    epsilon: float = DEFAULT_ALTITUDE_EPSILON,
) -> MinimumAltitudeResult:
    """Compute a minimum endpoint MSL over a synthetic terrain profile.

    The calculation inverts the straight LOS interpolation at each valid sample so
    the line from ``launch_antenna_msl_m`` to the endpoint clears DSM by the requested
    fraction of the first Fresnel radius. The result is an offline altitude planning
    aid, not a real communication-success or flight-safety guarantee.
    """

    if not isfinite(launch_antenna_msl_m):
        raise MinimumAltitudeError("launch_antenna_msl_m must be finite.")
    config = MinimumAltitudeConfig(
        frequency_hz=frequency_hz,
        required_fresnel_clearance_ratio=required_fresnel_clearance_ratio,
        epsilon=epsilon,
    )
    _ensure_profile_samples(profile.samples)

    resolved_wavelength_m = wavelength_m(config.frequency_hz)
    sample_requirements: list[AltitudeRequirementSample] = []
    for sample in profile.samples:
        _validate_profile_sample(sample)
        total_distance_m = sample.distance_from_start_m + sample.distance_to_end_m
        if total_distance_m <= 0.0:
            raise MinimumAltitudeError("profile sample total distance must be positive.")

        path_ratio = sample.distance_from_start_m / total_distance_m
        if not isfinite(path_ratio) or path_ratio < 0.0 or path_ratio > 1.0:
            raise MinimumAltitudeError("profile sample path_ratio must be within [0, 1].")
        if path_ratio <= config.epsilon:
            continue

        fresnel_radius_m = first_fresnel_radius_m(
            wavelength_m=resolved_wavelength_m,
            d1_m=sample.distance_from_start_m,
            d2_m=sample.distance_to_end_m,
        )
        required_clearance_m = config.required_fresnel_clearance_ratio * fresnel_radius_m
        required_los_msl_m = sample.dsm_msl + required_clearance_m
        required_drone_msl_m = (
            launch_antenna_msl_m
            + (required_los_msl_m - launch_antenna_msl_m) / path_ratio
        )
        sample_requirements.append(
            AltitudeRequirementSample(
                sample_index=sample.sample_index,
                distance_from_launch_m=sample.distance_from_start_m,
                distance_to_target_m=sample.distance_to_end_m,
                path_ratio=path_ratio,
                dem_msl_m=sample.dem_msl,
                dsm_msl_m=sample.dsm_msl,
                fresnel_radius_m=fresnel_radius_m,
                required_clearance_m=required_clearance_m,
                required_los_msl_m=required_los_msl_m,
                required_drone_msl_m=required_drone_msl_m,
            )
        )

    if not sample_requirements:
        raise MinimumAltitudeError("profile must contain at least one valid ratio sample.")

    limiting_requirement = max(
        sample_requirements,
        key=lambda sample: sample.required_drone_msl_m,
    )
    highest_dem_msl_m = max(sample.dem_msl for sample in profile.samples)
    target_dem_msl_m = profile.samples[-1].dem_msl
    minimum_required_msl_m = limiting_requirement.required_drone_msl_m
    agl_over_highest_dem_m = minimum_required_msl_m - highest_dem_msl_m
    agl_over_target_dem_m = minimum_required_msl_m - target_dem_msl_m

    return MinimumAltitudeResult(
        minimum_required_msl_m=minimum_required_msl_m,
        minimum_required_agl_over_highest_dem_m=agl_over_highest_dem_m,
        minimum_required_agl_over_target_dem_m=agl_over_target_dem_m,
        display_agl_over_highest_dem_m=max(0.0, agl_over_highest_dem_m),
        display_agl_over_target_dem_m=max(0.0, agl_over_target_dem_m),
        highest_dem_msl_m=highest_dem_msl_m,
        target_dem_msl_m=target_dem_msl_m,
        launch_antenna_msl_m=launch_antenna_msl_m,
        frequency_hz=config.frequency_hz,
        required_fresnel_clearance_ratio=config.required_fresnel_clearance_ratio,
        limiting_sample_index=limiting_requirement.sample_index,
        sample_requirements=tuple(sample_requirements),
    )


def summarize_minimum_altitude_result(result: MinimumAltitudeResult) -> str:
    """Return a compact human-readable summary of a minimum altitude result."""

    if not isinstance(result, MinimumAltitudeResult):
        raise MinimumAltitudeError("result must be a MinimumAltitudeResult.")

    return (
        "minimum_required_msl_m="
        f"{result.minimum_required_msl_m:.2f}; "
        "minimum_required_agl_over_highest_dem_m="
        f"{result.minimum_required_agl_over_highest_dem_m:.2f}; "
        "minimum_required_agl_over_target_dem_m="
        f"{result.minimum_required_agl_over_target_dem_m:.2f}; "
        f"limiting_sample_index={result.limiting_sample_index}; "
        "This is an offline DSM-based LOS/Fresnel clearance proxy, not a real "
        "communication-success or flight-safety guarantee."
    )


def _ensure_profile_samples(samples: tuple[TerrainProfileSample, ...]) -> None:
    if not samples:
        raise MinimumAltitudeError("terrain profile must contain at least one sample.")


def _validate_profile_sample(sample: TerrainProfileSample) -> None:
    values = (
        sample.distance_from_start_m,
        sample.distance_to_end_m,
        sample.dem_msl,
        sample.dsm_msl,
    )
    if any(not isfinite(value) for value in values):
        raise MinimumAltitudeError("profile sample distance, DEM, and DSM values must be finite.")
    if sample.distance_from_start_m < 0.0:
        raise MinimumAltitudeError("distance_from_start_m must be non-negative.")
    if sample.distance_to_end_m < 0.0:
        raise MinimumAltitudeError("distance_to_end_m must be non-negative.")
    if sample.dsm_msl < sample.dem_msl:
        raise MinimumAltitudeError("profile sample DSM must be greater than or equal to DEM.")
