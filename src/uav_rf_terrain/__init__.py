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
from .schemas import ColorClass, LaunchAreaCellScore, MissionInput, OutputMode, TerrainMode

__all__ = [
    "ColorClass",
    "DEFAULT_SCORE_WEIGHTS",
    "DISTANCE_WEIGHT",
    "DSM_FRESNEL_WEIGHT",
    "DSM_LOS_WEIGHT",
    "LaunchAreaCellScore",
    "MissionInput",
    "OutputMode",
    "SHIELDING_WEIGHT",
    "ScoreWeights",
    "TerrainMode",
]

__version__ = "0.1.0"
