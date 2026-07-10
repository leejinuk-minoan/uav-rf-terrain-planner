"""Pure Python terrain profile extraction over synthetic grids and adapters.

Task 004 extracts sampled DEM/DSM profile records between two local points. It does
not compute LOS line heights, LOS blocking, Fresnel radii, Fresnel clearance,
final scores, map layers, or real communication-quality metrics. Task 017A adds a
storage-independent adapter entry point without loading real terrain files.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil

from .coordinates import LocalPoint, distance_2d_m
from .synthetic import SyntheticTerrainGrid
from .terrain_data import TerrainDataAdapter, TerrainDatasetMetadata


class TerrainProfileError(ValueError):
    """Raised when terrain profile extraction inputs are invalid."""


@dataclass(frozen=True)
class TerrainProfileSample:
    """Single DEM/DSM sample along a terrain profile.

    Distances are horizontal 2D distances in meters along the start-to-end segment.
    ``surface_delta_m`` is ``dsm_msl - dem_msl``.
    """

    sample_index: int
    ix: int
    iy: int
    point: LocalPoint
    distance_from_start_m: float
    distance_to_end_m: float
    dem_msl: float
    dsm_msl: float
    surface_delta_m: float


@dataclass(frozen=True)
class TerrainProfile:
    """Ordered terrain profile samples from ``start`` to ``end``."""

    scenario_name: str
    start: LocalPoint
    end: LocalPoint
    sample_spacing_m: float
    samples: tuple[TerrainProfileSample, ...]

    @property
    def sample_count(self) -> int:
        """Return the number of samples in the profile."""

        return len(self.samples)

    @property
    def max_surface_delta_m(self) -> float:
        """Return the maximum DSM-DEM surface delta in the profile."""

        _ensure_samples(self.samples)
        return max(sample.surface_delta_m for sample in self.samples)

    @property
    def max_dem_msl(self) -> float:
        """Return the maximum DEM MSL height in the profile."""

        _ensure_samples(self.samples)
        return max(sample.dem_msl for sample in self.samples)

    @property
    def max_dsm_msl(self) -> float:
        """Return the maximum DSM MSL height in the profile."""

        _ensure_samples(self.samples)
        return max(sample.dsm_msl for sample in self.samples)


def local_point_to_grid_index(
    terrain: SyntheticTerrainGrid,
    point: LocalPoint,
) -> tuple[int, int]:
    """Convert a local metric point to a nearest grid index.

    The conversion uses ``SyntheticTerrainGrid.origin`` and ``terrain.grid_size_m``.
    The returned index is validated against the terrain grid bounds.
    """

    ix = int(round((point.x_m - terrain.origin.x_m) / terrain.grid_size_m))
    iy = int(round((point.y_m - terrain.origin.y_m) / terrain.grid_size_m))
    _validate_grid_index(terrain=terrain, ix=ix, iy=iy)
    return ix, iy


def grid_index_to_local_point(
    terrain: SyntheticTerrainGrid,
    ix: int,
    iy: int,
) -> LocalPoint:
    """Convert a grid index to a local metric point with ``z_m=0.0``.

    Z is intentionally not set to DEM or DSM height. AGL/MSL flight-altitude handling
    is reserved for later profile, LOS, and Fresnel integration tasks.
    """

    _validate_grid_index(terrain=terrain, ix=ix, iy=iy)
    return LocalPoint(
        x_m=terrain.origin.x_m + ix * terrain.grid_size_m,
        y_m=terrain.origin.y_m + iy * terrain.grid_size_m,
        z_m=0.0,
    )


def local_point_to_metadata_grid_index(
    metadata: TerrainDatasetMetadata,
    point: LocalPoint,
) -> tuple[int, int]:
    """Convert a local metric point to a nearest metadata grid index."""

    x_min, y_min, _, _ = metadata.dem.bounds
    resolution_m = metadata.dem.resolution_m
    ix = int(round((point.x_m - x_min) / resolution_m))
    iy = int(round((point.y_m - y_min) / resolution_m))
    _validate_metadata_grid_index(metadata=metadata, ix=ix, iy=iy)
    return ix, iy


def metadata_grid_index_to_local_point(
    metadata: TerrainDatasetMetadata,
    ix: int,
    iy: int,
) -> LocalPoint:
    """Convert a metadata grid index to a local metric point with ``z_m=0.0``."""

    _validate_metadata_grid_index(metadata=metadata, ix=ix, iy=iy)
    x_min, y_min, _, _ = metadata.dem.bounds
    return LocalPoint(
        x_m=x_min + ix * metadata.dem.resolution_m,
        y_m=y_min + iy * metadata.dem.resolution_m,
        z_m=0.0,
    )


def extract_terrain_profile(
    terrain: SyntheticTerrainGrid,
    start: LocalPoint,
    end: LocalPoint,
    *,
    sample_spacing_m: float | None = None,
) -> TerrainProfile:
    """Extract ordered DEM/DSM samples along a straight 2D start-to-end segment.

    Start and end samples are always included. Duplicate grid indices can occur when
    the sampling spacing is smaller than the terrain grid size; Task 004 intentionally
    keeps duplicates rather than deduplicating the profile.
    """

    resolved_spacing_m = terrain.grid_size_m if sample_spacing_m is None else sample_spacing_m
    return _extract_profile(
        scenario_name=terrain.scenario_name,
        start=start,
        end=end,
        sample_spacing_m=resolved_spacing_m,
        point_to_index=lambda point: local_point_to_grid_index(terrain, point),
        read_values=lambda ix, iy: (
            terrain.dem_at(ix=ix, iy=iy),
            terrain.dsm_at(ix=ix, iy=iy),
            terrain.dsm_at(ix=ix, iy=iy) - terrain.dem_at(ix=ix, iy=iy),
        ),
    )


def extract_terrain_profile_from_adapter(
    adapter: TerrainDataAdapter,
    start: LocalPoint,
    end: LocalPoint,
    *,
    sample_spacing_m: float | None = None,
    scenario_name: str | None = None,
) -> TerrainProfile:
    """Extract a terrain profile using metadata and adapter access methods."""

    metadata = adapter.validate_metadata()
    resolved_spacing_m = (
        metadata.dem.resolution_m if sample_spacing_m is None else sample_spacing_m
    )
    return _extract_profile(
        scenario_name=scenario_name or metadata.dataset_name,
        start=start,
        end=end,
        sample_spacing_m=resolved_spacing_m,
        point_to_index=lambda point: local_point_to_metadata_grid_index(metadata, point),
        read_values=lambda ix, iy: (
            adapter.get_dem_msl(ix, iy),
            adapter.get_dsm_msl(ix, iy),
            adapter.get_surface_delta_m(ix, iy),
        ),
    )


def _extract_profile(
    *,
    scenario_name: str,
    start: LocalPoint,
    end: LocalPoint,
    sample_spacing_m: float,
    point_to_index: Callable[[LocalPoint], tuple[int, int]],
    read_values: Callable[[int, int], tuple[float, float, float]],
) -> TerrainProfile:
    if sample_spacing_m <= 0:
        raise TerrainProfileError("sample_spacing_m must be positive.")

    segment_distance_m = distance_2d_m(start, end)
    if segment_distance_m <= 0:
        raise TerrainProfileError("start and end must be different local points.")

    point_to_index(start)
    point_to_index(end)
    step_count = max(1, int(ceil(segment_distance_m / sample_spacing_m)))
    samples: list[TerrainProfileSample] = []
    for sample_index in range(step_count + 1):
        fraction = sample_index / step_count
        point = LocalPoint(
            x_m=start.x_m + (end.x_m - start.x_m) * fraction,
            y_m=start.y_m + (end.y_m - start.y_m) * fraction,
            z_m=start.z_m + (end.z_m - start.z_m) * fraction,
        )
        ix, iy = point_to_index(point)
        dem_msl, dsm_msl, surface_delta_m = read_values(ix, iy)
        distance_from_start_m = segment_distance_m * fraction
        samples.append(
            TerrainProfileSample(
                sample_index=sample_index,
                ix=ix,
                iy=iy,
                point=point,
                distance_from_start_m=distance_from_start_m,
                distance_to_end_m=segment_distance_m - distance_from_start_m,
                dem_msl=dem_msl,
                dsm_msl=dsm_msl,
                surface_delta_m=surface_delta_m,
            )
        )

    return TerrainProfile(
        scenario_name=scenario_name,
        start=start,
        end=end,
        sample_spacing_m=sample_spacing_m,
        samples=tuple(samples),
    )


def _validate_grid_index(terrain: SyntheticTerrainGrid, ix: int, iy: int) -> None:
    if ix < 0 or ix >= terrain.width_cells:
        raise TerrainProfileError("ix is outside the terrain grid bounds.")
    if iy < 0 or iy >= terrain.height_cells:
        raise TerrainProfileError("iy is outside the terrain grid bounds.")


def _validate_metadata_grid_index(
    metadata: TerrainDatasetMetadata,
    ix: int,
    iy: int,
) -> None:
    if ix < 0 or ix >= metadata.dem.width:
        raise TerrainProfileError("ix is outside the terrain metadata bounds.")
    if iy < 0 or iy >= metadata.dem.height:
        raise TerrainProfileError("iy is outside the terrain metadata bounds.")


def _ensure_samples(samples: tuple[TerrainProfileSample, ...]) -> None:
    if not samples:
        raise TerrainProfileError("terrain profile must contain at least one sample.")
