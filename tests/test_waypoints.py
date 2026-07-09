from dataclasses import fields
from math import isclose
from pathlib import Path

import pytest

from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.waypoints import (
    RouteWaypoint,
    RouteWaypointReport,
    WaypointError,
    WaypointSamplingConfig,
    WaypointSourcePoint,
    build_route_waypoints,
    compute_flight_msl_m,
    compute_height_difference_from_launch_m,
    select_waypoint_source_points,
    summarize_waypoint_report,
)


def make_source_point(
    point_id: str,
    *,
    cumulative_distance_m: float,
    color_class: ColorClass = ColorClass.GREEN,
    terrain_msl_m: float = 100.0,
    surface_msl_m: float | None = None,
    shielding_stability_score: float = 90.0,
    overall_score: float = 85.0,
) -> WaypointSourcePoint:
    resolved_surface_msl_m = terrain_msl_m + 5.0 if surface_msl_m is None else surface_msl_m
    return WaypointSourcePoint(
        point_id=point_id,
        x_m=cumulative_distance_m,
        y_m=0.0,
        terrain_msl_m=terrain_msl_m,
        surface_msl_m=resolved_surface_msl_m,
        cumulative_distance_m=cumulative_distance_m,
        color_class=color_class,
        shielding_stability_score=shielding_stability_score,
        overall_score=overall_score,
    )


def sample_source_points() -> tuple[WaypointSourcePoint, ...]:
    return (
        make_source_point("p000", cumulative_distance_m=0.0, terrain_msl_m=100.0),
        make_source_point("p250", cumulative_distance_m=250.0, terrain_msl_m=105.0),
        make_source_point("p500", cumulative_distance_m=500.0, terrain_msl_m=110.0),
        make_source_point("p750", cumulative_distance_m=750.0, terrain_msl_m=115.0),
        make_source_point(
            "p1000",
            cumulative_distance_m=1000.0,
            color_class=ColorClass.ORANGE,
            terrain_msl_m=120.0,
        ),
        make_source_point(
            "p1500",
            cumulative_distance_m=1500.0,
            color_class=ColorClass.RED,
            terrain_msl_m=125.0,
        ),
    )


def test_waypoint_source_point_validation_accepts_valid_point() -> None:
    point = make_source_point("valid", cumulative_distance_m=0.0)

    assert point.point_id == "valid"
    assert point.color_class is ColorClass.GREEN


@pytest.mark.parametrize(
    "kwargs",
    [
        {"point_id": ""},
        {"x_m": float("nan")},
        {"y_m": float("inf")},
        {"terrain_msl_m": float("nan")},
        {"surface_msl_m": float("nan")},
        {"cumulative_distance_m": -1.0},
        {"surface_msl_m": 99.0},
        {"color_class": "green"},
        {"color_class": ColorClass.EXCLUDED},
        {"shielding_stability_score": -0.1},
        {"overall_score": 100.1},
    ],
)
def test_waypoint_source_point_validation_rejects_invalid_values(
    kwargs: dict[str, object],
) -> None:
    defaults: dict[str, object] = {
        "point_id": "p",
        "x_m": 0.0,
        "y_m": 0.0,
        "terrain_msl_m": 100.0,
        "surface_msl_m": 105.0,
        "cumulative_distance_m": 0.0,
        "color_class": ColorClass.GREEN,
        "shielding_stability_score": 90.0,
        "overall_score": 80.0,
    }
    defaults.update(kwargs)

    with pytest.raises(WaypointError):
        WaypointSourcePoint(**defaults)  # type: ignore[arg-type]


