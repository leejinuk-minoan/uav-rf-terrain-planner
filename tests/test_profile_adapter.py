from dataclasses import dataclass

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.profile import (
    TerrainProfileError,
    extract_terrain_profile,
    extract_terrain_profile_from_adapter,
    local_point_to_metadata_grid_index,
    metadata_grid_index_to_local_point,
)
from uav_rf_terrain.synthetic import (
    SCENARIO_FLAT_WITH_BUILDING,
    SyntheticTerrainGrid,
    create_synthetic_terrain,
)
from uav_rf_terrain.terrain_data import SyntheticTerrainDataAdapter, TerrainDatasetMetadata


def _terrain_and_points() -> tuple[SyntheticTerrainGrid, LocalPoint, LocalPoint]:
    terrain = create_synthetic_terrain(
        SCENARIO_FLAT_WITH_BUILDING,
        width_cells=7,
        height_cells=5,
        grid_size_m=10.0,
        base_dem_msl=50.0,
    )
    return terrain, LocalPoint(0.0, 20.0), LocalPoint(60.0, 20.0)


def test_adapter_profile_matches_existing_synthetic_profile() -> None:
    terrain, start, end = _terrain_and_points()
    direct = extract_terrain_profile(terrain, start, end)
    adapted = extract_terrain_profile_from_adapter(
        SyntheticTerrainDataAdapter(terrain), start, end, scenario_name=terrain.scenario_name
    )

    assert adapted.sample_count == direct.sample_count
    assert adapted.sample_spacing_m == direct.sample_spacing_m
    for actual, expected in zip(adapted.samples, direct.samples, strict=True):
        assert actual.ix == expected.ix
        assert actual.iy == expected.iy
        assert actual.distance_from_start_m == expected.distance_from_start_m
        assert actual.distance_to_end_m == expected.distance_to_end_m
        assert actual.dem_msl == expected.dem_msl
        assert actual.dsm_msl == expected.dsm_msl
        assert actual.surface_delta_m == expected.surface_delta_m


def test_default_adapter_spacing_uses_dem_resolution() -> None:
    terrain, start, end = _terrain_and_points()
    profile = extract_terrain_profile_from_adapter(SyntheticTerrainDataAdapter(terrain), start, end)

    assert profile.sample_spacing_m == terrain.grid_size_m
    assert profile.sample_count == 7


def test_explicit_adapter_spacing_is_used() -> None:
    terrain, start, end = _terrain_and_points()
    profile = extract_terrain_profile_from_adapter(
        SyntheticTerrainDataAdapter(terrain), start, end, sample_spacing_m=15.0
    )

    assert profile.sample_spacing_m == 15.0
    assert profile.sample_count == 5


@pytest.mark.parametrize("sample_spacing_m", [0.0, -1.0])
def test_invalid_adapter_sample_spacing_raises(sample_spacing_m: float) -> None:
    terrain, start, end = _terrain_and_points()
    with pytest.raises(TerrainProfileError, match="sample_spacing_m"):
        extract_terrain_profile_from_adapter(
            SyntheticTerrainDataAdapter(terrain),
            start,
            end,
            sample_spacing_m=sample_spacing_m,
        )


def test_same_adapter_profile_endpoints_raise() -> None:
    terrain, start, _ = _terrain_and_points()
    with pytest.raises(TerrainProfileError, match="different"):
        extract_terrain_profile_from_adapter(SyntheticTerrainDataAdapter(terrain), start, start)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (LocalPoint(-10.0, 20.0), LocalPoint(60.0, 20.0)),
        (LocalPoint(0.0, 20.0), LocalPoint(70.0, 20.0)),
    ],
)
def test_adapter_profile_out_of_bounds_endpoint_raises(
    start: LocalPoint, end: LocalPoint
) -> None:
    terrain, _, _ = _terrain_and_points()
    with pytest.raises(TerrainProfileError, match="metadata bounds"):
        extract_terrain_profile_from_adapter(SyntheticTerrainDataAdapter(terrain), start, end)


def test_metadata_grid_index_conversion_helpers() -> None:
    terrain, _, _ = _terrain_and_points()
    metadata = SyntheticTerrainDataAdapter(terrain).validate_metadata()

    assert local_point_to_metadata_grid_index(metadata, LocalPoint(20.0, 30.0)) == (2, 3)
    assert metadata_grid_index_to_local_point(metadata, 2, 3) == LocalPoint(20.0, 30.0, 0.0)


def test_metadata_grid_helpers_reject_out_of_bounds_values() -> None:
    terrain, _, _ = _terrain_and_points()
    metadata = SyntheticTerrainDataAdapter(terrain).validate_metadata()

    with pytest.raises(TerrainProfileError, match="metadata bounds"):
        local_point_to_metadata_grid_index(metadata, LocalPoint(70.0, 20.0))
    with pytest.raises(TerrainProfileError, match="metadata bounds"):
        metadata_grid_index_to_local_point(metadata, 0, 5)


@dataclass
class TrackingAdapter:
    delegate: SyntheticTerrainDataAdapter
    validation_called: bool = False

    def validate_metadata(self) -> TerrainDatasetMetadata:
        self.validation_called = True
        return self.delegate.validate_metadata()

    def get_metadata(self) -> TerrainDatasetMetadata:
        return self.delegate.get_metadata()

    def get_dem_msl(self, x_index: int, y_index: int) -> float:
        return self.delegate.get_dem_msl(x_index, y_index)

    def get_dsm_msl(self, x_index: int, y_index: int) -> float:
        return self.delegate.get_dsm_msl(x_index, y_index)

    def get_surface_delta_m(self, x_index: int, y_index: int) -> float:
        return self.delegate.get_surface_delta_m(x_index, y_index)


def test_adapter_metadata_validation_is_called() -> None:
    terrain, start, end = _terrain_and_points()
    adapter = TrackingAdapter(SyntheticTerrainDataAdapter(terrain))

    extract_terrain_profile_from_adapter(adapter, start, end)

    assert adapter.validation_called
