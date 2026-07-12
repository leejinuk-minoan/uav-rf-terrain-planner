from __future__ import annotations

import json
from pathlib import Path

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    SyntheticCandidatePreviewSmokeError,
)


def test_default_plain_text_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert preview_cli.run_preview_cli(("--synthetic",)) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Candidate display preview" in captured.out
    assert "MGRS" in captured.out
    assert "candidate_cell_mgrs" in captured.out
    _assert_no_internal_fields_in_text(captured.out)


def test_max_records_limits_rows_and_reports_omissions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--max-records", "3")) == 0
    output = capsys.readouterr().out
    assert sum(line.startswith("- candidate-") for line in output.splitlines()) == 3
    assert "additional record(s) omitted" in output


@pytest.mark.parametrize("value", ("0", "-1", "nope", "1.5", "3x"))
def test_invalid_limit_returns_nonzero_and_concise_stderr(
    capsys: pytest.CaptureFixture[str], value: str
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--max-records", value)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "positive integer" in captured.err
    assert "Traceback" not in captured.err


def test_json_stdout_is_valid_and_preserves_mgrs_policy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--json")) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["external_coordinate_format"] == "MGRS"
    assert payload["user_coordinate_field"] == "candidate_cell_mgrs"
    assert payload["records"]
    for record in payload["records"]:
        assert "candidate_cell_mgrs" in record
        assert set(record).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)
    assert set(payload).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)


def test_json_stdout_excludes_internal_coordinate_tokens(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--json")) == 0
    output = capsys.readouterr().out
    for field_name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f'"{field_name}"' not in output


def test_cli_creates_no_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    before = tuple(tmp_path.iterdir())
    assert preview_cli.run_preview_cli(("--synthetic", "--json")) == 0
    capsys.readouterr()
    assert tuple(tmp_path.iterdir()) == before


def test_expected_preview_error_returns_one_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(**_kwargs: object) -> None:
        raise SyntheticCandidatePreviewSmokeError("synthetic preview unavailable")

    monkeypatch.setattr(preview_cli, "build_synthetic_candidate_preview_smoke", fail)
    assert preview_cli.run_preview_cli(("--synthetic",)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "preview error: synthetic preview unavailable\n"
    assert "Traceback" not in captured.err


def test_missing_synthetic_flag_returns_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(()) == 2
    assert "--synthetic" in capsys.readouterr().err


def test_json_file_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "preview.json"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-json", str(output))) == 0
    captured = capsys.readouterr()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["external_coordinate_format"] == "MGRS"
    assert all("candidate_cell_mgrs" in record for record in payload["records"])
    assert all(set(record).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES) for record in payload["records"])
    assert "preview saved:" in captured.out
    assert "\"records\"" not in captured.out
    assert captured.err == ""


def test_text_file_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "preview.txt"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(output))) == 0
    text = output.read_text(encoding="utf-8")
    assert "Candidate display preview" in text
    assert "MGRS" in text
    assert "candidate_cell_mgrs" in text
    _assert_no_internal_fields_in_text(text)
    assert "preview saved:" in capsys.readouterr().out


def test_limited_text_file_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "preview.txt"
    args = ("--synthetic", "--max-records", "3", "--output-text", str(output))
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    text = output.read_text(encoding="utf-8")
    assert sum(line.startswith("- candidate-") for line in text.splitlines()) == 3
    assert "additional record(s) omitted" in text


def test_existing_file_requires_force_and_preserves_content(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "preview.txt"
    output.write_text("preserve", encoding="utf-8")
    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(output))) == 3
    captured = capsys.readouterr()
    assert output.read_text(encoding="utf-8") == "preserve"
    assert "already exists" in captured.err
    assert "Traceback" not in captured.err


def test_force_overwrites_existing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "preview.txt"
    output.write_text("old", encoding="utf-8")
    args = ("--synthetic", "--output-text", str(output), "--force")
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    assert "Candidate display preview" in output.read_text(encoding="utf-8")


def test_missing_parent_and_directory_path_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing" / "preview.json"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-json", str(missing))) == 3
    assert "parent directory" in capsys.readouterr().err
    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(tmp_path))) == 3
    assert "is a directory" in capsys.readouterr().err


@pytest.mark.parametrize(
    "args",
    (
        ("--synthetic", "--output-json", "a.json", "--output-text", "a.txt"),
        ("--synthetic", "--json", "--output-text", "a.txt"),
        ("--synthetic", "--json", "--output-json", "a.json"),
    ),
)
def test_conflicting_output_modes_return_parser_error(
    args: tuple[str, ...], capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot be used together" in captured.err
    assert "Traceback" not in captured.err


def test_cli_module_has_no_gis_or_directory_creation_behavior() -> None:
    source = Path("src/uav_rf_terrain/preview_cli.py").read_text(encoding="utf-8").lower()
    blocked = (
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "write_" + "bytes",
        "mkdir(",
    )
    for term in blocked:
        assert term not in source


def _assert_no_internal_fields_in_text(output: str) -> None:
    for field_name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"{field_name}=" not in output
        assert f'"{field_name}"' not in output
