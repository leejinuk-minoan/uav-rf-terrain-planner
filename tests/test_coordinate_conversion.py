from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from uav_rf_terrain.coordinate_conversion import (
    CoordinateConversionError,
    Epsg5179ToMgrsConverter,
    Epsg5179ToWgs84Converter,
    Wgs84MapPoint,
)
from uav_rf_terrain.coordinates import LocalPoint


def test_wgs84_map_point_uses_longitude_then_latitude_and_rejects_invalid_values() -> None:
    assert Wgs84MapPoint(127.0, 37.5) == Wgs84MapPoint(longitude_deg=127.0, latitude_deg=37.5)

    with pytest.raises(CoordinateConversionError):
        Wgs84MapPoint(True, 37.5)
    with pytest.raises(CoordinateConversionError):
        Wgs84MapPoint(181.0, 37.5)
    with pytest.raises(CoordinateConversionError):
        Wgs84MapPoint(127.0, float("nan"))


def test_lazy_coordinate_adapters_preserve_epsg_axis_and_mgrs_precision(monkeypatch: pytest.MonkeyPatch) -> None:
    transformer_calls: list[tuple[str, str, bool]] = []
    transform_calls: list[tuple[float, float]] = []
    mgrs_calls: list[tuple[float, float, int]] = []

    class FakeTransformer:
        def transform(self, x_m: float, y_m: float) -> tuple[float, float]:
            transform_calls.append((x_m, y_m))
            return (127.0, 37.5)

    class FakeTransformerFactory:
        @staticmethod
        def from_crs(source: str, destination: str, *, always_xy: bool) -> FakeTransformer:
            transformer_calls.append((source, destination, always_xy))
            return FakeTransformer()

    class FakeMgrs:
        def toMGRS(self, latitude: float, longitude: float, *, MGRSPrecision: int) -> str:
            mgrs_calls.append((latitude, longitude, MGRSPrecision))
            return " 52scb1234512345 "

    monkeypatch.setitem(sys.modules, "pyproj", SimpleNamespace(Transformer=FakeTransformerFactory))
    monkeypatch.setitem(sys.modules, "mgrs", SimpleNamespace(MGRS=FakeMgrs))
    point = LocalPoint(950000.0, 1950000.0)
    wgs84 = Epsg5179ToWgs84Converter()
    mgrs = Epsg5179ToMgrsConverter(wgs84)

    assert wgs84(point) == Wgs84MapPoint(127.0, 37.5)
    assert mgrs(point, precision=5) == "52SCB1234512345"
    assert transformer_calls == [("EPSG:5179", "EPSG:4326", True)]
    assert transform_calls == [(950000.0, 1950000.0), (950000.0, 1950000.0)]
    assert mgrs_calls == [(37.5, 127.0, 5)]
