"""Deterministic, self-contained offline HTML/SVG rendering for map packages."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from math import cos, radians
from pathlib import Path

from .coordinate_conversion import Wgs84MapPoint
from .real_terrain_launch_area_map import (
    RealTerrainLaunchAreaMapError,
    RealTerrainLaunchAreaMapPackage,
    validate_real_terrain_launch_area_map_package,
)


class LocalHtmlMapRendererError(ValueError):
    """Raised when a safe local HTML/SVG map cannot be rendered or written."""


@dataclass(frozen=True)
class LocalHtmlMapRenderConfig:
    width_px: int = 1000
    height_px: int = 800
    padding_px: int = 40

    def __post_init__(self) -> None:
        for name, value in (("width_px", self.width_px), ("height_px", self.height_px)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise LocalHtmlMapRendererError(f"{name} must be a positive integer.")
        if isinstance(self.padding_px, bool) or not isinstance(self.padding_px, int) or self.padding_px < 0:
            raise LocalHtmlMapRendererError("padding_px must be a non-negative integer.")
        if 2 * self.padding_px >= self.width_px or 2 * self.padding_px >= self.height_px:
            raise LocalHtmlMapRendererError("padding_px must leave positive drawable dimensions.")


def render_local_html_map(
    package: RealTerrainLaunchAreaMapPackage,
    config: LocalHtmlMapRenderConfig | None = None,
) -> str:
    """Return a deterministic UTF-8-safe HTML document without touching the filesystem."""

    config = LocalHtmlMapRenderConfig() if config is None else config
    try:
        validate_real_terrain_launch_area_map_package(package)
    except RealTerrainLaunchAreaMapError as exc:
        raise LocalHtmlMapRendererError("map package invariant validation failed.") from exc
    points = [
        point
        for polygon in package.candidate_polygons
        for point in polygon.polygon_wgs84[:-1]
    ] + [package.target_marker.position_wgs84]
    transformed = _viewport(points, config)
    point_index = 0
    polygons: list[str] = []
    for polygon in package.candidate_polygons:
        count = len(polygon.polygon_wgs84) - 1
        svg_points = transformed[point_index : point_index + count]
        point_index += count
        svg_points.append(svg_points[0])
        classes = f"candidate {polygon.color_class.value}"
        if polygon.is_selected:
            classes += " package-selected"
        polygons.append(
            '<polygon class="{}" data-candidate-id="{}" data-selectable="{}" points="{}" '
            'fill="{}" stroke="{}" fill-opacity="{}"/>'.format(
                escape(classes, quote=True),
                escape(polygon.candidate_id, quote=True),
                str(polygon.selectable).lower(),
                " ".join(f"{_number(x)},{_number(y)}" for x, y in svg_points),
                polygon.style.fill_hex,
                polygon.style.stroke_hex,
                _number(polygon.style.opacity),
            )
        )
    target_x, target_y = transformed[-1]
    target = '<circle class="target" cx="{}" cy="{}" r="6" fill="#1f77b4" stroke="#ffffff"/>'.format(
        _number(target_x), _number(target_y)
    )
    legend = "".join(
        '<li><span style="background:{};border-color:{};opacity:{}"></span>{}: {}</li>'.format(
            entry.fill_hex,
            entry.stroke_hex,
            _number(entry.opacity),
            escape(entry.label, quote=True),
            entry.count,
        )
        for entry in package.legend
    )
    warnings = "".join(f"<li>{escape(warning, quote=True)}</li>" for warning in package.warnings)
    summary = _definition_rows(
        (
            ("target_mgrs", package.target_marker.target_mgrs),
            ("source_candidate_count", package.summary.source_candidate_count),
            ("rendered_candidate_count", package.summary.rendered_candidate_count),
            ("selectable_candidate_count", package.summary.selectable_candidate_count),
            ("selected_candidate_count", package.summary.selected_candidate_count),
            ("hidden_excluded_count", package.summary.hidden_excluded_count),
        )
    )
    details = "".join(
        '<dl class="candidate-detail-source" data-candidate-id="{}" hidden>{}</dl>'.format(
            escape(polygon.candidate_id, quote=True),
            _definition_rows(tuple(polygon.popup.to_user_facing_dict().items())),
        )
        for polygon in package.candidate_polygons
    )
    title = escape(package.scenario_name, quote=True)
    csp = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="{csp}"><title>{title}</title>
<style>body{{font-family:sans-serif;margin:0;display:grid;grid-template-columns:1fr 320px}}svg{{width:100%;height:auto}}.candidate{{cursor:pointer}}.package-selected{{stroke:#000000;stroke-width:3}}.preview-selectable{{stroke:#000000;stroke-width:2;stroke-dasharray:4 2}}aside{{padding:12px;overflow-wrap:anywhere}}li span{{display:inline-block;width:12px;height:12px;border:1px solid;margin-right:6px}}dt{{font-weight:700}}dd{{margin:0 0 8px}}pre{{white-space:pre-wrap}}</style></head>
<body><svg viewBox="0 0 {config.width_px} {config.height_px}" role="img" aria-label="{title}">{''.join(polygons)}{target}</svg>
<aside><h1>{title}</h1><h2>Summary</h2><dl id="static-summary">{summary}</dl><h2>Candidate detail</h2><p id="preview">preview only</p><pre id="candidate-detail">no candidate previewed</pre><button type="button" id="reset-preview">Reset preview</button><h2>Legend</h2><ul>{legend}</ul><h2>Warnings</h2><ul>{warnings}</ul>{details}</aside>
<script>function resetPreview(){{document.querySelectorAll('.preview-selectable').forEach(function(item){{item.classList.remove('preview-selectable');}});document.getElementById('preview').textContent='preview only';document.getElementById('candidate-detail').textContent='no candidate previewed';}}function candidateDetail(candidateId){{var details=document.querySelectorAll('.candidate-detail-source');for(var index=0;index<details.length;index+=1){{if(details[index].dataset.candidateId===candidateId){{return details[index];}}}}return null;}}document.querySelectorAll('.candidate').forEach(function(node){{node.addEventListener('click',function(){{resetPreview();var detail=candidateDetail(node.dataset.candidateId);if(detail!==null){{document.getElementById('candidate-detail').textContent=detail.textContent;}}if(node.dataset.selectable==='true'){{node.classList.add('preview-selectable');document.getElementById('preview').textContent='preview only';}}else{{document.getElementById('preview').textContent='preview only: selectable=false';}}}});}});document.getElementById('reset-preview').addEventListener('click',resetPreview);</script>
</body></html>
"""


