"""Connect local raster source zones to candidate-grid metadata assignment."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable, Sequence
from math import ceil, isfinite, sqrt
from pathlib import Path
from types import ModuleType
from typing import Any

from uav_rf_terrain.candidate_source_zones import (
    CandidateSourceZoneAssignment,
    CandidateSourceZoneError,
    assign_source_zones_to_candidate_cells,
    summarize_candidate_source_zone_assignment,
)
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.grid import CandidateCell, CandidateGridConfig, generate_candidate_grid
from uav_rf_terrain.source_zone_raster import (
    LocalSourceZoneRasterClassifier,
    SourceZoneRasterError,
    classify_source_zone_values,
)
from uav_rf_terrain.source_zones import TerrainSourceZone

Point = tuple[float, float]
ZoneProvider = Callable[[float, float], TerrainSourceZone]


def build_smoke_candidate_cells(
    centers: Sequence[Point], *, spacing_m: float, radius_cells: int
) -> tuple[CandidateCell, ...]:
    """Build small square candidate grids around anonymous representative centers."""

    if not centers:
        raise CandidateSourceZoneError("representative centers must not be empty.")
    if not isfinite(spacing_m) or spacing_m <= 0:
        raise CandidateSourceZoneError("grid spacing must be positive and finite.")
    if isinstance(radius_cells, bool) or not isinstance(radius_cells, int) or radius_cells < 1:
        raise CandidateSourceZoneError("grid radius cells must be a positive integer.")
    cells: list[CandidateCell] = []
    for sample_index, (x_m, y_m) in enumerate(centers, start=1):
        grid = generate_candidate_grid(
            LocalPoint(x_m=x_m, y_m=y_m),
            CandidateGridConfig(
                radius_m=spacing_m * radius_cells,
                spacing_m=spacing_m,
                include_center=True,
                include_excluded=True,
            ),
        )
        cells.extend(
            CandidateCell(
                cell_id=f"sample-{sample_index}-{cell.cell_id}",
                point=cell.point,
                distance_2d_m=cell.distance_2d_m,
                distance_3d_m=cell.distance_3d_m,
                within_operation_radius=cell.within_operation_radius,
            )
            for cell in grid
        )
    return tuple(cells)


def run_candidate_source_zone_smoke(
    cells: Sequence[CandidateCell],
    provider: ZoneProvider,
    *,
    boundary_radius_cells: int,
) -> CandidateSourceZoneAssignment:
    """Assign provider zones to smoke candidate cells through the Task 020C API."""

    return assign_source_zones_to_candidate_cells(
        cells,
        provider,
        assignment_radius_cells=boundary_radius_cells,
    )


def format_smoke_summary(assignment: CandidateSourceZoneAssignment) -> str:
    """Format aggregate-only output without coordinates or file paths."""

    summary = summarize_candidate_source_zone_assignment(assignment)
    return "\n".join(
        (
            f"candidate_count={summary['candidate_source_zone_record_count']}",
            f"esa_derived_count={summary['esa_candidate_source_zone_count']}",
            f"wms_gap_filled_count={summary['wms_gap_filled_candidate_source_zone_count']}",
            f"dem_only_fallback_count={summary['dem_only_fallback_candidate_source_zone_count']}",
            f"mixed_boundary_count={summary['mixed_boundary_candidate_source_zone_count']}",
            f"source_sensitive_count={summary['source_sensitive_candidate_source_zone_count']}",
            f"dominant_source_zone={summary['candidate_source_zone_dominant_zone']}",
            f"assignment_radius_cells={summary['candidate_source_zone_assignment_radius_cells']}",
            "result_status=passed",
        )
    )


def find_representative_points(
    *,
    dem_path: str | Path,
    original_landcover_path: str | Path,
    gap_filled_landcover_path: str | Path,
    boundary_radius_cells: int,
    max_search_samples: int,
) -> tuple[Point, ...]:
    """Find ESA, WMS, fallback, and mixed representatives with bounded sampling."""

    if max_search_samples < 16:
        raise SourceZoneRasterError("max_search_samples must be at least 16.")
    rasterio = _load_rasterio()
    with rasterio.open(Path(dem_path)) as dem, rasterio.open(
        Path(original_landcover_path)
    ) as original, rasterio.open(Path(gap_filled_landcover_path)) as gap_filled:
        _require_matching_grid(dem, original, gap_filled)
        side = max(4, int(sqrt(max_search_samples)))
        row_step = max(1, ceil(dem.height / side))
        col_step = max(1, ceil(dem.width / side))
        sampled: dict[tuple[int, int], TerrainSourceZone] = {}
        representatives: dict[TerrainSourceZone, tuple[int, int]] = {}
        checked = 0
        for row in range(row_step // 2, dem.height, row_step):
            for col in range(col_step // 2, dem.width, col_step):
                if checked >= max_search_samples:
                    break
                checked += 1
                zone = _base_zone_at(dem, original, gap_filled, row, col)
                if zone is None:
                    continue
                sampled[(row, col)] = zone
                representatives.setdefault(zone, (row, col))
            if checked >= max_search_samples:
                break

        required = {
            TerrainSourceZone.ESA_DERIVED,
            TerrainSourceZone.WMS_GAP_FILLED,
            TerrainSourceZone.DEM_ONLY_FALLBACK,
        }
        if not required.issubset(representatives):
            raise SourceZoneRasterError("bounded search did not find all base source zones.")

        mixed_cell = _find_mixed_transition(
            sampled=sampled,
            dem=dem,
            original=original,
            gap_filled=gap_filled,
            boundary_radius_cells=boundary_radius_cells,
        )
        ordered_cells = (
            representatives[TerrainSourceZone.ESA_DERIVED],
            representatives[TerrainSourceZone.WMS_GAP_FILLED],
            representatives[TerrainSourceZone.DEM_ONLY_FALLBACK],
            mixed_cell,
        )
        return tuple(_cell_center(dem, row, col) for row, col in ordered_cells)


def _find_mixed_transition(
    *, sampled: dict[tuple[int, int], TerrainSourceZone], dem: Any, original: Any,
    gap_filled: Any, boundary_radius_cells: int,
) -> tuple[int, int]:
    lines: list[list[tuple[int, int, TerrainSourceZone]]] = []
    by_row: dict[int, list[tuple[int, int, TerrainSourceZone]]] = {}
    by_col: dict[int, list[tuple[int, int, TerrainSourceZone]]] = {}
    for (row, col), zone in sampled.items():
        by_row.setdefault(row, []).append((row, col, zone))
        by_col.setdefault(col, []).append((row, col, zone))
    lines.extend(sorted(values, key=lambda value: value[1]) for values in by_row.values())
    lines.extend(sorted(values, key=lambda value: value[0]) for values in by_col.values())
    for line in lines:
        for (row_a, col_a, zone_a), (row_b, col_b, zone_b) in zip(line, line[1:]):
            if zone_a is zone_b:
                continue
            steps = max(abs(row_b - row_a), abs(col_b - col_a))
            for step in range(steps + 1):
                row = round(row_a + (row_b - row_a) * step / max(1, steps))
                col = round(col_a + (col_b - col_a) * step / max(1, steps))
                if _has_mixed_neighborhood(
                    dem, original, gap_filled, row, col, boundary_radius_cells
                ):
                    return row, col
    raise SourceZoneRasterError("bounded search did not find a mixed boundary.")


def _has_mixed_neighborhood(
    dem: Any, original: Any, gap_filled: Any, row: int, col: int, radius: int
) -> bool:
    row_start, row_stop = max(0, row - radius), min(dem.height, row + radius + 1)
    col_start, col_stop = max(0, col - radius), min(dem.width, col + radius + 1)
    window = ((row_start, row_stop), (col_start, col_stop))
    dem_cells = dem.read(1, window=window, masked=True)
    original_cells = original.read(1, window=window)
    gap_cells = gap_filled.read(1, window=window)
    zones: set[TerrainSourceZone] = set()
    for local_row in range(row_stop - row_start):
        for local_col in range(col_stop - col_start):
            if bool(dem_cells.mask[local_row, local_col]):
                continue
            dem_value = float(dem_cells[local_row, local_col])
            if not isfinite(dem_value):
                continue
            zones.add(
                classify_source_zone_values(
                    dem_valid=True,
                    original_landcover_value=float(original_cells[local_row, local_col]),
                    gap_filled_landcover_value=float(gap_cells[local_row, local_col]),
                )
            )
            if len(zones) > 1:
                return True
    return False


def _base_zone_at(
    dem: Any, original: Any, gap_filled: Any, row: int, col: int
) -> TerrainSourceZone | None:
    dem_cell = dem.read(1, window=((row, row + 1), (col, col + 1)), masked=True)
    dem_valid = not bool(dem_cell.mask[0, 0]) and isfinite(float(dem_cell[0, 0]))
    if not dem_valid:
        return None
    original_value = float(original.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
    gap_value = float(gap_filled.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
    return classify_source_zone_values(
        dem_valid=True,
        original_landcover_value=original_value,
        gap_filled_landcover_value=gap_value,
    )


def _cell_center(raster: Any, row: int, col: int) -> Point:
    x_m, y_m = raster.xy(row, col, offset="center")
    return float(x_m), float(y_m)


def _require_matching_grid(dem: Any, original: Any, gap_filled: Any) -> None:
    for name, raster in (("original landcover", original), ("gap-filled landcover", gap_filled)):
        if (
            raster.crs != dem.crs
            or raster.transform != dem.transform
            or raster.bounds != dem.bounds
            or raster.width != dem.width
            or raster.height != dem.height
        ):
            raise SourceZoneRasterError(f"{name} grid must match DEM grid.")


def _load_rasterio() -> ModuleType:
    try:
        return importlib.import_module("rasterio")
    except ModuleNotFoundError as exc:
        raise SourceZoneRasterError("rasterio is required for local smoke use.") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dem-path", required=True)
    parser.add_argument("--original-landcover-path", required=True)
    parser.add_argument("--gap-filled-landcover-path", required=True)
    parser.add_argument("--boundary-radius-cells", type=int, default=3)
    parser.add_argument("--grid-spacing-m", type=float, default=90.0)
    parser.add_argument("--grid-radius-cells", type=int, default=2)
    parser.add_argument("--max-search-samples", type=int, default=5000)
    return parser


def _run_local_smoke(args: argparse.Namespace) -> CandidateSourceZoneAssignment:
    classifier = LocalSourceZoneRasterClassifier(
        args.dem_path, args.original_landcover_path, args.gap_filled_landcover_path
    )
    centers = find_representative_points(
        dem_path=args.dem_path,
        original_landcover_path=args.original_landcover_path,
        gap_filled_landcover_path=args.gap_filled_landcover_path,
        boundary_radius_cells=args.boundary_radius_cells,
        max_search_samples=args.max_search_samples,
    )
    cells = build_smoke_candidate_cells(
        centers, spacing_m=args.grid_spacing_m, radius_cells=args.grid_radius_cells
    )
    def provider(x_m: float, y_m: float) -> TerrainSourceZone:
        return classifier.sample_point(
            x_m, y_m, boundary_radius_cells=args.boundary_radius_cells
        ).output_source_zone
    return run_candidate_source_zone_smoke(
        cells, provider, boundary_radius_cells=args.boundary_radius_cells
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        assignment = _run_local_smoke(args)
    except (SourceZoneRasterError, CandidateSourceZoneError) as exc:
        print(f"candidate source-zone smoke error: {exc}", file=sys.stderr)
        return 1
    print(format_smoke_summary(assignment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
