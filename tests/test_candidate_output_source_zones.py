from pathlib import Path

import pytest

from uav_rf_terrain.candidate_output_source_zones import (
    CandidateOutputSourceZoneError,
    CandidateSourceZoneOutputBundle,
    CandidateSourceZoneOutputRecord,
    build_candidate_source_zone_output_records,
    summarize_candidate_source_zone_outputs,
)
from uav_rf_terrain.candidate_source_zones import (
    CandidateSourceZoneAssignment,
    assign_source_zones_to_candidate_cells,
)
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.grid import CandidateCell
from uav_rf_terrain.source_zones import TerrainSourceZone, summarize_source_zones


def _cell(cell_id: str, x_m: float, y_m: float) -> CandidateCell:
    point = LocalPoint(x_m=x_m, y_m=y_m)
    return CandidateCell(
        cell_id=cell_id,
        point=point,
        distance_2d_m=0.0,
        distance_3d_m=0.0,
        within_operation_radius=True,
    )


def _assignment() -> CandidateSourceZoneAssignment:
    cells = (
        _cell("cell-esa", 0.0, 0.0),
        _cell("cell-wms", 90.0, 0.0),
        _cell("cell-dem", 180.0, 0.0),
        _cell("cell-mixed", 270.0, 0.0),
    )
    zones = {
        "cell-esa": TerrainSourceZone.ESA_DERIVED,
        "cell-wms": TerrainSourceZone.WMS_GAP_FILLED,
        "cell-dem": TerrainSourceZone.DEM_ONLY_FALLBACK,
        "cell-mixed": TerrainSourceZone.MIXED_BOUNDARY,
    }
    return assign_source_zones_to_candidate_cells(
        cells,
        lambda x_m, y_m: zones[f"cell-{['esa', 'wms', 'dem', 'mixed'][int(x_m // 90)]}"],
        assignment_radius_cells=3,
    )


def _mgrs_mapping() -> dict[str, str]:
    return {
        "cell-esa": "52S CG 00000 00000",
        "cell-wms": "52S CG 00090 00000",
        "cell-dem": "52S CG 00180 00000",
        "cell-mixed": "52S CG 00270 00000",
    }


def test_build_candidate_source_zone_output_records_uses_candidate_cell_mgrs() -> None:
    bundle = build_candidate_source_zone_output_records(_assignment(), _mgrs_mapping())

    assert isinstance(bundle, CandidateSourceZoneOutputBundle)
    assert len(bundle.records) == 4
    assert {record.candidate_cell_mgrs for record in bundle.records} == set(
        _mgrs_mapping().values()
    )
    assert all(record.internal_debug_available for record in bundle.records)
    assert all(not hasattr(record, "x_m") for record in bundle.records)
    assert all(not hasattr(record, "y_m") for record in bundle.records)


def test_source_zone_counts_and_sensitive_summary_are_preserved() -> None:
    bundle = build_candidate_source_zone_output_records(_assignment(), _mgrs_mapping())
    summary = summarize_candidate_source_zone_outputs(bundle)

    assert summary["candidate_source_zone_output_record_count"] == 4
    assert summary["candidate_source_zone_user_coordinate_field"] == "candidate_cell_mgrs"
    assert summary["esa_candidate_source_zone_output_count"] == 1
    assert summary["wms_gap_filled_candidate_source_zone_output_count"] == 1
    assert summary["dem_only_fallback_candidate_source_zone_output_count"] == 1
    assert summary["mixed_boundary_candidate_source_zone_output_count"] == 1
    assert summary["source_sensitive_candidate_source_zone_output_count"] == 3
    assert summary["candidate_source_zone_output_source_sensitive"] is True
    assert summary["candidate_source_zone_output_dominant_zone"] == "mixed_boundary"
    assert summary["internal_debug_available_candidate_count"] == 4


