from dataclasses import fields
from pathlib import Path

import pytest

from uav_rf_terrain.candidate_source_zones import (
    CandidateSourceZoneAssignment,
    CandidateSourceZoneError,
    CandidateSourceZoneRecord,
    assign_source_zones_to_candidate_cells,
    summarize_candidate_source_zone_assignment,
)
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.grid import CandidateCell
from uav_rf_terrain.source_zones import SourceZoneSummary, TerrainSourceZone


def make_cell(cell_id: str, x_m: float, y_m: float = 0.0) -> CandidateCell:
    return CandidateCell(
        cell_id=cell_id,
        point=LocalPoint(x_m=x_m, y_m=y_m),
        distance_2d_m=abs(x_m),
        distance_3d_m=abs(x_m),
        within_operation_radius=True,
    )


def sample_cells() -> tuple[CandidateCell, ...]:
    return (
        make_cell("cell-esa", 0.0),
        make_cell("cell-wms", 100.0),
        make_cell("cell-dem-only", 200.0),
        make_cell("cell-mixed", 300.0),
    )


def sample_provider(x_m: float, y_m: float) -> TerrainSourceZone:
    assert y_m == 0.0
    if x_m == 0.0:
        return TerrainSourceZone.ESA_DERIVED
    if x_m == 100.0:
        return TerrainSourceZone.WMS_GAP_FILLED
    if x_m == 200.0:
        return TerrainSourceZone.DEM_ONLY_FALLBACK
    return TerrainSourceZone.MIXED_BOUNDARY


def test_assignment_error_is_value_error() -> None:
    assert issubclass(CandidateSourceZoneError, ValueError)


def test_candidate_cells_receive_all_source_zone_flags() -> None:
    assignment = assign_source_zones_to_candidate_cells(sample_cells(), sample_provider)
    zones_by_cell = {record.cell_id: record.source_zone for record in assignment.records}

    assert zones_by_cell["cell-esa"] is TerrainSourceZone.ESA_DERIVED
    assert zones_by_cell["cell-wms"] is TerrainSourceZone.WMS_GAP_FILLED
    assert zones_by_cell["cell-dem-only"] is TerrainSourceZone.DEM_ONLY_FALLBACK
    assert zones_by_cell["cell-mixed"] is TerrainSourceZone.MIXED_BOUNDARY


def test_summary_count_matches_source_zones_policy() -> None:
    assignment = assign_source_zones_to_candidate_cells(sample_cells(), sample_provider)
    summary = assignment.source_zone_summary

    assert isinstance(summary, SourceZoneSummary)
    assert summary.esa_derived_count == 1
    assert summary.wms_gap_filled_count == 1
    assert summary.dem_only_fallback_count == 1
    assert summary.mixed_boundary_count == 1
    assert summary.source_sensitive is True
    assert summary.dominant_zone is TerrainSourceZone.MIXED_BOUNDARY


def test_source_sensitive_count_matches_non_esa_records() -> None:
    assignment = assign_source_zones_to_candidate_cells(sample_cells(), sample_provider)

    assert assignment.source_sensitive_count == 3
    assert sum(record.source_sensitive for record in assignment.records) == 3


def test_assignment_radius_is_recorded_when_valid() -> None:
    assignment = assign_source_zones_to_candidate_cells(
        sample_cells(),
        sample_provider,
        assignment_radius_cells=2,
    )

    assert assignment.assignment_radius_cells == 2


def test_summarize_candidate_source_zone_assignment_returns_expected_keys() -> None:
    assignment = assign_source_zones_to_candidate_cells(sample_cells(), sample_provider)
    summary = summarize_candidate_source_zone_assignment(assignment)

    required_keys = {
        "candidate_source_zone_record_count",
        "esa_candidate_source_zone_count",
        "wms_gap_filled_candidate_source_zone_count",
        "dem_only_fallback_candidate_source_zone_count",
        "mixed_boundary_candidate_source_zone_count",
        "source_sensitive_candidate_source_zone_count",
        "candidate_source_zone_dominant_zone",
        "candidate_source_zone_source_sensitive",
        "candidate_source_zone_assignment_radius_cells",
        "candidate_source_zone_reason",
    }
    assert required_keys.issubset(summary.keys())
    assert summary["candidate_source_zone_record_count"] == 4
    assert summary["source_sensitive_candidate_source_zone_count"] == 3


