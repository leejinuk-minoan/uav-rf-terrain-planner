from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from uav_rf_terrain.source_zone_raster import (
    SourceZoneRasterError,
    SourceZoneRasterSample,
    classify_source_zone_neighborhood_values,
    classify_source_zone_values,
    summarize_source_zone_samples,
    _validate_aligned_rasters,
)
from uav_rf_terrain.source_zones import TerrainSourceZone, is_source_sensitive_zone


def test_dem_invalid_raises() -> None:
    with pytest.raises(SourceZoneRasterError, match="DEM cell is invalid"):
        classify_source_zone_values(
            dem_valid=False, original_landcover_value=0, gap_filled_landcover_value=0
        )


@pytest.mark.parametrize(
    ("original", "gap_filled", "expected"),
    ((10, 10, TerrainSourceZone.ESA_DERIVED),
     (0, 50, TerrainSourceZone.WMS_GAP_FILLED),
     (0, 0, TerrainSourceZone.DEM_ONLY_FALLBACK)),
)
def test_scalar_source_zone_rules(original: int, gap_filled: int, expected: TerrainSourceZone) -> None:
    assert classify_source_zone_values(
        dem_valid=True,
        original_landcover_value=original,
        gap_filled_landcover_value=gap_filled,
    ) is expected


@pytest.mark.parametrize("value", (math.nan, math.inf, -math.inf))
def test_non_finite_landcover_raises(value: float) -> None:
    with pytest.raises(SourceZoneRasterError, match="must be finite"):
        classify_source_zone_values(
            dem_valid=True, original_landcover_value=value, gap_filled_landcover_value=0
        )


def test_dem_only_fallback_is_source_sensitive() -> None:
    assert is_source_sensitive_zone(TerrainSourceZone.DEM_ONLY_FALLBACK)


def test_esa_and_wms_neighborhood_is_mixed_boundary() -> None:
    base, output = classify_source_zone_neighborhood_values(
        center_dem_valid=True,
        center_original_landcover_value=10,
        center_gap_filled_landcover_value=10,
        neighborhood_values=((True, 0, 50),),
        boundary_radius_cells=3,
    )
    assert base is TerrainSourceZone.ESA_DERIVED
    assert output is TerrainSourceZone.MIXED_BOUNDARY


def test_esa_only_neighborhood_remains_esa() -> None:
    _, output = classify_source_zone_neighborhood_values(
        center_dem_valid=True,
        center_original_landcover_value=10,
        center_gap_filled_landcover_value=10,
        neighborhood_values=((True, 40, 40), (True, 80, 80)),
        boundary_radius_cells=3,
    )
    assert output is TerrainSourceZone.ESA_DERIVED


def test_dem_only_neighbor_makes_output_mixed_boundary() -> None:
    _, output = classify_source_zone_neighborhood_values(
        center_dem_valid=True,
        center_original_landcover_value=0,
        center_gap_filled_landcover_value=50,
        neighborhood_values=((True, 0, 0),),
        boundary_radius_cells=3,
    )
    assert output is TerrainSourceZone.MIXED_BOUNDARY


def test_invalid_dem_neighbor_is_excluded_from_boundary_mix() -> None:
    _, output = classify_source_zone_neighborhood_values(
        center_dem_valid=True,
        center_original_landcover_value=10,
        center_gap_filled_landcover_value=10,
        neighborhood_values=((False, math.nan, math.nan),),
        boundary_radius_cells=3,
    )
    assert output is TerrainSourceZone.ESA_DERIVED


def test_zero_radius_returns_base_zone() -> None:
    base, output = classify_source_zone_neighborhood_values(
        center_dem_valid=True,
        center_original_landcover_value=0,
        center_gap_filled_landcover_value=50,
        neighborhood_values=((True, 10, 10),),
        boundary_radius_cells=0,
    )
    assert base is output is TerrainSourceZone.WMS_GAP_FILLED


def test_sample_summary_uses_task_020a_summary() -> None:
    summary = summarize_source_zone_samples((
        _sample(TerrainSourceZone.ESA_DERIVED, False),
        _sample(TerrainSourceZone.MIXED_BOUNDARY, True),
    ))
    assert summary.sample_count == 2
    assert summary.esa_derived_count == 1
    assert summary.mixed_boundary_count == 1
    assert summary.source_sensitive_count == 1
    assert summary.invalid_dem_count == 0


def test_public_record_has_no_prohibited_operational_fields() -> None:
    prohibited = {"rssi", "sinr", "packet_loss", "flight_command", "autopilot", "control_api"}
    assert prohibited.isdisjoint(SourceZoneRasterSample.__dataclass_fields__)


def test_aligned_raster_metadata_is_accepted() -> None:
    dem = _raster_metadata()
    _validate_aligned_rasters(dem, _raster_metadata(), _raster_metadata())


def test_misaligned_transform_raises() -> None:
    dem = _raster_metadata()
    shifted = _raster_metadata(transform=(90, 0, 90, 0, -90, 0))
    with pytest.raises(SourceZoneRasterError, match="transform must match"):
        _validate_aligned_rasters(dem, shifted, _raster_metadata())


def _sample(zone: TerrainSourceZone, sensitive: bool) -> SourceZoneRasterSample:
    return SourceZoneRasterSample(
        x_m=0.0, y_m=0.0, row=0, col=0, dem_valid=True,
        original_landcover_value=10.0, gap_filled_landcover_value=10.0,
        base_source_zone=TerrainSourceZone.ESA_DERIVED, output_source_zone=zone,
        boundary_radius_cells=3, source_sensitive=sensitive, reason="test sample",
    )


def _raster_metadata(
    *, transform: tuple[int, int, int, int, int, int] = (90, 0, 0, 0, -90, 0)
) -> SimpleNamespace:
    return SimpleNamespace(
        crs="EPSG:5179",
        transform=transform,
        bounds=(0, 0, 900, 900),
        width=10,
        height=10,
    )
