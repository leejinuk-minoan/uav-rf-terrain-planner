from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from examples import local_candidate_source_zone_smoke as smoke
from uav_rf_terrain.candidate_source_zones import CandidateSourceZoneError
from uav_rf_terrain.source_zone_raster import SourceZoneRasterError
from uav_rf_terrain.source_zones import TerrainSourceZone


def test_smoke_helper_calls_provider_and_summarizes_counts() -> None:
    cells = smoke.build_smoke_candidate_cells(((0.0, 0.0),), spacing_m=90.0, radius_cells=1)
    calls: list[tuple[float, float]] = []

    def provider(x_m: float, y_m: float) -> TerrainSourceZone:
        calls.append((x_m, y_m))
        if x_m < 0:
            return TerrainSourceZone.ESA_DERIVED
        if x_m > 0:
            return TerrainSourceZone.WMS_GAP_FILLED
        return TerrainSourceZone.DEM_ONLY_FALLBACK

    assignment = smoke.run_candidate_source_zone_smoke(
        cells, provider, boundary_radius_cells=3
    )
    assert len(calls) == len(cells) == 9
    assert assignment.source_zone_summary.esa_derived_count == 3
    assert assignment.source_zone_summary.wms_gap_filled_count == 3
    assert assignment.source_zone_summary.dem_only_fallback_count == 3
    assert assignment.source_sensitive_count == 6


def test_summary_format_has_aggregate_fields_only() -> None:
    cells = smoke.build_smoke_candidate_cells(((0.0, 0.0),), spacing_m=90.0, radius_cells=1)
    assignment = smoke.run_candidate_source_zone_smoke(
        cells, lambda _x, _y: TerrainSourceZone.ESA_DERIVED,
        boundary_radius_cells=3,
    )
    output = smoke.format_smoke_summary(assignment).lower()
    assert "candidate_count=9" in output
    assert "esa_derived_count=9" in output
    assert "point_x" not in output
    assert "point_y" not in output
    assert "\\" not in output
    assert "/" + "users/" not in output
    assert "/" + "home/" not in output


@pytest.mark.parametrize("error", (SourceZoneRasterError("bad raster"), CandidateSourceZoneError("bad assignment")))
def test_expected_error_returns_one_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
) -> None:
    monkeypatch.setattr(smoke, "_run_local_smoke", lambda _args: (_ for _ in ()).throw(error))
    result = smoke.main(_required_args())
    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err.startswith("candidate source-zone smoke error:")
    assert "Traceback" not in captured.err


def test_smoke_module_has_no_prohibited_fields_or_dependencies() -> None:
    text = Path("examples/local_candidate_source_zone_smoke.py").read_text(encoding="utf-8").lower()
    prohibited = {
        "rs" + "si",
        "si" + "nr",
        "packet_" + "loss",
        "flight_" + "command",
        "auto" + "pilot",
        "control_" + "api",
    }
    assert all(term not in text for term in prohibited)
    assert "import " + "rasterio" not in text
    assert "from " + "rasterio" not in text
    assert "import " + "geopandas" not in text


def test_assignment_records_have_no_prohibited_fields() -> None:
    field_names = {field.name for field in fields(smoke.CandidateSourceZoneAssignment)}
    assert field_names.isdisjoint({"rssi", "sinr", "packet_loss", "flight_command", "autopilot", "control_api"})


def _required_args() -> list[str]:
    return [
        "--dem-path", "dem.tif",
        "--original-landcover-path", "original.tif",
        "--gap-filled-landcover-path", "filled.tif",
    ]
