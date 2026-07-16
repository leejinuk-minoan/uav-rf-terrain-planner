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


def test_non_aligned_clipped_bounds_emit_only_aligned_nodes_inside_the_bounds() -> None:
    bounds = RouteGraphBounds(1.0, 11.0, 29.0, 39.0)

    nodes = build_route_grid(bounds, graph_spacing_m=10.0)

    assert [(node.row, node.column) for node in nodes] == [(1, 1), (1, 2), (2, 1), (2, 2)]
    assert all(
        bounds.min_x_m - 1e-12 <= node.point.x_m <= bounds.max_x_m + 1e-12
        and bounds.min_y_m - 1e-12 <= node.point.y_m <= bounds.max_y_m + 1e-12
        for node in nodes
    )


@pytest.mark.parametrize(
    ("bounds", "expected_ids"),
    [
        (
            RouteGraphBounds(10.0, 0.0, 10.0, 20.0),
            ["route-node-r00000-c00000", "route-node-r00001-c00000", "route-node-r00002-c00000"],
        ),
        (
            RouteGraphBounds(0.0, 10.0, 20.0, 10.0),
            ["route-node-r00000-c00000", "route-node-r00000-c00001", "route-node-r00000-c00002"],
        ),
    ],
)
def test_single_dimension_aligned_bounds_are_stable(
    bounds: RouteGraphBounds, expected_ids: list[str]
) -> None:
    assert [node.node_id for node in build_route_grid(bounds, graph_spacing_m=10.0)] == expected_ids


def test_bounds_without_an_aligned_node_are_rejected() -> None:
    with pytest.raises(RouteGraphError, match="no aligned"):
        build_route_grid(RouteGraphBounds(1.0, 1.0, 9.0, 9.0), graph_spacing_m=10.0)
