"""Coordinate structures and pure distance helpers for Task 002.

This module prepares local metric coordinates for later terrain and radio-risk
analysis. Optional MGRS conversion is intentionally isolated behind a runtime import
so the base package and CI do not require GIS dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import sqrt
from typing import Any


class MissingOptionalDependencyError(RuntimeError):
    """Raised when an optional coordinate-conversion dependency is unavailable."""


@dataclass(frozen=True)
class WGS84Point:
    """WGS84 coordinate placeholder for later projection workflows.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        altitude_m: Altitude in meters above the chosen vertical reference.
    """

    lat: float
    lon: float
    altitude_m: float = 0.0


@dataclass(frozen=True)
class LocalPoint:
    """Local metric point for pure Python distance and grid calculations.

    Args:
        x_m: Local x coordinate in meters.
        y_m: Local y coordinate in meters.
        z_m: Local z coordinate in meters.
    """

    x_m: float
    y_m: float
    z_m: float = 0.0


@dataclass(frozen=True)
class CoordinateReference:
    """Description of the coordinate reference used for analysis.

    Args:
        name: Human-readable CRS name.
        epsg: Optional EPSG code.
        description: Optional explanatory text.
    """

    name: str
    epsg: int | None = None
    description: str = ""


def distance_2d_m(a: LocalPoint, b: LocalPoint) -> float:
    """Return horizontal Euclidean distance between two local metric points."""

    dx_m = a.x_m - b.x_m
    dy_m = a.y_m - b.y_m
    return sqrt(dx_m * dx_m + dy_m * dy_m)


def distance_3d_m(a: LocalPoint, b: LocalPoint) -> float:
    """Return 3D Euclidean distance between two local metric points."""

    dx_m = a.x_m - b.x_m
    dy_m = a.y_m - b.y_m
    dz_m = a.z_m - b.z_m
    return sqrt(dx_m * dx_m + dy_m * dy_m + dz_m * dz_m)


def local_offset_point(
    origin: LocalPoint,
    dx_m: float,
    dy_m: float,
    dz_m: float = 0.0,
) -> LocalPoint:
    """Return a local point offset from an origin by metric deltas."""

    return LocalPoint(
        x_m=origin.x_m + dx_m,
        y_m=origin.y_m + dy_m,
        z_m=origin.z_m + dz_m,
    )


def mgrs_to_wgs84(mgrs_text: str) -> WGS84Point:
    """Convert MGRS text to WGS84 if the optional dependency is available.

    This structural helper is part of Task 002. It must be locally validated before
    being treated as an operationally accurate military-coordinate workflow.

    Args:
        mgrs_text: MGRS coordinate string.

    Raises:
        ValueError: If the input text is empty.
        MissingOptionalDependencyError: If the optional ``mgrs`` package is missing.
    """

    if not mgrs_text.strip():
        raise ValueError("mgrs_text must not be empty.")

    try:
        mgrs_module = import_module("mgrs")
    except ImportError as exc:
        raise MissingOptionalDependencyError(
            "Optional dependency 'mgrs' is required for MGRS conversion. "
            "Install the GIS extra and validate conversion locally."
        ) from exc

    mgrs_class = getattr(mgrs_module, "MGRS")
    converter: Any = mgrs_class()
    lat_lon: Any = converter.toLatLon(mgrs_text)
    return WGS84Point(lat=float(lat_lon[0]), lon=float(lat_lon[1]))
