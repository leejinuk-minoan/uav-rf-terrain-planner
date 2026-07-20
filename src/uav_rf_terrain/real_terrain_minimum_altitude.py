"""Pure Task 036B engine over prepared route/profile evidence only.

This module deliberately does not import or call a terrain adapter.  A later task
will prepare its immutable input from one checked terrain session.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from .coordinates import LocalPoint
from .fresnel import first_fresnel_radius_m, wavelength_m
from .profile import TerrainProfile
from .real_terrain_minimum_altitude_outputs import (
    RealTerrainMinimumAltitudeConfig, RealTerrainMinimumAltitudeResult,
    RealTerrainMinimumAltitudeSummary, RealTerrainRadialRequirementSample,
    RealTerrainRouteAltitudeSample, RealTerrainRouteMinimumAltitudeResult,
)
from .real_terrain_route_outputs import RouteMode


class RealTerrainMinimumAltitudeError(ValueError):
    """Raised for invalid prepared evidence or a fatal pure-engine invariant."""


@dataclass(frozen=True)
class PreparedRealTerrainRouteSample:
    route_sample_id: str
    route_id: str
    mode: RouteMode
    route_sample_index: int
    route_sample_mgrs: str
    projected_point: LocalPoint
    cumulative_route_distance_2d_m: float
    local_dem_msl_m: float
    local_dsm_msl_m: float
    is_snapped_target_endpoint: bool
    radial_distance_2d_m: float
    radial_profile: TerrainProfile | None

    def __post_init__(self) -> None:
        if not isinstance(self.projected_point, LocalPoint) or not isinstance(self.mode, RouteMode):
            raise RealTerrainMinimumAltitudeError("prepared sample point and mode are invalid.")
        if not isinstance(self.route_sample_id, str) or not self.route_sample_id or not isinstance(self.route_id, str) or not self.route_id:
            raise RealTerrainMinimumAltitudeError("prepared sample IDs are required.")
        if self.route_sample_mgrs != self.route_sample_mgrs.upper() or not self.route_sample_mgrs:
            raise RealTerrainMinimumAltitudeError("prepared sample MGRS must be uppercase.")
        if isinstance(self.route_sample_index, bool) or not isinstance(self.route_sample_index, int) or self.route_sample_index < 0:
            raise RealTerrainMinimumAltitudeError("prepared sample index is invalid.")
        for value in (self.cumulative_route_distance_2d_m, self.local_dem_msl_m, self.local_dsm_msl_m, self.radial_distance_2d_m):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise RealTerrainMinimumAltitudeError("prepared numeric evidence must be finite.")
        if self.cumulative_route_distance_2d_m < 0 or self.radial_distance_2d_m < 0 or self.local_dsm_msl_m < self.local_dem_msl_m:
            raise RealTerrainMinimumAltitudeError("prepared terrain/distance evidence is invalid.")
        if not isinstance(self.is_snapped_target_endpoint, bool):
            raise RealTerrainMinimumAltitudeError("target endpoint flag must be bool.")
        if self.radial_distance_2d_m > 0.0 and self.radial_profile is None:
            raise RealTerrainMinimumAltitudeError("nonzero radial distance requires a radial profile.")


@dataclass(frozen=True)
class PreparedRealTerrainRoute:
    route_id: str
    mode: RouteMode
    source_order: int
    source_total_distance_3d_m: float
    route_polyline_total_distance_2d_m: float
    terrain_metadata: object
    samples: tuple[PreparedRealTerrainRouteSample, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.mode, RouteMode) or not self.route_id or self.route_id != f"route-{self.mode.value}":
            raise RealTerrainMinimumAltitudeError("prepared route identity is invalid.")
        if isinstance(self.source_order, bool) or not isinstance(self.source_order, int) or self.source_order < 0 or not self.samples:
            raise RealTerrainMinimumAltitudeError("prepared route order/samples are invalid.")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0 for value in (self.source_total_distance_3d_m, self.route_polyline_total_distance_2d_m)):
            raise RealTerrainMinimumAltitudeError("prepared route distances are invalid.")
        if tuple(sample.route_sample_index for sample in self.samples) != tuple(range(len(self.samples))):
            raise RealTerrainMinimumAltitudeError("prepared sample indexes must be contiguous.")
        if any(sample.route_id != self.route_id or sample.mode is not self.mode for sample in self.samples):
            raise RealTerrainMinimumAltitudeError("prepared sample route parity failed.")


def compute_real_terrain_minimum_altitude(*, route_result: Any, selected_launch_site: Any, prepared_routes: tuple[PreparedRealTerrainRoute, ...], config: RealTerrainMinimumAltitudeConfig) -> RealTerrainMinimumAltitudeResult:
    """Compute deterministic proxy MSL results without terrain/session access."""
    if not isinstance(config, RealTerrainMinimumAltitudeConfig):
        raise RealTerrainMinimumAltitudeError("config must be RealTerrainMinimumAltitudeConfig.")
    try:
        source_config = route_result.config
        frequency = source_config.frequency_hz
        allowed_agl = source_config.allowed_flight_agl_m
        launch_ground = route_result.launch_ground_msl_m
        selected_id = route_result.selected_candidate_id
        launch_mgrs = route_result.launch_site_mgrs
        target_mgrs = route_result.target_mgrs
        metadata = route_result.terrain_metadata
    except AttributeError as exc:
        raise RealTerrainMinimumAltitudeError("route_result lacks complete route authority.") from exc
    if getattr(selected_launch_site, "candidate_id", None) != selected_id or getattr(selected_launch_site, "launch_site_mgrs", None) != launch_mgrs:
        raise RealTerrainMinimumAltitudeError("selected launch authority does not match route result.")
    if not isinstance(frequency, (int, float)) or isinstance(frequency, bool) or not isfinite(frequency) or frequency <= 0:
        raise RealTerrainMinimumAltitudeError("route frequency must be finite positive.")
    if config.expected_frequency_hz is not None and config.expected_frequency_hz != frequency:
        raise RealTerrainMinimumAltitudeError("expected frequency does not match route authority.")
    if config.profile_spacing_m is not None and config.profile_spacing_m > source_config.profile_spacing_m:
        raise RealTerrainMinimumAltitudeError("explicit profile spacing cannot exceed route profile spacing.")
    if len(prepared_routes) > config.max_routes or not prepared_routes:
        raise RealTerrainMinimumAltitudeError("prepared route count violates resource guard.")
    _validate_prepared_authority(route_result, prepared_routes, metadata, config.distance_tolerance_m)
    launch_antenna = launch_ground + allowed_agl
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and isfinite(v) for v in (launch_ground, allowed_agl, launch_antenna)):
        raise RealTerrainMinimumAltitudeError("launch authority is not finite.")
    total_profiles = 0
    for route in prepared_routes:
        if route.terrain_metadata != metadata:
            raise RealTerrainMinimumAltitudeError("prepared terrain metadata does not match route authority.")
        if len(route.samples) > config.max_route_samples:
            raise RealTerrainMinimumAltitudeError("route sample count violates resource guard.")
        for sample in route.samples:
            if sample.radial_profile is not None:
                count = len(sample.radial_profile.samples)
                if count > config.max_profile_samples_per_link:
                    raise RealTerrainMinimumAltitudeError("profile sample count violates resource guard.")
                total_profiles += count
    if total_profiles > config.max_total_profile_samples:
        raise RealTerrainMinimumAltitudeError("total profile sample count violates resource guard.")
    resolved_spacing = float(config.profile_spacing_m or source_config.profile_spacing_m)
    route_results = tuple(_compute_route(route, launch_point=selected_launch_site.projected_point, launch_ground=launch_ground, launch_antenna=launch_antenna, allowed_agl=allowed_agl, frequency=float(frequency), profile_spacing_m=resolved_spacing, config=config) for route in prepared_routes)
    warnings = tuple(warning for route in route_results for warning in route.warnings)
    return RealTerrainMinimumAltitudeResult(selected_id, launch_mgrs, target_mgrs, route_results, warnings, RealTerrainMinimumAltitudeSummary(len(route_results), warnings), metadata, selected_launch_site.projected_point, config)


def _validate_prepared_authority(route_result: Any, prepared_routes: tuple[PreparedRealTerrainRoute, ...], metadata: object, tolerance: float) -> None:
    """Revalidate source route and prepared evidence before any Fresnel calculation."""
    ids: set[str] = set()
    for expected_order, route in enumerate(prepared_routes):
        if route.source_order != expected_order or route.terrain_metadata != metadata:
            raise RealTerrainMinimumAltitudeError("prepared route order or terrain authority mismatch.")
        sample_ids = tuple(sample.route_sample_id for sample in route.samples)
        if len(set(sample_ids)) != len(sample_ids) or ids.intersection(sample_ids):
            raise RealTerrainMinimumAltitudeError("prepared sample IDs must be globally unique.")
        ids.update(sample_ids)
        if route.samples[0].cumulative_route_distance_2d_m != 0.0:
            raise RealTerrainMinimumAltitudeError("prepared route must start at cumulative 2D distance zero.")
        if abs(route.samples[-1].cumulative_route_distance_2d_m - route.route_polyline_total_distance_2d_m) > tolerance:
            raise RealTerrainMinimumAltitudeError("prepared route last 2D distance does not match route total.")
        if any(left.cumulative_route_distance_2d_m > right.cumulative_route_distance_2d_m + tolerance for left, right in zip(route.samples, route.samples[1:])):
            raise RealTerrainMinimumAltitudeError("prepared route cumulative 2D distance is not ordered.")
        targets = tuple(sample for sample in route.samples if sample.is_snapped_target_endpoint)
        if len(targets) != 1 or targets[0] is not route.samples[-1]:
            raise RealTerrainMinimumAltitudeError("prepared route must have exactly one final target endpoint.")
        if hasattr(route_result, "route_candidates"):
            candidates = route_result.route_candidates
            if len(candidates) != len(prepared_routes):
                raise RealTerrainMinimumAltitudeError("prepared route count does not match source routes.")
            source = candidates[expected_order]
            if source.route_id != route.route_id or source.mode is not route.mode or abs(source.total_distance_3d_m - route.source_total_distance_3d_m) > tolerance:
                raise RealTerrainMinimumAltitudeError("prepared route does not match source route authority.")
            if route.samples[0].route_sample_mgrs != route_result.snapped_launch_node_mgrs or route.samples[-1].route_sample_mgrs != route_result.snapped_target_node_mgrs:
                raise RealTerrainMinimumAltitudeError("prepared route endpoint MGRS does not match snap authority.")


def _compute_route(route: PreparedRealTerrainRoute, *, launch_point: LocalPoint, launch_ground: float, launch_antenna: float, allowed_agl: float, frequency: float, profile_spacing_m: float, config: RealTerrainMinimumAltitudeConfig) -> RealTerrainRouteMinimumAltitudeResult:
    samples = tuple(_compute_sample(item, launch_point, launch_ground, launch_antenna, allowed_agl, frequency, config) for item in route.samples)
    max_sample = max(samples, key=lambda item: (item.required_endpoint_msl_m, -item.cumulative_route_distance_2d_m, -item.route_sample_index))
    deficit_sample = min(samples, key=lambda item: (item.current_clearance_margin_m, item.cumulative_route_distance_2d_m, item.route_sample_index))
    msl = max_sample.required_endpoint_msl_m
    highest_dem = max(item.local_dem_msl_m for item in samples)
    target = next(item for item in samples if item.is_snapped_target_endpoint).local_dem_msl_m
    agl_high = _nonnegative(msl - highest_dem, config.distance_tolerance_m)
    agl_target = _nonnegative(msl - target, config.distance_tolerance_m)
    warnings: list[str] = []
    if deficit_sample.current_clearance_margin_m < -config.distance_tolerance_m:
        warnings.append(f"{route.route_id}: current fixed-AGL route is below the configured clearance proxy at one or more route samples.")
    if max_sample.is_snapped_target_endpoint:
        warnings.append(f"{route.route_id}: constant-MSL limiting sample is the snapped target endpoint.")
    if deficit_sample.is_snapped_target_endpoint:
        warnings.append(f"{route.route_id}: current-AGL deficit-limiting sample is the snapped target endpoint.")
    return RealTerrainRouteMinimumAltitudeResult(route.route_id, route.mode, route.source_order, route.source_total_distance_3d_m, route.route_polyline_total_distance_2d_m, frequency, config.required_fresnel_clearance_ratio, profile_spacing_m, launch_ground, launch_antenna, allowed_agl, msl, highest_dem, target, agl_high, agl_target, max_sample.route_sample_id, deficit_sample.current_clearance_margin_m, deficit_sample.current_clearance_margin_m >= -config.distance_tolerance_m, deficit_sample.route_sample_id, samples, tuple(warnings))


def _compute_sample(item: PreparedRealTerrainRouteSample, launch_point: LocalPoint, launch_ground: float, launch_antenna: float, allowed_agl: float, frequency: float, config: RealTerrainMinimumAltitudeConfig) -> RealTerrainRouteAltitudeSample:
    if item.radial_distance_2d_m <= config.distance_tolerance_m:
        if item.projected_point != launch_point or item.radial_profile is not None or abs(item.local_dem_msl_m - launch_ground) > config.distance_tolerance_m or item.local_dsm_msl_m > launch_antenna + config.distance_tolerance_m:
            raise RealTerrainMinimumAltitudeError("coincident launch evidence is invalid.")
        required = launch_antenna
        requirements: tuple[RealTerrainRadialRequirementSample, ...] = ()
        limiting = None
        semantics = "coincident_launch_occupancy"
    else:
        if item.radial_profile is None:
            raise RealTerrainMinimumAltitudeError("nonzero radial evidence requires a profile.")
        requirements = _requirements(item, launch_antenna, frequency, config)
        if not requirements:
            raise RealTerrainMinimumAltitudeError("radial profile has no eligible path ratio sample.")
        limiting = max(requirements, key=lambda value: (value.required_endpoint_msl_m, -value.radial_sample_index))
        required = limiting.required_endpoint_msl_m
        semantics = "radial_profile_proxy"
    current = item.local_dem_msl_m + allowed_agl
    return RealTerrainRouteAltitudeSample(item.route_sample_id, item.route_id, item.mode, item.route_sample_index, item.route_sample_mgrs, item.cumulative_route_distance_2d_m, item.local_dem_msl_m, item.local_dsm_msl_m, current, required, current - required, requirements, limiting, semantics, item.is_snapped_target_endpoint)


def _requirements(item: PreparedRealTerrainRouteSample, antenna: float, frequency: float, config: RealTerrainMinimumAltitudeConfig) -> tuple[RealTerrainRadialRequirementSample, ...]:
    assert item.radial_profile is not None
    result: list[RealTerrainRadialRequirementSample] = []
    wavelength = wavelength_m(frequency)
    for sample in item.radial_profile.samples:
        total = sample.distance_from_start_m + sample.distance_to_end_m
        if total <= 0.0:
            raise RealTerrainMinimumAltitudeError("radial profile total distance must be positive.")
        ratio = sample.distance_from_start_m / total
        if ratio <= config.epsilon_m:
            continue
        radius = first_fresnel_radius_m(
            wavelength_m=wavelength,
            d1_m=sample.distance_from_start_m,
            d2_m=sample.distance_to_end_m,
        )
        clearance = config.required_fresnel_clearance_ratio * radius
        los = sample.dsm_msl + clearance
        endpoint = antenna + (los - antenna) / ratio
        if not isfinite(endpoint):
            raise RealTerrainMinimumAltitudeError("radial requirement is non-finite.")
        result.append(RealTerrainRadialRequirementSample(f"{item.route_sample_id}-radial-{sample.sample_index:03d}", item.route_sample_id, sample.sample_index, sample.distance_from_start_m, sample.distance_to_end_m, ratio, sample.dem_msl, sample.dsm_msl, radius, clearance, los, endpoint))
    return tuple(result)


def _nonnegative(value: float, tolerance: float) -> float:
    if value < -tolerance:
        raise RealTerrainMinimumAltitudeError("AGL invariant is negative beyond tolerance.")
    return 0.0 if abs(value) <= tolerance else value
