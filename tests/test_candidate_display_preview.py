import json
from pathlib import Path

import pytest

from uav_rf_terrain.candidate_display_outputs import (
    CandidateDisplayBundle,
    CandidateDisplayRecord,
)
from uav_rf_terrain.candidate_display_preview import (
    CandidateDisplayPreview,
    CandidateDisplayPreviewError,
    build_candidate_display_preview,
    build_candidate_display_preview_dict,
    format_candidate_display_preview,
)
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.schemas import ColorClass


def _record(
    candidate_id: str,
    mgrs: str,
    color_class: ColorClass,
    score: float,
    source_zone: str,
    *,
    source_sensitive: bool = False,
) -> CandidateDisplayRecord:
    return CandidateDisplayRecord(
        candidate_id=candidate_id,
        candidate_cell_mgrs=mgrs,
        external_coordinate_format="MGRS",
        user_coordinate_field="candidate_cell_mgrs",
        color_class=color_class,
        color_name=color_class.value,
        overall_score=score,
        shielding_stability_score=max(score - 2.0, 0.0),
        source_zone=source_zone,
        source_sensitive=source_sensitive,
        source_zone_reason="Synthetic source-zone reason.",
        candidate_reason="Synthetic candidate reason.",
        display_label=f"{candidate_id} | {mgrs} | {color_class.value}",
    )


def _bundle() -> CandidateDisplayBundle:
    records = (
        _record(
            "candidate-001",
            "52S CG 00000 00000",
            ColorClass.GREEN,
            88.0,
            "esa_derived",
        ),
        _record(
            "candidate-002",
            "52S CG 00090 00000",
            ColorClass.YELLOW,
            72.0,
            "wms_gap_filled",
            source_sensitive=True,
        ),
        _record(
            "candidate-003",
            "52S CG 00180 00000",
            ColorClass.RED,
            45.0,
            "dem_only_fallback",
            source_sensitive=True,
        ),
    )
    return CandidateDisplayBundle(
        records=records,
        source_sensitive_count=2,
        reason="Synthetic candidate display bundle.",
    )


def test_display_bundle_builds_preview_object() -> None:
    preview = build_candidate_display_preview(_bundle())

    assert isinstance(preview, CandidateDisplayPreview)
    assert preview.title == "Candidate display preview"
    assert preview.external_coordinate_format == "MGRS"
    assert preview.user_coordinate_field == "candidate_cell_mgrs"
    assert preview.record_count == 3
    assert preview.source_sensitive_count == 2
    assert len(preview.records) == 3


def test_preview_dict_is_json_serializable_and_uses_primitives() -> None:
    preview_dict = build_candidate_display_preview_dict(_bundle())

    serialized = json.dumps(preview_dict, ensure_ascii=False)
    assert isinstance(serialized, str)
    assert isinstance(preview_dict["records"], list)
    assert isinstance(preview_dict["summary"], dict)
    assert preview_dict["external_coordinate_format"] == "MGRS"
    assert preview_dict["user_coordinate_field"] == "candidate_cell_mgrs"


def test_preview_dict_preserves_mgrs_and_summary_fields() -> None:
    preview_dict = build_candidate_display_preview_dict(_bundle())
    records = preview_dict["records"]
    summary = preview_dict["summary"]

    assert isinstance(records, list)
    assert records[0]["candidate_cell_mgrs"] == "52S CG 00000 00000"
    assert records[1]["external_coordinate_format"] == "MGRS"
    assert records[2]["user_coordinate_field"] == "candidate_cell_mgrs"
    assert isinstance(summary, dict)
    assert summary["candidate_display_record_count"] == 3
    assert summary["candidate_display_source_sensitive_count"] == 2
    assert summary["green_candidate_display_count"] == 1
    assert summary["yellow_candidate_display_count"] == 1
    assert summary["red_candidate_display_count"] == 1


def test_preview_dict_and_records_exclude_internal_coordinates() -> None:
    preview_dict = build_candidate_display_preview_dict(_bundle())
    records = preview_dict["records"]

    assert isinstance(records, list)
    assert set(preview_dict).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)
    for record in records:
        assert set(record).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)


def test_plain_text_preview_includes_mgrs_and_display_values() -> None:
    text = format_candidate_display_preview(_bundle())

    assert "Candidate display preview" in text
    assert "External coordinate format: MGRS" in text
    assert "User coordinate field: candidate_cell_mgrs" in text
    assert "52S CG 00000 00000" in text
    assert "score=88.0" in text
    assert "source_zone=esa_derived" in text
    assert "candidate-002 | 52S CG 00090 00000 | yellow" in text


def test_plain_text_preview_excludes_internal_geometry() -> None:
    text = format_candidate_display_preview(_bundle())

    for key in INTERNAL_COORDINATE_FIELD_NAMES:
        assert key not in text
    assert "100.0" not in text
    assert "200.0" not in text


def test_plain_text_max_records_limits_output_and_reports_omissions() -> None:
    text = format_candidate_display_preview(_bundle(), max_records=1)

    assert "candidate-001" in text
    assert "candidate-002" not in text
    assert "candidate-003" not in text
    assert "... 2 additional record(s) omitted." in text


def test_plain_text_max_records_larger_than_bundle_has_no_omission_line() -> None:
    text = format_candidate_display_preview(_bundle(), max_records=10)

    assert "candidate-001" in text
    assert "candidate-002" in text
    assert "candidate-003" in text
    assert "omitted" not in text


@pytest.mark.parametrize("max_records", [0, -1, True, 1.5, "1"])
def test_invalid_max_records_is_rejected(max_records: object) -> None:
    with pytest.raises(CandidateDisplayPreviewError):
        format_candidate_display_preview(_bundle(), max_records=max_records)  # type: ignore[arg-type]


def test_wrong_bundle_type_is_rejected() -> None:
    with pytest.raises(CandidateDisplayPreviewError):
        build_candidate_display_preview("not-a-bundle")  # type: ignore[arg-type]

    with pytest.raises(CandidateDisplayPreviewError):
        build_candidate_display_preview_dict(object())  # type: ignore[arg-type]

    with pytest.raises(CandidateDisplayPreviewError):
        format_candidate_display_preview(None)  # type: ignore[arg-type]


def test_preview_module_has_no_gis_or_rendering_dependency() -> None:
    text = Path("src/uav_rf_terrain/candidate_display_preview.py").read_text(
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


def test_preview_artifacts_contain_no_forbidden_wording() -> None:
    paths = (
        Path("src/uav_rf_terrain/candidate_display_preview.py"),
        Path("docs/handoff/task-021e-candidate-display-preview.md"),
        Path("docs/paper/experiments/EXP-20260711-019-candidate-display-preview.md"),
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
