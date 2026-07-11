"""Candidate source-zone output metadata scaffold.

This module converts Task 020C candidate source-zone assignments into user-facing
candidate output metadata records. User-facing coordinates are represented by
``candidate_cell_mgrs`` strings supplied by the caller. The module does not perform
MGRS conversion, read raster files, compute scores, render maps, or perform
field-outcome validation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .candidate_source_zones import (
    CandidateSourceZoneAssignment,
    CandidateSourceZoneRecord,
)
from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    require_mgrs_external_coordinate_field,
)
from .source_zones import (
    SourceZoneSummary,
    TerrainSourceZone,
    is_source_sensitive_zone,
    summarize_source_zones,
)


class CandidateOutputSourceZoneError(ValueError):
    """Raised when candidate source-zone output records are invalid."""


@dataclass(frozen=True)
class CandidateSourceZoneOutputRecord:
    """User-facing candidate source-zone output metadata record."""

    cell_id: str
    candidate_cell_mgrs: str
    source_zone: TerrainSourceZone
    source_sensitive: bool
    source_zone_reason: str
    internal_debug_available: bool = False

    def __post_init__(self) -> None:
        require_mgrs_external_coordinate_field("candidate_cell_mgrs")
        _validate_non_empty_string("cell_id", self.cell_id)
        _validate_non_empty_string("candidate_cell_mgrs", self.candidate_cell_mgrs)
        _validate_source_zone(self.source_zone)
        if not isinstance(self.source_sensitive, bool):
            raise CandidateOutputSourceZoneError("source_sensitive must be a bool.")
        expected_sensitive = is_source_sensitive_zone(self.source_zone)
        if self.source_sensitive != expected_sensitive:
            raise CandidateOutputSourceZoneError(
                "source_sensitive must match the record source_zone policy."
            )
        _validate_non_empty_string("source_zone_reason", self.source_zone_reason)
        if not isinstance(self.internal_debug_available, bool):
            raise CandidateOutputSourceZoneError("internal_debug_available must be a bool.")


@dataclass(frozen=True)
class CandidateSourceZoneOutputBundle:
    """Bundle of candidate source-zone output records and summary metadata."""

    records: tuple[CandidateSourceZoneOutputRecord, ...]
    source_zone_summary: SourceZoneSummary
    source_sensitive_count: int
    dominant_source_zone: TerrainSourceZone
    reason: str

    def __post_init__(self) -> None:
        _ensure_output_records(self.records)
        if not isinstance(self.source_zone_summary, SourceZoneSummary):
            raise CandidateOutputSourceZoneError(
                "source_zone_summary must be a SourceZoneSummary value."
            )
        _validate_non_negative_int("source_sensitive_count", self.source_sensitive_count)
        actual_sensitive = sum(1 for record in self.records if record.source_sensitive)
        if self.source_sensitive_count != actual_sensitive:
            raise CandidateOutputSourceZoneError(
                "source_sensitive_count must match output records."
            )
        _validate_source_zone(self.dominant_source_zone)
        if self.dominant_source_zone is not self.source_zone_summary.dominant_zone:
            raise CandidateOutputSourceZoneError(
                "dominant_source_zone must match source_zone_summary.dominant_zone."
            )
        _validate_non_empty_string("reason", self.reason)


def build_candidate_source_zone_output_records(
    assignment: CandidateSourceZoneAssignment,
    candidate_cell_mgrs_by_cell_id: Mapping[str, str],
) -> CandidateSourceZoneOutputBundle:
    """Build MGRS-based candidate source-zone output metadata records."""

    if not isinstance(assignment, CandidateSourceZoneAssignment):
        raise CandidateOutputSourceZoneError(
            "assignment must be a CandidateSourceZoneAssignment value."
        )
    if not isinstance(candidate_cell_mgrs_by_cell_id, Mapping):
        raise CandidateOutputSourceZoneError(
            "candidate_cell_mgrs_by_cell_id must be a mapping."
        )
    require_mgrs_external_coordinate_field("candidate_cell_mgrs")

    output_records: list[CandidateSourceZoneOutputRecord] = []
    for assignment_record in assignment.records:
        _validate_assignment_record(assignment_record)
        if assignment_record.cell_id not in candidate_cell_mgrs_by_cell_id:
            raise CandidateOutputSourceZoneError(
                f"missing candidate_cell_mgrs for cell_id={assignment_record.cell_id}."
            )
        candidate_cell_mgrs = candidate_cell_mgrs_by_cell_id[assignment_record.cell_id]
        output_records.append(
            CandidateSourceZoneOutputRecord(
                cell_id=assignment_record.cell_id,
                candidate_cell_mgrs=candidate_cell_mgrs,
                source_zone=assignment_record.source_zone,
                source_sensitive=is_source_sensitive_zone(assignment_record.source_zone),
                source_zone_reason=assignment_record.source_zone_reason,
                internal_debug_available=True,
            )
        )

    summary = summarize_source_zones(tuple(record.source_zone for record in output_records))
    return CandidateSourceZoneOutputBundle(
        records=tuple(output_records),
        source_zone_summary=summary,
        source_sensitive_count=sum(1 for record in output_records if record.source_sensitive),
        dominant_source_zone=summary.dominant_zone,
        reason=f"Candidate source-zone output metadata built with candidate_cell_mgrs: {summary.reason}",
    )


def summarize_candidate_source_zone_outputs(
    bundle: CandidateSourceZoneOutputBundle,
) -> dict[str, int | str | bool]:
    """Return summary fields for candidate source-zone output metadata."""

    if not isinstance(bundle, CandidateSourceZoneOutputBundle):
        raise CandidateOutputSourceZoneError(
            "bundle must be a CandidateSourceZoneOutputBundle value."
        )
    summary = bundle.source_zone_summary
    return {
        "candidate_source_zone_output_record_count": len(bundle.records),
        "candidate_source_zone_user_coordinate_field": "candidate_cell_mgrs",
        "external_coordinate_format": EXTERNAL_COORDINATE_FORMAT,
        "esa_candidate_source_zone_output_count": summary.esa_derived_count,
        "wms_gap_filled_candidate_source_zone_output_count": summary.wms_gap_filled_count,
        "dem_only_fallback_candidate_source_zone_output_count": summary.dem_only_fallback_count,
        "mixed_boundary_candidate_source_zone_output_count": summary.mixed_boundary_count,
        "source_sensitive_candidate_source_zone_output_count": bundle.source_sensitive_count,
        "candidate_source_zone_output_source_sensitive": summary.source_sensitive,
        "candidate_source_zone_output_dominant_zone": bundle.dominant_source_zone.value,
        "candidate_source_zone_output_reason": bundle.reason,
        "internal_debug_available_candidate_count": sum(
            1 for record in bundle.records if record.internal_debug_available
        ),
    }


def _ensure_output_records(
    records: Sequence[CandidateSourceZoneOutputRecord],
) -> tuple[CandidateSourceZoneOutputRecord, ...]:
    if not records:
        raise CandidateOutputSourceZoneError("records must not be empty.")
    resolved_records = tuple(records)
    for record in resolved_records:
        if not isinstance(record, CandidateSourceZoneOutputRecord):
            raise CandidateOutputSourceZoneError(
                "all records must be CandidateSourceZoneOutputRecord values."
            )
    return resolved_records


def _validate_assignment_record(record: CandidateSourceZoneRecord) -> None:
    if not isinstance(record, CandidateSourceZoneRecord):
        raise CandidateOutputSourceZoneError(
            "all assignment records must be CandidateSourceZoneRecord values."
        )


def _validate_source_zone(source_zone: TerrainSourceZone) -> None:
    if not isinstance(source_zone, TerrainSourceZone):
        raise CandidateOutputSourceZoneError("source_zone must be a TerrainSourceZone value.")


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateOutputSourceZoneError(f"{field_name} must be a non-empty string.")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateOutputSourceZoneError(f"{field_name} must be an integer.")
    if value < 0:
        raise CandidateOutputSourceZoneError(f"{field_name} must be non-negative.")
