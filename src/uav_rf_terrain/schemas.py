"""Schema dataclasses for UAV RF Terrain Planner MVP scaffolding.

These schemas describe offline analysis inputs and color-map oriented outputs. They
intentionally avoid required real-link fields such as RSSI, SINR, and packet loss.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import StrEnum


class TerrainMode(StrEnum):
    """Terrain/surface data mode for offline proxy analysis."""

    DSM_PRIMARY = "dsm_primary"
    DEM_FALLBACK = "dem_fallback"
    SYNTHETIC = "synthetic"


class OutputMode(StrEnum):
    """Supported output modes.

    The default is a color launch-area map layer. Ranked point lists are allowed only
    as debugging/validation support, not as the user-facing default output.
    """

    COLOR_LAUNCH_AREA_MAP = "color_launch_area_map"
    DEBUG_SCORE_TABLE = "debug_score_table"


class ColorClass(StrEnum):
    """Color classes for launch-area map visualization."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class MissionInput:
    """MVP mission input schema for offline proxy analysis.

    Args:
        target_mgrs: Target MGRS coordinate string. Coordinate conversion is Task 002.
        operating_radius_m: UAV operating radius in meters.
        operating_agl_m: User-provided fixed operating altitude above ground level in meters.
        frequency_hz: Communication center frequency in hertz for later Fresnel analysis.
        terrain_mode: DSM-primary, DEM fallback, or synthetic terrain mode.
        output_mode: Default output remains a color launch-area map layer.
    """

    target_mgrs: str
    operating_radius_m: float
    operating_agl_m: float
    frequency_hz: float
    terrain_mode: TerrainMode = TerrainMode.DSM_PRIMARY
    output_mode: OutputMode = OutputMode.COLOR_LAUNCH_AREA_MAP

    def validate(self) -> None:
        """Validate basic positive numeric inputs and safe default output mode."""

        if not self.target_mgrs.strip():
            raise ValueError("target_mgrs must not be empty.")
        if self.operating_radius_m <= 0:
            raise ValueError("operating_radius_m must be positive.")
        if self.operating_agl_m <= 0:
            raise ValueError("operating_agl_m must be positive.")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive.")


@dataclass(frozen=True)
class ScoreInputs:
    """Inputs for future Task 006 score calculation.

    Args:
        dsm_los_score: DSM-based LOS proxy score on a 0-100 scale.
        dsm_fresnel_score: DSM-based Fresnel clearance proxy score on a 0-100 scale.
        distance_3d_m: 3D distance to target in meters.
        operating_radius_m: UAV operating radius in meters.
        within_operation_radius: Whether the candidate is inside the operating radius.
    """

    dsm_los_score: float
    dsm_fresnel_score: float
    distance_3d_m: float
    operating_radius_m: float
    within_operation_radius: bool = True


@dataclass(frozen=True)
class LaunchAreaCellScore:
    """Color-map cell output schema for a launch-area candidate.

    This is a map-layer oriented schema. It is not a Top-N launch-site recommendation
    schema and does not claim actual communication success.
    """

    cell_id: str
    x_m: float
    y_m: float
    distance_3d_m: float
    within_operation_radius: bool
    dsm_los_score: float
    dsm_fresnel_score: float
    shielding_stability_score: float
    distance_score: float
    overall_score: float
    color_class: ColorClass
    notes: str = "offline terrain/surface-obstacle risk proxy"


@dataclass(frozen=True)
class SyntheticTerrainMetadata:
    """Metadata for synthetic DEM/DSM examples.

    Args:
        scenario_name: Synthetic scenario identifier.
        grid_size_m: Cell size in meters.
        width_cells: Number of grid cells on the x axis.
        height_cells: Number of grid cells on the y axis.
        uses_real_dem: Always false for Task 001 synthetic scaffolding.
        uses_real_dsm: Always false for Task 001 synthetic scaffolding.
    """

    scenario_name: str
    grid_size_m: float
    width_cells: int
    height_cells: int
    uses_real_dem: bool = False
    uses_real_dsm: bool = False


def mission_input_field_names() -> set[str]:
    """Return MissionInput field names for tests and documentation checks."""

    return {field.name for field in fields(MissionInput)}


def launch_area_cell_score_field_names() -> set[str]:
    """Return LaunchAreaCellScore field names for tests and documentation checks."""

    return {field.name for field in fields(LaunchAreaCellScore)}
