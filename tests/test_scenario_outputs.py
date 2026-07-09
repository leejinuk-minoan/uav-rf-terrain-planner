from dataclasses import fields
from pathlib import Path

import pytest

from uav_rf_terrain.routing import RouteCandidate
from uav_rf_terrain.scenario_outputs import (
    ScenarioOutputError,
    SyntheticCandidateRecord,
    SyntheticEndToEndScenario,
    SyntheticRouteOutput,
    build_synthetic_candidate_records,
    build_synthetic_end_to_end_scenario,
    build_synthetic_route_outputs,
    format_synthetic_end_to_end_summary,
    summarize_synthetic_end_to_end_scenario,
)
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.scoring import CandidateScore, compute_candidate_score
from uav_rf_terrain.waypoints import RouteWaypointReport


def make_candidate_score() -> CandidateScore:
    return compute_candidate_score(
        distance_3d_m=1_000.0,
        operating_radius_m=5_000.0,
        dsm_los_score=100.0,
        dsm_fresnel_score=90.0,
    )


def make_candidate_record(candidate_id: str = "candidate") -> SyntheticCandidateRecord:
    return SyntheticCandidateRecord(
        candidate_id=candidate_id,
        candidate_score=make_candidate_score(),
        color_class=ColorClass.GREEN,
        within_operation_radius=True,
        reason="green synthetic candidate",
    )


def make_route_output() -> SyntheticRouteOutput:
    return build_synthetic_route_outputs()[0]


def test_synthetic_candidate_record_validation_accepts_valid_record() -> None:
    record = make_candidate_record()

    assert record.candidate_id == "candidate"
    assert isinstance(record.candidate_score, CandidateScore)
    assert record.color_class is ColorClass.GREEN


@pytest.mark.parametrize(
    "kwargs",
    [
        {"candidate_id": ""},
        {"candidate_score": "not-score"},
        {"color_class": "green"},
        {"within_operation_radius": "true"},
        {"reason": ""},
    ],
)
def test_synthetic_candidate_record_validation_rejects_invalid_values(
    kwargs: dict[str, object],
) -> None:
    defaults: dict[str, object] = {
        "candidate_id": "candidate",
        "candidate_score": make_candidate_score(),
        "color_class": ColorClass.GREEN,
        "within_operation_radius": True,
        "reason": "green synthetic candidate",
    }
    defaults.update(kwargs)

    with pytest.raises(ScenarioOutputError):
        SyntheticCandidateRecord(**defaults)  # type: ignore[arg-type]


def test_synthetic_route_output_validation_accepts_valid_output() -> None:
    route_output = make_route_output()

    assert isinstance(route_output.route_candidate, RouteCandidate)
    assert isinstance(route_output.waypoint_report, RouteWaypointReport)
    assert route_output.route_candidate.route_id == route_output.waypoint_report.route_id


def test_synthetic_route_output_validation_rejects_invalid_types() -> None:
    route_output = make_route_output()

    with pytest.raises(ScenarioOutputError):
        SyntheticRouteOutput(  # type: ignore[arg-type]
            route_candidate="not-route",
            waypoint_report=route_output.waypoint_report,
        )
    with pytest.raises(ScenarioOutputError):
        SyntheticRouteOutput(  # type: ignore[arg-type]
            route_candidate=route_output.route_candidate,
            waypoint_report="not-waypoint-report",
        )


def test_synthetic_route_output_validation_rejects_route_id_mismatch() -> None:
    route_output = make_route_output()
    other_report = build_synthetic_route_outputs()[1].waypoint_report

    assert route_output.route_candidate.route_id != other_report.route_id
    with pytest.raises(ScenarioOutputError, match="route_id"):
        SyntheticRouteOutput(
            route_candidate=route_output.route_candidate,
            waypoint_report=other_report,
        )


def test_synthetic_end_to_end_scenario_validation_accepts_valid_scenario() -> None:
    route_output = make_route_output()
    scenario = SyntheticEndToEndScenario(
        scenario_name="scenario",
        candidates=(make_candidate_record(),),
        routes=(route_output,),
        selected_route_id=route_output.route_candidate.route_id,
        summary={},
    )

    assert scenario.scenario_name == "scenario"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scenario_name": ""},
        {"candidates": ()},
        {"candidates": ("not-candidate",)},
        {"routes": ()},
        {"routes": ("not-route-output",)},
        {"selected_route_id": "not-present"},
        {"summary": "not-dict"},
    ],
)
def test_synthetic_end_to_end_scenario_validation_rejects_invalid_values(
    kwargs: dict[str, object],
) -> None:
    route_output = make_route_output()
    defaults: dict[str, object] = {
        "scenario_name": "scenario",
        "candidates": (make_candidate_record(),),
        "routes": (route_output,),
        "selected_route_id": route_output.route_candidate.route_id,
        "summary": {},
    }
    defaults.update(kwargs)

    with pytest.raises(ScenarioOutputError):
        SyntheticEndToEndScenario(**defaults)  # type: ignore[arg-type]


def test_build_synthetic_candidate_records_returns_non_empty_records() -> None:
    records = build_synthetic_candidate_records()

    assert records
    assert all(isinstance(record, SyntheticCandidateRecord) for record in records)


