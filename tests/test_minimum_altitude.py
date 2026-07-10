from dataclasses import fields

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.fresnel import first_fresnel_radius_m, wavelength_m
from uav_rf_terrain.minimum_altitude import (
    AltitudeRequirementSample,
    MinimumAltitudeConfig,
    MinimumAltitudeError,
    MinimumAltitudeResult,
    compute_minimum_required_altitude,
    summarize_minimum_altitude_result,
)
from uav_rf_terrain.profile import TerrainProfile, TerrainProfileSample


def _sample(
    sample_index: int,
    distance_from_start_m: float,
    distance_to_end_m: float,
    dem_msl: float,
    dsm_msl: float,
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


def _profile(samples: tuple[TerrainProfileSample, ...]) -> TerrainProfile:
    return TerrainProfile(
        scenario_name="minimum_altitude_manual",
        start=LocalPoint(x_m=0.0, y_m=0.0),
        end=LocalPoint(x_m=1000.0, y_m=0.0),
        sample_spacing_m=500.0,
        samples=samples,
    )


def _flat_profile(dem_msl: float = 50.0) -> TerrainProfile:
    return _profile(
        (
            _sample(0, 0.0, 1000.0, dem_msl, dem_msl),
            _sample(1, 500.0, 500.0, dem_msl, dem_msl),
            _sample(2, 1000.0, 0.0, dem_msl, dem_msl),
        )
    )


def test_flat_terrain_minimum_msl_is_above_target_dem_due_to_fresnel_clearance() -> None:
    profile = _flat_profile()

    result = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
    )

    assert isinstance(result, MinimumAltitudeResult)
    assert result.minimum_required_msl_m >= result.target_dem_msl_m
    assert result.minimum_required_msl_m > 50.0
    assert result.limiting_sample_index == 1
    assert result.sample_requirements[0].path_ratio == pytest.approx(0.5)


def test_middle_ridge_sample_becomes_limiting_sample() -> None:
    profile = _profile(
        (
            _sample(0, 0.0, 1000.0, 50.0, 50.0),
            _sample(1, 500.0, 500.0, 85.0, 85.0),
            _sample(2, 1000.0, 0.0, 50.0, 50.0),
        )
    )

    result = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
    )

    assert result.limiting_sample_index == 1
    assert result.minimum_required_msl_m > 85.0


def test_58ghz_requires_no_more_msl_than_24ghz_for_same_profile() -> None:
    profile = _flat_profile()

    result_24 = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
    )
    result_58 = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=50.0,
        frequency_hz=5_800_000_000.0,
    )

    assert result_58.minimum_required_msl_m <= result_24.minimum_required_msl_m
    assert result_58.sample_requirements[0].fresnel_radius_m < (
        result_24.sample_requirements[0].fresnel_radius_m
    )


def test_increasing_required_clearance_ratio_increases_minimum_msl() -> None:
    profile = _flat_profile()

    low_clearance = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
        required_fresnel_clearance_ratio=0.2,
    )
    high_clearance = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
        required_fresnel_clearance_ratio=0.8,
    )

    assert high_clearance.minimum_required_msl_m > low_clearance.minimum_required_msl_m


def test_agl_conversions_use_highest_dem_and_target_dem() -> None:
    profile = _profile(
        (
            _sample(0, 0.0, 1000.0, 40.0, 40.0),
            _sample(1, 500.0, 500.0, 90.0, 90.0),
            _sample(2, 1000.0, 0.0, 60.0, 60.0),
        )
    )

    result = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=40.0,
        frequency_hz=2_400_000_000.0,
        required_fresnel_clearance_ratio=0.0,
    )

    assert result.highest_dem_msl_m == 90.0
    assert result.target_dem_msl_m == 60.0
    assert result.minimum_required_agl_over_highest_dem_m == pytest.approx(
        result.minimum_required_msl_m - 90.0
    )
    assert result.minimum_required_agl_over_target_dem_m == pytest.approx(
        result.minimum_required_msl_m - 60.0
    )
    assert result.display_agl_over_highest_dem_m == max(
        0.0,
        result.minimum_required_agl_over_highest_dem_m,
    )


