"""Align ESA WorldCover to DEM tiles and build a temporary DSM proxy.

The output is suitable for research, education, and simulation prototyping:

    temporary_dsm_msl = dem_msl + class_height_proxy

WorldCover contains land-cover classes, not measured building or vegetation
heights. The surface deltas below are heuristic assumptions and must not be
treated as an authoritative DSM.

NumPy and rasterio are local preprocessing script runtime dependencies, not
package dependencies of uav-rf-terrain-planner.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import Resampling, reproject, transform_bounds


ESA_HEIGHTS_M = {
    0: 0.0,    # NoData
    10: 14.0,  # Tree cover
    20: 2.0,   # Shrubland
    30: 1.0,   # Grassland
    40: 0.5,   # Cropland
    50: 8.0,   # Built-up
    60: 0.0,   # Bare/sparse vegetation
    70: 0.0,   # Snow and ice
    80: 0.0,   # Permanent water bodies
    90: 0.5,   # Herbaceous wetland
    95: 4.0,   # Mangroves
    100: 0.2,  # Moss and lichen
}


def find_dem_tiles(dem_root: Path) -> list[Path]:
    return sorted(dem_root.rglob("*.img"), key=lambda path: path.stem)


def find_worldcover_sources(worldcover_root: Path) -> list[Path]:
    return sorted(worldcover_root.glob("ESA_WorldCover_*_Map.tif"))


def overlaps(left: tuple[float, float, float, float], right: rasterio.coords.BoundingBox) -> bool:
    return not (
        left[2] <= right.left
        or left[0] >= right.right
        or left[3] <= right.bottom
        or left[1] >= right.top
    )


def align_worldcover(dem_src: rasterio.io.DatasetReader, sources: list[Path]) -> np.ndarray:
    classes = np.zeros((dem_src.height, dem_src.width), dtype=np.uint8)
    # Five source DEM sheets use the same Unified CS parameters but omit the
    # authority code in their WKT. Normalize them to the project CRS.
    dem_crs = dem_src.crs if dem_src.crs and dem_src.crs.to_epsg() else rasterio.crs.CRS.from_epsg(5179)
    dem_bounds_wgs84 = transform_bounds(
        dem_crs,
        "EPSG:4326",
        *dem_src.bounds,
        densify_pts=21,
    )

    matched = False
    for source_path in sources:
        with rasterio.open(source_path) as source:
            if not overlaps(dem_bounds_wgs84, source.bounds):
                continue
            matched = True
            reproject(
                source=rasterio.band(source, 1),
                destination=classes,
                src_transform=source.transform,
                src_crs=source.crs,
                src_nodata=source.nodata,
                dst_transform=dem_src.transform,
                dst_crs=dem_crs,
                dst_nodata=0,
                resampling=Resampling.nearest,
            )

    if not matched:
        raise RuntimeError(f"No WorldCover source overlaps DEM tile {dem_src.name}")
    return classes


def class_to_surface_delta(classes: np.ndarray) -> np.ndarray:
    surface = np.zeros(classes.shape, dtype=np.float32)
    for class_code, height_m in ESA_HEIGHTS_M.items():
        surface[classes == class_code] = height_m
    return surface


def write_tile(
    dem_path: Path,
    sources: list[Path],
    output_dir: Path,
) -> tuple[Path, Path, Path, dict[int, int]]:
    tile_id = dem_path.stem
    class_path = output_dir / "landcover_tiles" / f"{tile_id}_esa_worldcover_2021.tif"
    surface_path = output_dir / "surface_delta_tiles" / f"{tile_id}_surface_delta_proxy_m.tif"
    dsm_path = output_dir / "dsm_tiles" / f"{tile_id}_temporary_dsm_proxy_msl.tif"
    for path in (class_path, surface_path, dsm_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(dem_path) as dem_src:
        classes = align_worldcover(dem_src, sources)
        surface = class_to_surface_delta(classes)
        dem = dem_src.read(1, masked=True).astype(np.float32)
        dsm = (dem + surface).filled(-9999.0).astype(np.float32)

        class_profile = dem_src.profile.copy()
        class_profile.update(
            driver="GTiff",
            crs="EPSG:5179",
            dtype="uint8",
            nodata=0,
            compress="deflate",
            tiled=True,
        )
        float_profile = dem_src.profile.copy()
        float_profile.update(
            driver="GTiff",
            crs="EPSG:5179",
            dtype="float32",
            nodata=-9999.0,
            compress="deflate",
            tiled=True,
        )

        with rasterio.open(class_path, "w", **class_profile) as dst:
            dst.write(classes, 1)
            dst.update_tags(
                source="ESA WorldCover 10m 2021 v200",
                resampling="nearest",
                aligned_to=f"DEM tile {tile_id}",
            )
        with rasterio.open(surface_path, "w", **float_profile) as dst:
            dst.write(surface, 1)
            dst.update_tags(model="heuristic land-cover class height proxy")
        with rasterio.open(dsm_path, "w", **float_profile) as dst:
            dst.write(dsm, 1)
            dst.update_tags(
                model="temporary_dsm_msl = dem_msl + heuristic_surface_delta",
                limitation="not measured building or vegetation height",
            )

    unique, counts = np.unique(classes, return_counts=True)
    return class_path, surface_path, dsm_path, dict(zip(unique.tolist(), counts.tolist()))


def write_mosaic(tile_paths: list[Path], output_path: Path, dtype: str, nodata: float) -> None:
    datasets = [rasterio.open(path) for path in tile_paths]
    try:
        mosaic, transform = merge(datasets, nodata=nodata)
        profile = datasets[0].profile.copy()
        profile.update(
            driver="GTiff",
            width=mosaic.shape[2],
            height=mosaic.shape[1],
            transform=transform,
            dtype=dtype,
            nodata=nodata,
            compress="deflate",
            tiled=True,
            BIGTIFF="IF_SAFER",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(mosaic.astype(dtype, copy=False))
    finally:
        for dataset in datasets:
            dataset.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worldcover-root", type=Path, required=True)
    parser.add_argument(
        "--dem-root", type=Path, default=Path("METADATA_MAP/DEM_EXTRACTED_LATEST")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("METADATA_MAP/DSM_PROXY_FROM_ESA_WORLDCOVER")
    )
    parser.add_argument("--tile", default="")
    parser.add_argument("--skip-mosaic", action="store_true")
    parser.add_argument("--mosaic-only", action="store_true")
    args = parser.parse_args()

    dem_tiles = find_dem_tiles(args.dem_root)
    if args.tile:
        dem_tiles = [path for path in dem_tiles if path.stem == args.tile]
    sources = find_worldcover_sources(args.worldcover_root)
    if not dem_tiles:
        raise SystemExit("No DEM tiles matched.")
    if not sources:
        raise SystemExit("No ESA WorldCover source rasters matched.")

    manifest_path = args.output_dir / "processing_manifest.csv"
    if args.mosaic_only:
        class_paths = sorted((args.output_dir / "landcover_tiles").glob("*.tif"))
        surface_paths = sorted((args.output_dir / "surface_delta_tiles").glob("*.tif"))
        dsm_paths = sorted((args.output_dir / "dsm_tiles").glob("*.tif"))
        if not (len(class_paths) == len(surface_paths) == len(dsm_paths) == len(dem_tiles)):
            raise SystemExit("Existing output tile counts do not match the DEM tile count.")
        rows = []
        for class_path in class_paths:
            with rasterio.open(class_path) as source:
                unique, counts = np.unique(source.read(1), return_counts=True)
            rows.append(
                {
                    "tile_id": class_path.name.split("_", 1)[0],
                    "class_counts": repr(dict(zip(unique.tolist(), counts.tolist()))),
                }
            )
        with manifest_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=["tile_id", "class_counts"])
            writer.writeheader()
            writer.writerows(rows)
    else:
        rows: list[dict[str, object]] = []
        class_paths = []
        surface_paths = []
        dsm_paths = []
        for index, dem_path in enumerate(dem_tiles, start=1):
            class_path, surface_path, dsm_path, counts = write_tile(
                dem_path, sources, args.output_dir
            )
            class_paths.append(class_path)
            surface_paths.append(surface_path)
            dsm_paths.append(dsm_path)
            rows.append({"tile_id": dem_path.stem, "class_counts": repr(counts)})
            print(f"[{index}/{len(dem_tiles)}] {dem_path.stem} class_counts={counts}")

        with manifest_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=["tile_id", "class_counts"])
            writer.writeheader()
            writer.writerows(rows)

    if not args.skip_mosaic and not args.tile:
        write_mosaic(
            class_paths,
            args.output_dir / "south_korea_landcover_90m_epsg5179.tif",
            "uint8",
            0,
        )
        write_mosaic(
            surface_paths,
            args.output_dir / "south_korea_surface_delta_proxy_90m_epsg5179.tif",
            "float32",
            -9999.0,
        )
        write_mosaic(
            dsm_paths,
            args.output_dir / "south_korea_temporary_dsm_proxy_90m_epsg5179.tif",
            "float32",
            -9999.0,
        )

    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
