from __future__ import annotations

from dataclasses import replace

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
from uav_rf_terrain.real_terrain_route_outputs import (
    RealTerrainRouteCandidate,
    RealTerrainRouteConfig,
    RealTerrainRouteEdge,
    RealTerrainRouteNode,
    RealTerrainRoutePathPoint,
    RealTerrainRouteResult,
    RealTerrainRouteSummary,
    RouteMode,
    RouteNodeState,
    WaypointHandoffPoint,
)
from uav_rf_terrain.real_terrain_waypoint_outputs import RealTerrainWaypointConfig
from uav_rf_terrain.real_terrain_waypoint_reporting import (
    RealTerrainWaypointError,
    build_real_terrain_waypoint_reports,
)
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
)


def _metadata() -> TerrainDatasetMetadata:
    common = dict(
        source_dataset_name="test",
        source_provider="test",
        license_or_terms="test",
        crs="EPSG:5179",
        resolution_m=10.0,
        width=5,
        height=5,
        bounds=(0.0, 0.0, 1000.0, 1000.0),
        nodata_value=None,
        vertical_datum="MSL",
        processing_summary="test",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )
    return TerrainDatasetMetadata(
        "test-waypoint-terrain",
        TerrainRasterMetadata("dem", RASTER_TYPE_DEM, **common),
        TerrainRasterMetadata("dsm", RASTER_TYPE_DSM, **common),
        "2026-07-16",
        "pytest",
        "aligned",
        "test",
    )


def _mgrs(point: LocalPoint, *, precision: int) -> str:
    assert precision == 5
    return f"52SCB{int(point.x_m):05d}{int(point.y_m):05d}"


def _result(*, total: float = 1000.0) -> RealTerrainRouteResult:
    points = (LocalPoint(0.0, 0.0), LocalPoint(total / 2, 0.0), LocalPoint(total, 0.0))
    colors = (ColorClass.GREEN, ColorClass.RED, ColorClass.YELLOW)
    nodes = tuple(
        RealTerrainRouteNode(
            node_id=f"route-node-r00000-c{index:05d}",
            row=0,
            column=index,
            projected_point=point,
            node_mgrs=_mgrs(point, precision=5),
            terrain_msl_m=100.0 + index * 10.0,
            surface_msl_m=102.0 + index * 10.0,
            flight_agl_m=20.0,
            flight_msl_m=120.0 + index * 10.0,
            distance_3d_from_launch_m=float(index) * total / 2,
            within_operation_radius=True,
            state=RouteNodeState.VALID_SCORED,
            traversable=True,
            reason="valid",
            shielding_stability_score=90.0 - index * 20.0,
            overall_score=88.0 - index * 20.0,
            color_class=colors[index],
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
            source_sensitive=None,
            source_zone_reason="source-zone provider not requested",
            fresnel_diagnostics=None,
        )
        for index, point in enumerate(points)
    )
    path = tuple(
        RealTerrainRoutePathPoint(index, _mgrs(point, precision=5), 120.0 + index * 10.0)
        for index, point in enumerate(points)
    )
    candidate = RealTerrainRouteCandidate(
        route_id="route-shielding_minimum",
        mode=RouteMode.SHIELDING_MINIMUM,
        path=path,
        total_cost=1.0,
        total_distance_3d_m=total,
        mean_shielding_stability_score=70.0,
        minimum_shielding_stability_score=50.0,
        ordered_node_ids=tuple(node.node_id for node in nodes),
        ordered_projected_points=points,
        red_count=1,
        high_risk_count=1,
    )
    handoff = tuple(
        WaypointHandoffPoint(
            point_id=f"route-shielding_minimum-handoff-{index:03d}",
            projected_point=point,
            point_mgrs=_mgrs(point, precision=5),
            cumulative_distance_3d_m=float(index) * total / 2,
            terrain_msl_m=100.0 + index * 10.0,
            surface_msl_m=102.0 + index * 10.0,
            flight_agl_m=20.0,
            flight_msl_m=120.0 + index * 10.0,
            color_class=colors[index],
            shielding_stability_score=90.0 - index * 20.0,
            overall_score=88.0 - index * 20.0,
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
            source_sensitive=None,
            source_zone_reason="source-zone provider not requested",
        )
        for index, point in enumerate(points)
    )
    return RealTerrainRouteResult(
        scenario_name="waypoint test",
        mission_id="waypoint-test",
        selected_candidate_id="candidate-001",
        launch_site_mgrs=path[0].mgrs,
        target_mgrs=path[-1].mgrs,
        route_candidates=(candidate,),
        warnings=(),
        config=RealTerrainRouteConfig(10.0, 10.0, 20.0, 2_400_000_000.0, 1.0),
        terrain_metadata=_metadata(),
        graph_nodes=nodes,
        graph_edges=(RealTerrainRouteEdge(nodes[0].node_id, nodes[1].node_id, total / 2, 1, 1, 0),),
        summary=RealTerrainRouteSummary(3, 1, 3, 1),
        waypoint_handoffs=(handoff,),
        launch_ground_msl_m=100.0,
        snapped_launch_node_id=nodes[0].node_id,
        snapped_target_node_id=nodes[-1].node_id,
        snapped_launch_node_mgrs=path[0].mgrs,
        snapped_target_node_mgrs=path[-1].mgrs,
        launch_snap_distance_m=0.0,
        target_snap_distance_m=0.0,
    )