def test_candidate_records_include_all_color_classes() -> None:
    records = build_synthetic_candidate_records()
    color_classes = {record.color_class for record in records}

    assert ColorClass.GREEN in color_classes
    assert ColorClass.YELLOW in color_classes
    assert ColorClass.ORANGE in color_classes
    assert ColorClass.RED in color_classes
    assert ColorClass.EXCLUDED in color_classes


def test_candidate_records_use_candidate_score_and_existing_color_class() -> None:
    records = build_synthetic_candidate_records()

    assert all(isinstance(record.candidate_score, CandidateScore) for record in records)
    assert all(isinstance(record.color_class, ColorClass) for record in records)


def test_build_synthetic_route_outputs_returns_exactly_three_routes() -> None:
    routes = build_synthetic_route_outputs()

    assert len(routes) == 3
    assert all(isinstance(route, SyntheticRouteOutput) for route in routes)


def test_route_outputs_include_route_candidate_and_waypoint_report() -> None:
    routes = build_synthetic_route_outputs()

    for route in routes:
        assert isinstance(route.route_candidate, RouteCandidate)
        assert isinstance(route.waypoint_report, RouteWaypointReport)
        assert route.route_candidate.route_id == route.waypoint_report.route_id


def test_build_synthetic_end_to_end_scenario_returns_valid_scenario() -> None:
    scenario = build_synthetic_end_to_end_scenario()

    assert isinstance(scenario, SyntheticEndToEndScenario)
    assert scenario.scenario_name == "synthetic-e2e-default"
    assert scenario.candidates
    assert scenario.routes
    assert scenario.summary


def test_selected_route_id_belongs_to_routes() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    route_ids = {route.route_candidate.route_id for route in scenario.routes}

    assert scenario.selected_route_id in route_ids


def test_summary_contains_required_keys() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    summary = summarize_synthetic_end_to_end_scenario(scenario)

    required_keys = {
        "scenario_name",
        "candidate_count",
        "green_candidate_count",
        "yellow_candidate_count",
        "orange_candidate_count",
        "red_candidate_count",
        "excluded_candidate_count",
        "route_count",
        "selected_route_id",
        "selected_route_cost",
        "selected_route_total_distance_m",
        "selected_route_waypoint_count",
        "selected_route_red_waypoint_count",
        "selected_route_orange_waypoint_count",
    }
    assert required_keys.issubset(summary.keys())


def test_candidate_color_counts_are_correct() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    summary = scenario.summary

    assert summary["candidate_count"] == 5
    assert summary["green_candidate_count"] == 1
    assert summary["yellow_candidate_count"] == 1
    assert summary["orange_candidate_count"] == 1
    assert summary["red_candidate_count"] == 1
    assert summary["excluded_candidate_count"] == 1


def test_selected_route_summary_values_are_present() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    summary = scenario.summary

    assert isinstance(summary["selected_route_id"], str)
    assert isinstance(summary["selected_route_cost"], float)
    assert isinstance(summary["selected_route_total_distance_m"], float)
    assert isinstance(summary["selected_route_waypoint_count"], int)
    assert isinstance(summary["selected_route_red_waypoint_count"], int)
    assert isinstance(summary["selected_route_orange_waypoint_count"], int)


def test_format_synthetic_end_to_end_summary_returns_string() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    output = format_synthetic_end_to_end_summary(scenario)

    assert isinstance(output, str)
    assert scenario.scenario_name in output
    assert scenario.selected_route_id in output


def test_format_output_mentions_synthetic_or_offline() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    output = format_synthetic_end_to_end_summary(scenario).lower()

    assert "synthetic" in output
    assert "offline" in output


def test_scenario_outputs_module_has_no_map_or_gis_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/scenario_outputs.py").read_text(encoding="utf-8").lower()

    prohibited_imports = ("rasterio", "gdal", "geopandas", "folium", "streamlit", "osgeo")
    for prohibited_import in prohibited_imports:
        assert prohibited_import not in module_text


def test_scenario_output_structures_have_no_link_metric_fields() -> None:
    for dataclass_type in (SyntheticCandidateRecord, SyntheticRouteOutput, SyntheticEndToEndScenario):
        field_names = {field.name for field in fields(dataclass_type)}
        assert "rssi" not in field_names
        assert "sinr" not in field_names
        assert "packet_loss" not in field_names


def test_scenario_output_structures_have_no_command_or_control_fields() -> None:
    prohibited_fields = {
        "flight_command",
        "flight_commands",
        "autopilot",
        "control_api",
        "control_mode",
        "execution_plan",
    }
    for dataclass_type in (SyntheticCandidateRecord, SyntheticRouteOutput, SyntheticEndToEndScenario):
        field_names = {field.name for field in fields(dataclass_type)}
        assert field_names.isdisjoint(prohibited_fields)


def test_example_file_contains_no_real_dem_dsm_loading_or_map_rendering() -> None:
    example_text = Path("examples/synthetic_end_to_end.py").read_text(encoding="utf-8").lower()

    prohibited_terms = (
        "rasterio",
        "gdal",
        "geopandas",
        "folium",
        "streamlit",
        "osgeo",
        "read_file(",
        "open(",
        "map.render",
        "tilelayer",
    )
    for prohibited_term in prohibited_terms:
        assert prohibited_term not in example_text
