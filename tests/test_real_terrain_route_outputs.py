from __future__ import annotations

from dataclasses import replace

import pytest

from uav_rf_terrain.real_terrain_route_outputs import (
    RealTerrainRouteCandidate,
    RealTerrainRouteConfig,
    RealTerrainRouteNode,
    RealTerrainRouteOutputError,
    RealTerrainRoutePathPoint,
    RealTerrainRouteResult,
    RealTerrainRouteSummary,
    RouteMode,
    RouteNodeState,
    WaypointHandoffPoint,
    route_mode_cost_policy,
)
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
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
        width=2,
        height=1,
        bounds=(0.0, 0.0, 10.0, 0.0),
        nodata_value=None,
        vertical_datum="MSL",
        processing_summary="test",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )
    return TerrainDatasetMetadata(
        "route-test",
        TerrainRasterMetadata("dem", RASTER_TYPE_DEM, **common),
        TerrainRasterMetadata("dsm", RASTER_TYPE_DSM, **common),
        "2026-07-16",
        "pytest",
        "aligned",
        "test",
    )


def _valid_runtime_result() -> RealTerrainRouteResult:
    launch = LocalPoint(0.0, 0.0)
    target = LocalPoint(10.0, 0.0)
    node_values = (
        ("route-node-r00000-c00000", 0, 0, launch, "52SCB0000000000"),
        ("route-node-r00000-c00001", 0, 1, target, "52SCB0001000000"),
    )
    nodes = tuple(
        RealTerrainRouteNode(
            node_id=node_id,
            row=row,
            column=column,
            projected_point=point,
            node_mgrs=mgrs,
            terrain_msl_m=100.0,
            surface_msl_m=100.0,
            flight_agl_m=20.0,
            flight_msl_m=120.0,
            distance_3d_from_launch_m=float(column * 10),
            within_operation_radius=True,
            state=RouteNodeState.VALID_SCORED,
            traversable=True,
            reason="valid scored route node",
            shielding_stability_score=90.0,
            overall_score=90.0,
            color_class=ColorClass.GREEN,
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
            source_sensitive=None,
            source_zone_reason="source-zone provider not requested for route nodes",
            fresnel_diagnostics=None,
        )
        for node_id, row, column, point, mgrs in node_values
    )
    path = (
        RealTerrainRoutePathPoint(0, "52SCB0000000000", 120.0),
        RealTerrainRoutePathPoint(1, "52SCB0001000000", 120.0),
    )
    candidate = RealTerrainRouteCandidate(
        route_id="route-shielding_minimum",
        mode=RouteMode.SHIELDING_MINIMUM,
        path=path,
        total_cost=10.0,
        total_distance_3d_m=10.0,
        mean_shielding_stability_score=90.0,
        minimum_shielding_stability_score=90.0,
        ordered_node_ids=(nodes[0].node_id, nodes[1].node_id),
        ordered_projected_points=(launch, target),
    )
    handoff = (
        WaypointHandoffPoint(
            point_id="route-shielding_minimum-handoff-000",
            projected_point=launch,
            point_mgrs=path[0].mgrs,
            cumulative_distance_3d_m=0.0,
            terrain_msl_m=100.0,
            surface_msl_m=100.0,
            flight_agl_m=20.0,
            flight_msl_m=120.0,
            color_class=ColorClass.GREEN,
            shielding_stability_score=90.0,
            overall_score=90.0,
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
            source_sensitive=None,
            source_zone_reason="source-zone provider not requested for route nodes",
        ),
        WaypointHandoffPoint(
            point_id="route-shielding_minimum-handoff-001",
            projected_point=target,
            point_mgrs=path[1].mgrs,
            cumulative_distance_3d_m=10.0,
            terrain_msl_m=100.0,
            surface_msl_m=100.0,
            flight_agl_m=20.0,
            flight_msl_m=120.0,
            color_class=ColorClass.GREEN,
            shielding_stability_score=90.0,
            overall_score=90.0,
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
            source_sensitive=None,
            source_zone_reason="source-zone provider not requested for route nodes",
        ),
    )
    return RealTerrainRouteResult(
        scenario_name="route test",
        mission_id="route-test",
        selected_candidate_id="candidate-001",
        launch_site_mgrs="52SCB0000000000",
        target_mgrs="52SCB0001000000",
        route_candidates=(candidate,),
        warnings=(),
        config=RealTerrainRouteConfig(10.0, 10.0, 20.0, 2_400_000_000.0, 1.0),
        terrain_metadata=_metadata(),
        graph_nodes=nodes,
        graph_edges=(),
        summary=RealTerrainRouteSummary(2, 0, 2, 1),
        waypoint_handoffs=(handoff,),
        launch_ground_msl_m=100.0,
        snapped_launch_node_id=nodes[0].node_id,
        snapped_target_node_id=nodes[1].node_id,
        snapped_launch_node_mgrs=path[0].mgrs,
        snapped_target_node_mgrs=path[1].mgrs,
        launch_snap_distance_m=0.0,
        target_snap_distance_m=0.0,
    )


