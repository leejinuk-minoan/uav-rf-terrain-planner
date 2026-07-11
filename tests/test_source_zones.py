from dataclasses import fields
from pathlib import Path

import pytest

from uav_rf_terrain.map_outputs import build_map_output_package, format_map_output_summary
from uav_rf_terrain.routing import RouteCandidate, RouteCell, build_route_candidate
from uav_rf_terrain.scenario_outputs import build_synthetic_end_to_end_scenario
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.source_zones import (
    SourceZoneError,
    SourceZoneSummary,
    TerrainSourceZone,
    is_source_sensitive_zone,
    summarize_source_zones,
)
from uav_rf_terrain.waypoints import WaypointSourcePoint, build_route_waypoints, summarize_waypoint_report
from uav_rf_terrain.routing import RouteCandidateType


def test_terrain_source_zone_values() -> None:
    assert TerrainSourceZone.ESA_DERIVED == "esa_derived"
    assert TerrainSourceZone.WMS_GAP_FILLED == "wms_gap_filled"
    assert TerrainSourceZone.DEM_ONLY_FALLBACK == "dem_only_fallback"
    assert TerrainSourceZone.MIXED_BOUNDARY == "mixed_boundary"


def test_source_zone_summary_for_esa_only_is_not_source_sensitive() -> None:
    summary = summarize_source_zones((TerrainSourceZone.ESA_DERIVED, TerrainSourceZone.ESA_DERIVED))

    assert summary.esa_derived_count == 2
    assert summary.dominant_zone is TerrainSourceZone.ESA_DERIVED
    assert summary.source_sensitive is False


def test_source_zone_summary_flags_wms_dem_only_mixed_and_multiple_zones() -> None:
    summary = summarize_source_zones(
        (
            TerrainSourceZone.ESA_DERIVED,
            TerrainSourceZone.WMS_GAP_FILLED,
            TerrainSourceZone.DEM_ONLY_FALLBACK,
            TerrainSourceZone.MIXED_BOUNDARY,
        )
    )

    assert summary.esa_derived_count == 1
    assert summary.wms_gap_filled_count == 1
    assert summary.dem_only_fallback_count == 1
    assert summary.mixed_boundary_count == 1
    assert summary.source_sensitive is True
    assert summary.dominant_zone is TerrainSourceZone.MIXED_BOUNDARY


@pytest.mark.parametrize(
    "zone",
    [
        TerrainSourceZone.WMS_GAP_FILLED,
        TerrainSourceZone.DEM_ONLY_FALLBACK,
        TerrainSourceZone.MIXED_BOUNDARY,
    ],
)
def test_non_esa_zones_are_source_sensitive(zone: TerrainSourceZone) -> None:
    assert is_source_sensitive_zone(zone) is True


def test_empty_or_invalid_zone_summary_raises() -> None:
    with pytest.raises(SourceZoneError):
        summarize_source_zones(())
    with pytest.raises(SourceZoneError):
        summarize_source_zones(("esa_derived",))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"esa_derived_count": -1},
        {"wms_gap_filled_count": True},
        {"dominant_zone": "esa_derived"},
        {"source_sensitive": "no"},
        {"reason": ""},
    ],
)
def test_source_zone_summary_validation_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    defaults: dict[str, object] = {
        "esa_derived_count": 1,
        "wms_gap_filled_count": 0,
        "dem_only_fallback_count": 0,
        "mixed_boundary_count": 0,
        "dominant_zone": TerrainSourceZone.ESA_DERIVED,
        "source_sensitive": False,
        "reason": "ESA-derived source zone only.",
    }
    defaults.update(kwargs)

    with pytest.raises(SourceZoneError):
        SourceZoneSummary(**defaults)  # type: ignore[arg-type]


