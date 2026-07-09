from dataclasses import fields
from math import isclose
from pathlib import Path

import pytest

from uav_rf_terrain.routing import (
    RouteCandidate,
    RouteCandidateType,
    RouteCell,
    RouteCostWeights,
    RoutingError,
    build_route_candidate,
    compute_route_cost,
    compute_route_mean_shielding_score,
    compute_route_minimum_shielding_score,
    compute_route_total_distance_m,
    count_high_risk_cells,
    default_route_cost_weights,
    select_lowest_cost_route,
)
from uav_rf_terrain.schemas import ColorClass


def make_cell(
    cell_id: str,
    *,
    distance_from_previous_m: float = 100.0,
    color_class: ColorClass = ColorClass.GREEN,
    shielding_stability_score: float = 90.0,
    overall_score: float = 85.0,
) -> RouteCell:
    return RouteCell(
        cell_id=cell_id,
        distance_from_previous_m=distance_from_previous_m,
        color_class=color_class,
        shielding_stability_score=shielding_stability_score,
        overall_score=overall_score,
    )


def sample_cells() -> tuple[RouteCell, ...]:
    return (
        make_cell("cell-001", distance_from_previous_m=0.0, shielding_stability_score=90.0),
        make_cell("cell-002", distance_from_previous_m=100.0, shielding_stability_score=80.0),
        make_cell("cell-003", distance_from_previous_m=200.0, shielding_stability_score=70.0),
    )


def test_route_candidate_type_has_default_three_types() -> None:
    assert RouteCandidateType.SHIELDING_MINIMUM.value == "shielding_minimum"
    assert RouteCandidateType.DISTANCE_SHIELDING_BALANCED.value == "distance_shielding_balanced"
    assert RouteCandidateType.DETOUR_STABILITY.value == "detour_stability"


def test_default_route_cost_weights_values() -> None:
    shielding = default_route_cost_weights(RouteCandidateType.SHIELDING_MINIMUM)
    balanced = default_route_cost_weights(RouteCandidateType.DISTANCE_SHIELDING_BALANCED)
    detour = default_route_cost_weights(RouteCandidateType.DETOUR_STABILITY)

    assert shielding == RouteCostWeights(0.90, 0.10, 1.0)
    assert balanced == RouteCostWeights(0.70, 0.30, 1.0)
    assert detour == RouteCostWeights(0.85, 0.15, 2.0)


@pytest.mark.parametrize(
    "weights",
    [
        RouteCostWeights(0.0, 1.0),
        RouteCostWeights(1.0, 0.0),
        RouteCostWeights(0.5, 0.5, 2.0),
    ],
)
def test_route_cost_weights_validation_accepts_valid_values(weights: RouteCostWeights) -> None:
    weights.validate()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"shielding_weight": float("nan"), "distance_weight": 1.0},
        {"shielding_weight": 1.0, "distance_weight": float("inf")},
        {"shielding_weight": -0.1, "distance_weight": 1.0},
        {"shielding_weight": 0.0, "distance_weight": 0.0},
        {"shielding_weight": 1.0, "distance_weight": 0.0, "high_risk_penalty_weight": -1.0},
    ],
)
def test_route_cost_weights_validation_rejects_invalid_values(kwargs: dict[str, float]) -> None:
    with pytest.raises(RoutingError):
        RouteCostWeights(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cell_id": "", "distance_from_previous_m": 0.0},
        {"cell_id": "cell", "distance_from_previous_m": float("nan")},
        {"cell_id": "cell", "distance_from_previous_m": -1.0},
        {"cell_id": "cell", "distance_from_previous_m": 0.0, "color_class": "green"},
        {"cell_id": "cell", "distance_from_previous_m": 0.0, "shielding_stability_score": -1.0},
        {"cell_id": "cell", "distance_from_previous_m": 0.0, "overall_score": 101.0},
    ],
)
def test_route_cell_validation_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    defaults: dict[str, object] = {
        "cell_id": "cell",
        "distance_from_previous_m": 0.0,
        "color_class": ColorClass.GREEN,
        "shielding_stability_score": 90.0,
        "overall_score": 80.0,
    }
    defaults.update(kwargs)

    with pytest.raises(RoutingError):
        RouteCell(**defaults)  # type: ignore[arg-type]