def test_route_config_accepts_reviewed_defaults_and_mode_policies() -> None:
    config = RealTerrainRouteConfig(
        graph_spacing_m=50.0,
        profile_spacing_m=25.0,
        allowed_flight_agl_m=60.0,
        frequency_hz=2_400_000_000.0,
        route_margin_m=100.0,
    )

    assert config.connectivity == 8
    assert route_mode_cost_policy(RouteMode.SHIELDING_MINIMUM).shielding_weight == 0.90
    assert route_mode_cost_policy(RouteMode.DETOUR_STABILITY).high_risk_multiplier == 2.0


@pytest.mark.parametrize("field,value", [("graph_spacing_m", True), ("connectivity", 4)])
def test_route_config_rejects_invalid_numeric_and_locked_connectivity(
    field: str, value: object
) -> None:
    values: dict[str, object] = {
        "graph_spacing_m": 50.0,
        "profile_spacing_m": 25.0,
        "allowed_flight_agl_m": 60.0,
        "frequency_hz": 2_400_000_000.0,
        "route_margin_m": 100.0,
        field: value,
    }

    with pytest.raises(RealTerrainRouteOutputError):
        RealTerrainRouteConfig(**values)  # type: ignore[arg-type]


def test_non_valid_node_has_no_fabricated_score_or_non_excluded_color() -> None:
    with pytest.raises(RealTerrainRouteOutputError, match="excluded route node"):
        RealTerrainRouteNode(
            node_id="route-node-r00000-c00000",
            row=0,
            column=0,
            projected_point=LocalPoint(0.0, 0.0),
            node_mgrs=None,
            terrain_msl_m=None,
            surface_msl_m=None,
            flight_agl_m=20.0,
            flight_msl_m=None,
            distance_3d_from_launch_m=None,
            within_operation_radius=False,
            state=RouteNodeState.OUTSIDE_OPERATION_RADIUS,
            traversable=False,
            reason="outside operation radius",
            shielding_stability_score=0.0,
            overall_score=None,
            color_class=ColorClass.EXCLUDED,
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_APPLICABLE,
            source_sensitive=None,
            source_zone_reason="source-zone not applicable",
            fresnel_diagnostics=None,
        )


