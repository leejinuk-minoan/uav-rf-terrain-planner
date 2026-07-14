from __future__ import annotations

from dataclasses import replace

import pytest

from uav_rf_terrain.coordinate_conversion import Wgs84MapPoint
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.launch_site_selection import LaunchSiteSelectionError, select_launch_site
from uav_rf_terrain.local_html_map_renderer import (
    LocalHtmlMapRenderConfig,
    LocalHtmlMapRendererError,
    _number,
    _viewport,
    render_local_html_map,
    write_local_html_map,
)
from uav_rf_terrain.map_outputs import style_for_color_class
from uav_rf_terrain.real_terrain_candidate_analysis import (
    CandidateAnalysisMapFeature,
    CandidateAnalysisRecord,
    CandidateAnalysisState,
    RealTerrainLaunchAreaResult,
    RealTerrainLaunchAreaSummary,
    SourceZoneAvailability,
)
from uav_rf_terrain.real_terrain_launch_area_map import (
    RealTerrainLaunchAreaMapConfig,
    RealTerrainLaunchAreaMapError,
    build_real_terrain_launch_area_map_package,
)
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.scoring import CandidateScore
from uav_rf_terrain.terrain_data import RASTER_TYPE_DEM, RASTER_TYPE_DSM, TerrainDatasetMetadata, TerrainRasterMetadata


def test_map_config_requires_explicit_positive_cell_size_and_actual_bool() -> None:
    assert RealTerrainLaunchAreaMapConfig(candidate_cell_size_m=180.0).include_excluded is True

    with pytest.raises(RealTerrainLaunchAreaMapError):
        RealTerrainLaunchAreaMapConfig(candidate_cell_size_m=True)
    with pytest.raises(RealTerrainLaunchAreaMapError):
        RealTerrainLaunchAreaMapConfig(candidate_cell_size_m=0.0)
    with pytest.raises(RealTerrainLaunchAreaMapError):
        RealTerrainLaunchAreaMapConfig(candidate_cell_size_m=180.0, include_excluded=1)  # type: ignore[arg-type]


def test_map_point_ring_is_closed_with_four_distinct_wgs84_corners() -> None:
    ring = (
        Wgs84MapPoint(127.0, 37.0),
        Wgs84MapPoint(127.1, 37.0),
        Wgs84MapPoint(127.1, 37.1),
        Wgs84MapPoint(127.0, 37.1),
        Wgs84MapPoint(127.0, 37.0),
    )

    assert ring[0] == ring[-1]
    assert len(set(ring[:-1])) == 4


def _result() -> RealTerrainLaunchAreaResult:
    common = dict(source_dataset_name="test", source_provider="test", license_or_terms="test", crs="EPSG:5179", resolution_m=10.0, width=5, height=5, bounds=(0.0, 0.0, 40.0, 40.0), nodata_value=None, vertical_datum="MSL", processing_summary="test", is_synthetic=True, is_redistributable_processed_data=True)
    metadata = TerrainDatasetMetadata("test", TerrainRasterMetadata("dem", RASTER_TYPE_DEM, **common), TerrainRasterMetadata("dsm", RASTER_TYPE_DSM, **common), "2026-07-14", "pytest", "aligned", "test")
    score = CandidateScore(10.0, 100.0, 100.0, 100.0, 90.0, 100.0, 98.0)
    point = LocalPoint(20.0, 20.0)
    record = CandidateAnalysisRecord("candidate-001", point, point, CandidateAnalysisState.VALID_SCORED, "valid red candidate", 10.0, 10.0, True, 100.0, 100.0, 120.0, 2, score, ColorClass.RED, None, None, SourceZoneAvailability.NOT_REQUESTED, None, "not requested")
    feature = CandidateAnalysisMapFeature("candidate-feature-00000", "candidate-001", 20.0, 20.0, "EPSG:5179", None, "projected_only", CandidateAnalysisState.VALID_SCORED, ColorClass.RED, style_for_color_class(ColorClass.RED), 98.0, 100.0, 10.0, True, "valid red candidate", None, SourceZoneAvailability.NOT_REQUESTED, None, "not requested", None)
    summary = RealTerrainLaunchAreaSummary(1, 1, 0, tuple((state.value, 1 if state is CandidateAnalysisState.VALID_SCORED else 0) for state in CandidateAnalysisState), tuple((color.value, 1 if color is ColorClass.RED else 0) for color in ColorClass), tuple((state.value, 1 if state is SourceZoneAvailability.NOT_REQUESTED else 0) for state in SourceZoneAvailability), 0)
    return RealTerrainLaunchAreaResult("test scenario", metadata, point, 100.0, 100.0, 120.0, (record,), (feature,), summary, ())


