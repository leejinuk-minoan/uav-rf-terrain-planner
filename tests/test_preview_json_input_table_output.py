from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    build_synthetic_candidate_preview_smoke,
)


def _payload() -> dict[str, object]:
    return deepcopy(build_synthetic_candidate_preview_smoke().preview_dict)


def _write_input(path: Path, payload: object | None = None) -> dict[str, object]:
    resolved = _payload() if payload is None else payload
    path.write_text(json.dumps(resolved, ensure_ascii=False), encoding="utf-8")
    return resolved if isinstance(resolved, dict) else {}


def test_saved_input_table_stdout_and_file_are_equivalent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "preview.json"
    original = _write_input(source)
    source_before = source.read_bytes()
    assert preview_cli.run_preview_cli(("--input-json", str(source), "--table")) == 0
    stdout_table = capsys.readouterr().out
    output = tmp_path / "table.md"
    args = ("--input-json", str(source), "--output-table", str(output))
    assert preview_cli.run_preview_cli(args) == 0
    captured = capsys.readouterr()
    assert output.read_text(encoding="utf-8") == stdout_table
    assert captured.out == f"preview saved: {output}\n"
    assert source.read_bytes() == source_before
    assert original == _payload()
    assert "| 1 | candidate-green | 52S CG 00000 00000 |" in stdout_table
    assert stdout_table.index("candidate-green") < stdout_table.index("candidate-yellow")
    assert "source_zone" in stdout_table
    for name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {name} |" not in stdout_table


def test_saved_input_limit_and_force_policy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "preview.json"
    _write_input(source)
    output = tmp_path / "table.md"
    args = (
        "--input-json",
        str(source),
        "--max-records",
        "3",
        "--output-table",
        str(output),
    )
    assert preview_cli.run_preview_cli(args) == 0
    capsys.readouterr()
    limited = output.read_text(encoding="utf-8")
    assert "| 3 | candidate-orange |" in limited
    assert limited.endswith("... 2 additional row(s) omitted.\n")
    assert preview_cli.run_preview_cli(args) == 3
    assert "already exists" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == limited
    output.write_text("replace", encoding="utf-8")
    assert preview_cli.run_preview_cli((*args, "--force")) == 0
    capsys.readouterr()
    assert output.read_text(encoding="utf-8") == limited


@pytest.mark.parametrize(
    "args",
    (
        (),
        ("--table",),
        ("--synthetic", "--input-json", "input.json", "--table"),
        ("--input-json", "input.json"),
        ("--input-json", "input.json", "--json"),
        ("--input-json", "input.json", "--output-json", "copy.json"),
        ("--input-json", "input.json", "--output-text", "preview.txt"),
    ),
)
def test_source_and_saved_output_argument_errors_return_two(
    args: tuple[str, ...], capsys: pytest.CaptureFixture[str]
) -> None:
    assert preview_cli.run_preview_cli(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Traceback" not in captured.err


def test_saved_input_does_not_call_synthetic_helper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "preview.json"
    _write_input(source)

    def fail(**_kwargs: object) -> None:
        raise AssertionError("synthetic helper called")

    monkeypatch.setattr(preview_cli, "build_synthetic_candidate_preview_smoke", fail)
    assert preview_cli.run_preview_cli(("--input-json", str(source), "--table")) == 0
    assert "candidate-green" in capsys.readouterr().out


@pytest.mark.parametrize(
    "content",
    (
        b"\xff\xfe",
        b"{invalid",
        b"[]",
        b"42",
        b'"text"',
        b"true",
        b"null",
    ),
)
def test_decode_and_non_object_inputs_return_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: bytes
) -> None:
    source = tmp_path / "preview.json"
    source.write_bytes(content)
    assert preview_cli.run_preview_cli(("--input-json", str(source), "--table")) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "preview input error:" in captured.err
    assert "Traceback" not in captured.err


def test_missing_and_directory_inputs_return_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.json"
    assert preview_cli.run_preview_cli(("--input-json", str(missing), "--table")) == 1
    assert "must exist and be a file" in capsys.readouterr().err
    assert preview_cli.run_preview_cli(("--input-json", str(tmp_path), "--table")) == 1
    assert "must exist and be a file" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("scope", "field", "value"),
    (
        ("top", "title", None),
        ("record", "candidate_id", None),
        ("top", "record_count", 99),
        ("record", "overall_score", "bad"),
        ("record", "source_sensitive", "bad"),
        ("top", "external_coordinate_format", "WGS84"),
        ("record", "external_coordinate_format", "WGS84"),
        ("top", "x_m", 1.0),
        ("record", "x_m", 1.0),
    ),
)
def test_schema_failures_return_one_without_partial_or_replacement(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    scope: str,
    field: str,
    value: object,
) -> None:
    payload = _payload()
    target = payload if scope == "top" else payload["records"][0]
    if value is None:
        del target[field]
    else:
        target[field] = value
    source = tmp_path / "preview.json"
    _write_input(source, payload)
    output = tmp_path / "table.md"
    output.write_text("preserve", encoding="utf-8")
    args = (
        "--input-json",
        str(source),
        "--output-table",
        str(output),
        "--force",
    )
    assert preview_cli.run_preview_cli(args) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "preview table error:" in captured.err
    assert "Traceback" not in captured.err
    assert output.read_text(encoding="utf-8") == "preserve"


def test_output_path_errors_remain_three(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "preview.json"
    _write_input(source)
    missing = tmp_path / "missing" / "table.md"
    args = ("--input-json", str(source), "--output-table", str(missing))
    assert preview_cli.run_preview_cli(args) == 3
    assert not missing.parent.exists()
    assert "Traceback" not in capsys.readouterr().err
    assert preview_cli.run_preview_cli(
        ("--input-json", str(source), "--output-table", str(tmp_path))
    ) == 3
    assert "is a directory" in capsys.readouterr().err


def test_existing_synthetic_table_and_json_modes_remain_valid(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--table")) == 0
    assert "| row_no |" in capsys.readouterr().out
    assert preview_cli.run_preview_cli(
        ("--synthetic", "--max-records", "3", "--json")
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["records"]) == payload["record_count"] == 5
