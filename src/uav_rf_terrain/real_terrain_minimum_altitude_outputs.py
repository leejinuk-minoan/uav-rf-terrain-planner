"""Immutable, MGRS-facing outputs for the Task 036B pure altitude proxy.

The contracts deliberately contain no terrain adapter, raster cell, projected
coordinate, or raw profile fields.  Task 036C prepares terrain evidence separately.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .real_terrain_route_outputs import RouteMode


class RealTerrainMinimumAltitudeOutputError(ValueError):
    """Raised when a public altitude-output contract is invalid."""


def _finite(name: str, value: object, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise RealTerrainMinimumAltitudeOutputError(f"{name} must be finite numeric.")
    numeric = float(value)
    if positive and numeric <= 0.0:
        raise RealTerrainMinimumAltitudeOutputError(f"{name} must be positive.")
    return numeric


def _text(name: str, value: object, *, mgrs: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RealTerrainMinimumAltitudeOutputError(f"{name} must be non-empty text.")
    if mgrs and value != value.upper():
        raise RealTerrainMinimumAltitudeOutputError(f"{name} must be uppercase MGRS text.")
    return value


@dataclass(frozen=True)
class RealTerrainMinimumAltitudeConfig:
    """Bounded pure-engine configuration; values are proxy assumptions, not approvals."""

    expected_frequency_hz: float | None = None
    required_fresnel_clearance_ratio: float = 0.6
    profile_spacing_m: float | None = None
    epsilon_m: float = 1e-9
    distance_tolerance_m: float = 1e-9
    max_routes: int = 3
    max_route_samples: int = 10_000
    max_profile_samples_per_link: int = 10_000
    max_total_profile_samples: int = 50_000

    def __post_init__(self) -> None:
        if self.expected_frequency_hz is not None:
            _finite("expected_frequency_hz", self.expected_frequency_hz, positive=True)
        ratio = _finite("required_fresnel_clearance_ratio", self.required_fresnel_clearance_ratio)
        if not 0.0 <= ratio <= 1.0:
            raise RealTerrainMinimumAltitudeOutputError("required_fresnel_clearance_ratio must be within [0, 1].")
        if self.profile_spacing_m is not None:
            _finite("profile_spacing_m", self.profile_spacing_m, positive=True)
        _finite("epsilon_m", self.epsilon_m)
        _finite("distance_tolerance_m", self.distance_tolerance_m)
        if self.epsilon_m < 0.0 or self.distance_tolerance_m < 0.0:
            raise RealTerrainMinimumAltitudeOutputError("epsilon and tolerance must be non-negative.")
        for name in ("max_routes", "max_route_samples", "max_profile_samples_per_link", "max_total_profile_samples"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise RealTerrainMinimumAltitudeOutputError(f"{name} must be a positive integer.")


@dataclass(frozen=True)
class RealTerrainRadialRequirementSample:
    radial_requirement_id: str
    route_sample_id: str
    radial_sample_index: int
    distance_from_launch_m: float
    distance_to_endpoint_m: float
    path_ratio: float
    dem_msl_m: float
    dsm_msl_m: float
    fresnel_radius_m: float
    required_clearance_m: float
    required_los_msl_m: float
    required_endpoint_msl_m: float

    def __post_init__(self) -> None:
        _text("radial_requirement_id", self.radial_requirement_id)
        _text("route_sample_id", self.route_sample_id)
        if isinstance(self.radial_sample_index, bool) or not isinstance(self.radial_sample_index, int) or self.radial_sample_index < 0:
            raise RealTerrainMinimumAltitudeOutputError("radial_sample_index must be non-negative integer.")
        for name in ("distance_from_launch_m", "distance_to_endpoint_m", "path_ratio", "dem_msl_m", "dsm_msl_m", "fresnel_radius_m", "required_clearance_m", "required_los_msl_m", "required_endpoint_msl_m"):
            _finite(name, getattr(self, name))
        if self.distance_from_launch_m < 0.0 or self.distance_to_endpoint_m < 0.0 or not 0.0 <= self.path_ratio <= 1.0:
            raise RealTerrainMinimumAltitudeOutputError("radial distances and path_ratio are invalid.")
        if self.dsm_msl_m < self.dem_msl_m or self.fresnel_radius_m < 0.0 or self.required_clearance_m < 0.0:
            raise RealTerrainMinimumAltitudeOutputError("radial terrain/clearance values are invalid.")


@dataclass(frozen=True)
class RealTerrainRouteAltitudeSample:
    route_sample_id: str
    route_id: str
    mode: RouteMode
    route_sample_index: int
    route_sample_mgrs: str
    cumulative_route_distance_2d_m: float
    local_dem_msl_m: float
    local_dsm_msl_m: float
    current_route_flight_msl_m: float
    required_endpoint_msl_m: float
    current_clearance_margin_m: float
    radial_requirement_samples: tuple[RealTerrainRadialRequirementSample, ...]
    limiting_radial_requirement: RealTerrainRadialRequirementSample | None
    sample_semantics: str
    is_snapped_target_endpoint: bool

    def __post_init__(self) -> None:
        _text("route_sample_id", self.route_sample_id)
        _text("route_id", self.route_id)
        if not isinstance(self.mode, RouteMode):
            raise RealTerrainMinimumAltitudeOutputError("mode must be RouteMode.")
        if isinstance(self.route_sample_index, bool) or not isinstance(self.route_sample_index, int) or self.route_sample_index < 0:
            raise RealTerrainMinimumAltitudeOutputError("route_sample_index must be non-negative integer.")
        _text("route_sample_mgrs", self.route_sample_mgrs, mgrs=True)
        for name in ("cumulative_route_distance_2d_m", "local_dem_msl_m", "local_dsm_msl_m", "current_route_flight_msl_m", "required_endpoint_msl_m", "current_clearance_margin_m"):
            _finite(name, getattr(self, name))
        if self.cumulative_route_distance_2d_m < 0.0 or self.local_dsm_msl_m < self.local_dem_msl_m:
            raise RealTerrainMinimumAltitudeOutputError("route sample terrain/distance values are invalid.")
        if not isinstance(self.is_snapped_target_endpoint, bool):
            raise RealTerrainMinimumAltitudeOutputError("is_snapped_target_endpoint must be bool.")
        _text("sample_semantics", self.sample_semantics)
        if self.sample_semantics == "coincident_launch_occupancy":
            if self.radial_requirement_samples or self.limiting_radial_requirement is not None:
                raise RealTerrainMinimumAltitudeOutputError("coincident sample cannot expose radial requirements.")
        elif not self.radial_requirement_samples or self.limiting_radial_requirement is None:
            raise RealTerrainMinimumAltitudeOutputError("noncoincident sample requires radial requirements.")


@dataclass(frozen=True)
class RealTerrainRouteMinimumAltitudeResult:
    route_id: str
    mode: RouteMode
    source_order: int
    source_total_distance_3d_m: float
    route_polyline_total_distance_2d_m: float
    frequency_hz: float
    required_fresnel_clearance_ratio: float
    profile_spacing_m: float
    actual_launch_ground_msl_m: float
    launch_antenna_msl_m: float
    allowed_flight_agl_m: float
    minimum_required_constant_route_msl_m: float
    highest_route_dem_msl_m: float
    target_dem_msl_m: float
    agl_over_highest_route_dem_m: float
    agl_over_target_dem_m: float
    constant_msl_limiting_sample_id: str
    minimum_current_clearance_margin_m: float
    current_fixed_agl_meets_proxy: bool
    current_agl_deficit_limiting_sample_id: str
    route_samples: tuple[RealTerrainRouteAltitudeSample, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        _text("route_id", self.route_id)
        if not isinstance(self.mode, RouteMode) or isinstance(self.source_order, bool) or not isinstance(self.source_order, int) or self.source_order < 0:
            raise RealTerrainMinimumAltitudeOutputError("route identity is invalid.")
        for name in ("source_total_distance_3d_m", "route_polyline_total_distance_2d_m", "frequency_hz", "required_fresnel_clearance_ratio", "profile_spacing_m", "actual_launch_ground_msl_m", "launch_antenna_msl_m", "allowed_flight_agl_m", "minimum_required_constant_route_msl_m", "highest_route_dem_msl_m", "target_dem_msl_m", "agl_over_highest_route_dem_m", "agl_over_target_dem_m", "minimum_current_clearance_margin_m"):
            _finite(name, getattr(self, name))
        if self.source_total_distance_3d_m < 0.0 or self.route_polyline_total_distance_2d_m < 0.0 or self.frequency_hz <= 0.0:
            raise RealTerrainMinimumAltitudeOutputError("route distance/frequency values are invalid.")
        if not self.route_samples or not isinstance(self.current_fixed_agl_meets_proxy, bool):
            raise RealTerrainMinimumAltitudeOutputError("route samples and proxy state are required.")
        _text("constant_msl_limiting_sample_id", self.constant_msl_limiting_sample_id)
        _text("current_agl_deficit_limiting_sample_id", self.current_agl_deficit_limiting_sample_id)
        if len(set(self.warnings)) != len(self.warnings):
            raise RealTerrainMinimumAltitudeOutputError("route warnings must be unique.")


@dataclass(frozen=True)
class RealTerrainMinimumAltitudeSummary:
    route_count: int
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.route_count, bool) or not isinstance(self.route_count, int) or self.route_count <= 0:
            raise RealTerrainMinimumAltitudeOutputError("route_count must be positive integer.")
        if len(set(self.warnings)) != len(self.warnings):
            raise RealTerrainMinimumAltitudeOutputError("summary warnings must be unique.")


@dataclass(frozen=True)
class RealTerrainMinimumAltitudeResult:
    selected_candidate_id: str
    launch_site_mgrs: str
    target_mgrs: str
    route_results: tuple[RealTerrainRouteMinimumAltitudeResult, ...]
    warnings: tuple[str, ...]
    summary: RealTerrainMinimumAltitudeSummary
    _terrain_metadata: object
    _selected_projected_point: object
    _config: RealTerrainMinimumAltitudeConfig

    def __post_init__(self) -> None:
        _text("selected_candidate_id", self.selected_candidate_id)
        _text("launch_site_mgrs", self.launch_site_mgrs, mgrs=True)
        _text("target_mgrs", self.target_mgrs, mgrs=True)
        if not self.route_results or not isinstance(self.summary, RealTerrainMinimumAltitudeSummary):
            raise RealTerrainMinimumAltitudeOutputError("route_results and summary are required.")
        if self.summary.route_count != len(self.route_results) or self.warnings != self.summary.warnings:
            raise RealTerrainMinimumAltitudeOutputError("top-level warning/summary parity failed.")
        if not isinstance(self._config, RealTerrainMinimumAltitudeConfig):
            raise RealTerrainMinimumAltitudeOutputError("private config authority is invalid.")

    def to_public_dict(self) -> dict[str, object]:
        """Return MGRS-facing data without private projected/profile/raster authority."""
        return {"selected_candidate_id": self.selected_candidate_id, "launch_site_mgrs": self.launch_site_mgrs, "target_mgrs": self.target_mgrs, "warnings": self.warnings, "routes": tuple({"route_id": route.route_id, "mode": route.mode.value, "minimum_required_constant_route_msl_m": route.minimum_required_constant_route_msl_m, "agl_over_highest_route_dem_m": route.agl_over_highest_route_dem_m, "agl_over_target_dem_m": route.agl_over_target_dem_m} for route in self.route_results)}
