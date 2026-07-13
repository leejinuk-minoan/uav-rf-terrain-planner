import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.los import LineOfSightAnalysis, LineOfSightSample, analyze_dsm_los
from uav_rf_terrain.profile import TerrainProfile, TerrainProfileSample
from uav_rf_terrain.fresnel import (
    SPEED_OF_LIGHT_MPS,
    FresnelAnalysis,
    FresnelAnalysisError,
    analyze_dsm_fresnel,
    first_fresnel_radius_m,
    knife_edge_loss_db,
    knife_edge_nu_from_clearance_ratio,
    knife_edge_nu_from_height,
    wavelength_m,
)


def test_knife_edge_formula_foundation() -> None:
    assert knife_edge_nu_from_clearance_ratio(0.0) == 0.0
    assert knife_edge_nu_from_clearance_ratio(1.0) < 0.0
    assert knife_edge_nu_from_clearance_ratio(-1.0) > 0.0
    radius = first_fresnel_radius_m(wavelength_m=0.3, d1_m=100.0, d2_m=200.0)
    assert knife_edge_nu_from_height(h_m=2.5, wavelength_m=0.3, d1_m=100.0, d2_m=200.0) == pytest.approx(knife_edge_nu_from_clearance_ratio(-2.5 / radius))
    assert knife_edge_loss_db(-1.0) == 0.0
    assert knife_edge_loss_db(-0.78) == 0.0
    assert knife_edge_loss_db(0.0) == pytest.approx(6.03285, rel=1e-4)
    assert knife_edge_loss_db(1.0) > knife_edge_loss_db(0.0)


@pytest.mark.parametrize("value", (float("nan"), float("inf"), float("-inf")))
def test_knife_edge_helpers_reject_non_finite(value: float) -> None:
    with pytest.raises(FresnelAnalysisError):
        knife_edge_nu_from_clearance_ratio(value)
    with pytest.raises(FresnelAnalysisError):
        knife_edge_nu_from_height(h_m=value, wavelength_m=1.0, d1_m=1.0, d2_m=1.0)
    with pytest.raises(FresnelAnalysisError):
        knife_edge_loss_db(value)


@pytest.mark.parametrize("field", ("wavelength_m", "d1_m", "d2_m"))
def test_knife_edge_height_rejects_zero(field: str) -> None:
    values = {"h_m": 1.0, "wavelength_m": 1.0, "d1_m": 1.0, "d2_m": 1.0}
    values[field] = 0.0
    with pytest.raises(FresnelAnalysisError):
        knife_edge_nu_from_height(**values)


def _terrain_sample(
    sample_index: int,
    distance_from_start_m: float,
    distance_to_end_m: float,
    dsm_msl: float = 0.0,
) -> TerrainProfileSample:
    return TerrainProfileSample(
        sample_index=sample_index,
        ix=sample_index,
        iy=0,
        point=LocalPoint(x_m=distance_from_start_m, y_m=0.0),
        distance_from_start_m=distance_from_start_m,
        distance_to_end_m=distance_to_end_m,
        dem_msl=0.0,
        dsm_msl=dsm_msl,
        surface_delta_m=dsm_msl,
    )


def _profile_with_clearance_values(clearances: tuple[float, ...]) -> TerrainProfile:
    total_distance_m = 1000.0
    if len(clearances) == 1:
        distances = (500.0,)
    else:
        step_m = total_distance_m / (len(clearances) - 1)
        distances = tuple(index * step_m for index in range(len(clearances)))

    samples = tuple(
        _terrain_sample(
            sample_index=index,
            distance_from_start_m=distance,
            distance_to_end_m=total_distance_m - distance,
            dsm_msl=100.0 - clearance,
        )
        for index, (distance, clearance) in enumerate(zip(distances, clearances, strict=True))
    )
    return TerrainProfile(
        scenario_name="manual_fresnel",
        start=LocalPoint(x_m=0.0, y_m=0.0),
        end=LocalPoint(x_m=total_distance_m, y_m=0.0),
        sample_spacing_m=250.0,
        samples=samples,
    )


def _los_analysis_with_clearance_values(clearances: tuple[float, ...]) -> LineOfSightAnalysis:
    profile = _profile_with_clearance_values(clearances)
    return analyze_dsm_los(profile, launch_antenna_msl=100.0, drone_flight_msl=100.0)


