from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from uav_rf_terrain.candidate_display_outputs import build_candidate_display_records
from uav_rf_terrain.candidate_display_preview import (
    CandidateDisplayPreviewError,
    build_candidate_display_preview_dict,
    format_candidate_display_preview,
)
from uav_rf_terrain.fresnel import DominantFresnelObstacle, FresnelAnalysis
from uav_rf_terrain.fresnel_diagnostics import (
    DIAGNOSTIC_FIELD_NAMES,
    CandidateFresnelDiagnostics,
    CandidateFresnelDiagnosticsError,
    candidate_fresnel_diagnostics_from_analysis,
)
from uav_rf_terrain.map_outputs import (
    attach_candidate_source_zone_map_properties,
    build_candidate_cell_map_features,
)
from uav_rf_terrain.preview_appendix_table import format_preview_appendix_table
from uav_rf_terrain.preview_report import PreviewReportError, format_preview_report
from uav_rf_terrain.preview_cli import run_preview_cli
from uav_rf_terrain.scenario_outputs import build_synthetic_candidate_records
from uav_rf_terrain.synthetic_candidate_preview_smoke import (
    build_synthetic_candidate_mgrs_by_candidate_id,
    build_synthetic_candidate_source_zone_metadata_by_candidate_id,
)


def _analysis(*, eligible: bool) -> FresnelAnalysis:
    obstacle = (
        DominantFresnelObstacle(
            sample_index=4,
            distance_from_start_m=123.456,
            dsm_msl=87.654,
            los_msl=90.123,
            clearance_m=2.469,
            clearance_ratio=0.32149,
            fresnel_radius_m=7.681,
            fresnel_sample_score=32.149,
            nu=-0.45419,
            diffraction_loss_db=1.23456,
        )
        if eligible
        else None
    )
    return FresnelAnalysis(
        scenario_name="diagnostic-test",
        frequency_hz=2_400_000_000.0,
        wavelength_m=0.1249,
        samples=(),
        dsm_fresnel_score=95.123456,
        average_fresnel_score=95.123456,
        worst_obstacle_score=32.149 if eligible else None,
        dominant_obstacle=obstacle,
    )


def _display_bundle(diagnostics: CandidateFresnelDiagnostics):
    candidates = list(build_synthetic_candidate_records())
    candidates[0] = replace(candidates[0], fresnel_diagnostics=diagnostics)
    features = build_candidate_cell_map_features(candidates)
    mgrs = build_synthetic_candidate_mgrs_by_candidate_id(
        tuple(feature.candidate_id for feature in features)
    )
    metadata = build_synthetic_candidate_source_zone_metadata_by_candidate_id(features, mgrs)
    attached = attach_candidate_source_zone_map_properties(features, metadata)
    return build_candidate_display_records(attached)


def test_analysis_conversion_and_candidate_preview_path_preserve_diagnostics() -> None:
    analysis = _analysis(eligible=True)
    original = deepcopy(analysis)
    diagnostics = candidate_fresnel_diagnostics_from_analysis(analysis)
    bundle = _display_bundle(diagnostics)
    preview = build_candidate_display_preview_dict(bundle)
    record = preview["records"][0]

    assert analysis == original
    assert set(DIAGNOSTIC_FIELD_NAMES).issubset(record)
    assert record["average_fresnel_score"] == 95.123456
    assert record["dominant_obstacle_diffraction_loss_db"] == 1.23456
    assert "dominant_obstacle_sample_index" not in record
    assert bundle.records[0].overall_score == build_synthetic_candidate_records()[0].candidate_score.overall_score
    assert not DIAGNOSTIC_FIELD_NAMES.intersection(
        bundle.records[0].source_zone_reason.split()
    )


def test_no_eligible_conversion_emits_average_plus_nine_null_values() -> None:
    diagnostics = candidate_fresnel_diagnostics_from_analysis(_analysis(eligible=False))
    record = build_candidate_display_preview_dict(_display_bundle(diagnostics))["records"][0]

    assert record["average_fresnel_score"] == 95.123456
    assert all(record[name] is None for name in DIAGNOSTIC_FIELD_NAMES if name != "average_fresnel_score")


