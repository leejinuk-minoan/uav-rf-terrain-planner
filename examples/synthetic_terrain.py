"""Example runner for pure Python synthetic DEM/DSM terrain generation.

This script prints in-memory synthetic grid summaries only. It does not read real
DEM/DSM files, write GeoTIFFs, render maps, or verify actual link quality.
"""

from __future__ import annotations

from uav_rf_terrain.synthetic import (
    SyntheticTerrainGrid,
    available_synthetic_scenarios,
    create_synthetic_terrain,
)


def matrix_min(matrix: tuple[tuple[float, ...], ...]) -> float:
    """Return the minimum value from a matrix."""

    return min(value for row in matrix for value in row)


def matrix_max(matrix: tuple[tuple[float, ...], ...]) -> float:
    """Return the maximum value from a matrix."""

    return max(value for row in matrix for value in row)


def max_surface_delta(terrain: SyntheticTerrainGrid) -> float:
    """Return the maximum DSM-DEM delta in meters."""

    return max(
        terrain.surface_delta_at(ix=ix, iy=iy)
        for iy in range(terrain.height_cells)
        for ix in range(terrain.width_cells)
    )


def describe_terrain(terrain: SyntheticTerrainGrid) -> str:
    """Return a compact terrain summary line."""

    return (
        f"{terrain.scenario_name}: "
        f"{terrain.width_cells}x{terrain.height_cells}, "
        f"grid={terrain.grid_size_m}m, "
        f"DEM[min={matrix_min(terrain.dem_msl):.1f}, max={matrix_max(terrain.dem_msl):.1f}], "
        f"DSM[min={matrix_min(terrain.dsm_msl):.1f}, max={matrix_max(terrain.dsm_msl):.1f}], "
        f"max_surface_delta={max_surface_delta(terrain):.1f}, "
        "actual_drone_operation=false, actual_link_measurement=false"
    )


def main() -> None:
    """Print available synthetic scenarios and generated terrain summaries."""

    print("available_synthetic_scenarios:")
    for scenario_name in available_synthetic_scenarios():
        print(f"- {scenario_name}")

    print("\nsynthetic terrain summaries:")
    for scenario_name in available_synthetic_scenarios():
        terrain = create_synthetic_terrain(scenario_name)
        print(describe_terrain(terrain))


if __name__ == "__main__":
    main()
