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
from .terrain_data import TerrainDataError, validate_public_safe_label


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
            if self.selected_candidate_id != self.selected_candidate_id.strip():
                raise RealTerrainLaunchAreaMapError("selected_candidate_id must be stripped.")
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

    def __post_init__(self) -> None:
        _required_text("candidate_id", self.candidate_id)
        _required_text("candidate_cell_mgrs", self.candidate_cell_mgrs)
        if self.candidate_cell_mgrs != self.candidate_cell_mgrs.upper():
            raise RealTerrainLaunchAreaMapError("candidate_cell_mgrs must be uppercase.")
        if self.external_coordinate_format != "MGRS":
            raise RealTerrainLaunchAreaMapError("external_coordinate_format must be MGRS.")
        if self.user_coordinate_field != "candidate_cell_mgrs":
            raise RealTerrainLaunchAreaMapError("user_coordinate_field must be candidate_cell_mgrs.")
        if not isinstance(self.state, CandidateAnalysisState) or not isinstance(self.color_class, ColorClass):
            raise RealTerrainLaunchAreaMapError("popup state and color_class must use approved enums.")
        if not isinstance(self.selectable, bool) or not isinstance(self.within_operation_radius, bool):
            raise RealTerrainLaunchAreaMapError("popup boolean fields must be bool.")
        _required_text("color_name", self.color_name)
        _required_text("candidate_reason", self.candidate_reason)
        _required_text("source_zone_reason", self.source_zone_reason)
        if self.source_zone is not None and not isinstance(self.source_zone, TerrainSourceZone):
            raise RealTerrainLaunchAreaMapError("source_zone must use the approved enum or None.")
        if not isinstance(self.source_zone_state, SourceZoneAvailability):
            raise RealTerrainLaunchAreaMapError("source_zone_state must use the approved enum.")
        if self.source_sensitive is not None and not isinstance(self.source_sensitive, bool):
            raise RealTerrainLaunchAreaMapError("source_sensitive must be bool or None.")
        if self.fresnel_diagnostics is not None and not isinstance(
            self.fresnel_diagnostics, CandidateFresnelDiagnostics
        ):
            raise RealTerrainLaunchAreaMapError("fresnel_diagnostics must be approved diagnostics or None.")
        _optional_finite("overall_score", self.overall_score)
        _optional_finite("shielding_stability_score", self.shielding_stability_score)
        _optional_finite("distance_3d_m", self.distance_3d_m)
        if self.state is CandidateAnalysisState.VALID_SCORED:
            if self.overall_score is None or self.shielding_stability_score is None:
                raise RealTerrainLaunchAreaMapError("valid popup requires score fields.")
            if self.color_class is ColorClass.EXCLUDED:
                raise RealTerrainLaunchAreaMapError("valid popup cannot use excluded color.")
        else:
            if self.selectable or self.color_class is not ColorClass.EXCLUDED:
                raise RealTerrainLaunchAreaMapError("excluded popup state/color/selectability is invalid.")
            if self.overall_score is not None or self.shielding_stability_score is not None:
                raise RealTerrainLaunchAreaMapError("excluded popup scores must be None.")
        if self.selectable:
            if not self.within_operation_radius or self.distance_3d_m is None:
                raise RealTerrainLaunchAreaMapError("selectable popup requires radius and distance.")

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
        _required_text("feature_id", self.feature_id)
        _required_text("candidate_id", self.candidate_id)
        if not isinstance(self.center_wgs84, Wgs84MapPoint) or not all(
            isinstance(point, Wgs84MapPoint) for point in self.polygon_wgs84
        ):
            raise RealTerrainLaunchAreaMapError("candidate polygon points must be WGS84 map points.")
        if not isinstance(self.state, CandidateAnalysisState) or not isinstance(self.color_class, ColorClass):
            raise RealTerrainLaunchAreaMapError("candidate polygon state/color is invalid.")
        if not isinstance(self.style, MapStyle):
            raise RealTerrainLaunchAreaMapError("candidate polygon style must be MapStyle.")
        if not isinstance(self.selectable, bool) or not isinstance(self.is_selected, bool):
            raise RealTerrainLaunchAreaMapError("candidate polygon flags must be bool.")
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
        _required_text("target_mgrs", self.target_mgrs)
        if self.target_mgrs != self.target_mgrs.upper():
            raise RealTerrainLaunchAreaMapError("target_mgrs must be uppercase.")
        if not isinstance(self.position_wgs84, Wgs84MapPoint):
            raise RealTerrainLaunchAreaMapError("target position must be WGS84 map point.")


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

    def __post_init__(self) -> None:
        _required_text("legend key", self.key)
        _required_text("legend label", self.label)
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 0:
            raise RealTerrainLaunchAreaMapError("legend count must be a non-negative integer.")
        try:
            MapStyle(self.key, self.fill_hex, self.stroke_hex, self.opacity)
        except (TypeError, ValueError) as exc:
            raise RealTerrainLaunchAreaMapError("legend style is invalid.") from exc


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

    def __post_init__(self) -> None:
        for name, value in (
            ("source_candidate_count", self.source_candidate_count),
            ("rendered_candidate_count", self.rendered_candidate_count),
            ("selectable_candidate_count", self.selectable_candidate_count),
            ("selected_candidate_count", self.selected_candidate_count),
            ("hidden_excluded_count", self.hidden_excluded_count),
        ):
            _nonnegative_int(name, value)
        if self.source_candidate_count != self.rendered_candidate_count + self.hidden_excluded_count:
            raise RealTerrainLaunchAreaMapError("summary source and rendered counts do not agree.")
        _validate_count_tuple("color_counts", self.color_counts, tuple(color.value for color in ColorClass))
        _validate_count_tuple("state_counts", self.state_counts, tuple(state.value for state in CandidateAnalysisState))
        _validate_count_tuple(
            "source_zone_state_counts",
            self.source_zone_state_counts,
            tuple(state.value for state in SourceZoneAvailability),
        )
        if sum(count for _, count in self.color_counts) != self.rendered_candidate_count:
            raise RealTerrainLaunchAreaMapError("summary rendered color counts do not agree.")
        if sum(count for _, count in self.state_counts) != self.source_candidate_count:
            raise RealTerrainLaunchAreaMapError("summary state counts do not agree.")
        if sum(count for _, count in self.source_zone_state_counts) != self.source_candidate_count:
            raise RealTerrainLaunchAreaMapError("summary source-zone counts do not agree.")


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

    def __post_init__(self) -> None:
        validate_real_terrain_launch_area_map_package(self)

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


