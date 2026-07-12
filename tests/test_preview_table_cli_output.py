from __future__ import annotations

import json
from pathlib import Path

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.preview_appendix_table import PreviewAppendixTableError


EXPECTED_COLUMNS = (
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


def _table_stdout(capsys: pytest.CaptureFixture[str], *extra: str) -> str:
    assert preview_cli.run_preview_cli(("--synthetic", "--table", *extra)) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    return captured.out


def _assert_table_contract(table: str) -> None:
    assert all(column in table.splitlines()[0] for column in EXPECTED_COLUMNS)
    assert table.index("candidate-green") < table.index("candidate-yellow")
    assert "| 1 | candidate-green | 52S CG 00000 00000 |" in table
    assert "source_zone" in table
    assert "source_sensitive" in table
    assert "source_zone_reason" in table
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {name} |" not in table


def test_table_stdout_contract_and_no_file_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    table = _table_stdout(capsys)
    _assert_table_contract(table)
    assert list(tmp_path.iterdir()) == []


def test_limited_table_stdout_uses_formatter_omission(
    capsys: pytest.CaptureFixture[str],
) -> None:
    table = _table_stdout(capsys, "--max-records", "3")
    assert sum(line.startswith("| ") for line in table.splitlines()) == 5
    assert "| 1 | candidate-green |" in table
    assert "| 3 | candidate-orange |" in table
    assert "| 4 |" not in table
    assert table.endswith("... 2 additional row(s) omitted.\n")


def test_table_file_matches_stdout_and_has_one_trailing_newline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stdout_table = _table_stdout(capsys)
    output = tmp_path / "preview-table.md"
    args = ("--synthetic", "--output-table", str(output))
    assert preview_cli.run_preview_cli(args) == 0
    captured = capsys.readouterr()
    file_table = output.read_text(encoding="utf-8")
    assert file_table == stdout_table
    assert file_table.endswith("\n") and not file_table.endswith("\n\n")
    assert captured.out == f"preview saved: {output}\n"
    assert "| row_no |" not in captured.out
    assert captured.err == ""
    _assert_table_contract(file_table)


def test_limited_table_file_and_overwrite_policy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "preview-table.md"
    args = ("--synthetic", "--max-records", "3", "--output-table", str(output))
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    limited = output.read_text(encoding="utf-8")
    assert "| 3 | candidate-orange |" in limited
    assert limited.endswith("... 2 additional row(s) omitted.\n")

    assert preview_cli.run_preview_cli(args) == 3
    captured = capsys.readouterr()
    assert output.read_text(encoding="utf-8") == limited
    assert "already exists" in captured.err
    assert "Traceback" not in captured.err

    output.write_text("replace", encoding="utf-8")
    assert preview_cli.run_preview_cli((*args, "--force")) == 0
    capsys.readouterr()
    assert output.read_text(encoding="utf-8") == limited


def test_table_file_path_errors_are_status_three(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing" / "table.md"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-table", str(missing))) == 3
    assert not missing.parent.exists()
    assert "Traceback" not in capsys.readouterr().err

    assert preview_cli.run_preview_cli(("--synthetic", "--output-table", str(tmp_path))) == 3
    captured = capsys.readouterr()
    assert "is a directory" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    "selectors",
    (
        ("--json", "--table"),
        ("--json", "--output-json", "a.json"),
        ("--json", "--output-text", "a.txt"),
        ("--json", "--output-table", "a.md"),
        ("--table", "--output-json", "a.json"),
        ("--table", "--output-text", "a.txt"),
        ("--table", "--output-table", "a.md"),
        ("--output-json", "a.json", "--output-text", "a.txt"),
        ("--output-json", "a.json", "--output-table", "a.md"),
        ("--output-text", "a.txt", "--output-table", "a.md"),
    ),
)
def test_all_output_selector_conflicts_return_two(
    selectors: tuple[str, ...], capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", *selectors)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "output selectors cannot be used together" in captured.err
    assert "Traceback" not in captured.err


def test_formatter_error_returns_one_without_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_args: object, **_kwargs: object) -> str:
        raise PreviewAppendixTableError("invalid preview")

    monkeypatch.setattr(preview_cli, "format_preview_appendix_table", fail)
    assert preview_cli.run_preview_cli(("--synthetic", "--table")) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "preview table error: invalid preview\n"
    assert "Traceback" not in captured.err


def test_existing_modes_remain_compatible(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic",)) == 0
    plain = capsys.readouterr().out
    assert plain.startswith("Candidate display preview\n")

    assert preview_cli.run_preview_cli(("--synthetic", "--max-records", "3", "--json")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["records"]) == payload["record_count"] == 5

    json_file = tmp_path / "preview.json"
    args = ("--synthetic", "--max-records", "3", "--output-json", str(json_file))
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    assert len(json.loads(json_file.read_text(encoding="utf-8"))["records"]) == 5

    text_file = tmp_path / "preview.txt"
    args = ("--synthetic", "--max-records", "3", "--output-text", str(text_file))
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    text = text_file.read_text(encoding="utf-8")
    assert sum(line.startswith("- candidate-") for line in text.splitlines()) == 3
