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
from .fresnel import (
    FresnelAnalysis,
    FresnelAnalysisError,
    FresnelSample,
    analyze_dsm_fresnel,
    first_fresnel_radius_m,
    wavelength_m,
)
from .grid import (
    CandidateCell,
    CandidateGridConfig,
    filter_within_operation_radius,
    generate_candidate_grid,
)
from .los import (
    LineOfSightAnalysis,
    LineOfSightError,
    LineOfSightSample,
    analyze_dsm_los,
)
from .profile import (
    TerrainProfile,
    TerrainProfileError,
    TerrainProfileSample,
    extract_terrain_profile,
    grid_index_to_local_point,
    local_point_to_grid_index,
)
from .schemas import ColorClass, LaunchAreaCellScore, MissionInput, OutputMode, TerrainMode
from .scoring import (
    CandidateScore,
    ScoreComponentWeights,
    ScoringError,
    clamp_score,
    compute_candidate_score,
    compute_distance_score,
    compute_overall_score,
    compute_shielding_stability_score,
)
from .synthetic import (
    SyntheticTerrainError,
    SyntheticTerrainGrid,
    available_synthetic_scenarios,
    create_flat_terrain,
    create_flat_with_building_terrain,
    create_flat_with_trees_terrain,
    create_fixed_agl_case_terrain,
    create_fresnel_radius_position_variation_terrain,
    create_obstacle_position_variation_terrain,
    create_operating_radius_boundary_terrain,
    create_single_ridge_terrain,
    create_synthetic_terrain,
)

__all__ = [
    "CandidateCell",
    "CandidateGridConfig",
    "CandidateScore",
    "ColorClass",
    "CoordinateReference",
    "DEFAULT_SCORE_WEIGHTS",
    "DISTANCE_WEIGHT",
    "DSM_FRESNEL_WEIGHT",
    "DSM_LOS_WEIGHT",
    "FresnelAnalysis",
    "FresnelAnalysisError",
    "FresnelSample",
    "LaunchAreaCellScore",
    "LineOfSightAnalysis",
    "LineOfSightError",
    "LineOfSightSample",
    "LocalPoint",
    "MissingOptionalDependencyError",
    "MissionInput",
    "OutputMode",
    "SHIELDING_WEIGHT",
    "ScoreComponentWeights",
    "ScoreWeights",
    "ScoringError",
    "SyntheticTerrainError",
    "SyntheticTerrainGrid",
    "TerrainMode",
    "TerrainProfile",
    "TerrainProfileError",
    "TerrainProfileSample",
    "WGS84Point",
    "analyze_dsm_fresnel",
    "analyze_dsm_los",
    "available_synthetic_scenarios",
    "clamp_score",
    "compute_candidate_score",
    "compute_distance_score",
    "compute_overall_score",
    "compute_shielding_stability_score",
    "create_flat_terrain",
    "create_flat_with_building_terrain",
    "create_flat_with_trees_terrain",
    "create_fixed_agl_case_terrain",
    "create_fresnel_radius_position_variation_terrain",
    "create_obstacle_position_variation_terrain",
    "create_operating_radius_boundary_terrain",
    "create_single_ridge_terrain",
    "create_synthetic_terrain",
    "distance_2d_m",
    "distance_3d_m",
    "extract_terrain_profile",
    "filter_within_operation_radius",
    "first_fresnel_radius_m",
    "generate_candidate_grid",
    "grid_index_to_local_point",
    "local_offset_point",
    "local_point_to_grid_index",
    "mgrs_to_wgs84",
    "wavelength_m",
]

__version__ = "0.1.0"
