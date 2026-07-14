"""Run a bounded local real-terrain candidate-analysis smoke without file output."""

from __future__ import annotations

import argparse
import sys

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.geotiff_terrain_data import LocalGeoTiffTerrainDataAdapter
from uav_rf_terrain.real_terrain_candidate_analysis import (
    RealTerrainLaunchAreaAnalysisError,
    RealTerrainLaunchAreaConfig,
    analyze_real_terrain_launch_area,
)
from uav_rf_terrain.terrain_data import TerrainDataError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded local real-terrain analysis smoke.")
    parser.add_argument("--dem-path", required=True)
    parser.add_argument("--dsm-path", required=True)
    parser.add_argument("--target-x", type=float, required=True)
    parser.add_argument("--target-y", type=float, required=True)
    parser.add_argument("--radius-m", type=float, default=900.0)
    parser.add_argument("--spacing-m", type=float, default=180.0)
    parser.add_argument("--profile-spacing-m", type=float, default=90.0)
    parser.add_argument("--allowed-agl-m", type=float, default=100.0)
    parser.add_argument("--frequency-hz", type=float, default=2_400_000_000.0)
    args = parser.parse_args(argv)
    if args.radius_m > 900.0 or args.spacing_m < 180.0 or args.profile_spacing_m < 90.0:
        print("bounded smoke limits exceeded", file=sys.stderr)
        return 1
    try:
        result = analyze_real_terrain_launch_area(
            LocalGeoTiffTerrainDataAdapter(args.dem_path, args.dsm_path),
            RealTerrainLaunchAreaConfig(
                scenario_name="local-real-terrain-smoke",
                target_point=LocalPoint(args.target_x, args.target_y),
                operating_radius_m=args.radius_m,
                candidate_spacing_m=args.spacing_m,
                allowed_agl_m=args.allowed_agl_m,
                frequency_hz=args.frequency_hz,
                profile_sample_spacing_m=args.profile_spacing_m,
                include_center=False,
                include_out_of_radius=True,
            ),
        )
    except (RealTerrainLaunchAreaAnalysisError, TerrainDataError) as exc:
        print(f"analysis error: {exc}", file=sys.stderr)
        return 1
    print(f"candidate_count={result.summary.total_candidate_count}")
    print(f"state_counts={result.summary.state_counts}")
    print(f"color_counts={result.summary.color_counts}")
    print(f"source_zone_state_counts={result.summary.source_zone_state_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
