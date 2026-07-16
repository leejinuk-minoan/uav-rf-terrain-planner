from __future__ import annotations

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
from uav_rf_terrain.real_terrain_route_outputs import RouteMode
from uav_rf_terrain.real_terrain_waypoint_outputs import (
    RealTerrainRouteWaypointReport,
    RealTerrainWaypointConfig,
    RealTerrainWaypointOutputError,
    RealTerrainWaypointRecord,
    WaypointElevationSemantics,
    WaypointValueSemantics,
)
from uav_rf_terrain.schemas import ColorClass


def _record() -> RealTerrainWaypointRecord:
    return RealTerrainWaypointRecord(
        waypoint_id="route-shielding_minimum-wp-000",
        route_id="route-shielding_minimum",
        route_mode=RouteMode.SHIELDING_MINIMUM,
        sequence_index=0,
        target_interval_index=None,
        projected_point=LocalPoint(0.0, 0.0),
        mgrs="52SCB0000000000",
        cumulative_distance_3d_m=0.0,
        segment_distance_from_previous_3d_m=0.0,
        terrain_msl_m=100.0,
        surface_msl_m=102.0,
        flight_agl_m=20.0,
        flight_msl_m=120.0,
        height_difference_from_launch_m=20.0,
        color_class=ColorClass.GREEN,
        shielding_stability_score=90.0,
        overall_score=88.0,
        value_semantics=WaypointValueSemantics.SOURCE_NODE,
        elevation_semantics=WaypointElevationSemantics.SOURCE_NODE,
        left_source_point_id="route-shielding_minimum-handoff-000",
        right_source_point_id="route-shielding_minimum-handoff-000",
        interpolation_fraction=0.0,
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="source-zone provider not requested",
    )


def test_config_and_record_enforce_fixed_public_contract() -> None:
    assert RealTerrainWaypointConfig().spacing_m == 500.0
    with pytest.raises(RealTerrainWaypointOutputError):
        RealTerrainWaypointConfig(mgrs_precision=4)
    with pytest.raises(RealTerrainWaypointOutputError):
        RealTerrainWaypointConfig(spacing_m=True)
    record = _record()
    assert record.route_mode is RouteMode.SHIELDING_MINIMUM
    with pytest.raises(RealTerrainWaypointOutputError):
        _record().__class__(**{**record.__dict__, "source_zone_state": SourceZoneAvailability.AVAILABLE})


def test_route_report_requires_ordered_nonempty_waypoints() -> None:
    record = _record()
    report = RealTerrainRouteWaypointReport(
        route_id=record.route_id,
        route_mode=record.route_mode,
        path_semantics="snapped_graph_path",
        waypoint_spacing_m=500.0,
        total_route_distance_3d_m=0.0,
        waypoints=(record,),
        warnings=(),
    )
    assert report.waypoints[0].mgrs == "52SCB0000000000"
    with pytest.raises(RealTerrainWaypointOutputError):
        RealTerrainRouteWaypointReport(
            route_id=record.route_id,
            route_mode=record.route_mode,
            path_semantics="wrong",
            waypoint_spacing_m=500.0,
            total_route_distance_3d_m=0.0,
            waypoints=(record,),
            warnings=(),
        )
