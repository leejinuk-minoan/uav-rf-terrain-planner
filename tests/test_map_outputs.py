from dataclasses import fields
from pathlib import Path

import pytest

from uav_rf_terrain.map_outputs import (
    CandidateCellMapFeature,
    MapFeatureType,
    MapOutputError,
    MapOutputPackage,
    MapStyle,
    RouteMapFeature,
    WaypointMapFeature,
    build_candidate_cell_map_features,
    build_map_output_package,
    build_route_map_features,
    build_waypoint_map_features,
    format_map_output_summary,
    style_for_color_class,
    style_for_route_type,
    summarize_map_output_package,
)
from uav_rf_terrain.routing import RouteCandidateType
from uav_rf_terrain.scenario_outputs import build_synthetic_end_to_end_scenario
from uav_rf_terrain.schemas import ColorClass


def test_map_output_error_is_value_error() -> None:
    assert issubclass(MapOutputError, ValueError)


def test_map_feature_type_values() -> None:
    assert MapFeatureType.CANDIDATE_CELL == "candidate_cell"
    assert MapFeatureType.ROUTE == "route"
    assert MapFeatureType.WAYPOINT == "waypoint"


def test_map_style_validation_and_helpers() -> None:
    style = MapStyle("green", "#2ca02c", "#2ca02c", 1.0)
    assert style.color_name == "green"
    with pytest.raises(MapOutputError):
        MapStyle("", "#2ca02c", "#2ca02c")
    with pytest.raises(MapOutputError):
        MapStyle("green", "2ca02c", "#2ca02c")
    with pytest.raises(MapOutputError):
        MapStyle("green", "#2ca02c", "#2ca02c", 1.1)

    assert style_for_color_class(ColorClass.GREEN).fill_hex == "#2ca02c"
    assert style_for_color_class(ColorClass.YELLOW).fill_hex == "#ffdd57"
    assert style_for_color_class(ColorClass.ORANGE).fill_hex == "#ff7f0e"
    assert style_for_color_class(ColorClass.RED).fill_hex == "#d62728"
    assert style_for_color_class(ColorClass.EXCLUDED).fill_hex == "#808080"
    assert style_for_route_type(RouteCandidateType.SHIELDING_MINIMUM).fill_hex == "#1f77b4"
    assert style_for_route_type(RouteCandidateType.DISTANCE_SHIELDING_BALANCED).fill_hex == "#9467bd"
    assert style_for_route_type(RouteCandidateType.DETOUR_STABILITY).fill_hex == "#8c564b"


def make_candidate_feature() -> CandidateCellMapFeature:
    return CandidateCellMapFeature(
        "candidate-feature-000",
        "candidate-green",
        0.0,
        0.0,
        ColorClass.GREEN,
        style_for_color_class(ColorClass.GREEN),
        90.0,
        95.0,
        "green synthetic candidate",
    )


def make_route_feature() -> RouteMapFeature:
    return RouteMapFeature(
        "route-feature-000",
        "route-a",
        RouteCandidateType.SHIELDING_MINIMUM,
        ("route-a-wp-000",),
        1000.0,
        10.0,
        0,
        style_for_route_type(RouteCandidateType.SHIELDING_MINIMUM),
    )


def make_waypoint_feature() -> WaypointMapFeature:
    return WaypointMapFeature(
        "waypoint-feature-000",
        "route-a",
        "route-a-wp-000",
        0,
        0.0,
        0.0,
        0.0,
        120.0,
        220.0,
        120.0,
        ColorClass.GREEN,
        style_for_color_class(ColorClass.GREEN),
    )


def test_feature_validation_accepts_valid_features() -> None:
    assert make_candidate_feature().feature_id == "candidate-feature-000"
    assert make_route_feature().route_id == "route-a"
    assert make_waypoint_feature().waypoint_id == "route-a-wp-000"


def test_feature_validation_rejects_invalid_features() -> None:
    with pytest.raises(MapOutputError):
        CandidateCellMapFeature("", "candidate", 0.0, 0.0, ColorClass.GREEN, style_for_color_class(ColorClass.GREEN), 90.0, 90.0, "ok")
    with pytest.raises(MapOutputError):
        CandidateCellMapFeature("id", "candidate", float("nan"), 0.0, ColorClass.GREEN, style_for_color_class(ColorClass.GREEN), 90.0, 90.0, "ok")
    with pytest.raises(MapOutputError):
        CandidateCellMapFeature("id", "candidate", 0.0, 0.0, ColorClass.GREEN, style_for_color_class(ColorClass.GREEN), -0.1, 90.0, "ok")
    with pytest.raises(MapOutputError):
        RouteMapFeature("id", "route", "bad", ("wp",), 0.0, 0.0, 0, style_for_route_type(RouteCandidateType.SHIELDING_MINIMUM))  # type: ignore[arg-type]
    with pytest.raises(MapOutputError):
        RouteMapFeature("id", "route", RouteCandidateType.SHIELDING_MINIMUM, (), 0.0, 0.0, 0, style_for_route_type(RouteCandidateType.SHIELDING_MINIMUM))
    with pytest.raises(MapOutputError):
        RouteMapFeature("id", "route", RouteCandidateType.SHIELDING_MINIMUM, ("wp",), -1.0, 0.0, 0, style_for_route_type(RouteCandidateType.SHIELDING_MINIMUM))
    with pytest.raises(MapOutputError):
        WaypointMapFeature("id", "route", "wp", -1, 0.0, 0.0, 0.0, 120.0, 220.0, 120.0, ColorClass.GREEN, style_for_color_class(ColorClass.GREEN))
    with pytest.raises(MapOutputError):
        WaypointMapFeature("id", "route", "wp", 0, 0.0, 0.0, -1.0, 120.0, 220.0, 120.0, ColorClass.GREEN, style_for_color_class(ColorClass.GREEN))