def validate_real_terrain_launch_area_map_package(package: RealTerrainLaunchAreaMapPackage) -> None:
    """Reject inconsistent frozen map-package replacements before use."""

    if not isinstance(package, RealTerrainLaunchAreaMapPackage):
        raise RealTerrainLaunchAreaMapError("package must be RealTerrainLaunchAreaMapPackage.")
    _required_text("scenario_name", package.scenario_name)
    try:
        validate_public_safe_label(package.scenario_name)
    except TerrainDataError as exc:
        raise RealTerrainLaunchAreaMapError("scenario_name must be public-safe.") from exc
    if not isinstance(package.target_marker, RealTerrainTargetMarker):
        raise RealTerrainLaunchAreaMapError("package target_marker is invalid.")
    if not isinstance(package.selection_style, MapSelectionStyle):
        raise RealTerrainLaunchAreaMapError("package selection_style is invalid.")
    if not isinstance(package.summary, RealTerrainLaunchAreaMapSummary):
        raise RealTerrainLaunchAreaMapError("package summary is invalid.")
    if not isinstance(package.candidate_polygons, tuple) or not all(
        isinstance(polygon, RealTerrainCandidatePolygon) for polygon in package.candidate_polygons
    ):
        raise RealTerrainLaunchAreaMapError("package candidate polygons are invalid.")
    candidate_ids = [polygon.candidate_id for polygon in package.candidate_polygons]
    feature_ids = [polygon.feature_id for polygon in package.candidate_polygons]
    if len(set(candidate_ids)) != len(candidate_ids) or len(set(feature_ids)) != len(feature_ids):
        raise RealTerrainLaunchAreaMapError("package candidate and feature IDs must be unique.")
    summary = package.summary
    if summary.rendered_candidate_count != len(package.candidate_polygons):
        raise RealTerrainLaunchAreaMapError("package rendered candidate count is inconsistent.")
    if summary.selectable_candidate_count != sum(polygon.selectable for polygon in package.candidate_polygons):
        raise RealTerrainLaunchAreaMapError("package selectable candidate count is inconsistent.")
    if summary.selected_candidate_count != sum(polygon.is_selected for polygon in package.candidate_polygons):
        raise RealTerrainLaunchAreaMapError("package selected candidate count is inconsistent.")
    if package.selected_candidate_id is not None:
        _required_text("selected_candidate_id", package.selected_candidate_id)
        if package.selected_candidate_id != package.selected_candidate_id.strip():
            raise RealTerrainLaunchAreaMapError("selected_candidate_id must be stripped.")
        selected = [
            polygon
            for polygon in package.candidate_polygons
            if polygon.candidate_id == package.selected_candidate_id and polygon.is_selected
        ]
        if len(selected) != 1 or not selected[0].selectable or summary.selected_candidate_count != 1:
            raise RealTerrainLaunchAreaMapError("package selected candidate state is inconsistent.")
    elif summary.selected_candidate_count != 0 or any(
        polygon.is_selected for polygon in package.candidate_polygons
    ):
        raise RealTerrainLaunchAreaMapError("unselected package cannot contain selected polygons.")
    _validate_package_legend(package.legend, summary)
    if not isinstance(package.warnings, tuple) or not all(isinstance(warning, str) for warning in package.warnings):
        raise RealTerrainLaunchAreaMapError("package warnings must be strings.")
    if len(set(package.warnings)) != len(package.warnings):
        raise RealTerrainLaunchAreaMapError("package warnings must not contain duplicates.")