def test_builder_uses_actual_feature_center_and_deterministic_conversion_order() -> None:
    wgs_calls: list[LocalPoint] = []
    mgrs_calls: list[tuple[LocalPoint, int]] = []

    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        wgs_calls.append(point)
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        mgrs_calls.append((point, precision))
        return "52scb1234512345"

    package = build_real_terrain_launch_area_map_package(_result(), RealTerrainLaunchAreaMapConfig(10.0), projected_to_wgs84=wgs, projected_to_mgrs=mgrs)

    polygon = package.candidate_polygons[0]
    assert polygon.center_wgs84 == Wgs84MapPoint(0.02, 0.02)
    assert polygon.polygon_wgs84 == (
        Wgs84MapPoint(0.015, 0.015), Wgs84MapPoint(0.025, 0.015), Wgs84MapPoint(0.025, 0.025), Wgs84MapPoint(0.015, 0.025), Wgs84MapPoint(0.015, 0.015),
    )
    assert wgs_calls == [LocalPoint(20.0, 20.0), LocalPoint(20.0, 20.0), LocalPoint(15.0, 15.0), LocalPoint(25.0, 15.0), LocalPoint(25.0, 25.0), LocalPoint(15.0, 25.0)]
    assert mgrs_calls == [(LocalPoint(20.0, 20.0), 5), (LocalPoint(20.0, 20.0), 5)]
    assert polygon.popup.candidate_cell_mgrs == "52SCB1234512345"
    assert polygon.selectable is True


def test_builder_rejects_unknown_or_hidden_selected_candidate() -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        return "52SCB1234512345"

    with pytest.raises(RealTerrainLaunchAreaMapError, match="not found"):
        build_real_terrain_launch_area_map_package(_result(), RealTerrainLaunchAreaMapConfig(10.0, selected_candidate_id="missing"), projected_to_wgs84=wgs, projected_to_mgrs=mgrs)


def test_selection_and_renderer_keep_package_selection_separate_from_preview() -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        return "52SCB1234512345"

    result = _result()
    package = build_real_terrain_launch_area_map_package(result, RealTerrainLaunchAreaMapConfig(10.0), projected_to_wgs84=wgs, projected_to_mgrs=mgrs)
    selected = select_launch_site(result, package, "candidate-001")
    html = render_local_html_map(package)

    assert selected.candidate_id == "candidate-001"
    assert selected.launch_site_mgrs == "52SCB1234512345"
    assert selected.external_coordinate_format == "MGRS"
    assert package.selected_candidate_id is None
    assert "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;" in html
    assert "preview candidate:" in html
    assert 'id="reset-preview"' in html
    assert "reset-preview" in html
    assert "innerHTML" not in html
    selected_package = build_real_terrain_launch_area_map_package(result, RealTerrainLaunchAreaMapConfig(10.0, selected_candidate_id="candidate-001"), projected_to_wgs84=wgs, projected_to_mgrs=mgrs)
    with pytest.raises(LaunchSiteSelectionError, match="conflicting"):
        select_launch_site(result, selected_package, "other")


def test_selection_rejects_an_empty_popup_mgrs_value() -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        return "52SCB1234512345"

    result = _result()
    package = build_real_terrain_launch_area_map_package(
        result,
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=wgs,
        projected_to_mgrs=mgrs,
    )
    polygon = package.candidate_polygons[0]
    invalid_package = replace(
        package,
        candidate_polygons=(replace(polygon, popup=replace(polygon.popup, candidate_cell_mgrs="")),),
    )

    with pytest.raises(LaunchSiteSelectionError, match="MGRS"):
        select_launch_site(result, invalid_package, "candidate-001")


def test_renderer_handles_edge_viewports_and_normalizes_negative_zero() -> None:
    config = LocalHtmlMapRenderConfig(width_px=100, height_px=80, padding_px=10)
    diagonal = _viewport([Wgs84MapPoint(0.0, 0.0), Wgs84MapPoint(1.0, 1.0)], config)
    zero_x = _viewport([Wgs84MapPoint(1.0, 0.0), Wgs84MapPoint(1.0, 1.0)], config)
    zero_y = _viewport([Wgs84MapPoint(0.0, 1.0), Wgs84MapPoint(1.0, 1.0)], config)
    zero_both = _viewport([Wgs84MapPoint(1.0, 1.0)], config)

    assert diagonal[0][1] > diagonal[1][1]
    assert zero_x[0][0] == zero_x[1][0] == 50.0
    assert zero_y[0][1] == zero_y[1][1] == 40.0
    assert zero_both == [(50.0, 40.0)]
    assert _number(-0.0) == "0.000000"
    assert _number(1.0 / 3.0) == "0.333333"
    with pytest.raises(LocalHtmlMapRendererError, match="180"):
        _viewport([Wgs84MapPoint(-100.0, 0.0), Wgs84MapPoint(100.0, 0.0)], config)


