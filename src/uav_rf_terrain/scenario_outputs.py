"""Offline synthetic end-to-end scenario output scaffold.

This module connects candidate scoring, color classification, route candidate
evaluation, and waypoint reporting using synthetic data only. It produces a
reproducible analysis-pipeline output for examples, tests, and paper-supporting
records. It does not load real DEM/DSM files, render maps, generate vehicle
commands, or validate real link quality.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .classification import evaluate_launch_area_cell
from .routing import (
    RouteCandidate,
    RouteCandidateType,
    RouteCell,
    build_route_candidate,
    select_lowest_cost_route,
)
from .schemas import ColorClass
from .scoring import CandidateScore, compute_candidate_score
from .waypoints import (
    RouteWaypointReport,
    WaypointSamplingConfig,
    WaypointSourcePoint,
    build_route_waypoints,
    summarize_waypoint_report,
)

CandidateSpec = tuple[str, float, float, float, float, bool]
RouteSpec = tuple[str, RouteCandidateType, tuple[RouteCell, ...], tuple[WaypointSourcePoint, ...]]


class ScenarioOutputError(ValueError):
    """Raised when synthetic scenario output inputs or records are invalid."""


@dataclass(frozen=True)
class SyntheticCandidateRecord:
    """Synthetic candidate score and color classification bundle."""

    candidate_id: str
    candidate_score: CandidateScore
    color_class: ColorClass
    within_operation_radius: bool
    reason: str

    def __post_init__(self) -> None:
        _validate_non_empty_string("candidate_id", self.candidate_id)
        if not isinstance(self.candidate_score, CandidateScore):
            raise ScenarioOutputError("candidate_score must be a CandidateScore instance.")
        if not isinstance(self.color_class, ColorClass):
            raise ScenarioOutputError("color_class must be a ColorClass value.")
        if not isinstance(self.within_operation_radius, bool):
            raise ScenarioOutputError("within_operation_radius must be a bool.")
        _validate_non_empty_string("reason", self.reason)


@dataclass(frozen=True)
class SyntheticRouteOutput:
    """Synthetic route candidate and matching waypoint report bundle."""

    route_candidate: RouteCandidate
    waypoint_report: RouteWaypointReport

    def __post_init__(self) -> None:
        if not isinstance(self.route_candidate, RouteCandidate):
            raise ScenarioOutputError("route_candidate must be a RouteCandidate instance.")
        if not isinstance(self.waypoint_report, RouteWaypointReport):
            raise ScenarioOutputError("waypoint_report must be a RouteWaypointReport instance.")
        if self.route_candidate.route_id != self.waypoint_report.route_id:
            raise ScenarioOutputError("route_candidate.route_id must match waypoint_report.route_id.")


@dataclass(frozen=True)
class SyntheticEndToEndScenario:
    """Complete offline synthetic candidate-to-waypoint scenario output."""

    scenario_name: str
    candidates: tuple[SyntheticCandidateRecord, ...]
    routes: tuple[SyntheticRouteOutput, ...]
    selected_route_id: str
    summary: dict[str, float | int | str]

    def __post_init__(self) -> None:
        _validate_non_empty_string("scenario_name", self.scenario_name)
        _ensure_candidate_records(self.candidates)
        _ensure_route_outputs(self.routes)
        _validate_non_empty_string("selected_route_id", self.selected_route_id)
        route_ids = {route.route_candidate.route_id for route in self.routes}
        if self.selected_route_id not in route_ids:
            raise ScenarioOutputError("selected_route_id must match one of the route outputs.")
        if not isinstance(self.summary, dict):
            raise ScenarioOutputError("summary must be a dict.")


def build_synthetic_candidate_records() -> tuple[SyntheticCandidateRecord, ...]:
    """Build synthetic candidate score and color classification records."""

    candidate_specs: tuple[CandidateSpec, ...] = (
        ("candidate-green", 1_000.0, 5_000.0, 100.0, 95.0, True),
        ("candidate-yellow", 3_000.0, 5_000.0, 100.0, 60.0, True),
        ("candidate-orange", 3_500.0, 5_000.0, 100.0, 35.0, True),
        ("candidate-red-los-blocked", 1_000.0, 5_000.0, 0.0, 100.0, True),
        ("candidate-excluded-out-of-radius", 6_000.0, 5_000.0, 100.0, 90.0, False),
    )

    records: list[SyntheticCandidateRecord] = []
    for (
        candidate_id,
        distance_3d_m,
        operating_radius_m,
        dsm_los_score,
        dsm_fresnel_score,
        within_operation_radius,
    ) in candidate_specs:
        candidate_score = compute_candidate_score(
            distance_3d_m=distance_3d_m,
            operating_radius_m=operating_radius_m,
            dsm_los_score=dsm_los_score,
            dsm_fresnel_score=dsm_fresnel_score,
        )
        evaluation = evaluate_launch_area_cell(
            cell_id=candidate_id,
            candidate_score=candidate_score,
            within_operation_radius=within_operation_radius,
        )
        records.append(
            SyntheticCandidateRecord(
                candidate_id=candidate_id,
                candidate_score=candidate_score,
                color_class=evaluation.color_class,
                within_operation_radius=evaluation.within_operation_radius,
                reason=evaluation.reason,
            )
        )
    return tuple(records)


def build_synthetic_route_outputs() -> tuple[SyntheticRouteOutput, ...]:
    """Build three synthetic route outputs with matching waypoint reports."""

    route_specs: tuple[RouteSpec, ...] = (
        (
            "route-shielding-minimum",
            RouteCandidateType.SHIELDING_MINIMUM,
            (
                RouteCell("sm-000", 0.0, ColorClass.GREEN, 95.0, 92.0),
                RouteCell("sm-001", 500.0, ColorClass.GREEN, 92.0, 88.0),
                RouteCell("sm-002", 500.0, ColorClass.GREEN, 90.0, 86.0),
                RouteCell("sm-003", 500.0, ColorClass.YELLOW, 82.0, 74.0),
                RouteCell("sm-004", 500.0, ColorClass.GREEN, 91.0, 84.0),
            ),
            (
                _source_point("sm-p000", 0.0, ColorClass.GREEN, 100.0, 95.0, 92.0),
                _source_point("sm-p500", 500.0, ColorClass.GREEN, 103.0, 92.0, 88.0),
                _source_point("sm-p1000", 1000.0, ColorClass.GREEN, 106.0, 90.0, 86.0),
                _source_point("sm-p1500", 1500.0, ColorClass.YELLOW, 109.0, 82.0, 74.0),
                _source_point("sm-p2000", 2000.0, ColorClass.GREEN, 112.0, 91.0, 84.0),
            ),
        ),
        (
            "route-distance-shielding-balanced",
            RouteCandidateType.DISTANCE_SHIELDING_BALANCED,
            (
                RouteCell("ds-000", 0.0, ColorClass.GREEN, 86.0, 82.0),
                RouteCell("ds-001", 400.0, ColorClass.YELLOW, 75.0, 70.0),
                RouteCell("ds-002", 400.0, ColorClass.ORANGE, 58.0, 55.0),
                RouteCell("ds-003", 400.0, ColorClass.YELLOW, 78.0, 68.0),
                RouteCell("ds-004", 400.0, ColorClass.GREEN, 84.0, 76.0),
            ),
            (
                _source_point("ds-p000", 0.0, ColorClass.GREEN, 100.0, 86.0, 82.0),
                _source_point("ds-p400", 400.0, ColorClass.YELLOW, 102.0, 75.0, 70.0),
                _source_point("ds-p800", 800.0, ColorClass.ORANGE, 104.0, 58.0, 55.0),
                _source_point("ds-p1200", 1200.0, ColorClass.YELLOW, 106.0, 78.0, 68.0),
                _source_point("ds-p1600", 1600.0, ColorClass.GREEN, 108.0, 84.0, 76.0),
            ),
        ),
        (
            "route-detour-stability",
            RouteCandidateType.DETOUR_STABILITY,
            (
                RouteCell("dt-000", 0.0, ColorClass.GREEN, 90.0, 84.0),
                RouteCell("dt-001", 650.0, ColorClass.GREEN, 87.0, 80.0),
                RouteCell("dt-002", 650.0, ColorClass.YELLOW, 80.0, 72.0),
                RouteCell("dt-003", 650.0, ColorClass.GREEN, 88.0, 79.0),
                RouteCell("dt-004", 650.0, ColorClass.YELLOW, 82.0, 73.0),
            ),
            (
                _source_point("dt-p000", 0.0, ColorClass.GREEN, 100.0, 90.0, 84.0),
                _source_point("dt-p650", 650.0, ColorClass.GREEN, 106.0, 87.0, 80.0),
                _source_point("dt-p1300", 1300.0, ColorClass.YELLOW, 112.0, 80.0, 72.0),
                _source_point("dt-p1950", 1950.0, ColorClass.GREEN, 118.0, 88.0, 79.0),
                _source_point("dt-p2600", 2600.0, ColorClass.YELLOW, 124.0, 82.0, 73.0),
            ),
        ),
    )

    route_outputs: list[SyntheticRouteOutput] = []
    for route_id, route_type, route_cells, source_points in route_specs:
        route_candidate = build_route_candidate(
            route_id=route_id,
            route_type=route_type,
            cells=route_cells,
            distance_normalizer_m=4_000.0,
        )
        waypoint_report = build_route_waypoints(
            route_id=route_id,
            source_points=source_points,
            flight_agl_m=120.0,
            launch_terrain_msl_m=source_points[0].terrain_msl_m,
            config=WaypointSamplingConfig(spacing_m=500.0, include_start=True, include_end=True),
        )
        route_outputs.append(
            SyntheticRouteOutput(
                route_candidate=route_candidate,
                waypoint_report=waypoint_report,
            )
        )
    return tuple(route_outputs)


def build_synthetic_end_to_end_scenario(
    *,
    scenario_name: str = "synthetic-e2e-default",
) -> SyntheticEndToEndScenario:
    """Build one complete offline synthetic candidate-to-waypoint scenario."""

    _validate_non_empty_string("scenario_name", scenario_name)
    candidates = build_synthetic_candidate_records()
    routes = build_synthetic_route_outputs()
    selected_route = select_lowest_cost_route(tuple(route.route_candidate for route in routes))
    provisional = SyntheticEndToEndScenario(
        scenario_name=scenario_name,
        candidates=candidates,
        routes=routes,
        selected_route_id=selected_route.route_id,
        summary={},
    )
    return SyntheticEndToEndScenario(
        scenario_name=scenario_name,
        candidates=candidates,
        routes=routes,
        selected_route_id=selected_route.route_id,
        summary=summarize_synthetic_end_to_end_scenario(provisional),
    )


def summarize_synthetic_end_to_end_scenario(
    scenario: SyntheticEndToEndScenario,
) -> dict[str, float | int | str]:
    """Return candidate color counts and selected route metrics for a scenario."""

    if not isinstance(scenario, SyntheticEndToEndScenario):
        raise ScenarioOutputError("scenario must be a SyntheticEndToEndScenario instance.")
    selected_route_output = _selected_route_output(scenario.routes, scenario.selected_route_id)
    selected_summary = summarize_waypoint_report(selected_route_output.waypoint_report)
    return {
        "scenario_name": scenario.scenario_name,
        "candidate_count": len(scenario.candidates),
        "green_candidate_count": _count_candidates(scenario.candidates, ColorClass.GREEN),
        "yellow_candidate_count": _count_candidates(scenario.candidates, ColorClass.YELLOW),
        "orange_candidate_count": _count_candidates(scenario.candidates, ColorClass.ORANGE),
        "red_candidate_count": _count_candidates(scenario.candidates, ColorClass.RED),
        "excluded_candidate_count": _count_candidates(scenario.candidates, ColorClass.EXCLUDED),
        "route_count": len(scenario.routes),
        "selected_route_id": selected_route_output.route_candidate.route_id,
        "selected_route_cost": selected_route_output.route_candidate.route_cost,
        "selected_route_total_distance_m": selected_route_output.route_candidate.total_distance_m,
        "selected_route_waypoint_count": int(selected_summary["waypoint_count"]),
        "selected_route_red_waypoint_count": int(selected_summary["red_waypoint_count"]),
        "selected_route_orange_waypoint_count": int(selected_summary["orange_waypoint_count"]),
    }


def format_synthetic_end_to_end_summary(
    scenario: SyntheticEndToEndScenario,
) -> str:
    """Return a readable console summary for an offline synthetic scenario."""

    if not isinstance(scenario, SyntheticEndToEndScenario):
        raise ScenarioOutputError("scenario must be a SyntheticEndToEndScenario instance.")
    summary = scenario.summary or summarize_synthetic_end_to_end_scenario(scenario)
    return "\n".join(
        (
            "Synthetic/offline end-to-end scenario summary",
            f"Scenario: {summary['scenario_name']}",
            "Candidate color counts: "
            f"green={summary['green_candidate_count']}, "
            f"yellow={summary['yellow_candidate_count']}, "
            f"orange={summary['orange_candidate_count']}, "
            f"red={summary['red_candidate_count']}, "
            f"excluded={summary['excluded_candidate_count']}",
            f"Route count: {summary['route_count']}",
            f"Selected route id: {summary['selected_route_id']}",
            f"Selected route cost: {summary['selected_route_cost']:.3f}",
            f"Selected route distance m: {summary['selected_route_total_distance_m']:.3f}",
            f"Selected route waypoint count: {summary['selected_route_waypoint_count']}",
            "This is a reproducible synthetic analysis example, not a real map or field validation.",
        )
    )


def _source_point(
    point_id: str,
    cumulative_distance_m: float,
    color_class: ColorClass,
    terrain_msl_m: float,
    shielding_stability_score: float,
    overall_score: float,
) -> WaypointSourcePoint:
    return WaypointSourcePoint(
        point_id=point_id,
        x_m=cumulative_distance_m,
        y_m=0.0,
        terrain_msl_m=terrain_msl_m,
        surface_msl_m=terrain_msl_m + 5.0,
        cumulative_distance_m=cumulative_distance_m,
        color_class=color_class,
        shielding_stability_score=shielding_stability_score,
        overall_score=overall_score,
    )


def _count_candidates(
    candidates: Sequence[SyntheticCandidateRecord],
    color_class: ColorClass,
) -> int:
    return sum(1 for candidate in candidates if candidate.color_class is color_class)


def _selected_route_output(
    routes: Sequence[SyntheticRouteOutput],
    selected_route_id: str,
) -> SyntheticRouteOutput:
    for route in routes:
        if route.route_candidate.route_id == selected_route_id:
            return route
    raise ScenarioOutputError("selected_route_id must match one of the route outputs.")


def _ensure_candidate_records(candidates: tuple[SyntheticCandidateRecord, ...]) -> None:
    if not candidates:
        raise ScenarioOutputError("candidates must not be empty.")
    for candidate in candidates:
        if not isinstance(candidate, SyntheticCandidateRecord):
            raise ScenarioOutputError("all candidates must be SyntheticCandidateRecord instances.")


def _ensure_route_outputs(routes: tuple[SyntheticRouteOutput, ...]) -> None:
    if not routes:
        raise ScenarioOutputError("routes must not be empty.")
    for route in routes:
        if not isinstance(route, SyntheticRouteOutput):
            raise ScenarioOutputError("all routes must be SyntheticRouteOutput instances.")


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ScenarioOutputError(f"{field_name} must be a non-empty string.")
