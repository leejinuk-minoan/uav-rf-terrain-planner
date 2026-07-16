from __future__ import annotations

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.coordinate_conversion import Wgs84MapPoint
from uav_rf_terrain.launch_site_selection import SelectedLaunchSiteRecord, select_launch_site
from uav_rf_terrain.real_terrain_candidate_analysis import (
    RealTerrainLaunchAreaConfig,
    SourceZoneAvailability,
    analyze_real_terrain_launch_area,
)
from uav_rf_terrain.real_terrain_route_analysis import (
    RealTerrainRouteAnalysisError,
    analyze_selected_launch_site_routes,
    validate_selected_launch_site_for_route,
)
from uav_rf_terrain.real_terrain_route_outputs import RealTerrainRouteConfig
from uav_rf_terrain.real_terrain_launch_area_map import (
    RealTerrainLaunchAreaMapConfig,
    build_real_terrain_launch_area_map_package,
)
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
)


class _FlatAdapter:
    def get_metadata(self) -> TerrainDatasetMetadata:
        common = dict(
            source_dataset_name="test",
            source_provider="test",
            license_or_terms="test",
            crs="EPSG:5179",
            resolution_m=10.0,
            width=5,
            height=5,
            bounds=(0.0, 0.0, 40.0, 40.0),
            nodata_value=None,
            vertical_datum="MSL",
            processing_summary="test",
            is_synthetic=True,
            is_redistributable_processed_data=True,
        )
        return TerrainDatasetMetadata(
            "test-route-terrain",
            TerrainRasterMetadata("dem", RASTER_TYPE_DEM, **common),
            TerrainRasterMetadata("dsm", RASTER_TYPE_DSM, **common),
            "2026-07-16",
            "pytest",
            "aligned",
            "test",
        )

    def validate_metadata(self) -> TerrainDatasetMetadata:
        return self.get_metadata()

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        self._check(x_index, y_index)
        return 100.0

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        self._check(x_index, y_index)
        return 100.0

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        self._check(x_index, y_index)
        return 0.0

    @staticmethod
    def _check(x_index: int, y_index: int) -> None:
        if not 0 <= x_index < 5 or not 0 <= y_index < 5:
            raise TerrainDataError("outside test grid")


def test_selected_launch_site_requires_nonempty_public_mgrs_before_route_analysis() -> None:
    selected = SelectedLaunchSiteRecord(
        candidate_id="candidate-001",
        launch_site_mgrs="52SCB1234512345",
        external_coordinate_format="MGRS",
        user_coordinate_field="launch_site_mgrs",
        projected_point=LocalPoint(0.0, 0.0),
        color_class=ColorClass.GREEN,
        overall_score=90.0,
        shielding_stability_score=90.0,
        distance_3d_m=20.0,
        candidate_reason="valid",
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="not requested",
        fresnel_diagnostics=None,
    )
    config = RealTerrainRouteConfig(50.0, 25.0, 60.0, 2_400_000_000.0, 100.0)

    with pytest.raises(RealTerrainRouteAnalysisError, match="source result"):
        validate_selected_launch_site_for_route(selected, None, config)  # type: ignore[arg-type]


def test_route_analysis_returns_deterministic_mgrs_facing_path_without_internal_coordinates() -> None:
    adapter = _FlatAdapter()
    source = analyze_real_terrain_launch_area(
        adapter,
        RealTerrainLaunchAreaConfig(
            scenario_name="route test",
            target_point=LocalPoint(20.0, 20.0),
            operating_radius_m=30.0,
            candidate_spacing_m=10.0,
            allowed_agl_m=20.0,
            launch_antenna_height_agl_m=20.0,
            frequency_hz=2_400_000_000.0,
            profile_sample_spacing_m=10.0,
            include_center=False,
            include_out_of_radius=False,
        ),
    )

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        assert precision == 5
        return f"52SCB{int(point.x_m):05d}{int(point.y_m):05d}"

    package = build_real_terrain_launch_area_map_package(
        source,
        RealTerrainLaunchAreaMapConfig(candidate_cell_size_m=10.0),
        projected_to_wgs84=lambda point: Wgs84MapPoint(
            point.x_m / 1000.0,
            point.y_m / 1000.0,
        ),
        projected_to_mgrs=mgrs,
    )
    selected = select_launch_site(
        source,
        package,
        next(record.candidate_id for record in source.candidate_records if record.candidate_score),
    )

    result = analyze_selected_launch_site_routes(
        adapter,
        selected,
        source,
        RealTerrainRouteConfig(10.0, 10.0, 20.0, 2_400_000_000.0, 1.0),
        projected_to_mgrs=mgrs,
    )

    assert result.route_candidates
    public = result.to_public_dict()
    assert "x_m" not in str(public)
    assert result.launch_site_mgrs.startswith("52SCB")
