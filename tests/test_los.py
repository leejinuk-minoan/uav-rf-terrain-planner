import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.los import LineOfSightError, analyze_dsm_los
from uav_rf_terrain.profile import TerrainProfile, TerrainProfileSample, extract_terrain_profile
from uav_rf_terrain.synthetic import (
    SCENARIO_FLAT,
    SCENARIO_FLAT_WITH_BUILDING,
    SCENARIO_SINGLE_RIDGE,
    create_synthetic_terrain,
)


def _sample(
    sample_index: int,
    distance_from_start_m: float,
    distance_to_end_m: float,
    dsm_msl: float,
    dem_msl: float = 0.0,
) -> TerrainProfileSample:
    return TerrainProfileSample(
        sample_index=sample_index,
        ix=sample_index,
        iy=0,
        point=LocalPoint(x_m=distance_from_start_m, y_m=0.0),
        distance_from_start_m=distance_from_start_m,
        distance_to_end_m=distance_to_end_m,
        dem_msl=dem_msl,
        dsm_msl=dsm_msl,
        surface_delta_m=dsm_msl - dem_msl,
    )


def _manual_profile(samples: tuple[TerrainProfileSample, ...]) -> TerrainProfile:
    return TerrainProfile(
        scenario_name="manual",
        start=LocalPoint(x_m=0.0, y_m=0.0),
        end=LocalPoint(x_m=1000.0, y_m=0.0),
        sample_spacing_m=100.0,
        samples=samples,
    )


def _flat_midline_profile() -> TerrainProfile:
    terrain = create_synthetic_terrain(SCENARIO_FLAT)
    return extract_terrain_profile(
        terrain=terrain,
        start=LocalPoint(x_m=0.0, y_m=2500.0),
        end=LocalPoint(x_m=5000.0, y_m=2500.0),
    )


