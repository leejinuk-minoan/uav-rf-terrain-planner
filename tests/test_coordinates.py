import pytest

from uav_rf_terrain.coordinates import (
    CoordinateReference,
    LocalPoint,
    MissingOptionalDependencyError,
    WGS84Point,
    distance_2d_m,
    distance_3d_m,
    local_offset_point,
    mgrs_to_wgs84,
)


def test_local_point_can_be_created() -> None:
    point = LocalPoint(x_m=1.0, y_m=2.0, z_m=3.0)

    assert point.x_m == 1.0
    assert point.y_m == 2.0
    assert point.z_m == 3.0


def test_wgs84_point_can_be_created() -> None:
    point = WGS84Point(lat=37.0, lon=127.0, altitude_m=100.0)

    assert point.lat == 37.0
    assert point.lon == 127.0
    assert point.altitude_m == 100.0


def test_coordinate_reference_can_be_created() -> None:
    crs = CoordinateReference(name="Local tangent plane", epsg=None, description="test CRS")

    assert crs.name == "Local tangent plane"
    assert crs.description == "test CRS"


def test_distance_2d_m() -> None:
    a = LocalPoint(x_m=0.0, y_m=0.0)
    b = LocalPoint(x_m=3.0, y_m=4.0)

    assert distance_2d_m(a, b) == 5.0


def test_distance_3d_m() -> None:
    a = LocalPoint(x_m=0.0, y_m=0.0, z_m=0.0)
    b = LocalPoint(x_m=3.0, y_m=4.0, z_m=12.0)

    assert distance_3d_m(a, b) == 13.0


def test_local_offset_point() -> None:
    origin = LocalPoint(x_m=100.0, y_m=200.0, z_m=50.0)
    offset = local_offset_point(origin, dx_m=10.0, dy_m=-20.0, dz_m=5.0)

    assert offset == LocalPoint(x_m=110.0, y_m=180.0, z_m=55.0)


def test_mgrs_to_wgs84_requires_optional_dependency_or_returns_point() -> None:
    try:
        point = mgrs_to_wgs84("52SDG0000000000")
    except MissingOptionalDependencyError:
        pytest.skip("Optional 'mgrs' dependency is not installed in the base dev environment.")

    assert isinstance(point, WGS84Point)


def test_mgrs_to_wgs84_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="mgrs_text"):
        mgrs_to_wgs84(" ")
