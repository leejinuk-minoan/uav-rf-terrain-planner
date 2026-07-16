from __future__ import annotations

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.route_graph import (
    RouteGraphBounds,
    RouteGraphError,
    build_route_grid,
    neighboring_node_ids,
    snap_point_to_route_node,
)


def test_grid_is_row_major_and_neighbors_follow_fixed_clockwise_order() -> None:
    nodes = build_route_grid(RouteGraphBounds(0.0, 0.0, 20.0, 20.0), graph_spacing_m=10.0)

    assert [node.node_id for node in nodes] == [
        "route-node-r00000-c00000",
        "route-node-r00000-c00001",
        "route-node-r00000-c00002",
        "route-node-r00001-c00000",
        "route-node-r00001-c00001",
        "route-node-r00001-c00002",
        "route-node-r00002-c00000",
        "route-node-r00002-c00001",
        "route-node-r00002-c00002",
    ]
    assert neighboring_node_ids(nodes, "route-node-r00001-c00001") == (
        "route-node-r00002-c00001",
        "route-node-r00002-c00002",
        "route-node-r00001-c00002",
        "route-node-r00000-c00002",
        "route-node-r00000-c00001",
        "route-node-r00000-c00000",
        "route-node-r00001-c00000",
        "route-node-r00002-c00000",
    )


def test_snap_prefers_lower_row_then_column_on_exact_distance_tie() -> None:
    nodes = build_route_grid(RouteGraphBounds(0.0, 0.0, 10.0, 10.0), graph_spacing_m=10.0)

    snapped = snap_point_to_route_node(nodes, LocalPoint(5.0, 5.0), graph_spacing_m=10.0)

    assert snapped.node_id == "route-node-r00000-c00000"


def test_snap_rejects_point_outside_half_diagonal_limit() -> None:
    nodes = build_route_grid(RouteGraphBounds(0.0, 0.0, 10.0, 10.0), graph_spacing_m=10.0)

    with pytest.raises(RouteGraphError, match="cannot be snapped"):
        snap_point_to_route_node(nodes, LocalPoint(20.0, 20.0), graph_spacing_m=10.0)
