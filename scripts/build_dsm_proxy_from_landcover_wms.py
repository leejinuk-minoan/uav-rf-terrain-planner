"""Build temporary DSM proxy rasters from DEM and land-cover WMS RGB tiles.

The generated DSM is a terrain/surface-obstacle proxy:

    temporary_dsm_msl = dem_msl + landcover_class_height_proxy

It is not an authoritative DSM and must not be described as validated link
quality or actual obstacle height.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio


DEFAULT_HEIGHTS_M = {
    0: 0.0,   # unknown/background
    1: 8.0,   # urban/built-up
    2: 0.5,   # agriculture
    3: 14.0,  # forest
    4: 1.0,   # grass
    5: 0.5,   # wetland
    6: 0.0,   # bare land
    7: 0.0,   # water
}


def classify_rgb(rgb: np.ndarray) -> np.ndarray:
    """Classify rendered WMS RGB pixels into coarse land-cover classes.

    Classes:
        0 unknown/background
        1 urban/built-up
        2 agriculture
        3 forest
        4 grass
        5 wetland
        6 bare land
        7 water

    The WMS layer is a styled map image, not source class values. This heuristic
    groups colors into broad DSM proxy classes only.
    """
    r = rgb[0].astype(np.int16)
    g = rgb[1].astype(np.int16)
    b = rgb[2].astype(np.int16)
    out = np.zeros(r.shape, dtype=np.uint8)

    # Water: saturated blue/cyan.
    out[(b > 130) & (r < 120) & (g < 170)] = 7

    # Forest: dark/medium greens.
    out[(g > 55) & (g >= r + 15) & (g >= b + 10) & (r < 150)] = 3

    # Grass/managed vegetation: bright greens.
    out[(g > 130) & (r < 130) & (b < 130)] = 4

    # Agriculture: yellow/cream/orange fields.
    out[(r > 150) & (g > 130) & (b < 150)] = 2

    # Built-up: red/orange/white-gray urban map colors.
    out[(r > 170) & (g < 140) & (b < 140)] = 1
    out[(r > 185) & (g > 170) & (b > 150) & (np.abs(r - g) < 45)] = 1

    # Wetland: purple/magenta-ish.
    out[(r > 100) & (b > 120) & (g < 130)] = 5

    # Bare land: tan/gray, not already classified.
    bare = (out == 0) & (r > 120) & (g > 100) & (b > 80) & (np.abs(r - g) < 70)
    out[bare] = 6
    return out


def class_to_surface_delta(class_arr: np.ndarray) -> np.ndarray:
    surface = np.zeros(class_arr.shape, dtype=np.float32)
    for class_id, height_m in DEFAULT_HEIGHTS_M.items():
        surface[class_arr == class_id] = height_m
    return surface


def find_dem_for_tile(dem_root: Path, tile_id: str) -> Path:
    matches = sorted(dem_root.rglob(f"{tile_id}.img"))
    if not matches:
        raise FileNotFoundError(f"No DEM tile found for {tile_id} under {dem_root}")
    return matches[0]


def build_tile(
    *,
    rgb_path: Path,
    dem_path: Path,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    tile_id = rgb_path.name.split("_", 1)[0]
    output_dir.mkdir(parents=True, exist_ok=True)
    class_path = output_dir / f"{tile_id}_landcover_proxy_class.tif"
    surface_path = output_dir / f"{tile_id}_surface_delta_proxy_m.tif"
    dsm_path = output_dir / f"{tile_id}_temporary_dsm_proxy_msl.tif"

    with rasterio.open(rgb_path) as rgb_src, rasterio.open(dem_path) as dem_src:
        rgb = rgb_src.read([1, 2, 3])
        dem = dem_src.read(1, masked=True).astype("float32")
        classes = classify_rgb(rgb)
        surface = class_to_surface_delta(classes)
        dsm = (dem + surface).filled(-9999.0).astype("float32")

        class_profile = dem_src.profile.copy()
        class_profile.update(
            driver="GTiff",
            count=1,
            dtype="uint8",
            nodata=0,
            compress="lzw",
            tiled=True,
        )
        float_profile = dem_src.profile.copy()
        float_profile.update(
            driver="GTiff",
            count=1,
            dtype="float32",
            nodata=-9999.0,
            compress="lzw",
            tiled=True,
        )

        with rasterio.open(class_path, "w", **class_profile) as dst:
            dst.write(classes, 1)
        with rasterio.open(surface_path, "w", **float_profile) as dst:
            dst.write(surface, 1)
        with rasterio.open(dsm_path, "w", **float_profile) as dst:
            dst.write(dsm, 1)

    unique, counts = np.unique(classes, return_counts=True)
    print(f"{tile_id} class_counts={dict(zip(unique.tolist(), counts.tolist()))}")
    return class_path, surface_path, dsm_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--landcover-dir", type=Path, default=Path("METADATA_MAP/LANDCOVER_WMS"))
    parser.add_argument("--dem-root", type=Path, default=Path("METADATA_MAP/DEM_EXTRACTED_LATEST"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("METADATA_MAP/DSM_PROXY_FROM_WMS"),
    )
    parser.add_argument("--tile", default="")
    args = parser.parse_args()

    rgb_tiles = sorted(args.landcover_dir.glob("*_rgb.tif"))
    if args.tile:
        rgb_tiles = [path for path in rgb_tiles if path.name.startswith(f"{args.tile}_")]
    if not rgb_tiles:
        raise SystemExit("No land-cover WMS RGB tiles matched.")

    for rgb_path in rgb_tiles:
        tile_id = rgb_path.name.split("_", 1)[0]
        dem_path = find_dem_for_tile(args.dem_root, tile_id)
        class_path, surface_path, dsm_path = build_tile(
            rgb_path=rgb_path,
            dem_path=dem_path,
            output_dir=args.output_dir,
        )
        print(f"{tile_id} -> {class_path}, {surface_path}, {dsm_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
