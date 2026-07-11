"""Coordinate I/O policy guardrails for external MGRS boundaries.

This module defines policy constants only. It does not perform coordinate conversion,
load terrain files, render maps, or change scoring behavior.
"""

from __future__ import annotations

from enum import StrEnum


class CoordinateIoPolicyError(ValueError):
    """Raised when a coordinate field violates external I/O policy."""


class ExternalCoordinateFormat(StrEnum):
    """Supported external coordinate format."""

    MGRS = "MGRS"


EXTERNAL_COORDINATE_FORMAT = ExternalCoordinateFormat.MGRS.value

INTERNAL_COORDINATE_FIELD_NAMES = frozenset(
    {
        "x_m",
        "y_m",
        "row",
        "col",
        "epsg5179_x_m",
        "epsg5179_y_m",
        "wgs84_lat",
        "wgs84_lon",
        "local_x_m",
        "local_y_m",
        "raster_row",
        "raster_col",
    }
)

USER_FACING_MGRS_FIELD_NAMES = frozenset(
    {
        "target_mgrs",
        "launch_site_mgrs",
        "waypoint_mgrs",
        "candidate_cell_mgrs",
        "selected_route_waypoint_mgrs",
        "route_start_mgrs",
        "route_end_mgrs",
    }
)


def is_internal_coordinate_field(name: str) -> bool:
    """Return whether ``name`` is an internal/debug coordinate field."""

    resolved_name = _normalized_field_name(name)
    return resolved_name in INTERNAL_COORDINATE_FIELD_NAMES


def is_user_facing_mgrs_field(name: str) -> bool:
    """Return whether ``name`` is an approved user-facing MGRS coordinate field."""

    resolved_name = _normalized_field_name(name)
    return resolved_name in USER_FACING_MGRS_FIELD_NAMES


def require_mgrs_external_coordinate_field(name: str) -> None:
    """Require a user-facing coordinate field to use an approved MGRS name."""

    resolved_name = _normalized_field_name(name)
    if is_user_facing_mgrs_field(resolved_name):
        return
    if is_internal_coordinate_field(resolved_name):
        raise CoordinateIoPolicyError(
            f"{resolved_name} is an internal/debug coordinate field, not an external MGRS field."
        )
    raise CoordinateIoPolicyError(
        f"{resolved_name} is not an approved external MGRS coordinate field."
    )


def _normalized_field_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise CoordinateIoPolicyError("coordinate field name must be a non-empty string.")
    return name.strip().lower()