def test_sampling_reuses_exact_nodes_and_interpolates_conservatively() -> None:
    result = build_real_terrain_waypoint_reports(_result(), projected_to_mgrs=_mgrs)
    waypoints = result.route_reports[0].waypoints

    assert [waypoint.cumulative_distance_3d_m for waypoint in waypoints] == [0.0, 500.0, 1000.0]
    assert waypoints[1].value_semantics.value == "source_node"
    assert waypoints[1].left_source_point_id == "route-shielding_minimum-handoff-001"
    assert waypoints[1].flight_agl_m == 20.0
    assert waypoints[-1].segment_distance_from_previous_3d_m == 500.0

    interpolated = build_real_terrain_waypoint_reports(
        _result(), RealTerrainWaypointConfig(spacing_m=250.0), projected_to_mgrs=_mgrs
    ).route_reports[0].waypoints[1]
    assert interpolated.value_semantics.value == "segment_conservative_proxy"
    assert interpolated.color_class is ColorClass.RED
    assert interpolated.shielding_stability_score == 70.0
    assert interpolated.overall_score == 68.0
    assert 0.0 < interpolated.interpolation_fraction < 1.0


def test_short_and_zero_routes_emit_deterministic_warnings() -> None:
    short = build_real_terrain_waypoint_reports(_result(total=300.0), projected_to_mgrs=_mgrs)
    assert [item.cumulative_distance_3d_m for item in short.route_reports[0].waypoints] == [0.0, 300.0]
    assert short.route_reports[0].warnings == (
        "route-shielding_minimum: route shorter than requested waypoint spacing",
        "route-shielding_minimum: route produced endpoint-only waypoint report",
    )

    zero = _result(total=0.0)
    node = zero.graph_nodes[0]
    candidate = replace(
        zero.route_candidates[0],
        path=(zero.route_candidates[0].path[0],),
        total_cost=0.0,
        total_distance_3d_m=0.0,
        ordered_node_ids=(node.node_id,),
        ordered_projected_points=(node.projected_point,),
    )
    handoff = (zero.waypoint_handoffs[0][0],)
    zero = replace(
        zero,
        route_candidates=(candidate,),
        graph_nodes=(node,),
        graph_edges=(),
        summary=RealTerrainRouteSummary(1, 0, 1, 1),
        waypoint_handoffs=(handoff,),
        snapped_target_node_id=node.node_id,
        snapped_target_node_mgrs=candidate.path[0].mgrs,
    )
    zero_report = build_real_terrain_waypoint_reports(zero, projected_to_mgrs=_mgrs)
    assert len(zero_report.route_reports[0].waypoints) == 1
    assert zero_report.warnings == (
        "route-shielding_minimum: route shorter than requested waypoint spacing",
        "route-shielding_minimum: zero-distance route produced one waypoint",
    )
    assert zero_report.summary.warnings == zero_report.warnings


def test_conversion_is_cached_and_source_zone_remains_not_requested() -> None:
    calls: list[LocalPoint] = []

    def cached_mgrs(point: LocalPoint, *, precision: int) -> str:
        calls.append(point)
        return _mgrs(point, precision=precision)

    report = build_real_terrain_waypoint_reports(
        _result(), RealTerrainWaypointConfig(spacing_m=250.0), projected_to_mgrs=cached_mgrs
    )
    waypoints = report.route_reports[0].waypoints
    assert len(calls) == len(set(waypoint.projected_point for waypoint in waypoints))
    assert all(item.source_zone is None for item in waypoints)
    assert all(item.source_zone_state is SourceZoneAvailability.NOT_REQUESTED for item in waypoints)


@pytest.mark.parametrize(
    ("include_start", "include_end", "expected_distances"),
    (
        (True, True, [0.0, 500.0, 1000.0]),
        (True, False, [0.0, 500.0]),
        (False, True, [500.0, 1000.0]),
        (False, False, [500.0]),
    ),
)
def test_endpoint_policy_preserves_all_start_end_combinations(
    include_start: bool, include_end: bool, expected_distances: list[float]
) -> None:
    report = build_real_terrain_waypoint_reports(
        _result(),
        RealTerrainWaypointConfig(include_start=include_start, include_end=include_end),
        projected_to_mgrs=_mgrs,
    )
    assert [item.cumulative_distance_3d_m for item in report.route_reports[0].waypoints] == expected_distances


