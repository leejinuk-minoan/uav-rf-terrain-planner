"""Deterministic EPSG:5179 grid helpers for real-terrain route analysis."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, isfinite, sqrt

from .coordinates import LocalPoint, distance_2d_m


class RouteGraphError(ValueError):
    """Raised when graph bounds, nodes, or snapping are invalid."""


@dataclass(frozen=True)
class RouteGraphBounds:
    min_x_m: float
    min_y_m: float
    max_x_m: float
    max_y_m: float

    def __post_init__(self) -> None:
        if not all(isfinite(value) for value in (self.min_x_m, self.min_y_m, self.max_x_m, self.max_y_m)):
            raise RouteGraphError("route graph bounds must be finite.")
        if self.min_x_m > self.max_x_m or self.min_y_m > self.max_y_m:
            raise RouteGraphError("route graph bounds must not be inverted.")


@dataclass(frozen=True)
class RouteGraphNode:
    node_id: str
    row: int
    column: int
    point: LocalPoint


_NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = (
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)


def build_route_grid(bounds: RouteGraphBounds, *, graph_spacing_m: float) -> tuple[RouteGraphNode, ...]:
    """Build a stable South-to-North, West-to-East EPSG:5179 grid."""

    if not isinstance(bounds, RouteGraphBounds):
        raise RouteGraphError("bounds must be RouteGraphBounds.")
    if not isinstance(graph_spacing_m, (int, float)) or isinstance(graph_spacing_m, bool) or not isfinite(graph_spacing_m) or graph_spacing_m <= 0:
        raise RouteGraphError("graph_spacing_m must be positive and finite.")
    origin_x = floor(bounds.min_x_m / graph_spacing_m) * graph_spacing_m
    origin_y = floor(bounds.min_y_m / graph_spacing_m) * graph_spacing_m
    column_count = int(floor((bounds.max_x_m - origin_x) / graph_spacing_m + 1e-12)) + 1
    row_count = int(floor((bounds.max_y_m - origin_y) / graph_spacing_m + 1e-12)) + 1
    return tuple(
        RouteGraphNode(
            node_id=f"route-node-r{row:05d}-c{column:05d}",
            row=row,
            column=column,
            point=LocalPoint(origin_x + column * graph_spacing_m, origin_y + row * graph_spacing_m),
        )
        for row in range(row_count)
        for column in range(column_count)
    )


def neighboring_node_ids(nodes: tuple[RouteGraphNode, ...], node_id: str) -> tuple[str, ...]:
    """Return existing 8-neighbor IDs in the reviewed clockwise order."""

    by_position = {(node.row, node.column): node.node_id for node in nodes}
    current = next((node for node in nodes if node.node_id == node_id), None)
    if current is None:
        raise RouteGraphError("node_id is not present in graph.")
    return tuple(
        by_position[(current.row + row_offset, current.column + column_offset)]
        for row_offset, column_offset in _NEIGHBOR_OFFSETS
        if (current.row + row_offset, current.column + column_offset) in by_position
    )


def snap_point_to_route_node(
    nodes: tuple[RouteGraphNode, ...], point: LocalPoint, *, graph_spacing_m: float
) -> RouteGraphNode:
    """Snap a point to its nearest node with row/column deterministic tie-breaking."""

    if not nodes:
        raise RouteGraphError("cannot snap without graph nodes.")
    if graph_spacing_m <= 0 or not isfinite(graph_spacing_m):
        raise RouteGraphError("graph_spacing_m must be positive and finite.")
    node = min(nodes, key=lambda item: (distance_2d_m(point, item.point), item.row, item.column))
    if distance_2d_m(point, node.point) > graph_spacing_m * sqrt(2.0) / 2.0 + 1e-12:
        raise RouteGraphError("point cannot be snapped within the graph spacing limit.")
    return node