def test_waypoint_sampling_config_validation_accepts_defaults() -> None:
    config = WaypointSamplingConfig()

    assert config.spacing_m == 500.0
    assert config.include_start is True
    assert config.include_end is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"spacing_m": 0.0},
        {"spacing_m": -1.0},
        {"spacing_m": float("nan")},
        {"include_start": "yes"},
        {"include_end": 1},
    ],
)
def test_waypoint_sampling_config_validation_rejects_invalid_values(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(WaypointError):
        WaypointSamplingConfig(**kwargs)  # type: ignore[arg-type]


def make_route_waypoint(sequence_index: int = 0) -> RouteWaypoint:
    return RouteWaypoint(
        waypoint_id=f"route-wp-{sequence_index:03d}",
        sequence_index=sequence_index,
        source_point_id=f"p{sequence_index}",
        x_m=0.0,
        y_m=0.0,
        cumulative_distance_m=0.0,
        segment_distance_from_previous_m=0.0,
        terrain_msl_m=100.0,
        surface_msl_m=105.0,
        flight_agl_m=120.0,
        flight_msl_m=220.0,
        height_difference_from_launch_m=120.0,
        color_class=ColorClass.GREEN,
        shielding_stability_score=90.0,
        overall_score=80.0,
    )


def test_route_waypoint_validation_accepts_valid_waypoint() -> None:
    waypoint = make_route_waypoint()

    assert waypoint.waypoint_id == "route-wp-000"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"waypoint_id": ""},
        {"sequence_index": -1},
        {"sequence_index": True},
        {"source_point_id": ""},
        {"x_m": float("nan")},
        {"cumulative_distance_m": -1.0},
        {"segment_distance_from_previous_m": -1.0},
        {"surface_msl_m": 99.0},
        {"flight_agl_m": -1.0},
        {"flight_msl_m": float("inf")},
        {"height_difference_from_launch_m": float("nan")},
        {"color_class": ColorClass.EXCLUDED},
        {"shielding_stability_score": 101.0},
        {"overall_score": -0.1},
    ],
)
def test_route_waypoint_validation_rejects_invalid_values(
    kwargs: dict[str, object],
) -> None:
    defaults: dict[str, object] = {
        "waypoint_id": "route-wp-000",
        "sequence_index": 0,
        "source_point_id": "p0",
        "x_m": 0.0,
        "y_m": 0.0,
        "cumulative_distance_m": 0.0,
        "segment_distance_from_previous_m": 0.0,
        "terrain_msl_m": 100.0,
        "surface_msl_m": 105.0,
        "flight_agl_m": 120.0,
        "flight_msl_m": 220.0,
        "height_difference_from_launch_m": 120.0,
        "color_class": ColorClass.GREEN,
        "shielding_stability_score": 90.0,
        "overall_score": 80.0,
    }
    defaults.update(kwargs)

    with pytest.raises(WaypointError):
        RouteWaypoint(**defaults)  # type: ignore[arg-type]


def test_route_waypoint_report_validation_accepts_valid_report() -> None:
    report = RouteWaypointReport(
        route_id="route",
        waypoint_spacing_m=500.0,
        launch_terrain_msl_m=100.0,
        flight_agl_m=120.0,
        total_route_distance_m=0.0,
        waypoints=(make_route_waypoint(0),),
    )

    assert report.route_id == "route"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"route_id": ""},
        {"waypoint_spacing_m": 0.0},
        {"launch_terrain_msl_m": float("nan")},
        {"flight_agl_m": -1.0},
        {"total_route_distance_m": -1.0},
        {"waypoints": ()},
        {"waypoints": ("not-waypoint",)},
    ],
)
def test_route_waypoint_report_validation_rejects_invalid_values(
    kwargs: dict[str, object],
) -> None:
    defaults: dict[str, object] = {
        "route_id": "route",
        "waypoint_spacing_m": 500.0,
        "launch_terrain_msl_m": 100.0,
        "flight_agl_m": 120.0,
        "total_route_distance_m": 0.0,
        "waypoints": (make_route_waypoint(0),),
    }
    defaults.update(kwargs)

    with pytest.raises(WaypointError):
        RouteWaypointReport(**defaults)  # type: ignore[arg-type]


def test_route_waypoint_report_rejects_non_sequential_indexes() -> None:
    waypoint = make_route_waypoint(sequence_index=1)

    with pytest.raises(WaypointError, match="sequence_index"):
        RouteWaypointReport(
            route_id="route",
            waypoint_spacing_m=500.0,
            launch_terrain_msl_m=100.0,
            flight_agl_m=120.0,
            total_route_distance_m=0.0,
            waypoints=(waypoint,),
        )


def test_compute_flight_msl_m() -> None:
    assert compute_flight_msl_m(terrain_msl_m=100.0, flight_agl_m=120.0) == 220.0


@pytest.mark.parametrize("flight_agl_m", [-1.0, float("nan")])
def test_compute_flight_msl_m_rejects_invalid_agl(flight_agl_m: float) -> None:
    with pytest.raises(WaypointError):
        compute_flight_msl_m(terrain_msl_m=100.0, flight_agl_m=flight_agl_m)


def test_compute_height_difference_from_launch_m() -> None:
    assert (
        compute_height_difference_from_launch_m(
            flight_msl_m=240.0,
            launch_terrain_msl_m=100.0,
        )
        == 140.0
    )


def test_source_points_must_be_non_decreasing() -> None:
    points = (
        make_source_point("p500", cumulative_distance_m=500.0),
        make_source_point("p250", cumulative_distance_m=250.0),
    )

    with pytest.raises(WaypointError, match="non-decreasing"):
        select_waypoint_source_points(points)


def test_excluded_source_point_raises_waypoint_error() -> None:
    with pytest.raises(WaypointError, match="EXCLUDED"):
        make_source_point(
            "excluded",
            cumulative_distance_m=0.0,
            color_class=ColorClass.EXCLUDED,
        )


def test_500m_spacing_selects_expected_source_points() -> None:
    selected = select_waypoint_source_points(sample_source_points())

    assert [point.point_id for point in selected] == ["p000", "p500", "p1000", "p1500"]


def test_include_start_true_includes_first_point() -> None:
    selected = select_waypoint_source_points(
        sample_source_points(),
        config=WaypointSamplingConfig(include_start=True, include_end=False),
    )

    assert selected[0].point_id == "p000"


