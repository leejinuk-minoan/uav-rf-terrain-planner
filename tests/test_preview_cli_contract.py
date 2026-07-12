from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    SyntheticCandidatePreviewSmokeError,
)


TOP_LEVEL_FIELDS = {
    "title",
    "external_coordinate_format",
    "user_coordinate_field",
    "record_count",
    "source_sensitive_count",
    "records",
    "summary",
    "reason",
}
RECORD_FIELDS = {
    "candidate_id",
    "candidate_cell_mgrs",
    "external_coordinate_format",
    "user_coordinate_field",
    "color_class",
    "color_name",
    "overall_score",
    "shielding_stability_score",
    "source_zone",
    "source_sensitive",
    "source_zone_reason",
    "candidate_reason",
    "display_label",
}


def _json_stdout(
    capsys: pytest.CaptureFixture[str], *extra_args: str
) -> dict[str, Any]:
    args = ("--synthetic", *extra_args, "--json")
    assert preview_cli.run_preview_cli(args) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)


def _assert_no_internal_coordinate_tokens(text: str) -> None:
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f'"{name}"' not in text
        assert f"{name}=" not in text


def test_json_stdout_exact_top_level_and_record_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _json_stdout(capsys)
    assert set(payload) == TOP_LEVEL_FIELDS
    assert payload["external_coordinate_format"] == "MGRS"
    assert payload["user_coordinate_field"] == "candidate_cell_mgrs"
    assert payload["record_count"] == len(payload["records"])
    assert all(isinstance(value, (str, int, list, dict)) for value in payload.values())

    for record in payload["records"]:
        assert set(record) == RECORD_FIELDS
        assert record["candidate_cell_mgrs"].strip()
        assert record["external_coordinate_format"] == "MGRS"
        assert record["user_coordinate_field"] == "candidate_cell_mgrs"
        assert {"source_zone", "source_sensitive", "source_zone_reason"} <= set(record)
        assert all(isinstance(value, (str, int, float, bool)) for value in record.values())
        assert set(record).isdisjoint(INTERNAL_COORDINATE_FIELD_NAMES)


def test_json_stdout_and_file_are_semantically_equal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stdout_payload = _json_stdout(capsys)
    output = tmp_path / "preview.json"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-json", str(output))) == 0
    confirmation = capsys.readouterr()
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert file_payload == stdout_payload
    assert confirmation.err == ""
    assert confirmation.out.startswith("preview saved:")
    assert not confirmation.out.lstrip().startswith("{")
    assert output.read_bytes().endswith(b"\n")


def test_max_records_never_truncates_json_modes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    full = _json_stdout(capsys)
    limited_stdout = _json_stdout(capsys, "--max-records", "3")
    output = tmp_path / "preview.json"
    args = ("--synthetic", "--max-records", "3", "--output-json", str(output))
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    limited_file = json.loads(output.read_text(encoding="utf-8"))
    assert limited_stdout == full
    assert limited_file == full
    assert len(full["records"]) == full["record_count"]


def test_json_contains_no_python_repr_or_internal_coordinates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--json")) == 0
    text = capsys.readouterr().out
    assert "<class '" not in text
    assert "Enum." not in text
    assert "dataclass(" not in text
    _assert_no_internal_coordinate_tokens(text)


def test_plain_text_stdout_contract(capsys: pytest.CaptureFixture[str]) -> None:
    assert preview_cli.run_preview_cli(("--synthetic",)) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert captured.err == ""
    assert lines[0] == "Candidate display preview"
    assert "External coordinate format: MGRS" in lines
    assert "User coordinate field: candidate_cell_mgrs" in lines
    assert any(line.startswith("Records: ") for line in lines)
    assert any(line.startswith("Source-sensitive records: ") for line in lines)
    rows = [line for line in lines if line.startswith("- candidate-")]
    assert rows
    for row in rows:
        assert " | 52S " in row
        assert " | score=" in row
        assert " | source_zone=" in row
        assert "source_sensitive" not in row
        assert "source_zone_reason" not in row
    _assert_no_internal_coordinate_tokens(captured.out)


def test_plain_text_stdout_and_file_share_formatter_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic",)) == 0
    stdout_text = capsys.readouterr().out
    output = tmp_path / "preview.txt"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(output))) == 0
    capsys.readouterr()
    file_text = output.read_text(encoding="utf-8")
    assert file_text == stdout_text
    assert file_text.endswith("\n") and not file_text.endswith("\n\n")
    _assert_no_internal_coordinate_tokens(file_text)


def test_limited_plain_text_stdout_and_file_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ("--synthetic", "--max-records", "3")
    assert preview_cli.run_preview_cli(args) == 0
    stdout_text = capsys.readouterr().out
    output = tmp_path / "preview.txt"
    file_args = (*args, "--output-text", str(output))
    assert preview_cli.run_preview_cli(file_args) == 0
    capsys.readouterr()
    file_text = output.read_text(encoding="utf-8")
    assert file_text == stdout_text
    assert sum(line.startswith("- candidate-") for line in file_text.splitlines()) == 3
    assert "... 2 additional record(s) omitted." in file_text


def test_status_codes_and_concise_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic",)) == 0
    capsys.readouterr()

    def fail(**_kwargs: object) -> None:
        raise SyntheticCandidatePreviewSmokeError("unavailable")

    monkeypatch.setattr(preview_cli, "build_synthetic_candidate_preview_smoke", fail)
    assert preview_cli.run_preview_cli(("--synthetic",)) == 1
    error_one = capsys.readouterr().err
    assert error_one == "preview error: unavailable\n"
    assert "Traceback" not in error_one
    monkeypatch.undo()

    assert preview_cli.run_preview_cli(()) == 2
    error_two = capsys.readouterr().err
    assert "--synthetic" in error_two
    assert "Traceback" not in error_two

    missing = tmp_path / "missing" / "preview.json"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-json", str(missing))) == 3
    error_three = capsys.readouterr().err
    assert "parent directory" in error_three
    assert "Traceback" not in error_three


def test_explicit_path_and_overwrite_policy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "selected.txt"
    before = set(tmp_path.iterdir())
    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(target))) == 0
    capsys.readouterr()
    assert set(tmp_path.iterdir()) - before == {target}
    original = target.read_text(encoding="utf-8")

    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(target))) == 3
    protected = capsys.readouterr()
    assert target.read_text(encoding="utf-8") == original
    assert "already exists" in protected.err
    assert "Traceback" not in protected.err

    target.write_text("replace me", encoding="utf-8")
    args = ("--synthetic", "--output-text", str(target), "--force")
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    assert target.read_text(encoding="utf-8") == original


def test_missing_parent_directory_target_and_mode_conflicts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "not-created" / "preview.txt"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-text", str(missing))) == 3
    assert not missing.parent.exists()
    assert "Traceback" not in capsys.readouterr().err

    assert preview_cli.run_preview_cli(("--synthetic", "--output-json", str(tmp_path))) == 3
    assert "is a directory" in capsys.readouterr().err

    conflicts = (
        ("--synthetic", "--output-json", "a.json", "--output-text", "a.txt"),
        ("--synthetic", "--json", "--output-json", "a.json"),
        ("--synthetic", "--json", "--output-text", "a.txt"),
    )
    for args in conflicts:
        assert preview_cli.run_preview_cli(args) == 2
        captured = capsys.readouterr()
        assert "cannot be used together" in captured.err
        assert "Traceback" not in captured.err


@pytest.mark.parametrize("args", (("--synthetic",), ("--synthetic", "--json")))
def test_stdout_modes_create_no_files(
    args: tuple[str, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    assert list(tmp_path.iterdir()) == []
