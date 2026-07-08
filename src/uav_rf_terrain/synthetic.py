"""Pure Python synthetic DEM/DSM terrain generators for Task 003.

The grids in this module are small in-memory matrices for algorithm boundary-condition
testing. They do not load real DEM/DSM files, write GeoTIFFs, use GIS libraries, run
LOS/Fresnel algorithms, or claim real communication-quality validation.
"""

from __future__ import annotations

from dataclasses import dataclass

from .coordinates import LocalPoint

GridMatrix = tuple[tuple[float, ...], ...]

SCENARIO_FLAT = "flat"
SCENARIO_SINGLE_RIDGE = "single_ridge"
SCENARIO_FLAT_WITH_BUILDING = "flat_with_building"
SCENARIO_FLAT_WITH_TREES = "flat_with_trees"
SCENARIO_OBSTACLE_POSITION_VARIATION = "obstacle_position_variation"
SCENARIO_OPERATING_RADIUS_BOUNDARY = "operating_radius_boundary"
SCENARIO_FIXED_AGL_CASE = "fixed_agl_case"
SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION = "fresnel_radius_position_variation"

_SYNTHETIC_SCENARIOS: tuple[str, ...] = (
    SCENARIO_FLAT,
    SCENARIO_SINGLE_RIDGE,
    SCENARIO_FLAT_WITH_BUILDING,
    SCENARIO_FLAT_WITH_TREES,
    SCENARIO_OBSTACLE_POSITION_VARIATION,
    SCENARIO_OPERATING_RADIUS_BOUNDARY,
    SCENARIO_FIXED_AGL_CASE,
    SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION,
)


class SyntheticTerrainError(ValueError):
    """Raised when a synthetic terrain grid or scenario request is invalid."""


@dataclass(frozen=True)
class SyntheticTerrainGrid:
    """Small synthetic DEM/DSM grid for future LOS/Fresnel/scoring tests.

    Matrix indexing uses ``matrix[iy][ix]``. The DEM and DSM are expressed as MSL
    heights in meters. DSM values must be greater than or equal to the matching DEM
    values.
    """

    scenario_name: str
    grid_size_m: float
    dem_msl: GridMatrix
    dsm_msl: GridMatrix
    origin: LocalPoint = LocalPoint(x_m=0.0, y_m=0.0, z_m=0.0)
    description: str = ""

    def __post_init__(self) -> None:
        _validate_grid_size_values(
            width_cells=self.width_cells,
            height_cells=self.height_cells,
            grid_size_m=self.grid_size_m,
        )
        dem_shape = _matrix_shape(self.dem_msl)
        dsm_shape = _matrix_shape(self.dsm_msl)
        if dem_shape != dsm_shape:
            raise SyntheticTerrainError("DEM and DSM matrices must have the same shape.")

        for iy, row in enumerate(self.dsm_msl):
            for ix, dsm_value in enumerate(row):
                dem_value = self.dem_msl[iy][ix]
                if dsm_value < dem_value:
                    raise SyntheticTerrainError("Every DSM value must be greater than or equal to DEM.")

    @property
    def width_cells(self) -> int:
        """Return the number of cells along the x axis."""

        if not self.dem_msl:
            raise SyntheticTerrainError("DEM matrix must not be empty.")
        return len(self.dem_msl[0])

    @property
    def height_cells(self) -> int:
        """Return the number of cells along the y axis."""

        return len(self.dem_msl)

    def dem_at(self, ix: int, iy: int) -> float:
        """Return DEM MSL height at ``ix, iy``."""

        return self.dem_msl[iy][ix]

    def dsm_at(self, ix: int, iy: int) -> float:
        """Return DSM MSL height at ``ix, iy``."""

        return self.dsm_msl[iy][ix]

    def surface_delta_at(self, ix: int, iy: int) -> float:
        """Return DSM minus DEM surface height delta at ``ix, iy``."""

        return self.dsm_at(ix=ix, iy=iy) - self.dem_at(ix=ix, iy=iy)


def available_synthetic_scenarios() -> tuple[str, ...]:
    """Return available synthetic DEM/DSM scenario names."""

    return _SYNTHETIC_SCENARIOS


