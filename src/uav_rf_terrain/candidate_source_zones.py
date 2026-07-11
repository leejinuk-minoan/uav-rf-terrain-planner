"""Candidate-grid source-zone assignment scaffold.

This module connects candidate-grid cells to a source-zone provider. It is a pure
Python assignment layer for interpretation metadata. It does not read raster files,
run local GIS classifiers, compute candidate scores, render maps, or validate field
outcomes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Protocol

from .grid import CandidateCell
from .source_zones import (
    SourceZoneSummary,
    TerrainSourceZone,
    is_source_sensitive_zone,
    summarize_source_zones,
)


class CandidateSourceZoneError(ValueError):
    """Raised when candidate source-zone assignment inputs or outputs are invalid."""


class SourceZonePointProvider(Protocol):
    """Protocol for point-based source-zone providers.

    Later local tasks can adapt ``LocalSourceZoneRasterClassifier`` with a callable
    such as ``lambda x, y: classifier.sample_point(x, y).output_source_zone``.
    """

    def __call__(self, x_m: float, y_m: float) -> TerrainSourceZone:
        """Return a source zone for one projected candidate point."""


@dataclass(frozen=True)
class CandidateSourceZoneRecord:
    """Source-zone assignment for one candidate-grid cell."""

    cell_id: str
    x_m: float
    y_m: float
    source_zone: TerrainSourceZone
    source_sensitive: bool
    source_zone_reason: str

    def __post_init__(self) -> None:
        _validate_non_empty_string("cell_id", self.cell_id)
        _validate_finite("x_m", self.x_m)
        _validate_finite("y_m", self.y_m)
        _validate_source_zone(self.source_zone)
        if not isinstance(self.source_sensitive, bool):
            raise CandidateSourceZoneError("source_sensitive must be a bool.")
        _validate_non_empty_string("source_zone_reason", self.source_zone_reason)


@dataclass(frozen=True)
class CandidateSourceZoneAssignment:
    """Source-zone assignment result for a set of candidate-grid cells."""

    records: tuple[CandidateSourceZoneRecord, ...]
    source_zone_summary: SourceZoneSummary
    source_sensitive_count: int
    assignment_radius_cells: int | None
    reason: str

    def __post_init__(self) -> None:
        _ensure_records(self.records)
        if not isinstance(self.source_zone_summary, SourceZoneSummary):
            raise CandidateSourceZoneError("source_zone_summary must be a SourceZoneSummary value.")
        _validate_non_negative_int("source_sensitive_count", self.source_sensitive_count)
        if self.source_sensitive_count != sum(1 for record in self.records if record.source_sensitive):
            raise CandidateSourceZoneError(
                "source_sensitive_count must match the assigned source-sensitive records."
            )
        _validate_assignment_radius(self.assignment_radius_cells)
        _validate_non_empty_string("reason", self.reason)


def assign_source_zones_to_candidate_cells(
    cells: Sequence[CandidateCell],
    source_zone_provider: SourceZonePointProvider,
    assignment_radius_cells: int | None = None,
) -> CandidateSourceZoneAssignment:
    """Assign source-zone flags to candidate-grid cells using a point provider."""

    resolved_cells = _ensure_candidate_cells(cells)
    _validate_assignment_radius(assignment_radius_cells)
    if not callable(source_zone_provider):
        raise CandidateSourceZoneError("source_zone_provider must be callable.")

    records: list[CandidateSourceZoneRecord] = []
    for cell in resolved_cells:
        x_m = _validate_finite("cell.point.x_m", cell.point.x_m)
        y_m = _validate_finite("cell.point.y_m", cell.point.y_m)
        try:
            source_zone = source_zone_provider(x_m, y_m)
        except Exception as exc:  # noqa: BLE001 - preserve provider error context for caller.
            raise CandidateSourceZoneError(
                f"source_zone_provider failed for cell_id={cell.cell_id}: {exc}"
            ) from exc
        _validate_source_zone(source_zone)
        records.append(
            CandidateSourceZoneRecord(
                cell_id=cell.cell_id,
                x_m=x_m,
                y_m=y_m,
                source_zone=source_zone,
                source_sensitive=is_source_sensitive_zone(source_zone),
                source_zone_reason=_record_reason(source_zone),
            )
        )

    summary = summarize_source_zones(tuple(record.source_zone for record in records))
    return CandidateSourceZoneAssignment(
        records=tuple(records),
        source_zone_summary=summary,
        source_sensitive_count=sum(1 for record in records if record.source_sensitive),
        assignment_radius_cells=assignment_radius_cells,
        reason=f"Candidate source-zone assignment completed: {summary.reason}",
    )


def summarize_candidate_source_zone_assignment(
    assignment: CandidateSourceZoneAssignment,
) -> dict[str, int | str | bool | None]:
    """Return source-zone assignment summary fields for reports and later UI cards."""

    if not isinstance(assignment, CandidateSourceZoneAssignment):
        raise CandidateSourceZoneError(
            "assignment must be a CandidateSourceZoneAssignment value."
        )
    summary = assignment.source_zone_summary
    return {
        "candidate_source_zone_record_count": len(assignment.records),
        "esa_candidate_source_zone_count": summary.esa_derived_count,
        "wms_gap_filled_candidate_source_zone_count": summary.wms_gap_filled_count,
        "dem_only_fallback_candidate_source_zone_count": summary.dem_only_fallback_count,
        "mixed_boundary_candidate_source_zone_count": summary.mixed_boundary_count,
        "source_sensitive_candidate_source_zone_count": assignment.source_sensitive_count,
        "candidate_source_zone_dominant_zone": summary.dominant_zone.value,
        "candidate_source_zone_source_sensitive": summary.source_sensitive,
        "candidate_source_zone_assignment_radius_cells": assignment.assignment_radius_cells,
        "candidate_source_zone_reason": assignment.reason,
    }


def _ensure_candidate_cells(cells: Sequence[CandidateCell]) -> tuple[CandidateCell, ...]:
    if not cells:
        raise CandidateSourceZoneError("cells must not be empty.")
    resolved_cells = tuple(cells)
    for cell in resolved_cells:
        if not isinstance(cell, CandidateCell):
            raise CandidateSourceZoneError("all cells must be CandidateCell values.")
        _validate_non_empty_string("cell_id", cell.cell_id)
        _validate_finite("cell.point.x_m", cell.point.x_m)
        _validate_finite("cell.point.y_m", cell.point.y_m)
    return resolved_cells


def _ensure_records(
    records: tuple[CandidateSourceZoneRecord, ...]
) -> tuple[CandidateSourceZoneRecord, ...]:
    if not records:
        raise CandidateSourceZoneError("records must not be empty.")
    for record in records:
        if not isinstance(record, CandidateSourceZoneRecord):
            raise CandidateSourceZoneError("all records must be CandidateSourceZoneRecord values.")
    return records


def _record_reason(source_zone: TerrainSourceZone) -> str:
    if source_zone is TerrainSourceZone.ESA_DERIVED:
        return "ESA-derived candidate source zone."
    if source_zone is TerrainSourceZone.WMS_GAP_FILLED:
        return "WMS gap-filled candidate source zone."
    if source_zone is TerrainSourceZone.DEM_ONLY_FALLBACK:
        return "DEM-only fallback candidate source zone."
    return "Mixed-boundary candidate source zone."


def _validate_assignment_radius(value: int | None) -> None:
    if value is None:
        return
    _validate_non_negative_int("assignment_radius_cells", value)


def _validate_source_zone(source_zone: TerrainSourceZone) -> None:
    if not isinstance(source_zone, TerrainSourceZone):
        raise CandidateSourceZoneError("source_zone must be a TerrainSourceZone value.")


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateSourceZoneError(f"{field_name} must be a non-empty string.")


def _validate_finite(field_name: str, value: float) -> float:
    if not isfinite(value):
        raise CandidateSourceZoneError(f"{field_name} must be finite.")
    return value


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateSourceZoneError(f"{field_name} must be an integer.")
    if value < 0:
        raise CandidateSourceZoneError(f"{field_name} must be non-negative.")
