"""Run an application-prepared real-terrain route smoke without generating files.

The caller must provide a factory that returns an approved adapter, selected-site
record, source result, route config, and MGRS converter. This helper does not invent
coordinates, access GIS paths itself, open a browser, or write an artifact.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable
from typing import Any

from uav_rf_terrain.real_terrain_route_analysis import (
    RealTerrainRouteAnalysisError,
    analyze_selected_launch_site_routes,
)
from uav_rf_terrain.real_terrain_route_outputs import RealTerrainRouteResult


def _load_factory(factory_path: str) -> Callable[[], tuple[Any, Any, Any, Any, Any]]:
    module_name, separator, callable_name = factory_path.partition(":")
    if not separator or not module_name or not callable_name:
        raise ValueError("factory must use module:callable syntax.")
    factory = getattr(importlib.import_module(module_name), callable_name)
    if not callable(factory):
        raise ValueError("factory must be callable.")
    return factory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local real-terrain route smoke.")
    parser.add_argument("--factory", required=True, help="Application factory as module:callable.")
    args = parser.parse_args(argv)
    try:
        adapter, selected, source_result, config, projected_to_mgrs = _load_factory(args.factory)()
        result = analyze_selected_launch_site_routes(
            adapter,
            selected,
            source_result,
            config,
            projected_to_mgrs=projected_to_mgrs,
        )
        if not isinstance(result, RealTerrainRouteResult):
            raise ValueError("route analysis did not return RealTerrainRouteResult.")
    except (ImportError, AttributeError, TypeError, ValueError, RealTerrainRouteAnalysisError) as exc:
        print(f"route smoke error: {exc}", file=sys.stderr)
        return 1
    print(f"route_count={len(result.route_candidates)}")
    print(f"route_modes={','.join(route.mode.value for route in result.route_candidates)}")
    print(
        "route_distances_3d_m="
        + ",".join(f"{route.total_distance_3d_m:.3f}" for route in result.route_candidates)
    )
    print(f"warnings={len(result.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
