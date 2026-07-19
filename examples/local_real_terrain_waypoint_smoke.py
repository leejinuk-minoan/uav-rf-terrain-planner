"""Run application-prepared waypoint reporting without creating files or opening a browser.

The caller supplies a factory returning a complete real-terrain route result and an
MGRS converter. This script invents no coordinates, reads no GIS paths, and prints
aggregate-only status rather than a report artifact.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable
from typing import Any

from uav_rf_terrain.real_terrain_waypoint_outputs import RealTerrainWaypointResult
from uav_rf_terrain.real_terrain_waypoint_reporting import (
    RealTerrainWaypointError,
    build_real_terrain_waypoint_reports,
)


def _load_factory(factory_path: str) -> Callable[[], tuple[Any, Any]]:
    module_name, separator, callable_name = factory_path.partition(":")
    if not separator or not module_name or not callable_name:
        raise ValueError("factory must use module:callable syntax.")
    factory = getattr(importlib.import_module(module_name), callable_name)
    if not callable(factory):
        raise ValueError("factory must be callable.")
    return factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local real-terrain waypoint reporting smoke.")
    parser.add_argument("--factory", required=True, help="Application factory as module:callable.")
    args = parser.parse_args(argv)
    try:
        route_result, projected_to_mgrs = _load_factory(args.factory)()
        result = build_real_terrain_waypoint_reports(
            route_result, projected_to_mgrs=projected_to_mgrs
        )
        if not isinstance(result, RealTerrainWaypointResult):
            raise ValueError("waypoint reporting did not return RealTerrainWaypointResult.")
    except (ImportError, AttributeError, TypeError, ValueError, RealTerrainWaypointError) as exc:
        print(f"waypoint smoke error: {exc}", file=sys.stderr)
        return 1
    print(f"route_count={result.summary.route_count}")
    print(f"route_modes={','.join(report.route_mode.value for report in result.route_reports)}")
    print(f"waypoints_per_route={','.join(str(len(report.waypoints)) for report in result.route_reports)}")
    print(f"spacing_m={result.config.spacing_m:.3f}")
    print(f"warnings={len(result.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
