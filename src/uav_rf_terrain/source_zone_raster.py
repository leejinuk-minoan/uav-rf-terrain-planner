"""Local raster classification for terrain source-zone metadata."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import ExitStack
from dataclasses import dataclass
import importlib
from math import isfinite
from pathlib import Path
from types import ModuleType
from typing import Any

from .source_zones import TerrainSourceZone, is_source_sensitive_zone, summarize_source_zones

Numeric = int | float
NeighborhoodValue = tuple[bool, Numeric, Numeric]


class SourceZoneRasterError(ValueError):
    """Raised when local source-zone raster access or values are invalid."""


@dataclass(frozen=True)
class SourceZoneRasterSample:
    """One local raster point classified with base and boundary-aware zones."""

    x_m: float
    y_m: float
    row: int
    col: int
    dem_valid: bool
    original_landcover_value: float
    gap_filled_landcover_value: float
    base_source_zone: TerrainSourceZone
    output_source_zone: TerrainSourceZone
    boundary_radius_cells: int
    source_sensitive: bool
    reason: str


@dataclass(frozen=True)
class SourceZoneRasterSummary:
    """Counts for local raster source-zone samples."""

    sample_count: int
    esa_derived_count: int
    wms_gap_filled_count: int
    dem_only_fallback_count: int
    mixed_boundary_count: int
    source_sensitive_count: int
    invalid_dem_count: int
    boundary_radius_cells: int
    reason: str


def classify_source_zone_values(
    *,
    dem_valid: bool,
    original_landcover_value: Numeric,
    gap_filled_landcover_value: Numeric,
) -> TerrainSourceZone:
    """Classify one valid DEM cell from original and gap-filled landcover values."""

    if not isinstance(dem_valid, bool):
        raise SourceZoneRasterError("dem_valid must be a bool.")
    if not dem_valid:
        raise SourceZoneRasterError("DEM cell is invalid or NoData.")
    original = _finite_value("original_landcover_value", original_landcover_value)
    gap_filled = _finite_value("gap_filled_landcover_value", gap_filled_landcover_value)
    if original != 0:
        return TerrainSourceZone.ESA_DERIVED
    if gap_filled != 0:
        return TerrainSourceZone.WMS_GAP_FILLED
    return TerrainSourceZone.DEM_ONLY_FALLBACK


def classify_source_zone_neighborhood_values(
    *,
    center_dem_valid: bool,
    center_original_landcover_value: Numeric,
    center_gap_filled_landcover_value: Numeric,
    neighborhood_values: Sequence[NeighborhoodValue],
    boundary_radius_cells: int,
) -> tuple[TerrainSourceZone, TerrainSourceZone]:
    """Return base and output zones for preselected square-neighborhood values."""

    radius = _boundary_radius(boundary_radius_cells)
    base_zone = classify_source_zone_values(
        dem_valid=center_dem_valid,
        original_landcover_value=center_original_landcover_value,
        gap_filled_landcover_value=center_gap_filled_landcover_value,
    )
    if radius == 0:
        return base_zone, base_zone
    zones = {base_zone}
    for dem_valid, original_value, gap_filled_value in neighborhood_values:
        if not isinstance(dem_valid, bool):
            raise SourceZoneRasterError("neighborhood dem_valid must be a bool.")
        if not dem_valid:
            continue
        zones.add(
            classify_source_zone_values(
                dem_valid=True,
                original_landcover_value=original_value,
                gap_filled_landcover_value=gap_filled_value,
            )
        )
    output_zone = base_zone if len(zones) == 1 else TerrainSourceZone.MIXED_BOUNDARY
    return base_zone, output_zone


def summarize_source_zone_samples(
    samples: Sequence[SourceZoneRasterSample],
) -> SourceZoneRasterSummary:
    """Summarize boundary-aware output zones from local raster samples."""

    if not samples:
        raise SourceZoneRasterError("samples must not be empty.")
    resolved = tuple(samples)
    if any(not isinstance(sample, SourceZoneRasterSample) for sample in resolved):
        raise SourceZoneRasterError("all samples must be SourceZoneRasterSample values.")
    radii = {sample.boundary_radius_cells for sample in resolved}
    if len(radii) != 1:
        raise SourceZoneRasterError("all samples must use the same boundary radius.")
    summary = summarize_source_zones(tuple(sample.output_source_zone for sample in resolved))
    return SourceZoneRasterSummary(
        sample_count=len(resolved),
        esa_derived_count=summary.esa_derived_count,
        wms_gap_filled_count=summary.wms_gap_filled_count,
        dem_only_fallback_count=summary.dem_only_fallback_count,
        mixed_boundary_count=summary.mixed_boundary_count,
        source_sensitive_count=sum(sample.source_sensitive for sample in resolved),
        invalid_dem_count=sum(not sample.dem_valid for sample in resolved),
        boundary_radius_cells=next(iter(radii)),
        reason=summary.reason,
    )


@dataclass(frozen=True)
class LocalSourceZoneRasterClassifier:
    """Classify source zones from aligned local DEM and landcover rasters."""

    dem_path: str | Path
    original_landcover_path: str | Path
    gap_filled_landcover_path: str | Path

    def sample_point(
        self, x_m: float, y_m: float, boundary_radius_cells: int = 3
    ) -> SourceZoneRasterSample:
        """Classify one projected point."""

        return self.sample_points(
            ((x_m, y_m),), boundary_radius_cells=boundary_radius_cells
        )[0]

    def sample_points(
        self,
        points: Sequence[tuple[float, float]],
        boundary_radius_cells: int = 3,
    ) -> tuple[SourceZoneRasterSample, ...]:
        """Classify projected points using one aligned-raster open session."""

        if not points:
            raise SourceZoneRasterError("points must not be empty.")
        radius = _boundary_radius(boundary_radius_cells)
        rasterio = _load_rasterio()
        with ExitStack() as stack:
            dem = stack.enter_context(rasterio.open(Path(self.dem_path)))
            original = stack.enter_context(rasterio.open(Path(self.original_landcover_path)))
            gap_filled = stack.enter_context(rasterio.open(Path(self.gap_filled_landcover_path)))
            _validate_aligned_rasters(dem, original, gap_filled)
            return tuple(
                _sample_open_rasters(
                    dem=dem,
                    original=original,
                    gap_filled=gap_filled,
                    x_m=x_m,
                    y_m=y_m,
                    boundary_radius_cells=radius,
                )
                for x_m, y_m in points
            )


def _sample_open_rasters(
    *, dem: Any, original: Any, gap_filled: Any, x_m: float, y_m: float,
    boundary_radius_cells: int,
) -> SourceZoneRasterSample:
    x = _finite_value("x_m", x_m)
    y = _finite_value("y_m", y_m)
    row, col = dem.index(x, y)
    if not (0 <= row < dem.height and 0 <= col < dem.width):
        raise SourceZoneRasterError("sample point is outside the raster extent.")
    center_dem = dem.read(1, window=((row, row + 1), (col, col + 1)), masked=True)
    center_original = original.read(1, window=((row, row + 1), (col, col + 1)))
    center_gap = gap_filled.read(1, window=((row, row + 1), (col, col + 1)))
    dem_valid = not _masked(center_dem, 0, 0) and isfinite(float(center_dem[0, 0]))
    original_value = _read_landcover_cell(center_original, 0, 0, "original landcover")
    gap_value = _read_landcover_cell(center_gap, 0, 0, "gap-filled landcover")
    neighborhood: list[NeighborhoodValue] = []
    if boundary_radius_cells > 0:
        row_start = max(0, row - boundary_radius_cells)
        row_stop = min(dem.height, row + boundary_radius_cells + 1)
        col_start = max(0, col - boundary_radius_cells)
        col_stop = min(dem.width, col + boundary_radius_cells + 1)
        window = ((row_start, row_stop), (col_start, col_stop))
        dem_cells = dem.read(1, window=window, masked=True)
        original_cells = original.read(1, window=window)
        gap_cells = gap_filled.read(1, window=window)
        for local_row in range(row_stop - row_start):
            for local_col in range(col_stop - col_start):
                neighbor_valid = not _masked(dem_cells, local_row, local_col)
                if neighbor_valid:
                    neighbor_valid = isfinite(float(dem_cells[local_row, local_col]))
                if not neighbor_valid:
                    neighborhood.append((False, 0.0, 0.0))
                    continue
                neighborhood.append((
                    True,
                    _read_landcover_cell(original_cells, local_row, local_col, "original landcover"),
                    _read_landcover_cell(gap_cells, local_row, local_col, "gap-filled landcover"),
                ))
    base_zone, output_zone = classify_source_zone_neighborhood_values(
        center_dem_valid=dem_valid,
        center_original_landcover_value=original_value,
        center_gap_filled_landcover_value=gap_value,
        neighborhood_values=neighborhood,
        boundary_radius_cells=boundary_radius_cells,
    )
    return SourceZoneRasterSample(
        x_m=x, y_m=y, row=int(row), col=int(col), dem_valid=True,
        original_landcover_value=original_value,
        gap_filled_landcover_value=gap_value,
        base_source_zone=base_zone, output_source_zone=output_zone,
        boundary_radius_cells=boundary_radius_cells,
        source_sensitive=is_source_sensitive_zone(output_zone),
        reason=_sample_reason(base_zone, output_zone),
    )


def _sample_reason(base: TerrainSourceZone, output: TerrainSourceZone) -> str:
    if output is TerrainSourceZone.MIXED_BOUNDARY:
        return f"{base.value} base cell has multiple valid source zones nearby."
    if base is TerrainSourceZone.DEM_ONLY_FALLBACK:
        return "DEM-only fallback uses surface-delta zero and DSM proxy equal to DEM."
    return f"{base.value} source zone only within the requested neighborhood."


def _validate_aligned_rasters(dem: Any, original: Any, gap_filled: Any) -> None:
    if dem.crs is None:
        raise SourceZoneRasterError("DEM CRS is required.")
    for name, raster in (("original landcover", original), ("gap-filled landcover", gap_filled)):
        if raster.crs != dem.crs:
            raise SourceZoneRasterError(f"{name} CRS must match DEM CRS.")
        if raster.transform != dem.transform:
            raise SourceZoneRasterError(f"{name} transform must match DEM transform.")
        if raster.bounds != dem.bounds:
            raise SourceZoneRasterError(f"{name} bounds must match DEM bounds.")
        if raster.width != dem.width or raster.height != dem.height:
            raise SourceZoneRasterError(f"{name} dimensions must match DEM dimensions.")


def _load_rasterio() -> ModuleType:
    try:
        return importlib.import_module("rasterio")
    except ModuleNotFoundError as exc:
        raise SourceZoneRasterError(
            "rasterio is required for LocalSourceZoneRasterClassifier runtime use."
        ) from exc


def _read_landcover_cell(cells: Any, row: int, col: int, label: str) -> float:
    if _masked(cells, row, col):
        raise SourceZoneRasterError(f"{label} cell is masked or NoData.")
    return _finite_value(label, float(cells[row, col]))


def _masked(cells: Any, row: int, col: int) -> bool:
    mask: Any = getattr(cells, "mask", False)
    try:
        return bool(mask[row, col])
    except (IndexError, TypeError):
        return bool(mask)


def _finite_value(name: str, value: Numeric) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SourceZoneRasterError(f"{name} must be a numeric value.")
    resolved = float(value)
    if not isfinite(resolved):
        raise SourceZoneRasterError(f"{name} must be finite.")
    return resolved


def _boundary_radius(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceZoneRasterError("boundary_radius_cells must be an integer.")
    if value < 0:
        raise SourceZoneRasterError("boundary_radius_cells must be non-negative.")
    return value