def test_los_analysis_creation_succeeds() -> None:
    profile = _manual_profile(
        (
            _sample(0, 0.0, 1000.0, 10.0),
            _sample(1, 1000.0, 0.0, 10.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.scenario_name == "manual"
    assert analysis.launch_antenna_msl == 50.0
    assert analysis.drone_flight_msl == 180.0
    assert analysis.sample_count == 2


def test_sample_count_matches_profile_sample_count() -> None:
    profile = _flat_midline_profile()

    analysis = analyze_dsm_los(profile, launch_antenna_msl=100.0, drone_flight_msl=200.0)

    assert analysis.sample_count == profile.sample_count


def test_start_and_end_sample_ratios_are_zero_and_one() -> None:
    profile = _manual_profile(
        (
            _sample(0, 0.0, 1000.0, 10.0),
            _sample(1, 500.0, 500.0, 10.0),
            _sample(2, 1000.0, 0.0, 10.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.samples[0].ratio == 0.0
    assert analysis.samples[-1].ratio == 1.0


def test_los_line_msl_increases_linearly() -> None:
    profile = _manual_profile(
        (
            _sample(0, 0.0, 1000.0, 0.0),
            _sample(1, 500.0, 500.0, 0.0),
            _sample(2, 1000.0, 0.0, 0.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.samples[0].los_line_msl == pytest.approx(50.0)
    assert analysis.samples[1].los_line_msl == pytest.approx(115.0)
    assert analysis.samples[2].los_line_msl == pytest.approx(180.0)


def test_dsm_clearance_is_los_line_minus_dsm() -> None:
    profile = _manual_profile((_sample(0, 500.0, 500.0, 80.0),))

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.samples[0].dsm_clearance_m == pytest.approx(115.0 - 80.0)


def test_dsm_greater_than_or_equal_to_los_line_is_blocked() -> None:
    profile = _manual_profile(
        (
            _sample(0, 500.0, 500.0, 115.0),
            _sample(1, 800.0, 200.0, 153.9),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.samples[0].is_blocked is True
    assert analysis.samples[1].is_blocked is False


def test_blocked_sample_makes_profile_not_clear_and_score_zero() -> None:
    profile = _manual_profile(
        (
            _sample(0, 0.0, 1000.0, 10.0),
            _sample(1, 100.0, 900.0, 80.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.blocked_count == 1
    assert analysis.is_clear is False
    assert analysis.dsm_los_score == 0.0


def test_all_clear_profile_scores_100() -> None:
    profile = _manual_profile(
        (
            _sample(0, 0.0, 1000.0, 10.0),
            _sample(1, 500.0, 500.0, 20.0),
            _sample(2, 1000.0, 0.0, 30.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.blocked_count == 0
    assert analysis.is_clear is True
    assert analysis.dsm_los_score == 100.0


def test_min_clearance_m_is_computed() -> None:
    profile = _manual_profile(
        (
            _sample(0, 0.0, 1000.0, 40.0),
            _sample(1, 500.0, 500.0, 100.0),
            _sample(2, 1000.0, 0.0, 50.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.min_clearance_m == pytest.approx(10.0)


def test_flat_terrain_with_high_los_line_is_clear() -> None:
    profile = _flat_midline_profile()

    analysis = analyze_dsm_los(profile, launch_antenna_msl=100.0, drone_flight_msl=200.0)

    assert analysis.is_clear is True
    assert analysis.dsm_los_score == 100.0
    assert analysis.min_clearance_m > 0.0


def test_single_ridge_terrain_with_low_los_line_is_blocked() -> None:
    terrain = create_synthetic_terrain(SCENARIO_SINGLE_RIDGE)
    profile = extract_terrain_profile(
        terrain=terrain,
        start=LocalPoint(x_m=0.0, y_m=2500.0),
        end=LocalPoint(x_m=5000.0, y_m=2500.0),
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=60.0, drone_flight_msl=70.0)

    assert analysis.is_clear is False
    assert analysis.blocked_count > 0
    assert analysis.dsm_los_score == 0.0


def test_flat_with_building_center_obstacle_can_block_los() -> None:
    terrain = create_synthetic_terrain(SCENARIO_FLAT_WITH_BUILDING)
    profile = extract_terrain_profile(
        terrain=terrain,
        start=LocalPoint(x_m=0.0, y_m=2500.0),
        end=LocalPoint(x_m=5000.0, y_m=2500.0),
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=60.0, drone_flight_msl=70.0)

    assert analysis.is_clear is False
    assert analysis.blocked_count > 0
    assert analysis.dsm_los_score == 0.0


def test_required_geometry_example_100_300_500_800m() -> None:
    profile = _manual_profile(
        (
            _sample(0, 100.0, 900.0, 80.0),
            _sample(1, 300.0, 700.0, 80.0),
            _sample(2, 500.0, 500.0, 80.0),
            _sample(3, 800.0, 200.0, 80.0),
        )
    )

    analysis = analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)

    assert analysis.samples[0].ratio == pytest.approx(0.10)
    assert analysis.samples[0].los_line_msl == pytest.approx(63.0)
    assert analysis.samples[0].is_blocked is True

    assert analysis.samples[1].ratio == pytest.approx(0.30)
    assert analysis.samples[1].los_line_msl == pytest.approx(89.0)
    assert analysis.samples[1].is_blocked is False

    assert analysis.samples[2].ratio == pytest.approx(0.50)
    assert analysis.samples[2].los_line_msl == pytest.approx(115.0)
    assert analysis.samples[2].is_blocked is False

    assert analysis.samples[3].ratio == pytest.approx(0.80)
    assert analysis.samples[3].los_line_msl == pytest.approx(154.0)
    assert analysis.samples[3].is_blocked is False

    assert analysis.dsm_los_score == 0.0


def test_empty_samples_profile_raises_line_of_sight_error() -> None:
    profile = _manual_profile(())

    with pytest.raises(LineOfSightError, match="at least one sample"):
        analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)


def test_zero_total_distance_sample_raises_line_of_sight_error() -> None:
    profile = _manual_profile((_sample(0, 0.0, 0.0, 0.0),))

    with pytest.raises(LineOfSightError, match="total distance"):
        analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)


def test_abnormal_ratio_sample_raises_line_of_sight_error() -> None:
    profile = _manual_profile((_sample(0, -1.0, 1000.0, 0.0),))

    with pytest.raises(LineOfSightError, match="ratio"):
        analyze_dsm_los(profile, launch_antenna_msl=50.0, drone_flight_msl=180.0)


def test_non_finite_endpoint_height_raises_line_of_sight_error() -> None:
    profile = _manual_profile((_sample(0, 0.0, 1000.0, 0.0),))

    with pytest.raises(LineOfSightError, match="finite"):
        analyze_dsm_los(profile, launch_antenna_msl=float("nan"), drone_flight_msl=180.0)
