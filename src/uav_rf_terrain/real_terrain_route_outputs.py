"""Immutable output contracts for selected-launch-site terrain route analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .coordinates import LocalPoint
from .fresnel_diagnostics import CandidateFresnelDiagnostics
from .real_terrain_candidate_analysis import SourceZoneAvailability
from .schemas import ColorClass
from .source_zones import SourceZoneSummary, TerrainSourceZone


class RealTerrainRouteOutputError(ValueError):
    """Raised when a route configuration or output record is invalid."""


class RouteMode(str, Enum):
    """Fixed route objectives in deterministic output order."""

    SHIELDING_MINIMUM = "shielding_minimum"
    DISTANCE_SHIELDING_BALANCED = "distance_shielding_balanced"
    DETOUR_STABILITY = "detour_stability"


class RouteNodeState(str, Enum):
    """Explicit graph-node states; only ``valid_scored`` is traversable."""

    VALID_SCORED = "valid_scored"
    OUTSIDE_OPERATION_RADIUS = "outside_operation_radius"
    OUTSIDE_RASTER_EXTENT = "outside_raster_extent"
    TERRAIN_NODATA = "terrain_nodata"
    INVALID_SURFACE = "invalid_surface"
    PROFILE_UNAVAILABLE = "profile_unavailable"
    ANALYSIS_INVALID = "analysis_invalid"


RealTerrainRouteNodeState = RouteNodeState


@dataclass(frozen=True)
class RouteModeCostPolicy:
    shielding_weight: float
    distance_weight: float
    high_risk_multiplier: float


_MODE_COST_POLICIES: dict[RouteMode, RouteModeCostPolicy] = {
    RouteMode.SHIELDING_MINIMUM: RouteModeCostPolicy(0.90, 0.10, 1.0),
    RouteMode.DISTANCE_SHIELDING_BALANCED: RouteModeCostPolicy(0.70, 0.30, 1.0),
    RouteMode.DETOUR_STABILITY: RouteModeCostPolicy(0.85, 0.15, 2.0),
}


def route_mode_cost_policy(mode: RouteMode) -> RouteModeCostPolicy:
    """Return the reviewed immutable cost policy for one route mode."""

    if not isinstance(mode, RouteMode):
        raise RealTerrainRouteOutputError("mode must be a RouteMode.")
    return _MODE_COST_POLICIES[mode]


@dataclass(frozen=True)
class RealTerrainRouteConfig:
    """Bounded configuration for one selected-launch-site route analysis."""

    graph_spacing_m: float
    profile_spacing_m: float
    allowed_flight_agl_m: float
    frequency_hz: float
    route_margin_m: float
    connectivity: int = 8
    max_graph_nodes: int = 10_000
    max_graph_edges: int = 80_000
    max_profile_samples_per_node: int = 512
    max_total_profile_samples: int = 2_000_000
    max_path_expansions_per_search: int = 100_000
    max_total_path_expansions: int = 300_000
    overlap_penalty_weight: float = 100.0
    maximum_shared_edge_ratio: float = 0.80
    mission_id: str = "real-terrain-route"

    def __post_init__(self) -> None:
        for name, value in (
            ("graph_spacing_m", self.graph_spacing_m),
            ("profile_spacing_m", self.profile_spacing_m),
            ("allowed_flight_agl_m", self.allowed_flight_agl_m),
            ("frequency_hz", self.frequency_hz),
            ("route_margin_m", self.route_margin_m),
            ("overlap_penalty_weight", self.overlap_penalty_weight),
        ):
            _positive_finite(name, value)
        if self.connectivity != 8 or isinstance(self.connectivity, bool):
            raise RealTerrainRouteOutputError("connectivity is locked to 8.")
        for name, value in (
            ("max_graph_nodes", self.max_graph_nodes),
            ("max_graph_edges", self.max_graph_edges),
            ("max_profile_samples_per_node", self.max_profile_samples_per_node),
            ("max_total_profile_samples", self.max_total_profile_samples),
            ("max_path_expansions_per_search", self.max_path_expansions_per_search),
            ("max_total_path_expansions", self.max_total_path_expansions),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise RealTerrainRouteOutputError(f"{name} must be a positive integer.")
        if (
            isinstance(self.maximum_shared_edge_ratio, bool)
            or not isinstance(self.maximum_shared_edge_ratio, (int, float))
            or not isfinite(self.maximum_shared_edge_ratio)
            or not 0.0 <= self.maximum_shared_edge_ratio <= 1.0
        ):
            raise RealTerrainRouteOutputError(
                "maximum_shared_edge_ratio must be finite within [0, 1]."
            )
        if not isinstance(self.mission_id, str) or not self.mission_id.strip():
            raise RealTerrainRouteOutputError("mission_id must be non-empty.")


@dataclass(frozen=True)
class RealTerrainRoutePathPoint:
    """One user-facing converted path point without internal projected coordinates."""

    sequence_index: int
    mgrs: str
    flight_msl_m: float

    def __post_init__(self) -> None:
        if self.sequence_index < 0:
            raise RealTerrainRouteOutputError("sequence_index must be non-negative.")
        if not isinstance(self.mgrs, str) or not self.mgrs.strip() or self.mgrs != self.mgrs.upper():
            raise RealTerrainRouteOutputError("mgrs must be non-empty uppercase text.")
        _finite("flight_msl_m", self.flight_msl_m)


@dataclass(frozen=True)
class RealTerrainRouteNode:
    """Internal graph node with explicit terrain-analysis state."""

    node_id: str
    row: int
    column: int
    projected_point: LocalPoint
    node_mgrs: str | None
    terrain_msl_m: float | None
    surface_msl_m: float | None
    flight_agl_m: float
    flight_msl_m: float | None
    distance_3d_from_launch_m: float | None
    within_operation_radius: bool
    state: RouteNodeState
    traversable: bool
    reason: str
    shielding_stability_score: float | None
    overall_score: float | None
    color_class: ColorClass
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None

    def __post_init__(self) -> None:
        if (
            not self.node_id
            or isinstance(self.row, bool)
            or isinstance(self.column, bool)
            or not isinstance(self.row, int)
            or not isinstance(self.column, int)
            or self.row < 0
            or self.column < 0
        ):
            raise RealTerrainRouteOutputError("route node identity is invalid.")
        if not isinstance(self.projected_point, LocalPoint):
            raise RealTerrainRouteOutputError("projected_point must be LocalPoint.")
        _non_negative_finite("flight_agl_m", self.flight_agl_m)
        if (
            not isinstance(self.state, RouteNodeState)
            or not isinstance(self.color_class, ColorClass)
            or not isinstance(self.source_zone_state, SourceZoneAvailability)
            or (self.source_zone is not None and not isinstance(self.source_zone, TerrainSourceZone))
            or (self.source_sensitive is not None and not isinstance(self.source_sensitive, bool))
            or (
                self.fresnel_diagnostics is not None
                and not isinstance(self.fresnel_diagnostics, CandidateFresnelDiagnostics)
            )
        ):
            raise RealTerrainRouteOutputError("route node state or color is invalid.")
        if not isinstance(self.within_operation_radius, bool) or not isinstance(self.traversable, bool):
            raise RealTerrainRouteOutputError("route node booleans are invalid.")
        if not self.reason.strip() or not self.source_zone_reason.strip():
            raise RealTerrainRouteOutputError("route node reason must be non-empty.")
        if self.node_mgrs is not None and (not self.node_mgrs.strip() or self.node_mgrs != self.node_mgrs.upper()):
            raise RealTerrainRouteOutputError("node_mgrs must be uppercase when present.")
        for name, value in (
            ("terrain_msl_m", self.terrain_msl_m),
            ("surface_msl_m", self.surface_msl_m),
            ("flight_msl_m", self.flight_msl_m),
            ("distance_3d_from_launch_m", self.distance_3d_from_launch_m),
            ("shielding_stability_score", self.shielding_stability_score),
            ("overall_score", self.overall_score),
        ):
            if value is not None:
                _finite(name, value)
        valid = self.state is RouteNodeState.VALID_SCORED
        if valid != self.traversable:
            raise RealTerrainRouteOutputError("valid_scored and traversable must agree.")
        if valid:
            if (
                self.color_class is ColorClass.EXCLUDED
                or not self.within_operation_radius
                or self.flight_msl_m is None
                or self.distance_3d_from_launch_m is None
                or self.shielding_stability_score is None
                or self.overall_score is None
                or self.terrain_msl_m is None
                or self.surface_msl_m is None
            ):
                raise RealTerrainRouteOutputError("valid route node is incomplete.")
            if self.surface_msl_m < self.terrain_msl_m:
                raise RealTerrainRouteOutputError("valid route node surface must not be below terrain.")
            if self.surface_msl_m > self.flight_msl_m:
                raise RealTerrainRouteOutputError("valid route node surface must not exceed flight MSL.")
            if abs(self.flight_msl_m - (self.terrain_msl_m + self.flight_agl_m)) > 1e-9:
                raise RealTerrainRouteOutputError("valid route node flight MSL must equal terrain plus AGL.")
            _score("shielding_stability_score", self.shielding_stability_score)
            _score("overall_score", self.overall_score)
        elif (
            self.color_class is not ColorClass.EXCLUDED
            or self.shielding_stability_score is not None
            or self.overall_score is not None
        ):
            raise RealTerrainRouteOutputError("excluded route node must not invent scores.")
        if self.state is RouteNodeState.OUTSIDE_OPERATION_RADIUS and self.within_operation_radius:
            raise RealTerrainRouteOutputError("outside-radius route node must have radius flag false.")


@dataclass(frozen=True)
class RealTerrainRouteEdge:
    """One directed traversable airborne graph edge and its cost components."""

    from_node_id: str
    to_node_id: str
    distance_3d_m: float
    shielding_risk_cost: float
    distance_cost: float
    high_risk_penalty: float

    def __post_init__(self) -> None:
        if not self.from_node_id or not self.to_node_id:
            raise RealTerrainRouteOutputError("route edge node IDs must be non-empty.")
        for name, value in (
            ("distance_3d_m", self.distance_3d_m),
            ("shielding_risk_cost", self.shielding_risk_cost),
            ("distance_cost", self.distance_cost),
            ("high_risk_penalty", self.high_risk_penalty),
        ):
            _finite(name, value)
            if value < 0.0:
                raise RealTerrainRouteOutputError(f"{name} must be non-negative.")


@dataclass(frozen=True)
class WaypointHandoffPoint:
    """Unsampled route point retained for a later waypoint-report task."""

    point_id: str
    projected_point: LocalPoint
    point_mgrs: str
    cumulative_distance_3d_m: float
    terrain_msl_m: float
    surface_msl_m: float
    flight_agl_m: float
    flight_msl_m: float
    color_class: ColorClass
    shielding_stability_score: float
    overall_score: float
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str

    def __post_init__(self) -> None:
        if (
            not self.point_id
            or not isinstance(self.projected_point, LocalPoint)
            or not self.point_mgrs.strip()
            or self.point_mgrs != self.point_mgrs.upper()
            or self.point_mgrs != self.point_mgrs.strip()
        ):
            raise RealTerrainRouteOutputError("waypoint handoff identity is invalid.")
        for name, value in (
            ("cumulative_distance_3d_m", self.cumulative_distance_3d_m),
            ("terrain_msl_m", self.terrain_msl_m),
            ("surface_msl_m", self.surface_msl_m),
            ("flight_agl_m", self.flight_agl_m),
            ("flight_msl_m", self.flight_msl_m),
            ("shielding_stability_score", self.shielding_stability_score),
            ("overall_score", self.overall_score),
        ):
            _finite(name, value)
        _non_negative_finite("cumulative_distance_3d_m", self.cumulative_distance_3d_m)
        _non_negative_finite("flight_agl_m", self.flight_agl_m)
        if self.surface_msl_m < self.terrain_msl_m:
            raise RealTerrainRouteOutputError("waypoint handoff surface must not be below terrain.")
        if abs(self.flight_msl_m - (self.terrain_msl_m + self.flight_agl_m)) > 1e-9:
            raise RealTerrainRouteOutputError("waypoint handoff flight MSL must equal terrain plus AGL.")
        if self.color_class is ColorClass.EXCLUDED:
            raise RealTerrainRouteOutputError("waypoint handoff color must not be excluded.")
        _score("shielding_stability_score", self.shielding_stability_score)
        _score("overall_score", self.overall_score)
        if (
            not isinstance(self.color_class, ColorClass)
            or not isinstance(self.source_zone_state, SourceZoneAvailability)
            or (self.source_zone is not None and not isinstance(self.source_zone, TerrainSourceZone))
            or (self.source_sensitive is not None and not isinstance(self.source_sensitive, bool))
            or not self.source_zone_reason.strip()
        ):
            raise RealTerrainRouteOutputError("waypoint handoff source or color metadata is invalid.")


@dataclass(frozen=True)
class RealTerrainRouteSummary:
    graph_node_count: int
    graph_edge_count: int
    traversable_node_count: int
    route_count: int

    def __post_init__(self) -> None:
        for value in (
            self.graph_node_count,
            self.graph_edge_count,
            self.traversable_node_count,
            self.route_count,
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise RealTerrainRouteOutputError("route summary counts must be non-negative integers.")


@dataclass(frozen=True)
class RealTerrainRouteCandidate:
    """Immutable MGRS-facing route candidate for later map or waypoint handoff."""

    route_id: str
    mode: RouteMode
    path: tuple[RealTerrainRoutePathPoint, ...]
    total_cost: float
    total_distance_3d_m: float
    mean_shielding_stability_score: float
    minimum_shielding_stability_score: float
    warnings: tuple[str, ...] = ()
    ordered_node_ids: tuple[str, ...] = ()
    ordered_projected_points: tuple[LocalPoint, ...] = ()
    orange_count: int = 0
    red_count: int = 0
    high_risk_count: int = 0
    shared_edge_ratios: tuple[float, ...] = ()
    reason: str = "deterministic terrain-derived route candidate"
    source_zone_summary: SourceZoneSummary | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, RouteMode):
            raise RealTerrainRouteOutputError("mode must be a RouteMode.")
        if not isinstance(self.route_id, str) or not self.route_id.strip():
            raise RealTerrainRouteOutputError("route_id must be non-empty.")
        if self.route_id != f"route-{self.mode.value}":
            raise RealTerrainRouteOutputError("route_id must be derived from its route mode.")
        if not self.path:
            raise RealTerrainRouteOutputError("path must not be empty.")
        if tuple(point.sequence_index for point in self.path) != tuple(range(len(self.path))):
            raise RealTerrainRouteOutputError("path sequence indexes must start at zero.")
        for name, value in (
            ("total_cost", self.total_cost),
            ("total_distance_3d_m", self.total_distance_3d_m),
            ("mean_shielding_stability_score", self.mean_shielding_stability_score),
            ("minimum_shielding_stability_score", self.minimum_shielding_stability_score),
        ):
            _finite(name, value)
        if not self.ordered_node_ids or len(self.ordered_node_ids) != len(self.path):
            raise RealTerrainRouteOutputError("ordered_node_ids must match path length.")
        if not self.ordered_projected_points or len(self.ordered_projected_points) != len(self.path):
            raise RealTerrainRouteOutputError("ordered_projected_points must match path length.")
        if len(set(self.ordered_node_ids)) != len(self.ordered_node_ids):
            raise RealTerrainRouteOutputError("route candidate node IDs must be unique.")
        if any(not isinstance(point, LocalPoint) for point in self.ordered_projected_points):
            raise RealTerrainRouteOutputError("route candidate projected points must be LocalPoint.")
        if self.total_cost < 0.0 or self.total_distance_3d_m < 0.0:
            raise RealTerrainRouteOutputError("route cost and distance must be non-negative.")
        _score("mean_shielding_stability_score", self.mean_shielding_stability_score)
        _score("minimum_shielding_stability_score", self.minimum_shielding_stability_score)
        if self.minimum_shielding_stability_score > self.mean_shielding_stability_score:
            raise RealTerrainRouteOutputError("route minimum shielding score must not exceed mean.")
        for count in (self.orange_count, self.red_count, self.high_risk_count):
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise RealTerrainRouteOutputError("route risk counts must be non-negative integers.")
        if self.high_risk_count != self.orange_count + self.red_count:
            raise RealTerrainRouteOutputError("high_risk_count must equal orange plus red counts.")
        if not self.reason.strip():
            raise RealTerrainRouteOutputError("route reason must be non-empty.")
        if len(set(self.warnings)) != len(self.warnings):
            raise RealTerrainRouteOutputError("route candidate warnings must be unique.")
        for ratio in self.shared_edge_ratios:
            if not isfinite(ratio) or not 0.0 <= ratio <= 1.0:
                raise RealTerrainRouteOutputError("shared edge ratios must be within [0, 1].")

    @property
    def route_type(self) -> RouteMode:
        """Compatibility name for the route objective."""

        return self.mode


@dataclass(frozen=True)
class RealTerrainRouteResult:
    """Top-level immutable route output retained for future waypoint handoff."""

    scenario_name: str
    mission_id: str
    selected_candidate_id: str
    launch_site_mgrs: str
    target_mgrs: str
    route_candidates: tuple[RealTerrainRouteCandidate, ...]
    warnings: tuple[str, ...]
    config: RealTerrainRouteConfig | None = None
    terrain_metadata: object | None = None
    graph_nodes: tuple[RealTerrainRouteNode, ...] = ()
    graph_edges: tuple[RealTerrainRouteEdge, ...] = ()
    summary: RealTerrainRouteSummary | None = None
    waypoint_handoffs: tuple[tuple[WaypointHandoffPoint, ...], ...] = ()
    launch_ground_msl_m: float | None = None
    snapped_launch_node_id: str | None = None
    snapped_target_node_id: str | None = None
    snapped_launch_node_mgrs: str | None = None
    snapped_target_node_mgrs: str | None = None
    launch_snap_distance_m: float | None = None
    target_snap_distance_m: float | None = None
    path_semantics: str = "snapped_graph_path"

    def __post_init__(self) -> None:
        for name, value in (
            ("scenario_name", self.scenario_name),
            ("mission_id", self.mission_id),
            ("selected_candidate_id", self.selected_candidate_id),
            ("launch_site_mgrs", self.launch_site_mgrs),
            ("target_mgrs", self.target_mgrs),
        ):
            if not isinstance(value, str) or not value.strip():
                raise RealTerrainRouteOutputError(f"{name} must be non-empty.")
        if self.launch_site_mgrs != self.launch_site_mgrs.upper() or self.target_mgrs != self.target_mgrs.upper():
            raise RealTerrainRouteOutputError("MGRS output must be uppercase.")
        if not self.route_candidates:
            raise RealTerrainRouteOutputError("route_candidates must not be empty.")
        route_order = {mode: index for index, mode in enumerate(RouteMode)}
        modes = tuple(candidate.mode for candidate in self.route_candidates)
        if len(set(modes)) != len(modes) or tuple(sorted(modes, key=route_order.__getitem__)) != modes:
            raise RealTerrainRouteOutputError("route candidates must retain fixed mode order.")
        if len({candidate.route_id for candidate in self.route_candidates}) != len(self.route_candidates):
            raise RealTerrainRouteOutputError("route candidate IDs must be unique.")
        if self.config is not None and not isinstance(self.config, RealTerrainRouteConfig):
            raise RealTerrainRouteOutputError("config must be RealTerrainRouteConfig when present.")
        if self.summary is not None and self.summary.route_count != len(self.route_candidates):
            raise RealTerrainRouteOutputError("route summary count must match candidates.")
        if self.waypoint_handoffs and len(self.waypoint_handoffs) != len(self.route_candidates):
            raise RealTerrainRouteOutputError("waypoint handoffs must match route candidates.")
        if self.launch_ground_msl_m is not None:
            _finite("launch_ground_msl_m", self.launch_ground_msl_m)
        if len(set(self.warnings)) != len(self.warnings):
            raise RealTerrainRouteOutputError("result warnings must be unique.")
        if self.graph_nodes:
            _validate_result_graph_contract(self)
        if self.path_semantics != "snapped_graph_path":
            raise RealTerrainRouteOutputError("path_semantics must describe snapped graph paths.")

    def to_public_dict(self) -> dict[str, object]:
        """Return a user-facing dictionary without projected, raster, or WGS84 fields."""

        return {
            "scenario_name": self.scenario_name,
            "mission_id": self.mission_id,
            "selected_candidate_id": self.selected_candidate_id,
            "launch_site_mgrs": self.launch_site_mgrs,
            "target_mgrs": self.target_mgrs,
            "routes": tuple(
                {
                    "route_id": candidate.route_id,
                    "mode": candidate.mode.value,
                    "path": tuple(
                        {"sequence_index": point.sequence_index, "mgrs": point.mgrs, "flight_msl_m": point.flight_msl_m}
                        for point in candidate.path
                    ),
                    "total_cost": candidate.total_cost,
                    "total_distance_3d_m": candidate.total_distance_3d_m,
                    "mean_shielding_stability_score": candidate.mean_shielding_stability_score,
                    "minimum_shielding_stability_score": candidate.minimum_shielding_stability_score,
                    "orange_count": candidate.orange_count,
                    "red_count": candidate.red_count,
                    "high_risk_count": candidate.high_risk_count,
                    "shared_edge_ratios": candidate.shared_edge_ratios,
                    "reason": candidate.reason,
                    "warnings": candidate.warnings,
                }
                for candidate in self.route_candidates
            ),
            "warnings": self.warnings,
            "path_semantics": self.path_semantics,
            "snapped_launch_node_id": self.snapped_launch_node_id,
            "snapped_target_node_id": self.snapped_target_node_id,
            "snapped_launch_node_mgrs": self.snapped_launch_node_mgrs,
            "snapped_target_node_mgrs": self.snapped_target_node_mgrs,
            "launch_snap_distance_m": self.launch_snap_distance_m,
            "target_snap_distance_m": self.target_snap_distance_m,
        }


def _finite(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise RealTerrainRouteOutputError(f"{name} must be finite.")


def _positive_finite(name: str, value: object) -> None:
    _finite(name, value)
    if not isinstance(value, (int, float)) or value <= 0.0:
        raise RealTerrainRouteOutputError(f"{name} must be positive.")


def _non_negative_finite(name: str, value: object) -> None:
    _finite(name, value)
    if not isinstance(value, (int, float)) or value < 0.0:
        raise RealTerrainRouteOutputError(f"{name} must be non-negative.")


def _score(name: str, value: float) -> None:
    _finite(name, value)
    if value < 0.0 or value > 100.0:
        raise RealTerrainRouteOutputError(f"{name} must be within [0, 100].")


def _validate_result_graph_contract(result: RealTerrainRouteResult) -> None:
    nodes_by_id = {node.node_id: node for node in result.graph_nodes}
    if len(nodes_by_id) != len(result.graph_nodes):
        raise RealTerrainRouteOutputError("result graph node IDs must be unique.")
    if result.summary is None or (
        result.summary.graph_node_count != len(result.graph_nodes)
        or result.summary.graph_edge_count != len(result.graph_edges)
        or result.summary.traversable_node_count
        != sum(node.traversable for node in result.graph_nodes)
    ):
        raise RealTerrainRouteOutputError("result graph summary does not match graph records.")
    for edge in result.graph_edges:
        source = nodes_by_id.get(edge.from_node_id)
        destination = nodes_by_id.get(edge.to_node_id)
        if source is None or destination is None or not source.traversable or not destination.traversable:
            raise RealTerrainRouteOutputError("result edge must reference traversable graph nodes.")
    if any(
        node.source_zone is not None
        or node.source_zone_state is not SourceZoneAvailability.NOT_REQUESTED
        or node.source_sensitive is not None
        for node in result.graph_nodes
    ):
        raise RealTerrainRouteOutputError("route-node source-zone metadata must remain not requested in this MVP.")
    if not result.waypoint_handoffs or len(result.waypoint_handoffs) != len(result.route_candidates):
        raise RealTerrainRouteOutputError("result waypoint handoffs must match route candidates.")
    for index, candidate in enumerate(result.route_candidates):
        if len(candidate.shared_edge_ratios) != index:
            raise RealTerrainRouteOutputError("shared edge ratios must follow prior-route order.")
        path_nodes = tuple(nodes_by_id.get(node_id) for node_id in candidate.ordered_node_ids)
        if any(node is None for node in path_nodes) or any(
            node.projected_point != point
            for node, point in zip(path_nodes, candidate.ordered_projected_points)
            if node is not None
        ):
            raise RealTerrainRouteOutputError("candidate path must match graph node references.")
        handoff = result.waypoint_handoffs[index]
        if len(handoff) != len(candidate.path):
            raise RealTerrainRouteOutputError("waypoint handoff length must match candidate path.")
        if handoff and abs(handoff[-1].cumulative_distance_3d_m - candidate.total_distance_3d_m) > 1e-9:
            raise RealTerrainRouteOutputError("final waypoint cumulative distance must match route distance.")
        for sequence_index, (path_point, handoff_point) in enumerate(zip(candidate.path, handoff)):
            if (
                handoff_point.point_mgrs != path_point.mgrs
                or handoff_point.projected_point != candidate.ordered_projected_points[sequence_index]
                or handoff_point.point_id
                != f"route-{candidate.mode.value}-handoff-{sequence_index:03d}"
                or handoff_point.source_zone is not None
                or handoff_point.source_zone_state is not SourceZoneAvailability.NOT_REQUESTED
                or handoff_point.source_sensitive is not None
            ):
                raise RealTerrainRouteOutputError("waypoint handoff must match candidate path MGRS and point parity.")
    _validate_snap_metadata(result, nodes_by_id)


def _validate_snap_metadata(
    result: RealTerrainRouteResult,
    nodes_by_id: dict[str, RealTerrainRouteNode],
) -> None:
    values = (
        result.snapped_launch_node_id,
        result.snapped_target_node_id,
        result.snapped_launch_node_mgrs,
        result.snapped_target_node_mgrs,
        result.launch_snap_distance_m,
        result.target_snap_distance_m,
    )
    if any(value is not None for value in values):
        if any(value is None for value in values):
            raise RealTerrainRouteOutputError("snap metadata must be complete when present.")
        launch_node = nodes_by_id.get(result.snapped_launch_node_id or "")
        target_node = nodes_by_id.get(result.snapped_target_node_id or "")
        if launch_node is None or target_node is None:
            raise RealTerrainRouteOutputError("snap metadata must reference graph nodes.")
        for name, distance in (
            ("launch_snap_distance_m", result.launch_snap_distance_m),
            ("target_snap_distance_m", result.target_snap_distance_m),
        ):
            _non_negative_finite(name, distance)
        for mgrs in (result.snapped_launch_node_mgrs, result.snapped_target_node_mgrs):
            if not isinstance(mgrs, str) or not mgrs.strip() or mgrs != mgrs.upper():
                raise RealTerrainRouteOutputError("snapped MGRS metadata must be uppercase text.")
