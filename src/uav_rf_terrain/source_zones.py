"""Source-zone metadata for offline terrain-derived output records.

Source-zone flags describe which terrain data source policy produced a candidate,
route cell, or waypoint record. They are interpretation metadata for synthetic and
future raster-backed analysis outputs. They do not read raster files, render maps,
or validate field outcomes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class SourceZoneError(ValueError):
    """Raised when source-zone inputs are invalid."""


class TerrainSourceZone(StrEnum):
    """Terrain source zones used by candidate, route, and waypoint outputs."""

    ESA_DERIVED = "esa_derived"
    WMS_GAP_FILLED = "wms_gap_filled"
    DEM_ONLY_FALLBACK = "dem_only_fallback"
    MIXED_BOUNDARY = "mixed_boundary"


@dataclass(frozen=True)
class SourceZoneSummary:
    """Counts and source-sensitivity summary for a group of source zones."""

    esa_derived_count: int
    wms_gap_filled_count: int
    dem_only_fallback_count: int
    mixed_boundary_count: int
    dominant_zone: TerrainSourceZone
    source_sensitive: bool
    reason: str

    def __post_init__(self) -> None:
        _validate_non_negative_int("esa_derived_count", self.esa_derived_count)
        _validate_non_negative_int("wms_gap_filled_count", self.wms_gap_filled_count)
        _validate_non_negative_int("dem_only_fallback_count", self.dem_only_fallback_count)
        _validate_non_negative_int("mixed_boundary_count", self.mixed_boundary_count)
        if not isinstance(self.dominant_zone, TerrainSourceZone):
            raise SourceZoneError("dominant_zone must be a TerrainSourceZone value.")
        if not isinstance(self.source_sensitive, bool):
            raise SourceZoneError("source_sensitive must be a bool.")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise SourceZoneError("reason must be a non-empty string.")
        total_count = (
            self.esa_derived_count
            + self.wms_gap_filled_count
            + self.dem_only_fallback_count
            + self.mixed_boundary_count
        )
        if total_count <= 0:
            raise SourceZoneError("source-zone summary must include at least one zone.")


_SOURCE_ZONE_PRIORITY: tuple[TerrainSourceZone, ...] = (
    TerrainSourceZone.MIXED_BOUNDARY,
    TerrainSourceZone.DEM_ONLY_FALLBACK,
    TerrainSourceZone.WMS_GAP_FILLED,
    TerrainSourceZone.ESA_DERIVED,
)


def summarize_source_zones(zones: Sequence[TerrainSourceZone]) -> SourceZoneSummary:
    """Summarize source-zone counts and whether the record is source-sensitive."""

    resolved_zones = _ensure_source_zones(zones)
    counts = Counter(resolved_zones)
    dominant_zone = _dominant_zone(counts)
    unique_zones = set(resolved_zones)
    source_sensitive = (
        len(unique_zones) > 1
        or any(is_source_sensitive_zone(zone) for zone in resolved_zones)
    )
    return SourceZoneSummary(
        esa_derived_count=counts[TerrainSourceZone.ESA_DERIVED],
        wms_gap_filled_count=counts[TerrainSourceZone.WMS_GAP_FILLED],
        dem_only_fallback_count=counts[TerrainSourceZone.DEM_ONLY_FALLBACK],
        mixed_boundary_count=counts[TerrainSourceZone.MIXED_BOUNDARY],
        dominant_zone=dominant_zone,
        source_sensitive=source_sensitive,
        reason=_source_zone_reason(unique_zones=unique_zones, source_sensitive=source_sensitive),
    )


def is_source_sensitive_zone(zone: TerrainSourceZone) -> bool:
    """Return whether one zone should be flagged as source-sensitive."""

    _validate_source_zone(zone)
    return zone is not TerrainSourceZone.ESA_DERIVED


def _dominant_zone(counts: Counter[TerrainSourceZone]) -> TerrainSourceZone:
    return max(
        _SOURCE_ZONE_PRIORITY,
        key=lambda zone: (counts[zone], -_SOURCE_ZONE_PRIORITY.index(zone)),
    )


def _source_zone_reason(
    *,
    unique_zones: set[TerrainSourceZone],
    source_sensitive: bool,
) -> str:
    if not source_sensitive:
        return "ESA-derived source zone only."
    if len(unique_zones) > 1:
        return "Multiple terrain source zones are present."
    zone = next(iter(unique_zones))
    if zone is TerrainSourceZone.WMS_GAP_FILLED:
        return "WMS gap-filled source zone present."
    if zone is TerrainSourceZone.DEM_ONLY_FALLBACK:
        return "DEM-only fallback source zone present."
    return "Mixed-boundary source zone present."


def _ensure_source_zones(zones: Sequence[TerrainSourceZone]) -> tuple[TerrainSourceZone, ...]:
    if not zones:
        raise SourceZoneError("zones must not be empty.")
    resolved_zones = tuple(zones)
    for zone in resolved_zones:
        _validate_source_zone(zone)
    return resolved_zones


def _validate_source_zone(zone: TerrainSourceZone) -> None:
    if not isinstance(zone, TerrainSourceZone):
        raise SourceZoneError("source zone must be a TerrainSourceZone value.")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceZoneError(f"{field_name} must be an integer.")
    if value < 0:
        raise SourceZoneError(f"{field_name} must be non-negative.")