def create_synthetic_terrain(
    scenario_name: str,
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
) -> SyntheticTerrainGrid:
    """Create a synthetic terrain grid by scenario name."""

    factories = {
        SCENARIO_FLAT: create_flat_terrain,
        SCENARIO_SINGLE_RIDGE: create_single_ridge_terrain,
        SCENARIO_FLAT_WITH_BUILDING: create_flat_with_building_terrain,
        SCENARIO_FLAT_WITH_TREES: create_flat_with_trees_terrain,
        SCENARIO_OBSTACLE_POSITION_VARIATION: create_obstacle_position_variation_terrain,
        SCENARIO_OPERATING_RADIUS_BOUNDARY: create_operating_radius_boundary_terrain,
        SCENARIO_FIXED_AGL_CASE: create_fixed_agl_case_terrain,
        SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION: (
            create_fresnel_radius_position_variation_terrain
        ),
    }
    try:
        factory = factories[scenario_name]
    except KeyError as exc:
        raise SyntheticTerrainError(f"Unknown synthetic scenario: {scenario_name}") from exc

    return factory(
        width_cells=width_cells,
        height_cells=height_cells,
        grid_size_m=grid_size_m,
        base_dem_msl=base_dem_msl,
    )


def create_flat_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
) -> SyntheticTerrainGrid:
    """Create flat terrain where DEM and DSM are identical."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_FLAT,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dem,
        description="Flat baseline terrain with no surface obstacles.",
    )


def create_single_ridge_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
    ridge_height_m: float = 80.0,
) -> SyntheticTerrainGrid:
    """Create terrain with a vertical terrain ridge in both DEM and DSM."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    center_x = width_cells // 2
    ridge_half_width = max(0, width_cells // 30)
    dem = _add_rect_delta(
        dem,
        x_min=center_x - ridge_half_width,
        x_max=center_x + ridge_half_width,
        y_min=0,
        y_max=height_cells - 1,
        delta_m=ridge_height_m,
    )
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_SINGLE_RIDGE,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dem,
        description="Vertical terrain ridge for later LOS/Fresnel boundary tests.",
    )


def create_flat_with_building_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
    building_height_m: float = 35.0,
) -> SyntheticTerrainGrid:
    """Create flat DEM with a rectangular DSM building obstacle."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    dsm = _add_center_obstacle(dem, width_cells, height_cells, building_height_m)
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_FLAT_WITH_BUILDING,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dsm,
        description="Flat DEM with a central building-height DSM obstacle.",
    )


def create_flat_with_trees_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
    tree_height_m: float = 18.0,
) -> SyntheticTerrainGrid:
    """Create flat DEM with two DSM tree-canopy obstacle patches."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    dsm = _add_square_delta(
        dem,
        center_x=max(0, width_cells // 3),
        center_y=height_cells // 2,
        half_size=max(1, min(width_cells, height_cells) // 12),
        delta_m=tree_height_m,
    )
    dsm = _add_square_delta(
        dsm,
        center_x=min(width_cells - 1, (width_cells * 2) // 3),
        center_y=height_cells // 2,
        half_size=max(1, min(width_cells, height_cells) // 12),
        delta_m=tree_height_m,
    )
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_FLAT_WITH_TREES,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dsm,
        description="Flat DEM with tree-height DSM canopy patches.",
    )


def create_obstacle_position_variation_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
    obstacle_height_m: float = 25.0,
) -> SyntheticTerrainGrid:
    """Create equal-height DSM obstacles near start, middle, and end positions."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    dsm = dem
    for center_x in _path_position_x_values(width_cells):
        dsm = _add_square_delta(
            dsm,
            center_x=center_x,
            center_y=height_cells // 2,
            half_size=1,
            delta_m=obstacle_height_m,
        )
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_OBSTACLE_POSITION_VARIATION,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dsm,
        description="Equal-height DSM obstacles at multiple path positions.",
    )


def create_operating_radius_boundary_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
) -> SyntheticTerrainGrid:
    """Create flat terrain suited to candidate-grid radius boundary checks."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_OPERATING_RADIUS_BOUNDARY,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dem,
        description="Flat terrain for operating-radius boundary candidate tests.",
    )


