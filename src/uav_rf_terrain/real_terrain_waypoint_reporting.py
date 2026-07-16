"""Deterministic waypoint reporting over complete real-terrain route results."""

from __future__ import annotations

from dataclasses import dataclass
from .coordinate_conversion import ProjectedToMgrsConverter
from .coordinates import LocalPoint
from .real_terrain_candidate_analysis import SourceZoneAvailability
from .real_terrain_route_outputs import RealTerrainRouteResult, RouteMode, WaypointHandoffPoint
from .real_terrain_waypoint_outputs import (
    RealTerrainRouteWaypointReport,
    RealTerrainWaypointConfig,
    RealTerrainWaypointRecord,
    RealTerrainWaypointResult,
    RealTerrainWaypointSummary,
    WaypointElevationSemantics,
    WaypointValueSemantics,
    _route_warnings,
    _waypoint_targets,
)
from .schemas import ColorClass


class RealTerrainWaypointError(ValueError):
    """Raised when a complete route result cannot produce a waypoint report."""


_COLOR_SEVERITY = {
    ColorClass.GREEN: 0,
    ColorClass.YELLOW: 1,
    ColorClass.ORANGE: 2,
    ColorClass.RED: 3,
}


@dataclass(frozen=True)
class _SampleValue:
    projected_point: LocalPoint
    terrain_msl_m: float
    surface_msl_m: float
    flight_msl_m: float
    color_class: ColorClass
    shielding_stability_score: float
    overall_score: float
    value_semantics: WaypointValueSemantics
    elevation_semantics: WaypointElevationSemantics
    left_source_point_id: str
    right_source_point_id: str
    interpolation_fraction: float
    exact_source_mgrs: str | None


def build_real_terrain_waypoint_reports(
    route_result: RealTerrainRouteResult,
    config: RealTerrainWaypointConfig = RealTerrainWaypointConfig(),
    *,
    projected_to_mgrs: ProjectedToMgrsConverter,
) -> RealTerrainWaypointResult:
    """Build deterministic approximately fixed-interval reports for every route candidate."""

    if not isinstance(route_result, RealTerrainRouteResult):
        raise RealTerrainWaypointError("route_result must be a complete RealTerrainRouteResult.")
    if not isinstance(config, RealTerrainWaypointConfig):
        raise RealTerrainWaypointError("config must be RealTerrainWaypointConfig.")
    if not callable(projected_to_mgrs):
        raise RealTerrainWaypointError("projected_to_mgrs must be callable.")
    _validate_complete_route_result(route_result)

    try:
        targets_by_route = tuple(
            _waypoint_targets(candidate.total_distance_3d_m, config)
            for candidate in route_result.route_candidates
        )
    except Exception as exc:
        raise RealTerrainWaypointError(f"waypoint target policy validation failed: {exc}") from exc
    if any(len(targets) > config.max_waypoints_per_route for targets in targets_by_route):
        raise RealTerrainWaypointError("max_waypoints_per_route guard exceeded.")
    total_waypoints = sum(len(targets) for targets in targets_by_route)
    if total_waypoints > config.max_total_waypoints:
        raise RealTerrainWaypointError("max_total_waypoints guard exceeded.")

    cache: dict[LocalPoint, str] = {}
    reports: list[RealTerrainRouteWaypointReport] = []
    for candidate, handoff, targets in zip(
        route_result.route_candidates, route_result.waypoint_handoffs, targets_by_route
    ):
        records = _route_records(
            route_result=route_result,
            candidate_mode=candidate.mode,
            candidate_route_id=candidate.route_id,
            candidate_total_distance_m=candidate.total_distance_3d_m,
            handoff=handoff,
            targets=targets,
            config=config,
            projected_to_mgrs=projected_to_mgrs,
            cache=cache,
        )
        reports.append(
            RealTerrainRouteWaypointReport(
                route_id=candidate.route_id,
                route_mode=candidate.mode,
                path_semantics=route_result.path_semantics,
                waypoint_spacing_m=config.spacing_m,
                total_route_distance_3d_m=candidate.total_distance_3d_m,
                waypoints=records,
                warnings=_route_warnings(
                    route_id=candidate.route_id,
                    total_distance_m=candidate.total_distance_3d_m,
                    config=config,
                    waypoint_count=len(records),
                ),
            )
        )
    warnings = tuple(warning for report in reports for warning in report.warnings)
    return RealTerrainWaypointResult(
        scenario_name=route_result.scenario_name,
        mission_id=route_result.mission_id,
        selected_candidate_id=route_result.selected_candidate_id,
        launch_site_mgrs=route_result.launch_site_mgrs,
        target_mgrs=route_result.target_mgrs,
        config=config,
        launch_ground_msl_m=route_result.launch_ground_msl_m,
        source_route_ids=tuple(candidate.route_id for candidate in route_result.route_candidates),
        source_route_modes=tuple(candidate.mode for candidate in route_result.route_candidates),
        source_route_total_distance_3d_m=tuple(
            candidate.total_distance_3d_m for candidate in route_result.route_candidates
        ),
        snapped_launch_node_mgrs=route_result.snapped_launch_node_mgrs,
        snapped_target_node_mgrs=route_result.snapped_target_node_mgrs,
        route_reports=tuple(reports),
        summary=RealTerrainWaypointSummary(len(reports), total_waypoints, warnings),
        warnings=warnings,
    )


