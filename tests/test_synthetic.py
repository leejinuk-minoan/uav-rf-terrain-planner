import pytest

from uav_rf_terrain.synthetic import (
    SCENARIO_FLAT,
    SCENARIO_FLAT_WITH_BUILDING,
    SCENARIO_FLAT_WITH_TREES,
    SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION,
    SCENARIO_OBSTACLE_POSITION_VARIATION,
    SCENARIO_SINGLE_RIDGE,
    SyntheticTerrainError,
    SyntheticTerrainGrid,
    available_synthetic_scenarios,
    create_synthetic_terrain,
)

EXPECTED_SCENARIOS = {
    "flat",
    "single_ridge",
    "flat_with_building",
    "flat_with_trees",
    "obstacle_position_variation",
    "operating_radius_boundary",
    "fixed_agl_case",
    "fresnel_radius_position_variation",
}


def _all_values(matrix: tuple[tuple[float, ...], ...]) -> list[float]:
    return [value for row in matrix for value in row]


def _all_surface_deltas(terrain: SyntheticTerrainGrid) -> list[float]:
    return [
        terrain.surface_delta_at(ix=ix, iy=iy)
        for iy in range(terrain.height_cells)
        for ix in range(terrain.width_cells)
    ]


def test_available_synthetic_scenarios_contains_all_eight() -> None:
    assert set(available_synthetic_scenarios()) == EXPECTED_SCENARIOS
    assert len(available_synthetic_scenarios()) == 8


@pytest.mark.parametrize("scenario_name", sorted(EXPECTED_SCENARIOS))
def test_each_scenario_can_be_created(scenario_name: str) -> None:
    terrain = create_synthetic_terrain(scenario_name)

    assert terrain.scenario_name == scenario_name
    assert terrain.width_cells == 51
    assert terrain.height_cells == 51
    assert terrain.grid_size_m == 100.0


@pytest.mark.parametrize("scenario_name", sorted(EXPECTED_SCENARIOS))
def test_dem_and_dsm_shapes_match(scenario_name: str) -> None:
    terrain = create_synthetic_terrain(scenario_name, width_cells=9, height_cells=7)

    assert len(terrain.dem_msl) == len(terrain.dsm_msl) == 7
    assert len(terrain.dem_msl[0]) == len(terrain.dsm_msl[0]) == 9


@pytest.mark.parametrize("scenario_name", sorted(EXPECTED_SCENARIOS))
def test_dsm_is_greater_than_or_equal_to_dem(scenario_name: str) -> None:
    terrain = create_synthetic_terrain(scenario_name)

    for iy in range(terrain.height_cells):
        for ix in range(terrain.width_cells):
            assert terrain.dsm_at(ix=ix, iy=iy) >= terrain.dem_at(ix=ix, iy=iy)


def test_flat_scenario_has_identical_dem_and_dsm() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)

    assert terrain.dem_msl == terrain.dsm_msl
    assert max(_all_surface_deltas(terrain)) == 0.0


def test_single_ridge_scenario_has_dem_elevation_change() -> None:
    base_dem_msl = 50.0
    terrain = create_synthetic_terrain(SCENARIO_SINGLE_RIDGE, base_dem_msl=base_dem_msl)

    assert max(_all_values(terrain.dem_msl)) > base_dem_msl
    assert terrain.dem_msl == terrain.dsm_msl


def test_flat_with_building_has_flat_dem_and_dsm_obstacle() -> None:
    base_dem_msl = 50.0
    terrain = create_synthetic_terrain(SCENARIO_FLAT_WITH_BUILDING, base_dem_msl=base_dem_msl)

    assert set(_all_values(terrain.dem_msl)) == {base_dem_msl}
    assert max(_all_surface_deltas(terrain)) > 0.0


def test_flat_with_trees_has_surface_delta() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT_WITH_TREES)

    assert max(_all_surface_deltas(terrain)) > 0.0
    assert terrain.dem_msl != terrain.dsm_msl


def test_obstacle_position_variation_has_equal_height_obstacles_at_multiple_positions() -> None:
    terrain = create_synthetic_terrain(SCENARIO_OBSTACLE_POSITION_VARIATION)
    deltas = _all_surface_deltas(terrain)

    assert max(deltas) == 25.0
    assert deltas.count(25.0) >= 3


def test_fresnel_radius_position_variation_has_start_mid_end_obstacles() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION)
    y = terrain.height_cells // 2
    x_values = (terrain.width_cells // 8, terrain.width_cells // 2, (terrain.width_cells * 7) // 8)

    assert all(terrain.surface_delta_at(ix=x, iy=y) == 22.0 for x in x_values)


def test_invalid_scenario_name_raises() -> None:
    with pytest.raises(SyntheticTerrainError, match="Unknown synthetic scenario"):
        create_synthetic_terrain("unknown")


@pytest.mark.parametrize(
    ("width_cells", "height_cells", "grid_size_m"),
    [
        (0, 10, 100.0),
        (10, 0, 100.0),
        (10, 10, 0.0),
    ],
)
def test_invalid_grid_size_values_raise(
    width_cells: int,
    height_cells: int,
    grid_size_m: float,
) -> None:
    with pytest.raises(SyntheticTerrainError):
        create_synthetic_terrain(
            SCENARIO_FLAT,
            width_cells=width_cells,
            height_cells=height_cells,
            grid_size_m=grid_size_m,
        )


def test_synthetic_terrain_grid_rejects_shape_mismatch() -> None:
    with pytest.raises(SyntheticTerrainError, match="same shape"):
        SyntheticTerrainGrid(
            scenario_name="invalid",
            grid_size_m=100.0,
            dem_msl=((1.0,),),
            dsm_msl=((1.0, 2.0),),
        )


def test_synthetic_terrain_grid_rejects_dsm_below_dem() -> None:
    with pytest.raises(SyntheticTerrainError, match="DSM"):
        SyntheticTerrainGrid(
            scenario_name="invalid",
            grid_size_m=100.0,
            dem_msl=((2.0,),),
            dsm_msl=((1.0,),),
        )
