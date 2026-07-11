from pathlib import Path

import pytest

from uav_rf_terrain.map_outputs import (
    CandidateCellMapFeature,
    MapOutputError,
    attach_candidate_source_zone_map_properties,
    build_candidate_cell_map_features,
    build_map_output_package,
    format_map_output_summary,
    style_for_color_class,
    summarize_map_output_package,
)
from uav_rf_terrain.scenario_outputs import build_synthetic_end_to_end_scenario
from uav_rf_terrain.schemas import ColorClass


_INTERNAL_COORDINATE_KEYS = {
    "x_m",
    "y_m",
    "row",
    "col",
    "epsg5179_x_m",
    "epsg5179_y_m",
    "wgs84_lat",
    "wgs84_lon",
    "local_x_m",
    "local_y_m",
    "raster_row",
    "raster_col",
}


def _feature(candidate_id: str = "cell-001") -> CandidateCellMapFeature:
    return CandidateCellMapFeature(
        feature_id=f"feature-{candidate_id}",
        candidate_id=candidate_id,
        x_m=100.0,
        y_m=200.0,
        color_class=ColorClass.GREEN,
        style=style_for_color_class(ColorClass.GREEN),
        overall_score=90.0,
        shielding_stability_score=95.0,
        reason="synthetic candidate",
    )


def _metadata(
    cell_id: str,
    *,
    mgrs: str = "52S CG 00000 00000",
) -> dict[str, str | bool]:
    return {
        "cell_id": cell_id,
        "candidate_cell_mgrs": mgrs,
        "external_coordinate_format": "MGRS",
        "user_coordinate_field": "candidate_cell_mgrs",
        "source_zone": "esa_derived",
        "source_sensitive": False,
        "source_zone_reason": "ESA-derived source zone only.",
        "internal_debug_available": True,
    }


def _scenario_metadata() -> dict[str, dict[str, str | bool]]:
    scenario = build_synthetic_end_to_end_scenario()
    candidate_features = build_candidate_cell_map_features(scenario.candidates)
    return {
        feature.candidate_id: _metadata(
            feature.candidate_id,
            mgrs=f"52S CG {index:05d} 00000",
        )
        for index, feature in enumerate(candidate_features)
    }


def test_existing_candidate_feature_constructor_remains_backward_compatible() -> None:
    feature = _feature()

    assert feature.candidate_source_zone_map_properties == {}
    assert feature.x_m == 100.0
    assert feature.y_m == 200.0


def test_existing_build_map_output_package_call_still_works() -> None:
    package = build_map_output_package(build_synthetic_end_to_end_scenario())

    assert package.candidate_features
    assert all(
        not feature.candidate_source_zone_map_properties
        for feature in package.candidate_features
    )
    assert (
        package.summary[
            "candidate_source_zone_map_properties_external_coordinate_format"
        ]
        == "not_attached"
    )


def test_attach_properties_matches_candidate_id() -> None:
    features = (_feature("cell-001"),)
    attached = attach_candidate_source_zone_map_properties(
        features,
        {"cell-001": _metadata("cell-001")},
    )

    properties = attached[0].candidate_source_zone_map_properties
    assert properties["candidate_cell_mgrs"] == "52S CG 00000 00000"
    assert properties["external_coordinate_format"] == "MGRS"
    assert properties["user_coordinate_field"] == "candidate_cell_mgrs"
    assert properties["source_zone"] == "esa_derived"
    assert properties["source_sensitive"] is False
    assert properties["source_zone_reason"] == "ESA-derived source zone only."
    assert properties.keys().isdisjoint(_INTERNAL_COORDINATE_KEYS)


def test_attach_properties_copies_input_mapping() -> None:
    source = _metadata("cell-001")
    attached = attach_candidate_source_zone_map_properties(
        (_feature("cell-001"),),
        {"cell-001": source},
    )
    source["candidate_cell_mgrs"] = "changed"

    assert (
        attached[0].candidate_source_zone_map_properties["candidate_cell_mgrs"]
        == "52S CG 00000 00000"
    )


def test_require_all_true_rejects_missing_metadata() -> None:
    with pytest.raises(MapOutputError):
        attach_candidate_source_zone_map_properties(
            (_feature("cell-001"), _feature("cell-002")),
            {"cell-001": _metadata("cell-001")},
        )


def test_require_all_false_preserves_feature_without_metadata() -> None:
    features = (_feature("cell-001"), _feature("cell-002"))
    attached = attach_candidate_source_zone_map_properties(
        features,
        {"cell-001": _metadata("cell-001")},
        require_all=False,
    )

    assert attached[0].candidate_source_zone_map_properties
    assert attached[1] is features[1]
    assert not attached[1].candidate_source_zone_map_properties