def _validate_package_legend(
    legend: tuple[LaunchAreaLegendEntry, ...],
    summary: RealTerrainLaunchAreaMapSummary,
) -> None:
    expected_keys = tuple(color.value for color in ColorClass) + ("selected", "target")
    if not isinstance(legend, tuple) or not all(isinstance(entry, LaunchAreaLegendEntry) for entry in legend):
        raise RealTerrainLaunchAreaMapError("package legend entries are invalid.")
    if tuple(entry.key for entry in legend) != expected_keys:
        raise RealTerrainLaunchAreaMapError("package legend key order is invalid.")
    expected_styles = {color.value: style_for_color_class(color) for color in ColorClass}
    for entry in legend:
        if entry.key in expected_styles:
            style = expected_styles[entry.key]
            if (entry.fill_hex, entry.stroke_hex, entry.opacity) != (
                style.fill_hex,
                style.stroke_hex,
                style.opacity,
            ):
                raise RealTerrainLaunchAreaMapError("package legend color style is inconsistent.")
            if entry.count != dict(summary.color_counts)[entry.key]:
                raise RealTerrainLaunchAreaMapError("package legend color count is inconsistent.")
    if legend[-2].count != summary.selected_candidate_count:
        raise RealTerrainLaunchAreaMapError("package selected legend count is inconsistent.")
    if legend[-1].count != 1 or (legend[-1].fill_hex, legend[-1].stroke_hex, legend[-1].opacity) != (
        "#1f77b4",
        "#ffffff",
        1.0,
    ):
        raise RealTerrainLaunchAreaMapError("package target legend is inconsistent.")


