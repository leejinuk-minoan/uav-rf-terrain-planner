"""Immutable MGRS-facing Task 036B output contracts and recursive validators."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .coordinates import LocalPoint
from .launch_site_selection import SelectedLaunchSiteRecord
from .real_terrain_route_outputs import RealTerrainRouteResult, RouteMode
from .terrain_data import TerrainDataError, TerrainDatasetMetadata, validate_terrain_dataset_metadata


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


def _near(left: float, right: float, tolerance: float) -> bool:
    return (
        isinstance(left, (int, float))
        and not isinstance(left, bool)
        and isfinite(left)
        and isinstance(right, (int, float))
        and not isinstance(right, bool)
        and isfinite(right)
        and isinstance(tolerance, (int, float))
        and not isinstance(tolerance, bool)
        and isfinite(tolerance)
        and tolerance >= 0.0
        and abs(left - right) <= tolerance
    )


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
class RealTerrainMinimumAltitudeSourceRoute:
    """Private source-route authority retained for recursive result revalidation."""

    route_id: str
    mode: RouteMode
    source_order: int
    source_total_distance_3d_m: float

    def __post_init__(self) -> None:
        if not isinstance(self.mode, RouteMode) or self.route_id != f"route-{self.mode.value}":
            raise RealTerrainMinimumAltitudeOutputError("source route identity is invalid.")
        if isinstance(self.source_order, bool) or not isinstance(self.source_order, int) or self.source_order < 0:
            raise RealTerrainMinimumAltitudeOutputError("source route order is invalid.")
        if _finite("source_total_distance_3d_m", self.source_total_distance_3d_m) < 0.0:
            raise RealTerrainMinimumAltitudeOutputError("source route 3D total is invalid.")


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
        if not isinstance(self.radial_requirement_samples, tuple):
            raise RealTerrainMinimumAltitudeOutputError("radial requirement samples must be a tuple.")
        if self.limiting_radial_requirement is not None and not isinstance(
            self.limiting_radial_requirement, RealTerrainRadialRequirementSample
        ):
            raise RealTerrainMinimumAltitudeOutputError("limiting radial requirement type is invalid.")
        if self.sample_semantics == "coincident_launch_occupancy":
            if self.radial_requirement_samples or self.limiting_radial_requirement is not None:
                raise RealTerrainMinimumAltitudeOutputError("coincident sample cannot expose radial requirements.")
        elif self.sample_semantics == "radial_profile_proxy":
            if not self.radial_requirement_samples or self.limiting_radial_requirement is None:
                raise RealTerrainMinimumAltitudeOutputError("radial sample requires radial requirements.")
        else:
            raise RealTerrainMinimumAltitudeOutputError("route sample semantics are invalid.")


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
        if not isinstance(self.route_samples, tuple) or not isinstance(self.warnings, tuple):
            raise RealTerrainMinimumAltitudeOutputError("route samples and warnings must be tuples.")
        if not self.route_samples or not isinstance(self.current_fixed_agl_meets_proxy, bool):
            raise RealTerrainMinimumAltitudeOutputError("route samples and proxy state are required.")
        _text("constant_msl_limiting_sample_id", self.constant_msl_limiting_sample_id)
        _text("current_agl_deficit_limiting_sample_id", self.current_agl_deficit_limiting_sample_id)
        if len(set(self.warnings)) != len(self.warnings):
            raise RealTerrainMinimumAltitudeOutputError("route warnings must be unique.")


@dataclass(frozen=True)
class RealTerrainMinimumAltitudeSummary:
    route_count: int
    route_sample_count: int
    radial_requirement_count: int
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("route_count", "route_sample_count", "radial_requirement_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise RealTerrainMinimumAltitudeOutputError(f"{name} must be non-negative integer.")
        if self.route_count <= 0:
            raise RealTerrainMinimumAltitudeOutputError("route_count must be positive integer.")
        if not isinstance(self.warnings, tuple):
            raise RealTerrainMinimumAltitudeOutputError("summary warnings must be a tuple.")
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
    _terrain_metadata: TerrainDatasetMetadata
    _selected_projected_point: LocalPoint
    _config: RealTerrainMinimumAltitudeConfig
    _source_route_authority: tuple[RealTerrainMinimumAltitudeSourceRoute, ...]
    _source_route_result: RealTerrainRouteResult
    _selected_launch_site: SelectedLaunchSiteRecord
    _prepared_routes: tuple[object, ...]

    def __post_init__(self) -> None:
        validate_real_terrain_minimum_altitude_result(self)

    def to_public_dict(self) -> dict[str, object]:
        """Return MGRS-facing proxy output without projected/profile/raster details."""
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "launch_site_mgrs": self.launch_site_mgrs,
            "target_mgrs": self.target_mgrs,
            "warnings": self.warnings,
            "routes": tuple(
                {
                    "route_id": route.route_id,
                    "mode": route.mode.value,
                    "source_total_distance_3d_m": route.source_total_distance_3d_m,
                    "route_polyline_total_distance_2d_m": route.route_polyline_total_distance_2d_m,
                    "minimum_required_constant_route_msl_m": route.minimum_required_constant_route_msl_m,
                    "agl_over_highest_route_dem_m": route.agl_over_highest_route_dem_m,
                    "agl_over_target_dem_m": route.agl_over_target_dem_m,
                    "current_fixed_agl_meets_proxy": route.current_fixed_agl_meets_proxy,
                    "minimum_current_clearance_margin_m": route.minimum_current_clearance_margin_m,
                    "constant_msl_limiting_sample_id": route.constant_msl_limiting_sample_id,
                    "constant_msl_limiting_sample_mgrs": _sample_by_id(route, route.constant_msl_limiting_sample_id).route_sample_mgrs,
                    "current_agl_deficit_limiting_sample_id": route.current_agl_deficit_limiting_sample_id,
                    "current_agl_deficit_limiting_sample_mgrs": _sample_by_id(route, route.current_agl_deficit_limiting_sample_id).route_sample_mgrs,
                    "warnings": route.warnings,
                    "interpretation_limit": "offline DSM/LOS/Fresnel clearance proxy; not a flight, communication, or approval guarantee",
                }
                for route in self.route_results
            ),
        }


def validate_real_terrain_minimum_altitude_result(result: RealTerrainMinimumAltitudeResult) -> None:
    """Recursively validate immutable Task 036B outputs after direct mutation attempts."""
    _text("selected_candidate_id", result.selected_candidate_id)
    _text("launch_site_mgrs", result.launch_site_mgrs, mgrs=True)
    _text("target_mgrs", result.target_mgrs, mgrs=True)
    if not isinstance(result._config, RealTerrainMinimumAltitudeConfig):
        raise RealTerrainMinimumAltitudeOutputError("private config authority is invalid.")
    if not isinstance(result._terrain_metadata, TerrainDatasetMetadata):
        raise RealTerrainMinimumAltitudeOutputError("private terrain metadata authority is invalid.")
    if not isinstance(result._selected_projected_point, LocalPoint):
        raise RealTerrainMinimumAltitudeOutputError("private selected projected authority is invalid.")
    if not isinstance(result._source_route_result, RealTerrainRouteResult):
        raise RealTerrainMinimumAltitudeOutputError("private source route authority is invalid.")
    if not isinstance(result._selected_launch_site, SelectedLaunchSiteRecord):
        raise RealTerrainMinimumAltitudeOutputError("private selected launch authority is invalid.")
    if not isinstance(result.route_results, tuple) or not isinstance(result.warnings, tuple):
        raise RealTerrainMinimumAltitudeOutputError("result collections must be tuples.")
    if not isinstance(result._source_route_authority, tuple) or not isinstance(result._prepared_routes, tuple):
        raise RealTerrainMinimumAltitudeOutputError("private authority collections must be tuples.")
    if not isinstance(result.summary, RealTerrainMinimumAltitudeSummary) or not result.route_results:
        raise RealTerrainMinimumAltitudeOutputError("route results and summary are required.")
    try:
        result._config.__post_init__()
        validate_terrain_dataset_metadata(result._terrain_metadata)
    except TerrainDataError as exc:
        raise RealTerrainMinimumAltitudeOutputError("terrain metadata authority is invalid.") from exc
    if len(result._source_route_authority) != len(result.route_results) or len(result._prepared_routes) != len(result.route_results):
        raise RealTerrainMinimumAltitudeOutputError("source route authority count does not match results.")
    all_samples: list[RealTerrainRouteAltitudeSample] = []
    all_radial: list[RealTerrainRadialRequirementSample] = []
    warnings: list[str] = []
    for order, (route, source) in enumerate(zip(result.route_results, result._source_route_authority)):
        route.__post_init__()
        source.__post_init__()
        if source.source_order != order or route.source_order != order or route.route_id != source.route_id or route.mode is not source.mode or not _near(route.source_total_distance_3d_m, source.source_total_distance_3d_m, result._config.distance_tolerance_m):
            raise RealTerrainMinimumAltitudeOutputError("route source authority parity failed.")
        _validate_route_result(route, result._config)
        all_samples.extend(route.route_samples)
        all_radial.extend(radial for sample in route.route_samples for radial in sample.radial_requirement_samples)
        warnings.extend(route.warnings)
    if len({sample.route_sample_id for sample in all_samples}) != len(all_samples):
        raise RealTerrainMinimumAltitudeOutputError("route sample IDs must be globally unique.")
    if len({radial.radial_requirement_id for radial in all_radial}) != len(all_radial):
        raise RealTerrainMinimumAltitudeOutputError("radial requirement IDs must be globally unique.")
    if tuple(warnings) != result.warnings or result.summary.warnings != result.warnings:
        raise RealTerrainMinimumAltitudeOutputError("top-level warning/summary parity failed.")
    result.summary.__post_init__()
    if result.summary.route_count != len(result.route_results) or result.summary.route_sample_count != len(all_samples) or result.summary.radial_requirement_count != len(all_radial):
        raise RealTerrainMinimumAltitudeOutputError("summary count parity failed.")


def _validate_route_result(route: RealTerrainRouteMinimumAltitudeResult, config: RealTerrainMinimumAltitudeConfig) -> None:
    tolerance = config.distance_tolerance_m
    if route.route_id != f"route-{route.mode.value}":
        raise RealTerrainMinimumAltitudeOutputError("route identity formula failed.")
    if not _near(route.required_fresnel_clearance_ratio, config.required_fresnel_clearance_ratio, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route clearance-ratio authority failed.")
    if route.profile_spacing_m <= 0.0 or route.launch_antenna_msl_m != route.actual_launch_ground_msl_m + route.allowed_flight_agl_m:
        raise RealTerrainMinimumAltitudeOutputError("route launch formula failed.")
    if tuple(sample.route_sample_index for sample in route.route_samples) != tuple(range(len(route.route_samples))):
        raise RealTerrainMinimumAltitudeOutputError("route sample order failed.")
    if len({sample.route_sample_id for sample in route.route_samples}) != len(route.route_samples):
        raise RealTerrainMinimumAltitudeOutputError("route sample IDs must be unique.")
    expected_warnings: list[str] = []
    for sample in route.route_samples:
        _validate_route_sample(sample, route, config)
    constant = _maximum_required(route.route_samples, tolerance)
    deficit = _minimum_margin(route.route_samples, tolerance)
    if route.constant_msl_limiting_sample_id != constant.route_sample_id or not _near(route.minimum_required_constant_route_msl_m, constant.required_endpoint_msl_m, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("constant-MSL limiting formula failed.")
    if route.current_agl_deficit_limiting_sample_id != deficit.route_sample_id or not _near(route.minimum_current_clearance_margin_m, deficit.current_clearance_margin_m, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("current-margin limiting formula failed.")
    if route.current_fixed_agl_meets_proxy != (deficit.current_clearance_margin_m >= -tolerance):
        raise RealTerrainMinimumAltitudeOutputError("current fixed-AGL status formula failed.")
    highest = max(sample.local_dem_msl_m for sample in route.route_samples)
    target = route.route_samples[-1].local_dem_msl_m
    if not _near(route.highest_route_dem_msl_m, highest, tolerance) or not _near(route.target_dem_msl_m, target, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route DEM authority failed.")
    if route.agl_over_highest_route_dem_m < -tolerance or route.agl_over_target_dem_m < -tolerance:
        raise RealTerrainMinimumAltitudeOutputError("route AGL must be nonnegative.")
    if not _near(route.agl_over_highest_route_dem_m, max(0.0, route.minimum_required_constant_route_msl_m - highest), tolerance) or not _near(route.agl_over_target_dem_m, max(0.0, route.minimum_required_constant_route_msl_m - target), tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route AGL formula failed.")
    if deficit.current_clearance_margin_m < -tolerance:
        expected_warnings.append(f"{route.route_id}: current fixed-AGL route is below the configured clearance proxy at one or more route samples.")
    if constant.is_snapped_target_endpoint:
        expected_warnings.append(f"{route.route_id}: constant-MSL limiting sample is the snapped target endpoint.")
    if deficit.is_snapped_target_endpoint:
        expected_warnings.append(f"{route.route_id}: current-AGL deficit-limiting sample is the snapped target endpoint.")
    if tuple(expected_warnings) != route.warnings:
        raise RealTerrainMinimumAltitudeOutputError("route warning order/formula failed.")


def _validate_route_sample(sample: RealTerrainRouteAltitudeSample, route: RealTerrainRouteMinimumAltitudeResult, config: RealTerrainMinimumAltitudeConfig) -> None:
    tolerance = config.distance_tolerance_m
    sample.__post_init__()
    if sample.route_id != route.route_id or sample.mode is not route.mode or sample.route_sample_id != f"{route.route_id}-sample-{sample.route_sample_index:03d}":
        raise RealTerrainMinimumAltitudeOutputError("route sample identity parity failed.")
    if not _near(sample.current_route_flight_msl_m, sample.local_dem_msl_m + route.allowed_flight_agl_m, tolerance) or not _near(sample.current_clearance_margin_m, sample.current_route_flight_msl_m - sample.required_endpoint_msl_m, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route sample formula failed.")
    if sample.sample_semantics == "coincident_launch_occupancy":
        if not _near(sample.required_endpoint_msl_m, route.launch_antenna_msl_m, tolerance):
            raise RealTerrainMinimumAltitudeOutputError("coincident sample formula failed.")
        return
    radial = _maximum_radial(sample.radial_requirement_samples, tolerance)
    if sample.limiting_radial_requirement != radial or not _near(sample.required_endpoint_msl_m, radial.required_endpoint_msl_m, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("radial limiting formula failed.")
    for requirement in sample.radial_requirement_samples:
        requirement.__post_init__()
        _validate_radial_requirement(requirement, sample, route, config)


def _validate_radial_requirement(requirement: RealTerrainRadialRequirementSample, sample: RealTerrainRouteAltitudeSample, route: RealTerrainRouteMinimumAltitudeResult, config: RealTerrainMinimumAltitudeConfig) -> None:
    tolerance = config.distance_tolerance_m
    if requirement.route_sample_id != sample.route_sample_id or requirement.radial_requirement_id != f"{sample.route_sample_id}-radial-{requirement.radial_sample_index:03d}":
        raise RealTerrainMinimumAltitudeOutputError("radial requirement identity parity failed.")
    total = requirement.distance_from_launch_m + requirement.distance_to_endpoint_m
    if total <= 0.0 or requirement.path_ratio <= config.epsilon_m or not _near(requirement.path_ratio, requirement.distance_from_launch_m / total, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("radial path-ratio formula failed.")
    if not _near(requirement.required_clearance_m, route.required_fresnel_clearance_ratio * requirement.fresnel_radius_m, tolerance) or not _near(requirement.required_los_msl_m, requirement.dsm_msl_m + requirement.required_clearance_m, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("radial clearance formula failed.")
    expected_endpoint = route.launch_antenna_msl_m + (requirement.required_los_msl_m - route.launch_antenna_msl_m) / requirement.path_ratio
    if not _near(requirement.required_endpoint_msl_m, expected_endpoint, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("radial endpoint formula failed.")


def _maximum_radial(items: tuple[RealTerrainRadialRequirementSample, ...], tolerance: float) -> RealTerrainRadialRequirementSample:
    best = items[0]
    for item in items[1:]:
        difference = item.required_endpoint_msl_m - best.required_endpoint_msl_m
        if difference > tolerance or (abs(difference) <= tolerance and item.radial_sample_index < best.radial_sample_index):
            best = item
    return best


def _maximum_required(items: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float) -> RealTerrainRouteAltitudeSample:
    best = items[0]
    for item in items[1:]:
        difference = item.required_endpoint_msl_m - best.required_endpoint_msl_m
        key = (item.cumulative_route_distance_2d_m, item.route_sample_index, -1 if item.limiting_radial_requirement is None else item.limiting_radial_requirement.radial_sample_index)
        best_key = (best.cumulative_route_distance_2d_m, best.route_sample_index, -1 if best.limiting_radial_requirement is None else best.limiting_radial_requirement.radial_sample_index)
        if difference > tolerance or (abs(difference) <= tolerance and key < best_key):
            best = item
    return best


def _minimum_margin(items: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float) -> RealTerrainRouteAltitudeSample:
    best = items[0]
    for item in items[1:]:
        difference = item.current_clearance_margin_m - best.current_clearance_margin_m
        if difference < -tolerance or (abs(difference) <= tolerance and (item.cumulative_route_distance_2d_m, item.route_sample_index) < (best.cumulative_route_distance_2d_m, best.route_sample_index)):
            best = item
    return best


def _sample_by_id(route: RealTerrainRouteMinimumAltitudeResult, sample_id: str) -> RealTerrainRouteAltitudeSample:
    for sample in route.route_samples:
        if sample.route_sample_id == sample_id:
            return sample
    raise RealTerrainMinimumAltitudeOutputError("limiting sample ID is not present in route samples.")
