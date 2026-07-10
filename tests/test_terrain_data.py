from dataclasses import replace
from pathlib import Path

import pytest

from uav_rf_terrain.synthetic import SCENARIO_FLAT_WITH_BUILDING, create_synthetic_terrain
from uav_rf_terrain.terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    SyntheticTerrainDataAdapter,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
    validate_terrain_dataset_metadata,
)


def _raster_metadata(*, raster_type: str = RASTER_TYPE_DEM) -> TerrainRasterMetadata:
    return TerrainRasterMetadata(
        name=f"synthetic-{raster_type.lower()}",
        raster_type=raster_type,
        source_dataset_name="synthetic-dataset",
        source_provider="synthetic provider",
        license_or_terms="synthetic fixture",
        crs="LOCAL_SYNTHETIC_METERS",
        resolution_m=10.0,
        width=4,
        height=3,
        bounds=(0.0, 0.0, 30.0, 20.0),
        nodata_value=None,
        vertical_datum="synthetic_msl",
        processing_summary="Created in memory for unit tests.",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )


def _dataset_metadata() -> TerrainDatasetMetadata:
    return TerrainDatasetMetadata(
        dataset_name="synthetic-dataset",
        dem=_raster_metadata(raster_type=RASTER_TYPE_DEM),
        dsm=_raster_metadata(raster_type=RASTER_TYPE_DSM),
        processing_date="2026-07-10",
        processing_tool="unit-test",
        alignment_status="aligned",
        notes="Synthetic unit-test metadata.",
    )


def test_terrain_raster_metadata_creation() -> None:
    metadata = _raster_metadata()

    assert metadata.raster_type == RASTER_TYPE_DEM
    assert metadata.resolution_m == 10.0


def test_terrain_dataset_metadata_creation() -> None:
    metadata = _dataset_metadata()

    assert metadata.dataset_name == "synthetic-dataset"
    assert metadata.dem.raster_type == RASTER_TYPE_DEM
    assert metadata.dsm.raster_type == RASTER_TYPE_DSM


def test_metadata_alignment_validation_passes() -> None:
    validate_terrain_dataset_metadata(_dataset_metadata())


def test_crs_mismatch_validation_fails() -> None:
    metadata = _dataset_metadata()
    metadata = replace(metadata, dsm=replace(metadata.dsm, crs="LOCAL_OTHER"))

    with pytest.raises(TerrainDataError, match="crs"):
        validate_terrain_dataset_metadata(metadata)


def test_resolution_mismatch_validation_fails() -> None:
    metadata = _dataset_metadata()
    metadata = replace(metadata, dsm=replace(metadata.dsm, resolution_m=20.0))

    with pytest.raises(TerrainDataError, match="resolution_m"):
        validate_terrain_dataset_metadata(metadata)


def test_width_height_mismatch_validation_fails() -> None:
    metadata = _dataset_metadata()
    metadata = replace(metadata, dsm=replace(metadata.dsm, width=5, height=4))

    with pytest.raises(TerrainDataError, match="width"):
        validate_terrain_dataset_metadata(metadata)


def test_invalid_raster_type_fails() -> None:
    with pytest.raises(TerrainDataError, match="raster_type"):
        _raster_metadata(raster_type="SURFACE")


def test_synthetic_adapter_dem_and_dsm_access() -> None:
    terrain = create_synthetic_terrain(
        SCENARIO_FLAT_WITH_BUILDING,
        width_cells=5,
        height_cells=5,
        grid_size_m=10.0,
        base_dem_msl=50.0,
    )
    adapter = SyntheticTerrainDataAdapter(terrain)

    assert adapter.get_dem_msl(2, 2) == 50.0
    assert adapter.get_dsm_msl(2, 2) > adapter.get_dem_msl(2, 2)


def test_synthetic_adapter_surface_delta_calculation() -> None:
    terrain = create_synthetic_terrain(
        SCENARIO_FLAT_WITH_BUILDING,
        width_cells=5,
        height_cells=5,
        grid_size_m=10.0,
        base_dem_msl=50.0,
    )
    adapter = SyntheticTerrainDataAdapter(terrain)

    assert adapter.get_surface_delta_m(2, 2) == adapter.get_dsm_msl(2, 2) - 50.0


def test_synthetic_adapter_out_of_bounds_exception() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT_WITH_BUILDING, width_cells=3, height_cells=3)
    adapter = SyntheticTerrainDataAdapter(terrain)

    with pytest.raises(TerrainDataError, match="x_index"):
        adapter.get_dem_msl(3, 0)
    with pytest.raises(TerrainDataError, match="y_index"):
        adapter.get_dsm_msl(0, -1)


def test_private_local_path_guard() -> None:
    with pytest.raises(TerrainDataError, match="private local paths"):
        TerrainDatasetMetadata(
            dataset_name="synthetic-dataset",
            dem=_raster_metadata(raster_type=RASTER_TYPE_DEM),
            dsm=_raster_metadata(raster_type=RASTER_TYPE_DSM),
            processing_date="2026-07-10",
            processing_tool="C:/Users/example/local-tool",
            alignment_status="aligned",
            notes="Synthetic unit-test metadata.",
        )


def test_public_https_url_is_allowed_in_metadata_field() -> None:
    metadata = TerrainDatasetMetadata(
        dataset_name="synthetic-dataset",
        dem=replace(
            _raster_metadata(raster_type=RASTER_TYPE_DEM),
            license_or_terms="https://example.org/source-or-license",
        ),
        dsm=replace(
            _raster_metadata(raster_type=RASTER_TYPE_DSM),
            license_or_terms="https://example.org/source-or-license",
        ),
        processing_date="2026-07-10",
        processing_tool="unit-test",
        alignment_status="aligned",
        notes="Synthetic unit-test metadata.",
    )

    validate_terrain_dataset_metadata(metadata)


@pytest.mark.parametrize(
    "local_path",
    [
        "C:/Users/example/source",
        r"C:\Users\example\source",
        "/home/example/source",
        "file:///Users/example/source",
    ],
)
def test_private_local_path_guard_blocks_local_path_forms(local_path: str) -> None:
    with pytest.raises(TerrainDataError, match="private local paths"):
        TerrainDatasetMetadata(
            dataset_name="synthetic-dataset",
            dem=_raster_metadata(raster_type=RASTER_TYPE_DEM),
            dsm=_raster_metadata(raster_type=RASTER_TYPE_DSM),
            processing_date="2026-07-10",
            processing_tool=local_path,
            alignment_status="aligned",
            notes="Synthetic unit-test metadata.",
        )


def test_terrain_data_module_has_no_external_gis_imports() -> None:
    module_text = Path("src/uav_rf_terrain/terrain_data.py").read_text(encoding="utf-8")

    assert "import raster" not in module_text
    assert "import osgeo" not in module_text
    assert "import geo" not in module_text