def _manual_los_analysis(samples: tuple[LineOfSightSample, ...]) -> LineOfSightAnalysis:
    return LineOfSightAnalysis(
        scenario_name="manual_fresnel",
        launch_antenna_msl=100.0,
        drone_flight_msl=100.0,
        samples=samples,
        dsm_los_score=100.0,
    )


def _los_sample(
    sample_index: int,
    d1_m: float,
    d2_m: float,
    dsm_clearance_m: float,
) -> LineOfSightSample:
    terrain_sample = _terrain_sample(
        sample_index=sample_index,
        distance_from_start_m=d1_m,
        distance_to_end_m=d2_m,
        dsm_msl=100.0 - dsm_clearance_m,
    )
    total_distance_m = d1_m + d2_m
    ratio = 0.0 if total_distance_m == 0.0 else d1_m / total_distance_m
    return LineOfSightSample(
        sample_index=sample_index,
        terrain_sample=terrain_sample,
        ratio=ratio,
        los_line_msl=100.0,
        dsm_clearance_m=dsm_clearance_m,
        is_blocked=dsm_clearance_m <= 0.0,
    )


def test_wavelength_m_calculation() -> None:
    assert wavelength_m(2_400_000_000.0) == pytest.approx(SPEED_OF_LIGHT_MPS / 2_400_000_000.0)


@pytest.mark.parametrize("frequency_hz", [0.0, -1.0, float("nan"), float("inf")])
def test_frequency_hz_must_be_positive_and_finite(frequency_hz: float) -> None:
    with pytest.raises(FresnelAnalysisError, match="frequency_hz"):
        wavelength_m(frequency_hz)


def test_first_fresnel_radius_m_calculation() -> None:
    lam = wavelength_m(2_400_000_000.0)

    radius = first_fresnel_radius_m(wavelength_m=lam, d1_m=500.0, d2_m=500.0)

    assert radius == pytest.approx((lam * 500.0 * 500.0 / 1000.0) ** 0.5)


def test_endpoint_sample_radius_zero_and_score_100() -> None:
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, dsm_clearance_m=-50.0),
            _los_sample(1, 1000.0, 0.0, dsm_clearance_m=-50.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.samples[0].fresnel_radius_m == 0.0
    assert analysis.samples[0].fresnel_intrusion_ratio == 0.0
    assert analysis.samples[0].dsm_fresnel_sample_score == 100.0
    assert analysis.samples[1].fresnel_radius_m == 0.0
    assert analysis.samples[1].dsm_fresnel_sample_score == 100.0


def test_sample_count_matches_los_analysis() -> None:
    los_analysis = _los_analysis_with_clearance_values((100.0, 100.0, 100.0))

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.sample_count == len(los_analysis.samples)


def test_d1_d2_match_terrain_profile_distances() -> None:
    los_analysis = _los_analysis_with_clearance_values((100.0, 100.0, 100.0))

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    for fresnel_sample, los_sample in zip(analysis.samples, los_analysis.samples, strict=True):
        assert fresnel_sample.d1_m == los_sample.terrain_sample.distance_from_start_m
        assert fresnel_sample.d2_m == los_sample.terrain_sample.distance_to_end_m


def test_midpoint_fresnel_radius_is_larger_than_endpoint_and_near_end() -> None:
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, dsm_clearance_m=100.0),
            _los_sample(1, 100.0, 900.0, dsm_clearance_m=100.0),
            _los_sample(2, 300.0, 700.0, dsm_clearance_m=100.0),
            _los_sample(3, 500.0, 500.0, dsm_clearance_m=100.0),
            _los_sample(4, 800.0, 200.0, dsm_clearance_m=100.0),
            _los_sample(5, 1000.0, 0.0, dsm_clearance_m=100.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)
    radius_by_distance = {
        sample.d1_m: sample.fresnel_radius_m
        for sample in analysis.samples
    }

    assert radius_by_distance[500.0] == analysis.max_fresnel_radius_m
    assert radius_by_distance[500.0] > radius_by_distance[0.0]
    assert radius_by_distance[500.0] > radius_by_distance[100.0]
    assert radius_by_distance[500.0] > radius_by_distance[800.0]


