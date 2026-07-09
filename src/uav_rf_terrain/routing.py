"""Pure Python route candidate evaluation scaffold for offline analysis.

Routes in this module are analysis data structures for later display and waypoint
workflows. They are not flight instructions, autonomous execution plans, or verified
communication-quality outputs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from .schemas import ColorClass


class RoutingError(ValueError):
    """Raised when route candidate inputs or cost parameters are invalid."""


class RouteCandidateType(StrEnum):
    """Supported offline route candidate types."""

    SHIELDING_MINIMUM = "shielding_minimum"
    DISTANCE_SHIELDING_BALANCED = "distance_shielding_balanced"
    DETOUR_STABILITY = "detour_stability"


@dataclass(frozen=True)
class RouteCostWeights:
    """Weights for offline route candidate cost calculation."""

    shielding_weight: float
    distance_weight: float
    high_risk_penalty_weight: float = 0.0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate finite, non-negative route cost weights."""

        for field_name, value in (
            ("shielding_weight", self.shielding_weight),
            ("distance_weight", self.distance_weight),
            ("high_risk_penalty_weight", self.high_risk_penalty_weight),
        ):
            if not isfinite(value):
                raise RoutingError(f"{field_name} must be finite.")
            if value < 0.0:
                raise RoutingError(f"{field_name} must be non-negative.")

        if self.shielding_weight + self.distance_weight <= 0.0:
            raise RoutingError("shielding_weight + distance_weight must be greater than 0.")


@dataclass(frozen=True)
class RouteCell:
    """One ordered cell in an offline route candidate."""

    cell_id: str
    distance_from_previous_m: float
    color_class: ColorClass
    shielding_stability_score: float
    overall_score: float

    def __post_init__(self) -> None:
        _validate_non_empty_string("cell_id", self.cell_id)
        _validate_non_negative_finite("distance_from_previous_m", self.distance_from_previous_m)
        if not isinstance(self.color_class, ColorClass):
            raise RoutingError("color_class must be a ColorClass value.")
        _validate_score("shielding_stability_score", self.shielding_stability_score)
        _validate_score("overall_score", self.overall_score)


@dataclass(frozen=True)
class RouteCandidate:
    """Offline route candidate evaluation result."""

    route_id: str
    route_type: RouteCandidateType
    cells: tuple[RouteCell, ...]
    total_distance_m: float
    mean_shielding_stability_score: float
    minimum_shielding_stability_score: float
    high_risk_cell_count: int
    route_cost: float
    reason: str

    def __post_init__(self) -> None:
        _validate_non_empty_string("route_id", self.route_id)
        if not isinstance(self.route_type, RouteCandidateType):
            raise RoutingError("route_type must be a RouteCandidateType value.")
        _ensure_route_cells(self.cells)
        _validate_non_negative_finite("total_distance_m", self.total_distance_m)
        _validate_score("mean_shielding_stability_score", self.mean_shielding_stability_score)
        _validate_score(
            "minimum_shielding_stability_score",
            self.minimum_shielding_stability_score,
        )
        _validate_non_negative_int("high_risk_cell_count", self.high_risk_cell_count)
        _validate_non_negative_finite("route_cost", self.route_cost)
        _validate_non_empty_string("reason", self.reason)


def default_route_cost_weights(route_type: RouteCandidateType) -> RouteCostWeights:
    """Return default route cost weights for a route candidate type."""

    if not isinstance(route_type, RouteCandidateType):
        raise RoutingError("route_type must be a RouteCandidateType value.")

    if route_type is RouteCandidateType.SHIELDING_MINIMUM:
        return RouteCostWeights(
            shielding_weight=0.90,
            distance_weight=0.10,
            high_risk_penalty_weight=1.0,
        )
    if route_type is RouteCandidateType.DISTANCE_SHIELDING_BALANCED:
        return RouteCostWeights(
            shielding_weight=0.70,
            distance_weight=0.30,
            high_risk_penalty_weight=1.0,
        )
    return RouteCostWeights(
        shielding_weight=0.85,
        distance_weight=0.15,
        high_risk_penalty_weight=2.0,
    )


def compute_route_total_distance_m(cells: Sequence[RouteCell]) -> float:
    """Return route total distance as sum of cell-to-cell segment distances."""

    resolved_cells = _ensure_route_cells(cells)
    return sum(cell.distance_from_previous_m for cell in resolved_cells)


def compute_route_mean_shielding_score(cells: Sequence[RouteCell]) -> float:
    """Return the arithmetic mean shielding stability score for route cells."""

    resolved_cells = _ensure_route_cells(cells)
    return sum(cell.shielding_stability_score for cell in resolved_cells) / len(resolved_cells)


def compute_route_minimum_shielding_score(cells: Sequence[RouteCell]) -> float:
    """Return the minimum shielding stability score for route cells."""

    resolved_cells = _ensure_route_cells(cells)
    return min(cell.shielding_stability_score for cell in resolved_cells)


def count_high_risk_cells(
    cells: Sequence[RouteCell],
    *,
    include_orange: bool = True,
) -> int:
    """Count DSM-shielding high-risk route cells.

    ``RED`` is always counted. ``ORANGE`` is counted when ``include_orange`` is true.
    ``EXCLUDED`` cannot be part of a valid route candidate.
    """

    if not isinstance(include_orange, bool):
        raise RoutingError("include_orange must be a bool.")

    resolved_cells = _ensure_route_cells(cells)
    high_risk_count = 0
    for cell in resolved_cells:
        if cell.color_class is ColorClass.EXCLUDED:
            raise RoutingError("EXCLUDED cells cannot be included in a route candidate.")
        if cell.color_class is ColorClass.RED:
            high_risk_count += 1
        elif include_orange and cell.color_class is ColorClass.ORANGE:
            high_risk_count += 1
    return high_risk_count