def test_output_bundle_validates_summary_consistency() -> None:
    record = CandidateSourceZoneOutputRecord(
        cell_id="cell-esa",
        candidate_cell_mgrs="52S CG 00000 00000",
        source_zone=TerrainSourceZone.ESA_DERIVED,
        source_sensitive=False,
        source_zone_reason="ESA-derived candidate source zone.",
    )
    source_summary = summarize_source_zones((TerrainSourceZone.ESA_DERIVED,))

    with pytest.raises(CandidateOutputSourceZoneError):
        CandidateSourceZoneOutputBundle(
            records=(record,),
            source_zone_summary=source_summary,
            source_sensitive_count=1,
            dominant_source_zone=TerrainSourceZone.ESA_DERIVED,
            reason="bad count",
        )


def test_candidate_cell_mgrs_is_required_and_non_empty() -> None:
    mapping = _mgrs_mapping()
    mapping["cell-wms"] = " "

    with pytest.raises(CandidateOutputSourceZoneError):
        build_candidate_source_zone_output_records(_assignment(), mapping)


def test_missing_candidate_cell_mgrs_for_cell_raises() -> None:
    mapping = _mgrs_mapping()
    del mapping["cell-dem"]

    with pytest.raises(CandidateOutputSourceZoneError):
        build_candidate_source_zone_output_records(_assignment(), mapping)


def test_assignment_type_is_required() -> None:
    with pytest.raises(CandidateOutputSourceZoneError):
        build_candidate_source_zone_output_records(object(), _mgrs_mapping())  # type: ignore[arg-type]


def test_mapping_type_is_required() -> None:
    with pytest.raises(CandidateOutputSourceZoneError):
        build_candidate_source_zone_output_records(_assignment(), object())  # type: ignore[arg-type]


def test_source_sensitive_must_match_source_zone_policy() -> None:
    with pytest.raises(CandidateOutputSourceZoneError):
        CandidateSourceZoneOutputRecord(
            cell_id="cell-wms",
            candidate_cell_mgrs="52S CG 00090 00000",
            source_zone=TerrainSourceZone.WMS_GAP_FILLED,
            source_sensitive=False,
            source_zone_reason="WMS gap-filled candidate source zone.",
        )


def test_summary_requires_bundle_type() -> None:
    with pytest.raises(CandidateOutputSourceZoneError):
        summarize_candidate_source_zone_outputs(object())  # type: ignore[arg-type]


def test_candidate_output_source_zone_module_has_no_gis_dependency_imports() -> None:
    module_text = Path("src/uav_rf_terrain/candidate_output_source_zones.py").read_text(
        encoding="utf-8"
    )

    for token in ("rasterio", "gdal", "geopandas", "osgeo", "folium", "streamlit"):
        assert token not in module_text.lower()


def test_output_records_have_no_internal_coordinate_fields_by_default() -> None:
    record_fields = set(CandidateSourceZoneOutputRecord.__dataclass_fields__)

    assert "candidate_cell_mgrs" in record_fields
    assert "x_m" not in record_fields
    assert "y_m" not in record_fields
    assert "row" not in record_fields
    assert "col" not in record_fields
    assert "epsg5179_x_m" not in record_fields
    assert "epsg5179_y_m" not in record_fields


def test_new_files_do_not_add_forbidden_wording() -> None:
    forbidden_phrases = (
        "실제 통신 성공률" + " 예측",
        "RSSI" + " 예측",
        "SINR" + " 예측",
        "packet loss" + " 예측",
        "실측 검증" + " 완료",
        "정찰 성공" + " 보장",
        "통신 가능" + " 보장",
        "실제 비행 가능" + " 보장",
        "공역승인 최적고도" + " 보장",
        "guaranteed " + "communication",
        "guaranteed " + "reconnaissance",
        "guaranteed " + "flight safety",
        "airspace approval " + "guarantee",
        "control-system command " + "output",
        "vehicle-execution command " + "output",
        "autopilot " + "integration",
        "flight command " + "generation",
    )
    paths = (
        Path("src/uav_rf_terrain/candidate_output_source_zones.py"),
        Path("docs/paper/experiments/EXP-20260711-015-candidate-source-zone-output-metadata.md"),
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in text
