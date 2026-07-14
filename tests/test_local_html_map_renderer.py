from __future__ import annotations

from dataclasses import replace

import pytest

from test_real_terrain_launch_area_map import _result

from uav_rf_terrain.coordinate_conversion import Wgs84MapPoint
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.fresnel_diagnostics import CandidateFresnelDiagnostics, DIAGNOSTIC_FIELD_ORDER
from uav_rf_terrain.local_html_map_renderer import (
    LocalHtmlMapRenderConfig,
    LocalHtmlMapRendererError,
    render_local_html_map,
)
from uav_rf_terrain.map_outputs import style_for_color_class
from uav_rf_terrain.real_terrain_candidate_analysis import CandidateAnalysisState
from uav_rf_terrain.real_terrain_launch_area_map import (
    RealTerrainLaunchAreaMapConfig,
    build_real_terrain_launch_area_map_package,
)
from uav_rf_terrain.schemas import ColorClass


def test_renderer_config_requires_positive_dimensions_and_safe_padding() -> None:
    assert LocalHtmlMapRenderConfig() == LocalHtmlMapRenderConfig(width_px=1000, height_px=800, padding_px=40)

    with pytest.raises(LocalHtmlMapRendererError):
        LocalHtmlMapRenderConfig(width_px=True)
    with pytest.raises(LocalHtmlMapRendererError):
        LocalHtmlMapRenderConfig(width_px=80, height_px=80, padding_px=40)


def _wgs(point: LocalPoint) -> Wgs84MapPoint:
    return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)


def _mgrs(point: LocalPoint, *, precision: int) -> str:
    return "52SCB1234512345"


def test_renderer_serializes_static_summary_and_popup_fields_in_contract_order() -> None:
    package = build_real_terrain_launch_area_map_package(
        _result(),
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=_wgs,
        projected_to_mgrs=_mgrs,
    )

    html = render_local_html_map(package)

    assert "target_mgrs" in html
    assert "52SCB1234512345" in html
    assert "source_candidate_count" in html
    assert "hidden_excluded_count" in html
    fields = tuple(package.candidate_polygons[0].popup.to_user_facing_dict())
    positions = [html.index(f"<dt>{field}</dt>") for field in fields]
    assert positions == sorted(positions)
    assert "not available" in html
    assert "candidate-detail-source" in html
    assert "candidateDetail" in html
    script = html.split("<script>", 1)[1]
    assert "candidate-001" not in script
    assert "innerHTML" not in script
    assert "eval(" not in script
    assert "Function(" not in script
    assert "document.write" not in script
    assert "http://" not in html
    assert "https://" not in html


def test_renderer_flattens_fresnel_diagnostics_in_approved_field_order() -> None:
    result = _result()
    diagnostics = CandidateFresnelDiagnostics.no_eligible(average_fresnel_score=90.0)
    record = replace(result.candidate_records[0], fresnel_diagnostics=diagnostics)
    feature = replace(result.candidate_features[0], fresnel_diagnostics=diagnostics)
    package = build_real_terrain_launch_area_map_package(
        replace(result, candidate_records=(record,), candidate_features=(feature,)),
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=_wgs,
        projected_to_mgrs=_mgrs,
    )

    html = render_local_html_map(package)
    positions = [html.index(field) for field in DIAGNOSTIC_FIELD_ORDER]

    assert positions == sorted(positions)
    assert "average_fresnel_score=90.0" in html


def test_renderer_keeps_excluded_detail_visible_but_never_marks_it_preview_selectable() -> None:
    result = _result()
    record = replace(
        result.candidate_records[0],
        state=CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
        candidate_score=None,
        color_class=ColorClass.EXCLUDED,
        within_operation_radius=False,
        distance_3d_m=None,
        reason="excluded detail reason",
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
        reason="excluded detail reason",
    )
    package = build_real_terrain_launch_area_map_package(
        replace(result, candidate_records=(record,), candidate_features=(feature,)),
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=_wgs,
        projected_to_mgrs=_mgrs,
    )

    html = render_local_html_map(package)

    assert "excluded detail reason" in html
    assert "selectable</dt><dd>false" in html
    assert "if(node.dataset.selectable==='true'){node.classList.add('preview-selectable')" in html
    assert "preview only: selectable=false" in html


def test_renderer_rejects_a_package_mutated_outside_frozen_constructor_invariants() -> None:
    package = build_real_terrain_launch_area_map_package(
        _result(),
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=_wgs,
        projected_to_mgrs=_mgrs,
    )
    object.__setattr__(package.summary, "rendered_candidate_count", 0)

    with pytest.raises(LocalHtmlMapRendererError, match="invariant"):
        render_local_html_map(package)
