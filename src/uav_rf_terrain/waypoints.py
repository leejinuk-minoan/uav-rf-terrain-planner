"""Pure Python offline waypoint report scaffolding.

Waypoints in this module are route reporting points for later map/UI and paper-analysis
workflows. They are not vehicle commands, execution plans, or verified link-quality
outputs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

from .schemas import ColorClass


class WaypointError(ValueError):
    """Raised when waypoint report inputs or derived outputs are invalid."""


@dataclass(frozen=True)
class WaypointSourcePoint:
    """Ordered source point used to sample offline waypoint report points.

    The surface/terrain ordering check follows synthetic DSM/DEM consistency. Real
    data noise may require a relaxed tolerance in a later local GIS task.
    """

    point_id: str
    x_m: float
    y_m: float
    terrain_msl_m: float
    surface_msl_m: float
    cumulative_distance_m: float
    color_class: ColorClass
    shielding_stability_score: float
    overall_score: float

    def __post_init__(self) -> None:
        _validate_non_empty_string("point_id", self.point_id)
        _validate_finite("x_m", self.x_m)
        _validate_finite("y_m", self.y_m)
        _validate_finite("terrain_msl_m", self.terrain_msl_m)
        _validate_finite("surface_msl_m", self.surface_msl_m)
        _validate_non_negative_finite("cumulative_distance_m", self.cumulative_distance_m)
        if self.surface_msl_m < self.terrain_msl_m:
            raise WaypointError("surface_msl_m must be greater than or equal to terrain_msl_m.")
        _validate_color_class(self.color_class)
        _reject_excluded(self.color_class)
        _validate_score("shielding_stability_score", self.shielding_stability_score)
        _validate_score("overall_score", self.overall_score)


@dataclass(frozen=True)
class WaypointSamplingConfig:
    """Configuration for approximate interval-based waypoint report sampling."""

    spacing_m: float = 500.0
    include_start: bool = True
    include_end: bool = True

    def __post_init__(self) -> None:
        if not isfinite(self.spacing_m) or self.spacing_m <= 0.0:
            raise WaypointError("spacing_m must be finite and positive.")
        if not isinstance(self.include_start, bool):
            raise WaypointError("include_start must be a bool.")
        if not isinstance(self.include_end, bool):
            raise WaypointError("include_end must be a bool.")


@dataclass(frozen=True)
class RouteWaypoint:
    """Offline route reporting waypoint."""

    waypoint_id: str
    sequence_index: int
    source_point_id: str
    x_m: float
    y_m: float
    cumulative_distance_m: float
    segment_distance_from_previous_m: float
    terrain_msl_m: float
    surface_msl_m: float
    flight_agl_m: float
    flight_msl_m: float
    height_difference_from_launch_m: float
    color_class: ColorClass
    shielding_stability_score: float
    overall_score: float

    def __post_init__(self) -> None:
        _validate_non_empty_string("waypoint_id", self.waypoint_id)
        _validate_non_negative_int("sequence_index", self.sequence_index)
        _validate_non_empty_string("source_point_id", self.source_point_id)
        _validate_finite("x_m", self.x_m)
        _validate_finite("y_m", self.y_m)
        _validate_non_negative_finite("cumulative_distance_m", self.cumulative_distance_m)
        _validate_non_negative_finite(
            "segment_distance_from_previous_m",
            self.segment_distance_from_previous_m,
        )
        _validate_finite("terrain_msl_m", self.terrain_msl_m)
        _validate_finite("surface_msl_m", self.surface_msl_m)
        if self.surface_msl_m < self.terrain_msl_m:
            raise WaypointError("surface_msl_m must be greater than or equal to terrain_msl_m.")
        _validate_non_negative_finite("flight_agl_m", self.flight_agl_m)
        _validate_finite("flight_msl_m", self.flight_msl_m)
        _validate_finite(
            "height_difference_from_launch_m",
            self.height_difference_from_launch_m,
        )
        _validate_color_class(self.color_class)
        _reject_excluded(self.color_class)
        _validate_score("shielding_stability_score", self.shielding_stability_score)
        _validate_score("overall_score", self.overall_score)


@dataclass(frozen=True)
class RouteWaypointReport:
    """Offline waypoint report for one route candidate."""

    route_id: str
    waypoint_spacing_m: float
    launch_terrain_msl_m: float
    flight_agl_m: float
    total_route_distance_m: float
    waypoints: tuple[RouteWaypoint, ...]

    def __post_init__(self) -> None:
        _validate_non_empty_string("route_id", self.route_id)
        _validate_positive_finite("waypoint_spacing_m", self.waypoint_spacing_m)
        _validate_finite("launch_terrain_msl_m", self.launch_terrain_msl_m)
        _validate_non_negative_finite("flight_agl_m", self.flight_agl_m)
        _validate_non_negative_finite("total_route_distance_m", self.total_route_distance_m)
        if not self.waypoints:
            raise WaypointError("waypoints must not be empty.")
        previous_distance: float | None = None
        for expected_index, waypoint in enumerate(self.waypoints):
            if not isinstance(waypoint, RouteWaypoint):
                raise WaypointError("all waypoints must be RouteWaypoint instances.")
            if waypoint.sequence_index != expected_index:
                raise WaypointError("waypoints sequence_index must increase from 0 without gaps.")
            if previous_distance is not None and waypoint.cumulative_distance_m < previous_distance:
                raise WaypointError("waypoint cumulative_distance_m must be non-decreasing.")
            previous_distance = waypoint.cumulative_distance_m


def compute_flight_msl_m(*, terrain_msl_m: float, flight_agl_m: float) -> float:
    """Compute reporting flight MSL from terrain MSL and fixed AGL."""

    _validate_finite("terrain_msl_m", terrain_msl_m)
    _validate_non_negative_finite("flight_agl_m", flight_agl_m)
    return terrain_msl_m + flight_agl_m


def compute_height_difference_from_launch_m(
    *,
    flight_msl_m: float,
    launch_terrain_msl_m: float,
) -> float:
    """Compute height difference from the launch terrain MSL datum."""

    _validate_finite("flight_msl_m", flight_msl_m)
    _validate_finite("launch_terrain_msl_m", launch_terrain_msl_m)
    return flight_msl_m - launch_terrain_msl_m


def select_waypoint_source_points(
    source_points: Sequence[WaypointSourcePoint],
    *,
    config: WaypointSamplingConfig = WaypointSamplingConfig(),
) -> tuple[WaypointSourcePoint, ...]:
    """Select source points at approximately fixed distance intervals.

    The MVP method selects the first source point whose cumulative distance is greater
    than or equal to each target interval. It does not interpolate between points.
    """

    resolved_points = _ensure_source_points(source_points)
    if not isinstance(config, WaypointSamplingConfig):
        raise WaypointError("config must be a WaypointSamplingConfig instance.")

    selected: list[WaypointSourcePoint] = []
    selected_ids: set[str] = set()

    if config.include_start:
        _append_unique(selected, selected_ids, resolved_points[0])

    target_distance_m = config.spacing_m
    for point in resolved_points:
        if point.cumulative_distance_m >= target_distance_m:
            _append_unique(selected, selected_ids, point)
            while target_distance_m <= point.cumulative_distance_m:
                target_distance_m += config.spacing_m

    if config.include_end:
        _append_unique(selected, selected_ids, resolved_points[-1])

    return tuple(selected)


def build_route_waypoints(
    *,
    route_id: str,
    source_points: Sequence[WaypointSourcePoint],
    flight_agl_m: float,
    launch_terrain_msl_m: float,
    config: WaypointSamplingConfig = WaypointSamplingConfig(),
) -> RouteWaypointReport:
    """Build an offline waypoint report for one route candidate."""

    _validate_non_empty_string("route_id", route_id)
    _validate_non_negative_finite("flight_agl_m", flight_agl_m)
    _validate_finite("launch_terrain_msl_m", launch_terrain_msl_m)
    resolved_points = _ensure_source_points(source_points)
    selected_points = select_waypoint_source_points(resolved_points, config=config)
    if not selected_points:
        raise WaypointError("selected waypoint source points must not be empty.")

    waypoints: list[RouteWaypoint] = []
    previous_cumulative_distance_m: float | None = None
    for sequence_index, point in enumerate(selected_points):
        flight_msl_m = compute_flight_msl_m(
            terrain_msl_m=point.terrain_msl_m,
            flight_agl_m=flight_agl_m,
        )
        segment_distance_from_previous_m = (
            0.0
            if previous_cumulative_distance_m is None
            else point.cumulative_distance_m - previous_cumulative_distance_m
        )
        if segment_distance_from_previous_m < 0.0:
            raise WaypointError("selected source points must be non-decreasing by distance.")
        waypoints.append(
            RouteWaypoint(
                waypoint_id=f"{route_id}-wp-{sequence_index:03d}",
                sequence_index=sequence_index,
                source_point_id=point.point_id,
                x_m=point.x_m,
                y_m=point.y_m,
                cumulative_distance_m=point.cumulative_distance_m,
                segment_distance_from_previous_m=segment_distance_from_previous_m,
                terrain_msl_m=point.terrain_msl_m,
                surface_msl_m=point.surface_msl_m,
                flight_agl_m=flight_agl_m,
                flight_msl_m=flight_msl_m,
                height_difference_from_launch_m=compute_height_difference_from_launch_m(
                    flight_msl_m=flight_msl_m,
                    launch_terrain_msl_m=launch_terrain_msl_m,
                ),
                color_class=point.color_class,
                shielding_stability_score=point.shielding_stability_score,
                overall_score=point.overall_score,
            )
        )
        previous_cumulative_distance_m = point.cumulative_distance_m

    return RouteWaypointReport(
        route_id=route_id,
        waypoint_spacing_m=config.spacing_m,
        launch_terrain_msl_m=launch_terrain_msl_m,
        flight_agl_m=flight_agl_m,
        total_route_distance_m=resolved_points[-1].cumulative_distance_m,
        waypoints=tuple(waypoints),
    )


def summarize_waypoint_report(report: RouteWaypointReport) -> dict[str, float | int | str]:
    """Summarize waypoint report metrics for paper tables or future UI summaries."""

    if not isinstance(report, RouteWaypointReport):
        raise WaypointError("report must be a RouteWaypointReport instance.")

    flight_msl_values = [waypoint.flight_msl_m for waypoint in report.waypoints]
    height_difference_values = [
        waypoint.height_difference_from_launch_m for waypoint in report.waypoints
    ]
    return {
        "route_id": report.route_id,
        "waypoint_count": len(report.waypoints),
        "waypoint_spacing_m": report.waypoint_spacing_m,
        "total_route_distance_m": report.total_route_distance_m,
        "flight_agl_m": report.flight_agl_m,
        "min_flight_msl_m": min(flight_msl_values),
        "max_flight_msl_m": max(flight_msl_values),
        "min_height_difference_from_launch_m": min(height_difference_values),
        "max_height_difference_from_launch_m": max(height_difference_values),
        "red_waypoint_count": sum(
            1 for waypoint in report.waypoints if waypoint.color_class is ColorClass.RED
        ),
        "orange_waypoint_count": sum(
            1 for waypoint in report.waypoints if waypoint.color_class is ColorClass.ORANGE
        ),
    }


def _ensure_source_points(
    source_points: Sequence[WaypointSourcePoint],
) -> tuple[WaypointSourcePoint, ...]:
    if not source_points:
        raise WaypointError("source_points must not be empty.")
    resolved_points = tuple(source_points)
    previous_distance: float | None = None
    for point in resolved_points:
        if not isinstance(point, WaypointSourcePoint):
            raise WaypointError("all source_points must be WaypointSourcePoint instances.")
        _reject_excluded(point.color_class)
        if previous_distance is not None and point.cumulative_distance_m < previous_distance:
            raise WaypointError("source_points cumulative_distance_m must be non-decreasing.")
        previous_distance = point.cumulative_distance_m
    return resolved_points


def _append_unique(
    selected: list[WaypointSourcePoint],
    selected_ids: set[str],
    point: WaypointSourcePoint,
) -> None:
    if point.point_id not in selected_ids:
        selected.append(point)
        selected_ids.add(point.point_id)


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise WaypointError(f"{field_name} must be a non-empty string.")


def _validate_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise WaypointError(f"{field_name} must be finite.")


def _validate_positive_finite(field_name: str, value: float) -> None:
    if not isfinite(value) or value <= 0.0:
        raise WaypointError(f"{field_name} must be finite and positive.")


def _validate_non_negative_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise WaypointError(f"{field_name} must be finite.")
    if value < 0.0:
        raise WaypointError(f"{field_name} must be non-negative.")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WaypointError(f"{field_name} must be an integer.")
    if value < 0:
        raise WaypointError(f"{field_name} must be non-negative.")


def _validate_score(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise WaypointError(f"{field_name} must be finite.")
    if value < 0.0 or value > 100.0:
        raise WaypointError(f"{field_name} must be within [0, 100].")


def _validate_color_class(color_class: ColorClass) -> None:
    if not isinstance(color_class, ColorClass):
        raise WaypointError("color_class must be a ColorClass value.")


def _reject_excluded(color_class: ColorClass) -> None:
    if color_class is ColorClass.EXCLUDED:
        raise WaypointError("ColorClass.EXCLUDED cannot be used in waypoint source/report points.")
