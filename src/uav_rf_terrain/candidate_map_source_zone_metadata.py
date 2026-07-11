"""Candidate source-zone bridge for future map-ready metadata.

This module converts Task 021A ``CandidateSourceZoneOutputBundle`` records into
rendering-independent map-ready property dictionaries. User-facing candidate
coordinates remain ``candidate_cell_mgrs`` values supplied upstream. The module
performs no MGRS conversion, raster reading, score calculation, visual rendering,
or operational validation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .candidate_output_source_zones import (
    CandidateSourceZoneOutputBundle,
    CandidateSourceZoneOutputRecord,
)
from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    require_mgrs_external_coordinate_field,
)
from .source_zones import SourceZoneSummary, TerrainSourceZone, is_source_sensitive_zone

_USER_COORDINATE_FIELD = "candidate_cell_mgrs"


class CandidateMapSourceZoneMetadataError(ValueError):
    """Raised when candidate map source-zone metadata is invalid."""


@dataclass(frozen=True)
class CandidateMapSourceZoneProperties:
    """Rendering-independent candidate map property metadata."""

    cell_id: str
    candidate_cell_mgrs: str
    external_coordinate_format: str
    source_zone: TerrainSourceZone
    source_sensitive: bool
    source_zone_reason: str
    user_coordinate_field: str = _USER_COORDINATE_FIELD
    internal_debug_available: bool = False

    def __post_init__(self) -> None:
        require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)
        _validate_non_empty_string("cell_id", self.cell_id)
        _validate_non_empty_string("candidate_cell_mgrs", self.candidate_cell_mgrs)
        if self.external_coordinate_format != EXTERNAL_COORDINATE_FORMAT:
            raise CandidateMapSourceZoneMetadataError(
                "external_coordinate_format must match the project external coordinate policy."
            )
        if self.user_coordinate_field != _USER_COORDINATE_FIELD:
            raise CandidateMapSourceZoneMetadataError(
                "user_coordinate_field must be candidate_cell_mgrs."
            )
        _validate_source_zone(self.source_zone)
        if not isinstance(self.source_sensitive, bool):
            raise CandidateMapSourceZoneMetadataError("source_sensitive must be a bool.")
        expected_sensitive = is_source_sensitive_zone(self.source_zone)
        if self.source_sensitive != expected_sensitive:
            raise CandidateMapSourceZoneMetadataError(
                "source_sensitive must match the source_zone policy."
            )
        _validate_non_empty_string("source_zone_reason", self.source_zone_reason)
        if not isinstance(self.internal_debug_available, bool):
            raise CandidateMapSourceZoneMetadataError(
                "internal_debug_available must be a bool."
            )

    def to_map_properties(self) -> dict[str, str | bool]:
        """Return future map-ready properties without internal coordinate fields."""

        return {
            "cell_id": self.cell_id,
            "candidate_cell_mgrs": self.candidate_cell_mgrs,
            "external_coordinate_format": self.external_coordinate_format,
            "user_coordinate_field": self.user_coordinate_field,
            "source_zone": self.source_zone.value,
            "source_sensitive": self.source_sensitive,
            "source_zone_reason": self.source_zone_reason,
            "internal_debug_available": self.internal_debug_available,
        }


@dataclass(frozen=True)
class CandidateMapSourceZoneMetadataBundle:
    """Bundle of candidate map source-zone metadata properties."""

    properties: tuple[CandidateMapSourceZoneProperties, ...]
    source_zone_summary: SourceZoneSummary
    source_sensitive_count: int
    dominant_source_zone: TerrainSourceZone
    reason: str

    def __post_init__(self) -> None:
        _ensure_properties(self.properties)
        if not isinstance(self.source_zone_summary, SourceZoneSummary):
            raise CandidateMapSourceZoneMetadataError(
                "source_zone_summary must be a SourceZoneSummary value."
            )
        _validate_non_negative_int("source_sensitive_count", self.source_sensitive_count)
        actual_sensitive = sum(1 for item in self.properties if item.source_sensitive)
        if self.source_sensitive_count != actual_sensitive:
            raise CandidateMapSourceZoneMetadataError(
                "source_sensitive_count must match metadata properties."
            )
        _validate_source_zone(self.dominant_source_zone)
        if self.dominant_source_zone is not self.source_zone_summary.dominant_zone:
            raise CandidateMapSourceZoneMetadataError(
                "dominant_source_zone must match source_zone_summary.dominant_zone."
            )
        _validate_non_empty_string("reason", self.reason)


def build_candidate_map_source_zone_properties(
    output_bundle: CandidateSourceZoneOutputBundle,
) -> CandidateMapSourceZoneMetadataBundle:
    """Convert candidate output source-zone records into map-ready properties."""

    if not isinstance(output_bundle, CandidateSourceZoneOutputBundle):
        raise CandidateMapSourceZoneMetadataError(
            "output_bundle must be a CandidateSourceZoneOutputBundle value."
        )
    require_mgrs_external_coordinate_field(_USER_COORDINATE_FIELD)

    properties: list[CandidateMapSourceZoneProperties] = []
    for output_record in output_bundle.records:
        _validate_output_record(output_record)
        properties.append(
            CandidateMapSourceZoneProperties(
                cell_id=output_record.cell_id,
                candidate_cell_mgrs=output_record.candidate_cell_mgrs,
                external_coordinate_format=EXTERNAL_COORDINATE_FORMAT,
                source_zone=output_record.source_zone,
                source_sensitive=output_record.source_sensitive,
                source_zone_reason=output_record.source_zone_reason,
                user_coordinate_field=_USER_COORDINATE_FIELD,
                internal_debug_available=output_record.internal_debug_available,
            )
        )

    return CandidateMapSourceZoneMetadataBundle(
        properties=tuple(properties),
        source_zone_summary=output_bundle.source_zone_summary,
        source_sensitive_count=output_bundle.source_sensitive_count,
        dominant_source_zone=output_bundle.dominant_source_zone,
        reason=(
            "Candidate source-zone output records converted to map-ready properties: "
            f"{output_bundle.reason}"
        ),
    )


def build_candidate_map_source_zone_properties_by_cell_id(
    metadata_bundle: CandidateMapSourceZoneMetadataBundle,
) -> dict[str, dict[str, str | bool]]:
    """Return map-ready properties keyed by candidate cell id."""

    if not isinstance(metadata_bundle, CandidateMapSourceZoneMetadataBundle):
        raise CandidateMapSourceZoneMetadataError(
            "metadata_bundle must be a CandidateMapSourceZoneMetadataBundle value."
        )
    properties_by_cell_id: dict[str, dict[str, str | bool]] = {}
    for item in metadata_bundle.properties:
        if item.cell_id in properties_by_cell_id:
            raise CandidateMapSourceZoneMetadataError(
                f"duplicate cell_id in map metadata: {item.cell_id}."
            )
        properties_by_cell_id[item.cell_id] = item.to_map_properties()
    return properties_by_cell_id


def summarize_candidate_map_source_zone_metadata(
    metadata_bundle: CandidateMapSourceZoneMetadataBundle,
) -> dict[str, int | str | bool]:
    """Return summary values for candidate map source-zone metadata."""

    if not isinstance(metadata_bundle, CandidateMapSourceZoneMetadataBundle):
        raise CandidateMapSourceZoneMetadataError(
            "metadata_bundle must be a CandidateMapSourceZoneMetadataBundle value."
        )
    summary = metadata_bundle.source_zone_summary
    return {
        "candidate_map_source_zone_metadata_count": len(metadata_bundle.properties),
        "candidate_map_source_zone_user_coordinate_field": _USER_COORDINATE_FIELD,
        "external_coordinate_format": EXTERNAL_COORDINATE_FORMAT,
        "esa_candidate_map_source_zone_count": summary.esa_derived_count,
        "wms_gap_filled_candidate_map_source_zone_count": summary.wms_gap_filled_count,
        "dem_only_fallback_candidate_map_source_zone_count": summary.dem_only_fallback_count,
        "mixed_boundary_candidate_map_source_zone_count": summary.mixed_boundary_count,
        "source_sensitive_candidate_map_source_zone_count": metadata_bundle.source_sensitive_count,
        "dominant_candidate_map_source_zone": metadata_bundle.dominant_source_zone.value,
        "candidate_map_source_zone_metadata_reason": metadata_bundle.reason,
    }


def _validate_output_record(record: CandidateSourceZoneOutputRecord) -> None:
    if not isinstance(record, CandidateSourceZoneOutputRecord):
        raise CandidateMapSourceZoneMetadataError(
            "all output records must be CandidateSourceZoneOutputRecord values."
        )


def _ensure_properties(
    properties: Sequence[CandidateMapSourceZoneProperties],
) -> tuple[CandidateMapSourceZoneProperties, ...]:
    if not properties:
        raise CandidateMapSourceZoneMetadataError("properties must not be empty.")
    resolved = tuple(properties)
    for item in resolved:
        if not isinstance(item, CandidateMapSourceZoneProperties):
            raise CandidateMapSourceZoneMetadataError(
                "all properties must be CandidateMapSourceZoneProperties values."
            )
    return resolved


def _validate_source_zone(source_zone: TerrainSourceZone) -> None:
    if not isinstance(source_zone, TerrainSourceZone):
        raise CandidateMapSourceZoneMetadataError(
            "source_zone must be a TerrainSourceZone value."
        )


def _validate_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CandidateMapSourceZoneMetadataError(
            f"{field_name} must be a non-empty string."
        )


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CandidateMapSourceZoneMetadataError(f"{field_name} must be an integer.")
    if value < 0:
        raise CandidateMapSourceZoneMetadataError(f"{field_name} must be non-negative.")
