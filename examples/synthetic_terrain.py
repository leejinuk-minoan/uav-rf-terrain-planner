"""Synthetic terrain metadata scaffold for Task 001.

Task 001 keeps this file at metadata-placeholder level only. The concrete synthetic
DEM/DSM generator is reserved for Task 003.
"""

from __future__ import annotations

from uav_rf_terrain.schemas import SyntheticTerrainMetadata


DEFAULT_SYNTHETIC_SCENARIOS: tuple[SyntheticTerrainMetadata, ...] = (
    SyntheticTerrainMetadata(
        scenario_name="flat",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="single_ridge",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="flat_with_building",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="flat_with_trees",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="obstacle_position_variation",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="operating_radius_boundary",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="fixed_agl_case",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
    SyntheticTerrainMetadata(
        scenario_name="fresnel_radius_position_variation",
        grid_size_m=100.0,
        width_cells=51,
        height_cells=51,
    ),
)


def list_synthetic_scenarios() -> tuple[SyntheticTerrainMetadata, ...]:
    """Return placeholder synthetic scenario metadata.

    Returns:
        Tuple of synthetic scenario metadata records. These records use no real DEM
        and no real DSM data.
    """

    return DEFAULT_SYNTHETIC_SCENARIOS


if __name__ == "__main__":
    for scenario in list_synthetic_scenarios():
        print(f"{scenario.scenario_name}: {scenario.width_cells}x{scenario.height_cells}, grid={scenario.grid_size_m}m")