def test_renderer_escapes_data_and_writes_only_an_explicit_path(tmp_path: pytest.TempPathFactory) -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        return "52SCB1234512345"

    package = build_real_terrain_launch_area_map_package(
        _result(),
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=wgs,
        projected_to_mgrs=mgrs,
    )
    malicious = '<script>"\'&<></script>'
    polygon = package.candidate_polygons[0]
    unsafe_package = replace(
        package,
        scenario_name=malicious,
        candidate_polygons=(
            replace(polygon, candidate_id=malicious, popup=replace(polygon.popup, candidate_id=malicious)),
        ),
    )

    first = render_local_html_map(unsafe_package)
    second = render_local_html_map(unsafe_package)
    output = tmp_path / "map.html"
    written = write_local_html_map(unsafe_package, output)

    assert first == second
    assert malicious not in first
    assert "&lt;script&gt;&quot;&#x27;&amp;&lt;&gt;&lt;/script&gt;" in first
    assert "innerHTML" not in first
    assert "eval(" not in first
    assert "Function(" not in first
    assert "document.write" not in first
    assert written == output
    assert output.read_text(encoding="utf-8") == first
    with pytest.raises(LocalHtmlMapRendererError, match="already exists"):
        write_local_html_map(unsafe_package, output)


def test_renderer_supports_target_only_package() -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        return "52SCB1234512345"

    package = build_real_terrain_launch_area_map_package(
        _result(),
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=wgs,
        projected_to_mgrs=mgrs,
    )

    html = render_local_html_map(replace(package, candidate_polygons=()))

    assert "<circle class=\"target\"" in html
    assert "<polygon " not in html


def test_builder_rejects_feature_parity_errors_before_conversion() -> None:
    def should_not_convert(point: LocalPoint) -> Wgs84MapPoint:
        raise AssertionError("conversion must not run for invalid parity")

    result = _result()
    feature = replace(result.candidate_features[0], x_m=21.0)
    invalid = replace(result, candidate_features=(feature,))

    with pytest.raises(RealTerrainLaunchAreaMapError, match="parity"):
        build_real_terrain_launch_area_map_package(
            invalid,
            RealTerrainLaunchAreaMapConfig(10.0),
            projected_to_wgs84=should_not_convert,
            projected_to_mgrs=lambda point, *, precision: "52SCB1234512345",
        )


def test_visibility_and_selection_reject_excluded_or_hidden_candidates() -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    def mgrs(point: LocalPoint, *, precision: int) -> str:
        return "52SCB1234512345"

    result = _result()
    record = replace(
        result.candidate_records[0],
        state=CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
        candidate_score=None,
        color_class=ColorClass.EXCLUDED,
        within_operation_radius=False,
        distance_3d_m=None,
    )
    feature = replace(
        result.candidate_features[0],
        state=CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
        color_class=ColorClass.EXCLUDED,
        style=style_for_color_class(ColorClass.EXCLUDED),
        overall_score=None,
        shielding_stability_score=None,
        within_operation_radius=False,
        distance_3d_m=None,
    )
    excluded_result = replace(result, candidate_records=(record,), candidate_features=(feature,))
    visible = build_real_terrain_launch_area_map_package(
        excluded_result,
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=wgs,
        projected_to_mgrs=mgrs,
    )
    hidden = build_real_terrain_launch_area_map_package(
        excluded_result,
        RealTerrainLaunchAreaMapConfig(10.0, include_excluded=False),
        projected_to_wgs84=wgs,
        projected_to_mgrs=mgrs,
    )

    assert visible.candidate_polygons[0].selectable is False
    assert "no selectable launch-site candidates were produced" in visible.warnings
    assert hidden.candidate_polygons == ()
    assert "no candidate polygons were included by the map configuration" in hidden.warnings
    with pytest.raises(LaunchSiteSelectionError, match="not selectable"):
        select_launch_site(excluded_result, visible, "candidate-001")
    with pytest.raises(LaunchSiteSelectionError, match="hidden"):
        select_launch_site(excluded_result, hidden, "candidate-001")