def _validate_complete_route_result(route_result: RealTerrainRouteResult) -> None:
    try:
        route_result.__post_init__()
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        raise RealTerrainWaypointError("route_result complete invariant validation failed.") from exc
    if route_result.path_semantics != "snapped_graph_path":
        raise RealTerrainWaypointError("route_result must retain snapped_graph_path semantics.")
    if len(route_result.waypoint_handoffs) != len(route_result.route_candidates):
        raise RealTerrainWaypointError("route_result handoff count does not match candidates.")
    for candidate, handoff in zip(route_result.route_candidates, route_result.waypoint_handoffs):
        if not handoff or len(handoff) != len(candidate.path):
            raise RealTerrainWaypointError("route candidate handoff parity is invalid.")
        previous = -1.0
        for point in handoff:
            if point.cumulative_distance_3d_m < previous:
                raise RealTerrainWaypointError("handoff cumulative distance must be non-decreasing.")
            previous = point.cumulative_distance_3d_m
        if abs(handoff[0].cumulative_distance_3d_m) > 1e-9 or abs(
            handoff[-1].cumulative_distance_3d_m - candidate.total_distance_3d_m
        ) > 1e-9:
            raise RealTerrainWaypointError("handoff cumulative distance does not match route total.")


def _route_records(
    *,
    route_result: RealTerrainRouteResult,
    candidate_mode: RouteMode,
    candidate_route_id: str,
    candidate_total_distance_m: float,
    handoff: tuple[WaypointHandoffPoint, ...],
    targets: tuple[tuple[float, int | None], ...],
    config: RealTerrainWaypointConfig,
    projected_to_mgrs: ProjectedToMgrsConverter,
    cache: dict[LocalPoint, str],
) -> tuple[RealTerrainWaypointRecord, ...]:
    records: list[RealTerrainWaypointRecord] = []
    cursor = 0
    previous_distance: float | None = None
    for sequence_index, (target_distance, interval_index) in enumerate(targets):
        sample, cursor = _sample_at_distance(
            handoff,
            target_distance=target_distance,
            tolerance_m=config.distance_tolerance_m,
            cursor=cursor,
        )
        mgrs = _mgrs_for_point(sample.projected_point, config, projected_to_mgrs, cache)
        if sample.exact_source_mgrs is not None and mgrs != sample.exact_source_mgrs:
            raise RealTerrainWaypointError("exact source waypoint MGRS parity failed.")
        segment_distance = 0.0 if previous_distance is None else target_distance - previous_distance
        if segment_distance < -config.distance_tolerance_m:
            raise RealTerrainWaypointError("waypoint target distances must be ordered.")
        records.append(
            RealTerrainWaypointRecord(
                waypoint_id=f"route-{candidate_mode.value}-wp-{sequence_index:03d}",
                route_id=candidate_route_id,
                route_mode=candidate_mode,
                sequence_index=sequence_index,
                target_interval_index=interval_index,
                projected_point=sample.projected_point,
                mgrs=mgrs,
                cumulative_distance_3d_m=target_distance,
                segment_distance_from_previous_3d_m=max(segment_distance, 0.0),
                terrain_msl_m=sample.terrain_msl_m,
                surface_msl_m=sample.surface_msl_m,
                flight_agl_m=route_result.config.allowed_flight_agl_m,
                flight_msl_m=sample.flight_msl_m,
                height_difference_from_launch_m=sample.flight_msl_m - route_result.launch_ground_msl_m,
                color_class=sample.color_class,
                shielding_stability_score=sample.shielding_stability_score,
                overall_score=sample.overall_score,
                value_semantics=sample.value_semantics,
                elevation_semantics=sample.elevation_semantics,
                left_source_point_id=sample.left_source_point_id,
                right_source_point_id=sample.right_source_point_id,
                interpolation_fraction=sample.interpolation_fraction,
                source_zone=None,
                source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
                source_sensitive=None,
                source_zone_reason="source-zone provider not requested",
            )
        )
        previous_distance = target_distance
    if abs(records[-1].cumulative_distance_3d_m - candidate_total_distance_m) > config.distance_tolerance_m and config.include_end:
        raise RealTerrainWaypointError("final waypoint does not match route total distance.")
    return tuple(records)


