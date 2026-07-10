from types import SimpleNamespace

from examples import local_geotiff_adapter_smoke as smoke
from uav_rf_terrain.profile import TerrainProfileError
from uav_rf_terrain.terrain_data import TerrainDataError


CLI_ARGS = [
    "--dem-path",
    "dem.tif",
    "--dsm-path",
    "dsm.tif",
    "--start-x",
    "0",
    "--start-y",
    "0",
    "--end-x",
    "90",
    "--end-y",
    "0",
]


class FakeAdapter:
    def __init__(self, dem_path: object, dsm_path: object) -> None:
        self.dem_path = dem_path
        self.dsm_path = dsm_path

    def validate_metadata(self) -> object:
        return SimpleNamespace(
            dataset_name="fake-dataset",
            dem=SimpleNamespace(
                crs="EPSG:5179",
                resolution_m=90.0,
                width=2,
                height=1,
                bounds=(0.0, 0.0, 180.0, 90.0),
            ),
        )


def test_terrain_profile_error_is_concise(
    monkeypatch, capsys,
) -> None:
    monkeypatch.setattr(smoke, "LocalGeoTiffTerrainDataAdapter", FakeAdapter)

    def raise_profile_error(*args: object, **kwargs: object) -> object:
        raise TerrainProfileError("point is outside terrain bounds")

    monkeypatch.setattr(smoke, "extract_terrain_profile_from_adapter", raise_profile_error)

    assert smoke.main(CLI_ARGS) == 1
    output = capsys.readouterr()
    assert "Local GeoTIFF smoke test failed:" in output.err
    assert "point is outside terrain bounds" in output.err
    assert "Traceback" not in output.err
    assert "Traceback" not in output.out


def test_terrain_data_error_is_concise(monkeypatch, capsys) -> None:
    class InvalidAdapter(FakeAdapter):
        def validate_metadata(self) -> object:
            raise TerrainDataError("DEM and DSM metadata mismatch")

    monkeypatch.setattr(smoke, "LocalGeoTiffTerrainDataAdapter", InvalidAdapter)

    assert smoke.main(CLI_ARGS) == 1
    output = capsys.readouterr()
    assert "Local GeoTIFF smoke test failed:" in output.err
    assert "DEM and DSM metadata mismatch" in output.err
    assert "Traceback" not in output.err
    assert "Traceback" not in output.out


def test_success_preserves_stdout_keys(monkeypatch, capsys) -> None:
    monkeypatch.setattr(smoke, "LocalGeoTiffTerrainDataAdapter", FakeAdapter)
    profile = SimpleNamespace(
        sample_count=2,
        max_dem_msl=100.0,
        max_dsm_msl=114.0,
        max_surface_delta_m=14.0,
    )
    monkeypatch.setattr(
        smoke,
        "extract_terrain_profile_from_adapter",
        lambda *args, **kwargs: profile,
    )

    assert smoke.main(CLI_ARGS) == 0
    output = capsys.readouterr()
    assert output.err == ""
    for key in (
        "dataset=",
        "crs=",
        "resolution_m=",
        "size=",
        "bounds=",
        "sample_count=",
        "max_dem_msl=",
        "max_dsm_msl=",
        "max_surface_delta_m=",
    ):
        assert key in output.out
