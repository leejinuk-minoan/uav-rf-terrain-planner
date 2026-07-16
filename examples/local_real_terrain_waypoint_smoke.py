"""Aggregate-only local smoke helper for a caller-supplied route result.

This example deliberately accepts no terrain path or coordinate CLI input. A local
caller supplies an already validated `RealTerrainRouteResult` factory and a MGRS
converter; no generated report artifact, browser, or operational coordinate is used.
"""

from __future__ import annotations

from collections.abc import Callable

from uav_rf_terrain.coordinate_conversion import ProjectedToMgrsConverter
from uav_rf_terrain.real_terrain_route_outputs import RealTerrainRouteResult
from uav_rf_terrain.real_terrain_waypoint_outputs import RealTerrainWaypointConfig
from uav_rf_terrain.real_terrain_waypoint_reporting import build_real_terrain_waypoint_reports


def run_smoke(
    route_result_factory: Callable[[], RealTerrainRouteResult],
    *,
    projected_to_mgrs: ProjectedToMgrsConverter,
    config: RealTerrainWaypointConfig = RealTerrainWaypointConfig(),
) -> dict[str, object]:
    """Build a report and return aggregate-only counts for a local caller."""

    result = build_real_terrain_waypoint_reports(
        route_result_factory(), config, projected_to_mgrs=projected_to_mgrs
    )
    return {
        "route_count": result.summary.route_count,
        "waypoint_count": result.summary.waypoint_count,
        "route_modes": tuple(report.route_mode.value for report in result.route_reports),
        "waypoints_per_route": tuple(len(report.waypoints) for report in result.route_reports),
        "spacing_m": result.config.spacing_m,
        "warnings": result.warnings,
    }


if __name__ == "__main__":
    print("Import run_smoke with a local route-result factory; no browser or file output is created.")