def test_outside_radius_node_rejects_coordinated_radius_or_traversability_mutation() -> None:
    node = RealTerrainRouteNode(
        node_id="route-node-r00000-c00000",
        row=0,
        column=0,
        projected_point=LocalPoint(0.0, 0.0),
        node_mgrs=None,
        terrain_msl_m=100.0,
        surface_msl_m=100.0,
        flight_agl_m=20.0,
        flight_msl_m=120.0,
        distance_3d_from_launch_m=20.001,
        within_operation_radius=False,
        state=RouteNodeState.OUTSIDE_OPERATION_RADIUS,
        traversable=False,
        reason="outside operation radius",
        shielding_stability_score=None,
        overall_score=None,
        color_class=ColorClass.EXCLUDED,
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="source-zone provider not requested",
        fresnel_diagnostics=None,
    )

    with pytest.raises(RealTerrainRouteOutputError, match="radius flag false"):
        replace(node, within_operation_radius=True)
    with pytest.raises(RealTerrainRouteOutputError, match="valid_scored and traversable"):
        replace(node, traversable=True)


def test_complete_result_rejects_coordinated_removal_of_runtime_authority() -> None:
    result = _valid_runtime_result()

    with pytest.raises(RealTerrainRouteOutputError):
        replace(
            result,
            graph_nodes=(),
            graph_edges=(),
            summary=None,
            waypoint_handoffs=(),
            snapped_launch_node_id=None,
            snapped_target_node_id=None,
            snapped_launch_node_mgrs=None,
            snapped_target_node_mgrs=None,
            launch_snap_distance_m=None,
            target_snap_distance_m=None,
        )


@pytest.mark.parametrize(
    "candidate_change",
    [
        {"ordered_node_ids": ("route-node-r00000-c00001", "route-node-r00000-c00000")},
        {
            "path": (
                RealTerrainRoutePathPoint(0, "52SCB0001000000", 120.0),
                RealTerrainRoutePathPoint(1, "52SCB0000000000", 120.0),
            )
        },
    ],
)
def test_complete_result_rejects_candidate_endpoint_authority_mismatch(
    candidate_change: dict[str, object],
) -> None:
    result = _valid_runtime_result()
    candidate = replace(result.route_candidates[0], **candidate_change)

    with pytest.raises(RealTerrainRouteOutputError):
        replace(result, route_candidates=(candidate,))


def test_complete_result_rejects_snap_or_handoff_endpoint_mutation() -> None:
    result = _valid_runtime_result()
    handoff = list(result.waypoint_handoffs[0])
    handoff[0] = replace(handoff[0], projected_point=LocalPoint(10.0, 0.0))

    with pytest.raises(RealTerrainRouteOutputError):
        replace(result, waypoint_handoffs=(tuple(handoff),))
    with pytest.raises(RealTerrainRouteOutputError):
        replace(result, snapped_target_node_mgrs="52SCB0000000000")


@pytest.mark.parametrize(
    "result_change",
    [
        {"snapped_launch_node_id": "route-node-r00000-c00001"},
        {"snapped_target_node_id": "route-node-r00000-c00000"},
    ],
)
def test_complete_result_rejects_snap_node_id_endpoint_mutation(
    result_change: dict[str, object],
) -> None:
    with pytest.raises(RealTerrainRouteOutputError):
        replace(_valid_runtime_result(), **result_change)


def test_complete_result_accepts_one_node_zero_edge_same_snapped_endpoint() -> None:
    result = _valid_runtime_result()
    node = result.graph_nodes[0]
    candidate = replace(
        result.route_candidates[0],
        path=(result.route_candidates[0].path[0],),
        total_cost=0.0,
        total_distance_3d_m=0.0,
        ordered_node_ids=(node.node_id,),
        ordered_projected_points=(node.projected_point,),
    )
    handoff = (result.waypoint_handoffs[0][0],)

    same_node = replace(
        result,
        route_candidates=(candidate,),
        graph_nodes=(node,),
        graph_edges=(),
        summary=RealTerrainRouteSummary(1, 0, 1, 1),
        waypoint_handoffs=(handoff,),
        snapped_target_node_id=node.node_id,
        snapped_target_node_mgrs=candidate.path[0].mgrs,
    )

    assert same_node.route_candidates[0].total_distance_3d_m == 0.0
    assert same_node.waypoint_handoffs[0][0].point_mgrs == same_node.snapped_launch_node_mgrs