def test_public_output_keeps_private_route_authority_internal() -> None:
    result = build_real_terrain_waypoint_reports(
        _result(), RealTerrainWaypointConfig(include_start=False, include_end=False), projected_to_mgrs=_mgrs
    )
    public = result.to_public_dict()
    assert "x_m" not in str(public)
    assert "projected" not in str(public)
    assert "launch_ground_msl_m" not in public
    assert "source_route_ids" not in public
    assert "snapped_launch_node_mgrs" not in public
    assert public["routes"][0]["waypoints"][0]["source_zone_state"] == "not_requested"
    with pytest.raises(RealTerrainWaypointError, match="zero route waypoints"):
        build_real_terrain_waypoint_reports(
            _result(total=0.0),
            RealTerrainWaypointConfig(include_start=False, include_end=False),
            projected_to_mgrs=_mgrs,
        )


def test_guards_and_malformed_handoff_are_fatal_before_partial_output() -> None:
    calls: list[LocalPoint] = []

    def counting_mgrs(point: LocalPoint, *, precision: int) -> str:
        calls.append(point)
        return _mgrs(point, precision=precision)

    with pytest.raises(RealTerrainWaypointError, match="max_waypoints_per_route"):
        build_real_terrain_waypoint_reports(
            _result(),
            RealTerrainWaypointConfig(spacing_m=100.0, max_waypoints_per_route=2),
            projected_to_mgrs=counting_mgrs,
        )
    assert not calls
    with pytest.raises(RealTerrainWaypointError, match="MGRS conversion"):
        build_real_terrain_waypoint_reports(_result(), projected_to_mgrs=lambda point, *, precision: " ")
    with pytest.raises(RealTerrainWaypointError, match="non-text"):
        build_real_terrain_waypoint_reports(_result(), projected_to_mgrs=lambda point, *, precision: 1)  # type: ignore[arg-type]
    with pytest.raises(RealTerrainWaypointError, match="MGRS conversion"):
        build_real_terrain_waypoint_reports(
            _result(),
            projected_to_mgrs=lambda point, *, precision: (_ for _ in ()).throw(RuntimeError("bad converter")),
        )
    bad_handoff = list(_result().waypoint_handoffs[0])
    bad_handoff[1] = replace(bad_handoff[1], source_zone_state=SourceZoneAvailability.UNAVAILABLE)
    malformed_result = _result()
    object.__setattr__(malformed_result, "waypoint_handoffs", (tuple(bad_handoff),))
    with pytest.raises(RealTerrainWaypointError, match="complete invariant"):
        build_real_terrain_waypoint_reports(malformed_result, projected_to_mgrs=_mgrs)


def test_zero_distance_accepts_each_enabled_endpoint_and_rejects_none() -> None:
    zero = _result(total=0.0)
    node = zero.graph_nodes[0]
    candidate = replace(
        zero.route_candidates[0],
        path=(zero.route_candidates[0].path[0],),
        total_cost=0.0,
        total_distance_3d_m=0.0,
        ordered_node_ids=(node.node_id,),
        ordered_projected_points=(node.projected_point,),
    )
    zero = replace(
        zero,
        route_candidates=(candidate,),
        graph_nodes=(node,),
        graph_edges=(),
        summary=RealTerrainRouteSummary(1, 0, 1, 1),
        waypoint_handoffs=((zero.waypoint_handoffs[0][0],),),
        snapped_target_node_id=node.node_id,
        snapped_target_node_mgrs=candidate.path[0].mgrs,
    )
    for include_start, include_end in ((True, True), (True, False), (False, True)):
        output = build_real_terrain_waypoint_reports(
            zero,
            RealTerrainWaypointConfig(include_start=include_start, include_end=include_end),
            projected_to_mgrs=_mgrs,
        )
        assert len(output.route_reports[0].waypoints) == 1
    with pytest.raises(RealTerrainWaypointError, match="zero route waypoints"):
        build_real_terrain_waypoint_reports(
            zero,
            RealTerrainWaypointConfig(include_start=False, include_end=False),
            projected_to_mgrs=_mgrs,
        )


def test_forward_sampling_cursor_never_moves_backward(monkeypatch: pytest.MonkeyPatch) -> None:
    import uav_rf_terrain.real_terrain_waypoint_reporting as reporting

    cursors: list[int] = []
    original = reporting._sample_at_distance

    def recording_sample(*args: object, **kwargs: object) -> tuple[object, int]:
        cursors.append(int(kwargs["cursor"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(reporting, "_sample_at_distance", recording_sample)
    build_real_terrain_waypoint_reports(
        _result(), RealTerrainWaypointConfig(spacing_m=125.0), projected_to_mgrs=_mgrs
    )
    assert cursors == sorted(cursors)
