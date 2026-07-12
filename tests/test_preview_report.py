from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.preview_appendix_table import format_preview_appendix_table
from uav_rf_terrain.preview_report import PreviewReportError, format_preview_report
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    build_synthetic_candidate_preview_smoke,
)


def _preview() -> dict[str, object]:
    return deepcopy(build_synthetic_candidate_preview_smoke().preview_dict)


def test_report_sections_summary_and_context_are_deterministic() -> None:
    report = format_preview_report(_preview())
    assert isinstance(report, str)
    headings = (
        "# Preview Candidate Report",
        "## Summary",
        "## Source and Output Context",
        "## Candidate Overview",
        "## Source-Zone Interpretation",
        "## Coordinate Boundary",
        "## Appendix Table",
        "## Limitations",
    )
    positions = [report.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "Record count: 5" in report
    assert "Source-sensitive count: 3" in report
    assert "External coordinate format: MGRS" in report
    assert "User coordinate field: candidate_cell_mgrs" in report
    assert "Input provenance: not encoded in preview" in report
    assert report.endswith("\n") and not report.endswith("\n\n")


def test_candidate_and_source_zone_summaries_use_existing_values() -> None:
    report = format_preview_report(_preview())
    assert "Color class counts: green=1, yellow=1, orange=1, red=1, excluded=1" in report
    assert "Overall score range: 16.0 to 93.60000000000001" in report
    assert "Shielding stability score range: 0.0 to 97.0" in report
    assert "Source-zone counts: esa_derived=2, wms_gap_filled=1, dem_only_fallback=1, mixed_boundary=1" in report
    assert "interpretation metadata only" in report


def test_table_inclusion_is_exact_and_optional() -> None:
    preview = _preview()
    table = format_preview_appendix_table(preview)
    report = format_preview_report(preview)
    assert f"## Appendix Table\n{table}\n\n## Limitations" in report
    without = format_preview_report(preview, include_table=False)
    assert "## Appendix Table" not in without
    assert "| row_no |" not in without
    assert without.index("## Coordinate Boundary") < without.index("## Limitations")


def test_coordinate_boundary_and_input_immutability() -> None:
    preview = _preview()
    original = deepcopy(preview)
    report = format_preview_report(preview)
    assert "external_coordinate_format = MGRS" in report
    assert "user_coordinate_field = candidate_cell_mgrs" in report
    assert "52S CG 00000 00000" in report
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {name} |" not in report
    assert preview == original


@pytest.mark.parametrize("scope", ("top", "record"))
def test_invalid_preview_is_wrapped_and_chained(scope: str) -> None:
    preview = _preview()
    target = preview if scope == "top" else preview["records"][0]
    target["x_m"] = 1.0
    with pytest.raises(PreviewReportError) as caught:
        format_preview_report(preview, include_table=False)
    assert caught.value.__cause__ is not None


def test_formatter_creates_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert format_preview_report(_preview())
    assert list(tmp_path.iterdir()) == []


def test_module_has_no_cli_gis_rendering_path_or_file_dependency() -> None:
    source = Path("src/uav_rf_terrain/preview_report.py").read_text(encoding="utf-8").lower()
    blocked = (
        "argparse",
        "pathlib",
        "preview_" + "cli",
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "open(",
        "write_" + "text",
        "html",
    )
    assert all(term not in source for term in blocked)