def test_route_candidate_validation_accepts_valid_candidate() -> None:
    candidate = build_route_candidate(
        route_id="route-1",
        route_type=RouteCandidateType.SHIELDING_MINIMUM,
        cells=sample_cells(),
        distance_normalizer_m=1000.0,
    )

    assert isinstance(candidate, RouteCandidate)
    assert candidate.route_id == "route-1"
    assert candidate.route_type is RouteCandidateType.SHIELDING_MINIMUM
    assert candidate.cells == sample_cells()
    assert candidate.total_distance_m == 300.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"route_id": ""},
        {"route_type": "shielding_minimum"},
        {"cells": ()},
        {"total_distance_m": -1.0},
        {"mean_shielding_stability_score": 101.0},
        {"minimum_shielding_stability_score": -0.1},
        {"high_risk_cell_count": -1},
        {"high_risk_cell_count": 1.5},
        {"route_cost": float("nan")},
        {"reason": ""},
    ],
)
def test_route_candidate_validation_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    defaults: dict[str, object] = {
        "route_id": "route-1",
        "route_type": RouteCandidateType.SHIELDING_MINIMUM,
        "cells": sample_cells(),
        "total_distance_m": 300.0,
        "mean_shielding_stability_score": 80.0,
        "minimum_shielding_stability_score": 70.0,
        "high_risk_cell_count": 0,
        "route_cost": 20.0,
        "reason": "test route",
    }
    defaults.update(kwargs)

    with pytest.raises(RoutingError):
        RouteCandidate(**defaults)  # type: ignore[arg-type]


def test_compute_route_total_distance_m() -> None:
    assert compute_route_total_distance_m(sample_cells()) == 300.0


def test_compute_route_mean_shielding_score() -> None:
    assert compute_route_mean_shielding_score(sample_cells()) == 80.0


def test_compute_route_minimum_shielding_score() -> None:
    assert compute_route_minimum_shielding_score(sample_cells()) == 70.0


def test_red_high_risk_count() -> None:
    cells = (
        make_cell("cell-001", color_class=ColorClass.GREEN),
        make_cell("cell-002", color_class=ColorClass.RED),
        make_cell("cell-003", color_class=ColorClass.YELLOW),
    )

    assert count_high_risk_cells(cells) == 1


def test_orange_high_risk_count_when_include_orange_true() -> None:
    cells = (
        make_cell("cell-001", color_class=ColorClass.GREEN),
        make_cell("cell-002", color_class=ColorClass.ORANGE),
        make_cell("cell-003", color_class=ColorClass.RED),
    )

    assert count_high_risk_cells(cells, include_orange=True) == 2


def test_orange_not_high_risk_when_include_orange_false() -> None:
    cells = (
        make_cell("cell-001", color_class=ColorClass.GREEN),
        make_cell("cell-002", color_class=ColorClass.ORANGE),
        make_cell("cell-003", color_class=ColorClass.RED),
    )

    assert count_high_risk_cells(cells, include_orange=False) == 1


def test_excluded_cell_in_route_raises_routing_error() -> None:
    cells = (make_cell("cell-001", color_class=ColorClass.EXCLUDED),)

    with pytest.raises(RoutingError, match="EXCLUDED"):
        count_high_risk_cells(cells)

    with pytest.raises(RoutingError, match="EXCLUDED"):
        build_route_candidate(
            route_id="route-excluded",
            route_type=RouteCandidateType.SHIELDING_MINIMUM,
            cells=cells,
            distance_normalizer_m=1000.0,
        )


def test_route_cost_calculation() -> None:
    cost = compute_route_cost(
        total_distance_m=500.0,
        mean_shielding_stability_score=80.0,
        high_risk_cell_count=1,
        weights=RouteCostWeights(
            shielding_weight=0.7,
            distance_weight=0.3,
            high_risk_penalty_weight=1.0,
        ),
        distance_normalizer_m=1000.0,
    )

    assert cost == 129.0


@pytest.mark.parametrize("distance_normalizer_m", [0.0, -1.0, float("nan")])
def test_distance_normalizer_error(distance_normalizer_m: float) -> None:
    with pytest.raises(RoutingError, match="distance_normalizer_m"):
        compute_route_cost(
            total_distance_m=500.0,
            mean_shielding_stability_score=80.0,
            high_risk_cell_count=0,
            weights=RouteCostWeights(0.7, 0.3),
            distance_normalizer_m=distance_normalizer_m,
        )


def test_negative_distance_error() -> None:
    with pytest.raises(RoutingError, match="total_distance_m"):
        compute_route_cost(
            total_distance_m=-1.0,
            mean_shielding_stability_score=80.0,
            high_risk_cell_count=0,
            weights=RouteCostWeights(0.7, 0.3),
            distance_normalizer_m=1000.0,
        )


