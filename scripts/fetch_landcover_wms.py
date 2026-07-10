"""Fetch land-cover WMS tiles aligned to local DEM tiles.

This script uses the public land-cover WMS as a rendered map source and writes
georeferenced RGB GeoTIFFs aligned to existing DEM tiles. It does not download
source GIS vectors or claim authoritative land-cover class values.
"""

from __future__ import annotations

import argparse
import time
import urllib.parse
import urllib.request
from pathlib import Path

import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import transform_bounds


DEFAULT_WMS_URL = "https://api.mcee.go.kr/geoserver/wms"
DEFAULT_LAYER = "EGIS:lv3_2025y"


def iter_dem_tiles(dem_root: Path) -> list[Path]:
    return sorted(dem_root.rglob("*.img"))


def build_getmap_url(
    *,
    service_url: str,
    layer: str,
    bbox_3857: tuple[float, float, float, float],
    width: int,
    height: int,
    image_format: str,
) -> str:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "SRS": "EPSG:3857",
        "BBOX": ",".join(f"{v:.6f}" for v in bbox_3857),
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FORMAT": image_format,
        "TRANSPARENT": "false",
        "TILED": "false",
    }
    return service_url + "?" + urllib.parse.urlencode(params)


def fetch_bytes(url: str, timeout_s: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "uav-rf-terrain-planner/0.1"})
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read()
    if b"ServiceException" in payload[:500] or b"ExceptionReport" in payload[:500]:
        raise RuntimeError(payload[:1000].decode("utf-8", errors="replace"))
    if "image" not in content_type.lower() and not payload.startswith(b"\x89PNG"):
        raise RuntimeError(f"Unexpected response content type: {content_type}")
    return payload


def write_aligned_rgb(payload: bytes, dem_path: Path, output_path: Path) -> None:
    with rasterio.open(dem_path) as dem_src:
        profile = dem_src.profile.copy()
        profile.update(
            driver="GTiff",
            count=3,
            dtype="uint8",
            nodata=None,
            compress="lzw",
            tiled=True,
            photometric="RGB",
        )
        with MemoryFile(payload) as memfile:
            with memfile.open() as image_src:
                rgb = image_src.read([1, 2, 3])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(rgb)


def fetch_tile(
    *,
    dem_path: Path,
    output_dir: Path,
    service_url: str,
    layer: str,
    image_format: str,
    timeout_s: int,
) -> Path:
    tile_id = dem_path.stem
    output_path = output_dir / f"{tile_id}_{layer.replace(':', '_')}_rgb.tif"
    with rasterio.open(dem_path) as src:
        bounds = transform_bounds(src.crs, "EPSG:3857", *src.bounds, densify_pts=21)
        url = build_getmap_url(
            service_url=service_url,
            layer=layer,
            bbox_3857=bounds,
            width=src.width,
            height=src.height,
            image_format=image_format,
        )
    payload = fetch_bytes(url, timeout_s)
    write_aligned_rgb(payload, dem_path, output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dem-root",
        type=Path,
        default=Path("METADATA_MAP/DEM_EXTRACTED_LATEST"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("METADATA_MAP/LANDCOVER_WMS"),
    )
    parser.add_argument("--service-url", default=DEFAULT_WMS_URL)
    parser.add_argument("--layer", default=DEFAULT_LAYER)
    parser.add_argument("--format", default="image/png")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--tile", default="")
    parser.add_argument("--sleep-s", type=float, default=0.2)
    parser.add_argument("--timeout-s", type=int, default=60)
    args = parser.parse_args()

    dem_tiles = iter_dem_tiles(args.dem_root)
    if args.tile:
        dem_tiles = [path for path in dem_tiles if path.stem == args.tile]
    if args.limit > 0:
        dem_tiles = dem_tiles[: args.limit]
    if not dem_tiles:
        raise SystemExit("No DEM tiles matched.")

    for index, dem_path in enumerate(dem_tiles, start=1):
        output_path = fetch_tile(
            dem_path=dem_path,
            output_dir=args.output_dir,
            service_url=args.service_url,
            layer=args.layer,
            image_format=args.format,
            timeout_s=args.timeout_s,
        )
        print(f"[{index}/{len(dem_tiles)}] {dem_path.stem} -> {output_path}")
        if args.sleep_s > 0:
            time.sleep(args.sleep_s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
