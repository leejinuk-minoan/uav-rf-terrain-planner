from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from uav_rf_terrain.geotiff_terrain_data import (
    LocalGeoTiffTerrainDataAdapter,
    _project_index_to_raster_row_col,
)
from uav_rf_terrain.terrain_data import TerrainDataError, TerrainDatasetMetadata


@dataclass(frozen=True)
class FakeCrs:
    value: str = "EPSG:5179"

    def to_string(self) -> str:
        return self.value


@dataclass
class FakeCell:
    value: float
    masked: bool = False

    @property
    def mask(self) -> bool:
        return self.masked

    def __getitem__(self, key: tuple[int, int]) -> float:
        assert key == (0, 0)
        return self.value


@dataclass
class FakeDataset:
    values: list[list[float]]
    crs: FakeCrs | None = field(default_factory=FakeCrs)
    transform: Any = field(
        default_factory=lambda: SimpleNamespace(a=10.0, b=0.0, d=0.0, e=-10.0)
    )
    bounds: Any = field(
        default_factory=lambda: SimpleNamespace(left=0.0, bottom=0.0, right=30.0, top=30.0)
    )
    nodata: float | None = -9999.0
    masked_cells: set[tuple[int, int]] = field(default_factory=set)
    read_windows: list[tuple[tuple[int, int], tuple[int, int]]] = field(default_factory=list)

    @property
    def width(self) -> int:
        return len(self.values[0])

    @property
    def height(self) -> int:
        return len(self.values)

    def __enter__(self) -> "FakeDataset":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(
        self,
        band: int,
        *,
        window: tuple[tuple[int, int], tuple[int, int]],
        masked: bool,
    ) -> FakeCell:
        assert band == 1
        assert masked
        self.read_windows.append(window)
        row, col = window[0][0], window[1][0]
        return FakeCell(self.values[row][col], (row, col) in self.masked_cells)


@dataclass
class FakeRasterio:
    datasets: dict[str, FakeDataset]

    def open(self, path: Path) -> FakeDataset:
        return self.datasets[Path(path).name]


def _datasets() -> dict[str, FakeDataset]:
    return {
        "dem.tif": FakeDataset(
            [
                [20.0, 21.0, 22.0],
                [10.0, 11.0, 12.0],
                [0.0, 1.0, 2.0],
            ]
        ),
        "dsm.tif": FakeDataset(
            [
                [25.0, 26.0, 27.0],
                [15.0, 16.0, 17.0],
                [5.0, 6.0, 7.0],
            ]
        ),
    }


def _adapter(monkeypatch: pytest.MonkeyPatch, datasets: dict[str, FakeDataset]):
    fake = FakeRasterio(datasets)
    monkeypatch.setattr(
        "uav_rf_terrain.geotiff_terrain_data.importlib.import_module",
        lambda name: fake if name == "rasterio" else __import__(name),
    )
    return LocalGeoTiffTerrainDataAdapter("dem.tif", "dsm.tif")


def test_missing_rasterio_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str):
        if name == "rasterio":
            raise ModuleNotFoundError(name)
        return __import__(name)

    monkeypatch.setattr(
        "uav_rf_terrain.geotiff_terrain_data.importlib.import_module",
        missing,
    )

    with pytest.raises(TerrainDataError, match="rasterio is required"):
        LocalGeoTiffTerrainDataAdapter("dem.tif", "dsm.tif").get_metadata()


def test_fake_geotiff_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = _adapter(monkeypatch, _datasets()).get_metadata()

    assert isinstance(metadata, TerrainDatasetMetadata)
    assert metadata.dem.crs == "EPSG:5179"
    assert metadata.dem.resolution_m == 10.0
    assert metadata.dem.width == 3
    assert metadata.dem.height == 3
    assert metadata.dem.bounds == (0.0, 0.0, 30.0, 30.0)
    assert metadata.dem.nodata_value == -9999.0


