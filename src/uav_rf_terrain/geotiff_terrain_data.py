"""Optional local GeoTIFF adapter for aligned DEM/DSM terrain data."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import importlib
from math import ceil, isfinite
from pathlib import Path
from types import ModuleType
from typing import Any

from .terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainNoDataError,
    TerrainPointOutsideError,
    TerrainPointSample,
    TerrainRasterMetadata,
    validate_terrain_dataset_metadata,
)
from .coordinates import LocalPoint, distance_2d_m
from .profile import TerrainProfile, TerrainProfileError, TerrainProfileSample


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

    def open_analysis_session(self) -> "LocalGeoTiffTerrainAnalysisSession":
        """Return a lazy context that reuses one open DEM/DSM pair."""

        return LocalGeoTiffTerrainAnalysisSession(self)

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
            raise TerrainNoDataError("terrain cell is masked or NoData.")

        value = float(cell[0, 0])
        if metadata.nodata_value is not None and value == metadata.nodata_value:
            raise TerrainNoDataError("terrain cell is NoData.")
        if not isfinite(value):
            raise TerrainNoDataError("terrain cell must be finite.")
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


class LocalGeoTiffTerrainAnalysisSession:
    """Read point and profile samples with one open north-up DEM/DSM pair."""

    def __init__(self, adapter: LocalGeoTiffTerrainDataAdapter) -> None:
        self._adapter = adapter
        self._stack: ExitStack | None = None
        self._dem: Any | None = None
        self._dsm: Any | None = None
        self.metadata: TerrainDatasetMetadata | None = None

    def __enter__(self) -> "LocalGeoTiffTerrainAnalysisSession":
        stack = ExitStack()
        try:
            rasterio = _load_rasterio()
            dem = stack.enter_context(rasterio.open(Path(self._adapter.dem_path)))
            dsm = stack.enter_context(rasterio.open(Path(self._adapter.dsm_path)))
            _validate_north_up_transform(dem.transform)
            _validate_north_up_transform(dsm.transform)
            metadata = TerrainDatasetMetadata(
                dataset_name=self._adapter.dataset_name,
                dem=self._adapter._raster_metadata(dem, RASTER_TYPE_DEM),
                dsm=self._adapter._raster_metadata(dsm, RASTER_TYPE_DSM),
                processing_date=self._adapter.processing_date,
                processing_tool=self._adapter.processing_tool,
                alignment_status="aligned local GeoTIFF DEM/DSM pair",
                notes=self._adapter.notes,
            )
            validate_terrain_dataset_metadata(metadata)
        except Exception:
            stack.close()
            raise
        self._stack = stack
        self._dem = dem
        self._dsm = dsm
        self.metadata = metadata
        return self

    def __exit__(self, *args: object) -> None:
        if self._stack is not None:
            self._stack.close()
        self._stack = None
        self._dem = None
        self._dsm = None

    def sample_point(self, point: LocalPoint) -> TerrainPointSample:
        """Return the effective DEM/DSM sample for one projected point."""

        dem, dsm = self._open_sources()
        if not isfinite(point.x_m) or not isfinite(point.y_m):
            raise TerrainDataError("sample point coordinates must be finite.")
        bounds = dem.bounds
        if not (
            bounds.left <= point.x_m < bounds.right
            and bounds.bottom < point.y_m <= bounds.top
        ):
            raise TerrainPointOutsideError("sample point is outside the raster extent.")
        row, col = dem.index(point.x_m, point.y_m)
        if not (0 <= row < dem.height and 0 <= col < dem.width):
            raise TerrainPointOutsideError("sample point is outside the raster extent.")
        dem_value = _read_open_value(dem, row=row, col=col)
        dsm_value = _read_open_value(dsm, row=row, col=col)
        effective_dsm = max(dsm_value, dem_value)
        center_x, center_y = dem.xy(row, col)
        return TerrainPointSample(
            requested_point=point,
            cell_center_point=LocalPoint(float(center_x), float(center_y)),
            x_index=int(col),
            y_index=int(dem.height - 1 - row),
            dem_msl=dem_value,
            dsm_msl=effective_dsm,
            surface_delta_m=effective_dsm - dem_value,
        )

    def extract_profile(
        self,
        start: LocalPoint,
        end: LocalPoint,
        *,
        sample_spacing_m: float,
        scenario_name: str,
    ) -> TerrainProfile:
        """Extract a profile through the same open dataset handles."""

        if not isfinite(sample_spacing_m) or sample_spacing_m <= 0:
            raise TerrainProfileError("sample_spacing_m must be positive.")
        distance = distance_2d_m(start, end)
        if distance <= 0:
            raise TerrainProfileError("start and end must be different local points.")
        steps = max(1, int(ceil(distance / sample_spacing_m)))
        samples: list[TerrainProfileSample] = []
        for sample_index in range(steps + 1):
            fraction = sample_index / steps
            requested = LocalPoint(
                start.x_m + (end.x_m - start.x_m) * fraction,
                start.y_m + (end.y_m - start.y_m) * fraction,
                start.z_m + (end.z_m - start.z_m) * fraction,
            )
            sample = self.sample_point(requested)
            samples.append(
                TerrainProfileSample(
                    sample_index=sample_index,
                    ix=sample.x_index,
                    iy=sample.y_index,
                    point=requested,
                    distance_from_start_m=distance * fraction,
                    distance_to_end_m=distance * (1.0 - fraction),
                    dem_msl=sample.dem_msl,
                    dsm_msl=sample.dsm_msl,
                    surface_delta_m=sample.surface_delta_m,
                )
            )
        return TerrainProfile(
            scenario_name=scenario_name,
            start=start,
            end=end,
            sample_spacing_m=sample_spacing_m,
            samples=tuple(samples),
        )

    def _open_sources(self) -> tuple[Any, Any]:
        if self._dem is None or self._dsm is None:
            raise TerrainDataError("terrain analysis session is not open.")
        return self._dem, self._dsm


def _validate_north_up_transform(transform: Any) -> None:
    if not (transform.a > 0 and transform.e < 0 and transform.b == 0 and transform.d == 0):
        raise TerrainDataError(
            "north-up GeoTIFF transform must have a > 0, e < 0, b == 0, and d == 0."
        )


def _read_open_value(source: Any, *, row: int, col: int) -> float:
    cell = source.read(1, window=((row, row + 1), (col, col + 1)), masked=True)
    if _cell_is_masked(cell):
        raise TerrainNoDataError("terrain cell is masked or NoData.")
    value = float(cell[0, 0])
    if source.nodata is not None and value == float(source.nodata):
        raise TerrainNoDataError("terrain cell is NoData.")
    if not isfinite(value):
        raise TerrainNoDataError("terrain cell must be finite.")
    return value
