"""Pure Python DSM-based Fresnel radius and clearance analysis for Task 006.

This module consumes Task 005 LineOfSightAnalysis results and computes first Fresnel
radius, DSM clearance ratio, intrusion ratio, and a DSM Fresnel sample score. It does
not implement final scoring, shielding/overall score integration, color-map classes,
map layers, real DEM/DSM loading, or real communication-quality validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt

from .los import LineOfSightAnalysis, LineOfSightSample

SPEED_OF_LIGHT_MPS: float = 299_792_458.0
"""Speed of light in meters per second used for wavelength calculation."""


class FresnelAnalysisError(ValueError):
    """Raised when DSM Fresnel analysis inputs are invalid."""


@dataclass(frozen=True)
class FresnelSample:
    """DSM Fresnel clearance analysis for one LOS sample."""

    sample_index: int
    los_sample: LineOfSightSample
    d1_m: float
    d2_m: float
    wavelength_m: float
    fresnel_radius_m: float
    clearance_ratio: float
    fresnel_intrusion_ratio: float
    dsm_fresnel_sample_score: float


@dataclass(frozen=True)
class FresnelAnalysis:
    """DSM Fresnel analysis over ordered LOS samples."""

    scenario_name: str
    frequency_hz: float
    wavelength_m: float
    samples: tuple[FresnelSample, ...]
    dsm_fresnel_score: float

    @property
    def sample_count(self) -> int:
        """Return the number of Fresnel samples."""

        return len(self.samples)

    @property
    def max_fresnel_radius_m(self) -> float:
        """Return the maximum first Fresnel radius along the path."""

        _ensure_fresnel_samples(self.samples)
        return max(sample.fresnel_radius_m for sample in self.samples)

    @property
    def max_intrusion_ratio(self) -> float:
        """Return the maximum DSM Fresnel intrusion ratio along the path."""

        _ensure_fresnel_samples(self.samples)
        return max(sample.fresnel_intrusion_ratio for sample in self.samples)

    @property
    def min_sample_score(self) -> float:
        """Return the minimum DSM Fresnel sample score along the path."""

        _ensure_fresnel_samples(self.samples)
        return min(sample.dsm_fresnel_sample_score for sample in self.samples)


def wavelength_m(frequency_hz: float) -> float:
    """Return wavelength in meters for a positive finite frequency in hertz."""

    if not isfinite(frequency_hz) or frequency_hz <= 0:
        raise FresnelAnalysisError("frequency_hz must be finite and positive.")
    return SPEED_OF_LIGHT_MPS / frequency_hz


def first_fresnel_radius_m(
    *,
    wavelength_m: float,
    d1_m: float,
    d2_m: float,
) -> float:
    """Return first Fresnel radius in meters for a profile sample.

    Endpoint samples can have d1 or d2 equal to zero, which yields a zero Fresnel
    radius. Negative, non-finite, or zero total path distance inputs are rejected.
    """

    if not isfinite(wavelength_m) or wavelength_m <= 0:
        raise FresnelAnalysisError("wavelength_m must be finite and positive.")
    if not isfinite(d1_m) or d1_m < 0:
        raise FresnelAnalysisError("d1_m must be finite and non-negative.")
    if not isfinite(d2_m) or d2_m < 0:
        raise FresnelAnalysisError("d2_m must be finite and non-negative.")

    total_distance_m = d1_m + d2_m
    if total_distance_m <= 0:
        raise FresnelAnalysisError("d1_m + d2_m must be positive.")

    if d1_m == 0.0 or d2_m == 0.0:
        return 0.0

    return sqrt(wavelength_m * d1_m * d2_m / total_distance_m)


def analyze_dsm_fresnel(
    los_analysis: LineOfSightAnalysis,
    *,
    frequency_hz: float,
) -> FresnelAnalysis:
    """Analyze DSM-based Fresnel clearance over LOS analysis samples.

    The returned ``dsm_fresnel_score`` is the arithmetic mean of per-sample scores.
    Final shielding stability and overall score integration are reserved for a later
    task.
    """

    resolved_wavelength_m = wavelength_m(frequency_hz)
    _ensure_los_samples(los_analysis.samples)

    fresnel_samples: list[FresnelSample] = []
    for los_sample in los_analysis.samples:
        terrain_sample = los_sample.terrain_sample
        d1_m = terrain_sample.distance_from_start_m
        d2_m = terrain_sample.distance_to_end_m
        radius_m = first_fresnel_radius_m(
            wavelength_m=resolved_wavelength_m,
            d1_m=d1_m,
            d2_m=d2_m,
        )
        clearance_ratio, intrusion_ratio, sample_score = _clearance_metrics(
            dsm_clearance_m=los_sample.dsm_clearance_m,
            fresnel_radius_m=radius_m,
        )
        fresnel_samples.append(
            FresnelSample(
                sample_index=los_sample.sample_index,
                los_sample=los_sample,
                d1_m=d1_m,
                d2_m=d2_m,
                wavelength_m=resolved_wavelength_m,
                fresnel_radius_m=radius_m,
                clearance_ratio=clearance_ratio,
                fresnel_intrusion_ratio=intrusion_ratio,
                dsm_fresnel_sample_score=sample_score,
            )
        )

    dsm_fresnel_score = sum(
        sample.dsm_fresnel_sample_score for sample in fresnel_samples
    ) / len(fresnel_samples)
    return FresnelAnalysis(
        scenario_name=los_analysis.scenario_name,
        frequency_hz=frequency_hz,
        wavelength_m=resolved_wavelength_m,
        samples=tuple(fresnel_samples),
        dsm_fresnel_score=dsm_fresnel_score,
    )


def _clearance_metrics(
    *,
    dsm_clearance_m: float,
    fresnel_radius_m: float,
) -> tuple[float, float, float]:
    if not isfinite(dsm_clearance_m):
        raise FresnelAnalysisError("dsm_clearance_m must be finite.")
    if not isfinite(fresnel_radius_m) or fresnel_radius_m < 0:
        raise FresnelAnalysisError("fresnel_radius_m must be finite and non-negative.")

    if fresnel_radius_m == 0.0:
        return 1.0, 0.0, 100.0

    clearance_ratio = dsm_clearance_m / fresnel_radius_m
    fresnel_intrusion_ratio = _clamp(1.0 - clearance_ratio, lower=0.0, upper=1.0)
    dsm_fresnel_sample_score = _clamp(
        100.0 * (1.0 - fresnel_intrusion_ratio),
        lower=0.0,
        upper=100.0,
    )
    return clearance_ratio, fresnel_intrusion_ratio, dsm_fresnel_sample_score


def _clamp(value: float, *, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _ensure_los_samples(samples: tuple[LineOfSightSample, ...]) -> None:
    if not samples:
        raise FresnelAnalysisError("LOS analysis must contain at least one sample.")


def _ensure_fresnel_samples(samples: tuple[FresnelSample, ...]) -> None:
    if not samples:
        raise FresnelAnalysisError("Fresnel analysis must contain at least one sample.")