def test_out_of_range_score_error() -> None:
    with pytest.raises(RoutingError, match="mean_shielding_stability_score"):
        compute_route_cost(
            total_distance_m=1.0,
            mean_shielding_stability_score=101.0,
            high_risk_cell_count=0,
            weights=RouteCostWeights(0.7, 0.3),
            distance_normalizer_m=1000.0,
        )


def test_build_route_candidate_uses_default_weights() -> None:
    cells = sample_cells()
    candidate = build_route_candidate(
        route_id="route-default",
        route_type=RouteCandidateType.SHIELDING_MINIMUM,
        cells=cells,
        distance_normalizer_m=1000.0,
    )

    assert candidate.total_distance_m == 300.0
    assert candidate.mean_shielding_stability_score == 80.0
    assert candidate.minimum_shielding_stability_score == 70.0
    assert candidate.high_risk_cell_count == 0
    assert isclose(candidate.route_cost, 21.0)
    assert "shielding_minimum" in candidate.reason


def test_build_route_candidate_uses_custom_weights() -> None:
    cells = sample_cells()
    candidate = build_route_candidate(
        route_id="route-custom",
        route_type=RouteCandidateType.DISTANCE_SHIELDING_BALANCED,
        cells=cells,
        distance_normalizer_m=1000.0,
        weights=RouteCostWeights(
            shielding_weight=1.0,
            distance_weight=0.0,
            high_risk_penalty_weight=0.0,
        ),
    )

    assert candidate.route_cost == 20.0


def test_select_lowest_cost_route() -> None:
    high_cost = RouteCandidate(
        route_id="route-high",
        route_type=RouteCandidateType.SHIELDING_MINIMUM,
        cells=sample_cells(),
        total_distance_m=300.0,
        mean_shielding_stability_score=80.0,
        minimum_shielding_stability_score=70.0,
        high_risk_cell_count=0,
        route_cost=30.0,
        reason="high",
    )
    low_cost = RouteCandidate(
        route_id="route-low",
        route_type=RouteCandidateType.DISTANCE_SHIELDING_BALANCED,
        cells=sample_cells(),
        total_distance_m=300.0,
        mean_shielding_stability_score=85.0,
        minimum_shielding_stability_score=75.0,
        high_risk_cell_count=0,
        route_cost=10.0,
        reason="low",
    )

    assert select_lowest_cost_route((high_cost, low_cost)) is low_cost


def test_select_lowest_cost_route_keeps_input_order_on_tie() -> None:
    first = build_route_candidate(
        route_id="route-first",
        route_type=RouteCandidateType.SHIELDING_MINIMUM,
        cells=sample_cells(),
        distance_normalizer_m=1000.0,
    )
    second = RouteCandidate(
        route_id="route-second",
        route_type=RouteCandidateType.DETOUR_STABILITY,
        cells=sample_cells(),
        total_distance_m=first.total_distance_m,
        mean_shielding_stability_score=first.mean_shielding_stability_score,
        minimum_shielding_stability_score=first.minimum_shielding_stability_score,
        high_risk_cell_count=first.high_risk_cell_count,
        route_cost=first.route_cost,
        reason="same cost",
    )

    assert select_lowest_cost_route((first, second)) is first


def test_select_lowest_cost_route_rejects_empty_input() -> None:
    with pytest.raises(RoutingError, match="candidates"):
        select_lowest_cost_route(())


def test_routing_module_has_no_map_rendering_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/routing.py").read_text(encoding="utf-8").lower()

    prohibited_imports = ("rasterio", "gdal", "geopandas", "folium", "streamlit", "osgeo")
    for prohibited_import in prohibited_imports:
        assert prohibited_import not in module_text


def test_route_candidate_has_no_required_link_metric_fields() -> None:
    field_names = {field.name for field in fields(RouteCandidate)}

    assert "rssi" not in field_names
    assert "sinr" not in field_names
    assert "packet_loss" not in field_names


def test_route_candidate_has_no_actual_flight_command_fields() -> None:
    field_names = {field.name for field in fields(RouteCandidate)}

    prohibited_fields = {
        "flight_command",
        "flight_commands",
        "autopilot",
        "control_api",
        "control_mode",
        "execution_plan",
    }
    assert field_names.isdisjoint(prohibited_fields)
