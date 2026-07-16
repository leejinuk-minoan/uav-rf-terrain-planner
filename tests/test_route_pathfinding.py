from __future__ import annotations

from uav_rf_terrain.route_pathfinding import DirectedRouteEdge, dijkstra_shortest_path
from uav_rf_terrain.route_pathfinding import RoutePathfindingError
import pytest


def test_dijkstra_prefers_lower_distance_then_predecessor_on_equal_cost() -> None:
    edges = (
        DirectedRouteEdge("start", "left", 1.0, 2.0),
        DirectedRouteEdge("start", "right", 1.0, 1.0),
        DirectedRouteEdge("left", "target", 1.0, 2.0),
        DirectedRouteEdge("right", "target", 1.0, 1.0),
    )

    path = dijkstra_shortest_path(
        edges,
        start_node_id="start",
        target_node_id="target",
        node_positions={"start": (0, 0), "left": (1, 0), "right": (0, 1), "target": (2, 0)},
        max_path_expansions=20,
    )

    assert path.node_ids == ("start", "right", "target")
    assert path.total_cost == 2.0
    assert path.total_distance_3d_m == 2.0


def test_dijkstra_reports_no_path_and_expansion_guard() -> None:
    with pytest.raises(RoutePathfindingError, match="no traversable"):
        dijkstra_shortest_path(
            (),
            start_node_id="start",
            target_node_id="target",
            node_positions={"start": (0, 0), "target": (1, 0)},
            max_path_expansions=1,
        )
    with pytest.raises(RoutePathfindingError, match="expansion guard"):
        dijkstra_shortest_path(
            (
                DirectedRouteEdge("start", "middle", 1.0, 1.0),
                DirectedRouteEdge("middle", "target", 1.0, 1.0),
            ),
            start_node_id="start",
            target_node_id="target",
            node_positions={"start": (0, 0), "middle": (0, 1), "target": (0, 2)},
            max_path_expansions=1,
        )
