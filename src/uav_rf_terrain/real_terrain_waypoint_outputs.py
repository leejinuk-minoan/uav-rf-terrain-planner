"""Immutable MGRS-facing output contracts for real-terrain waypoint reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import floor, isfinite

from .coordinates import LocalPoint
from .real_terrain_candidate_analysis import SourceZoneAvailability
from .real_terrain_route_outputs import RouteMode
from .schemas import ColorClass
from .source_zones import TerrainSourceZone


class RealTerrainWaypointOutputError(ValueError):
    """Raised when a real-terrain waypoint report contract is invalid."""


class WaypointValueSemantics(StrEnum):
    """How a waypoint risk and score values were obtained."""

    SOURCE_NODE = "source_node"
    SEGMENT_CONSERVATIVE_PROXY = "segment_conservative_proxy"


class WaypointElevationSemantics(StrEnum):
    """How a waypoint elevation values were obtained."""

    SOURCE_NODE = "source_node"
    ENDPOINT_LINEAR_INTERPOLATION = "endpoint_linear_interpolation"


@dataclass(frozen=True)
class RealTerrainWaypointConfig:
    """Bounded deterministic configuration for route waypoint reporting."""

    spacing_m: float = 500.0
    include_start: bool = True
    include_end: bool = True
    mgrs_precision: int = 5
    distance_tolerance_m: float = 1e-9
    max_waypoints_per_route: int = 10_000
    max_total_waypoints: int = 30_000

    def __post_init__(self) -> None:
        _positive_finite("spacing_m", self.spacing_m)
        _positive_finite("distance_tolerance_m", self.distance_tolerance_m)
        if not isinstance(self.include_start, bool) or not isinstance(self.include_end, bool):
            raise RealTerrainWaypointOutputError("include_start and include_end must be bool values.")
        if isinstance(self.mgrs_precision, bool) or self.mgrs_precision != 5:
            raise RealTerrainWaypointOutputError("mgrs_precision is locked to 5.")
        for name, value in (
            ("max_waypoints_per_route", self.max_waypoints_per_route),
            ("max_total_waypoints", self.max_total_waypoints),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise RealTerrainWaypointOutputError(f"{name} must be a positive integer.")


@dataclass(frozen=True)
class RealTerrainWaypointRecord:
    """One deterministic route-report waypoint with internal projection retained privately."""

    waypoint_id: str
    route_id: str
    route_mode: RouteMode
    sequence_index: int
    target_interval_index: int | None
    projected_point: LocalPoint
    mgrs: str
    cumulative_distance_3d_m: float
    segment_distance_from_previous_3d_m: float
    terrain_msl_m: float
    surface_msl_m: float
    flight_agl_m: float
    flight_msl_m: float
    height_difference_from_launch_m: float
    color_class: ColorClass
    shielding_stability_score: float
    overall_score: float
    value_semantics: WaypointValueSemantics
    elevation_semantics: WaypointElevationSemantics
    left_source_point_id: str
    right_source_point_id: str
    interpolation_fraction: float
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.route_mode, RouteMode) or not isinstance(self.projected_point, LocalPoint):
            raise RealTerrainWaypointOutputError("route mode and projected point are invalid.")
        expected_id = f"route-{self.route_mode.value}-wp-{self.sequence_index:03d}"
        if (
            not isinstance(self.waypoint_id, str)
            or self.waypoint_id != expected_id
            or self.route_id != f"route-{self.route_mode.value}"
        ):
            raise RealTerrainWaypointOutputError("waypoint identity must follow the route mode and sequence.")
        if isinstance(self.sequence_index, bool) or not isinstance(self.sequence_index, int) or self.sequence_index < 0:
            raise RealTerrainWaypointOutputError("sequence_index must be a non-negative integer.")
        if self.target_interval_index is not None and (
            isinstance(self.target_interval_index, bool)
            or not isinstance(self.target_interval_index, int)
            or self.target_interval_index < 0
        ):
            raise RealTerrainWaypointOutputError("target_interval_index must be non-negative when present.")
        if not isinstance(self.mgrs, str) or not self.mgrs.strip() or self.mgrs != self.mgrs.strip().upper():
            raise RealTerrainWaypointOutputError("mgrs must be non-empty uppercase text.")
        for name, value in (
            ("cumulative_distance_3d_m", self.cumulative_distance_3d_m),
            ("segment_distance_from_previous_3d_m", self.segment_distance_from_previous_3d_m),
            ("terrain_msl_m", self.terrain_msl_m),
            ("surface_msl_m", self.surface_msl_m),
            ("flight_agl_m", self.flight_agl_m),
            ("flight_msl_m", self.flight_msl_m),
            ("height_difference_from_launch_m", self.height_difference_from_launch_m),
            ("shielding_stability_score", self.shielding_stability_score),
            ("overall_score", self.overall_score),
            ("interpolation_fraction", self.interpolation_fraction),
        ):
            _finite(name, value)
        if self.cumulative_distance_3d_m < 0 or self.segment_distance_from_previous_3d_m < 0:
            raise RealTerrainWaypointOutputError("waypoint distances must be non-negative.")
        if self.surface_msl_m < self.terrain_msl_m or self.flight_msl_m < self.surface_msl_m:
            raise RealTerrainWaypointOutputError("waypoint elevation ordering must be terrain <= surface <= flight.")
        if self.flight_agl_m < 0 or abs(self.flight_msl_m - (self.terrain_msl_m + self.flight_agl_m)) > 1e-9:
            raise RealTerrainWaypointOutputError("waypoint flight MSL must equal terrain plus AGL.")
        if self.color_class is ColorClass.EXCLUDED or not isinstance(self.color_class, ColorClass):
            raise RealTerrainWaypointOutputError("waypoint color must be non-excluded.")
        _score("shielding_stability_score", self.shielding_stability_score)
        _score("overall_score", self.overall_score)
        if not isinstance(self.value_semantics, WaypointValueSemantics) or not isinstance(
            self.elevation_semantics, WaypointElevationSemantics
        ):
            raise RealTerrainWaypointOutputError("waypoint semantics are invalid.")
        if (
            not isinstance(self.left_source_point_id, str)
            or not isinstance(self.right_source_point_id, str)
            or not self.left_source_point_id.strip()
            or not self.right_source_point_id.strip()
            or self.left_source_point_id != self.left_source_point_id.strip()
            or self.right_source_point_id != self.right_source_point_id.strip()
        ):
            raise RealTerrainWaypointOutputError("waypoint source references must be non-empty stripped text.")
        exact = self.value_semantics is WaypointValueSemantics.SOURCE_NODE
        if exact != (self.elevation_semantics is WaypointElevationSemantics.SOURCE_NODE):
            raise RealTerrainWaypointOutputError("value and elevation semantics must agree for exact waypoints.")
        if exact and (
            self.left_source_point_id != self.right_source_point_id
            or abs(self.interpolation_fraction) > 1e-9
        ):
            raise RealTerrainWaypointOutputError("exact source waypoints must reference one source point.")
        if not exact and (
            self.left_source_point_id == self.right_source_point_id
            or not 0.0 < self.interpolation_fraction < 1.0
            or self.elevation_semantics
            is not WaypointElevationSemantics.ENDPOINT_LINEAR_INTERPOLATION
        ):
            raise RealTerrainWaypointOutputError("interpolated waypoints require strict interior bracketing.")
        if (
            self.source_zone is not None
            or self.source_zone_state is not SourceZoneAvailability.NOT_REQUESTED
            or self.source_sensitive is not None
            or self.source_zone_reason != "source-zone provider not requested"
        ):
            raise RealTerrainWaypointOutputError("route waypoint source-zone policy must remain not requested.")


@dataclass(frozen=True)
class RealTerrainRouteWaypointReport:
    """Waypoint report for one available route candidate."""

    route_id: str
    route_mode: RouteMode
    path_semantics: str
    waypoint_spacing_m: float
    total_route_distance_3d_m: float
    waypoints: tuple[RealTerrainWaypointRecord, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.route_mode, RouteMode) or self.route_id != f"route-{self.route_mode.value}":
            raise RealTerrainWaypointOutputError("route report identity is invalid.")
        if self.path_semantics != "snapped_graph_path":
            raise RealTerrainWaypointOutputError("route report must retain snapped_graph_path semantics.")
        _positive_finite("waypoint_spacing_m", self.waypoint_spacing_m)
        _non_negative_finite("total_route_distance_3d_m", self.total_route_distance_3d_m)
        if (
            not self.waypoints
            or len(set(self.warnings)) != len(self.warnings)
            or any(not isinstance(warning, str) or not warning.strip() for warning in self.warnings)
        ):
            raise RealTerrainWaypointOutputError("route report waypoints and warnings are invalid.")
        previous: RealTerrainWaypointRecord | None = None
        for index, waypoint in enumerate(self.waypoints):
            if not isinstance(waypoint, RealTerrainWaypointRecord) or waypoint.route_id != self.route_id:
                raise RealTerrainWaypointOutputError("route report waypoint route parity is invalid.")
            waypoint.__post_init__()
            if waypoint.sequence_index != index:
                raise RealTerrainWaypointOutputError("route report waypoint sequence is not contiguous.")
            if previous is not None:
                if waypoint.cumulative_distance_3d_m < previous.cumulative_distance_3d_m:
                    raise RealTerrainWaypointOutputError("route report waypoint distances must be ordered.")
                if abs(
                    waypoint.segment_distance_from_previous_3d_m
                    - (waypoint.cumulative_distance_3d_m - previous.cumulative_distance_3d_m)
                ) > 1e-9:
                    raise RealTerrainWaypointOutputError("route report segment distance is inconsistent.")
            elif abs(waypoint.segment_distance_from_previous_3d_m) > 1e-9:
                raise RealTerrainWaypointOutputError("first waypoint segment distance must be zero.")
            previous = waypoint


@dataclass(frozen=True)
class RealTerrainWaypointSummary:
    route_count: int
    waypoint_count: int
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.route_count, self.waypoint_count):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise RealTerrainWaypointOutputError("summary counts must be non-negative integers.")
        if len(set(self.warnings)) != len(self.warnings) or any(
            not isinstance(warning, str) or not warning.strip() for warning in self.warnings
        ):
            raise RealTerrainWaypointOutputError("summary warnings must be unique.")


@dataclass(frozen=True)
class RealTerrainWaypointResult:
    """Complete immutable output for all available route waypoint reports."""

    scenario_name: str
    mission_id: str
    selected_candidate_id: str
    launch_site_mgrs: str
    target_mgrs: str
    config: RealTerrainWaypointConfig
    launch_ground_msl_m: float
    source_route_ids: tuple[str, ...]
    source_route_modes: tuple[RouteMode, ...]
    source_route_total_distance_3d_m: tuple[float, ...]
    snapped_launch_node_mgrs: str
    snapped_target_node_mgrs: str
    route_reports: tuple[RealTerrainRouteWaypointReport, ...]
    summary: RealTerrainWaypointSummary
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("scenario_name", self.scenario_name),
            ("mission_id", self.mission_id),
            ("selected_candidate_id", self.selected_candidate_id),
            ("launch_site_mgrs", self.launch_site_mgrs),
            ("target_mgrs", self.target_mgrs),
        ):
            if not isinstance(value, str) or not value.strip():
                raise RealTerrainWaypointOutputError(f"{name} must be non-empty.")
        if self.launch_site_mgrs != self.launch_site_mgrs.upper() or self.target_mgrs != self.target_mgrs.upper():
            raise RealTerrainWaypointOutputError("result MGRS must be uppercase.")
        if not isinstance(self.config, RealTerrainWaypointConfig) or not self.route_reports:
            raise RealTerrainWaypointOutputError("result config and route reports are required.")
        self.config.__post_init__()
        _finite("launch_ground_msl_m", self.launch_ground_msl_m)
        _validate_mgrs("snapped_launch_node_mgrs", self.snapped_launch_node_mgrs)
        _validate_mgrs("snapped_target_node_mgrs", self.snapped_target_node_mgrs)
        if not (
            len(self.source_route_ids)
            == len(self.source_route_modes)
            == len(self.source_route_total_distance_3d_m)
            == len(self.route_reports)
        ):
            raise RealTerrainWaypointOutputError("source route authority lengths must match reports.")
        if len(set(self.source_route_ids)) != len(self.source_route_ids):
            raise RealTerrainWaypointOutputError("source route IDs must be unique.")
        if not isinstance(self.summary, RealTerrainWaypointSummary):
            raise RealTerrainWaypointOutputError("result summary is invalid.")
        self.summary.__post_init__()
        if any(not isinstance(report, RealTerrainRouteWaypointReport) for report in self.route_reports):
            raise RealTerrainWaypointOutputError("result route reports are invalid.")
        for report in self.route_reports:
            report.__post_init__()
        if any(not isinstance(mode, RouteMode) for mode in self.source_route_modes):
            raise RealTerrainWaypointOutputError("source route modes are invalid.")
        route_order = {mode: index for index, mode in enumerate(RouteMode)}
        modes = tuple(report.route_mode for report in self.route_reports)
        if (
            len(set(modes)) != len(modes)
            or tuple(sorted(modes, key=route_order.__getitem__)) != modes
            or self.source_route_modes != modes
        ):
            raise RealTerrainWaypointOutputError("route report order must follow route mode order.")
        for index, (route_id, mode, total_distance, report) in enumerate(
            zip(
                self.source_route_ids,
                self.source_route_modes,
                self.source_route_total_distance_3d_m,
                self.route_reports,
            )
        ):
            if (
                not isinstance(mode, RouteMode)
                or not isinstance(route_id, str)
                or route_id != f"route-{mode.value}"
                or report.route_id != route_id
                or report.route_mode is not mode
            ):
                raise RealTerrainWaypointOutputError("source route identity does not match report authority.")
            _non_negative_finite(f"source_route_total_distance_3d_m[{index}]", total_distance)
            if abs(report.total_route_distance_3d_m - total_distance) > self.config.distance_tolerance_m:
                raise RealTerrainWaypointOutputError("route report total does not match source authority.")
            if abs(report.waypoint_spacing_m - self.config.spacing_m) > self.config.distance_tolerance_m:
                raise RealTerrainWaypointOutputError("route report spacing must match result config.")
            _validate_report_targets(
                report,
                source_total_distance_m=float(total_distance),
                config=self.config,
                snapped_launch_mgrs=self.snapped_launch_node_mgrs,
                snapped_target_mgrs=self.snapped_target_node_mgrs,
            )
            for waypoint in report.waypoints:
                if abs(
                    waypoint.height_difference_from_launch_m
                    - (waypoint.flight_msl_m - self.launch_ground_msl_m)
                ) > self.config.distance_tolerance_m:
                    raise RealTerrainWaypointOutputError("waypoint height difference must match launch ground authority.")
        waypoint_ids = tuple(
            waypoint.waypoint_id for report in self.route_reports for waypoint in report.waypoints
        )
        if len(set(waypoint_ids)) != len(waypoint_ids):
            raise RealTerrainWaypointOutputError("waypoint IDs must be globally unique across route reports.")
        if self.summary.route_count != len(self.route_reports) or self.summary.waypoint_count != sum(
            len(report.waypoints) for report in self.route_reports
        ):
            raise RealTerrainWaypointOutputError("result summary does not match reports.")
        expected_warnings = _stable_warning_union(tuple(report.warnings for report in self.route_reports))
        if (
            len(set(self.warnings)) != len(self.warnings)
            or any(not isinstance(warning, str) or not warning.strip() for warning in self.warnings)
            or self.warnings != expected_warnings
            or self.summary.warnings != expected_warnings
        ):
            raise RealTerrainWaypointOutputError("result warnings must be unique.")

    def to_public_dict(self) -> dict[str, object]:
        """Return MGRS-facing report values without internal projected coordinates."""

        return {
            "scenario_name": self.scenario_name,
            "mission_id": self.mission_id,
            "selected_candidate_id": self.selected_candidate_id,
            "launch_site_mgrs": self.launch_site_mgrs,
            "target_mgrs": self.target_mgrs,
            "waypoint_spacing_m": self.config.spacing_m,
            "routes": tuple(
                {
                    "route_id": report.route_id,
                    "route_mode": report.route_mode.value,
                    "total_route_distance_3d_m": report.total_route_distance_3d_m,
                    "waypoints": tuple(
                        {
                            "waypoint_id": item.waypoint_id,
                            "sequence_index": item.sequence_index,
                            "mgrs": item.mgrs,
                            "cumulative_distance_3d_m": item.cumulative_distance_3d_m,
                            "segment_distance_from_previous_3d_m": item.segment_distance_from_previous_3d_m,
                            "terrain_msl_m": item.terrain_msl_m,
                            "surface_msl_m": item.surface_msl_m,
                            "flight_agl_m": item.flight_agl_m,
                            "flight_msl_m": item.flight_msl_m,
                            "height_difference_from_launch_m": item.height_difference_from_launch_m,
                            "color_class": item.color_class.value,
                            "shielding_stability_score": item.shielding_stability_score,
                            "overall_score": item.overall_score,
                            "value_semantics": item.value_semantics.value,
                            "elevation_semantics": item.elevation_semantics.value,
                            "source_zone_state": item.source_zone_state.value,
                        }
                        for item in report.waypoints
                    ),
                    "warnings": report.warnings,
                }
                for report in self.route_reports
            ),
            "warnings": self.warnings,
        }


def _finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise RealTerrainWaypointOutputError(f"{name} must be finite.")
    return float(value)


def _positive_finite(name: str, value: object) -> None:
    if _finite(name, value) <= 0:
        raise RealTerrainWaypointOutputError(f"{name} must be positive.")


def _non_negative_finite(name: str, value: object) -> None:
    if _finite(name, value) < 0:
        raise RealTerrainWaypointOutputError(f"{name} must be non-negative.")


def _score(name: str, value: object) -> None:
    numeric = _finite(name, value)
    if numeric < 0 or numeric > 100:
        raise RealTerrainWaypointOutputError(f"{name} must be within [0, 100].")


def _validate_mgrs(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip().upper():
        raise RealTerrainWaypointOutputError(f"{name} must be non-empty uppercase MGRS text.")


def _waypoint_targets(
    total_distance_m: float, config: RealTerrainWaypointConfig
) -> tuple[tuple[float, int | None], ...]:
    """Return the reviewed target sequence without performing conversion or sampling."""

    _non_negative_finite("total_distance_m", total_distance_m)
    targets: list[tuple[float, int | None]] = []
    if config.include_start:
        targets.append((0.0, None))
    interval_count = floor((total_distance_m - config.distance_tolerance_m) / config.spacing_m)
    for interval_index in range(1, max(interval_count, 0) + 1):
        targets.append((interval_index * config.spacing_m, interval_index))
    if config.include_end and (
        not targets or abs(targets[-1][0] - total_distance_m) > config.distance_tolerance_m
    ):
        targets.append((total_distance_m, None))
    deduplicated: list[tuple[float, int | None]] = []
    for target in targets:
        if not deduplicated or abs(target[0] - deduplicated[-1][0]) > config.distance_tolerance_m:
            deduplicated.append(target)
    if not deduplicated:
        raise RealTerrainWaypointOutputError("configuration produces zero route waypoints.")
    return tuple(deduplicated)


def _route_warnings(
    *, route_id: str, total_distance_m: float, config: RealTerrainWaypointConfig, waypoint_count: int
) -> tuple[str, ...]:
    """Return stable route-scoped warnings without duplicating the zero-distance meaning."""

    warnings: list[str] = []
    if total_distance_m < config.spacing_m - config.distance_tolerance_m:
        warnings.append(f"{route_id}: route shorter than requested waypoint spacing")
    if total_distance_m <= config.distance_tolerance_m and waypoint_count == 1:
        warnings.append(f"{route_id}: zero-distance route produced one waypoint")
    elif _is_endpoint_only(total_distance_m, config, waypoint_count):
        warnings.append(f"{route_id}: route produced endpoint-only waypoint report")
    return tuple(warnings)


def _is_endpoint_only(total_distance_m: float, config: RealTerrainWaypointConfig, waypoint_count: int) -> bool:
    endpoints = int(config.include_start) + int(config.include_end)
    return total_distance_m > config.distance_tolerance_m and waypoint_count == endpoints


def _stable_warning_union(route_warnings: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    return tuple(warning for warnings in route_warnings for warning in warnings)


def _validate_report_targets(
    report: RealTerrainRouteWaypointReport,
    *,
    source_total_distance_m: float,
    config: RealTerrainWaypointConfig,
    snapped_launch_mgrs: str,
    snapped_target_mgrs: str,
) -> None:
    try:
        targets = _waypoint_targets(source_total_distance_m, config)
    except RealTerrainWaypointOutputError:
        raise
    if len(report.waypoints) != len(targets):
        raise RealTerrainWaypointOutputError("route report waypoint count does not match target policy.")
    for waypoint, (target, interval_index) in zip(report.waypoints, targets):
        if (
            abs(waypoint.cumulative_distance_3d_m - target) > config.distance_tolerance_m
            or waypoint.target_interval_index != interval_index
        ):
            raise RealTerrainWaypointOutputError("route report waypoint targets do not match config policy.")
    zero_distance = source_total_distance_m <= config.distance_tolerance_m
    if zero_distance:
        if len(report.waypoints) != 1:
            raise RealTerrainWaypointOutputError("zero-distance route must produce one waypoint.")
        if snapped_launch_mgrs != snapped_target_mgrs or report.waypoints[0].mgrs != snapped_launch_mgrs:
            raise RealTerrainWaypointOutputError("zero-distance route endpoints do not match snapped authority.")
        expected_warnings = _route_warnings(
            route_id=report.route_id,
            total_distance_m=source_total_distance_m,
            config=config,
            waypoint_count=len(report.waypoints),
        )
        if report.warnings != expected_warnings:
            raise RealTerrainWaypointOutputError("route report warnings do not match deterministic policy.")
        return
    if config.include_start:
        if (
            abs(report.waypoints[0].cumulative_distance_3d_m) > config.distance_tolerance_m
            or report.waypoints[0].mgrs != snapped_launch_mgrs
        ):
            raise RealTerrainWaypointOutputError("route report start does not match snapped authority.")
    elif any(abs(item.cumulative_distance_3d_m) <= config.distance_tolerance_m for item in report.waypoints):
        raise RealTerrainWaypointOutputError("route report includes a disallowed start waypoint.")
    if config.include_end:
        if (
            abs(report.waypoints[-1].cumulative_distance_3d_m - source_total_distance_m)
            > config.distance_tolerance_m
            or report.waypoints[-1].mgrs != snapped_target_mgrs
        ):
            raise RealTerrainWaypointOutputError("route report end does not match snapped authority.")
    elif any(
        abs(item.cumulative_distance_3d_m - source_total_distance_m) <= config.distance_tolerance_m
        for item in report.waypoints
    ):
        raise RealTerrainWaypointOutputError("route report includes a disallowed end waypoint.")
    expected_warnings = _route_warnings(
        route_id=report.route_id,
        total_distance_m=source_total_distance_m,
        config=config,
        waypoint_count=len(report.waypoints),
    )
    if report.warnings != expected_warnings:
        raise RealTerrainWaypointOutputError("route report warnings do not match deterministic policy.")
