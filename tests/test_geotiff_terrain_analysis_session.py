from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.geotiff_terrain_data import LocalGeoTiffTerrainDataAdapter
from uav_rf_terrain.terrain_data import TerrainDataError


@dataclass
class FakeCell:
    value: float

    @property
    def mask(self) -> bool:
        return False

    def __getitem__(self, key: tuple[int, int]) -> float:
        return self.value


@dataclass
class FakeDataset:
    values: list[list[float]]
    transform: Any = field(
        default_factory=lambda: SimpleNamespace(a=10.0, b=0.0, c=0.0, d=0.0, e=-10.0, f=30.0)
    )
    bounds: Any = field(
        default_factory=lambda: SimpleNamespace(left=0.0, bottom=0.0, right=30.0, top=30.0)
    )
    crs: Any = field(default_factory=lambda: SimpleNamespace(to_string=lambda: "EPSG:5179"))
    nodata: float | None = None
    opens: int = 0
    closes: int = 0

    @property
    def width(self) -> int:
        return len(self.values[0])

    @property
    def height(self) -> int:
        return len(self.values)

    def __enter__(self) -> "FakeDataset":
        self.opens += 1
        return self

    def __exit__(self, *args: object) -> None:
        self.closes += 1

    def index(self, x: float, y: float) -> tuple[int, int]:
        return int((30.0 - y) // 10.0), int(x // 10.0)

    def xy(self, row: int, col: int) -> tuple[float, float]:
        return col * 10.0 + 5.0, 30.0 - row * 10.0 - 5.0

    def read(self, band: int, *, window: tuple[tuple[int, int], tuple[int, int]], masked: bool) -> FakeCell:
        row, col = window[0][0], window[1][0]
        return FakeCell(self.values[row][col])


@dataclass
class FakeRasterio:
    datasets: dict[str, FakeDataset]

    def open(self, path: Path) -> FakeDataset:
        return self.datasets[path.name]


def _adapter(monkeypatch: pytest.MonkeyPatch) -> tuple[LocalGeoTiffTerrainDataAdapter, FakeDataset, FakeDataset]:
    dem = FakeDataset([[100.0] * 3 for _ in range(3)])
    dsm = FakeDataset([[110.0] * 3 for _ in range(3)])
    fake = FakeRasterio({"dem.tif": dem, "dsm.tif": dsm})
    monkeypatch.setattr(
        "uav_rf_terrain.geotiff_terrain_data.importlib.import_module",
        lambda name: fake if name == "rasterio" else __import__(name),
    )
    return LocalGeoTiffTerrainDataAdapter("dem.tif", "dsm.tif"), dem, dsm


def test_analysis_session_samples_north_up_edges_with_one_open_per_raster(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter, dem, dsm = _adapter(monkeypatch)

    with adapter.open_analysis_session() as session:
        left_top = session.sample_point(LocalPoint(0.0, 30.0))
        epsilon_inside = session.sample_point(LocalPoint(29.999, 0.001))
        assert (left_top.x_index, left_top.y_index) == (0, 2)
        assert (epsilon_inside.x_index, epsilon_inside.y_index) == (2, 0)
        assert left_top.cell_center_point == LocalPoint(5.0, 25.0)
        with pytest.raises(TerrainDataError, match="outside the raster extent"):
            session.sample_point(LocalPoint(30.0, 20.0))
        with pytest.raises(TerrainDataError, match="outside the raster extent"):
            session.sample_point(LocalPoint(20.0, 0.0))

    assert (dem.opens, dsm.opens) == (1, 1)
    assert (dem.closes, dsm.closes) == (1, 1)


@pytest.mark.parametrize(
    "transform",
    [
        SimpleNamespace(a=-10.0, b=0.0, c=0.0, d=0.0, e=-10.0, f=30.0),
        SimpleNamespace(a=10.0, b=0.0, c=0.0, d=0.0, e=10.0, f=30.0),
        SimpleNamespace(a=10.0, b=1.0, c=0.0, d=0.0, e=-10.0, f=30.0),
        SimpleNamespace(a=10.0, b=0.0, c=0.0, d=1.0, e=-10.0, f=30.0),
    ],
)
def test_analysis_session_rejects_unsupported_transforms(
    monkeypatch: pytest.MonkeyPatch, transform: Any
) -> None:
    adapter, dem, _ = _adapter(monkeypatch)
    dem.transform = transform

    with pytest.raises(TerrainDataError, match="north-up"):
        with adapter.open_analysis_session():
            pass
