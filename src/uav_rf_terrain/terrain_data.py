"""Terrain data adapter interfaces for DEM/DSM integration scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import re
from typing import TYPE_CHECKING, Protocol

from .synthetic import SyntheticTerrainGrid

if TYPE_CHECKING:
    from .coordinates import LocalPoint

Bounds = tuple[float, float, float, float]

RASTER_TYPE_DEM = "DEM"
RASTER_TYPE_DSM = "DSM"

_LOCAL_URI_PREFIX = "file://"
_PUBLIC_URL_PREFIXES = ("http://", "https://")
_WINDOWS_DRIVE_PATH_PATTERN = re.compile(r"(^|[\s\"'`(=])[a-z]:[\\/]")
_UNC_PATH_PATTERN = re.compile(r"(^|[\s\"'`(=])\\\\")
_POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(^|[\s\"'`(=])(/users/|/home/)")


class TerrainDataError(ValueError):
    """Raised when terrain metadata or adapter access is invalid."""


@dataclass(frozen=True)
class TerrainPointSample:
    """One effective DEM/DSM point sample returned by an analysis session."""

    requested_point: LocalPoint
    cell_center_point: LocalPoint
    x_index: int
    y_index: int
    dem_msl: float
    dsm_msl: float
    surface_delta_m: float


@dataclass(frozen=True)
class TerrainRasterMetadata:
    """Metadata for one DEM or DSM raster-like terrain surface."""

    name: str
    raster_type: str
    source_dataset_name: str
    source_provider: str
    license_or_terms: str
    crs: str
    resolution_m: float
    width: int
    height: int
    bounds: Bounds
    nodata_value: float | None
    vertical_datum: str
    processing_summary: str
    is_synthetic: bool
    is_redistributable_processed_data: bool

    def __post_init__(self) -> None:
        _validate_raster_metadata(self)


@dataclass(frozen=True)
class TerrainDatasetMetadata:
    """Paired DEM/DSM metadata for a terrain dataset adapter."""

    dataset_name: str
    dem: TerrainRasterMetadata
    dsm: TerrainRasterMetadata
    processing_date: str
    processing_tool: str
    alignment_status: str
    notes: str

    def __post_init__(self) -> None:
        _validate_metadata_strings(
            (
                self.dataset_name,
                self.processing_date,
                self.processing_tool,
                self.alignment_status,
                self.notes,
            )
        )


class TerrainDataAdapter(Protocol):
    """Interface for DEM/DSM terrain access without prescribing storage."""

    def get_metadata(self) -> TerrainDatasetMetadata:
        """Return dataset metadata for the terrain source."""

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        """Return DEM MSL height in meters at a grid index."""

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        """Return DSM MSL height in meters at a grid index."""

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        """Return DSM minus DEM surface delta in meters at a grid index."""

    def validate_metadata(self) -> TerrainDatasetMetadata:
        """Validate and return dataset metadata."""


@dataclass(frozen=True)
class SyntheticTerrainDataAdapter:
    """In-memory adapter backed by an existing synthetic terrain grid."""

    terrain: SyntheticTerrainGrid
    dataset_name: str | None = None

    def get_metadata(self) -> TerrainDatasetMetadata:
        """Return synthetic DEM/DSM metadata for the backing grid."""

        dataset_name = self.dataset_name or f"synthetic-{self.terrain.scenario_name}"
        bounds = _synthetic_bounds(self.terrain)
        return TerrainDatasetMetadata(
            dataset_name=dataset_name,
            dem=_synthetic_raster_metadata(dataset_name, RASTER_TYPE_DEM, bounds, self.terrain),
            dsm=_synthetic_raster_metadata(dataset_name, RASTER_TYPE_DSM, bounds, self.terrain),
            processing_date="2026-07-10",
            processing_tool="SyntheticTerrainDataAdapter",
            alignment_status="aligned synthetic grid",
            notes=self.terrain.description or "Synthetic in-memory DEM/DSM pair.",
        )

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        """Return DEM MSL height in meters at a grid index."""

        self._validate_indices(x_index=x_index, y_index=y_index)
        return self.terrain.dem_at(ix=x_index, iy=y_index)

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        """Return DSM MSL height in meters at a grid index."""

        self._validate_indices(x_index=x_index, y_index=y_index)
        return self.terrain.dsm_at(ix=x_index, iy=y_index)

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        """Return DSM minus DEM surface delta in meters at a grid index."""

        self._validate_indices(x_index=x_index, y_index=y_index)
        return self.terrain.surface_delta_at(ix=x_index, iy=y_index)

    def validate_metadata(self) -> TerrainDatasetMetadata:
        """Validate and return synthetic dataset metadata."""

        metadata = self.get_metadata()
        validate_terrain_dataset_metadata(metadata)
        return metadata

    def _validate_indices(self, *, x_index: int, y_index: int) -> None:
        if not 0 <= x_index < self.terrain.width_cells:
            raise TerrainDataError(f"x_index out of bounds: {x_index}")
        if not 0 <= y_index < self.terrain.height_cells:
            raise TerrainDataError(f"y_index out of bounds: {y_index}")


def validate_terrain_dataset_metadata(metadata: TerrainDatasetMetadata) -> None:
    """Validate paired DEM/DSM metadata alignment and repository-safe strings."""

    if metadata.dem.raster_type != RASTER_TYPE_DEM:
        raise TerrainDataError("DEM metadata must use raster_type 'DEM'.")
    if metadata.dsm.raster_type != RASTER_TYPE_DSM:
        raise TerrainDataError("DSM metadata must use raster_type 'DSM'.")

    _require_equal("crs", metadata.dem.crs, metadata.dsm.crs)
    _require_equal("resolution_m", metadata.dem.resolution_m, metadata.dsm.resolution_m)
    _require_equal("width", metadata.dem.width, metadata.dsm.width)
    _require_equal("height", metadata.dem.height, metadata.dsm.height)
    _require_equal("bounds", metadata.dem.bounds, metadata.dsm.bounds)
    _require_equal("vertical_datum", metadata.dem.vertical_datum, metadata.dsm.vertical_datum)


def _validate_raster_metadata(metadata: TerrainRasterMetadata) -> None:
    _validate_metadata_strings(
        (
            metadata.name,
            metadata.raster_type,
            metadata.source_dataset_name,
            metadata.source_provider,
            metadata.license_or_terms,
            metadata.crs,
            metadata.vertical_datum,
            metadata.processing_summary,
        )
    )
    if metadata.raster_type not in {RASTER_TYPE_DEM, RASTER_TYPE_DSM}:
        raise TerrainDataError("raster_type must be 'DEM' or 'DSM'.")
    if metadata.resolution_m <= 0 or not isfinite(metadata.resolution_m):
        raise TerrainDataError("resolution_m must be a positive finite value.")
    if metadata.width <= 0:
        raise TerrainDataError("width must be positive.")
    if metadata.height <= 0:
        raise TerrainDataError("height must be positive.")
    if len(metadata.bounds) != 4 or any(not isfinite(value) for value in metadata.bounds):
        raise TerrainDataError("bounds must contain four finite values.")
    if metadata.nodata_value is not None and not isfinite(metadata.nodata_value):
        raise TerrainDataError("nodata_value must be finite when provided.")


def _validate_metadata_strings(values: tuple[str, ...]) -> None:
    for value in values:
        if not value.strip():
            raise TerrainDataError("metadata string fields must not be blank.")
        _raise_for_private_path(value)


def _raise_for_private_path(value: str) -> None:
    normalized = value.strip().casefold()
    if normalized.startswith(_PUBLIC_URL_PREFIXES):
        return
    if (
        normalized.startswith(_LOCAL_URI_PREFIX)
        or _WINDOWS_DRIVE_PATH_PATTERN.search(normalized)
        or _UNC_PATH_PATTERN.search(normalized)
        or _POSIX_PRIVATE_PATH_PATTERN.search(normalized)
    ):
        raise TerrainDataError("metadata must not include private local paths.")


def _require_equal(field_name: str, dem_value: object, dsm_value: object) -> None:
    if dem_value != dsm_value:
        raise TerrainDataError(f"DEM/DSM metadata mismatch for {field_name}.")


def _synthetic_bounds(terrain: SyntheticTerrainGrid) -> Bounds:
    x_min = terrain.origin.x_m
    y_min = terrain.origin.y_m
    x_max = x_min + (terrain.width_cells - 1) * terrain.grid_size_m
    y_max = y_min + (terrain.height_cells - 1) * terrain.grid_size_m
    return (x_min, y_min, x_max, y_max)


def _synthetic_raster_metadata(
    dataset_name: str,
    raster_type: str,
    bounds: Bounds,
    terrain: SyntheticTerrainGrid,
) -> TerrainRasterMetadata:
    return TerrainRasterMetadata(
        name=f"{dataset_name}-{raster_type.lower()}",
        raster_type=raster_type,
        source_dataset_name=dataset_name,
        source_provider="uav-rf-terrain synthetic generator",
        license_or_terms="Synthetic in-memory fixture for tests",
        crs="LOCAL_SYNTHETIC_METERS",
        resolution_m=terrain.grid_size_m,
        width=terrain.width_cells,
        height=terrain.height_cells,
        bounds=bounds,
        nodata_value=None,
        vertical_datum="synthetic_msl",
        processing_summary="Generated in memory from synthetic terrain fixtures.",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )
