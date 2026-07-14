"""Renderer-neutral map package for Task 035B real-terrain candidate results."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import isfinite
from typing import Any

from .coordinate_conversion import (
    ProjectedToMgrsConverter,
    ProjectedToWgs84Converter,
    Wgs84MapPoint,
)
from .coordinates import LocalPoint
from .fresnel_diagnostics import CandidateFresnelDiagnostics
from .map_outputs import MapStyle, style_for_color_class
from .real_terrain_candidate_analysis import (
    CandidateAnalysisMapFeature,
    CandidateAnalysisRecord,
    CandidateAnalysisState,
    RealTerrainLaunchAreaResult,
    SourceZoneAvailability,
)
from .schemas import ColorClass
from .source_zones import TerrainSourceZone


class RealTerrainLaunchAreaMapError(ValueError):
    """Raised when a real-terrain map package cannot be built safely."""


@dataclass(frozen=True)
class RealTerrainLaunchAreaMapConfig:
    candidate_cell_size_m: float
    selected_candidate_id: str | None = None
    include_excluded: bool = True

    def __post_init__(self) -> None:
        _positive("candidate_cell_size_m", self.candidate_cell_size_m)
        if self.selected_candidate_id is not None:
            if not isinstance(self.selected_candidate_id, str) or not self.selected_candidate_id.strip():
                raise RealTerrainLaunchAreaMapError("selected_candidate_id must be None or non-empty.")
        if not isinstance(self.include_excluded, bool):
            raise RealTerrainLaunchAreaMapError("include_excluded must be bool.")


@dataclass(frozen=True)
class RealTerrainCandidatePopup:
    candidate_id: str
    candidate_cell_mgrs: str
    external_coordinate_format: str
    user_coordinate_field: str
    state: CandidateAnalysisState
    color_class: ColorClass
    color_name: str
    selectable: bool
    overall_score: float | None
    shielding_stability_score: float | None
    distance_3d_m: float | None
    within_operation_radius: bool
    candidate_reason: str
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None

    def to_user_facing_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_cell_mgrs": self.candidate_cell_mgrs,
            "external_coordinate_format": self.external_coordinate_format,
            "user_coordinate_field": self.user_coordinate_field,
            "state": self.state.value,
            "color_class": self.color_class.value,
            "color_name": self.color_name,
            "selectable": self.selectable,
            "overall_score": self.overall_score,
            "shielding_stability_score": self.shielding_stability_score,
            "distance_3d_m": self.distance_3d_m,
            "within_operation_radius": self.within_operation_radius,
            "candidate_reason": self.candidate_reason,
            "source_zone": None if self.source_zone is None else self.source_zone.value,
            "source_zone_state": self.source_zone_state.value,
            "source_sensitive": self.source_sensitive,
            "source_zone_reason": self.source_zone_reason,
            "fresnel_diagnostics": (
                None if self.fresnel_diagnostics is None else self.fresnel_diagnostics.to_flat_dict()
            ),
        }


@dataclass(frozen=True)
class RealTerrainCandidatePolygon:
    feature_id: str
    candidate_id: str
    center_wgs84: Wgs84MapPoint
    polygon_wgs84: tuple[Wgs84MapPoint, ...]
    state: CandidateAnalysisState
    color_class: ColorClass
    style: MapStyle
    selectable: bool
    is_selected: bool
    popup: RealTerrainCandidatePopup

    def __post_init__(self) -> None:
        if len(self.polygon_wgs84) != 5 or self.polygon_wgs84[0] != self.polygon_wgs84[-1]:
            raise RealTerrainLaunchAreaMapError("candidate polygon must be a closed five-point ring.")
        if len(set(self.polygon_wgs84[:-1])) != 4:
            raise RealTerrainLaunchAreaMapError("candidate polygon must have four distinct corners.")
        if self.candidate_id != self.popup.candidate_id:
            raise RealTerrainLaunchAreaMapError("candidate polygon and popup IDs must match.")
        if self.state is not self.popup.state or self.color_class is not self.popup.color_class:
            raise RealTerrainLaunchAreaMapError("candidate polygon and popup state must match.")
        if self.selectable != self.popup.selectable:
            raise RealTerrainLaunchAreaMapError("candidate polygon and popup selectability must match.")
        if self.style != style_for_color_class(self.color_class):
            raise RealTerrainLaunchAreaMapError("candidate polygon style must match color class.")
        if self.is_selected and not self.selectable:
            raise RealTerrainLaunchAreaMapError("selected candidate must be selectable.")


@dataclass(frozen=True)
class RealTerrainTargetMarker:
    marker_id: str
    target_mgrs: str
    position_wgs84: Wgs84MapPoint
    style: MapStyle
    label: str

    def __post_init__(self) -> None:
        if self.marker_id != "target-marker" or self.label != "target":
            raise RealTerrainLaunchAreaMapError("target marker contract is invalid.")
        if self.style != MapStyle("target", "#1f77b4", "#ffffff", 1.0):
            raise RealTerrainLaunchAreaMapError("target marker style is invalid.")


@dataclass(frozen=True)
class MapSelectionStyle:
    stroke_hex: str = "#000000"
    stroke_width: float = 3.0
    opacity: float = 1.0

    def __post_init__(self) -> None:
        if self.stroke_hex != "#000000" or self.stroke_width != 3.0 or self.opacity != 1.0:
            raise RealTerrainLaunchAreaMapError("selection style must use the approved values.")


@dataclass(frozen=True)
class LaunchAreaLegendEntry:
    key: str
    label: str
    fill_hex: str
    stroke_hex: str
    opacity: float
    count: int


@dataclass(frozen=True)
class RealTerrainLaunchAreaMapSummary:
    source_candidate_count: int
    rendered_candidate_count: int
    selectable_candidate_count: int
    selected_candidate_count: int
    hidden_excluded_count: int
    color_counts: tuple[tuple[str, int], ...]
    state_counts: tuple[tuple[str, int], ...]
    source_zone_state_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RealTerrainLaunchAreaMapPackage:
    scenario_name: str
    target_marker: RealTerrainTargetMarker
    candidate_polygons: tuple[RealTerrainCandidatePolygon, ...]
    selected_candidate_id: str | None
    selection_style: MapSelectionStyle
    legend: tuple[LaunchAreaLegendEntry, ...]
    summary: RealTerrainLaunchAreaMapSummary
    warnings: tuple[str, ...]

    def to_user_facing_dict(self) -> dict[str, object]:
        return {
            "scenario_name": self.scenario_name,
            "target": {"target_mgrs": self.target_marker.target_mgrs, "label": self.target_marker.label},
            "selected_candidate_id": self.selected_candidate_id,
            "candidates": [polygon.popup.to_user_facing_dict() for polygon in self.candidate_polygons],
            "summary": {
                "source_candidate_count": self.summary.source_candidate_count,
                "rendered_candidate_count": self.summary.rendered_candidate_count,
                "selectable_candidate_count": self.summary.selectable_candidate_count,
                "selected_candidate_count": self.summary.selected_candidate_count,
                "hidden_excluded_count": self.summary.hidden_excluded_count,
                "color_counts": dict(self.summary.color_counts),
                "state_counts": dict(self.summary.state_counts),
                "source_zone_state_counts": dict(self.summary.source_zone_state_counts),
            },
            "warnings": list(self.warnings),
        }


def build_real_terrain_launch_area_map_package(
    result: RealTerrainLaunchAreaResult,
    config: RealTerrainLaunchAreaMapConfig,
    *,
    projected_to_wgs84: ProjectedToWgs84Converter,
    projected_to_mgrs: ProjectedToMgrsConverter,
) -> RealTerrainLaunchAreaMapPackage:
    """Build an immutable, file-free map package from a verified real result."""

    records, features = _validate_result_parity(result)
    try:
        target_wgs84 = projected_to_wgs84(result.target_point)
        target_mgrs = _mgrs(projected_to_mgrs, result.target_point)
    except Exception as exc:
        raise RealTerrainLaunchAreaMapError("target coordinate conversion failed.") from exc
    included = [
        (record, feature)
        for record, feature in zip(records, features, strict=True)
        if config.include_excluded or record.state is CandidateAnalysisState.VALID_SCORED
    ]
    polygons: list[RealTerrainCandidatePolygon] = []
    for record, feature in included:
        selectable = _selectable(record)
        if config.selected_candidate_id == record.candidate_id and not selectable:
            raise RealTerrainLaunchAreaMapError("selected_candidate_id is not selectable.")
        try:
            center = projected_to_wgs84(record.candidate_point)
            mgrs = _mgrs(projected_to_mgrs, record.candidate_point)
            ring = _convert_ring(feature, config.candidate_cell_size_m, projected_to_wgs84)
        except Exception as exc:
            raise RealTerrainLaunchAreaMapError("candidate coordinate conversion failed.") from exc
        popup = RealTerrainCandidatePopup(
            candidate_id=record.candidate_id,
            candidate_cell_mgrs=mgrs,
            external_coordinate_format="MGRS",
            user_coordinate_field="candidate_cell_mgrs",
            state=record.state,
            color_class=record.color_class,
            color_name=feature.style.color_name,
            selectable=selectable,
            overall_score=None if record.candidate_score is None else record.candidate_score.overall_score,
            shielding_stability_score=(
                None if record.candidate_score is None else record.candidate_score.shielding_stability_score
            ),
            distance_3d_m=record.distance_3d_m,
            within_operation_radius=record.within_operation_radius,
            candidate_reason=record.reason,
            source_zone=record.source_zone,
            source_zone_state=record.source_zone_state,
            source_sensitive=record.source_sensitive,
            source_zone_reason=record.source_zone_reason,
            fresnel_diagnostics=record.fresnel_diagnostics,
        )
        polygons.append(
            RealTerrainCandidatePolygon(
                feature_id=feature.feature_id,
                candidate_id=record.candidate_id,
                center_wgs84=center,
                polygon_wgs84=ring,
                state=record.state,
                color_class=record.color_class,
                style=feature.style,
                selectable=selectable,
                is_selected=config.selected_candidate_id == record.candidate_id,
                popup=popup,
            )
        )
    _validate_selected(config.selected_candidate_id, records, polygons)
    warnings = _warnings(result.warnings, polygons)
    summary = _summary(records, polygons, len(records) - len(included))
    return RealTerrainLaunchAreaMapPackage(
        scenario_name=result.scenario_name,
        target_marker=RealTerrainTargetMarker(
            marker_id="target-marker",
            target_mgrs=target_mgrs,
            position_wgs84=target_wgs84,
            style=MapStyle("target", "#1f77b4", "#ffffff", 1.0),
            label="target",
        ),
        candidate_polygons=tuple(polygons),
        selected_candidate_id=config.selected_candidate_id,
        selection_style=MapSelectionStyle(),
        legend=_legend(polygons, summary),
        summary=summary,
        warnings=warnings,
    )


def _validate_result_parity(
    result: RealTerrainLaunchAreaResult,
) -> tuple[tuple[CandidateAnalysisRecord, ...], tuple[CandidateAnalysisMapFeature, ...]]:
    if not isinstance(result, RealTerrainLaunchAreaResult):
        raise RealTerrainLaunchAreaMapError("result must be RealTerrainLaunchAreaResult.")
    records, features = result.candidate_records, result.candidate_features
    if not records or not features or len(records) != len(features):
        raise RealTerrainLaunchAreaMapError("result records and features must be non-empty and aligned.")
    if len({record.candidate_id for record in records}) != len(records) or any(
        not record.candidate_id for record in records
    ):
        raise RealTerrainLaunchAreaMapError("record candidate IDs must be non-empty and unique.")
    if len({feature.candidate_id for feature in features}) != len(features) or len(
        {feature.feature_id for feature in features}
    ) != len(features):
        raise RealTerrainLaunchAreaMapError("feature IDs must be non-empty and unique.")
    for record, feature in zip(records, features, strict=True):
        if (
            feature.candidate_id != record.candidate_id
            or feature.geometry_crs != "EPSG:5179"
            or feature.x_m != record.candidate_point.x_m
            or feature.y_m != record.candidate_point.y_m
            or feature.state is not record.state
            or feature.color_class is not record.color_class
            or feature.within_operation_radius != record.within_operation_radius
            or feature.reason != record.reason
            or feature.source_zone != record.source_zone
            or feature.source_zone_state is not record.source_zone_state
            or feature.source_sensitive != record.source_sensitive
            or feature.source_zone_reason != record.source_zone_reason
            or feature.fresnel_diagnostics != record.fresnel_diagnostics
            or feature.candidate_cell_mgrs is not None
            or feature.coordinate_display_state != "projected_only"
        ):
            raise RealTerrainLaunchAreaMapError("record and feature parity validation failed.")
        score = record.candidate_score
        if (feature.overall_score, feature.shielding_stability_score) != (
            None if score is None else score.overall_score,
            None if score is None else score.shielding_stability_score,
        ):
            raise RealTerrainLaunchAreaMapError("record and feature score parity validation failed.")
    return records, features


def _convert_ring(
    feature: CandidateAnalysisMapFeature,
    size: float,
    converter: ProjectedToWgs84Converter,
) -> tuple[Wgs84MapPoint, ...]:
    half = size / 2.0
    corners = (
        LocalPoint(feature.x_m - half, feature.y_m - half),
        LocalPoint(feature.x_m + half, feature.y_m - half),
        LocalPoint(feature.x_m + half, feature.y_m + half),
        LocalPoint(feature.x_m - half, feature.y_m + half),
    )
    converted = tuple(converter(point) for point in corners)
    return converted + (converted[0],)


def _mgrs(converter: ProjectedToMgrsConverter, point: LocalPoint) -> str:
    value = converter(point, precision=5)
    if not isinstance(value, str) or not value.strip():
        raise RealTerrainLaunchAreaMapError("MGRS conversion returned empty text.")
    return value.strip().upper()


def _selectable(record: CandidateAnalysisRecord) -> bool:
    return (
        record.state is CandidateAnalysisState.VALID_SCORED
        and record.candidate_score is not None
        and record.color_class is not ColorClass.EXCLUDED
        and record.within_operation_radius
    )


def _validate_selected(
    selected_id: str | None,
    records: tuple[CandidateAnalysisRecord, ...],
    polygons: list[RealTerrainCandidatePolygon],
) -> None:
    if selected_id is None:
        return
    if selected_id not in {record.candidate_id for record in records}:
        raise RealTerrainLaunchAreaMapError("selected_candidate_id was not found.")
    selected = [polygon for polygon in polygons if polygon.candidate_id == selected_id]
    if len(selected) != 1:
        raise RealTerrainLaunchAreaMapError("selected_candidate_id is hidden by map configuration.")
    if not selected[0].selectable or not selected[0].is_selected:
        raise RealTerrainLaunchAreaMapError("selected_candidate_id is not selectable.")


def _warnings(base: tuple[str, ...], polygons: list[RealTerrainCandidatePolygon]) -> tuple[str, ...]:
    values = list(base)
    if not any(polygon.selectable for polygon in polygons):
        values.append("no selectable launch-site candidates were produced")
    if not polygons:
        values.append("no candidate polygons were included by the map configuration")
    return tuple(dict.fromkeys(values))


def _summary(
    records: tuple[CandidateAnalysisRecord, ...],
    polygons: list[RealTerrainCandidatePolygon],
    hidden_excluded_count: int,
) -> RealTerrainLaunchAreaMapSummary:
    colors = Counter(polygon.color_class for polygon in polygons)
    states = Counter(record.state for record in records)
    zones = Counter(record.source_zone_state for record in records)
    return RealTerrainLaunchAreaMapSummary(
        source_candidate_count=len(records),
        rendered_candidate_count=len(polygons),
        selectable_candidate_count=sum(polygon.selectable for polygon in polygons),
        selected_candidate_count=sum(polygon.is_selected for polygon in polygons),
        hidden_excluded_count=hidden_excluded_count,
        color_counts=tuple((color.value, colors[color]) for color in ColorClass),
        state_counts=tuple((state.value, states[state]) for state in CandidateAnalysisState),
        source_zone_state_counts=tuple((state.value, zones[state]) for state in SourceZoneAvailability),
    )


def _legend(
    polygons: list[RealTerrainCandidatePolygon],
    summary: RealTerrainLaunchAreaMapSummary,
) -> tuple[LaunchAreaLegendEntry, ...]:
    styles = {color: style_for_color_class(color) for color in ColorClass}
    entries = [
        LaunchAreaLegendEntry(color.value, color.value, styles[color].fill_hex, styles[color].stroke_hex, styles[color].opacity, dict(summary.color_counts)[color.value])
        for color in ColorClass
    ]
    entries.append(LaunchAreaLegendEntry("selected", "selected", "#000000", "#000000", 1.0, summary.selected_candidate_count))
    entries.append(LaunchAreaLegendEntry("target", "target", "#1f77b4", "#ffffff", 1.0, 1))
    return tuple(entries)


def _positive(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or value <= 0:
        raise RealTerrainLaunchAreaMapError(f"{name} must be positive and finite.")