def test_24ghz_radius_is_larger_than_58ghz_radius() -> None:
    radius_24 = first_fresnel_radius_m(
        wavelength_m=wavelength_m(2_400_000_000.0),
        d1_m=500.0,
        d2_m=500.0,
    )
    radius_58 = first_fresnel_radius_m(
        wavelength_m=wavelength_m(5_800_000_000.0),
        d1_m=500.0,
        d2_m=500.0,
    )

    assert radius_24 > radius_58


def test_clearance_greater_than_or_equal_radius_scores_100() -> None:
    lam = wavelength_m(2_400_000_000.0)
    radius = first_fresnel_radius_m(wavelength_m=lam, d1_m=500.0, d2_m=500.0)
    los_analysis = _manual_los_analysis((_los_sample(0, 500.0, 500.0, radius),))

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.samples[0].clearance_ratio == pytest.approx(1.0)
    assert analysis.samples[0].fresnel_intrusion_ratio == 0.0
    assert analysis.samples[0].dsm_fresnel_sample_score == 100.0


def test_zero_clearance_scores_zero() -> None:
    los_analysis = _manual_los_analysis((_los_sample(0, 500.0, 500.0, 0.0),))

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.samples[0].clearance_ratio == 0.0
    assert analysis.samples[0].fresnel_intrusion_ratio == 1.0
    assert analysis.samples[0].dsm_fresnel_sample_score == 0.0


def test_negative_clearance_scores_zero() -> None:
    los_analysis = _manual_los_analysis((_los_sample(0, 500.0, 500.0, -5.0),))

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.samples[0].fresnel_intrusion_ratio == 1.0
    assert analysis.samples[0].dsm_fresnel_sample_score == 0.0


def test_partial_clearance_scores_between_zero_and_100() -> None:
    lam = wavelength_m(2_400_000_000.0)
    radius = first_fresnel_radius_m(wavelength_m=lam, d1_m=500.0, d2_m=500.0)
    los_analysis = _manual_los_analysis((_los_sample(0, 500.0, 500.0, radius / 2.0),))

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.samples[0].clearance_ratio == pytest.approx(0.5)
    assert analysis.samples[0].fresnel_intrusion_ratio == pytest.approx(0.5)
    assert 0.0 < analysis.samples[0].dsm_fresnel_sample_score < 100.0
    assert analysis.samples[0].dsm_fresnel_sample_score == pytest.approx(50.0)


def test_dsm_fresnel_score_is_average_sample_score() -> None:
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, 100.0),
            _los_sample(1, 500.0, 500.0, 0.0),
            _los_sample(2, 1000.0, 0.0, 100.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    expected_average = sum(
        sample.dsm_fresnel_sample_score for sample in analysis.samples
    ) / analysis.sample_count
    assert analysis.dsm_fresnel_score == pytest.approx(expected_average)
    assert analysis.average_fresnel_score == analysis.dsm_fresnel_score
    assert analysis.dsm_fresnel_score == pytest.approx((100.0 + 0.0 + 100.0) / 3.0)


def test_dominant_obstacle_excludes_endpoints_and_reports_worst_eligible_score() -> None:
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, -100.0),
            _los_sample(1, 250.0, 750.0, 4.0),
            _los_sample(2, 500.0, 500.0, 0.0),
            _los_sample(3, 1000.0, 0.0, -100.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.dominant_obstacle is not None
    assert analysis.dominant_obstacle.sample_index == 2
    assert analysis.worst_obstacle_score == 0.0
    assert analysis.dominant_obstacle.clearance_m == 0.0
    assert analysis.dominant_obstacle.nu == 0.0
    assert analysis.dominant_obstacle.diffraction_loss_db == pytest.approx(6.03285, rel=1e-4)


def test_dominant_obstacle_uses_lowest_index_to_break_clearance_ratio_tie() -> None:
    frequency_hz = 2_400_000_000.0
    radius_1 = first_fresnel_radius_m(
        wavelength_m=wavelength_m(frequency_hz), d1_m=250.0, d2_m=750.0
    )
    radius_2 = first_fresnel_radius_m(
        wavelength_m=wavelength_m(frequency_hz), d1_m=750.0, d2_m=250.0
    )
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, 100.0),
            _los_sample(7, 250.0, 750.0, radius_1 / 2.0),
            _los_sample(3, 750.0, 250.0, radius_2 / 2.0),
            _los_sample(9, 1000.0, 0.0, 100.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=frequency_hz)

    assert analysis.dominant_obstacle is not None
    assert analysis.dominant_obstacle.sample_index == 3
    assert analysis.dominant_obstacle.clearance_ratio == pytest.approx(0.5)
    assert analysis.dominant_obstacle.nu == pytest.approx(
        knife_edge_nu_from_clearance_ratio(analysis.dominant_obstacle.clearance_ratio)
    )
    assert analysis.dominant_obstacle.diffraction_loss_db == pytest.approx(
        knife_edge_loss_db(analysis.dominant_obstacle.nu)
    )


