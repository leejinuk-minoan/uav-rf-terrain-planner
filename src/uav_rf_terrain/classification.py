"""Pure Python color classification for launch-area candidate cells.

This module converts Task 007 ``CandidateScore`` values into color classes for a
future launch-area map. It does not render maps, create Folium/Streamlit UI, load
real DEM/DSM files, generate GeoTIFFs, plan routes, create Top-N launch-site output,
or validate real communication quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .schemas import ColorClass
from .scoring import CandidateScore

_THRESHOLD_TOLERANCE: float = 1e-9


class ClassificationError(ValueError):
    """Raised when color classification inputs or thresholds are invalid."""


@dataclass(frozen=True)
class ColorClassificationThresholds:
    """MVP heuristic thresholds for candidate-cell color classification.

    These thresholds are offline proxy visualization thresholds. They are not verified
    communication-success probabilities or real link-quality guarantees.
    """

    green_min_overall_score: float = 75.0
    yellow_min_overall_score: float = 60.0
    orange_min_overall_score: float = 40.0

    def validate(self) -> None:
        """Validate finite, normalized ordering for color thresholds."""

        for field_name, value in (
            ("green_min_overall_score", self.green_min_overall_score),
            ("yellow_min_overall_score", self.yellow_min_overall_score),
            ("orange_min_overall_score", self.orange_min_overall_score),
        ):
            if not isfinite(value):
                raise ClassificationError(f"{field_name} must be finite.")
            if value < 0.0 or value > 100.0:
                raise ClassificationError(f"{field_name} must be within [0, 100].")

        if self.orange_min_overall_score - self.yellow_min_overall_score > _THRESHOLD_TOLERANCE:
            raise ClassificationError(
                "orange_min_overall_score must be less than or equal to yellow_min_overall_score."
            )
        if self.yellow_min_overall_score - self.green_min_overall_score > _THRESHOLD_TOLERANCE:
            raise ClassificationError(
                "yellow_min_overall_score must be less than or equal to green_min_overall_score."
            )


@dataclass(frozen=True)
class LaunchAreaCellEvaluation:
    """Color-classification result for one launch-area candidate cell.

    This structure is intended as data for a future color launch-area map. It is not a
    map layer, not a rendered UI object, and not a ranked Top-N launch-site output.
    """

    cell_id: str
    color_class: ColorClass
    candidate_score: CandidateScore
    within_operation_radius: bool
    reason: str


def classify_candidate_score(
    candidate_score: CandidateScore,
    *,
    within_operation_radius: bool,
    thresholds: ColorClassificationThresholds = ColorClassificationThresholds(),
) -> ColorClass:
    """Classify a candidate score into an existing ``ColorClass`` value."""

    _validate_classification_inputs(
        candidate_score=candidate_score,
        within_operation_radius=within_operation_radius,
        thresholds=thresholds,
    )

    if not within_operation_radius:
        return ColorClass.EXCLUDED
    if candidate_score.dsm_los_score == 0.0:
        return ColorClass.RED
    if candidate_score.shielding_stability_score == 0.0:
        return ColorClass.RED
    if candidate_score.overall_score < thresholds.orange_min_overall_score:
        return ColorClass.RED
    if candidate_score.overall_score < thresholds.yellow_min_overall_score:
        return ColorClass.ORANGE
    if candidate_score.overall_score < thresholds.green_min_overall_score:
        return ColorClass.YELLOW
    return ColorClass.GREEN


def evaluate_launch_area_cell(
    *,
    cell_id: str,
    candidate_score: CandidateScore,
    within_operation_radius: bool,
    thresholds: ColorClassificationThresholds = ColorClassificationThresholds(),
) -> LaunchAreaCellEvaluation:
    """Return a color-class evaluation result for one candidate launch cell."""

    if not isinstance(cell_id, str) or not cell_id.strip():
        raise ClassificationError("cell_id must be a non-empty string.")

    color_class = classify_candidate_score(
        candidate_score,
        within_operation_radius=within_operation_radius,
        thresholds=thresholds,
    )
    return LaunchAreaCellEvaluation(
        cell_id=cell_id,
        color_class=color_class,
        candidate_score=candidate_score,
        within_operation_radius=within_operation_radius,
        reason=classification_reason(
            candidate_score=candidate_score,
            within_operation_radius=within_operation_radius,
            color_class=color_class,
            thresholds=thresholds,
        ),
    )


def classification_reason(
    *,
    candidate_score: CandidateScore,
    within_operation_radius: bool,
    color_class: ColorClass | None = None,
    thresholds: ColorClassificationThresholds = ColorClassificationThresholds(),
) -> str:
    """Return a concise reason string for the selected color class."""

    _validate_classification_inputs(
        candidate_score=candidate_score,
        within_operation_radius=within_operation_radius,
        thresholds=thresholds,
    )

    resolved_color_class = color_class or classify_candidate_score(
        candidate_score,
        within_operation_radius=within_operation_radius,
        thresholds=thresholds,
    )

    if resolved_color_class is ColorClass.EXCLUDED:
        return "excluded: outside operating radius"
    if candidate_score.dsm_los_score == 0.0:
        return "red: DSM LOS score is 0"
    if candidate_score.shielding_stability_score == 0.0:
        return "red: shielding stability score is 0"
    if resolved_color_class is ColorClass.RED:
        return f"red: overall score below {thresholds.orange_min_overall_score:g}"
    if resolved_color_class is ColorClass.ORANGE:
        return (
            "orange: overall score between "
            f"{thresholds.orange_min_overall_score:g} and {thresholds.yellow_min_overall_score:g}"
        )
    if resolved_color_class is ColorClass.YELLOW:
        return (
            "yellow: overall score between "
            f"{thresholds.yellow_min_overall_score:g} and {thresholds.green_min_overall_score:g}"
        )
    return f"green: overall score at least {thresholds.green_min_overall_score:g} with DSM LOS clear"


def _validate_classification_inputs(
    *,
    candidate_score: CandidateScore,
    within_operation_radius: bool,
    thresholds: ColorClassificationThresholds,
) -> None:
    if not isinstance(candidate_score, CandidateScore):
        raise ClassificationError("candidate_score must be a CandidateScore instance.")
    if not isinstance(within_operation_radius, bool):
        raise ClassificationError("within_operation_radius must be a bool.")
    if not isinstance(thresholds, ColorClassificationThresholds):
        raise ClassificationError(
            "thresholds must be a ColorClassificationThresholds instance."
        )
    thresholds.validate()
