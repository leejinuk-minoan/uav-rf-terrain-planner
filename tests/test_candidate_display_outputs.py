from pathlib import Path

import pytest

from uav_rf_terrain.candidate_display_outputs import (
    CandidateDisplayBundle,
    CandidateDisplayOutputError,
    CandidateDisplayRecord,
    build_candidate_display_records,
    build_candidate_display_records_by_candidate_id,
    summarize_candidate_display_records,
)
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.map_outputs import CandidateCellMapFeature, style_for_color_class
from uav_rf_terrain.schemas import ColorClass


def _metadata(
    *,
    mgrs: str = "52S CG 00000 00000",
    source_zone: str = "esa_derived",
    source_sensitive: bool = False,
) -> dict[str, str | bool]:
    return {
        "cell_id": "candidate-001",
        "candidate_cell_mgrs": mgrs,
        "external_coordinate_format": "MGRS",
        "user_coordinate_field": "candidate_cell_mgrs",
        "source_zone": source_zone,
        "source_sensitive": source_sensitive,
        "source_zone_reason": "Synthetic source-zone metadata.",
        "internal_debug_available": True,
    }


def _feature(
    candidate_id: str = "candidate-001",
    *,
    color_class: ColorClass = ColorClass.GREEN,
    mgrs: str = "52S CG 00000 00000",
    source_zone: str = "esa_derived",
    source_sensitive: bool = False,
) -> CandidateCellMapFeature:
    return CandidateCellMapFeature(
        feature_id=f"feature-{candidate_id}",
        candidate_id=candidate_id,
        x_m=100.0,
        y_m=200.0,
        color_class=color_class,
        style=style_for_color_class(color_class),
        overall_score=88.0,
        shielding_stability_score=91.0,
        reason="Synthetic candidate reason.",
        candidate_source_zone_map_properties=_metadata(
            mgrs=mgrs,
            source_zone=source_zone,
            source_sensitive=source_sensitive,
        ),
    )


def _inject_metadata(
    feature: CandidateCellMapFeature,
    metadata: dict[str, str | bool],
) -> CandidateCellMapFeature:
    object.__setattr__(feature, "candidate_source_zone_map_properties", metadata)
    return feature


def test_candidate_feature_with_metadata_builds_display_record() -> None:
    bundle = build_candidate_display_records((_feature(),))
    record = bundle.records[0]

    assert isinstance(record, CandidateDisplayRecord)
    assert record.candidate_id == "candidate-001"
    assert record.candidate_cell_mgrs == "52S CG 00000 00000"
    assert record.external_coordinate_format == "MGRS"
    assert record.user_coordinate_field == "candidate_cell_mgrs"


def test_display_dict_uses_primitive_user_facing_values() -> None:
    record = build_candidate_display_records((_feature(),)).records[0]
    display = record.to_display_dict()

    assert display["candidate_cell_mgrs"] == "52S CG 00000 00000"
    assert display["external_coordinate_format"] == "MGRS"
    assert display["user_coordinate_field"] == "candidate_cell_mgrs"
    assert display["color_class"] == "green"
    assert display["source_zone"] == "esa_derived"
    assert display["overall_score"] == 88.0
    assert display["shielding_stability_score"] == 91.0
    assert display["candidate_reason"] == "Synthetic candidate reason."
    assert display.keys().isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)


def test_display_label_contains_mgrs_and_no_internal_geometry() -> None:
    record = build_candidate_display_records((_feature(),)).records[0]

    assert record.display_label == (
        "candidate-001 | 52S CG 00000 00000 | green"
    )
    assert "x_m" not in record.display_label
    assert "y_m" not in record.display_label
    assert "100.0" not in record.display_label
    assert "200.0" not in record.display_label


def test_source_zone_and_candidate_fields_are_preserved() -> None:
    record = build_candidate_display_records(
        (
            _feature(
                source_zone="mixed_boundary",
                source_sensitive=True,
            ),
        )
    ).records[0]

    assert record.source_zone == "mixed_boundary"
    assert record.source_sensitive is True
    assert record.source_zone_reason == "Synthetic source-zone metadata."
    assert record.color_name == "green"


