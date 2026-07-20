from __future__ import annotations

from dataclasses import dataclass

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.profile import TerrainProfile, TerrainProfileSample
from uav_rf_terrain.real_terrain_minimum_altitude import (
    PreparedRealTerrainRoute,
    PreparedRealTerrainRouteSample,
    RealTerrainMinimumAltitudeError,
    compute_real_terrain_minimum_altitude,
)
from uav_rf_terrain.real_terrain_minimum_altitude_outputs import (
    RealTerrainMinimumAltitudeConfig,
)
from uav_rf_terrain.real_terrain_route_outputs import RouteMode


@dataclass(frozen=True)
class _RouteConfig:
    allowed_flight_agl_m: float = 20.0
    frequency_hz: float = 300_000_000.0
    profile_spacing_m: float = 10.0


@dataclass(frozen=True)
class _RouteResult:
    config: _RouteConfig = _RouteConfig()
    launch_ground_msl_m: float = 100.0
    selected_candidate_id: str = "candidate-001"
    launch_site_mgrs: str = "52SCB0000000000"
    target_mgrs: str = "52SCB0001000000"
    terrain_metadata: str = "metadata"


@dataclass(frozen=True)
class _SelectedLaunch:
    candidate_id: str = "candidate-001"
    launch_site_mgrs: str = "52SCB0000000000"
    projected_point: LocalPoint = LocalPoint(0.0, 0.0)


def _profile() -> TerrainProfile:
    return TerrainProfile(
        scenario_name="test",
        start=LocalPoint(0.0, 0.0),
        end=LocalPoint(10.0, 0.0),
        sample_spacing_m=10.0,
        samples=(
            TerrainProfileSample(0, 0, 0, LocalPoint(0.0, 0.0), 0.0, 10.0, 100.0, 100.0, 0.0),
            TerrainProfileSample(1, 1, 0, LocalPoint(10.0, 0.0), 10.0, 0.0, 120.0, 120.0, 0.0),
        ),
    )


def test_pure_engine_uses_hand_calculated_endpoint_requirement() -> None:
    # wavelength = 1 m, t = 1 and r = 0 at the endpoint: required MSL = DSM = 120.
    prepared = PreparedRealTerrainRoute(
        route_id="route-shielding_minimum",
        mode=RouteMode.SHIELDING_MINIMUM,
        source_order=0,
        source_total_distance_3d_m=10.0,
        route_polyline_total_distance_2d_m=0.0,
        terrain_metadata="metadata",
        samples=(
            PreparedRealTerrainRouteSample(
                route_sample_id="route-shielding_minimum-sample-000",
                route_id="route-shielding_minimum",
                mode=RouteMode.SHIELDING_MINIMUM,
                route_sample_index=0,
                route_sample_mgrs="52SCB0001000000",
                projected_point=LocalPoint(10.0, 0.0),
                cumulative_route_distance_2d_m=0.0,
                local_dem_msl_m=120.0,
                local_dsm_msl_m=120.0,
                is_snapped_target_endpoint=True,
                radial_distance_2d_m=10.0,
                radial_profile=_profile(),
            ),
        ),
    )
    result = compute_real_terrain_minimum_altitude(
        route_result=_RouteResult(),
        selected_launch_site=_SelectedLaunch(),
        prepared_routes=(prepared,),
        config=RealTerrainMinimumAltitudeConfig(expected_frequency_hz=300_000_000.0),
    )
    route = result.route_results[0]
    assert route.minimum_required_constant_route_msl_m == pytest.approx(120.0)
    assert route.route_samples[0].current_clearance_margin_m == pytest.approx(20.0)


def test_nonzero_evidence_requires_profile() -> None:
    with pytest.raises(RealTerrainMinimumAltitudeError):
        PreparedRealTerrainRouteSample(
            route_sample_id="route-shielding_minimum-sample-000",
            route_id="route-shielding_minimum",
            mode=RouteMode.SHIELDING_MINIMUM,
            route_sample_index=0,
            route_sample_mgrs="52SCB0001000000",
            projected_point=LocalPoint(10.0, 0.0),
            cumulative_route_distance_2d_m=0.0,
            local_dem_msl_m=120.0,
            local_dsm_msl_m=120.0,
            is_snapped_target_endpoint=True,
            radial_distance_2d_m=10.0,
            radial_profile=None,
        )
