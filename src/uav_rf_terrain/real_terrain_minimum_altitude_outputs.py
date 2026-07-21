"""Immutable MGRS-facing Task 036B output contracts and recursive validators."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from ._minimum_altitude_selection import (
    MinimumAltitudeSelectionError,
    select_tolerance_representative,
)
from .coordinates import LocalPoint
from .real_terrain_route_outputs import RouteMode
from .terrain_data import (
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
    validate_terrain_dataset_metadata,
)


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


def _validate_exact_terrain_metadata(metadata: object) -> TerrainDatasetMetadata:
    """Rerun reviewed metadata validators after frozen-record mutation attempts."""

    if type(metadata) is not TerrainDatasetMetadata:
        raise RealTerrainMinimumAltitudeOutputError("private terrain metadata authority is invalid.")
    if type(metadata.dem) is not TerrainRasterMetadata or type(metadata.dsm) is not TerrainRasterMetadata:
        raise RealTerrainMinimumAltitudeOutputError("private terrain raster metadata authority is invalid.")
    _preflight_terrain_metadata_fields(metadata)
    try:
        metadata.dem.__post_init__()
        metadata.dsm.__post_init__()
        metadata.__post_init__()
        validate_terrain_dataset_metadata(metadata)
    except TerrainDataError as exc:
        raise RealTerrainMinimumAltitudeOutputError("private terrain metadata authority is invalid.") from exc
    return metadata


def _preflight_terrain_metadata_fields(metadata: TerrainDatasetMetadata) -> None:
    """Reject malformed metadata primitives before reviewed validators dereference them."""

    if any(
        type(value) is not str
        for value in (
            metadata.dataset_name,
            metadata.processing_date,
            metadata.processing_tool,
            metadata.alignment_status,
            metadata.notes,
        )
    ):
        raise RealTerrainMinimumAltitudeOutputError("private terrain metadata authority is invalid.")
    for raster in (metadata.dem, metadata.dsm):
        if any(
            type(value) is not str
            for value in (
                raster.name,
                raster.raster_type,
                raster.source_dataset_name,
                raster.source_provider,
                raster.license_or_terms,
                raster.crs,
                raster.vertical_datum,
                raster.processing_summary,
            )
        ):
            raise RealTerrainMinimumAltitudeOutputError("private terrain raster metadata authority is invalid.")
        if (
            isinstance(raster.resolution_m, bool)
            or not isinstance(raster.resolution_m, (int, float))
            or not isfinite(raster.resolution_m)
            or isinstance(raster.width, bool)
            or not isinstance(raster.width, int)
            or isinstance(raster.height, bool)
            or not isinstance(raster.height, int)
            or type(raster.bounds) is not tuple
            or len(raster.bounds) != 4
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                for value in raster.bounds
            )
            or (
                raster.nodata_value is not None
                and (
                    isinstance(raster.nodata_value, bool)
                    or not isinstance(raster.nodata_value, (int, float))
                    or not isfinite(raster.nodata_value)
                )
            )
            or type(raster.is_synthetic) is not bool
            or type(raster.is_redistributable_processed_data) is not bool
        ):
            raise RealTerrainMinimumAltitudeOutputError("private terrain raster metadata authority is invalid.")


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
class RealTerrainMinimumAltitudeProfileSampleSnapshot:
    """Independent immutable profile cell retained only for result validation."""

    sample_index: int
    point: LocalPoint
    distance_from_start_m: float
    distance_to_end_m: float
    dem_msl_m: float
    dsm_msl_m: float
    surface_delta_m: float


@dataclass(frozen=True)
class RealTerrainMinimumAltitudeProfileSnapshot:
    scenario_name: str
    start: LocalPoint
    end: LocalPoint
    sample_spacing_m: float
    samples: tuple[RealTerrainMinimumAltitudeProfileSampleSnapshot, ...]


@dataclass(frozen=True)
class RealTerrainMinimumAltitudePreparedSampleSnapshot:
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
    radial_profile: RealTerrainMinimumAltitudeProfileSnapshot | None


@dataclass(frozen=True)
class RealTerrainMinimumAltitudePreparedRouteSnapshot:
    route_id: str
    mode: RouteMode
    source_order: int
    source_total_distance_3d_m: float
    route_polyline_total_distance_2d_m: float
    samples: tuple[RealTerrainMinimumAltitudePreparedSampleSnapshot, ...]


@dataclass(frozen=True)
class RealTerrainMinimumAltitudeAuthoritySnapshot:
    """Compact independent evidence snapshot; never exposed through public output."""

    selected_candidate_id: str
    launch_site_mgrs: str
    target_mgrs: str
    selected_projected_point: LocalPoint
    config: RealTerrainMinimumAltitudeConfig
    frequency_hz: float
    allowed_flight_agl_m: float
    source_profile_spacing_m: float
    resolved_profile_spacing_m: float
    launch_ground_msl_m: float
    terrain_metadata: TerrainDatasetMetadata
    source_routes: tuple[RealTerrainMinimumAltitudeSourceRoute, ...]
    prepared_routes: tuple[RealTerrainMinimumAltitudePreparedRouteSnapshot, ...]


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
        if type(self.radial_requirement_samples) is not tuple:
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
        if type(self.route_samples) is not tuple or type(self.warnings) is not tuple:
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
        if type(self.warnings) is not tuple:
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
    _authority: RealTerrainMinimumAltitudeAuthoritySnapshot
    _authority_fingerprint: str
    _output_fingerprint: str

    def __post_init__(self) -> None:
        validate_real_terrain_minimum_altitude_result(self)

    def to_public_dict(self) -> dict[str, object]:
        """Return MGRS-facing proxy output without projected/profile/raster details."""
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "launch_site_mgrs": self.launch_site_mgrs,
            "target_mgrs": self.target_mgrs,
            "distance_tolerance_m": self._authority.config.distance_tolerance_m,
            "limiter_semantics": "canonical_extreme_tolerance_representative",
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
    if type(result) is not RealTerrainMinimumAltitudeResult:
        raise RealTerrainMinimumAltitudeOutputError("result type is invalid.")
    _text("selected_candidate_id", result.selected_candidate_id)
    _text("launch_site_mgrs", result.launch_site_mgrs, mgrs=True)
    _text("target_mgrs", result.target_mgrs, mgrs=True)
    if type(result._authority) is not RealTerrainMinimumAltitudeAuthoritySnapshot:
        raise RealTerrainMinimumAltitudeOutputError("private authority snapshot is invalid.")
    if not isinstance(result._authority_fingerprint, str) or not result._authority_fingerprint:
        raise RealTerrainMinimumAltitudeOutputError("private authority fingerprint is invalid.")
    if type(result.route_results) is not tuple or type(result.warnings) is not tuple:
        raise RealTerrainMinimumAltitudeOutputError("result collections must be tuples.")
    if type(result.summary) is not RealTerrainMinimumAltitudeSummary or not result.route_results:
        raise RealTerrainMinimumAltitudeOutputError("route results and summary are required.")
    _preflight_output_nested_types(result)
    result._authority.config.__post_init__()
    _validate_exact_terrain_metadata(result._authority.terrain_metadata)
    if (
        type(result._authority.source_routes) is not tuple
        or type(result._authority.prepared_routes) is not tuple
        or len(result._authority.source_routes) != len(result.route_results)
        or len(result._authority.prepared_routes) != len(result.route_results)
    ):
        raise RealTerrainMinimumAltitudeOutputError("source route authority count does not match results.")
    all_samples: list[RealTerrainRouteAltitudeSample] = []
    all_radial: list[RealTerrainRadialRequirementSample] = []
    warnings: list[str] = []
    for order, (route, source) in enumerate(zip(result.route_results, result._authority.source_routes)):
        if type(route) is not RealTerrainRouteMinimumAltitudeResult:
            raise RealTerrainMinimumAltitudeOutputError("output route type is invalid.")
        if type(source) is not RealTerrainMinimumAltitudeSourceRoute:
            raise RealTerrainMinimumAltitudeOutputError("source route snapshot type is invalid.")
        route.__post_init__()
        source.__post_init__()
        if source.source_order != order or route.source_order != order or route.route_id != source.route_id or route.mode is not source.mode or not _near(route.source_total_distance_3d_m, source.source_total_distance_3d_m, result._authority.config.distance_tolerance_m):
            raise RealTerrainMinimumAltitudeOutputError("route source authority parity failed.")
        _validate_route_result(route, result._authority.config)
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


def _preflight_output_nested_types(result: RealTerrainMinimumAltitudeResult) -> None:
    """Check exact replay inputs before dataclass validators or selector callbacks."""

    authority = result._authority
    if type(authority.config) is not RealTerrainMinimumAltitudeConfig:
        raise RealTerrainMinimumAltitudeOutputError("private authority config is invalid.")
    if type(authority.source_routes) is not tuple or type(authority.prepared_routes) is not tuple:
        raise RealTerrainMinimumAltitudeOutputError("private authority collections are invalid.")
    if any(type(warning) is not str for warning in result.warnings):
        raise RealTerrainMinimumAltitudeOutputError("result warnings must be text.")
    if type(result.summary.warnings) is not tuple or any(
        type(warning) is not str for warning in result.summary.warnings
    ):
        raise RealTerrainMinimumAltitudeOutputError("summary warnings must be text.")
    if any(type(source) is not RealTerrainMinimumAltitudeSourceRoute for source in authority.source_routes):
        raise RealTerrainMinimumAltitudeOutputError("source route snapshot type is invalid.")
    for route in result.route_results:
        if type(route) is not RealTerrainRouteMinimumAltitudeResult:
            raise RealTerrainMinimumAltitudeOutputError("output route type is invalid.")
        if type(route.route_samples) is not tuple or type(route.warnings) is not tuple:
            raise RealTerrainMinimumAltitudeOutputError("output route collections are invalid.")
        if any(type(warning) is not str for warning in route.warnings):
            raise RealTerrainMinimumAltitudeOutputError("output route warnings must be text.")
        for sample in route.route_samples:
            if type(sample) is not RealTerrainRouteAltitudeSample:
                raise RealTerrainMinimumAltitudeOutputError("output route sample type is invalid.")
            if type(sample.radial_requirement_samples) is not tuple:
                raise RealTerrainMinimumAltitudeOutputError("output radial collection is invalid.")
            if any(
                type(requirement) is not RealTerrainRadialRequirementSample
                for requirement in sample.radial_requirement_samples
            ):
                raise RealTerrainMinimumAltitudeOutputError("output radial requirement type is invalid.")


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
    exact_constant, constant = _select_constant_msl_extreme(route.route_samples, tolerance)
    exact_margin, deficit = _select_current_margin_extreme(route.route_samples, tolerance)
    if route.constant_msl_limiting_sample_id != constant.route_sample_id or route.minimum_required_constant_route_msl_m != exact_constant:
        raise RealTerrainMinimumAltitudeOutputError("constant-MSL limiting formula failed.")
    if route.current_agl_deficit_limiting_sample_id != deficit.route_sample_id or route.minimum_current_clearance_margin_m != exact_margin:
        raise RealTerrainMinimumAltitudeOutputError("current-margin limiting formula failed.")
    if route.current_fixed_agl_meets_proxy != (exact_margin >= -tolerance):
        raise RealTerrainMinimumAltitudeOutputError("current fixed-AGL status formula failed.")
    highest = max(sample.local_dem_msl_m for sample in route.route_samples)
    target = route.route_samples[-1].local_dem_msl_m
    if not _near(route.highest_route_dem_msl_m, highest, tolerance) or not _near(route.target_dem_msl_m, target, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route DEM authority failed.")
    if route.agl_over_highest_route_dem_m < -tolerance or route.agl_over_target_dem_m < -tolerance:
        raise RealTerrainMinimumAltitudeOutputError("route AGL must be nonnegative.")
    if not _near(route.agl_over_highest_route_dem_m, max(0.0, route.minimum_required_constant_route_msl_m - highest), tolerance) or not _near(route.agl_over_target_dem_m, max(0.0, route.minimum_required_constant_route_msl_m - target), tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route AGL formula failed.")
    if exact_margin < -tolerance:
        expected_warnings.append(f"{route.route_id}: current fixed-AGL route is below the configured clearance proxy at one or more route samples.")
    if constant.is_snapped_target_endpoint:
        expected_warnings.append(f"{route.route_id}: constant-MSL limiting sample is the snapped target endpoint.")
    if deficit.is_snapped_target_endpoint:
        expected_warnings.append(f"{route.route_id}: current-AGL deficit-limiting sample is the snapped target endpoint.")
    if tuple(expected_warnings) != route.warnings:
        raise RealTerrainMinimumAltitudeOutputError("route warning order/formula failed.")


def _validate_route_sample(sample: RealTerrainRouteAltitudeSample, route: RealTerrainRouteMinimumAltitudeResult, config: RealTerrainMinimumAltitudeConfig) -> None:
    tolerance = config.distance_tolerance_m
    if type(sample) is not RealTerrainRouteAltitudeSample:
        raise RealTerrainMinimumAltitudeOutputError("output route sample type is invalid.")
    sample.__post_init__()
    if sample.route_id != route.route_id or sample.mode is not route.mode or sample.route_sample_id != f"{route.route_id}-sample-{sample.route_sample_index:03d}":
        raise RealTerrainMinimumAltitudeOutputError("route sample identity parity failed.")
    if not _near(sample.current_route_flight_msl_m, sample.local_dem_msl_m + route.allowed_flight_agl_m, tolerance) or not _near(sample.current_clearance_margin_m, sample.current_route_flight_msl_m - sample.required_endpoint_msl_m, tolerance):
        raise RealTerrainMinimumAltitudeOutputError("route sample formula failed.")
    if sample.sample_semantics == "coincident_launch_occupancy":
        if not _near(sample.required_endpoint_msl_m, route.launch_antenna_msl_m, tolerance):
            raise RealTerrainMinimumAltitudeOutputError("coincident sample formula failed.")
        return
    exact_radial, radial = _select_radial_extreme(sample.radial_requirement_samples, tolerance)
    if sample.limiting_radial_requirement != radial or sample.required_endpoint_msl_m != exact_radial:
        raise RealTerrainMinimumAltitudeOutputError("radial limiting formula failed.")
    for requirement in sample.radial_requirement_samples:
        if type(requirement) is not RealTerrainRadialRequirementSample:
            raise RealTerrainMinimumAltitudeOutputError("output radial requirement type is invalid.")
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
    return _select_radial_extreme(items, tolerance)[1]


def _select_radial_extreme(
    items: tuple[RealTerrainRadialRequirementSample, ...], tolerance: float
) -> tuple[float, RealTerrainRadialRequirementSample]:
    try:
        return select_tolerance_representative(
            items,
            value=lambda item: item.required_endpoint_msl_m,
            tie_key=lambda item: item.radial_sample_index,
            tolerance=tolerance,
            maximize=True,
        )
    except MinimumAltitudeSelectionError as exc:
        raise RealTerrainMinimumAltitudeOutputError("radial limiter selection is invalid.") from exc


def _maximum_required(items: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float) -> RealTerrainRouteAltitudeSample:
    return _select_constant_msl_extreme(items, tolerance)[1]


def _select_constant_msl_extreme(
    items: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float
) -> tuple[float, RealTerrainRouteAltitudeSample]:
    try:
        return select_tolerance_representative(
            items,
            value=lambda item: item.required_endpoint_msl_m,
            tie_key=lambda item: (
                item.cumulative_route_distance_2d_m,
                item.route_sample_index,
                -1
                if item.limiting_radial_requirement is None
                else item.limiting_radial_requirement.radial_sample_index,
            ),
            tolerance=tolerance,
            maximize=True,
        )
    except MinimumAltitudeSelectionError as exc:
        raise RealTerrainMinimumAltitudeOutputError("constant-MSL limiter selection is invalid.") from exc


def _minimum_margin(items: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float) -> RealTerrainRouteAltitudeSample:
    return _select_current_margin_extreme(items, tolerance)[1]


def _select_current_margin_extreme(
    items: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float
) -> tuple[float, RealTerrainRouteAltitudeSample]:
    try:
        return select_tolerance_representative(
            items,
            value=lambda item: item.current_clearance_margin_m,
            tie_key=lambda item: (item.cumulative_route_distance_2d_m, item.route_sample_index),
            tolerance=tolerance,
            maximize=False,
        )
    except MinimumAltitudeSelectionError as exc:
        raise RealTerrainMinimumAltitudeOutputError("current-margin limiter selection is invalid.") from exc


def _sample_by_id(route: RealTerrainRouteMinimumAltitudeResult, sample_id: str) -> RealTerrainRouteAltitudeSample:
    for sample in route.route_samples:
        if sample.route_sample_id == sample_id:
            return sample
    raise RealTerrainMinimumAltitudeOutputError("limiting sample ID is not present in route samples.")
