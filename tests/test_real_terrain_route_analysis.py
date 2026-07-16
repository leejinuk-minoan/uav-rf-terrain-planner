from __future__ import annotations

from dataclasses import replace

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.coordinate_conversion import Wgs84MapPoint
from uav_rf_terrain.launch_site_selection import SelectedLaunchSiteRecord, select_launch_site
from uav_rf_terrain.real_terrain_candidate_analysis import (
    RealTerrainLaunchAreaConfig,
    RealTerrainLaunchAreaResult,
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
    def __init__(self) -> None:
        self.validate_metadata_calls = 0

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
        self.validate_metadata_calls += 1
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


def _source_selected_and_config(
    adapter: _FlatAdapter,
) -> tuple[RealTerrainLaunchAreaResult, SelectedLaunchSiteRecord, RealTerrainRouteConfig]:
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
        projected_to_wgs84=lambda point: Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0),
        projected_to_mgrs=mgrs,
    )
    selected = select_launch_site(
        source,
        package,
        next(record.candidate_id for record in source.candidate_records if record.candidate_score),
    )
    return source, selected, RealTerrainRouteConfig(10.0, 10.0, 20.0, 2_400_000_000.0, 1.0)


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
    source, selected, config = _source_selected_and_config(adapter)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        assert precision == 5
        return f"52SCB{int(point.x_m):05d}{int(point.y_m):05d}"

    result = analyze_selected_launch_site_routes(
        adapter,
        selected,
        source,
        config,
        projected_to_mgrs=mgrs,
    )

    assert result.route_candidates
    public = result.to_public_dict()
    assert "x_m" not in str(public)
    assert result.launch_site_mgrs.startswith("52SCB")
    assert public["path_semantics"] == "snapped_graph_path"
    assert result.snapped_launch_node_id is not None


def test_selected_mgrs_mismatch_and_conversion_failure_do_not_open_a_route_session() -> None:
    adapter = _FlatAdapter()
    source, selected, config = _source_selected_and_config(adapter)
    adapter.validate_metadata_calls = 0

    with pytest.raises(RealTerrainRouteAnalysisError, match="does not match"):
        analyze_selected_launch_site_routes(
            adapter,
            replace(selected, launch_site_mgrs="52SCB9999999999"),
            source,
            config,
            projected_to_mgrs=lambda point, *, precision: "52SCB0000000000",
        )
    assert adapter.validate_metadata_calls == 0

    with pytest.raises(RealTerrainRouteAnalysisError, match="MGRS conversion failed"):
        analyze_selected_launch_site_routes(
            adapter,
            selected,
            source,
            config,
            projected_to_mgrs=lambda point, *, precision: None,  # type: ignore[return-value]
        )
    assert adapter.validate_metadata_calls == 0


def test_route_mgrs_conversion_cache_reuses_each_projected_point_for_candidate_and_handoff() -> None:
    adapter = _FlatAdapter()
    source, selected, config = _source_selected_and_config(adapter)
    calls: list[LocalPoint] = []

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        assert precision == 5
        calls.append(point)
        return f"52SCB{int(point.x_m):05d}{int(point.y_m):05d}"

    result = analyze_selected_launch_site_routes(adapter, selected, source, config, projected_to_mgrs=mgrs)

    expected_points = {selected.projected_point, source.target_point}
    expected_points.update(
        point for candidate in result.route_candidates for point in candidate.ordered_projected_points
    )
    assert len(calls) == len(expected_points)
    assert all(
        handoff_point.point_mgrs == path_point.mgrs
        for candidate, handoff in zip(result.route_candidates, result.waypoint_handoffs)
        for path_point, handoff_point in zip(candidate.path, handoff)
    )


def test_same_snapped_launch_and_target_returns_a_one_node_zero_distance_route() -> None:
    adapter = _FlatAdapter()
    source, selected, config = _source_selected_and_config(adapter)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        assert precision == 5
        return f"52SCB{int(point.x_m):05d}{int(point.y_m):05d}"

    result = analyze_selected_launch_site_routes(
        adapter,
        selected,
        source,
        replace(config, graph_spacing_m=40.0),
        projected_to_mgrs=mgrs,
    )

    assert result.snapped_launch_node_id == result.snapped_target_node_id
    assert all(len(candidate.path) == 1 and candidate.total_distance_3d_m == 0.0 for candidate in result.route_candidates)
