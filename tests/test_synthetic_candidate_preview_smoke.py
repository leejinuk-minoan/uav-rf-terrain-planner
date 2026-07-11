import json
from pathlib import Path

import pytest

from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.map_outputs import build_candidate_cell_map_features
from uav_rf_terrain.scenario_outputs import build_synthetic_end_to_end_scenario
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    SyntheticCandidatePreviewSmokeError,
    SyntheticCandidatePreviewSmokeResult,
    build_synthetic_candidate_mgrs_by_candidate_id,
    build_synthetic_candidate_preview_smoke,
    build_synthetic_candidate_source_zone_metadata_by_candidate_id,
    summarize_synthetic_candidate_preview_smoke,
)

_REQUIRED_METADATA_KEYS = {
    "cell_id",
    "candidate_cell_mgrs",
    "external_coordinate_format",
    "user_coordinate_field",
    "source_zone",
    "source_sensitive",
    "source_zone_reason",
    "internal_debug_available",
}


def _candidate_features():
    scenario = build_synthetic_end_to_end_scenario()
    return build_candidate_cell_map_features(scenario.candidates)


def test_full_synthetic_candidate_preview_smoke_result() -> None:
    result = build_synthetic_candidate_preview_smoke()

    assert isinstance(result, SyntheticCandidatePreviewSmokeResult)
    assert result.scenario_name == "synthetic-e2e-default"
    assert result.candidate_feature_count > 0
    assert result.display_record_count == result.preview_record_count
    assert result.candidate_feature_count == result.display_record_count
    assert result.external_coordinate_format == "MGRS"
    assert result.user_coordinate_field == "candidate_cell_mgrs"


def test_preview_dict_is_json_serializable_and_records_are_list() -> None:
    result = build_synthetic_candidate_preview_smoke()

    serialized = json.dumps(result.preview_dict, ensure_ascii=False)
    assert isinstance(serialized, str)
    assert isinstance(result.preview_dict["records"], list)
    assert result.preview_dict["record_count"] == result.preview_record_count
    assert result.preview_dict["source_sensitive_count"] == (
        result.source_sensitive_count
    )


def test_preview_output_contains_mgrs_policy_and_placeholder_values() -> None:
    result = build_synthetic_candidate_preview_smoke()
    records = result.preview_dict["records"]

    assert isinstance(records, list)
    assert records[0]["candidate_cell_mgrs"] == "52S CG 00000 00000"
    assert records[1]["candidate_cell_mgrs"] == "52S CG 00090 00000"
    assert records[0]["external_coordinate_format"] == "MGRS"
    assert records[0]["user_coordinate_field"] == "candidate_cell_mgrs"
    assert "Candidate display preview" in result.preview_text
    assert "External coordinate format: MGRS" in result.preview_text
    assert "User coordinate field: candidate_cell_mgrs" in result.preview_text
    assert "52S CG 00000 00000" in result.preview_text


def test_preview_dict_and_text_exclude_internal_coordinates() -> None:
    result = build_synthetic_candidate_preview_smoke()
    records = result.preview_dict["records"]

    assert isinstance(records, list)
    assert set(result.preview_dict).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)
    for record in records:
        assert set(record).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)
    for key in INTERNAL_COORDINATE_FIELD_NAMES:
        assert key not in result.preview_text
    assert "EPSG:5179" not in result.preview_text
    assert "WGS84" not in result.preview_text


def test_summary_preserves_counts_and_coordinate_policy() -> None:
    result = build_synthetic_candidate_preview_smoke()
    summary = summarize_synthetic_candidate_preview_smoke(result)

    assert summary["scenario_name"] == result.scenario_name
    assert summary["candidate_feature_count"] == result.candidate_feature_count
    assert summary["display_record_count"] == result.display_record_count
    assert summary["preview_record_count"] == result.preview_record_count
    assert summary["source_sensitive_count"] == result.source_sensitive_count
    assert summary["external_coordinate_format"] == "MGRS"
    assert summary["user_coordinate_field"] == "candidate_cell_mgrs"


