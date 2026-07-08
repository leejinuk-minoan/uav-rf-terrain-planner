from dataclasses import fields
from pathlib import Path

import pytest

from uav_rf_terrain.classification import (
    ClassificationError,
    ColorClassificationThresholds,
    LaunchAreaCellEvaluation,
    classify_candidate_score,
    evaluate_launch_area_cell,
)
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.scoring import CandidateScore


def make_score(
    *,
    dsm_los_score: float = 100.0,
    shielding_stability_score: float = 80.0,
    overall_score: float = 80.0,
) -> CandidateScore:
    return CandidateScore(
        distance_3d_m=100.0,
        operating_radius_m=1000.0,
        dsm_los_score=dsm_los_score,
        dsm_fresnel_score=100.0,
        distance_score=90.0,
        shielding_stability_score=shielding_stability_score,
        overall_score=overall_score,
    )


def test_threshold_defaults() -> None:
    thresholds = ColorClassificationThresholds()

    assert thresholds.green_min_overall_score == 75.0
    assert thresholds.yellow_min_overall_score == 60.0
    assert thresholds.orange_min_overall_score == 40.0


def test_threshold_order_error_raises_classification_error() -> None:
    thresholds = ColorClassificationThresholds(
        green_min_overall_score=75.0,
        yellow_min_overall_score=30.0,
        orange_min_overall_score=40.0,
    )

    with pytest.raises(ClassificationError, match="orange_min_overall_score"):
        thresholds.validate()


def test_threshold_upper_order_error_raises_classification_error() -> None:
    thresholds = ColorClassificationThresholds(
        green_min_overall_score=50.0,
        yellow_min_overall_score=60.0,
        orange_min_overall_score=40.0,
    )

    with pytest.raises(ClassificationError, match="yellow_min_overall_score"):
        thresholds.validate()


@pytest.mark.parametrize("threshold_value", [float("nan"), float("inf")])
def test_non_finite_threshold_raises_classification_error(threshold_value: float) -> None:
    thresholds = ColorClassificationThresholds(green_min_overall_score=threshold_value)

    with pytest.raises(ClassificationError, match="green_min_overall_score"):
        thresholds.validate()


@pytest.mark.parametrize("threshold_value", [-0.1, 100.1])
def test_out_of_range_threshold_raises_classification_error(threshold_value: float) -> None:
    thresholds = ColorClassificationThresholds(orange_min_overall_score=threshold_value)

    with pytest.raises(ClassificationError, match="orange_min_overall_score"):
        thresholds.validate()


def test_within_operation_radius_false_is_excluded() -> None:
    color_class = classify_candidate_score(make_score(), within_operation_radius=False)

    assert color_class is ColorClass.EXCLUDED


def test_dsm_los_score_zero_is_red() -> None:
    color_class = classify_candidate_score(
        make_score(dsm_los_score=0.0, shielding_stability_score=0.0, overall_score=20.0),
        within_operation_radius=True,
    )

    assert color_class is ColorClass.RED


def test_shielding_stability_score_zero_is_red() -> None:
    color_class = classify_candidate_score(
        make_score(dsm_los_score=100.0, shielding_stability_score=0.0, overall_score=80.0),
        within_operation_radius=True,
    )

    assert color_class is ColorClass.RED


def test_overall_score_below_40_is_red() -> None:
    color_class = classify_candidate_score(make_score(overall_score=39.9), within_operation_radius=True)

    assert color_class is ColorClass.RED


@pytest.mark.parametrize("overall_score", [40.0, 50.0, 59.999])
def test_overall_score_40_to_below_60_is_orange(overall_score: float) -> None:
    color_class = classify_candidate_score(make_score(overall_score=overall_score), within_operation_radius=True)

    assert color_class is ColorClass.ORANGE


@pytest.mark.parametrize("overall_score", [60.0, 70.0, 74.999])
def test_overall_score_60_to_below_75_is_yellow(overall_score: float) -> None:
    color_class = classify_candidate_score(make_score(overall_score=overall_score), within_operation_radius=True)

    assert color_class is ColorClass.YELLOW


@pytest.mark.parametrize("overall_score", [75.0, 90.0, 100.0])
def test_overall_score_at_least_75_and_los_clear_is_green(overall_score: float) -> None:
    color_class = classify_candidate_score(make_score(overall_score=overall_score), within_operation_radius=True)

    assert color_class is ColorClass.GREEN


@pytest.mark.parametrize("cell_id", ["", "   "])
def test_empty_cell_id_raises_classification_error(cell_id: str) -> None:
    with pytest.raises(ClassificationError, match="cell_id"):
        evaluate_launch_area_cell(
            cell_id=cell_id,
            candidate_score=make_score(),
            within_operation_radius=True,
        )


def test_candidate_score_type_error_raises_classification_error() -> None:
    with pytest.raises(ClassificationError, match="candidate_score"):
        classify_candidate_score("not-a-score", within_operation_radius=True)  # type: ignore[arg-type]


def test_within_operation_radius_type_error_raises_classification_error() -> None:
    with pytest.raises(ClassificationError, match="within_operation_radius"):
        classify_candidate_score(make_score(), within_operation_radius="true")  # type: ignore[arg-type]


def test_thresholds_type_error_raises_classification_error() -> None:
    with pytest.raises(ClassificationError, match="thresholds"):
        classify_candidate_score(
            make_score(),
            within_operation_radius=True,
            thresholds="default",  # type: ignore[arg-type]
        )


def test_launch_area_cell_evaluation_contains_required_fields() -> None:
    evaluation = evaluate_launch_area_cell(
        cell_id="cell_x+0000_y+0000",
        candidate_score=make_score(overall_score=90.0),
        within_operation_radius=True,
    )

    assert isinstance(evaluation, LaunchAreaCellEvaluation)
    assert evaluation.cell_id == "cell_x+0000_y+0000"
    assert evaluation.color_class is ColorClass.GREEN
    assert isinstance(evaluation.candidate_score, CandidateScore)
    assert evaluation.within_operation_radius is True
    assert "green" in evaluation.reason


def test_launch_area_cell_evaluation_dataclass_has_no_top5_or_ranking_output() -> None:
    field_names = {field.name for field in fields(LaunchAreaCellEvaluation)}

    prohibited_fields = {"rank", "ranking", "top_n", "top_5", "ranked_launch_sites"}
    assert field_names.isdisjoint(prohibited_fields)


def test_launch_area_cell_evaluation_has_no_required_link_metric_fields() -> None:
    field_names = {field.name for field in fields(LaunchAreaCellEvaluation)}

    assert "rssi" not in field_names
    assert "sinr" not in field_names
    assert "packet_loss" not in field_names


def test_classification_reuses_existing_color_class_enum() -> None:
    color_class = classify_candidate_score(make_score(), within_operation_radius=True)

    assert isinstance(color_class, ColorClass)
    assert color_class is ColorClass.GREEN


def test_classification_module_has_no_map_rendering_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/classification.py").read_text(encoding="utf-8")

    prohibited_imports = ("folium", "streamlit", "rasterio", "geopandas", "gdal", "osgeo")
    lowered = module_text.lower()
    for prohibited_import in prohibited_imports:
        assert prohibited_import not in lowered


def test_classification_reason_for_excluded() -> None:
    evaluation = evaluate_launch_area_cell(
        cell_id="cell_x+0001_y+0001",
        candidate_score=make_score(),
        within_operation_radius=False,
    )

    assert evaluation.color_class is ColorClass.EXCLUDED
    assert "outside operating radius" in evaluation.reason
