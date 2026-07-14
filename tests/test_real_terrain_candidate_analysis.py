from __future__ import annotations

from dataclasses import dataclass

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
)
from uav_rf_terrain.source_zones import TerrainSourceZone

from uav_rf_terrain.real_terrain_candidate_analysis import (
    CandidateAnalysisState,
    RealTerrainLaunchAreaAnalysisError,
    RealTerrainLaunchAreaConfig,
    SourceZoneAvailability,
    analyze_real_terrain_launch_area,
)


def _metadata() -> TerrainDatasetMetadata:
    common = dict(
        source_dataset_name="test terrain",
        source_provider="test provider",
        license_or_terms="test only",
        crs="EPSG:5179",
        resolution_m=10.0,
        width=5,
        height=5,
        bounds=(0.0, 0.0, 40.0, 40.0),
        nodata_value=None,
        vertical_datum="MSL",
        processing_summary="in-memory test terrain",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )
    return TerrainDatasetMetadata(
        dataset_name="test-epsg5179-terrain",
        dem=TerrainRasterMetadata(name="test-dem", raster_type=RASTER_TYPE_DEM, **common),
        dsm=TerrainRasterMetadata(name="test-dsm", raster_type=RASTER_TYPE_DSM, **common),
        processing_date="2026-07-14",
        processing_tool="pytest",
        alignment_status="aligned",
        notes="in-memory test fixture",
    )


@dataclass
class GridAdapter:
    dem: float = 100.0
    dsm: float = 100.0
    metadata_calls: int = 0

    def validate_metadata(self) -> TerrainDatasetMetadata:
        self.metadata_calls += 1
        return _metadata()

    def get_metadata(self) -> TerrainDatasetMetadata:
        return _metadata()

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        self._validate_index(x_index, y_index)
        return self.dem

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        self._validate_index(x_index, y_index)
        return self.dsm

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        self._validate_index(x_index, y_index)
        return self.dsm - self.dem

    @staticmethod
    def _validate_index(x_index: int, y_index: int) -> None:
        if not 0 <= x_index < 5 or not 0 <= y_index < 5:
            raise TerrainDataError("terrain cell is outside fixture bounds")


def _config(**overrides: object) -> RealTerrainLaunchAreaConfig:
    values: dict[str, object] = {
        "scenario_name": "test real terrain analysis",
        "target_point": LocalPoint(20.0, 20.0),
        "operating_radius_m": 10.0,
        "candidate_spacing_m": 10.0,
        "allowed_agl_m": 20.0,
        "launch_antenna_height_agl_m": 20.0,
        "frequency_hz": 2_400_000_000.0,
        "profile_sample_spacing_m": 10.0,
        "include_center": True,
        "include_out_of_radius": True,
    }
    values.update(overrides)
    return RealTerrainLaunchAreaConfig(**values)  # type: ignore[arg-type]


def test_pipeline_returns_real_projected_features_and_ordered_source_zone_batch() -> None:
    provider_points: list[tuple[LocalPoint, ...]] = []

    def provider(points: tuple[LocalPoint, ...]) -> tuple[TerrainSourceZone, ...]:
        provider_points.append(points)
        return tuple(TerrainSourceZone.ESA_DERIVED for _ in points)

    result = analyze_real_terrain_launch_area(
        GridAdapter(),
        _config(),
        source_zone_provider=provider,
    )

    assert result.summary.total_candidate_count == 9
    assert tuple(record.candidate_id for record in result.candidate_records) == tuple(
        feature.candidate_id for feature in result.candidate_features
    )
    assert result.candidate_features[0].feature_id == "candidate-feature-00000"
    assert result.candidate_features[0].x_m == result.candidate_records[0].candidate_point.x_m
    assert result.candidate_features[0].y_m == result.candidate_records[0].candidate_point.y_m
    assert result.candidate_features[0].geometry_crs == "EPSG:5179"
    assert result.candidate_features[0].candidate_cell_mgrs is None
    assert result.candidate_features[0].coordinate_display_state == "projected_only"
    assert len(provider_points) == 1
    eligible = [
        record
        for record in result.candidate_records
        if record.state is not CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
    ]
    assert provider_points[0] == tuple(record.candidate_point for record in eligible)
    assert all(record.source_zone_state is SourceZoneAvailability.AVAILABLE for record in eligible)
    assert all(
        record.source_zone_state is SourceZoneAvailability.NOT_APPLICABLE
        for record in result.candidate_records
        if record.state is CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
    )


def test_pipeline_normalizes_lower_dsm_without_mutating_adapter_values() -> None:
    adapter = GridAdapter(dem=100.0, dsm=90.0)

    result = analyze_real_terrain_launch_area(
        adapter,
        _config(include_center=False, include_out_of_radius=False),
    )

    assert result.target_surface_msl == 100.0
    assert all(record.launch_surface_msl == 100.0 for record in result.candidate_records)
    assert adapter.get_dsm_msl(2, 2) == 90.0
    assert all(record.state is CandidateAnalysisState.VALID_SCORED for record in result.candidate_records)


def test_source_zone_provider_failure_marks_only_eligible_records_unavailable() -> None:
    def unavailable_provider(points: tuple[LocalPoint, ...]) -> tuple[TerrainSourceZone, ...]:
        raise RuntimeError("local landcover unavailable")

    result = analyze_real_terrain_launch_area(
        GridAdapter(), _config(), source_zone_provider=unavailable_provider
    )

    assert result.warnings == ("source-zone provider unavailable",)
    assert any(record.state is CandidateAnalysisState.VALID_SCORED for record in result.candidate_records)
    assert all(
        record.source_zone_state is SourceZoneAvailability.UNAVAILABLE
        for record in result.candidate_records
        if record.state is not CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS
    )


def test_invalid_config_fails_before_adapter_access() -> None:
    adapter = GridAdapter()

    with pytest.raises(RealTerrainLaunchAreaAnalysisError, match="scenario_name"):
        analyze_real_terrain_launch_area(adapter, _config(scenario_name=" "))

    assert adapter.metadata_calls == 0
