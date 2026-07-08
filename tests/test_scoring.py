from dataclasses import fields

import pytest

from uav_rf_terrain.config import DISTANCE_WEIGHT, DSM_FRESNEL_WEIGHT, DSM_LOS_WEIGHT, SHIELDING_WEIGHT
from uav_rf_terrain.scoring import (
    CandidateScore,
    ScoreComponentWeights,
    ScoringError,
    clamp_score,
    compute_candidate_score,
    compute_distance_score,
    compute_overall_score,
    compute_shielding_stability_score,
)


def test_default_weights_match_config_constants() -> None:
    weights = ScoreComponentWeights()

    assert weights.shielding_weight == SHIELDING_WEIGHT
    assert weights.distance_weight == DISTANCE_WEIGHT
    assert weights.dsm_los_weight == DSM_LOS_WEIGHT
    assert weights.dsm_fresnel_weight == DSM_FRESNEL_WEIGHT


def test_distance_score_calculation() -> None:
    score = compute_distance_score(distance_3d_m=250.0, operating_radius_m=1000.0)

    assert score == pytest.approx(75.0)


def test_distance_score_zero_distance_is_100() -> None:
    assert compute_distance_score(distance_3d_m=0.0, operating_radius_m=1000.0) == 100.0


def test_distance_score_at_operating_radius_is_zero() -> None:
    assert compute_distance_score(distance_3d_m=1000.0, operating_radius_m=1000.0) == 0.0


def test_distance_score_beyond_operating_radius_clamps_to_zero() -> None:
    assert compute_distance_score(distance_3d_m=1500.0, operating_radius_m=1000.0) == 0.0


@pytest.mark.parametrize("operating_radius_m", [0.0, -1.0])
def test_operating_radius_m_must_be_positive(operating_radius_m: float) -> None:
    with pytest.raises(ScoringError, match="operating_radius_m"):
        compute_distance_score(distance_3d_m=1.0, operating_radius_m=operating_radius_m)


def test_negative_distance_3d_m_raises_scoring_error() -> None:
    with pytest.raises(ScoringError, match="distance_3d_m"):
        compute_distance_score(distance_3d_m=-1.0, operating_radius_m=1000.0)


def test_shielding_stability_score_uses_los_40_fresnel_60() -> None:
    score = compute_shielding_stability_score(dsm_los_score=80.0, dsm_fresnel_score=50.0)

    assert score == pytest.approx(80.0 * 0.40 + 50.0 * 0.60)


def test_los_zero_applies_strict_shielding_cap() -> None:
    score = compute_shielding_stability_score(dsm_los_score=0.0, dsm_fresnel_score=100.0)

    assert score == 0.0


def test_overall_score_uses_shielding_80_distance_20() -> None:
    score = compute_overall_score(shielding_stability_score=70.0, distance_score=50.0)

    assert score == pytest.approx(70.0 * 0.80 + 50.0 * 0.20)


def test_candidate_score_full_calculation() -> None:
    score = compute_candidate_score(
        distance_3d_m=250.0,
        operating_radius_m=1000.0,
        dsm_los_score=80.0,
        dsm_fresnel_score=50.0,
    )

    assert isinstance(score, CandidateScore)
    assert score.distance_score == pytest.approx(75.0)
    assert score.shielding_stability_score == pytest.approx(62.0)
    assert score.overall_score == pytest.approx(62.0 * 0.80 + 75.0 * 0.20)
    assert score.distance_3d_m == 250.0
    assert score.operating_radius_m == 1000.0
    assert score.dsm_los_score == 80.0
    assert score.dsm_fresnel_score == 50.0


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("distance_3d_m", {"distance_3d_m": float("nan"), "operating_radius_m": 1000.0}),
        ("operating_radius_m", {"distance_3d_m": 1.0, "operating_radius_m": float("inf")}),
    ],
)
def test_distance_inputs_must_be_finite(field_name: str, kwargs: dict[str, float]) -> None:
    with pytest.raises(ScoringError, match=field_name):
        compute_distance_score(**kwargs)


@pytest.mark.parametrize("score_value", [float("nan"), float("inf")])
def test_score_input_non_finite_raises_scoring_error(score_value: float) -> None:
    with pytest.raises(ScoringError, match="dsm_los_score"):
        compute_shielding_stability_score(dsm_los_score=score_value, dsm_fresnel_score=50.0)


@pytest.mark.parametrize("score_value", [-0.1, 100.1])
def test_score_input_out_of_range_raises_scoring_error(score_value: float) -> None:
    with pytest.raises(ScoringError, match="dsm_fresnel_score"):
        compute_shielding_stability_score(dsm_los_score=50.0, dsm_fresnel_score=score_value)


def test_compute_overall_score_rejects_out_of_range_components() -> None:
    with pytest.raises(ScoringError, match="shielding_stability_score"):
        compute_overall_score(shielding_stability_score=101.0, distance_score=50.0)


def test_weight_sum_must_equal_one() -> None:
    weights = ScoreComponentWeights(
        shielding_weight=0.70,
        distance_weight=0.20,
        dsm_los_weight=0.40,
        dsm_fresnel_weight=0.60,
    )

    with pytest.raises(ScoringError, match="shielding_weight and distance_weight"):
        weights.validate()


def test_los_fresnel_weight_sum_must_equal_one() -> None:
    weights = ScoreComponentWeights(
        shielding_weight=0.80,
        distance_weight=0.20,
        dsm_los_weight=0.40,
        dsm_fresnel_weight=0.50,
    )

    with pytest.raises(ScoringError, match="dsm_los_weight and dsm_fresnel_weight"):
        weights.validate()


def test_negative_weight_raises_scoring_error() -> None:
    weights = ScoreComponentWeights(
        shielding_weight=-0.10,
        distance_weight=1.10,
        dsm_los_weight=0.40,
        dsm_fresnel_weight=0.60,
    )

    with pytest.raises(ScoringError, match="shielding_weight"):
        weights.validate()


def test_non_finite_weight_raises_scoring_error() -> None:
    weights = ScoreComponentWeights(
        shielding_weight=float("nan"),
        distance_weight=0.20,
        dsm_los_weight=0.40,
        dsm_fresnel_weight=0.60,
    )

    with pytest.raises(ScoringError, match="shielding_weight"):
        weights.validate()


def test_clamp_score_bounds_outputs() -> None:
    assert clamp_score(-1.0) == 0.0
    assert clamp_score(50.0) == 50.0
    assert clamp_score(101.0) == 100.0


def test_candidate_score_has_no_color_classification() -> None:
    field_names = {field.name for field in fields(CandidateScore)}

    assert "color_class" not in field_names
    assert "classification" not in field_names
    assert "map_color" not in field_names


def test_candidate_score_has_no_top5_or_ranking_output() -> None:
    field_names = {field.name for field in fields(CandidateScore)}

    prohibited_fields = {"rank", "ranking", "top_n", "top_5", "ranked_launch_sites"}
    assert field_names.isdisjoint(prohibited_fields)


def test_candidate_score_has_no_required_link_metric_fields() -> None:
    field_names = {field.name for field in fields(CandidateScore)}

    assert "rssi" not in field_names
    assert "sinr" not in field_names
    assert "packet_loss" not in field_names


def test_los_blocked_still_keeps_distance_component_in_overall_score() -> None:
    score = compute_candidate_score(
        distance_3d_m=0.0,
        operating_radius_m=1000.0,
        dsm_los_score=0.0,
        dsm_fresnel_score=100.0,
    )

    assert score.shielding_stability_score == 0.0
    assert score.distance_score == 100.0
    assert score.overall_score == pytest.approx(20.0)
