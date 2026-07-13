from __future__ import annotations

import json
from pathlib import Path

import pytest

from uav_rf_terrain import preview_cli
from uav_rf_terrain.preview_report import PreviewReportError
from uav_rf_terrain.synthetic_candidate_preview_smoke import build_synthetic_candidate_preview_smoke


def test_synthetic_report_stdout_and_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert preview_cli.run_preview_cli(("--synthetic", "--report")) == 0
    report = capsys.readouterr().out
    assert report.startswith("# Preview Candidate Report\n")
    assert "## Appendix Table" in report
    assert report.endswith("\n") and not report.endswith("\n\n")
    output = tmp_path / "report.md"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-report", str(output))) == 0
    captured = capsys.readouterr()
    assert output.read_text(encoding="utf-8") == report
    assert captured.out == f"preview saved: {output}\n"


def test_saved_report_stdout_and_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "preview.json"
    source.write_text(json.dumps(build_synthetic_candidate_preview_smoke().preview_dict), encoding="utf-8")
    assert preview_cli.run_preview_cli(("--input-json", str(source), "--report")) == 0
    report = capsys.readouterr().out
    assert "external_coordinate_format = MGRS" in report
    assert "52S CG 00000 00000" in report
    output = tmp_path / "report.md"
    assert preview_cli.run_preview_cli(("--input-json", str(source), "--output-report", str(output))) == 0
    capsys.readouterr()
    assert output.read_text(encoding="utf-8") == report


@pytest.mark.parametrize("selector", ("--json", "--table", "--output-json", "--output-text", "--output-table"))
@pytest.mark.parametrize("report", ("--report", "--output-report"))
def test_report_output_conflicts(selector: str, report: str, capsys: pytest.CaptureFixture[str]) -> None:
    args = ["--synthetic", report]
    if report == "--output-report":
        args.append("r.md")
    args.append(selector)
    if selector.startswith("--output-"):
        args.append("x.out")
    assert preview_cli.run_preview_cli(tuple(args)) == 2
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("report", ("--report", "--output-report"))
def test_report_rejects_max_records(report: str, capsys: pytest.CaptureFixture[str]) -> None:
    args = ["--synthetic", report]
    if report == "--output-report":
        args.append("r.md")
    args.extend(("--max-records", "3"))
    assert preview_cli.run_preview_cli(tuple(args)) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_report_error_and_file_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def fail(*_args: object, **_kwargs: object) -> str:
        raise PreviewReportError("invalid preview")
    monkeypatch.setattr(preview_cli, "format_preview_report", fail)
    output = tmp_path / "report.md"
    output.write_text("preserve", encoding="utf-8")
    assert preview_cli.run_preview_cli(("--synthetic", "--output-report", str(output), "--force")) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "preview report error: invalid preview" in captured.err
    assert output.read_text(encoding="utf-8") == "preserve"


def test_report_output_path_and_force(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "missing" / "report.md"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-report", str(missing))) == 3
    capsys.readouterr()
    output = tmp_path / "report.md"
    output.write_text("old", encoding="utf-8")
    assert preview_cli.run_preview_cli(("--synthetic", "--output-report", str(output))) == 3
    capsys.readouterr()
    assert output.read_text(encoding="utf-8") == "old"
    assert preview_cli.run_preview_cli(("--synthetic", "--output-report", str(output), "--force")) == 0
    capsys.readouterr()
    assert output.read_text(encoding="utf-8").startswith("# Preview Candidate Report")