def create_fixed_agl_case_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
    plateau_delta_m: float = 20.0,
) -> SyntheticTerrainGrid:
    """Create DEM/DSM terrain with a broad plateau for fixed-AGL reasoning."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    dem = _add_rect_delta(
        dem,
        x_min=width_cells // 4,
        x_max=(width_cells * 3) // 4,
        y_min=height_cells // 4,
        y_max=(height_cells * 3) // 4,
        delta_m=plateau_delta_m,
    )
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_FIXED_AGL_CASE,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dem,
        description="Broad plateau for checking fixed user AGL assumptions later.",
    )


def create_fresnel_radius_position_variation_terrain(
    *,
    width_cells: int = 51,
    height_cells: int = 51,
    grid_size_m: float = 100.0,
    base_dem_msl: float = 50.0,
    obstacle_height_m: float = 22.0,
) -> SyntheticTerrainGrid:
    """Create equal-height DSM obstacles near start, midpoint, and endpoint regions."""

    _validate_grid_size_values(width_cells, height_cells, grid_size_m)
    dem = _constant_matrix(width_cells, height_cells, base_dem_msl)
    dsm = dem
    for center_x in _path_position_x_values(width_cells):
        dsm = _add_square_delta(
            dsm,
            center_x=center_x,
            center_y=height_cells // 2,
            half_size=1,
            delta_m=obstacle_height_m,
        )
    return SyntheticTerrainGrid(
        scenario_name=SCENARIO_FRESNEL_RADIUS_POSITION_VARIATION,
        grid_size_m=grid_size_m,
        dem_msl=dem,
        dsm_msl=dsm,
        description="Equal-height DSM obstacles for later d1/d2 Fresnel-position tests.",
    )


def _validate_grid_size_values(width_cells: int, height_cells: int, grid_size_m: float) -> None:
    if width_cells <= 0:
        raise SyntheticTerrainError("width_cells must be positive.")
    if height_cells <= 0:
        raise SyntheticTerrainError("height_cells must be positive.")
    if grid_size_m <= 0:
        raise SyntheticTerrainError("grid_size_m must be positive.")


def _matrix_shape(matrix: GridMatrix) -> tuple[int, int]:
    if not matrix:
        raise SyntheticTerrainError("matrix must not be empty.")
    width = len(matrix[0])
    if width == 0:
        raise SyntheticTerrainError("matrix rows must not be empty.")
    for row in matrix:
        if len(row) != width:
            raise SyntheticTerrainError("matrix rows must have the same width.")
    return len(matrix), width


def _constant_matrix(width_cells: int, height_cells: int, value: float) -> GridMatrix:
    return tuple(tuple(float(value) for _ in range(width_cells)) for _ in range(height_cells))


def _add_center_obstacle(
    matrix: GridMatrix,
    width_cells: int,
    height_cells: int,
    delta_m: float,
) -> GridMatrix:
    half_size = max(1, min(width_cells, height_cells) // 10)
    return _add_square_delta(
        matrix,
        center_x=width_cells // 2,
        center_y=height_cells // 2,
        half_size=half_size,
        delta_m=delta_m,
    )


def _add_square_delta(
    matrix: GridMatrix,
    *,
    center_x: int,
    center_y: int,
    half_size: int,
    delta_m: float,
) -> GridMatrix:
    return _add_rect_delta(
        matrix,
        x_min=center_x - half_size,
        x_max=center_x + half_size,
        y_min=center_y - half_size,
        y_max=center_y + half_size,
        delta_m=delta_m,
    )


def _add_rect_delta(
    matrix: GridMatrix,
    *,
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    delta_m: float,
) -> GridMatrix:
    height, width = _matrix_shape(matrix)
    clipped_x_min = max(0, x_min)
    clipped_x_max = min(width - 1, x_max)
    clipped_y_min = max(0, y_min)
    clipped_y_max = min(height - 1, y_max)

    rows: list[tuple[float, ...]] = []
    for iy, row in enumerate(matrix):
        new_row: list[float] = []
        for ix, value in enumerate(row):
            if clipped_x_min <= ix <= clipped_x_max and clipped_y_min <= iy <= clipped_y_max:
                new_row.append(value + delta_m)
            else:
                new_row.append(value)
        rows.append(tuple(new_row))
    return tuple(rows)


def _path_position_x_values(width_cells: int) -> tuple[int, int, int]:
    return (
        max(0, width_cells // 8),
        width_cells // 2,
        min(width_cells - 1, (width_cells * 7) // 8),
    )
