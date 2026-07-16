"""Deterministic EPSG:5179 grid helpers for real-terrain route analysis."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor, isfinite, sqrt

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


@dataclass(frozen=True)
class RouteGraphTopology:
    """Precomputed immutable node and neighbor indexes for bounded route work."""

    nodes: tuple[RouteGraphNode, ...]
    node_by_id: dict[str, RouteGraphNode]
    node_id_by_position: dict[tuple[int, int], str]
    neighbors_by_id: dict[str, tuple[str, ...]]


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
    minimum_column = int(ceil((bounds.min_x_m - origin_x) / graph_spacing_m - 1e-12))
    maximum_column = int(floor((bounds.max_x_m - origin_x) / graph_spacing_m + 1e-12))
    minimum_row = int(ceil((bounds.min_y_m - origin_y) / graph_spacing_m - 1e-12))
    maximum_row = int(floor((bounds.max_y_m - origin_y) / graph_spacing_m + 1e-12))
    if minimum_column > maximum_column or minimum_row > maximum_row:
        raise RouteGraphError("route graph bounds contain no aligned lattice node.")
    return tuple(
        RouteGraphNode(
            node_id=f"route-node-r{row:05d}-c{column:05d}",
            row=row,
            column=column,
            point=LocalPoint(origin_x + column * graph_spacing_m, origin_y + row * graph_spacing_m),
        )
        for row in range(minimum_row, maximum_row + 1)
        for column in range(minimum_column, maximum_column + 1)
    )


def neighboring_node_ids(nodes: tuple[RouteGraphNode, ...], node_id: str) -> tuple[str, ...]:
    """Return existing 8-neighbor IDs in the reviewed clockwise order."""

    topology = build_route_graph_topology(nodes)
    try:
        return topology.neighbors_by_id[node_id]
    except KeyError as exc:
        raise RouteGraphError("node_id is not present in graph.") from exc


def build_route_graph_topology(nodes: tuple[RouteGraphNode, ...]) -> RouteGraphTopology:
    """Build node/position/ordered-neighbor indexes exactly once for a graph."""

    node_by_id = {node.node_id: node for node in nodes}
    if len(node_by_id) != len(nodes):
        raise RouteGraphError("route graph node IDs must be unique.")
    node_id_by_position = {(node.row, node.column): node.node_id for node in nodes}
    if len(node_id_by_position) != len(nodes):
        raise RouteGraphError("route graph positions must be unique.")
    neighbors_by_id = {
        node.node_id: tuple(
            node_id_by_position[(node.row + row_offset, node.column + column_offset)]
            for row_offset, column_offset in _NEIGHBOR_OFFSETS
            if (node.row + row_offset, node.column + column_offset) in node_id_by_position
        )
        for node in nodes
    }
    return RouteGraphTopology(nodes, node_by_id, node_id_by_position, neighbors_by_id)


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