def test_per_sample_required_endpoint_altitude_matches_formula() -> None:
    profile = _flat_profile()
    frequency_hz = 2_400_000_000.0
    launch_antenna_msl_m = 50.0
    ratio = 0.5
    radius = first_fresnel_radius_m(
        wavelength_m=wavelength_m(frequency_hz),
        d1_m=500.0,
        d2_m=500.0,
    )

    result = compute_minimum_required_altitude(
        profile,
        launch_antenna_msl_m=launch_antenna_msl_m,
        frequency_hz=frequency_hz,
    )

    expected_required_los = 50.0 + 0.6 * radius
    expected_endpoint_msl = (
        launch_antenna_msl_m + (expected_required_los - launch_antenna_msl_m) / ratio
    )
    assert result.sample_requirements[0].required_los_msl_m == pytest.approx(
        expected_required_los
    )
    assert result.sample_requirements[0].required_drone_msl_m == pytest.approx(
        expected_endpoint_msl
    )


def test_launch_endpoint_sample_is_skipped() -> None:
    result = compute_minimum_required_altitude(
        _flat_profile(),
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
    )

    assert [sample.sample_index for sample in result.sample_requirements] == [1, 2]


@pytest.mark.parametrize("frequency_hz", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_frequency_raises(frequency_hz: float) -> None:
    with pytest.raises(MinimumAltitudeError, match="frequency_hz"):
        compute_minimum_required_altitude(
            _flat_profile(),
            launch_antenna_msl_m=50.0,
            frequency_hz=frequency_hz,
        )


def test_empty_profile_raises() -> None:
    with pytest.raises(MinimumAltitudeError, match="at least one sample"):
        compute_minimum_required_altitude(
            _profile(()),
            launch_antenna_msl_m=50.0,
            frequency_hz=2_400_000_000.0,
        )


def test_zero_length_profile_raises() -> None:
    profile = _profile((_sample(0, 0.0, 0.0, 50.0, 50.0),))

    with pytest.raises(MinimumAltitudeError, match="total distance"):
        compute_minimum_required_altitude(
            profile,
            launch_antenna_msl_m=50.0,
            frequency_hz=2_400_000_000.0,
        )


def test_negative_clearance_ratio_raises() -> None:
    with pytest.raises(MinimumAltitudeError, match="clearance_ratio"):
        compute_minimum_required_altitude(
            _flat_profile(),
            launch_antenna_msl_m=50.0,
            frequency_hz=2_400_000_000.0,
            required_fresnel_clearance_ratio=-0.1,
        )


def test_all_samples_at_launch_endpoint_raise() -> None:
    profile = _profile(
        (
            _sample(0, 0.0, 1000.0, 50.0, 50.0),
            _sample(1, 0.0, 1000.0, 50.0, 50.0),
        )
    )

    with pytest.raises(MinimumAltitudeError, match="valid ratio sample"):
        compute_minimum_required_altitude(
            profile,
            launch_antenna_msl_m=50.0,
            frequency_hz=2_400_000_000.0,
        )


def test_summary_contains_offline_proxy_boundary_wording() -> None:
    result = compute_minimum_required_altitude(
        _flat_profile(),
        launch_antenna_msl_m=50.0,
        frequency_hz=2_400_000_000.0,
    )

    summary = summarize_minimum_altitude_result(result)

    assert "offline DSM-based LOS/Fresnel clearance proxy" in summary
    assert "not a real communication-success or flight-safety guarantee" in summary
    assert "limiting_sample_index=1" in summary


def test_summary_rejects_wrong_type() -> None:
    with pytest.raises(MinimumAltitudeError, match="MinimumAltitudeResult"):
        summarize_minimum_altitude_result("not-result")  # type: ignore[arg-type]


def test_public_dataclasses_have_expected_fields() -> None:
    sample_field_names = {field.name for field in fields(AltitudeRequirementSample)}
    result_field_names = {field.name for field in fields(MinimumAltitudeResult)}

    assert "required_drone_msl_m" in sample_field_names
    assert "minimum_required_msl_m" in result_field_names
    assert "minimum_required_agl_over_highest_dem_m" in result_field_names


def test_config_accepts_default_proxy_threshold() -> None:
    config = MinimumAltitudeConfig(frequency_hz=2_400_000_000.0)

    assert config.required_fresnel_clearance_ratio == 0.6
