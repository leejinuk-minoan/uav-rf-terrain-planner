"""Optional local GeoTIFF adapter for aligned DEM/DSM terrain data."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from math import isfinite
from pathlib import Path
from types import ModuleType
from typing import Any

from .terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
    validate_terrain_dataset_metadata,
)


@dataclass(frozen=True)
class LocalGeoTiffTerrainDataAdapter:
    """Read aligned local DEM/DSM GeoTIFFs through the terrain adapter protocol.

    File paths remain runtime-only values and are never copied into public metadata.
    Rasterio is imported lazily when metadata or cell values are requested.
    """

    dem_path: str | Path
    dsm_path: str | Path
    dataset_name: str = "local-geotiff-dem-dsm"
    source_dataset_name: str = "local redistributable processed DEM/DSM"
    source_provider: str = "user-prepared public-source terrain data"
    license_or_terms: str = "see local processing metadata"
    processing_date: str = "2026-07-10"
    processing_tool: str = "Task 018A preprocessing scripts"
    vertical_datum: str = "MSL"
    notes: str = (
        "Local GeoTIFF DEM/DSM adapter metadata; file paths are not stored "
        "in public metadata."
    )

    def get_metadata(self) -> TerrainDatasetMetadata:
        """Read and return aligned DEM/DSM metadata."""

        rasterio = _load_rasterio()
        with rasterio.open(Path(self.dem_path)) as dem_source:
            dem = self._raster_metadata(dem_source, RASTER_TYPE_DEM)
        with rasterio.open(Path(self.dsm_path)) as dsm_source:
            dsm = self._raster_metadata(dsm_source, RASTER_TYPE_DSM)
        return TerrainDatasetMetadata(
            dataset_name=self.dataset_name,
            dem=dem,
            dsm=dsm,
            processing_date=self.processing_date,
            processing_tool=self.processing_tool,
            alignment_status="aligned local GeoTIFF DEM/DSM pair",
            notes=self.notes,
        )

    def validate_metadata(self) -> TerrainDatasetMetadata:
        """Validate GeoTIFF-specific constraints and DEM/DSM alignment."""

        metadata = self.get_metadata()
        validate_terrain_dataset_metadata(metadata)
        return metadata

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        """Return a finite, non-NoData DEM MSL value."""

        metadata = self.validate_metadata()
        return self._read_value(
            Path(self.dem_path),
            metadata.dem,
            x_index=x_index,
            y_index=y_index,
        )

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        """Return a finite, non-NoData DSM MSL value."""

        metadata = self.validate_metadata()
        return self._read_value(
            Path(self.dsm_path),
            metadata.dsm,
            x_index=x_index,
            y_index=y_index,
        )

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        """Return DSM minus DEM at a project grid index."""

        return self.get_dsm_msl(x_index, y_index) - self.get_dem_msl(x_index, y_index)

    def _raster_metadata(self, source: Any, raster_type: str) -> TerrainRasterMetadata:
        transform = source.transform
        if transform.b != 0 or transform.d != 0:
            raise TerrainDataError("rotated or sheared GeoTIFF transforms are not supported.")

        x_resolution_m = abs(float(transform.a))
        y_resolution_m = abs(float(transform.e))
        if not isfinite(x_resolution_m) or not isfinite(y_resolution_m):
            raise TerrainDataError("GeoTIFF pixel resolution must be finite.")
        if x_resolution_m != y_resolution_m:
            raise TerrainDataError("GeoTIFF x/y pixel sizes must match.")
        if source.crs is None:
            raise TerrainDataError("GeoTIFF CRS is required.")

        bounds = source.bounds
        return TerrainRasterMetadata(
            name=f"{self.dataset_name}-{raster_type.lower()}",
            raster_type=raster_type,
            source_dataset_name=self.source_dataset_name,
            source_provider=self.source_provider,
            license_or_terms=self.license_or_terms,
            crs=source.crs.to_string(),
            resolution_m=x_resolution_m,
            width=int(source.width),
            height=int(source.height),
            bounds=(
                float(bounds.left),
                float(bounds.bottom),
                float(bounds.right),
                float(bounds.top),
            ),
            nodata_value=None if source.nodata is None else float(source.nodata),
            vertical_datum=self.vertical_datum,
            processing_summary="Read from a user-provided local GeoTIFF at runtime.",
            is_synthetic=False,
            is_redistributable_processed_data=True,
        )

    def _read_value(
        self,
        path: Path,
        metadata: TerrainRasterMetadata,
        *,
        x_index: int,
        y_index: int,
    ) -> float:
        row, col = _project_index_to_raster_row_col(
            width=metadata.width,
            height=metadata.height,
            x_index=x_index,
            y_index=y_index,
        )
        rasterio = _load_rasterio()
        with rasterio.open(path) as source:
            cell = source.read(
                1,
                window=((row, row + 1), (col, col + 1)),
                masked=True,
            )
        if _cell_is_masked(cell):
            raise TerrainDataError("terrain cell is masked or NoData.")

        value = float(cell[0, 0])
        if metadata.nodata_value is not None and value == metadata.nodata_value:
            raise TerrainDataError("terrain cell is NoData.")
        if not isfinite(value):
            raise TerrainDataError("terrain cell must be finite.")
        return value


def _load_rasterio() -> ModuleType:
    try:
        return importlib.import_module("rasterio")
    except ModuleNotFoundError as exc:
        raise TerrainDataError(
            "rasterio is required for LocalGeoTiffTerrainDataAdapter runtime use."
        ) from exc


def _project_index_to_raster_row_col(
    *,
    width: int,
    height: int,
    x_index: int,
    y_index: int,
) -> tuple[int, int]:
    if not 0 <= x_index < width:
        raise TerrainDataError(f"x_index out of bounds: {x_index}")
    if not 0 <= y_index < height:
        raise TerrainDataError(f"y_index out of bounds: {y_index}")
    return height - 1 - y_index, x_index


def _cell_is_masked(cell: Any) -> bool:
    mask: Any = getattr(cell, "mask", False)
    try:
        return bool(mask[0, 0])
    except (IndexError, TypeError):
        return bool(mask)