@pytest.mark.parametrize("value", (float("nan"), float("inf"), float("-inf"), True))
def test_diagnostic_model_rejects_non_finite_and_bool_average(value: float) -> None:
    with pytest.raises(CandidateFresnelDiagnosticsError):
        CandidateFresnelDiagnostics.no_eligible(average_fresnel_score=value)


def test_preview_validation_rejects_partial_and_mixed_diagnostics() -> None:
    diagnostics = candidate_fresnel_diagnostics_from_analysis(_analysis(eligible=True))
    bundle = _display_bundle(diagnostics)
    preview = build_candidate_display_preview_dict(bundle)
    record = preview["records"][0]
    del record["dominant_obstacle_nu"]
    with pytest.raises(CandidateDisplayPreviewError):
        from uav_rf_terrain.candidate_display_preview import CandidateDisplayPreview

        CandidateDisplayPreview(
            title=str(preview["title"]),
            external_coordinate_format="MGRS",
            user_coordinate_field="candidate_cell_mgrs",
            record_count=int(preview["record_count"]),
            source_sensitive_count=int(preview["source_sensitive_count"]),
            records=tuple(preview["records"]),
            summary=preview["summary"],
            reason=str(preview["reason"]),
        )

    report_preview = build_candidate_display_preview_dict(bundle)
    report_preview["records"][0]["dominant_obstacle_nu"] = None
    with pytest.raises(PreviewReportError):
        format_preview_report(report_preview)

    non_finite = build_candidate_display_preview_dict(bundle)
    non_finite["records"][0]["dominant_obstacle_nu"] = float("inf")
    with pytest.raises(PreviewReportError):
        format_preview_report(non_finite)


def test_plain_text_report_and_appendix_table_contracts() -> None:
    eligible_bundle = _display_bundle(
        candidate_fresnel_diagnostics_from_analysis(_analysis(eligible=True))
    )
    no_eligible_bundle = _display_bundle(
        candidate_fresnel_diagnostics_from_analysis(_analysis(eligible=False))
    )
    text = format_candidate_display_preview(eligible_bundle)
    no_eligible_text = format_candidate_display_preview(no_eligible_bundle)
    preview = build_candidate_display_preview_dict(eligible_bundle)
    report = format_preview_report(preview)
    table = format_preview_appendix_table(preview)

    assert "fresnel_avg=95.1 | fresnel_worst=32.1 | diffraction_loss=1.2 dB" in text
    assert "fresnel_avg=95.1 | fresnel_worst=unavailable | diffraction_loss=unavailable" in no_eligible_text
    headings = ("## Candidate Overview", "## Fresnel Diagnostics", "## Source-Zone Interpretation")
    assert [report.index(heading) for heading in headings] == sorted(report.index(heading) for heading in headings)
    assert "candidate-green | 52S CG 00000 00000" in report
    assert "distance=123.5 m" in report
    assert "clearance_ratio=0.321" in report
    assert "nu=-0.454" in report
    assert "diffraction_loss=1.2 dB" in report
    assert "diagnostic proxies only" in report
    assert not any(name in table for name in DIAGNOSTIC_FIELD_NAMES)


def test_legacy_report_states_diagnostics_unavailable() -> None:
    from uav_rf_terrain.synthetic_candidate_preview_smoke import (
        build_synthetic_candidate_preview_smoke,
    )

    preview = build_synthetic_candidate_preview_smoke().preview_dict
    original = deepcopy(preview)
    report = format_preview_report(preview)
    assert "diagnostics unavailable in this preview record" in report
    assert preview == original


def test_saved_json_report_stdout_and_file_are_identical(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    preview = build_candidate_display_preview_dict(
        _display_bundle(candidate_fresnel_diagnostics_from_analysis(_analysis(eligible=True)))
    )
    input_path = tmp_path / "preview.json"
    output_path = tmp_path / "report.md"
    input_path.write_text(json.dumps(preview), encoding="utf-8")

    assert run_preview_cli(["--input-json", str(input_path), "--report"]) == 0
    stdout_report = capsys.readouterr().out
    assert run_preview_cli(
        ["--input-json", str(input_path), "--output-report", str(output_path)]
    ) == 0
    capsys.readouterr()
    assert output_path.read_text(encoding="utf-8") == stdout_report
