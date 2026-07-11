"""Pure Python map/UI output data scaffold.

This module converts offline synthetic scenario outputs into rendering-independent
feature records for later UI modules. It produces data only. It does not load
terrain files, build visual layers, call external map libraries, generate vehicle
commands, or validate radio-link quality.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from math import isfinite
import re

from .coordinate_io_policy import (
    EXTERNAL_COORDINATE_FORMAT,
    require_mgrs_external_coordinate_field,
)
from .routing import RouteCandidateType
from .scenario_outputs import (
    SyntheticCandidateRecord,
    SyntheticEndToEndScenario,
    SyntheticRouteOutput,
)
from .schemas import ColorClass
from .source_zones import (
    SourceZoneSummary,
    TerrainSourceZone,
    is_source_sensitive_zone,
    summarize_source_zones,
)

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_CANDIDATE_SOURCE_ZONE_REQUIRED_KEYS = frozenset(
    {
        "candidate_cell_mgrs",
        "external_coordinate_format",
        "user_coordinate_field",
        "source_zone",
        "source_sensitive",
        "source_zone_reason",
    }
)
_BLOCKED_USER_FACING_COORDINATE_KEYS = frozenset(
    {
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
)


class MapOutputError(ValueError):
    """Raised when map output data package inputs are invalid."""


class MapFeatureType(StrEnum):
    """Rendering-independent feature record types."""

    CANDIDATE_CELL = "candidate_cell"
    ROUTE = "route"
    WAYPOINT = "waypoint"


@dataclass(frozen=True)
class MapStyle:
    """Style metadata for later UI modules, not a rendered layer."""

    color_name: str
    fill_hex: str
    stroke_hex: str
    opacity: float = 1.0

    def __post_init__(self) -> None:
        _validate_non_empty_string("color_name", self.color_name)
        _validate_hex_color("fill_hex", self.fill_hex)
        _validate_hex_color("stroke_hex", self.stroke_hex)
        _validate_opacity(self.opacity)


@dataclass(frozen=True)
class CandidateCellMapFeature:
    """Map-ready candidate cell feature record for later UI consumption."""

    feature_id: str
    candidate_id: str
    x_m: float
    y_m: float
    color_class: ColorClass
    style: MapStyle
    overall_score: float
    shielding_stability_score: float
    reason: str
    source_zone: TerrainSourceZone = TerrainSourceZone.ESA_DERIVED
    source_sensitive: bool = False
    source_zone_reason: str = "ESA-derived source zone only."
    candidate_source_zone_map_properties: Mapping[str, str | bool] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        _validate_non_empty_string("feature_id", self.feature_id)
        _validate_non_empty_string("candidate_id", self.candidate_id)
        _validate_finite("x_m", self.x_m)
        _validate_finite("y_m", self.y_m)
        _validate_color_class(self.color_class)
        _validate_map_style(self.style)
        _validate_score("overall_score", self.overall_score)
        _validate_score("shielding_stability_score", self.shielding_stability_score)
        _validate_non_empty_string("reason", self.reason)
        _validate_source_zone(self.source_zone)
        _validate_bool("source_sensitive", self.source_sensitive)
        _validate_non_empty_string("source_zone_reason", self.source_zone_reason)
        _validate_candidate_source_zone_map_properties(
            self.candidate_source_zone_map_properties
        )


@dataclass(frozen=True)
class RouteMapFeature:
    """Map-ready route feature record for later UI consumption."""

    feature_id: str
    route_id: str
    route_type: RouteCandidateType
    point_ids: tuple[str, ...]
    total_distance_m: float
    route_cost: float
    high_risk_cell_count: int
    style: MapStyle
    source_zone_summary: SourceZoneSummary = field(
        default_factory=lambda: summarize_source_zones((TerrainSourceZone.ESA_DERIVED,))
    )
    source_sensitive: bool = False
    source_zone_reason: str = "ESA-derived source zone only."

    def __post_init__(self) -> None:
        _validate_non_empty_string("feature_id", self.feature_id)
        _validate_non_empty_string("route_id", self.route_id)
        if not isinstance(self.route_type, RouteCandidateType):
            raise MapOutputError("route_type must be a RouteCandidateType value.")
        _ensure_point_ids(self.point_ids)
        _validate_non_negative_finite("total_distance_m", self.total_distance_m)
        _validate_non_negative_finite("route_cost", self.route_cost)
        _validate_non_negative_int("high_risk_cell_count", self.high_risk_cell_count)
        _validate_map_style(self.style)
        if not isinstance(self.source_zone_summary, SourceZoneSummary):
            raise MapOutputError("source_zone_summary must be a SourceZoneSummary instance.")
        _validate_bool("source_sensitive", self.source_sensitive)
        _validate_non_empty_string("source_zone_reason", self.source_zone_reason)


@dataclass(frozen=True)
class WaypointMapFeature:
    """Map-ready waypoint feature record for later UI consumption."""

    feature_id: str
    route_id: str
    waypoint_id: str
    sequence_index: int
    x_m: float
    y_m: float
    cumulative_distance_m: float
    flight_agl_m: float
    flight_msl_m: float
    height_difference_from_launch_m: float
    color_class: ColorClass
    style: MapStyle
    source_zone: TerrainSourceZone = TerrainSourceZone.ESA_DERIVED
    source_sensitive: bool = False

    def __post_init__(self) -> None:
        _validate_non_empty_string("feature_id", self.feature_id)
        _validate_non_empty_string("route_id", self.route_id)
        _validate_non_empty_string("waypoint_id", self.waypoint_id)
        _validate_non_negative_int("sequence_index", self.sequence_index)
        _validate_finite("x_m", self.x_m)
        _validate_finite("y_m", self.y_m)
        _validate_non_negative_finite("cumulative_distance_m", self.cumulative_distance_m)
        _validate_non_negative_finite("flight_agl_m", self.flight_agl_m)
        _validate_finite("flight_msl_m", self.flight_msl_m)
        _validate_finite(
            "height_difference_from_launch_m",
            self.height_difference_from_launch_m,
        )
        _validate_color_class(self.color_class)
        _validate_map_style(self.style)
        _validate_source_zone(self.source_zone)
        _validate_bool("source_sensitive", self.source_sensitive)


@dataclass(frozen=True)
class MapOutputPackage:
    """Rendering-independent feature data package for later UI modules."""

    scenario_name: str
    candidate_features: tuple[CandidateCellMapFeature, ...]
    route_features: tuple[RouteMapFeature, ...]
    waypoint_features: tuple[WaypointMapFeature, ...]
    selected_route_id: str
    summary: dict[str, float | int | str | bool]

    def __post_init__(self) -> None:
        _validate_non_empty_string("scenario_name", self.scenario_name)
        _ensure_candidate_features(self.candidate_features)
        _ensure_route_features(self.route_features)
        _ensure_waypoint_features(self.waypoint_features)
        _validate_non_empty_string("selected_route_id", self.selected_route_id)
        route_ids = {feature.route_id for feature in self.route_features}
        if self.selected_route_id not in route_ids:
            raise MapOutputError(
                "selected_route_id must match one route feature route_id."
            )
        if not isinstance(self.summary, dict):
            raise MapOutputError("summary must be a dict.")


def style_for_color_class(color_class: ColorClass) -> MapStyle:
    """Return style metadata for a color class."""

    _validate_color_class(color_class)
    if color_class is ColorClass.GREEN:
        return MapStyle(color_name="green", fill_hex="#2ca02c", stroke_hex="#2ca02c")
    if color_class is ColorClass.YELLOW:
        return MapStyle(color_name="yellow", fill_hex="#ffdd57", stroke_hex="#ffdd57")
    if color_class is ColorClass.ORANGE:
        return MapStyle(color_name="orange", fill_hex="#ff7f0e", stroke_hex="#ff7f0e")
    if color_class is ColorClass.RED:
        return MapStyle(color_name="red", fill_hex="#d62728", stroke_hex="#d62728")
    return MapStyle(
        color_name="excluded",
        fill_hex="#808080",
        stroke_hex="#808080",
        opacity=0.5,
    )


def style_for_route_type(route_type: RouteCandidateType) -> MapStyle:
    """Return style metadata for a route type."""

    if not isinstance(route_type, RouteCandidateType):
        raise MapOutputError("route_type must be a RouteCandidateType value.")
    if route_type is RouteCandidateType.SHIELDING_MINIMUM:
        return MapStyle(
            color_name="shielding_minimum",
            fill_hex="#1f77b4",
            stroke_hex="#1f77b4",
        )
    if route_type is RouteCandidateType.DISTANCE_SHIELDING_BALANCED:
        return MapStyle(
            color_name="distance_shielding_balanced",
            fill_hex="#9467bd",
            stroke_hex="#9467bd",
        )
    return MapStyle(
        color_name="detour_stability",
        fill_hex="#8c564b",
        stroke_hex="#8c564b",
    )


def build_candidate_cell_map_features(
    candidates: Sequence[SyntheticCandidateRecord],
) -> tuple[CandidateCellMapFeature, ...]:
    """Convert synthetic candidate records into map-ready candidate features."""

    resolved_candidates = _ensure_synthetic_candidates(candidates)
    features: list[CandidateCellMapFeature] = []
    for index, candidate in enumerate(resolved_candidates):
        source_sensitive = is_source_sensitive_zone(candidate.source_zone)
        source_summary = summarize_source_zones((candidate.source_zone,))
        features.append(
            CandidateCellMapFeature(
                feature_id=f"candidate-feature-{index:03d}",
                candidate_id=candidate.candidate_id,
                x_m=index * 500.0,
                y_m=0.0,
                color_class=candidate.color_class,
                style=style_for_color_class(candidate.color_class),
                overall_score=candidate.candidate_score.overall_score,
                shielding_stability_score=(
                    candidate.candidate_score.shielding_stability_score
                ),
                reason=candidate.reason,
                source_zone=candidate.source_zone,
                source_sensitive=source_sensitive,
                source_zone_reason=source_summary.reason,
            )
        )
    return tuple(features)


def attach_candidate_source_zone_map_properties(
    candidate_features: Sequence[CandidateCellMapFeature],
    metadata_by_cell_id: Mapping[str, Mapping[str, str | bool]],
    *,
    require_all: bool = True,
) -> tuple[CandidateCellMapFeature, ...]:
    """Attach optional Task 021B metadata to candidate features by candidate id."""

    resolved_features = _ensure_candidate_feature_sequence(candidate_features)
    if not isinstance(metadata_by_cell_id, Mapping):
        raise MapOutputError("metadata_by_cell_id must be a mapping.")
    if not isinstance(require_all, bool):
        raise MapOutputError("require_all must be a bool.")

    attached: list[CandidateCellMapFeature] = []
    for feature in resolved_features:
        if feature.candidate_id not in metadata_by_cell_id:
            if require_all:
                raise MapOutputError(
                    "missing candidate source-zone map metadata for "
                    f"candidate_id={feature.candidate_id}."
                )
            attached.append(feature)
            continue
        properties = metadata_by_cell_id[feature.candidate_id]
        _validate_candidate_source_zone_map_properties(properties)
        attached.append(
            replace(
                feature,
                candidate_source_zone_map_properties=dict(properties),
            )
        )
    return tuple(attached)


def build_route_map_features(
    routes: Sequence[SyntheticRouteOutput],
) -> tuple[RouteMapFeature, ...]:
    """Convert synthetic route outputs into map-ready route features."""

    resolved_routes = _ensure_synthetic_routes(routes)
    features: list[RouteMapFeature] = []
    for index, route_output in enumerate(resolved_routes):
        route_candidate = route_output.route_candidate
        point_ids = tuple(
            waypoint.waypoint_id
            for waypoint in route_output.waypoint_report.waypoints
        )
        source_zone_summary = route_candidate.source_zone_summary
        features.append(
            RouteMapFeature(
                feature_id=f"route-feature-{index:03d}",
                route_id=route_candidate.route_id,
                route_type=route_candidate.route_type,
                point_ids=point_ids,
                total_distance_m=route_candidate.total_distance_m,
                route_cost=route_candidate.route_cost,
                high_risk_cell_count=route_candidate.high_risk_cell_count,
                style=style_for_route_type(route_candidate.route_type),
                source_zone_summary=source_zone_summary,
                source_sensitive=source_zone_summary.source_sensitive,
                source_zone_reason=source_zone_summary.reason,
            )
        )
    return tuple(features)


def build_waypoint_map_features(
    routes: Sequence[SyntheticRouteOutput],
) -> tuple[WaypointMapFeature, ...]:
    """Convert synthetic route waypoint reports into map-ready waypoint features."""

    resolved_routes = _ensure_synthetic_routes(routes)
    features: list[WaypointMapFeature] = []
    feature_index = 0
    for route_output in resolved_routes:
        for waypoint in route_output.waypoint_report.waypoints:
            features.append(
                WaypointMapFeature(
                    feature_id=f"waypoint-feature-{feature_index:03d}",
                    route_id=route_output.route_candidate.route_id,
                    waypoint_id=waypoint.waypoint_id,
                    sequence_index=waypoint.sequence_index,
                    x_m=waypoint.x_m,
                    y_m=waypoint.y_m,
                    cumulative_distance_m=waypoint.cumulative_distance_m,
                    flight_agl_m=waypoint.flight_agl_m,
                    flight_msl_m=waypoint.flight_msl_m,
                    height_difference_from_launch_m=(
                        waypoint.height_difference_from_launch_m
                    ),
                    color_class=waypoint.color_class,
                    style=style_for_color_class(waypoint.color_class),
                    source_zone=waypoint.source_zone,
                    source_sensitive=is_source_sensitive_zone(waypoint.source_zone),
                )
            )
            feature_index += 1
    return tuple(features)


def build_map_output_package(
    scenario: SyntheticEndToEndScenario,
    candidate_source_zone_metadata_by_cell_id: (
        Mapping[str, Mapping[str, str | bool]] | None
    ) = None,
) -> MapOutputPackage:
    """Convert a synthetic scenario into a backward-compatible map-ready package."""

    if not isinstance(scenario, SyntheticEndToEndScenario):
        raise MapOutputError("scenario must be a SyntheticEndToEndScenario instance.")
    candidate_features = build_candidate_cell_map_features(scenario.candidates)
    if candidate_source_zone_metadata_by_cell_id is not None:
        candidate_features = attach_candidate_source_zone_map_properties(
            candidate_features,
            candidate_source_zone_metadata_by_cell_id,
        )
    route_features = build_route_map_features(scenario.routes)
    waypoint_features = build_waypoint_map_features(scenario.routes)
    provisional = MapOutputPackage(
        scenario_name=scenario.scenario_name,
        candidate_features=candidate_features,
        route_features=route_features,
        waypoint_features=waypoint_features,
        selected_route_id=scenario.selected_route_id,
        summary={},
    )
    return MapOutputPackage(
        scenario_name=scenario.scenario_name,
        candidate_features=candidate_features,
        route_features=route_features,
        waypoint_features=waypoint_features,
        selected_route_id=scenario.selected_route_id,
        summary=summarize_map_output_package(provisional),
    )


def summarize_map_output_package(
    package: MapOutputPackage,
) -> dict[str, float | int | str | bool]:
    """Summarize map-ready feature counts for reporting and future UI cards."""

    if not isinstance(package, MapOutputPackage):
        raise MapOutputError("package must be a MapOutputPackage instance.")
    candidate_source_summary = summarize_source_zones(
        tuple(feature.source_zone for feature in package.candidate_features)
    )
    waypoint_source_summary = summarize_source_zones(
        tuple(feature.source_zone for feature in package.waypoint_features)
    )
    attached_metadata_count = sum(
        1
        for feature in package.candidate_features
        if feature.candidate_source_zone_map_properties
    )
    missing_metadata_count = len(package.candidate_features) - attached_metadata_count
    metadata_attached = attached_metadata_count > 0
    return {
        "scenario_name": package.scenario_name,
        "candidate_feature_count": len(package.candidate_features),
        "route_feature_count": len(package.route_features),
        "waypoint_feature_count": len(package.waypoint_features),
        "selected_route_id": package.selected_route_id,
        "green_candidate_feature_count": _count_candidate_features(
            package.candidate_features,
            ColorClass.GREEN,
        ),
        "yellow_candidate_feature_count": _count_candidate_features(
            package.candidate_features,
            ColorClass.YELLOW,
        ),
        "orange_candidate_feature_count": _count_candidate_features(
            package.candidate_features,
            ColorClass.ORANGE,
        ),
        "red_candidate_feature_count": _count_candidate_features(
            package.candidate_features,
            ColorClass.RED,
        ),
        "excluded_candidate_feature_count": _count_candidate_features(
            package.candidate_features,
            ColorClass.EXCLUDED,
        ),
        "esa_candidate_feature_count": candidate_source_summary.esa_derived_count,
        "wms_gap_filled_candidate_feature_count": (
            candidate_source_summary.wms_gap_filled_count
        ),
        "dem_only_fallback_candidate_feature_count": (
            candidate_source_summary.dem_only_fallback_count
        ),
        "mixed_boundary_candidate_feature_count": (
            candidate_source_summary.mixed_boundary_count
        ),
        "source_sensitive_candidate_feature_count": sum(
            1 for feature in package.candidate_features if feature.source_sensitive
        ),
        "source_sensitive_route_feature_count": sum(
            1 for feature in package.route_features if feature.source_sensitive
        ),
        "source_sensitive_waypoint_feature_count": sum(
            1 for feature in package.waypoint_features if feature.source_sensitive
        ),
        "dem_only_fallback_waypoint_feature_count": (
            waypoint_source_summary.dem_only_fallback_count
        ),
        "mixed_boundary_waypoint_feature_count": (
            waypoint_source_summary.mixed_boundary_count
        ),
        "red_waypoint_feature_count": _count_waypoint_features(
            package.waypoint_features,
            ColorClass.RED,
        ),
        "orange_waypoint_feature_count": _count_waypoint_features(
            package.waypoint_features,
            ColorClass.ORANGE,
        ),
        "candidate_source_zone_map_properties_feature_count": (
            attached_metadata_count
        ),
        "candidate_source_zone_map_properties_missing_feature_count": (
            missing_metadata_count
        ),
        "candidate_source_zone_map_properties_external_coordinate_format": (
            EXTERNAL_COORDINATE_FORMAT if metadata_attached else "not_attached"
        ),
        "candidate_source_zone_map_properties_user_coordinate_field": (
            "candidate_cell_mgrs" if metadata_attached else "not_attached"
        ),
    }


def format_map_output_summary(package: MapOutputPackage) -> str:
    """Return a readable map-ready data summary string."""

    if not isinstance(package, MapOutputPackage):
        raise MapOutputError("package must be a MapOutputPackage instance.")
    summary = package.summary or summarize_map_output_package(package)
    return "\n".join(
        (
            "Synthetic map/UI output data package summary",
            f"Scenario: {summary['scenario_name']}",
            f"Candidate features: {int(summary['candidate_feature_count'])}",
            f"Route features: {int(summary['route_feature_count'])}",
            f"Waypoint features: {int(summary['waypoint_feature_count'])}",
            "Candidate color counts: "
            f"green={int(summary['green_candidate_feature_count'])}, "
            f"yellow={int(summary['yellow_candidate_feature_count'])}, "
            f"orange={int(summary['orange_candidate_feature_count'])}, "
            f"red={int(summary['red_candidate_feature_count'])}, "
            f"excluded={int(summary['excluded_candidate_feature_count'])}",
            "Candidate source-zone map metadata: "
            f"attached={int(summary['candidate_source_zone_map_properties_feature_count'])}, "
            f"missing={int(summary['candidate_source_zone_map_properties_missing_feature_count'])}",
            "Source-sensitive candidates: "
            f"{int(summary['source_sensitive_candidate_feature_count'])}",
            "Source-sensitive routes: "
            f"{int(summary['source_sensitive_route_feature_count'])}",
            f"Selected route id: {summary['selected_route_id']}",
            "This is map-ready data, not a rendered map.",
        )
    )


def _validate_candidate_source_zone_map_properties(
    properties: Mapping[str, str | bool],
) -> None:
    if not isinstance(properties, Mapping):
        raise MapOutputError(
            "candidate_source_zone_map_properties must be a mapping."
        )
    if not properties:
        return
    property_keys = set(properties)
    blocked_keys = property_keys.intersection(
        _BLOCKED_USER_FACING_COORDINATE_KEYS
    )
    if blocked_keys:
        raise MapOutputError(
            "candidate source-zone map properties must not contain internal "
            f"coordinate keys: {sorted(blocked_keys)}."
        )
    missing_keys = _CANDIDATE_SOURCE_ZONE_REQUIRED_KEYS.difference(property_keys)
    if missing_keys:
        raise MapOutputError(
            "candidate source-zone map properties missing required keys: "
            f"{sorted(missing_keys)}."
        )
    require_mgrs_external_coordinate_field("candidate_cell_mgrs")
    _validate_non_empty_string(
        "candidate_cell_mgrs",
        properties["candidate_cell_mgrs"],
    )
    if properties["external_coordinate_format"] != EXTERNAL_COORDINATE_FORMAT:
        raise MapOutputError("external_coordinate_format must be MGRS.")
    if properties["user_coordinate_field"] != "candidate_cell_mgrs":
        raise MapOutputError(
            "user_coordinate_field must be candidate_cell_mgrs."
        )
    _validate_non_empty_string("source_zone", properties["source_zone"])
    _validate_bool("source_sensitive", properties["source_sensitive"])
    _validate_non_empty_string(
        "source_zone_reason",
        properties["source_zone_reason"],
    )
    if "internal_debug_available" in properties:
        _validate_bool(
            "internal_debug_available",
            properties["internal_debug_available"],
        )


def _count_candidate_features(
    features: Sequence[CandidateCellMapFeature],
    color_class: ColorClass,
) -> int:
    return sum(1 for feature in features if feature.color_class is color_class)


def _count_waypoint_features(
    features: Sequence[WaypointMapFeature],
    color_class: ColorClass,
) -> int:
    return sum(1 for feature in features if feature.color_class is color_class)


def _ensure_synthetic_candidates(
    candidates: Sequence[SyntheticCandidateRecord],
) -> tuple[SyntheticCandidateRecord, ...]:
    if not candidates:
        raise MapOutputError("candidates must not be empty.")
    resolved_candidates = tuple(candidates)
    for candidate in resolved_candidates:
        if not isinstance(candidate, SyntheticCandidateRecord):
            raise MapOutputError(
                "all candidates must be SyntheticCandidateRecord instances."
            )
    return resolved_candidates


def _ensure_synthetic_routes(
    routes: Sequence[SyntheticRouteOutput],
) -> tuple[SyntheticRouteOutput, ...]:
    if not routes:
        raise MapOutputError("routes must not be empty.")
    resolved_routes = tuple(routes)
    for route in resolved_routes:
        if not isinstance(route, SyntheticRouteOutput):
            raise MapOutputError(
                "all routes must be SyntheticRouteOutput instances."
            )
    return resolved_routes


def _ensure_point_ids(point_ids: tuple[str, ...]) -> None:
    if not point_ids:
        raise MapOutputError("point_ids must not be empty.")
    for point_id in point_ids:
        _validate_non_empty_string("point_id", point_id)


def _ensure_candidate_feature_sequence(
    features: Sequence[CandidateCellMapFeature],
) -> tuple[CandidateCellMapFeature, ...]:
    if not features:
        raise MapOutputError("candidate_features must not be empty.")
    resolved = tuple(features)
    for feature in resolved:
        if not isinstance(feature, CandidateCellMapFeature):
            raise MapOutputError(
                "all candidate_features must be CandidateCellMapFeature instances."
            )
    return resolved


def _ensure_candidate_features(
    features: tuple[CandidateCellMapFeature, ...],
) -> None:
    _ensure_candidate_feature_sequence(features)


def _ensure_route_features(features: tuple[RouteMapFeature, ...]) -> None:
    if not features:
        raise MapOutputError("route_features must not be empty.")
    for feature in features:
        if not isinstance(feature, RouteMapFeature):
            raise MapOutputError(
                "all route_features must be RouteMapFeature instances."
            )


def _ensure_waypoint_features(features: tuple[WaypointMapFeature, ...]) -> None:
    if not features:
        raise MapOutputError("waypoint_features must not be empty.")
    for feature in features:
        if not isinstance(feature, WaypointMapFeature):
            raise MapOutputError(
                "all waypoint_features must be WaypointMapFeature instances."
            )


def _validate_map_style(style: MapStyle) -> None:
    if not isinstance(style, MapStyle):
        raise MapOutputError("style must be a MapStyle instance.")


def _validate_color_class(color_class: ColorClass) -> None:
    if not isinstance(color_class, ColorClass):
        raise MapOutputError("color_class must be a ColorClass value.")


def _validate_source_zone(source_zone: TerrainSourceZone) -> None:
    if not isinstance(source_zone, TerrainSourceZone):
        raise MapOutputError("source_zone must be a TerrainSourceZone value.")


def _validate_bool(field_name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise MapOutputError(f"{field_name} must be a bool.")


def _validate_non_empty_string(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MapOutputError(f"{field_name} must be a non-empty string.")


def _validate_hex_color(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not _HEX_COLOR_RE.match(value):
        raise MapOutputError(f"{field_name} must use #RRGGBB hex format.")


def _validate_opacity(value: float) -> None:
    if not isfinite(value):
        raise MapOutputError("opacity must be finite.")
    if value < 0.0 or value > 1.0:
        raise MapOutputError("opacity must be within [0, 1].")


def _validate_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise MapOutputError(f"{field_name} must be finite.")


def _validate_non_negative_finite(field_name: str, value: float) -> None:
    _validate_finite(field_name, value)
    if value < 0.0:
        raise MapOutputError(f"{field_name} must be non-negative.")


def _validate_score(field_name: str, value: float) -> None:
    _validate_finite(field_name, value)
    if value < 0.0 or value > 100.0:
        raise MapOutputError(f"{field_name} must be within [0, 100].")


def _validate_non_negative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MapOutputError(f"{field_name} must be an integer.")
    if value < 0:
        raise MapOutputError(f"{field_name} must be non-negative.")
