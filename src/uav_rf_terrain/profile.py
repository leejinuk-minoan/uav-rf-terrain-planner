"""Pure Python terrain profile extraction over synthetic DEM/DSM grids.

Task 004 extracts sampled DEM/DSM profile records between two local points. It does
not compute LOS line heights, LOS blocking, Fresnel radii, Fresnel clearance,
final scores, map layers, or real communication-quality metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from .coordinates import LocalPoint, distance_2d_m
from .synthetic import SyntheticTerrainGrid


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
    if resolved_spacing_m <= 0:
        raise TerrainProfileError("sample_spacing_m must be positive.")

    segment_distance_m = distance_2d_m(start, end)
    if segment_distance_m <= 0:
        raise TerrainProfileError("start and end must be different local points.")

    # Validate endpoints before generating intermediate samples.
    local_point_to_grid_index(terrain=terrain, point=start)
    local_point_to_grid_index(terrain=terrain, point=end)

    step_count = max(1, int(ceil(segment_distance_m / resolved_spacing_m)))
    dx_m = end.x_m - start.x_m
    dy_m = end.y_m - start.y_m
    dz_m = end.z_m - start.z_m

    samples: list[TerrainProfileSample] = []
    for sample_index in range(step_count + 1):
        fraction = sample_index / step_count
        point = LocalPoint(
            x_m=start.x_m + dx_m * fraction,
            y_m=start.y_m + dy_m * fraction,
            z_m=start.z_m + dz_m * fraction,
        )
        ix, iy = local_point_to_grid_index(terrain=terrain, point=point)
        dem_msl = terrain.dem_at(ix=ix, iy=iy)
        dsm_msl = terrain.dsm_at(ix=ix, iy=iy)
        distance_from_start_m = segment_distance_m * fraction
        distance_to_end_m = segment_distance_m - distance_from_start_m
        samples.append(
            TerrainProfileSample(
                sample_index=sample_index,
                ix=ix,
                iy=iy,
                point=point,
                distance_from_start_m=distance_from_start_m,
                distance_to_end_m=distance_to_end_m,
                dem_msl=dem_msl,
                dsm_msl=dsm_msl,
                surface_delta_m=dsm_msl - dem_msl,
            )
        )

    return TerrainProfile(
        scenario_name=terrain.scenario_name,
        start=start,
        end=end,
        sample_spacing_m=resolved_spacing_m,
        samples=tuple(samples),
    )


def _validate_grid_index(terrain: SyntheticTerrainGrid, ix: int, iy: int) -> None:
    if ix < 0 or ix >= terrain.width_cells:
        raise TerrainProfileError("ix is outside the terrain grid bounds.")
    if iy < 0 or iy >= terrain.height_cells:
        raise TerrainProfileError("iy is outside the terrain grid bounds.")


def _ensure_samples(samples: tuple[TerrainProfileSample, ...]) -> None:
    if not samples:
        raise TerrainProfileError("terrain profile must contain at least one sample.")
