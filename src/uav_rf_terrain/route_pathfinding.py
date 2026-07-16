"""Standard-library deterministic Dijkstra helpers for terrain route graphs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import heapq
from math import isfinite


class RoutePathfindingError(ValueError):
    """Raised when deterministic route search cannot produce a valid path."""

    def __init__(self, message: str, *, expansions: int = 0) -> None:
        super().__init__(message)
        self.expansions = expansions


class RouteNoPathError(RoutePathfindingError):
    """Raised when one route objective has no traversable path."""


class RouteExpansionLimitError(RoutePathfindingError):
    """Raised when a path search exceeds its explicit resource limit."""


class RoutePathfindingInputError(RoutePathfindingError):
    """Raised when a graph, position index, or penalty input is malformed."""


class RoutePathfindingInvariantError(RoutePathfindingError):
    """Raised when a predecessor or graph invariant cannot be reconstructed."""


@dataclass(frozen=True)
class DirectedRouteEdge:
    from_node_id: str
    to_node_id: str
    cost: float
    distance_3d_m: float

    def __post_init__(self) -> None:
        if not self.from_node_id or not self.to_node_id:
            raise RoutePathfindingInputError("route edge node IDs must be non-empty.")
        for name, value in (("cost", self.cost), ("distance_3d_m", self.distance_3d_m)):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0.0
            ):
                raise RoutePathfindingInputError(f"edge {name} must be finite and non-negative.")


@dataclass(frozen=True)
class DijkstraPath:
    node_ids: tuple[str, ...]
    total_cost: float
    total_distance_3d_m: float
    expansions: int


def dijkstra_shortest_path(
    edges: tuple[DirectedRouteEdge, ...],
    *,
    start_node_id: str,
    target_node_id: str,
    node_positions: dict[str, tuple[int, int]],
    max_path_expansions: int,
    additional_edge_cost: dict[tuple[str, str], float] | None = None,
) -> DijkstraPath:
    """Return a deterministic least-cost directed path using reviewed tie-breaks."""

    if not start_node_id or not target_node_id:
        raise RoutePathfindingInputError("start_node_id and target_node_id must be non-empty.")
    if isinstance(max_path_expansions, bool) or not isinstance(max_path_expansions, int) or max_path_expansions <= 0:
        raise RoutePathfindingInputError("max_path_expansions must be a positive integer.")
    if start_node_id not in node_positions or target_node_id not in node_positions:
        raise RoutePathfindingInputError("start and target node positions must be present.")
    for node_id, position in node_positions.items():
        if (
            not isinstance(node_id, str)
            or not node_id
            or not isinstance(position, tuple)
            or len(position) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in position)
        ):
            raise RoutePathfindingInputError("node positions must use non-empty IDs and integer row/column pairs.")
    for edge in edges:
        if edge.from_node_id not in node_positions or edge.to_node_id not in node_positions:
            raise RoutePathfindingInputError("every edge endpoint must have a node position.")
    if start_node_id == target_node_id:
        return DijkstraPath((start_node_id,), 0.0, 0.0, 0)
    adjacency: dict[str, list[DirectedRouteEdge]] = defaultdict(list)
    for edge in edges:
        adjacency[edge.from_node_id].append(edge)
    for source in adjacency:
        adjacency[source].sort(key=lambda edge: (node_positions[edge.to_node_id], edge.to_node_id))
    penalties = additional_edge_cost or {}
    for edge_key, penalty in penalties.items():
        if (
            not isinstance(edge_key, tuple)
            or len(edge_key) != 2
            or not all(isinstance(node_id, str) and node_id for node_id in edge_key)
            or isinstance(penalty, bool)
            or not isinstance(penalty, (int, float))
            or not isfinite(penalty)
            or penalty < 0.0
        ):
            raise RoutePathfindingInputError(
                "additional edge cost must use directed IDs and finite non-negative values."
            )
    tolerance = 1e-12
    counter = 0
    queue: list[tuple[float, float, int, int, int, str]] = []
    start_row, start_column = node_positions[start_node_id]
    heapq.heappush(queue, (0.0, 0.0, start_row, start_column, counter, start_node_id))
    distances: dict[str, tuple[float, float, tuple[int, int] | None]] = {
        start_node_id: (0.0, 0.0, None)
    }
    predecessors: dict[str, str] = {}
    expansions = 0
    while queue:
        cost, distance, _, _, _, node_id = heapq.heappop(queue)
        best_cost, best_distance, _ = distances[node_id]
        if cost > best_cost + tolerance or (abs(cost - best_cost) <= tolerance and distance > best_distance + tolerance):
            continue
        if node_id == target_node_id:
            path: list[str] = [node_id]
            while path[-1] != start_node_id:
                predecessor = predecessors.get(path[-1])
                if predecessor is None:
                    raise RoutePathfindingInvariantError(
                        "path predecessor is unavailable during reconstruction.",
                        expansions=expansions,
                    )
                path.append(predecessor)
            path.reverse()
            return DijkstraPath(tuple(path), cost, distance, expansions)
        expansions += 1
        if expansions > max_path_expansions:
            raise RouteExpansionLimitError("path expansion guard exceeded.", expansions=expansions)
        for edge in adjacency.get(node_id, ()):
            penalty = penalties.get((edge.from_node_id, edge.to_node_id), 0.0)
            candidate_cost = cost + edge.cost + penalty
            candidate_distance = distance + edge.distance_3d_m
            predecessor_position = node_positions[node_id]
            existing = distances.get(edge.to_node_id)
            should_replace = existing is None or candidate_cost < existing[0] - tolerance
            if existing is not None and abs(candidate_cost - existing[0]) <= tolerance:
                should_replace = (
                    candidate_distance < existing[1] - tolerance
                    or (
                        abs(candidate_distance - existing[1]) <= tolerance
                        and predecessor_position < (existing[2] or predecessor_position)
                    )
                )
            if should_replace:
                distances[edge.to_node_id] = (candidate_cost, candidate_distance, predecessor_position)
                predecessors[edge.to_node_id] = node_id
                row, column = node_positions[edge.to_node_id]
                counter += 1
                heapq.heappush(queue, (candidate_cost, candidate_distance, row, column, counter, edge.to_node_id))
    raise RouteNoPathError("no traversable path was found.", expansions=expansions)
