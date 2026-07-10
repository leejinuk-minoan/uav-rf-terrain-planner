"""Run adapter-based terrain profile extraction with synthetic in-memory data."""

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.profile import extract_terrain_profile_from_adapter
from uav_rf_terrain.synthetic import SCENARIO_FLAT_WITH_BUILDING, create_synthetic_terrain
from uav_rf_terrain.terrain_data import SyntheticTerrainDataAdapter


def main() -> None:
    terrain = create_synthetic_terrain(
        SCENARIO_FLAT_WITH_BUILDING,
        width_cells=7,
        height_cells=5,
        grid_size_m=10.0,
        base_dem_msl=50.0,
    )
    profile = extract_terrain_profile_from_adapter(
        SyntheticTerrainDataAdapter(terrain),
        LocalPoint(0.0, 20.0),
        LocalPoint(60.0, 20.0),
    )
    first, last = profile.samples[0], profile.samples[-1]
    print(f"sample_count={profile.sample_count}")
    print(f"max_dem_msl={profile.max_dem_msl}")
    print(f"max_dsm_msl={profile.max_dsm_msl}")
    print(f"max_surface_delta_m={profile.max_surface_delta_m}")
    print(f"first=({first.ix}, {first.iy}, {first.dem_msl}, {first.dsm_msl})")
    print(f"last=({last.ix}, {last.iy}, {last.dem_msl}, {last.dsm_msl})")


if __name__ == "__main__":
    main()
