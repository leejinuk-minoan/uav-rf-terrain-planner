from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.coordinate_io_policy import INTERNAL_COORDINATE_FIELD_NAMES
from uav_rf_terrain.fresnel_diagnostics import DIAGNOSTIC_FIELD_ORDER
from uav_rf_terrain.preview_appendix_table import (
    PreviewAppendixTableError,
    format_fresnel_diagnostics_appendix_table,
)
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    build_synthetic_candidate_preview_smoke,
)


_ELIGIBLE_VALUES = {
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


def _write_preview(path: Path, preview: dict[str, object]) -> None:
    path.write_text(json.dumps(preview), encoding="utf-8")


def _diagnostic_header() -> str:
    return "| " + " | ".join(
        (
            "row_no",
            "candidate_id",
            "candidate_cell_mgrs",
            "diagnostic_status",
            *DIAGNOSTIC_FIELD_ORDER,
        )
    ) + " |"


def test_synthetic_diagnostic_stdout_matches_existing_formatter_and_creates_no_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    expected = format_fresnel_diagnostics_appendix_table(_preview()) + "\n"

    assert preview_cli.run_preview_cli(("--synthetic", "--diagnostic-table")) == 0

    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""
    assert captured.out.splitlines()[0] == _diagnostic_header()
    assert "dominant_obstacle_sample_index" not in captured.out
    for field_name in INTERNAL_COORDINATE_FIELD_NAMES:
        assert f"| {field_name} |" not in captured.out
    assert list(tmp_path.iterdir()) == []


def test_synthetic_diagnostic_file_matches_stdout_with_limit_and_one_newline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stdout_args = ("--synthetic", "--max-records", "3", "--diagnostic-table")
    assert preview_cli.run_preview_cli(stdout_args) == 0
    stdout = capsys.readouterr().out

    output = tmp_path / "diagnostic.md"
    file_args = (
        "--synthetic",
        "--max-records",
        "3",
        "--output-diagnostic-table",
        str(output),
    )
    assert preview_cli.run_preview_cli(file_args) == 0
    captured = capsys.readouterr()
    assert output.read_text(encoding="utf-8") == stdout
    assert stdout.endswith("\n") and not stdout.endswith("\n\n")
    assert "| 3 | candidate-orange |" in stdout
    assert stdout.endswith("... 2 additional row(s) omitted.\n")
    assert captured.out == f"preview saved: {output}\n"
    assert captured.err == ""


@pytest.mark.parametrize("state", ("legacy", "eligible", "no_eligible"))
def test_saved_preview_diagnostic_stdout_and_file_match_direct_formatter(
    state: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    preview = _preview()
    record = preview["records"][0]
    assert isinstance(record, dict)
    if state == "eligible":
        record.update(_ELIGIBLE_VALUES)
    elif state == "no_eligible":
        record.update({field: None for field in DIAGNOSTIC_FIELD_ORDER})
        record["average_fresnel_score"] = 100.0
    source = tmp_path / f"{state}.json"
    _write_preview(source, preview)
    expected = format_fresnel_diagnostics_appendix_table(preview) + "\n"

    assert (
        preview_cli.run_preview_cli(("--input-json", str(source), "--diagnostic-table"))
        == 0
    )
    assert capsys.readouterr().out == expected

    output = tmp_path / f"{state}.md"
    assert (
        preview_cli.run_preview_cli(
            ("--input-json", str(source), "--output-diagnostic-table", str(output))
        )
        == 0
    )
    captured = capsys.readouterr()
    assert output.read_text(encoding="utf-8") == expected
    assert captured.out == f"preview saved: {output}\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    "mutation",
    (
        {"average_fresnel_score": 10.0},
        {**_ELIGIBLE_VALUES, "dominant_obstacle_nu": None},
        {**_ELIGIBLE_VALUES, "dominant_obstacle_nu": True},
        {**_ELIGIBLE_VALUES, "dominant_obstacle_nu": float("nan")},
        {**_ELIGIBLE_VALUES, "dominant_obstacle_nu": float("inf")},
        {**_ELIGIBLE_VALUES, "dominant_obstacle_nu": float("-inf")},
    ),
)
def test_invalid_saved_diagnostics_return_one_without_an_artifact(
    mutation: dict[str, object], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    preview = _preview()
    record = preview["records"][0]
    assert isinstance(record, dict)
    record.update(mutation)
    source = tmp_path / "invalid.json"
    _write_preview(source, preview)
    output = tmp_path / "diagnostic.md"

    assert (
        preview_cli.run_preview_cli(
            ("--input-json", str(source), "--output-diagnostic-table", str(output))
        )
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("preview diagnostic table error: ")
    assert "Traceback" not in captured.err
    assert not output.exists()


def test_diagnostic_formatter_failure_preserves_forced_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(*_args: object, **_kwargs: object) -> str:
        raise PreviewAppendixTableError("invalid diagnostic preview")

    monkeypatch.setattr(preview_cli, "format_fresnel_diagnostics_appendix_table", fail)
    output = tmp_path / "diagnostic.md"
    output.write_text("preserve", encoding="utf-8")

    assert (
        preview_cli.run_preview_cli(
            ("--synthetic", "--output-diagnostic-table", str(output), "--force")
        )
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "preview diagnostic table error: invalid diagnostic preview\n"
    assert output.read_text(encoding="utf-8") == "preserve"


def test_diagnostic_file_policy_requires_existing_parent_and_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing" / "diagnostic.md"
    assert (
        preview_cli.run_preview_cli(
            ("--synthetic", "--output-diagnostic-table", str(missing))
        )
        == 3
    )
    assert "parent directory" in capsys.readouterr().err
    assert not missing.parent.exists()

    assert (
        preview_cli.run_preview_cli(
            ("--synthetic", "--output-diagnostic-table", str(tmp_path))
        )
        == 3
    )
    assert "is a directory" in capsys.readouterr().err

    output = tmp_path / "diagnostic.md"
    output.write_text("preserve", encoding="utf-8")
    args = ("--synthetic", "--output-diagnostic-table", str(output))
    assert preview_cli.run_preview_cli(args) == 3
    assert output.read_text(encoding="utf-8") == "preserve"
    assert "already exists" in capsys.readouterr().err

    assert preview_cli.run_preview_cli((*args, "--force")) == 0
    capsys.readouterr()
    assert output.read_text(encoding="utf-8").startswith("| row_no |")


def test_diagnostic_selectors_conflict_with_all_existing_output_selectors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    diagnostic_selectors = (
        ("--diagnostic-table",),
        ("--output-diagnostic-table", str(tmp_path / "diagnostic.md")),
    )
    existing_selectors = (
        ("--json",),
        ("--table",),
        ("--report",),
        ("--output-json", str(tmp_path / "preview.json")),
        ("--output-text", str(tmp_path / "preview.txt")),
        ("--output-table", str(tmp_path / "preview-table.md")),
        ("--output-report", str(tmp_path / "report.md")),
    )
    for diagnostic in diagnostic_selectors:
        for existing in existing_selectors:
            assert preview_cli.run_preview_cli(("--synthetic", *diagnostic, *existing)) == 2
            captured = capsys.readouterr()
            assert captured.out == ""
            assert "output selectors cannot be used together" in captured.err
            assert "Traceback" not in captured.err
    assert (
        preview_cli.run_preview_cli(
            (
                "--synthetic",
                "--diagnostic-table",
                "--output-diagnostic-table",
                str(tmp_path / "diagnostic.md"),
            )
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "output selectors cannot be used together" in captured.err
    assert list(tmp_path.iterdir()) == []


def test_saved_preview_allows_only_table_report_or_diagnostic_outputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "preview.json"
    _write_preview(source, _preview())
    base = ("--input-json", str(source))

    assert preview_cli.run_preview_cli(base) == 2
    assert "requires table, report, or diagnostic table output" in capsys.readouterr().err
    for selector in ("--json", "--output-json", "--output-text"):
        args = [*base, selector]
        if selector.startswith("--output-"):
            args.append(str(tmp_path / "disallowed.out"))
        assert preview_cli.run_preview_cli(tuple(args)) == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Traceback" not in captured.err


def test_diagnostic_output_does_not_relax_source_count_validation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert preview_cli.run_preview_cli(("--diagnostic-table",)) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "exactly one of --synthetic or --input-json is required" in captured.err