def test_empty_cell_list_raises() -> None:
    with pytest.raises(CandidateSourceZoneError, match="cells"):
        assign_source_zones_to_candidate_cells((), sample_provider)


def test_invalid_provider_result_raises() -> None:
    def invalid_provider(x_m: float, y_m: float) -> TerrainSourceZone:
        del x_m, y_m
        return "esa_derived"  # type: ignore[return-value]

    with pytest.raises(CandidateSourceZoneError, match="source_zone"):
        assign_source_zones_to_candidate_cells(sample_cells(), invalid_provider)


def test_provider_exception_wraps_original_message() -> None:
    def failing_provider(x_m: float, y_m: float) -> TerrainSourceZone:
        del x_m, y_m
        raise RuntimeError("provider unavailable")

    with pytest.raises(CandidateSourceZoneError, match="provider unavailable") as exc_info:
        assign_source_zones_to_candidate_cells(sample_cells(), failing_provider)

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_non_finite_coordinate_raises() -> None:
    cells = (make_cell("cell-bad", float("nan")),)

    with pytest.raises(CandidateSourceZoneError, match="finite"):
        assign_source_zones_to_candidate_cells(cells, sample_provider)


def test_empty_cell_id_raises() -> None:
    cells = (make_cell("", 0.0),)

    with pytest.raises(CandidateSourceZoneError, match="cell_id"):
        assign_source_zones_to_candidate_cells(cells, sample_provider)


def test_negative_assignment_radius_cells_raises() -> None:
    with pytest.raises(CandidateSourceZoneError, match="assignment_radius_cells"):
        assign_source_zones_to_candidate_cells(
            sample_cells(),
            sample_provider,
            assignment_radius_cells=-1,
        )


def test_assignment_validation_rejects_mismatched_source_sensitive_count() -> None:
    assignment = assign_source_zones_to_candidate_cells(sample_cells(), sample_provider)

    with pytest.raises(CandidateSourceZoneError, match="source_sensitive_count"):
        CandidateSourceZoneAssignment(
            records=assignment.records,
            source_zone_summary=assignment.source_zone_summary,
            source_sensitive_count=0,
            assignment_radius_cells=None,
            reason="bad count",
        )


def test_record_validation_rejects_invalid_values() -> None:
    with pytest.raises(CandidateSourceZoneError):
        CandidateSourceZoneRecord(
            cell_id="",
            x_m=0.0,
            y_m=0.0,
            source_zone=TerrainSourceZone.ESA_DERIVED,
            source_sensitive=False,
            source_zone_reason="reason",
        )
    with pytest.raises(CandidateSourceZoneError):
        CandidateSourceZoneRecord(
            cell_id="cell",
            x_m=float("inf"),
            y_m=0.0,
            source_zone=TerrainSourceZone.ESA_DERIVED,
            source_sensitive=False,
            source_zone_reason="reason",
        )


def test_module_imports_no_gis_dependencies() -> None:
    module_text = Path("src/uav_rf_terrain/candidate_source_zones.py").read_text(
        encoding="utf-8"
    ).lower()
    blocked = (
        "ras" + "terio",
        "g" + "dal",
        "geo" + "pandas",
        "fo" + "lium",
        "stream" + "lit",
        "os" + "geo",
    )
    for name in blocked:
        assert name not in module_text


def test_records_contain_no_link_or_command_fields() -> None:
    blocked = {
        "rs" + "si",
        "si" + "nr",
        "packet_" + "loss",
        "flight_" + "command",
        "auto" + "pilot",
        "control_" + "api",
    }
    for dataclass_type in (CandidateSourceZoneRecord, CandidateSourceZoneAssignment):
        field_names = {field.name for field in fields(dataclass_type)}
        assert field_names.isdisjoint(blocked)