def _sample_at_distance(
    handoff: tuple[WaypointHandoffPoint, ...],
    *,
    target_distance: float,
    tolerance_m: float,
    cursor: int,
) -> tuple[_SampleValue, int]:
    while cursor + 1 < len(handoff) and handoff[cursor + 1].cumulative_distance_3d_m < target_distance - tolerance_m:
        cursor += 1
    current = handoff[cursor]
    if abs(current.cumulative_distance_3d_m - target_distance) <= tolerance_m:
        return _exact_sample(current), cursor
    if cursor + 1 >= len(handoff):
        raise RealTerrainWaypointError("waypoint target cannot be bracketed by handoff points.")
    right = handoff[cursor + 1]
    if abs(right.cumulative_distance_3d_m - target_distance) <= tolerance_m:
        return _exact_sample(right), cursor + 1
    denominator = right.cumulative_distance_3d_m - current.cumulative_distance_3d_m
    if denominator <= 0.0:
        raise RealTerrainWaypointError("waypoint interpolation denominator must be positive.")
    fraction = (target_distance - current.cumulative_distance_3d_m) / denominator
    if not 0.0 < fraction < 1.0:
        raise RealTerrainWaypointError("waypoint interpolation fraction must be within the segment.")
    terrain = _linear(current.terrain_msl_m, right.terrain_msl_m, fraction)
    surface = _linear(current.surface_msl_m, right.surface_msl_m, fraction)
    flight = _linear(current.flight_msl_m, right.flight_msl_m, fraction)
    if not terrain <= surface <= flight:
        raise RealTerrainWaypointError("interpolated waypoint elevation ordering is invalid.")
    color = max((current.color_class, right.color_class), key=_COLOR_SEVERITY.__getitem__)
    return (
        _SampleValue(
            projected_point=LocalPoint(
                _linear(current.projected_point.x_m, right.projected_point.x_m, fraction),
                _linear(current.projected_point.y_m, right.projected_point.y_m, fraction),
            ),
            terrain_msl_m=terrain,
            surface_msl_m=surface,
            flight_msl_m=flight,
            color_class=color,
            shielding_stability_score=min(current.shielding_stability_score, right.shielding_stability_score),
            overall_score=min(current.overall_score, right.overall_score),
            value_semantics=WaypointValueSemantics.SEGMENT_CONSERVATIVE_PROXY,
            elevation_semantics=WaypointElevationSemantics.ENDPOINT_LINEAR_INTERPOLATION,
            left_source_point_id=current.point_id,
            right_source_point_id=right.point_id,
            interpolation_fraction=fraction,
            exact_source_mgrs=None,
        ),
        cursor,
    )


def _exact_sample(point: WaypointHandoffPoint) -> _SampleValue:
    return _SampleValue(
        projected_point=point.projected_point,
        terrain_msl_m=point.terrain_msl_m,
        surface_msl_m=point.surface_msl_m,
        flight_msl_m=point.flight_msl_m,
        color_class=point.color_class,
        shielding_stability_score=point.shielding_stability_score,
        overall_score=point.overall_score,
        value_semantics=WaypointValueSemantics.SOURCE_NODE,
        elevation_semantics=WaypointElevationSemantics.SOURCE_NODE,
        left_source_point_id=point.point_id,
        right_source_point_id=point.point_id,
        interpolation_fraction=0.0,
        exact_source_mgrs=point.point_mgrs,
    )


def _mgrs_for_point(
    point: LocalPoint,
    config: RealTerrainWaypointConfig,
    projected_to_mgrs: ProjectedToMgrsConverter,
    cache: dict[LocalPoint, str],
) -> str:
    cached = cache.get(point)
    if cached is not None:
        return cached
    try:
        value = projected_to_mgrs(point, precision=config.mgrs_precision)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        raise RealTerrainWaypointError("MGRS conversion failed.") from exc
    if not isinstance(value, str):
        raise RealTerrainWaypointError("MGRS conversion returned non-text output.")
    normalized = value.strip().upper()
    if not normalized:
        raise RealTerrainWaypointError("MGRS conversion returned empty output.")
    cache[point] = normalized
    return normalized


def _linear(left: float, right: float, fraction: float) -> float:
    return left + (right - left) * fraction
