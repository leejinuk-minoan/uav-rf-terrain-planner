from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.fresnel_diagnostics import DIAGNOSTIC_FIELD_ORDER
from uav_rf_terrain.preview_appendix_table import (
    PreviewAppendixTableError,
    format_fresnel_diagnostics_appendix_table,
    format_preview_appendix_table,
)
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    build_synthetic_candidate_preview_smoke,
)


TABLE_COLUMNS = (
    "row_no",
    "candidate_id",
    "candidate_cell_mgrs",
    "color_class",
    "color_name",
    "overall_score",
    "shielding_stability_score",
    "source_zone",
    "source_sensitive",
    "source_zone_reason",
    "candidate_reason",
)

DIAGNOSTIC_COLUMNS = (
    "row_no",
    "candidate_id",
    "candidate_cell_mgrs",
    "diagnostic_status",
    *DIAGNOSTIC_FIELD_ORDER,
)

DIAGNOSTIC_VALUES = {
    "average_fresnel_score": 95.123456,
    "worst_obstacle_score": 32.149,
    "dominant_obstacle_distance_from_start_m": 123.456,
    "dominant_obstacle_dsm_msl": 87.654,
    "dominant_obstacle_los_msl": 90.123,
    "dominant_obstacle_clearance_m": 2.469,
    "dominant_obstacle_clearance_ratio": 0.32149,
    "dominant_obstacle_fresnel_radius_m": 7.681,
    "dominant_obstacle_nu": -0.45419,
    "dominant_obstacle_diffraction_loss_db": 1.23456,
}


def _preview() -> dict[str, object]:
    return deepcopy(build_synthetic_candidate_preview_smoke().preview_dict)


def test_valid_preview_produces_all_columns_and_preserves_order() -> None:
    preview = _preview()
    table = format_preview_appendix_table(preview)
    assert isinstance(table, str)
    header = table.splitlines()[0]
    assert all(column in header for column in TABLE_COLUMNS)
    positions = [table.index(record["candidate_id"]) for record in preview["records"]]
    assert positions == sorted(positions)
    assert "| 1 | candidate-green |" in table
    assert "| 5 | candidate-excluded-out-of-radius |" in table


def test_mgrs_scores_and_source_metadata_are_displayed_without_recalculation() -> None:
    preview = _preview()
    first = preview["records"][0]
    table = format_preview_appendix_table(preview)
    for field in (
        "candidate_cell_mgrs",
        "overall_score",
        "shielding_stability_score",
        "source_zone",
        "source_sensitive",
        "source_zone_reason",
        "candidate_reason",
    ):
        assert str(first[field]) in table
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {name} |" not in table


def test_text_cells_normalize_lines_and_escape_pipes() -> None:
    preview = _preview()
    preview["records"][0]["candidate_reason"] = "line one\nline | two"
    table = format_preview_appendix_table(preview)
    assert "line one line \\| two" in table
    assert "line one\nline" not in table


@pytest.mark.parametrize(
    ("scope", "field", "value"),
    (
        ("top", "external_coordinate_format", "WGS84"),
        ("record", "external_coordinate_format", "WGS84"),
        ("top", "user_coordinate_field", "x_m"),
        ("record", "user_coordinate_field", "x_m"),
    ),
)
def test_mgrs_contract_is_required(scope: str, field: str, value: object) -> None:
    preview = _preview()
    target = preview if scope == "top" else preview["records"][0]
    target[field] = value
    with pytest.raises(PreviewAppendixTableError):
        format_preview_appendix_table(preview)


@pytest.mark.parametrize("scope", ("top", "record"))
def test_internal_coordinate_keys_are_rejected(scope: str) -> None:
    preview = _preview()
    target = preview if scope == "top" else preview["records"][0]
    target["x_m"] = 123.0
    with pytest.raises(PreviewAppendixTableError, match="internal coordinate"):
        format_preview_appendix_table(preview)


def test_missing_fields_empty_records_and_count_mismatch_are_rejected() -> None:
    preview = _preview()
    del preview["title"]
    with pytest.raises(PreviewAppendixTableError, match="missing required"):
        format_preview_appendix_table(preview)

    preview = _preview()
    del preview["records"][0]["candidate_id"]
    with pytest.raises(PreviewAppendixTableError, match="missing required"):
        format_preview_appendix_table(preview)

    preview = _preview()
    preview["records"] = []
    preview["record_count"] = 0
    with pytest.raises(PreviewAppendixTableError, match="must not be empty"):
        format_preview_appendix_table(preview)

    preview = _preview()
    preview["record_count"] = 99
    with pytest.raises(PreviewAppendixTableError, match=r"len\(records\)"):
        format_preview_appendix_table(preview)


def test_record_value_types_are_validated() -> None:
    preview = _preview()
    preview["records"][0]["candidate_cell_mgrs"] = ""
    with pytest.raises(PreviewAppendixTableError, match="non-empty"):
        format_preview_appendix_table(preview)

    preview = _preview()
    preview["records"][0]["source_sensitive"] = "false"
    with pytest.raises(PreviewAppendixTableError, match="bool"):
        format_preview_appendix_table(preview)

    preview = _preview()
    preview["records"][0]["overall_score"] = "93.6"
    with pytest.raises(PreviewAppendixTableError, match="numeric"):
        format_preview_appendix_table(preview)