def test_max_preview_records_truncates_text_and_reports_omissions() -> None:
    result = build_synthetic_candidate_preview_smoke(max_preview_records=2)

    assert "candidate-green" in result.preview_text
    assert "candidate-yellow" in result.preview_text
    assert "candidate-orange" not in result.preview_text
    assert "... 3 additional record(s) omitted." in result.preview_text
    assert result.preview_record_count == 5


@pytest.mark.parametrize("max_preview_records", [0, -1, True, 1.5, "2"])
def test_invalid_max_preview_records_is_rejected(max_preview_records: object) -> None:
    with pytest.raises((SyntheticCandidatePreviewSmokeError, ValueError)):
        build_synthetic_candidate_preview_smoke(
            max_preview_records=max_preview_records  # type: ignore[arg-type]
        )


def test_placeholder_mgrs_provider_is_deterministic() -> None:
    mapping = build_synthetic_candidate_mgrs_by_candidate_id(
        ("candidate-001", "candidate-002", "candidate-003")
    )

    assert mapping == {
        "candidate-001": "52S CG 00000 00000",
        "candidate-002": "52S CG 00090 00000",
        "candidate-003": "52S CG 00180 00000",
    }


def test_placeholder_mgrs_provider_rejects_empty_and_duplicate_ids() -> None:
    with pytest.raises(SyntheticCandidatePreviewSmokeError):
        build_synthetic_candidate_mgrs_by_candidate_id(())
    with pytest.raises(SyntheticCandidatePreviewSmokeError):
        build_synthetic_candidate_mgrs_by_candidate_id(("candidate-001", " "))
    with pytest.raises(SyntheticCandidatePreviewSmokeError):
        build_synthetic_candidate_mgrs_by_candidate_id(
            ("candidate-001", "candidate-001")
        )


def test_metadata_builder_creates_required_mgrs_source_zone_fields() -> None:
    features = _candidate_features()
    mgrs_mapping = build_synthetic_candidate_mgrs_by_candidate_id(
        tuple(feature.candidate_id for feature in features)
    )
    metadata = build_synthetic_candidate_source_zone_metadata_by_candidate_id(
        features,
        mgrs_mapping,
    )

    assert set(metadata) == {feature.candidate_id for feature in features}
    for feature in features:
        properties = metadata[feature.candidate_id]
        assert _REQUIRED_METADATA_KEYS.issubset(properties)
        assert properties["cell_id"] == feature.candidate_id
        assert properties["candidate_cell_mgrs"] == mgrs_mapping[feature.candidate_id]
        assert properties["external_coordinate_format"] == "MGRS"
        assert properties["user_coordinate_field"] == "candidate_cell_mgrs"
        assert properties["source_zone"] == feature.source_zone.value
        assert properties["source_sensitive"] is feature.source_sensitive
        assert properties["source_zone_reason"] == feature.source_zone_reason
        assert properties["internal_debug_available"] is False
        assert set(properties).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)


def test_metadata_builder_rejects_missing_mgrs_mapping() -> None:
    features = _candidate_features()

    with pytest.raises(SyntheticCandidatePreviewSmokeError):
        build_synthetic_candidate_source_zone_metadata_by_candidate_id(
            features,
            {},
        )


def test_summary_rejects_wrong_result_type() -> None:
    with pytest.raises(SyntheticCandidatePreviewSmokeError):
        summarize_synthetic_candidate_preview_smoke(object())  # type: ignore[arg-type]


def test_smoke_module_has_no_gis_or_rendering_dependency() -> None:
    text = Path(
        "src/uav_rf_terrain/synthetic_candidate_preview_smoke.py"
    ).read_text(encoding="utf-8").lower()
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


def test_smoke_artifacts_contain_no_forbidden_wording() -> None:
    paths = (
        Path("src/uav_rf_terrain/synthetic_candidate_preview_smoke.py"),
        Path("docs/handoff/task-021f-synthetic-candidate-preview-smoke.md"),
        Path(
            "docs/paper/experiments/"
            "EXP-20260711-020-synthetic-candidate-preview-smoke.md"
        ),
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