def test_summary_reports_source_sensitive_and_color_counts() -> None:
    features = (
        _feature("green", color_class=ColorClass.GREEN),
        _feature("yellow", color_class=ColorClass.YELLOW),
        _feature(
            "orange",
            color_class=ColorClass.ORANGE,
            source_zone="wms_gap_filled",
            source_sensitive=True,
        ),
        _feature(
            "red",
            color_class=ColorClass.RED,
            source_zone="dem_only_fallback",
            source_sensitive=True,
        ),
        _feature("excluded", color_class=ColorClass.EXCLUDED),
    )
    bundle = build_candidate_display_records(features)
    summary = summarize_candidate_display_records(bundle)

    assert summary["candidate_display_record_count"] == 5
    assert summary["candidate_display_external_coordinate_format"] == "MGRS"
    assert summary["candidate_display_user_coordinate_field"] == (
        "candidate_cell_mgrs"
    )
    assert summary["candidate_display_source_sensitive_count"] == 2
    assert summary["green_candidate_display_count"] == 1
    assert summary["yellow_candidate_display_count"] == 1
    assert summary["orange_candidate_display_count"] == 1
    assert summary["red_candidate_display_count"] == 1
    assert summary["excluded_candidate_display_count"] == 1


def test_by_candidate_id_mapping_uses_display_dict() -> None:
    bundle = build_candidate_display_records(
        (
            _feature("candidate-001", mgrs="52S CG 00000 00000"),
            _feature("candidate-002", mgrs="52S CG 00090 00000"),
        )
    )
    mapped = build_candidate_display_records_by_candidate_id(bundle)

    assert set(mapped) == {"candidate-001", "candidate-002"}
    assert mapped["candidate-002"]["candidate_cell_mgrs"] == (
        "52S CG 00090 00000"
    )


def test_duplicate_candidate_id_is_rejected() -> None:
    record = build_candidate_display_records((_feature(),)).records[0]
    bundle = CandidateDisplayBundle(
        records=(record, record),
        source_sensitive_count=0,
        reason="Duplicate test bundle.",
    )

    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records_by_candidate_id(bundle)


def test_feature_without_attached_metadata_is_rejected() -> None:
    feature = CandidateCellMapFeature(
        feature_id="feature-no-metadata",
        candidate_id="candidate-no-metadata",
        x_m=100.0,
        y_m=200.0,
        color_class=ColorClass.GREEN,
        style=style_for_color_class(ColorClass.GREEN),
        overall_score=88.0,
        shielding_stability_score=91.0,
        reason="Synthetic candidate reason.",
    )

    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records((feature,))


def test_empty_candidate_features_are_rejected() -> None:
    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records(())


@pytest.mark.parametrize("blocked_key", sorted(INTERNAL_COORDINATE_FIELD_NAMES))
def test_internal_coordinate_metadata_key_is_rejected(blocked_key: str) -> None:
    feature = _feature()
    metadata = dict(feature.candidate_source_zone_map_properties)
    metadata[blocked_key] = "blocked"
    _inject_metadata(feature, metadata)

    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records((feature,))


def test_non_mgrs_external_coordinate_format_is_rejected() -> None:
    feature = _feature()
    metadata = dict(feature.candidate_source_zone_map_properties)
    metadata["external_coordinate_format"] = "EPSG:5179"
    _inject_metadata(feature, metadata)

    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records((feature,))


def test_wrong_user_coordinate_field_is_rejected() -> None:
    feature = _feature()
    metadata = dict(feature.candidate_source_zone_map_properties)
    metadata["user_coordinate_field"] = "x_m"
    _inject_metadata(feature, metadata)

    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records((feature,))


def test_empty_candidate_cell_mgrs_is_rejected() -> None:
    feature = _feature()
    metadata = dict(feature.candidate_source_zone_map_properties)
    metadata["candidate_cell_mgrs"] = " "
    _inject_metadata(feature, metadata)

    with pytest.raises(CandidateDisplayOutputError):
        build_candidate_display_records((feature,))


def test_candidate_display_module_has_no_gis_or_rendering_dependency() -> None:
    text = Path("src/uav_rf_terrain/candidate_display_outputs.py").read_text(
        encoding="utf-8"
    ).lower()
    blocked = (
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "fo" + "lium",
        "stream" + "lit",
        "q" + "gis",
        "html" + ".",
        "markdown" + ".",
    )
    for term in blocked:
        assert term not in text


def test_display_outputs_contain_no_forbidden_wording() -> None:
    paths = (
        Path("src/uav_rf_terrain/candidate_display_outputs.py"),
        Path("docs/handoff/task-021d-candidate-display-formatter.md"),
        Path("docs/paper/experiments/EXP-20260711-018-candidate-display-formatter.md"),
    )
    blocked = (
        "guaranteed " + "communication",
        "guaranteed " + "reconnaissance",
        "guaranteed " + "flight safety",
        "airspace approval " + "guarantee",
        "autopilot " + "integration",
        "flight command " + "generation",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for term in blocked:
            assert term not in text