def test_max_rows_limits_display_and_reports_omissions() -> None:
    preview = _preview()
    full = format_preview_appendix_table(preview, max_rows=None)
    limited = format_preview_appendix_table(preview, max_rows=3)
    assert "| 5 |" in full
    assert "| 1 | candidate-green |" in limited
    assert "| 3 | candidate-orange |" in limited
    assert "| 4 |" not in limited
    assert limited.endswith("... 2 additional row(s) omitted.")


@pytest.mark.parametrize("value", (0, -1, True, 1.5, "3"))
def test_invalid_max_rows_is_rejected(value: object) -> None:
    with pytest.raises(PreviewAppendixTableError):
        format_preview_appendix_table(_preview(), max_rows=value)  # type: ignore[arg-type]


def test_formatter_does_not_mutate_input_or_create_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    preview = _preview()
    original = deepcopy(preview)
    assert isinstance(format_preview_appendix_table(preview, max_rows=2), str)
    assert preview == original
    assert list(tmp_path.iterdir()) == []


def test_default_table_exact_output_ignores_malformed_diagnostic_extras() -> None:
    preview = _preview()
    expected = format_preview_appendix_table(preview)
    preview["records"][0]["average_fresnel_score"] = float("nan")
    assert format_preview_appendix_table(preview) == expected


def test_diagnostic_table_has_exact_columns_and_legacy_state() -> None:
    preview = _preview()
    table = format_fresnel_diagnostics_appendix_table(preview)
    assert DIAGNOSTIC_COLUMNS[4:] == DIAGNOSTIC_FIELD_ORDER
    assert table.splitlines()[0] == "| " + " | ".join(DIAGNOSTIC_COLUMNS) + " |"
    first = table.splitlines()[2]
    assert first == (
        "| 1 | candidate-green | 52S CG 00000 00000 | unavailable | "
        + " | ".join(["unavailable"] * len(DIAGNOSTIC_FIELD_ORDER))
        + " |"
    )
    assert "dominant_obstacle_sample_index" not in table


def test_diagnostic_table_formats_eligible_values_with_required_precision() -> None:
    preview = _preview()
    preview["records"][0].update(DIAGNOSTIC_VALUES)
    table = format_fresnel_diagnostics_appendix_table(preview)
    row = table.splitlines()[2]
    assert "| eligible | 95.1 | 32.1 | 123.5 | 87.7 | 90.1 | 2.5 | 0.321 | 7.7 | -0.454 | 1.2 |" in row


def test_diagnostic_table_formats_no_eligible_state() -> None:
    preview = _preview()
    preview["records"][0].update(
        {name: None for name in DIAGNOSTIC_VALUES}
    )
    preview["records"][0]["average_fresnel_score"] = 100.0
    table = format_fresnel_diagnostics_appendix_table(preview)
    row = table.splitlines()[2]
    assert "| no-eligible-obstacle | 100.0 | " in row
    assert row.count("not-applicable") == len(DIAGNOSTIC_FIELD_ORDER) - 1


@pytest.mark.parametrize(
    "mutation",
    (
        {"average_fresnel_score": 10.0},
        {**DIAGNOSTIC_VALUES, "dominant_obstacle_nu": None},
        {**DIAGNOSTIC_VALUES, "dominant_obstacle_nu": True},
        {**DIAGNOSTIC_VALUES, "dominant_obstacle_nu": float("nan")},
        {**DIAGNOSTIC_VALUES, "dominant_obstacle_nu": float("inf")},
        {**DIAGNOSTIC_VALUES, "dominant_obstacle_nu": float("-inf")},
    ),
)
def test_diagnostic_table_rejects_invalid_states(mutation: dict[str, object]) -> None:
    preview = _preview()
    preview["records"][0].update(mutation)
    with pytest.raises(PreviewAppendixTableError, match="diagnostic"):
        format_fresnel_diagnostics_appendix_table(preview)


def test_diagnostic_table_preserves_order_limit_escaping_and_immutability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    preview = _preview()
    preview["records"][0]["candidate_id"] = "candidate|green"
    preview["records"][0]["dominant_obstacle_sample_index"] = 7
    original = deepcopy(preview)
    table = format_fresnel_diagnostics_appendix_table(preview, max_rows=2)
    assert "candidate\\|green" in table
    assert "| 2 | candidate-yellow |" in table
    assert "| 3 |" not in table
    assert table.endswith("... 3 additional row(s) omitted.")
    assert "dominant_obstacle_sample_index" not in table
    assert "| 7 |" not in table
    assert preview == original
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("value", (0, -1, True, 1.5, "2"))
def test_diagnostic_table_reuses_max_rows_validation(value: object) -> None:
    with pytest.raises(PreviewAppendixTableError):
        format_fresnel_diagnostics_appendix_table(
            _preview(), max_rows=value  # type: ignore[arg-type]
        )


def test_diagnostic_table_rejects_internal_coordinate() -> None:
    preview = _preview()
    preview["records"][0]["raster_row"] = 3
    with pytest.raises(PreviewAppendixTableError, match="internal coordinate"):
        format_fresnel_diagnostics_appendix_table(preview)


def test_module_has_no_gis_cli_rendering_or_file_writing_dependency() -> None:
    source = Path(
        "src/uav_rf_terrain/preview_appendix_table.py"
    ).read_text(encoding="utf-8").lower()
    blocked = (
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "preview_" + "cli",
        "pathlib",
        "open(",
        "write_" + "text",
        "write_" + "bytes",
        "html",
    )
    assert all(term not in source for term in blocked)