def build_real_terrain_launch_area_map_package(
    result: RealTerrainLaunchAreaResult,
    config: RealTerrainLaunchAreaMapConfig,
    *,
    projected_to_wgs84: ProjectedToWgs84Converter,
    projected_to_mgrs: ProjectedToMgrsConverter,
) -> RealTerrainLaunchAreaMapPackage:
    """Build an immutable, file-free map package from a verified real result."""

    if not isinstance(config, RealTerrainLaunchAreaMapConfig):
        raise RealTerrainLaunchAreaMapError("config must be RealTerrainLaunchAreaMapConfig.")
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
    if not all(isinstance(record, CandidateAnalysisRecord) for record in records) or not all(
        isinstance(feature, CandidateAnalysisMapFeature) for feature in features
    ):
        raise RealTerrainLaunchAreaMapError("result records and features must use approved types.")
    if len({record.candidate_id for record in records}) != len(records) or any(
        not isinstance(record.candidate_id, str)
        or not record.candidate_id
        or record.candidate_id != record.candidate_id.strip()
        for record in records
    ):
        raise RealTerrainLaunchAreaMapError("record candidate IDs must be non-empty and unique.")
    if len({feature.candidate_id for feature in features}) != len(features) or len(
        {feature.feature_id for feature in features}
    ) != len(features):
        raise RealTerrainLaunchAreaMapError("feature IDs must be non-empty and unique.")
    for record, feature in zip(records, features, strict=True):
        if (
            not isinstance(feature.candidate_id, str)
            or not feature.candidate_id
            or feature.candidate_id != feature.candidate_id.strip()
            or not isinstance(feature.feature_id, str)
            or not feature.feature_id
            or feature.feature_id != feature.feature_id.strip()
        ):
            raise RealTerrainLaunchAreaMapError("feature IDs must be non-empty and unique.")
        if not isinstance(record.candidate_point, LocalPoint):
            raise RealTerrainLaunchAreaMapError("record candidate point must be LocalPoint.")
        _finite_pair("record candidate point", record.candidate_point.x_m, record.candidate_point.y_m)
        _finite_pair("feature coordinates", feature.x_m, feature.y_m)
        if not isinstance(record.state, CandidateAnalysisState) or not isinstance(
            feature.state, CandidateAnalysisState
        ):
            raise RealTerrainLaunchAreaMapError("record and feature state must use approved enums.")
        if not isinstance(record.color_class, ColorClass) or not isinstance(feature.color_class, ColorClass):
            raise RealTerrainLaunchAreaMapError("record and feature color must use approved enums.")
        if not isinstance(record.within_operation_radius, bool) or not isinstance(
            feature.within_operation_radius, bool
        ):
            raise RealTerrainLaunchAreaMapError("record and feature radius state must be bool.")
        if not isinstance(record.reason, str) or not isinstance(feature.reason, str):
            raise RealTerrainLaunchAreaMapError("record and feature reason must be text.")
        if (
            record.source_zone is not None
            and not isinstance(record.source_zone, TerrainSourceZone)
            or feature.source_zone is not None
            and not isinstance(feature.source_zone, TerrainSourceZone)
            or not isinstance(record.source_zone_state, SourceZoneAvailability)
            or not isinstance(feature.source_zone_state, SourceZoneAvailability)
            or record.source_sensitive is not None
            and not isinstance(record.source_sensitive, bool)
            or feature.source_sensitive is not None
            and not isinstance(feature.source_sensitive, bool)
            or not isinstance(record.source_zone_reason, str)
            or not isinstance(feature.source_zone_reason, str)
            or record.fresnel_diagnostics is not None
            and not isinstance(record.fresnel_diagnostics, CandidateFresnelDiagnostics)
            or feature.fresnel_diagnostics is not None
            and not isinstance(feature.fresnel_diagnostics, CandidateFresnelDiagnostics)
        ):
            raise RealTerrainLaunchAreaMapError("record and feature source/diagnostic fields are invalid.")
        if not isinstance(feature.style, MapStyle) or feature.style != style_for_color_class(feature.color_class):
            raise RealTerrainLaunchAreaMapError("record and feature style parity validation failed.")
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
        if record.state is CandidateAnalysisState.VALID_SCORED:
            if score is None or record.color_class is ColorClass.EXCLUDED:
                raise RealTerrainLaunchAreaMapError("valid candidate score/color invariant failed.")
        elif score is not None or record.color_class is not ColorClass.EXCLUDED:
            raise RealTerrainLaunchAreaMapError("excluded candidate score/color invariant failed.")
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


def _required_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise RealTerrainLaunchAreaMapError(f"{name} must be a non-empty stripped string.")


def _optional_finite(name: str, value: object) -> None:
    if value is not None:
        _finite(name, value)


def _finite(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise RealTerrainLaunchAreaMapError(f"{name} must be finite numeric.")


def _finite_pair(name: str, x_value: object, y_value: object) -> None:
    _finite(f"{name} x", x_value)
    _finite(f"{name} y", y_value)


def _nonnegative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RealTerrainLaunchAreaMapError(f"{name} must be a non-negative integer.")


def _validate_count_tuple(name: str, values: object, expected_keys: tuple[str, ...]) -> None:
    if not isinstance(values, tuple) or tuple(key for key, _ in values) != expected_keys:
        raise RealTerrainLaunchAreaMapError(f"{name} keys are not in approved order.")
    for key, count in values:
        if not isinstance(key, str):
            raise RealTerrainLaunchAreaMapError(f"{name} keys must be strings.")
        _nonnegative_int(f"{name} count", count)
