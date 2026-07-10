"""Example use of the synthetic terrain data adapter scaffold."""

from __future__ import annotations

from uav_rf_terrain.synthetic import SCENARIO_FLAT_WITH_BUILDING, create_synthetic_terrain
from uav_rf_terrain.terrain_data import SyntheticTerrainDataAdapter


def main() -> None:
    terrain = create_synthetic_terrain(
        SCENARIO_FLAT_WITH_BUILDING,
        width_cells=7,
        height_cells=7,
        grid_size_m=25.0,
        base_dem_msl=50.0,
    )
    adapter = SyntheticTerrainDataAdapter(terrain)
    metadata = adapter.validate_metadata()

    center_x = terrain.width_cells // 2
    center_y = terrain.height_cells // 2
    print(f"Dataset: {metadata.dataset_name}")
    print(f"DEM MSL: {adapter.get_dem_msl(center_x, center_y):.1f} m")
    print(f"DSM MSL: {adapter.get_dsm_msl(center_x, center_y):.1f} m")
    print(f"Surface delta: {adapter.get_surface_delta_m(center_x, center_y):.1f} m")


if __name__ == "__main__":
    main()
