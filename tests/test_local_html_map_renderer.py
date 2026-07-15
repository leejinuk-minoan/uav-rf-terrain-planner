from __future__ import annotations

from dataclasses import replace
from html.parser import HTMLParser

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


class _CandidateDetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.details: dict[str, str] = {}
        self._candidate_id: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "pre" and attributes.get("class") == "candidate-detail-source":
            self._candidate_id = attributes["data-candidate-id"]
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._candidate_id is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self._candidate_id is not None:
            self.details[self._candidate_id] = "".join(self._parts)
            self._candidate_id = None
            self._parts = []


def _detail_text_by_candidate(html: str) -> dict[str, str]:
    parser = _CandidateDetailParser()
    parser.feed(html)
    return parser.details


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
    detail_lines = _detail_text_by_candidate(html)["candidate-001"].splitlines()
    assert [line.split(": ", 1)[0] for line in detail_lines] == list(fields)
    assert "not available" in html
    assert "candidate-detail-source" in html
    assert "candidateDetailText" in html
    script = html.split("<script>", 1)[1]
    assert "candidate-001" not in script
    assert "innerHTML" not in script
    assert "eval(" not in script
    assert "Function(" not in script
    assert "document.write" not in script
    assert "http://" not in html
    assert "https://" not in html


def test_renderer_serializes_click_detail_as_deterministic_lines_with_fresnel_diagnostics() -> None:
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
    detail_lines = _detail_text_by_candidate(html)["candidate-001"].splitlines()
    fresnel_line = next(line for line in detail_lines if line.startswith("fresnel_diagnostics: "))

    assert detail_lines[0] == "candidate_id: candidate-001"
    assert detail_lines[7] == "selectable: true"
    assert "source_zone: not available" in detail_lines
    assert "source_sensitive: not available" in detail_lines
    assert "average_fresnel_score=90.0" in fresnel_line
    positions = [fresnel_line.index(field) for field in DIAGNOSTIC_FIELD_ORDER]
    assert positions == sorted(positions)


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
    excluded_lines = _detail_text_by_candidate(html)["candidate-001"].splitlines()
    assert excluded_lines[7] == "selectable: false"
    assert "overall_score: not available" in excluded_lines
    assert "distance_3d_m: not available" in excluded_lines
    assert "candidate_reason: excluded detail reason" in excluded_lines
    assert "if(node.dataset.selectable==='true'){node.classList.add('preview-selectable')" in html
    assert "preview only: selectable=false" in html
    assert "textContent='no candidate previewed'" in html


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
