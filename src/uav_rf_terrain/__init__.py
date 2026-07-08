"""UAV RF Terrain Planner core package.

This package contains research/education/simulation-oriented helpers for offline
terrain and surface-obstacle RF shielding risk proxy analysis. It does not provide
actual UAV control, real-time flight control, mission success guarantees, or verified
communication quality outputs.
"""

from .config import (
    DEFAULT_SCORE_WEIGHTS,
    DISTANCE_WEIGHT,
    DSM_FRESNEL_WEIGHT,
    DSM_LOS_WEIGHT,
    SHIELDING_WEIGHT,
    ScoreWeights,
)
from .coordinates import (
    CoordinateReference,
    LocalPoint,
    MissingOptionalDependencyError,
    WGS84Point,
    distance_2d_m,
    distance_3d_m,
    local_offset_point,
    mgrs_to_wgs84,
)
from .grid import (
    CandidateCell,
    CandidateGridConfig,
    filter_within_operation_radius,
    generate_candidate_grid,
)
from .schemas import ColorClass, LaunchAreaCellScore, MissionInput, OutputMode, TerrainMode

__all__ = [
    "CandidateCell",
    "CandidateGridConfig",
    "ColorClass",
    "CoordinateReference",
    "DEFAULT_SCORE_WEIGHTS",
    "DISTANCE_WEIGHT",
    "DSM_FRESNEL_WEIGHT",
    "DSM_LOS_WEIGHT",
    "LaunchAreaCellScore",
    "LocalPoint",
    "MissingOptionalDependencyError",
    "MissionInput",
    "OutputMode",
    "SHIELDING_WEIGHT",
    "ScoreWeights",
    "TerrainMode",
    "WGS84Point",
    "distance_2d_m",
    "distance_3d_m",
    "filter_within_operation_radius",
    "generate_candidate_grid",
    "local_offset_point",
    "mgrs_to_wgs84",
]

__version__ = "0.1.0"
