"""Run an optional local GeoTIFF adapter and terrain-profile smoke test."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.geotiff_terrain_data import LocalGeoTiffTerrainDataAdapter
from uav_rf_terrain.profile import TerrainProfileError, extract_terrain_profile_from_adapter
from uav_rf_terrain.terrain_data import TerrainDataError


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dem-path", type=Path, required=True)
    parser.add_argument("--dsm-path", type=Path, required=True)
    parser.add_argument("--start-x", type=float, required=True)
    parser.add_argument("--start-y", type=float, required=True)
    parser.add_argument("--end-x", type=float, required=True)
    parser.add_argument("--end-y", type=float, required=True)
    parser.add_argument("--sample-spacing-m", type=float)
    args = parser.parse_args(argv)

    try:
        adapter = LocalGeoTiffTerrainDataAdapter(args.dem_path, args.dsm_path)
        metadata = adapter.validate_metadata()
        profile = extract_terrain_profile_from_adapter(
            adapter,
            LocalPoint(args.start_x, args.start_y),
            LocalPoint(args.end_x, args.end_y),
            sample_spacing_m=args.sample_spacing_m,
        )
    except (TerrainDataError, TerrainProfileError) as exc:
        print(f"Local GeoTIFF smoke test failed: {exc}", file=sys.stderr)
        return 1

    print(f"dataset={metadata.dataset_name}")
    print(f"crs={metadata.dem.crs}")
    print(f"resolution_m={metadata.dem.resolution_m}")
    print(f"size={metadata.dem.width}x{metadata.dem.height}")
    print(f"bounds={metadata.dem.bounds}")
    print(f"sample_count={profile.sample_count}")
    print(f"max_dem_msl={profile.max_dem_msl}")
    print(f"max_dsm_msl={profile.max_dsm_msl}")
    print(f"max_surface_delta_m={profile.max_surface_delta_m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