def test_map_output_package_validation() -> None:
    package = MapOutputPackage(
        "scenario",
        (make_candidate_feature(),),
        (make_route_feature(),),
        (make_waypoint_feature(),),
        "route-a",
        {},
    )
    assert package.selected_route_id == "route-a"
    with pytest.raises(MapOutputError):
        MapOutputPackage("", (make_candidate_feature(),), (make_route_feature(),), (make_waypoint_feature(),), "route-a", {})
    with pytest.raises(MapOutputError):
        MapOutputPackage("scenario", (), (make_route_feature(),), (make_waypoint_feature(),), "route-a", {})
    with pytest.raises(MapOutputError):
        MapOutputPackage("scenario", (make_candidate_feature(),), (make_route_feature(),), (make_waypoint_feature(),), "missing", {})


def test_builders_return_expected_feature_records() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    candidate_features = build_candidate_cell_map_features(scenario.candidates)
    route_features = build_route_map_features(scenario.routes)
    waypoint_features = build_waypoint_map_features(scenario.routes)
    package = build_map_output_package(scenario)

    assert len(candidate_features) == len(scenario.candidates)
    assert candidate_features[1].x_m == 500.0
    assert len(route_features) == len(scenario.routes)
    assert all(feature.point_ids for feature in route_features)
    assert waypoint_features
    assert package.selected_route_id == scenario.selected_route_id


def test_summary_contains_required_keys_and_counts() -> None:
    package = build_map_output_package(build_synthetic_end_to_end_scenario())
    summary = summarize_map_output_package(package)

    required_keys = {
        "scenario_name",
        "candidate_feature_count",
        "route_feature_count",
        "waypoint_feature_count",
        "selected_route_id",
        "green_candidate_feature_count",
        "yellow_candidate_feature_count",
        "orange_candidate_feature_count",
        "red_candidate_feature_count",
        "excluded_candidate_feature_count",
        "red_waypoint_feature_count",
        "orange_waypoint_feature_count",
    }
    assert required_keys.issubset(summary.keys())
    assert summary["green_candidate_feature_count"] == 1
    assert summary["yellow_candidate_feature_count"] == 1
    assert summary["orange_candidate_feature_count"] == 1
    assert summary["red_candidate_feature_count"] == 1
    assert summary["excluded_candidate_feature_count"] == 1
    assert isinstance(summary["red_waypoint_feature_count"], int)
    assert isinstance(summary["orange_waypoint_feature_count"], int)


def test_format_map_output_summary_returns_string_and_mentions_boundary() -> None:
    package = build_map_output_package(build_synthetic_end_to_end_scenario())
    output = format_map_output_summary(package).lower()

    assert isinstance(output, str)
    assert "map-ready data" in output
    assert "not a rendered map" in output


def test_map_outputs_module_imports_no_disallowed_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/map_outputs.py").read_text(encoding="utf-8").lower()
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


def test_map_output_structures_contain_no_link_or_command_fields() -> None:
    blocked = {
        "rs" + "si",
        "si" + "nr",
        "packet_" + "loss",
        "flight_" + "command",
        "flight_" + "commands",
        "auto" + "pilot",
        "control_" + "api",
        "control_" + "mode",
        "execution_" + "plan",
    }
    for dataclass_type in (CandidateCellMapFeature, RouteMapFeature, WaypointMapFeature, MapOutputPackage):
        field_names = {field.name for field in fields(dataclass_type)}
        assert field_names.isdisjoint(blocked)


def test_example_file_contains_no_file_loading_or_render_dependency() -> None:
    example_text = Path("examples/synthetic_map_output.py").read_text(encoding="utf-8").lower()
    blocked = (
        "read_" + "file(",
        "o" + "pen(",
        "ras" + "ter",
        "geo" + "tiff",
        "dem_" + "path",
        "dsm_" + "path",
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "fo" + "lium",
        "stream" + "lit",
        "os" + "geo",
        "tile" + "layer",
    )
    for term in blocked:
        assert term not in example_text
