import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.profile import (
    TerrainProfileError,
    extract_terrain_profile,
    grid_index_to_local_point,
    local_point_to_grid_index,
)
from uav_rf_terrain.synthetic import (
    SCENARIO_FLAT,
    SCENARIO_FLAT_WITH_BUILDING,
    SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION,
    SCENARIO_OBSTACLE_POSITION_VARIATION,
    SCENARIO_SINGLE_RIDGE,
    create_synthetic_terrain,
)


def _horizontal_midline_points() -> tuple[LocalPoint, LocalPoint]:
    return LocalPoint(x_m=0.0, y_m=2500.0), LocalPoint(x_m=5000.0, y_m=2500.0)


def test_flat_terrain_profile_extraction_succeeds() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)

    assert profile.scenario_name == SCENARIO_FLAT
    assert profile.sample_count >= 2
    assert profile.samples[0].ix == 0
    assert profile.samples[-1].ix == terrain.width_cells - 1


def test_profile_includes_start_and_end_samples() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)

    assert profile.samples[0].point == start
    assert profile.samples[-1].point == end
    assert profile.samples[0].distance_from_start_m == 0.0
    assert profile.samples[-1].distance_to_end_m == pytest.approx(0.0)


def test_each_sample_reads_dem_and_dsm_values() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)

    for sample in profile.samples:
        assert sample.dem_msl == terrain.dem_at(ix=sample.ix, iy=sample.iy)
        assert sample.dsm_msl == terrain.dsm_at(ix=sample.ix, iy=sample.iy)
        assert sample.surface_delta_m == sample.dsm_msl - sample.dem_msl


def test_flat_terrain_surface_delta_is_zero() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)

    assert all(sample.surface_delta_m == 0.0 for sample in profile.samples)
    assert profile.max_surface_delta_m == 0.0


def test_building_profile_crossing_center_has_surface_delta() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT_WITH_BUILDING)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)

    assert any(sample.surface_delta_m > 0.0 for sample in profile.samples)
    assert profile.max_surface_delta_m > 0.0


def test_single_ridge_profile_crossing_center_has_dem_peak() -> None:
    base_dem_msl = 50.0
    terrain = create_synthetic_terrain(SCENARIO_SINGLE_RIDGE, base_dem_msl=base_dem_msl)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)

    assert profile.max_dem_msl > base_dem_msl
    assert profile.max_dsm_msl == profile.max_dem_msl


def test_obstacle_position_variation_has_multiple_surface_obstacle_samples() -> None:
    terrain = create_synthetic_terrain(SCENARIO_OBSTACLE_POSITION_VARIATION)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)
    obstacle_samples = [sample for sample in profile.samples if sample.surface_delta_m > 0.0]

    assert len(obstacle_samples) >= 3
    assert {sample.ix for sample in obstacle_samples}.issuperset({6, 25, 44})


def test_fresnel_position_variation_has_start_mid_end_obstacle_samples() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION)
    start, end = _horizontal_midline_points()

    profile = extract_terrain_profile(terrain=terrain, start=start, end=end)
    obstacle_ix = {sample.ix for sample in profile.samples if sample.surface_delta_m > 0.0}

    assert obstacle_ix.issuperset({6, 25, 44})


def test_local_point_and_grid_index_round_trip() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    point = LocalPoint(x_m=1200.0, y_m=3400.0)

    ix, iy = local_point_to_grid_index(terrain=terrain, point=point)
    round_trip = grid_index_to_local_point(terrain=terrain, ix=ix, iy=iy)

    assert (ix, iy) == (12, 34)
    assert round_trip == LocalPoint(x_m=1200.0, y_m=3400.0, z_m=0.0)


@pytest.mark.parametrize(
    "point",
    [
        LocalPoint(x_m=-100.0, y_m=0.0),
        LocalPoint(x_m=0.0, y_m=-100.0),
        LocalPoint(x_m=5100.0, y_m=0.0),
        LocalPoint(x_m=0.0, y_m=5100.0),
    ],
)
def test_out_of_bounds_point_raises(point: LocalPoint) -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)

    with pytest.raises(TerrainProfileError):
        local_point_to_grid_index(terrain=terrain, point=point)


@pytest.mark.parametrize("sample_spacing_m", [0.0, -1.0])
def test_sample_spacing_less_than_or_equal_to_zero_raises(sample_spacing_m: float) -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    start, end = _horizontal_midline_points()

    with pytest.raises(TerrainProfileError, match="sample_spacing_m"):
        extract_terrain_profile(
            terrain=terrain,
            start=start,
            end=end,
            sample_spacing_m=sample_spacing_m,
        )


def test_start_and_end_same_point_raises() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    point = LocalPoint(x_m=0.0, y_m=2500.0)

    with pytest.raises(TerrainProfileError, match="different"):
        extract_terrain_profile(terrain=terrain, start=point, end=point)
