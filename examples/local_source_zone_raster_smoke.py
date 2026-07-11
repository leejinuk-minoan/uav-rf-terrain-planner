"""Run a local source-zone classifier smoke check for one projected point."""

from __future__ import annotations

import argparse
import sys

from uav_rf_terrain.source_zone_raster import LocalSourceZoneRasterClassifier, SourceZoneRasterError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dem-path", required=True)
    parser.add_argument("--original-landcover-path", required=True)
    parser.add_argument("--gap-filled-landcover-path", required=True)
    parser.add_argument("--point-x", type=float, required=True)
    parser.add_argument("--point-y", type=float, required=True)
    parser.add_argument("--boundary-radius-cells", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    classifier = LocalSourceZoneRasterClassifier(
        dem_path=args.dem_path,
        original_landcover_path=args.original_landcover_path,
        gap_filled_landcover_path=args.gap_filled_landcover_path,
    )
    try:
        sample = classifier.sample_point(
            args.point_x, args.point_y, boundary_radius_cells=args.boundary_radius_cells
        )
    except SourceZoneRasterError as exc:
        print(f"source-zone error: {exc}", file=sys.stderr)
        return 1
    print(f"sample_x_m={sample.x_m}")
    print(f"sample_y_m={sample.y_m}")
    print(f"row={sample.row}")
    print(f"col={sample.col}")
    print(f"base_source_zone={sample.base_source_zone.value}")
    print(f"output_source_zone={sample.output_source_zone.value}")
    print(f"source_sensitive={str(sample.source_sensitive).lower()}")
    print(f"reason={sample.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
