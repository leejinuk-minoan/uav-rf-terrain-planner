from __future__ import annotations

import json
from pathlib import Path

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES


def test_documented_synthetic_workflows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic",)) == 0
    plain = capsys.readouterr().out
    assert plain.startswith("Candidate display preview\n")

    assert preview_cli.run_preview_cli(("--synthetic", "--json")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, dict)
    assert payload["record_count"] == len(payload["records"]) == 5

    preview_json = tmp_path / "preview.json"
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--output-json", str(preview_json))
    ) == 0
    capsys.readouterr()
    assert json.loads(preview_json.read_text(encoding="utf-8")) == payload

    assert preview_cli.run_preview_cli(("--synthetic", "--table")) == 0
    table = capsys.readouterr().out
    _assert_table_contract(table)

    table_file = tmp_path / "synthetic-table.md"
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--output-table", str(table_file))
    ) == 0
    capsys.readouterr()
    assert table_file.read_text(encoding="utf-8") == table


def test_documented_saved_json_reuse_workflows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    preview_json = tmp_path / "preview.json"
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--output-json", str(preview_json))
    ) == 0
    capsys.readouterr()

    assert preview_cli.run_preview_cli(
        ("--input-json", str(preview_json), "--table")
    ) == 0
    saved_table = capsys.readouterr().out
    _assert_table_contract(saved_table)

    table_file = tmp_path / "saved-table.md"
    assert preview_cli.run_preview_cli(
        ("--input-json", str(preview_json), "--output-table", str(table_file))
    ) == 0
    capsys.readouterr()
    assert table_file.read_text(encoding="utf-8") == saved_table
    assert set(tmp_path.iterdir()) == {preview_json, table_file}


def test_documented_row_limit_and_overwrite_workflows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    preview_json = tmp_path / "preview.json"
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--output-json", str(preview_json))
    ) == 0
    capsys.readouterr()

    args = ("--input-json", str(preview_json), "--table", "--max-records", "3")
    assert preview_cli.run_preview_cli(args) == 0
    limited = capsys.readouterr().out
    assert sum(line.startswith("| ") for line in limited.splitlines()) == 5
    assert "| 3 | candidate-orange |" in limited
    assert limited.endswith("... 2 additional row(s) omitted.\n")

    table_file = tmp_path / "table.md"
    table_file.write_text("protected", encoding="utf-8")
    output_args = (
        "--input-json",
        str(preview_json),
        "--output-table",
        str(table_file),
    )
    assert preview_cli.run_preview_cli(output_args) == 3
    capsys.readouterr()
    assert table_file.read_text(encoding="utf-8") == "protected"
    assert preview_cli.run_preview_cli((*output_args, "--force")) == 0
    capsys.readouterr()
    replaced = table_file.read_text(encoding="utf-8")
    _assert_table_contract(replaced)
    assert replaced != "protected"
    assert set(tmp_path.iterdir()) == {preview_json, table_file}


def _assert_table_contract(table: str) -> None:
    assert table.startswith("| row_no | candidate_id | candidate_cell_mgrs |")
    assert "52S CG 00000 00000" in table
    assert "source_zone" in table
    assert "source_sensitive" in table
    assert "source_zone_reason" in table
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {name} |" not in table


def test_documented_report_workflows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--report")) == 0
    report = capsys.readouterr().out
    _assert_report_contract(report)

    synthetic_file = tmp_path / "synthetic-report.md"
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--output-report", str(synthetic_file))
    ) == 0
    assert capsys.readouterr().out == f"preview saved: {synthetic_file}\n"
    assert synthetic_file.read_text(encoding="utf-8") == report

    preview_json = tmp_path / "preview.json"
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--output-json", str(preview_json))
    ) == 0
    capsys.readouterr()
    assert preview_cli.run_preview_cli(
        ("--input-json", str(preview_json), "--report")
    ) == 0
    assert capsys.readouterr().out == report

    saved_file = tmp_path / "saved-report.md"
    assert preview_cli.run_preview_cli(
        ("--input-json", str(preview_json), "--output-report", str(saved_file))
    ) == 0
    capsys.readouterr()
    assert saved_file.read_text(encoding="utf-8") == report


def test_documented_report_error_and_overwrite_workflows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "report.md"
    output.write_text("protected", encoding="utf-8")
    args = ("--synthetic", "--output-report", str(output))
    assert preview_cli.run_preview_cli(args) == 3
    capsys.readouterr()
    assert output.read_text(encoding="utf-8") == "protected"
    assert preview_cli.run_preview_cli((*args, "--force")) == 0
    capsys.readouterr()
    replaced = output.read_text(encoding="utf-8")
    _assert_report_contract(replaced)

    assert preview_cli.run_preview_cli(
        ("--synthetic", "--report", "--max-records", "3")
    ) == 2
    capsys.readouterr()
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{invalid", encoding="utf-8")
    before = output.read_text(encoding="utf-8")
    invalid_args = (
        "--input-json",
        str(invalid),
        "--output-report",
        str(output),
        "--force",
    )
    assert preview_cli.run_preview_cli(invalid_args) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert output.read_text(encoding="utf-8") == before


def _assert_report_contract(report: str) -> None:
    assert report.startswith("# Preview Candidate Report\n")
    assert report.endswith("\n") and not report.endswith("\n\n")
    for heading in ("## Summary", "## Candidate Overview", "## Appendix Table", "## Limitations"):
        assert heading in report
    assert "external_coordinate_format = MGRS" in report
    assert "candidate_cell_mgrs" in report
    assert "source_zone" in report
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {name} |" not in report