def test_route_cell_and_candidate_carry_source_zone_summary() -> None:
    cells = (
        RouteCell("cell-0", 0.0, ColorClass.GREEN, 90.0, 85.0, TerrainSourceZone.ESA_DERIVED),
        RouteCell("cell-1", 100.0, ColorClass.YELLOW, 80.0, 75.0, TerrainSourceZone.WMS_GAP_FILLED),
    )
    route = build_route_candidate(
        route_id="route-source-zone",
        route_type=RouteCandidateType.SHIELDING_MINIMUM,
        cells=cells,
        distance_normalizer_m=1000.0,
    )

    assert isinstance(route, RouteCandidate)
    assert route.source_zone_summary.source_sensitive is True
    assert route.source_zone_summary.wms_gap_filled_count == 1


def test_waypoints_carry_source_zone_and_summary_counts() -> None:
    source_points = (
        WaypointSourcePoint("p0", 0.0, 0.0, 100.0, 105.0, 0.0, ColorClass.GREEN, 90.0, 85.0),
        WaypointSourcePoint(
            "p1",
            500.0,
            0.0,
            102.0,
            102.0,
            500.0,
            ColorClass.GREEN,
            88.0,
            82.0,
            TerrainSourceZone.DEM_ONLY_FALLBACK,
        ),
    )
    report = build_route_waypoints(
        route_id="route-source-zone",
        source_points=source_points,
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )
    summary = summarize_waypoint_report(report)

    assert report.waypoints[1].source_zone is TerrainSourceZone.DEM_ONLY_FALLBACK
    assert summary["dem_only_fallback_waypoint_count"] == 1
    assert summary["source_sensitive_waypoint_count"] == 1
    assert summary["waypoint_source_sensitive"] is True


def test_synthetic_scenario_includes_all_source_zones() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    candidate_zones = {candidate.source_zone for candidate in scenario.candidates}
    route_zones = {
        cell.source_zone
        for route_output in scenario.routes
        for cell in route_output.route_candidate.cells
    }
    waypoint_zones = {
        waypoint.source_zone
        for route_output in scenario.routes
        for waypoint in route_output.waypoint_report.waypoints
    }

    for zone in TerrainSourceZone:
        assert zone in candidate_zones
        assert zone in route_zones
        assert zone in waypoint_zones


def test_synthetic_summary_includes_source_sensitive_counts() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    summary = scenario.summary

    assert summary["esa_candidate_count"] == 2
    assert summary["wms_gap_filled_candidate_count"] == 1
    assert summary["dem_only_fallback_candidate_count"] == 1
    assert summary["mixed_boundary_candidate_count"] == 1
    assert summary["source_sensitive_candidate_count"] == 3
    assert summary["selected_route_source_sensitive"] is True
    assert isinstance(summary["selected_route_dem_only_fallback_waypoint_count"], int)


def test_map_output_features_include_source_zone_flags() -> None:
    package = build_map_output_package(build_synthetic_end_to_end_scenario())

    assert any(feature.source_sensitive for feature in package.candidate_features)
    assert any(feature.source_sensitive for feature in package.route_features)
    assert any(feature.source_sensitive for feature in package.waypoint_features)
    assert package.summary["source_sensitive_candidate_feature_count"] == 3
    assert package.summary["source_sensitive_route_feature_count"] >= 1
    assert package.summary["source_sensitive_waypoint_feature_count"] >= 1


def test_map_output_summary_mentions_source_sensitive_count() -> None:
    package = build_map_output_package(build_synthetic_end_to_end_scenario())
    output = format_map_output_summary(package)

    assert "Source-sensitive candidates" in output
    assert "map-ready data" in output
    assert "not a rendered map" in output


def test_source_zone_fields_do_not_add_link_or_command_fields() -> None:
    blocked = {
        "rs" + "si",
        "si" + "nr",
        "packet_" + "loss",
        "flight_" + "command",
        "auto" + "pilot",
        "control_" + "api",
    }
    for dataclass_type in (RouteCell, WaypointSourcePoint):
        field_names = {field.name for field in fields(dataclass_type)}
        assert field_names.isdisjoint(blocked)


def test_source_zone_module_uses_no_gis_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/source_zones.py").read_text(encoding="utf-8").lower()
    blocked = (
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "fo" + "lium",
        "stream" + "lit",
        "os" + "geo",
    )
    for name in blocked:
        assert name not in module_text