def compute_route_cost(
    *,
    total_distance_m: float,
    mean_shielding_stability_score: float,
    high_risk_cell_count: int,
    weights: RouteCostWeights,
    distance_normalizer_m: float,
) -> float:
    """Compute weighted route cost from distance, shielding risk, and high-risk count."""

    _validate_non_negative_finite("total_distance_m", total_distance_m)
    _validate_score("mean_shielding_stability_score", mean_shielding_stability_score)
    _validate_non_negative_int("high_risk_cell_count", high_risk_cell_count)
    if not isinstance(weights, RouteCostWeights):
        raise RoutingError("weights must be a RouteCostWeights instance.")
    weights.validate()
    if not isfinite(distance_normalizer_m) or distance_normalizer_m <= 0.0:
        raise RoutingError("distance_normalizer_m must be finite and positive.")

    distance_cost = _clamp(total_distance_m / distance_normalizer_m, lower=0.0, upper=1.0) * 100.0
    shielding_risk_cost = 100.0 - mean_shielding_stability_score
    high_risk_cost = high_risk_cell_count * 100.0
    return (
        weights.shielding_weight * shielding_risk_cost
        + weights.distance_weight * distance_cost
        + weights.high_risk_penalty_weight * high_risk_cost
    )


def build_route_candidate(
    *,
    route_id: str,
    route_type: RouteCandidateType,
    cells: Sequence[RouteCell],
    distance_normalizer_m: float,
    weights: RouteCostWeights | None = None,
) -> RouteCandidate:
    """Build an offline route candidate evaluation result."""

    _validate_non_empty_string("route_id", route_id)
    if not isinstance(route_type, RouteCandidateType):
        raise RoutingError("route_type must be a RouteCandidateType value.")
    resolved_cells = _ensure_route_cells(cells)
    resolved_weights = default_route_cost_weights(route_type) if weights is None else weights
    if not isinstance(resolved_weights, RouteCostWeights):
        raise RoutingError("weights must be a RouteCostWeights instance.")

    total_distance_m = compute_route_total_distance_m(resolved_cells)
    mean_shielding_stability_score = compute_route_mean_shielding_score(resolved_cells)
    minimum_shielding_stability_score = compute_route_minimum_shielding_score(resolved_cells)
    high_risk_cell_count = count_high_risk_cells(resolved_cells, include_orange=True)
    route_cost = compute_route_cost(
        total_distance_m=total_distance_m,
        mean_shielding_stability_score=mean_shielding_stability_score,
        high_risk_cell_count=high_risk_cell_count,
        weights=resolved_weights,
        distance_normalizer_m=distance_normalizer_m,
    )

    return RouteCandidate(
        route_id=route_id,
        route_type=route_type,
        cells=tuple(resolved_cells),
        total_distance_m=total_distance_m,
        mean_shielding_stability_score=mean_shielding_stability_score,
        minimum_shielding_stability_score=minimum_shielding_stability_score,
        high_risk_cell_count=high_risk_cell_count,
        route_cost=route_cost,
        reason=_route_candidate_reason(
            route_type=route_type,
            total_distance_m=total_distance_m,
            mean_shielding_stability_score=mean_shielding_stability_score,
            high_risk_cell_count=high_risk_cell_count,
        ),
    )


def select_lowest_cost_route(candidates: Sequence[RouteCandidate]) -> RouteCandidate:
    """Return the lowest-cost route candidate, preserving input order on ties."""

    if not candidates:
        raise RoutingError("candidates must not be empty.")
    for candidate in candidates:
        if not isinstance(candidate, RouteCandidate):
            raise RoutingError("all candidates must be RouteCandidate instances.")
    return min(candidates, key=lambda candidate: candidate.route_cost)


def _route_candidate_reason(
    *,
    route_type: RouteCandidateType,
    total_distance_m: float,
    mean_shielding_stability_score: float,
    high_risk_cell_count: int,
) -> str:
    return (
        f"{route_type.value}: distance={total_distance_m:g}m, "
        f"mean_shielding={mean_shielding_stability_score:g}, "
        f"high_risk_cells={high_risk_cell_count}"
    )


def _ensure_route_cells(cells: Sequence[RouteCell]) -> tuple[RouteCell, ...]:
    if not cells:
        raise RoutingError("cells must not be empty.")
    resolved_cells = tuple(cells)
    for cell in resolved_cells:
        if not isinstance(cell, RouteCell):
            raise RoutingError("all cells must be RouteCell instances.")
    return resolved_cells


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RoutingError(f"{field_name} must be a non-empty string.")


def _validate_non_negative_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise RoutingError(f"{field_name} must be finite.")
    if value < 0.0:
        raise RoutingError(f"{field_name} must be non-negative.")


def _validate_score(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise RoutingError(f"{field_name} must be finite.")
    if value < 0.0 or value > 100.0:
        raise RoutingError(f"{field_name} must be within [0, 100].")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RoutingError(f"{field_name} must be an integer.")
    if value < 0:
        raise RoutingError(f"{field_name} must be non-negative.")


def _clamp(value: float, *, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
