from pathlib import Path

import pytest

from uav_rf_terrain.coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    CoordinateIoPolicyError,
    is_internal_coordinate_field,
    is_user_facing_mgrs_field,
    require_mgrs_external_coordinate_field,
)


def test_external_coordinate_format_is_mgrs() -> None:
    assert EXTERNAL_COORDINATE_FORMAT == "MGRS"


@pytest.mark.parametrize(
    "field_name",
    (
        "target_mgrs",
        "launch_site_mgrs",
        "waypoint_mgrs",
        "candidate_cell_mgrs",
        "selected_route_waypoint_mgrs",
    ),
)
def test_user_facing_mgrs_fields_are_recognized(field_name: str) -> None:
    assert is_user_facing_mgrs_field(field_name)
    assert not is_internal_coordinate_field(field_name)


@pytest.mark.parametrize(
    "field_name",
    (
        "x_m",
        "y_m",
        "row",
        "col",
        "epsg5179_x_m",
        "epsg5179_y_m",
    ),
)
def test_internal_coordinate_fields_are_recognized(field_name: str) -> None:
    assert is_internal_coordinate_field(field_name)
    assert not is_user_facing_mgrs_field(field_name)


def test_require_mgrs_external_coordinate_field_accepts_mgrs_field() -> None:
    require_mgrs_external_coordinate_field("target_mgrs")


@pytest.mark.parametrize("field_name", ("x_m", "row"))
def test_require_mgrs_external_coordinate_field_rejects_internal_fields(field_name: str) -> None:
    with pytest.raises(CoordinateIoPolicyError):
        require_mgrs_external_coordinate_field(field_name)


def test_require_mgrs_external_coordinate_field_rejects_unknown_field() -> None:
    with pytest.raises(CoordinateIoPolicyError):
        require_mgrs_external_coordinate_field("target_x")


def test_policy_document_contains_required_boundary_terms() -> None:
    policy_text = Path("docs/architecture/mgrs-external-io-policy.md").read_text(
        encoding="utf-8"
    )

    assert "External input" in policy_text
    assert "External output" in policy_text
    assert "internal/debug" in policy_text
    assert "target_mgrs" in policy_text
    assert "candidate_cell_mgrs" in policy_text
    assert "waypoint_mgrs" in policy_text


def test_readme_or_policy_mentions_map_waypoint_scenario_coordinate_boundary() -> None:
    readme_text = Path("README.md").read_text(encoding="utf-8")
    policy_text = Path("docs/architecture/mgrs-external-io-policy.md").read_text(
        encoding="utf-8"
    )
    combined = f"{readme_text}\n{policy_text}"

    assert "map popup" in combined
    assert "waypoint" in combined
    assert "scenario" in combined.lower()
    assert "MGRS" in combined


def test_new_files_do_not_add_forbidden_wording() -> None:
    forbidden_phrases = (
        "실제 통신 성공률" + " 예측",
        "RSSI" + " 예측",
        "SINR" + " 예측",
        "packet loss" + " 예측",
        "실측 검증" + " 완료",
        "정찰 성공" + " 보장",
        "통신 가능" + " 보장",
        "실제 비행 가능" + " 보장",
        "공역승인 최적고도" + " 보장",
        "guaranteed " + "communication",
        "guaranteed " + "reconnaissance",
        "guaranteed " + "flight safety",
        "airspace approval " + "guarantee",
        "control-system command " + "output",
        "vehicle-execution command " + "output",
        "autopilot " + "integration",
        "flight command " + "generation",
    )
    paths = (
        Path("docs/architecture/mgrs-external-io-policy.md"),
        Path("src/uav_rf_terrain/coordinate_io_policy.py"),
        Path("docs/paper/experiments/EXP-20260711-014-mgrs-external-io-policy.md"),
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in text
