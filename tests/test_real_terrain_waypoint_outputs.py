from __future__ import annotations

from dataclasses import replace

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
from uav_rf_terrain.real_terrain_route_outputs import RouteMode
from uav_rf_terrain.real_terrain_waypoint_outputs import (
    RealTerrainRouteWaypointReport,
    RealTerrainWaypointConfig,
    RealTerrainWaypointOutputError,
    RealTerrainWaypointRecord,
    RealTerrainWaypointResult,
    RealTerrainWaypointSummary,
    WaypointElevationSemantics,
    WaypointValueSemantics,
)
from uav_rf_terrain.schemas import ColorClass


_MGRS = "52SCB0000000000"


def _record(mode: RouteMode = RouteMode.SHIELDING_MINIMUM) -> RealTerrainWaypointRecord:
    return RealTerrainWaypointRecord(
        waypoint_id=f"route-{mode.value}-wp-000",
        route_id=f"route-{mode.value}",
        route_mode=mode,
        sequence_index=0,
        target_interval_index=None,
        projected_point=LocalPoint(0.0, 0.0),
        mgrs=_MGRS,
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
        left_source_point_id=f"route-{mode.value}-handoff-000",
        right_source_point_id=f"route-{mode.value}-handoff-000",
        interpolation_fraction=0.0,
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="source-zone provider not requested",
    )


def _zero_report(mode: RouteMode) -> RealTerrainRouteWaypointReport:
    route_id = f"route-{mode.value}"
    warnings = (
        f"{route_id}: route shorter than requested waypoint spacing",
        f"{route_id}: zero-distance route produced one waypoint",
    )
    return RealTerrainRouteWaypointReport(
        route_id=route_id,
        route_mode=mode,
        path_semantics="snapped_graph_path",
        waypoint_spacing_m=500.0,
        total_route_distance_3d_m=0.0,
        waypoints=(_record(mode),),
        warnings=warnings,
    )


def _result(modes: tuple[RouteMode, ...] = (RouteMode.SHIELDING_MINIMUM,)) -> RealTerrainWaypointResult:
    reports = tuple(_zero_report(mode) for mode in modes)
    warnings = tuple(warning for report in reports for warning in report.warnings)
    return RealTerrainWaypointResult(
        scenario_name="waypoint output test",
        mission_id="waypoint-output-test",
        selected_candidate_id="candidate-001",
        launch_site_mgrs=_MGRS,
        target_mgrs=_MGRS,
        config=RealTerrainWaypointConfig(),
        launch_ground_msl_m=100.0,
        source_route_ids=tuple(f"route-{mode.value}" for mode in modes),
        source_route_modes=modes,
        source_route_total_distance_3d_m=tuple(0.0 for _ in modes),
        snapped_launch_node_mgrs=_MGRS,
        snapped_target_node_mgrs=_MGRS,
        route_reports=reports,
        summary=RealTerrainWaypointSummary(len(reports), len(reports), warnings),
        warnings=warnings,
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
        replace(record, source_zone_state=SourceZoneAvailability.AVAILABLE)


@pytest.mark.parametrize("fraction", (0.0, 1.0, -0.1, 1.1))
def test_interpolated_record_requires_strict_interior_fraction(fraction: float) -> None:
    record = _record()
    with pytest.raises(RealTerrainWaypointOutputError, match="interpolated"):
        replace(
            record,
            value_semantics=WaypointValueSemantics.SEGMENT_CONSERVATIVE_PROXY,
            elevation_semantics=WaypointElevationSemantics.ENDPOINT_LINEAR_INTERPOLATION,
            right_source_point_id="route-shielding_minimum-handoff-001",
            interpolation_fraction=fraction,
        )


def test_route_report_requires_ordered_nonempty_waypoints() -> None:
    record = _record()
    report = _zero_report(RouteMode.SHIELDING_MINIMUM)
    assert report.waypoints[0].mgrs == _MGRS
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


@pytest.mark.parametrize("count", (1, 2, 3))
def test_result_validates_one_two_and_three_ordered_route_sets(count: int) -> None:
    modes = tuple(RouteMode)[:count]
    result = _result(modes)
    assert result.summary.route_count == count
    assert tuple(report.route_mode for report in result.route_reports) == modes
    assert result.summary.warnings == result.warnings


def test_result_keeps_private_authority_and_cross_validates_mutations() -> None:
    result = _result()
    public = result.to_public_dict()
    assert "launch_ground_msl_m" not in public
    assert "source_route_ids" not in public
    assert "snapped_target_node_mgrs" not in public

    object.__setattr__(result, "source_route_total_distance_3d_m", (1.0,))
    with pytest.raises(RealTerrainWaypointOutputError, match="total"):
        result.__post_init__()

    snapped_result = _result()
    object.__setattr__(snapped_result, "snapped_target_node_mgrs", "52SCB0000000001")
    with pytest.raises(RealTerrainWaypointOutputError, match="endpoints"):
        snapped_result.__post_init__()

    height_result = _result()
    object.__setattr__(height_result.route_reports[0].waypoints[0], "height_difference_from_launch_m", 21.0)
    with pytest.raises(RealTerrainWaypointOutputError, match="height difference"):
        height_result.__post_init__()


def test_result_rejects_coordinated_authority_and_warning_mutation() -> None:
    result = _result()
    object.__setattr__(result, "source_route_ids", ())
    object.__setattr__(result, "source_route_modes", ())
    object.__setattr__(result, "source_route_total_distance_3d_m", ())
    object.__setattr__(result, "route_reports", ())
    object.__setattr__(result, "summary", RealTerrainWaypointSummary(0, 0, ()))
    object.__setattr__(result, "warnings", ())
    with pytest.raises(RealTerrainWaypointOutputError, match="route reports"):
        result.__post_init__()

    warning_result = _result()
    object.__setattr__(warning_result, "warnings", ())
    with pytest.raises(RealTerrainWaypointOutputError, match="warnings"):
        warning_result.__post_init__()

    with pytest.raises(RealTerrainWaypointOutputError, match="warnings"):
        replace(
            _result(),
            summary=RealTerrainWaypointSummary(1, 1, ()),
            warnings=(),
        )
