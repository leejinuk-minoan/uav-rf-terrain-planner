from pathlib import Path

import pytest

from uav_rf_terrain.candidate_map_source_zone_metadata import (
    CandidateMapSourceZoneMetadataBundle,
    CandidateMapSourceZoneMetadataError,
    CandidateMapSourceZoneProperties,
    build_candidate_map_source_zone_properties,
    build_candidate_map_source_zone_properties_by_cell_id,
    summarize_candidate_map_source_zone_metadata,
)
from uav_rf_terrain.candidate_output_source_zones import (
    CandidateSourceZoneOutputBundle,
    build_candidate_source_zone_output_records,
)
from uav_rf_terrain.candidate_source_zones import assign_source_zones_to_candidate_cells
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.grid import CandidateCell
from uav_rf_terrain.source_zones import TerrainSourceZone, summarize_source_zones


def _cell(cell_id: str, x_m: float, y_m: float) -> CandidateCell:
    return CandidateCell(
        cell_id=cell_id,
        point=LocalPoint(x_m=x_m, y_m=y_m),
        distance_2d_m=0.0,
        distance_3d_m=0.0,
        within_operation_radius=True,
    )


def _output_bundle() -> CandidateSourceZoneOutputBundle:
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
    assignment = assign_source_zones_to_candidate_cells(
        cells,
        lambda x_m, y_m: zones[f"cell-{['esa', 'wms', 'dem', 'mixed'][int(x_m // 90)]}"],
        assignment_radius_cells=3,
    )
    mgrs_by_cell_id = {
        "cell-esa": "52S CG 00000 00000",
        "cell-wms": "52S CG 00090 00000",
        "cell-dem": "52S CG 00180 00000",
        "cell-mixed": "52S CG 00270 00000",
    }
    return build_candidate_source_zone_output_records(assignment, mgrs_by_cell_id)


def test_build_candidate_map_source_zone_properties_from_output_bundle() -> None:
    metadata_bundle = build_candidate_map_source_zone_properties(_output_bundle())

    assert isinstance(metadata_bundle, CandidateMapSourceZoneMetadataBundle)
    assert len(metadata_bundle.properties) == 4
    assert metadata_bundle.source_sensitive_count == 3
    assert metadata_bundle.dominant_source_zone == TerrainSourceZone.MIXED_BOUNDARY


def test_map_ready_properties_include_mgrs_and_source_zone_metadata() -> None:
    metadata_bundle = build_candidate_map_source_zone_properties(_output_bundle())
    first = metadata_bundle.properties[0]
    properties = first.to_map_properties()

    assert properties["cell_id"] == "cell-esa"
    assert properties["candidate_cell_mgrs"] == "52S CG 00000 00000"
    assert properties["external_coordinate_format"] == "MGRS"
    assert properties["user_coordinate_field"] == "candidate_cell_mgrs"
    assert properties["source_zone"] == "esa_derived"
    assert properties["source_sensitive"] is False
    assert isinstance(properties["source_zone_reason"], str)


def test_source_zone_counts_sensitive_count_and_dominant_zone_summary() -> None:
    metadata_bundle = build_candidate_map_source_zone_properties(_output_bundle())
    summary = summarize_candidate_map_source_zone_metadata(metadata_bundle)

    assert summary["candidate_map_source_zone_metadata_count"] == 4
    assert summary["candidate_map_source_zone_user_coordinate_field"] == "candidate_cell_mgrs"
    assert summary["external_coordinate_format"] == "MGRS"
    assert summary["esa_candidate_map_source_zone_count"] == 1
    assert summary["wms_gap_filled_candidate_map_source_zone_count"] == 1
    assert summary["dem_only_fallback_candidate_map_source_zone_count"] == 1
    assert summary["mixed_boundary_candidate_map_source_zone_count"] == 1
    assert summary["source_sensitive_candidate_map_source_zone_count"] == 3
    assert summary["dominant_candidate_map_source_zone"] == "mixed_boundary"
    assert "candidate_cell_mgrs" in str(summary["candidate_map_source_zone_metadata_reason"])


def test_by_cell_id_mapping_uses_to_map_properties() -> None:
    metadata_bundle = build_candidate_map_source_zone_properties(_output_bundle())
    by_cell_id = build_candidate_map_source_zone_properties_by_cell_id(metadata_bundle)

    assert set(by_cell_id) == {"cell-esa", "cell-wms", "cell-dem", "cell-mixed"}
    assert by_cell_id["cell-wms"]["candidate_cell_mgrs"] == "52S CG 00090 00000"
    assert by_cell_id["cell-dem"]["source_zone"] == "dem_only_fallback"
    assert by_cell_id["cell-mixed"]["source_sensitive"] is True