def test_single_intrusion_preserves_high_average_and_identifies_zero_worst_score() -> None:
    los_analysis = _manual_los_analysis(
        tuple(
            _los_sample(index, index * 100.0, (10 - index) * 100.0, 0.0 if index == 5 else 100.0)
            for index in range(11)
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.average_fresnel_score > 90.0
    assert analysis.worst_obstacle_score == 0.0
    assert analysis.dominant_obstacle is not None
    assert analysis.dominant_obstacle.sample_index == 5


def test_dominant_obstacle_distinguishes_clear_intrusion_and_los_exceedance() -> None:
    frequency_hz = 2_400_000_000.0
    radius = first_fresnel_radius_m(
        wavelength_m=wavelength_m(frequency_hz), d1_m=500.0, d2_m=500.0
    )
    clear_intrusion = analyze_dsm_fresnel(
        _manual_los_analysis((_los_sample(1, 500.0, 500.0, radius / 2.0),)),
        frequency_hz=frequency_hz,
    )
    los_exceedance = analyze_dsm_fresnel(
        _manual_los_analysis((_los_sample(1, 500.0, 500.0, -1.0),)),
        frequency_hz=frequency_hz,
    )

    assert clear_intrusion.samples[0].los_sample.is_blocked is False
    assert clear_intrusion.dominant_obstacle is not None
    assert 0.0 < clear_intrusion.dominant_obstacle.fresnel_sample_score < 100.0
    assert los_exceedance.dominant_obstacle is not None
    assert los_exceedance.dominant_obstacle.clearance_m < 0.0
    assert los_exceedance.dominant_obstacle.nu > 0.0
    assert (
        los_exceedance.dominant_obstacle.diffraction_loss_db
        > clear_intrusion.dominant_obstacle.diffraction_loss_db
    )


def test_no_eligible_sample_has_no_dominant_obstacle() -> None:
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, -50.0),
            _los_sample(1, 1000.0, 0.0, -50.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.dominant_obstacle is None
    assert analysis.worst_obstacle_score is None
    assert analysis.average_fresnel_score == analysis.dsm_fresnel_score == 100.0


def test_analysis_properties() -> None:
    los_analysis = _manual_los_analysis(
        (
            _los_sample(0, 0.0, 1000.0, 100.0),
            _los_sample(1, 500.0, 500.0, 0.0),
            _los_sample(2, 1000.0, 0.0, 100.0),
        )
    )

    analysis = analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)

    assert analysis.max_fresnel_radius_m == analysis.samples[1].fresnel_radius_m
    assert analysis.max_intrusion_ratio == 1.0
    assert analysis.min_sample_score == 0.0
    assert isinstance(analysis, FresnelAnalysis)


def test_empty_los_samples_raise_fresnel_analysis_error() -> None:
    los_analysis = _manual_los_analysis(())

    with pytest.raises(FresnelAnalysisError, match="at least one sample"):
        analyze_dsm_fresnel(los_analysis, frequency_hz=2_400_000_000.0)


@pytest.mark.parametrize("frequency_hz", [float("nan"), float("inf")])
def test_non_finite_frequency_raises_fresnel_analysis_error(frequency_hz: float) -> None:
    los_analysis = _los_analysis_with_clearance_values((100.0, 100.0, 100.0))

    with pytest.raises(FresnelAnalysisError, match="frequency_hz"):
        analyze_dsm_fresnel(los_analysis, frequency_hz=frequency_hz)


def test_first_fresnel_radius_rejects_negative_distance() -> None:
    with pytest.raises(FresnelAnalysisError, match="d1_m"):
        first_fresnel_radius_m(wavelength_m=1.0, d1_m=-1.0, d2_m=10.0)
