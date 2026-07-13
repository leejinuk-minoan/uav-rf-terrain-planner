"""Typed projection of Fresnel diagnostics for candidate preview outputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from numbers import Real

from .fresnel import FresnelAnalysis


class CandidateFresnelDiagnosticsError(ValueError):
    """Raised when a candidate diagnostic projection is incomplete or invalid."""


DIAGNOSTIC_FIELD_ORDER = (
        "average_fresnel_score",
        "worst_obstacle_score",
        "dominant_obstacle_distance_from_start_m",
        "dominant_obstacle_dsm_msl",
        "dominant_obstacle_los_msl",
        "dominant_obstacle_clearance_m",
        "dominant_obstacle_clearance_ratio",
        "dominant_obstacle_fresnel_radius_m",
        "dominant_obstacle_nu",
        "dominant_obstacle_diffraction_loss_db",
)
DIAGNOSTIC_FIELD_NAMES = frozenset(DIAGNOSTIC_FIELD_ORDER)


@dataclass(frozen=True)
class CandidateFresnelDiagnostics:
    average_fresnel_score: float
    worst_obstacle_score: float | None
    dominant_obstacle_distance_from_start_m: float | None
    dominant_obstacle_dsm_msl: float | None
    dominant_obstacle_los_msl: float | None
    dominant_obstacle_clearance_m: float | None
    dominant_obstacle_clearance_ratio: float | None
    dominant_obstacle_fresnel_radius_m: float | None
    dominant_obstacle_nu: float | None
    dominant_obstacle_diffraction_loss_db: float | None

    def __post_init__(self) -> None:
        _require_finite("average_fresnel_score", self.average_fresnel_score)
        values = self.to_flat_dict()
        nullable = [
            values[name]
            for name in DIAGNOSTIC_FIELD_ORDER
            if name != "average_fresnel_score"
        ]
        if all(value is None for value in nullable):
            return
        if any(value is None for value in nullable):
            raise CandidateFresnelDiagnosticsError(
                "obstacle diagnostic values must be all numeric or all absent."
            )
        for name, value in values.items():
            _require_finite(name, value)

    @classmethod
    def no_eligible(cls, *, average_fresnel_score: float) -> CandidateFresnelDiagnostics:
        return cls(average_fresnel_score, None, None, None, None, None, None, None, None, None)

    def to_flat_dict(self) -> dict[str, float | None]:
        return {name: getattr(self, name) for name in DIAGNOSTIC_FIELD_ORDER}


def candidate_fresnel_diagnostics_from_analysis(
    analysis: FresnelAnalysis,
) -> CandidateFresnelDiagnostics:
    if not isinstance(analysis, FresnelAnalysis):
        raise CandidateFresnelDiagnosticsError("analysis must be FresnelAnalysis.")
    obstacle = analysis.dominant_obstacle
    if obstacle is None:
        return CandidateFresnelDiagnostics.no_eligible(
            average_fresnel_score=analysis.average_fresnel_score
        )
    return CandidateFresnelDiagnostics(
        average_fresnel_score=analysis.average_fresnel_score,
        worst_obstacle_score=analysis.worst_obstacle_score,
        dominant_obstacle_distance_from_start_m=obstacle.distance_from_start_m,
        dominant_obstacle_dsm_msl=obstacle.dsm_msl,
        dominant_obstacle_los_msl=obstacle.los_msl,
        dominant_obstacle_clearance_m=obstacle.clearance_m,
        dominant_obstacle_clearance_ratio=obstacle.clearance_ratio,
        dominant_obstacle_fresnel_radius_m=obstacle.fresnel_radius_m,
        dominant_obstacle_nu=obstacle.nu,
        dominant_obstacle_diffraction_loss_db=obstacle.diffraction_loss_db,
    )


def validate_flat_fresnel_diagnostics(record: Mapping[str, object]) -> str:
    if not isinstance(record, Mapping):
        raise CandidateFresnelDiagnosticsError("diagnostic record must be a mapping.")
    keys = set(record.keys())
    present = DIAGNOSTIC_FIELD_NAMES.intersection(keys)
    if not present:
        return "legacy"
    if present != DIAGNOSTIC_FIELD_NAMES:
        raise CandidateFresnelDiagnosticsError("diagnostic fields must be all present or all absent.")
    values = {name: record[name] for name in DIAGNOSTIC_FIELD_ORDER}
    _require_finite("average_fresnel_score", values["average_fresnel_score"])
    nullable = [
        values[name]
        for name in DIAGNOSTIC_FIELD_ORDER
        if name != "average_fresnel_score"
    ]
    if all(value is None for value in nullable):
        return "no_eligible"
    if any(value is None for value in nullable):
        raise CandidateFresnelDiagnosticsError("diagnostic null values form an invalid mixed state.")
    for name in DIAGNOSTIC_FIELD_ORDER:
        _require_finite(name, values[name])
    return "eligible"


def _require_finite(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)):
        raise CandidateFresnelDiagnosticsError(f"{name} must be finite numeric.")
