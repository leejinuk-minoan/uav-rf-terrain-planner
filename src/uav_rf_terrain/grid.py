"""Candidate launch-area grid helpers for Task 002.

The grid produced here is a color-map-oriented cell structure. It does not rank Top
5 launch sites and does not perform DSM, LOS, Fresnel, or final scoring analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from .coordinates import LocalPoint, distance_2d_m, distance_3d_m, local_offset_point


@dataclass(frozen=True)
class CandidateGridConfig:
    """Configuration for local candidate-cell generation around a target point.

    Args:
        radius_m: Operating radius in meters.
        spacing_m: Grid spacing in meters.
        include_center: Whether to include the center point as a candidate cell.
        include_excluded: Whether to retain cells outside the operating radius with
            ``within_operation_radius=False`` for later gray/transparent map layers.
    """

    radius_m: float
    spacing_m: float
    include_center: bool = True
    include_excluded: bool = True

    def __post_init__(self) -> None:
        if self.radius_m <= 0:
            raise ValueError("radius_m must be positive.")
        if self.spacing_m <= 0:
            raise ValueError("spacing_m must be positive.")
        if self.spacing_m > self.radius_m:
            raise ValueError("spacing_m should be less than or equal to radius_m.")


@dataclass(frozen=True)
class CandidateCell:
    """Candidate launch-area cell for later color-map scoring.

    This structure is intentionally grid/cell oriented. It is not a ranked output and
    does not include Top-N recommendation fields.
    """

    cell_id: str
    point: LocalPoint
    distance_2d_m: float
    distance_3d_m: float
    within_operation_radius: bool


def generate_candidate_grid(
    center: LocalPoint,
    config: CandidateGridConfig,
) -> list[CandidateCell]:
    """Generate candidate cells in a square search window around ``center``.

    Candidates outside ``config.radius_m`` are marked as excluded candidates when
    ``include_excluded`` is true. This supports later color launch-area maps where
    out-of-radius cells can be displayed as gray/transparent cells.
    """

    cells: list[CandidateCell] = []
    steps = ceil(config.radius_m / config.spacing_m)

    for ix in range(-steps, steps + 1):
        for iy in range(-steps, steps + 1):
            if not config.include_center and ix == 0 and iy == 0:
                continue

            candidate = local_offset_point(
                origin=center,
                dx_m=ix * config.spacing_m,
                dy_m=iy * config.spacing_m,
            )
            distance_2d = distance_2d_m(center, candidate)
            distance_3d = distance_3d_m(center, candidate)
            within_operation_radius = distance_3d <= config.radius_m

            if not within_operation_radius and not config.include_excluded:
                continue

            cells.append(
                CandidateCell(
                    cell_id=_candidate_cell_id(ix=ix, iy=iy),
                    point=candidate,
                    distance_2d_m=distance_2d,
                    distance_3d_m=distance_3d,
                    within_operation_radius=within_operation_radius,
                )
            )

    return cells


def filter_within_operation_radius(cells: list[CandidateCell]) -> list[CandidateCell]:
    """Return only candidate cells within the configured operating radius."""

    return [cell for cell in cells if cell.within_operation_radius]


def _candidate_cell_id(ix: int, iy: int) -> str:
    """Return a stable candidate cell identifier based on grid offsets."""

    return f"cell_x{ix:+04d}_y{iy:+04d}"