def write_local_html_map(
    package: RealTerrainLaunchAreaMapPackage,
    output_path: str | Path,
    *,
    config: LocalHtmlMapRenderConfig | None = None,
    force: bool = False,
) -> Path:
    """Write an explicitly requested HTML path without opening a browser."""

    output = Path(output_path)
    if output.exists() and not force:
        raise LocalHtmlMapRendererError("output path already exists; use force to overwrite.")
    html_text = render_local_html_map(package, config)
    output.write_text(html_text, encoding="utf-8", newline="\n")
    return output


def _viewport(points: list[Wgs84MapPoint], config: LocalHtmlMapRenderConfig) -> list[tuple[float, float]]:
    longitudes = [point.longitude_deg for point in points]
    latitudes = [point.latitude_deg for point in points]
    if max(longitudes) - min(longitudes) > 180.0:
        raise LocalHtmlMapRendererError("longitude span exceeds 180 degrees.")
    reference_lon = sum(set(longitudes)) / len(set(longitudes))
    reference_lat = sum(set(latitudes)) / len(set(latitudes))
    local = [
        (radians(point.longitude_deg - reference_lon) * cos(radians(reference_lat)), radians(point.latitude_deg - reference_lat))
        for point in points
    ]
    x_values, y_values = [point[0] for point in local], [point[1] for point in local]
    x_min, x_max, y_min, y_max = min(x_values), max(x_values), min(y_values), max(y_values)
    x_span, y_span = x_max - x_min, y_max - y_min
    usable_width, usable_height = config.width_px - 2 * config.padding_px, config.height_px - 2 * config.padding_px
    if x_span == 0 and y_span == 0:
        return [(config.width_px / 2, config.height_px / 2) for _ in local]
    if x_span == 0:
        scale = usable_height / y_span
        return [(config.width_px / 2, config.padding_px + (y_max - y) * scale) for _, y in local]
    if y_span == 0:
        scale = usable_width / x_span
        return [(config.padding_px + (x - x_min) * scale, config.height_px / 2) for x, _ in local]
    scale = min(usable_width / x_span, usable_height / y_span)
    left = config.padding_px + (usable_width - x_span * scale) / 2
    bottom = config.padding_px + (usable_height - y_span * scale) / 2
    return [(left + (x - x_min) * scale, bottom + (y_max - y) * scale) for x, y in local]


def _number(value: float) -> str:
    text = f"{value:.6f}"
    return "0.000000" if text == "-0.000000" else text


def _definition_rows(items: tuple[tuple[object, object], ...]) -> str:
    return "".join(
        "<dt>{}</dt><dd>{}</dd>".format(
            escape(str(key), quote=True),
            escape(_display(value), quote=True),
        )
        for key, value in items
    )


def _display(value: object) -> str:
    if value is None:
        return "not available"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, dict):
        return "; ".join(f"{key}={_display(nested)}" for key, nested in value.items())
    return str(value)
