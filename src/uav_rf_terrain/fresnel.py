"""Pure Python DSM-based Fresnel radius and clearance analysis for Task 006.

This module consumes Task 005 LineOfSightAnalysis results and computes first Fresnel
radius, DSM clearance ratio, intrusion ratio, and a DSM Fresnel sample score. It does
not implement final scoring, shielding/overall score integration, color-map classes,
map layers, real DEM/DSM loading, or real communication-quality validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log10, sqrt

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
class DominantFresnelObstacle:
    """Most restrictive eligible Fresnel sample and knife-edge loss proxy."""

    sample_index: int
    distance_from_start_m: float
    dsm_msl: float
    los_msl: float
    clearance_m: float
    clearance_ratio: float
    fresnel_radius_m: float
    fresnel_sample_score: float
    nu: float
    diffraction_loss_db: float


@dataclass(frozen=True)
class FresnelAnalysis:
    """DSM Fresnel analysis over ordered LOS samples."""

    scenario_name: str
    frequency_hz: float
    wavelength_m: float
    samples: tuple[FresnelSample, ...]
    dsm_fresnel_score: float
    average_fresnel_score: float
    worst_obstacle_score: float | None
    dominant_obstacle: DominantFresnelObstacle | None

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


def knife_edge_nu_from_clearance_ratio(clearance_ratio: float) -> float:
    if not isfinite(clearance_ratio):
        raise FresnelAnalysisError("clearance_ratio must be finite.")
    return -sqrt(2.0) * clearance_ratio


def knife_edge_nu_from_height(*, h_m: float, wavelength_m: float, d1_m: float, d2_m: float) -> float:
    if not isfinite(h_m):
        raise FresnelAnalysisError("h_m must be finite.")
    for name, value in (("wavelength_m", wavelength_m), ("d1_m", d1_m), ("d2_m", d2_m)):
        if not isfinite(value) or value <= 0:
            raise FresnelAnalysisError(f"{name} must be finite and positive.")
    return h_m * sqrt(2.0 * (d1_m + d2_m) / (wavelength_m * d1_m * d2_m))


def knife_edge_loss_db(nu: float) -> float:
    if not isfinite(nu):
        raise FresnelAnalysisError("nu must be finite.")
    if nu <= -0.78:
        return 0.0
    loss_db = 6.9 + 20.0 * log10(sqrt((nu - 0.1) ** 2 + 1.0) + nu - 0.1)
    if not isfinite(loss_db):
        raise FresnelAnalysisError("knife-edge loss result must be finite.")
    return max(0.0, loss_db)


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

    resolved_samples = tuple(fresnel_samples)
    average_fresnel_score = sum(
        sample.dsm_fresnel_sample_score for sample in fresnel_samples
    ) / len(fresnel_samples)
    dominant_obstacle = _find_dominant_fresnel_obstacle(resolved_samples)
    return FresnelAnalysis(
        scenario_name=los_analysis.scenario_name,
        frequency_hz=frequency_hz,
        wavelength_m=resolved_wavelength_m,
        samples=resolved_samples,
        dsm_fresnel_score=average_fresnel_score,
        average_fresnel_score=average_fresnel_score,
        worst_obstacle_score=(
            dominant_obstacle.fresnel_sample_score if dominant_obstacle is not None else None
        ),
        dominant_obstacle=dominant_obstacle,
    )


def _find_dominant_fresnel_obstacle(
    samples: tuple[FresnelSample, ...],
) -> DominantFresnelObstacle | None:
    eligible_samples: list[FresnelSample] = []
    for sample in samples:
        values = (sample.clearance_ratio, sample.dsm_fresnel_sample_score)
        if not all(isfinite(value) for value in values):
            raise FresnelAnalysisError("dominant obstacle sample values must be finite.")
        if sample.d1_m > 0.0 and sample.d2_m > 0.0 and sample.fresnel_radius_m > 0.0:
            eligible_samples.append(sample)

    if not eligible_samples:
        return None

    sample = min(eligible_samples, key=lambda item: (item.clearance_ratio, item.sample_index))
    nu = knife_edge_nu_from_clearance_ratio(sample.clearance_ratio)
    los_sample = sample.los_sample
    return DominantFresnelObstacle(
        sample_index=sample.sample_index,
        distance_from_start_m=sample.d1_m,
        dsm_msl=los_sample.terrain_sample.dsm_msl,
        los_msl=los_sample.los_line_msl,
        clearance_m=los_sample.dsm_clearance_m,
        clearance_ratio=sample.clearance_ratio,
        fresnel_radius_m=sample.fresnel_radius_m,
        fresnel_sample_score=sample.dsm_fresnel_sample_score,
        nu=nu,
        diffraction_loss_db=knife_edge_loss_db(nu),
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