def test_duplicate_cell_id_in_mapping_raises() -> None:
    source_summary = summarize_source_zones(
        (TerrainSourceZone.ESA_DERIVED, TerrainSourceZone.WMS_GAP_FILLED)
    )
    metadata_bundle = CandidateMapSourceZoneMetadataBundle(
        properties=(
            CandidateMapSourceZoneProperties(
                cell_id="duplicate-cell",
                candidate_cell_mgrs="52S CG 00000 00000",
                external_coordinate_format="MGRS",
                source_zone=TerrainSourceZone.ESA_DERIVED,
                source_sensitive=False,
                source_zone_reason="ESA-derived source zone only.",
            ),
            CandidateMapSourceZoneProperties(
                cell_id="duplicate-cell",
                candidate_cell_mgrs="52S CG 00090 00000",
                external_coordinate_format="MGRS",
                source_zone=TerrainSourceZone.WMS_GAP_FILLED,
                source_sensitive=True,
                source_zone_reason="WMS gap-filled source zone present.",
            ),
        ),
        source_zone_summary=source_summary,
        source_sensitive_count=1,
        dominant_source_zone=source_summary.dominant_zone,
        reason="duplicate test bundle",
    )

    with pytest.raises(CandidateMapSourceZoneMetadataError):
        build_candidate_map_source_zone_properties_by_cell_id(metadata_bundle)


def test_wrong_bundle_type_raises() -> None:
    with pytest.raises(CandidateMapSourceZoneMetadataError):
        build_candidate_map_source_zone_properties(object())  # type: ignore[arg-type]

    with pytest.raises(CandidateMapSourceZoneMetadataError):
        summarize_candidate_map_source_zone_metadata(object())  # type: ignore[arg-type]

    with pytest.raises(CandidateMapSourceZoneMetadataError):
        build_candidate_map_source_zone_properties_by_cell_id(object())  # type: ignore[arg-type]


def test_empty_metadata_records_raise() -> None:
    source_summary = summarize_source_zones((TerrainSourceZone.ESA_DERIVED,))

    with pytest.raises(CandidateMapSourceZoneMetadataError):
        CandidateMapSourceZoneMetadataBundle(
            properties=(),
            source_zone_summary=source_summary,
            source_sensitive_count=0,
            dominant_source_zone=TerrainSourceZone.ESA_DERIVED,
            reason="empty test bundle",
        )


def test_source_sensitive_must_match_source_zone_policy() -> None:
    with pytest.raises(CandidateMapSourceZoneMetadataError):
        CandidateMapSourceZoneProperties(
            cell_id="cell-wms",
            candidate_cell_mgrs="52S CG 00090 00000",
            external_coordinate_format="MGRS",
            source_zone=TerrainSourceZone.WMS_GAP_FILLED,
            source_sensitive=False,
            source_zone_reason="WMS gap-filled source zone present.",
        )


def test_properties_dict_has_no_internal_coordinate_keys() -> None:
    metadata_bundle = build_candidate_map_source_zone_properties(_output_bundle())
    properties = metadata_bundle.properties[0].to_map_properties()
    blocked_keys = {
        "x_m",
        "y_m",
        "row",
        "col",
        "epsg5179_x_m",
        "epsg5179_y_m",
        "wgs84_lat",
        "wgs84_lon",
        "local_x_m",
        "local_y_m",
        "raster_row",
        "raster_col",
    }

    assert properties.keys().isdisjoint(blocked_keys)


def test_module_has_no_gis_raster_or_rendering_dependency_imports() -> None:
    module_text = Path("src/uav_rf_terrain/candidate_map_source_zone_metadata.py").read_text(
        encoding="utf-8"
    )

    for token in ("rasterio", "gdal", "geopandas", "osgeo", "folium", "streamlit"):
        assert token not in module_text.lower()


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
        Path("src/uav_rf_terrain/candidate_map_source_zone_metadata.py"),
        Path("docs/handoff/task-021b-candidate-source-zone-map-metadata.md"),
        Path("docs/paper/experiments/EXP-20260711-016-candidate-source-zone-map-metadata.md"),
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in text