def test_extra_metadata_key_is_allowed() -> None:
    attached = attach_candidate_source_zone_map_properties(
        (_feature("cell-001"),),
        {
            "cell-001": _metadata("cell-001"),
            "unused-cell": _metadata("unused-cell"),
        },
    )

    assert len(attached) == 1


@pytest.mark.parametrize("blocked_key", sorted(_INTERNAL_COORDINATE_KEYS))
def test_internal_coordinate_key_in_metadata_is_rejected(blocked_key: str) -> None:
    metadata = _metadata("cell-001")
    metadata[blocked_key] = "blocked"

    with pytest.raises(MapOutputError):
        attach_candidate_source_zone_map_properties(
            (_feature("cell-001"),),
            {"cell-001": metadata},
        )


def test_non_mgrs_external_coordinate_format_is_rejected() -> None:
    metadata = _metadata("cell-001")
    metadata["external_coordinate_format"] = "EPSG:5179"

    with pytest.raises(MapOutputError):
        attach_candidate_source_zone_map_properties(
            (_feature("cell-001"),),
            {"cell-001": metadata},
        )


def test_wrong_user_coordinate_field_is_rejected() -> None:
    metadata = _metadata("cell-001")
    metadata["user_coordinate_field"] = "x_m"

    with pytest.raises(MapOutputError):
        attach_candidate_source_zone_map_properties(
            (_feature("cell-001"),),
            {"cell-001": metadata},
        )


def test_empty_candidate_cell_mgrs_is_rejected() -> None:
    metadata = _metadata("cell-001")
    metadata["candidate_cell_mgrs"] = " "

    with pytest.raises(MapOutputError):
        attach_candidate_source_zone_map_properties(
            (_feature("cell-001"),),
            {"cell-001": metadata},
        )


def test_summary_reports_attached_and_missing_counts() -> None:
    package = build_map_output_package(build_synthetic_end_to_end_scenario())
    partially_attached_features = attach_candidate_source_zone_map_properties(
        package.candidate_features,
        {
            package.candidate_features[0].candidate_id: _metadata(
                package.candidate_features[0].candidate_id
            )
        },
        require_all=False,
    )
    partial_package = type(package)(
        scenario_name=package.scenario_name,
        candidate_features=partially_attached_features,
        route_features=package.route_features,
        waypoint_features=package.waypoint_features,
        selected_route_id=package.selected_route_id,
        summary={},
    )
    summary = summarize_map_output_package(partial_package)

    assert summary["candidate_source_zone_map_properties_feature_count"] == 1
    assert summary["candidate_source_zone_map_properties_missing_feature_count"] == (
        len(package.candidate_features) - 1
    )
    assert (
        summary["candidate_source_zone_map_properties_external_coordinate_format"]
        == "MGRS"
    )
    assert (
        summary["candidate_source_zone_map_properties_user_coordinate_field"]
        == "candidate_cell_mgrs"
    )


def test_build_map_output_package_accepts_optional_metadata_path() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    package = build_map_output_package(
        scenario,
        candidate_source_zone_metadata_by_cell_id=_scenario_metadata(),
    )

    assert all(
        feature.candidate_source_zone_map_properties
        for feature in package.candidate_features
    )
    assert package.summary["candidate_source_zone_map_properties_feature_count"] == len(
        package.candidate_features
    )
    assert package.summary["candidate_source_zone_map_properties_missing_feature_count"] == 0
    assert (
        package.summary[
            "candidate_source_zone_map_properties_external_coordinate_format"
        ]
        == "MGRS"
    )


def test_format_summary_mentions_attachment_counts_and_rendering_boundary() -> None:
    scenario = build_synthetic_end_to_end_scenario()
    package = build_map_output_package(
        scenario,
        candidate_source_zone_metadata_by_cell_id=_scenario_metadata(),
    )
    text = format_map_output_summary(package)

    assert "Candidate source-zone map metadata: attached=" in text
    assert "This is map-ready data, not a rendered map." in text


def test_map_outputs_has_no_gis_or_rendering_dependency_imports() -> None:
    text = Path("src/uav_rf_terrain/map_outputs.py").read_text(encoding="utf-8").lower()
    blocked_imports = (
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "fo" + "lium",
        "stream" + "lit",
        "os" + "geo",
    )

    for blocked_import in blocked_imports:
        assert blocked_import not in text


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
        Path("src/uav_rf_terrain/map_outputs.py"),
        Path("docs/handoff/task-021c-map-output-source-zone-properties.md"),
        Path("docs/paper/experiments/EXP-20260711-017-map-output-source-zone-properties.md"),
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in text
