from __future__ import annotations

import pytest

from uav_rf_terrain.real_terrain_route_outputs import (
    RealTerrainRouteConfig,
    RealTerrainRouteNode,
    RealTerrainRouteOutputError,
    RouteMode,
    RouteNodeState,
    route_mode_cost_policy,
)
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
from uav_rf_terrain.schemas import ColorClass


def test_route_config_accepts_reviewed_defaults_and_mode_policies() -> None:
    config = RealTerrainRouteConfig(
        graph_spacing_m=50.0,
        profile_spacing_m=25.0,
        allowed_flight_agl_m=60.0,
        frequency_hz=2_400_000_000.0,
        route_margin_m=100.0,
    )

    assert config.connectivity == 8
    assert route_mode_cost_policy(RouteMode.SHIELDING_MINIMUM).shielding_weight == 0.90
    assert route_mode_cost_policy(RouteMode.DETOUR_STABILITY).high_risk_multiplier == 2.0


@pytest.mark.parametrize("field,value", [("graph_spacing_m", True), ("connectivity", 4)])
def test_route_config_rejects_invalid_numeric_and_locked_connectivity(
    field: str, value: object
) -> None:
    values: dict[str, object] = {
        "graph_spacing_m": 50.0,
        "profile_spacing_m": 25.0,
        "allowed_flight_agl_m": 60.0,
        "frequency_hz": 2_400_000_000.0,
        "route_margin_m": 100.0,
        field: value,
    }

    with pytest.raises(RealTerrainRouteOutputError):
        RealTerrainRouteConfig(**values)  # type: ignore[arg-type]


def test_non_valid_node_has_no_fabricated_score_or_non_excluded_color() -> None:
    with pytest.raises(RealTerrainRouteOutputError, match="excluded route node"):
        RealTerrainRouteNode(
            node_id="route-node-r00000-c00000",
            row=0,
            column=0,
            projected_point=LocalPoint(0.0, 0.0),
            node_mgrs=None,
            terrain_msl_m=None,
            surface_msl_m=None,
            flight_agl_m=20.0,
            flight_msl_m=None,
            distance_3d_from_launch_m=None,
            within_operation_radius=False,
            state=RouteNodeState.OUTSIDE_OPERATION_RADIUS,
            traversable=False,
            reason="outside operation radius",
            shielding_stability_score=0.0,
            overall_score=None,
            color_class=ColorClass.EXCLUDED,
            source_zone=None,
            source_zone_state=SourceZoneAvailability.NOT_APPLICABLE,
            source_sensitive=None,
            source_zone_reason="source-zone not applicable",
            fresnel_diagnostics=None,
        )
