from dataclasses import fields

from uav_rf_terrain import __version__
from uav_rf_terrain.config import (
    DEFAULT_OUTPUT_MODE,
    DEFAULT_SCORE_WEIGHTS,
    DISTANCE_WEIGHT,
    DSM_FRESNEL_WEIGHT,
    DSM_LOS_WEIGHT,
    PROHIBITED_REQUIRED_LINK_METRICS,
    SHIELDING_WEIGHT,
)
from uav_rf_terrain.schemas import (
    ColorClass,
    LaunchAreaCellScore,
    MissionInput,
    OutputMode,
    TerrainMode,
    launch_area_cell_score_field_names,
    mission_input_field_names,
)


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_default_score_weights_match_task_001_baseline() -> None:
    assert DSM_LOS_WEIGHT == 0.40
    assert DSM_FRESNEL_WEIGHT == 0.60
    assert SHIELDING_WEIGHT == 0.80
    assert DISTANCE_WEIGHT == 0.20
    assert DEFAULT_SCORE_WEIGHTS.shielding_component_sum() == 1.0
    assert DEFAULT_SCORE_WEIGHTS.overall_component_sum() == 1.0


def test_default_output_mode_is_color_map_not_top_five() -> None:
    mission = MissionInput(
        target_mgrs="52S DG 00000 00000",
        operating_radius_m=5000.0,
        operating_agl_m=120.0,
        frequency_hz=2_400_000_000.0,
    )
    mission.validate()

    assert mission.terrain_mode is TerrainMode.DSM_PRIMARY
    assert mission.output_mode is OutputMode.COLOR_LAUNCH_AREA_MAP
    assert DEFAULT_OUTPUT_MODE == "color_launch_area_map"


def test_required_schema_excludes_actual_link_measurement_fields() -> None:
    required_names = mission_input_field_names() | launch_area_cell_score_field_names()
    assert required_names.isdisjoint(PROHIBITED_REQUIRED_LINK_METRICS)
    assert "surface_complexity_score" not in required_names
    assert "surface_obstacle_density_score" not in required_names


def test_launch_area_cell_score_is_color_class_oriented() -> None:
    score = LaunchAreaCellScore(
        cell_id="synthetic-cell-001",
        x_m=0.0,
        y_m=0.0,
        distance_3d_m=1000.0,
        within_operation_radius=True,
        dsm_los_score=100.0,
        dsm_fresnel_score=90.0,
        shielding_stability_score=94.0,
        distance_score=80.0,
        overall_score=91.2,
        color_class=ColorClass.GREEN,
    )

    assert score.color_class == ColorClass.GREEN
    assert "offline" in score.notes


def test_mission_input_dataclass_has_no_top_n_default() -> None:
    field_names = {field.name for field in fields(MissionInput)}
    assert "top_n" not in field_names
    assert "ranked_launch_sites" not in field_names
