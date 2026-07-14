"""Lazy EPSG:5179 coordinate adapters for the real-terrain map boundary."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from math import isfinite
from typing import Any, Protocol

from .coordinates import LocalPoint


class CoordinateConversionError(ValueError):
    """Raised when a renderer-internal or MGRS conversion is invalid."""


@dataclass(frozen=True)
class Wgs84MapPoint:
    """Renderer-internal WGS84 point stored as longitude then latitude."""

    longitude_deg: float
    latitude_deg: float

    def __post_init__(self) -> None:
        _finite("longitude_deg", self.longitude_deg)
        _finite("latitude_deg", self.latitude_deg)
        if not -180.0 <= self.longitude_deg <= 180.0:
            raise CoordinateConversionError("longitude_deg must be within [-180, 180].")
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise CoordinateConversionError("latitude_deg must be within [-90, 90].")


class ProjectedToWgs84Converter(Protocol):
    """Convert an internal EPSG:5179 point to renderer WGS84 coordinates."""

    def __call__(self, point: LocalPoint) -> Wgs84MapPoint: ...


class ProjectedToMgrsConverter(Protocol):
    """Convert an internal EPSG:5179 point to user-facing MGRS text."""

    def __call__(self, point: LocalPoint, *, precision: int) -> str: ...


class Epsg5179ToWgs84Converter:
    """Lazily create a pyproj transformer with the EPSG:5179 map contract."""

    def __init__(self) -> None:
        self._transformer: Any | None = None

    def __call__(self, point: LocalPoint) -> Wgs84MapPoint:
        _finite("point.x_m", point.x_m)
        _finite("point.y_m", point.y_m)
        transformer = self._get_transformer()
        try:
            longitude, latitude = transformer.transform(point.x_m, point.y_m)
        except Exception as exc:  # pyproj implementation errors are boundary errors.
            raise CoordinateConversionError("EPSG:5179 to WGS84 conversion failed.") from exc
        try:
            return Wgs84MapPoint(float(longitude), float(latitude))
        except (TypeError, ValueError, CoordinateConversionError) as exc:
            raise CoordinateConversionError("EPSG:5179 conversion returned invalid WGS84 data.") from exc

    def _get_transformer(self) -> Any:
        if self._transformer is not None:
            return self._transformer
        try:
            pyproj = importlib.import_module("pyproj")
            self._transformer = pyproj.Transformer.from_crs(
                "EPSG:5179",
                "EPSG:4326",
                always_xy=True,
            )
        except ModuleNotFoundError as exc:
            raise CoordinateConversionError("pyproj is required for EPSG:5179 WGS84 conversion.") from exc
        except Exception as exc:
            raise CoordinateConversionError("EPSG:5179 WGS84 transformer initialization failed.") from exc
        return self._transformer


class Epsg5179ToMgrsConverter:
    """Lazily convert EPSG:5179 through WGS84 into normalized MGRS text."""

    def __init__(self, wgs84_converter: ProjectedToWgs84Converter | None = None) -> None:
        self._wgs84_converter = wgs84_converter or Epsg5179ToWgs84Converter()
        self._mgrs: Any | None = None

    def __call__(self, point: LocalPoint, *, precision: int) -> str:
        if isinstance(precision, bool) or not isinstance(precision, int) or not 0 <= precision <= 5:
            raise CoordinateConversionError("precision must be an integer between 0 and 5.")
        wgs84 = self._wgs84_converter(point)
        try:
            output = self._get_mgrs().toMGRS(
                wgs84.latitude_deg,
                wgs84.longitude_deg,
                MGRSPrecision=precision,
            )
        except Exception as exc:
            raise CoordinateConversionError("WGS84 to MGRS conversion failed.") from exc
        if isinstance(output, bytes):
            output = output.decode("ascii")
        if not isinstance(output, str):
            raise CoordinateConversionError("MGRS conversion returned invalid text.")
        normalized = output.strip().upper()
        if not normalized:
            raise CoordinateConversionError("MGRS conversion returned empty text.")
        return normalized

    def _get_mgrs(self) -> Any:
        if self._mgrs is not None:
            return self._mgrs
        try:
            module = importlib.import_module("mgrs")
            self._mgrs = module.MGRS()
        except ModuleNotFoundError as exc:
            raise CoordinateConversionError("mgrs is required for MGRS conversion.") from exc
        except Exception as exc:
            raise CoordinateConversionError("MGRS converter initialization failed.") from exc
        return self._mgrs


def _finite(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
        raise CoordinateConversionError(f"{name} must be finite.")