def test_include_start_false_excludes_first_point() -> None:
    selected = select_waypoint_source_points(
        sample_source_points(),
        config=WaypointSamplingConfig(include_start=False, include_end=True),
    )

    assert selected[0].point_id == "p500"


def test_include_end_true_includes_last_point() -> None:
    selected = select_waypoint_source_points(
        sample_source_points(),
        config=WaypointSamplingConfig(include_start=False, include_end=True),
    )

    assert selected[-1].point_id == "p1500"


def test_include_end_false_can_exclude_last_point() -> None:
    points = sample_source_points() + (
        make_source_point("p1750", cumulative_distance_m=1750.0),
    )
    selected = select_waypoint_source_points(
        points,
        config=WaypointSamplingConfig(include_start=True, include_end=False),
    )

    assert selected[-1].point_id == "p1500"


def test_duplicate_source_point_removed() -> None:
    points = (
        make_source_point("p000", cumulative_distance_m=0.0),
        make_source_point("p500", cumulative_distance_m=500.0),
    )
    selected = select_waypoint_source_points(
        points,
        config=WaypointSamplingConfig(spacing_m=500.0, include_start=False, include_end=True),
    )

    assert [point.point_id for point in selected] == ["p500"]


def test_build_route_waypoints_generates_sequential_ids() -> None:
    report = build_route_waypoints(
        route_id="route-a",
        source_points=sample_source_points(),
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )

    assert [waypoint.waypoint_id for waypoint in report.waypoints] == [
        "route-a-wp-000",
        "route-a-wp-001",
        "route-a-wp-002",
        "route-a-wp-003",
    ]


def test_build_route_waypoints_computes_msl_and_launch_height_difference() -> None:
    report = build_route_waypoints(
        route_id="route-a",
        source_points=sample_source_points(),
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )

    assert report.waypoints[0].flight_msl_m == 220.0
    assert report.waypoints[0].height_difference_from_launch_m == 120.0
    assert report.waypoints[-1].flight_msl_m == 245.0
    assert report.waypoints[-1].height_difference_from_launch_m == 145.0


def test_segment_distance_from_previous_m() -> None:
    report = build_route_waypoints(
        route_id="route-a",
        source_points=sample_source_points(),
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )

    assert [waypoint.segment_distance_from_previous_m for waypoint in report.waypoints] == [
        0.0,
        500.0,
        500.0,
        500.0,
    ]


def test_route_waypoint_report_total_distance_m() -> None:
    report = build_route_waypoints(
        route_id="route-a",
        source_points=sample_source_points(),
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )

    assert report.total_route_distance_m == 1500.0


def test_summarize_waypoint_report() -> None:
    report = build_route_waypoints(
        route_id="route-a",
        source_points=sample_source_points(),
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )

    summary = summarize_waypoint_report(report)

    assert summary["route_id"] == "route-a"
    assert summary["waypoint_count"] == 4
    assert summary["waypoint_spacing_m"] == 500.0
    assert summary["total_route_distance_m"] == 1500.0
    assert summary["flight_agl_m"] == 120.0
    assert summary["min_flight_msl_m"] == 220.0
    assert summary["max_flight_msl_m"] == 245.0
    assert summary["min_height_difference_from_launch_m"] == 120.0
    assert summary["max_height_difference_from_launch_m"] == 145.0
    assert summary["orange_waypoint_count"] == 1
    assert summary["red_waypoint_count"] == 1


def test_summarize_waypoint_report_rejects_wrong_type() -> None:
    with pytest.raises(WaypointError, match="report"):
        summarize_waypoint_report("not-a-report")  # type: ignore[arg-type]


def test_waypoints_module_has_no_map_rendering_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/waypoints.py").read_text(encoding="utf-8").lower()

    prohibited_imports = ("rasterio", "gdal", "geopandas", "folium", "streamlit", "osgeo")
    for prohibited_import in prohibited_imports:
        assert prohibited_import not in module_text


def test_route_waypoint_has_no_required_link_metric_fields() -> None:
    field_names = {field.name for field in fields(RouteWaypoint)}

    assert "rssi" not in field_names
    assert "sinr" not in field_names
    assert "packet_loss" not in field_names


def test_route_waypoint_has_no_command_or_control_fields() -> None:
    field_names = {field.name for field in fields(RouteWaypoint)}

    prohibited_fields = {
        "flight_command",
        "flight_commands",
        "autopilot",
        "control_api",
        "control_mode",
        "execution_plan",
    }
    assert field_names.isdisjoint(prohibited_fields)


def test_built_waypoint_preserves_color_and_scores() -> None:
    report = build_route_waypoints(
        route_id="route-a",
        source_points=sample_source_points(),
        flight_agl_m=120.0,
        launch_terrain_msl_m=100.0,
    )

    orange_waypoint = report.waypoints[2]
    assert orange_waypoint.color_class is ColorClass.ORANGE
    assert orange_waypoint.shielding_stability_score == 90.0
    assert orange_waypoint.overall_score == 85.0
    assert isclose(orange_waypoint.cumulative_distance_m, 1000.0)