@pytest.mark.parametrize(
    (("field_name", "value", "error_match")),
    [
        ("crs", FakeCrs("EPSG:5186"), "crs"),
        ("transform", SimpleNamespace(a=20.0, b=0.0, d=0.0, e=-20.0), "resolution_m"),
        ("values", [[1.0, 2.0], [3.0, 4.0]], "width"),
        (
            "bounds",
            SimpleNamespace(left=0.0, bottom=0.0, right=40.0, top=30.0),
            "bounds",
        ),
    ],
)
def test_dem_dsm_alignment_mismatch_raises(
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    value: object,
    error_match: str,
) -> None:
    datasets = _datasets()
    setattr(datasets["dsm.tif"], field_name, value)

    with pytest.raises(TerrainDataError, match=error_match):
        _adapter(monkeypatch, datasets).validate_metadata()


def test_rotated_transform_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    datasets = _datasets()
    datasets["dem.tif"].transform = SimpleNamespace(a=10.0, b=1.0, d=0.0, e=-10.0)

    with pytest.raises(TerrainDataError, match="rotated or sheared"):
        _adapter(monkeypatch, datasets).get_metadata()


def test_unequal_xy_pixel_size_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    datasets = _datasets()
    datasets["dem.tif"].transform = SimpleNamespace(a=10.0, b=0.0, d=0.0, e=-20.0)

    with pytest.raises(TerrainDataError, match="x/y pixel sizes"):
        _adapter(monkeypatch, datasets).get_metadata()


@pytest.mark.parametrize(("y_index", "expected_row"), [(0, 2), (2, 0)])
def test_project_y_index_converts_to_raster_row(y_index: int, expected_row: int) -> None:
    assert _project_index_to_raster_row_col(
        width=3, height=3, x_index=1, y_index=y_index
    ) == (expected_row, 1)


def test_dem_dsm_and_surface_delta_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    datasets = _datasets()
    adapter = _adapter(monkeypatch, datasets)

    assert adapter.get_dem_msl(1, 0) == 1.0
    assert adapter.get_dsm_msl(1, 2) == 26.0
    assert adapter.get_surface_delta_m(1, 1) == 5.0
    assert datasets["dem.tif"].read_windows[-1] == ((1, 2), (1, 2))


def test_masked_and_nodata_values_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    datasets = _datasets()
    datasets["dem.tif"].masked_cells.add((2, 0))
    adapter = _adapter(monkeypatch, datasets)

    with pytest.raises(TerrainDataError, match="masked or NoData"):
        adapter.get_dem_msl(0, 0)

    datasets["dem.tif"].masked_cells.clear()
    datasets["dem.tif"].values[2][0] = -9999.0
    with pytest.raises(TerrainDataError, match="NoData"):
        adapter.get_dem_msl(0, 0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_values_raise(monkeypatch: pytest.MonkeyPatch, value: float) -> None:
    datasets = _datasets()
    datasets["dem.tif"].values[2][0] = value

    with pytest.raises(TerrainDataError, match="finite"):
        _adapter(monkeypatch, datasets).get_dem_msl(0, 0)


@pytest.mark.parametrize(("x_index", "y_index"), [(-1, 0), (3, 0), (0, -1), (0, 3)])
def test_out_of_bounds_index_raises(
    monkeypatch: pytest.MonkeyPatch, x_index: int, y_index: int
) -> None:
    with pytest.raises(TerrainDataError, match="out of bounds"):
        _adapter(monkeypatch, _datasets()).get_dem_msl(x_index, y_index)


def test_metadata_does_not_include_runtime_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = _adapter(monkeypatch, _datasets()).get_metadata()
    serialized = repr(metadata)

    assert "dem.tif" not in serialized
    assert "dsm.tif" not in serialized


def test_package_root_import_does_not_import_rasterio() -> None:
    command = (
        "import sys; import uav_rf_terrain; "
        "assert 'rasterio' not in sys.modules; print('package_import_ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "package_import_ok"
