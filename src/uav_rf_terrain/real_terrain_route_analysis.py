"""Selected-launch-site real-terrain route recommendation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from .classification import ClassificationError, classify_candidate_score
from .coordinate_conversion import CoordinateConversionError, ProjectedToMgrsConverter
from .coordinates import LocalPoint, distance_2d_m, distance_3d_m
from .fresnel import FresnelAnalysisError, analyze_dsm_fresnel
from .fresnel_diagnostics import CandidateFresnelDiagnostics, candidate_fresnel_diagnostics_from_analysis
from .launch_site_selection import SelectedLaunchSiteRecord
from .los import LineOfSightError, analyze_dsm_los
from .real_terrain_candidate_analysis import (
    CandidateAnalysisRecord,
    CandidateAnalysisState,
    RealTerrainLaunchAreaResult,
    SourceZoneAvailability,
    _resolve_session,
)
from .real_terrain_route_outputs import (
    RealTerrainRouteCandidate,
    RealTerrainRouteConfig,
    RealTerrainRouteEdge,
    RealTerrainRouteNode,
    RealTerrainRoutePathPoint,
    RealTerrainRouteResult,
    RealTerrainRouteSummary,
    RouteMode,
    RouteNodeState,
    WaypointHandoffPoint,
    route_mode_cost_policy,
)
from .route_graph import (
    RouteGraphBounds,
    RouteGraphError,
    RouteGraphNode,
    RouteGraphTopology,
    build_route_graph_topology,
    build_route_grid,
    snap_point_to_route_node,
)
from .route_pathfinding import (
    DijkstraPath,
    DirectedRouteEdge,
    RouteExpansionLimitError,
    RouteNoPathError,
    RoutePathfindingInputError,
    RoutePathfindingInvariantError,
    RoutePathfindingError,
    dijkstra_shortest_path,
)
from .schemas import ColorClass
from .scoring import CandidateScore, ScoringError, compute_candidate_score
from .profile import TerrainProfileError
from .terrain_data import (
    TerrainDataAdapter,
    TerrainDataError,
    TerrainNoDataError,
    TerrainPointOutsideError,
    validate_public_safe_label,
)


class RealTerrainRouteAnalysisError(ValueError):
    """Raised when selected-launch-site route analysis cannot complete safely."""


class _Node:
    def __init__(
        self,
        graph: RouteGraphNode,
        state: RouteNodeState,
        reason: str,
        flight_msl_m: float | None = None,
        distance_3d_m: float | None = None,
        score: CandidateScore | None = None,
        color_class: ColorClass = ColorClass.EXCLUDED,
        terrain_msl_m: float | None = None,
        surface_msl_m: float | None = None,
        fresnel_diagnostics: CandidateFresnelDiagnostics | None = None,
        within_operation_radius: bool = False,
    ) -> None:
        self.graph = graph
        self.state = state
        self.reason = reason
        self.flight_msl_m = flight_msl_m
        self.distance_3d_m = distance_3d_m
        self.score = score
        self.color_class = color_class
        self.terrain_msl_m = terrain_msl_m
        self.surface_msl_m = surface_msl_m
        self.fresnel_diagnostics = fresnel_diagnostics
        self.within_operation_radius = within_operation_radius

    @property
    def traversable(self) -> bool:
        return (
            self.state is RouteNodeState.VALID_SCORED
            and self.score is not None
            and self.color_class is not ColorClass.EXCLUDED
            and self.flight_msl_m is not None
            and self.distance_3d_m is not None
        )


class _PathCandidate:
    def __init__(
        self,
        mode: RouteMode,
        path: DijkstraPath,
        shared_edge_ratios: tuple[float, ...],
    ) -> None:
        self.mode = mode
        self.path = path
        self.shared_edge_ratios = shared_edge_ratios


@dataclass(frozen=True)
class _BaseRouteEdge:
    """Mode-independent topology and cost components for one directed edge."""

    from_node_id: str
    to_node_id: str
    distance_3d_m: float
    shielding_risk_cost: float
    distance_cost: float
    high_risk_penalty: float


def validate_selected_launch_site_for_route(
    selected: SelectedLaunchSiteRecord,
    source_result: RealTerrainLaunchAreaResult,
    config: RealTerrainRouteConfig,
) -> CandidateAnalysisRecord:
    """Validate immutable selection/source parity before terrain session access."""

    if not isinstance(selected, SelectedLaunchSiteRecord):
        raise RealTerrainRouteAnalysisError("selected launch site must be SelectedLaunchSiteRecord.")
    if not isinstance(source_result, RealTerrainLaunchAreaResult):
        raise RealTerrainRouteAnalysisError("source result must be RealTerrainLaunchAreaResult.")
    if not isinstance(config, RealTerrainRouteConfig):
        raise RealTerrainRouteAnalysisError("config must be RealTerrainRouteConfig.")
    try:
        validate_public_safe_label(source_result.scenario_name)
        validate_public_safe_label(config.mission_id)
    except TerrainDataError as exc:
        raise RealTerrainRouteAnalysisError("scenario or mission label is not public-safe.") from exc
    mission_values = (
        source_result.operation_radius_m,
        source_result.allowed_agl_m,
        source_result.frequency_hz,
        source_result.profile_sample_spacing_m,
    )
    if any(value is None for value in mission_values):
        raise RealTerrainRouteAnalysisError("source result does not retain route mission authority.")
    if (
        source_result.allowed_agl_m != config.allowed_flight_agl_m
        or source_result.frequency_hz != config.frequency_hz
        or source_result.profile_sample_spacing_m != config.profile_spacing_m
    ):
        raise RealTerrainRouteAnalysisError("route config does not match source mission authority.")
    record = next(
        (item for item in source_result.candidate_records if item.candidate_id == selected.candidate_id),
        None,
    )
    if record is None:
        raise RealTerrainRouteAnalysisError("selected candidate is not present in source result.")
    if (
        record.candidate_point != selected.projected_point
        or record.state is not CandidateAnalysisState.VALID_SCORED
        or record.candidate_score is None
        or record.color_class is ColorClass.EXCLUDED
        or not record.within_operation_radius
    ):
        raise RealTerrainRouteAnalysisError("selected candidate does not satisfy source selection invariants.")
    score = record.candidate_score
    if (
        record.color_class is not selected.color_class
        or score.overall_score != selected.overall_score
        or score.shielding_stability_score != selected.shielding_stability_score
        or record.distance_3d_m != selected.distance_3d_m
        or record.reason != selected.candidate_reason
        or record.source_zone != selected.source_zone
        or record.source_zone_state is not selected.source_zone_state
        or record.source_sensitive is not selected.source_sensitive
        or record.source_zone_reason != selected.source_zone_reason
        or record.fresnel_diagnostics != selected.fresnel_diagnostics
    ):
        raise RealTerrainRouteAnalysisError("selected launch site does not match source candidate parity.")
    if source_result.operation_radius_m != score.operating_radius_m:
        raise RealTerrainRouteAnalysisError("source operation radius does not match selected candidate.")
    return record


def analyze_selected_launch_site_routes(
    adapter: TerrainDataAdapter,
    selected: SelectedLaunchSiteRecord,
    source_result: RealTerrainLaunchAreaResult,
    config: RealTerrainRouteConfig,
    *,
    projected_to_mgrs: ProjectedToMgrsConverter,
) -> RealTerrainRouteResult:
    """Produce up to three bounded, deterministic MGRS-facing route candidates."""

    record = validate_selected_launch_site_for_route(selected, source_result, config)
    selected_score = record.candidate_score
    if selected_score is None:
        raise RealTerrainRouteAnalysisError("selected candidate score is unavailable.")
    if not callable(projected_to_mgrs):
        raise RealTerrainRouteAnalysisError("projected_to_mgrs must be callable.")
    mgrs_cache: dict[LocalPoint, str] = {}
    try:
        selected_mgrs = _mgrs_for_point(selected.projected_point, projected_to_mgrs, mgrs_cache)
    except Exception as exc:
        raise RealTerrainRouteAnalysisError("route MGRS conversion failed.") from exc
    if selected_mgrs != selected.launch_site_mgrs:
        raise RealTerrainRouteAnalysisError("selected launch MGRS does not match projected conversion.")
    _validate_pre_session_guards(source_result, selected, selected_score, config)
    try:
        with _resolve_session(adapter) as session:
            metadata = session.metadata
            if metadata.dem.crs != "EPSG:5179" or metadata.dsm.crs != "EPSG:5179":
                raise RealTerrainRouteAnalysisError("terrain dataset CRS must be EPSG:5179.")
            if metadata.dem.bounds != metadata.dsm.bounds:
                raise RealTerrainRouteAnalysisError("DEM and DSM bounds must match.")
            launch_sample = session.sample_point(selected.projected_point)
            target_sample = session.sample_point(source_result.target_point)
            launch_flight_msl = launch_sample.dem_msl + config.allowed_flight_agl_m
            target_flight_msl = target_sample.dem_msl + config.allowed_flight_agl_m
            if launch_sample.dsm_msl > launch_flight_msl or target_sample.dsm_msl > target_flight_msl:
                raise RealTerrainRouteAnalysisError("launch or target surface is above flight MSL.")
            target_distance_3d_m = distance_3d_m(
                LocalPoint(
                    selected.projected_point.x_m,
                    selected.projected_point.y_m,
                    launch_flight_msl,
                ),
                LocalPoint(
                    source_result.target_point.x_m,
                    source_result.target_point.y_m,
                    target_flight_msl,
                ),
            )
            if target_distance_3d_m > selected_score.operating_radius_m + 1e-12:
                raise RealTerrainRouteAnalysisError("target flight point is outside operation radius.")
            bounds = _route_bounds(
                launch=selected.projected_point,
                target=source_result.target_point,
                operation_radius_m=selected_score.operating_radius_m,
                route_margin_m=config.route_margin_m,
                raster_bounds=metadata.dem.bounds,
            )
            graph_nodes = build_route_grid(bounds, graph_spacing_m=config.graph_spacing_m)
            if len(graph_nodes) > config.max_graph_nodes:
                raise RealTerrainRouteAnalysisError("graph node guard exceeded.")
            profile_estimate = sum(
                max(1, ceil(distance_2d_m(selected.projected_point, node.point) / config.profile_spacing_m)) + 1
                for node in graph_nodes
            )
            if any(
                max(1, ceil(distance_2d_m(selected.projected_point, node.point) / config.profile_spacing_m)) + 1
                > config.max_profile_samples_per_node
                for node in graph_nodes
            ):
                raise RealTerrainRouteAnalysisError("profile sample-per-node guard exceeded.")
            if profile_estimate > config.max_total_profile_samples:
                raise RealTerrainRouteAnalysisError("total profile sample guard exceeded.")
            analyzed_nodes = tuple(
                _analyze_node(
                    session,
                    node,
                    launch_point=selected.projected_point,
                    launch_flight_msl=launch_flight_msl,
                    target_radius_m=selected_score.operating_radius_m,
                    config=config,
                    scenario_name=source_result.scenario_name,
                )
                for node in graph_nodes
            )
    except RealTerrainRouteAnalysisError:
        raise
    except (TerrainDataError, RouteGraphError) as exc:
        raise RealTerrainRouteAnalysisError("terrain route analysis session failed.") from exc

    start = snap_point_to_route_node(graph_nodes, selected.projected_point, graph_spacing_m=config.graph_spacing_m)
    target = snap_point_to_route_node(graph_nodes, source_result.target_point, graph_spacing_m=config.graph_spacing_m)
    by_id = {node.graph.node_id: node for node in analyzed_nodes}
    if not by_id[start.node_id].traversable or not by_id[target.node_id].traversable:
        raise RealTerrainRouteAnalysisError("snapped launch or target node is not traversable.")
    topology = build_route_graph_topology(graph_nodes)
    base_edges = _build_base_edges(analyzed_nodes, topology, config)
    if len(base_edges) > config.max_graph_edges:
        raise RealTerrainRouteAnalysisError("graph edge guard exceeded.")
    candidates, warnings = _route_candidates(
        base_edges,
        by_id,
        start.node_id,
        target.node_id,
        config,
    )
    try:
        target_mgrs = _mgrs_for_point(source_result.target_point, projected_to_mgrs, mgrs_cache)
        snapped_launch_mgrs = _mgrs_for_point(start.point, projected_to_mgrs, mgrs_cache)
        snapped_target_mgrs = _mgrs_for_point(target.point, projected_to_mgrs, mgrs_cache)
        output_candidates = tuple(
            _to_output_candidate(candidate, by_id, mgrs_cache, projected_to_mgrs) for candidate in candidates
        )
        handoffs = tuple(_waypoint_handoff(candidate, by_id, mgrs_cache, projected_to_mgrs) for candidate in candidates)
    except Exception as exc:
        raise RealTerrainRouteAnalysisError("route MGRS conversion failed.") from exc
    node_outputs = tuple(_node_output(node, config) for node in analyzed_nodes)
    edge_outputs = tuple(_edge_output(edge) for edge in base_edges)
    return RealTerrainRouteResult(
        scenario_name=source_result.scenario_name,
        mission_id=config.mission_id,
        selected_candidate_id=selected.candidate_id,
        launch_site_mgrs=selected.launch_site_mgrs,
        target_mgrs=target_mgrs,
        route_candidates=output_candidates,
        warnings=warnings,
        config=config,
        terrain_metadata=metadata,
        graph_nodes=node_outputs,
        graph_edges=edge_outputs,
        summary=RealTerrainRouteSummary(
            graph_node_count=len(node_outputs),
            graph_edge_count=len(edge_outputs),
            traversable_node_count=sum(node.traversable for node in analyzed_nodes),
            route_count=len(output_candidates),
        ),
        waypoint_handoffs=handoffs,
        launch_ground_msl_m=launch_sample.dem_msl,
        snapped_launch_node_id=start.node_id,
        snapped_target_node_id=target.node_id,
        snapped_launch_node_mgrs=snapped_launch_mgrs,
        snapped_target_node_mgrs=snapped_target_mgrs,
        launch_snap_distance_m=distance_2d_m(selected.projected_point, start.point),
        target_snap_distance_m=distance_2d_m(source_result.target_point, target.point),
    )


def _route_bounds(*, launch: LocalPoint, target: LocalPoint, operation_radius_m: float, route_margin_m: float, raster_bounds: tuple[float, float, float, float]) -> RouteGraphBounds:
    min_x = max(min(launch.x_m, target.x_m) - route_margin_m, launch.x_m - operation_radius_m, raster_bounds[0])
    min_y = max(min(launch.y_m, target.y_m) - route_margin_m, launch.y_m - operation_radius_m, raster_bounds[1])
    max_x = min(max(launch.x_m, target.x_m) + route_margin_m, launch.x_m + operation_radius_m, raster_bounds[2])
    max_y = min(max(launch.y_m, target.y_m) + route_margin_m, launch.y_m + operation_radius_m, raster_bounds[3])
    if min_x > max_x or min_y > max_y:
        raise RealTerrainRouteAnalysisError("route bounds are empty after clipping.")
    return RouteGraphBounds(min_x, min_y, max_x, max_y)


def _validate_pre_session_guards(
    source_result: RealTerrainLaunchAreaResult,
    selected: SelectedLaunchSiteRecord,
    selected_score: CandidateScore,
    config: RealTerrainRouteConfig,
) -> None:
    """Reject an oversized route plan using source metadata before raster access."""

    metadata = source_result.dataset_metadata
    bounds = _route_bounds(
        launch=selected.projected_point,
        target=source_result.target_point,
        operation_radius_m=selected_score.operating_radius_m,
        route_margin_m=config.route_margin_m,
        raster_bounds=metadata.dem.bounds,
    )
    nodes = build_route_grid(bounds, graph_spacing_m=config.graph_spacing_m)
    if len(nodes) > config.max_graph_nodes:
        raise RealTerrainRouteAnalysisError("graph node guard exceeded before terrain session.")
    if len(nodes) * 8 > config.max_graph_edges:
        raise RealTerrainRouteAnalysisError("graph edge guard exceeded before terrain session.")
    profile_counts = tuple(
        max(1, ceil(distance_2d_m(selected.projected_point, node.point) / config.profile_spacing_m))
        + 1
        for node in nodes
    )
    if any(count > config.max_profile_samples_per_node for count in profile_counts):
        raise RealTerrainRouteAnalysisError("profile sample-per-node guard exceeded before terrain session.")
    if sum(profile_counts) > config.max_total_profile_samples:
        raise RealTerrainRouteAnalysisError("total profile sample guard exceeded before terrain session.")


def _analyze_node(session: object, graph: RouteGraphNode, *, launch_point: LocalPoint, launch_flight_msl: float, target_radius_m: float, config: RealTerrainRouteConfig, scenario_name: str) -> _Node:
    try:
        sample = session.sample_point(graph.point)  # type: ignore[attr-defined]
    except TerrainPointOutsideError as exc:
        return _Node(graph, RouteNodeState.OUTSIDE_RASTER_EXTENT, str(exc))
    except TerrainNoDataError as exc:
        return _Node(graph, RouteNodeState.TERRAIN_NODATA, str(exc))
    except TerrainDataError as exc:
        return _Node(graph, RouteNodeState.TERRAIN_NODATA, str(exc))
    flight_msl = sample.dem_msl + config.allowed_flight_agl_m
    distance = distance_3d_m(LocalPoint(launch_point.x_m, launch_point.y_m, launch_flight_msl), LocalPoint(graph.point.x_m, graph.point.y_m, flight_msl))
    if distance > target_radius_m + 1e-12:
        return _Node(
            graph,
            RouteNodeState.OUTSIDE_OPERATION_RADIUS,
            "outside operation radius",
            flight_msl,
            distance,
            terrain_msl_m=sample.dem_msl,
            surface_msl_m=sample.dsm_msl,
            within_operation_radius=False,
        )
    if sample.dsm_msl > flight_msl:
        return _Node(
            graph,
            RouteNodeState.INVALID_SURFACE,
            "surface is above flight MSL",
            flight_msl,
            distance,
            terrain_msl_m=sample.dem_msl,
            surface_msl_m=sample.dsm_msl,
            within_operation_radius=True,
        )
    try:
        if graph.point == launch_point:
            score = compute_candidate_score(distance_3d_m=0.0, operating_radius_m=target_radius_m, dsm_los_score=100.0, dsm_fresnel_score=100.0)
            diagnostics = CandidateFresnelDiagnostics.no_eligible(average_fresnel_score=100.0)
        else:
            try:
                profile = session.extract_profile(  # type: ignore[attr-defined]
                    launch_point,
                    graph.point,
                    sample_spacing_m=config.profile_spacing_m,
                    scenario_name=scenario_name,
                )
            except (TerrainDataError, TerrainProfileError) as exc:
                return _Node(
                    graph,
                    RouteNodeState.PROFILE_UNAVAILABLE,
                    str(exc),
                    flight_msl,
                    distance,
                    terrain_msl_m=sample.dem_msl,
                    surface_msl_m=sample.dsm_msl,
                    within_operation_radius=True,
                )
            los = analyze_dsm_los(
                profile,
                launch_antenna_msl=launch_flight_msl,
                drone_flight_msl=flight_msl,
            )
            fresnel = analyze_dsm_fresnel(los, frequency_hz=config.frequency_hz)
            diagnostics = candidate_fresnel_diagnostics_from_analysis(fresnel)
            score = compute_candidate_score(
                distance_3d_m=distance,
                operating_radius_m=target_radius_m,
                dsm_los_score=los.dsm_los_score,
                dsm_fresnel_score=fresnel.dsm_fresnel_score,
            )
        color = classify_candidate_score(score, within_operation_radius=True)
    except (
        LineOfSightError,
        FresnelAnalysisError,
        ScoringError,
        ClassificationError,
    ) as exc:
        return _Node(
            graph,
            RouteNodeState.ANALYSIS_INVALID,
            str(exc),
            flight_msl,
            distance,
            terrain_msl_m=sample.dem_msl,
            surface_msl_m=sample.dsm_msl,
            within_operation_radius=True,
        )
    return _Node(
        graph,
        RouteNodeState.VALID_SCORED,
        "valid scored route node",
        flight_msl,
        distance,
        score,
        color,
        terrain_msl_m=sample.dem_msl,
        surface_msl_m=sample.dsm_msl,
        fresnel_diagnostics=diagnostics,
        within_operation_radius=True,
    )


def _build_base_edges(
    nodes: tuple[_Node, ...],
    topology: RouteGraphTopology,
    config: RealTerrainRouteConfig,
) -> tuple[_BaseRouteEdge, ...]:
    """Construct immutable graph topology and mode-independent edge parts once."""

    by_id = {node.graph.node_id: node for node in nodes}
    edges: list[_BaseRouteEdge] = []
    for node in nodes:
        if not node.traversable:
            continue
        for neighbor_id in topology.neighbors_by_id[node.graph.node_id]:
            neighbor = by_id[neighbor_id]
            if not neighbor.traversable:
                continue
            distance = distance_3d_m(
                LocalPoint(node.graph.point.x_m, node.graph.point.y_m, node.flight_msl_m or 0.0),
                LocalPoint(neighbor.graph.point.x_m, neighbor.graph.point.y_m, neighbor.flight_msl_m or 0.0),
            )
            risk = 100.0 - (neighbor.score.shielding_stability_score if neighbor.score else 0.0)
            distance_component = min(distance / config.graph_spacing_m, 2.0) * 50.0
            color_penalty = (
                0.0
                if neighbor.color_class in {ColorClass.GREEN, ColorClass.YELLOW}
                else 50.0
                if neighbor.color_class is ColorClass.ORANGE
                else 100.0
            )
            edges.append(
                _BaseRouteEdge(
                    node.graph.node_id,
                    neighbor_id,
                    distance,
                    risk,
                    distance_component,
                    color_penalty,
                )
            )
    return tuple(edges)


def _mode_edges(base_edges: tuple[_BaseRouteEdge, ...], mode: RouteMode) -> tuple[DirectedRouteEdge, ...]:
    """Reweight precomputed edge components without rebuilding graph topology."""

    policy = route_mode_cost_policy(mode)
    return tuple(
        DirectedRouteEdge(
            edge.from_node_id,
            edge.to_node_id,
            policy.shielding_weight * edge.shielding_risk_cost
            + policy.distance_weight * edge.distance_cost
            + policy.high_risk_multiplier * edge.high_risk_penalty,
            edge.distance_3d_m,
        )
        for edge in base_edges
    )


def _route_candidates(
    base_edges: tuple[_BaseRouteEdge, ...],
    by_id: dict[str, _Node],
    start_id: str,
    target_id: str,
    config: RealTerrainRouteConfig,
) -> tuple[tuple[_PathCandidate, ...], tuple[str, ...]]:
    positions = {node_id: (node.graph.row, node.graph.column) for node_id, node in by_id.items()}
    previous_edges: set[tuple[str, str]] = set()
    candidates: list[_PathCandidate] = []
    warnings: list[str] = []
    expansions_total = 0
    for mode in RouteMode:
        edges = _mode_edges(base_edges, mode)
        penalties = {edge: config.overlap_penalty_weight for edge in previous_edges}
        try:
            path = dijkstra_shortest_path(edges, start_node_id=start_id, target_node_id=target_id, node_positions=positions, max_path_expansions=config.max_path_expansions_per_search, additional_edge_cost=penalties)
        except RouteNoPathError as exc:
            expansions_total = _add_expansions(expansions_total, exc, config)
            warnings.append(f"{mode.value} route unavailable")
            continue
        except (RouteExpansionLimitError, RoutePathfindingInputError, RoutePathfindingInvariantError) as exc:
            raise RealTerrainRouteAnalysisError("route pathfinding failed.") from exc
        expansions_total = _add_expansions(expansions_total, path, config)
        directed = set(zip(path.node_ids, path.node_ids[1:]))
        if any(path.node_ids == prior.path.node_ids for prior in candidates):
            warnings.append(f"{mode.value} route duplicates an earlier route")
            continue
        shared_ratios = _shared_edge_ratios(directed, candidates)
        if shared_ratios and max(shared_ratios) > config.maximum_shared_edge_ratio:
                retry_penalties = {edge: config.overlap_penalty_weight * 2.0 for edge in previous_edges}
                try:
                    path = dijkstra_shortest_path(edges, start_node_id=start_id, target_node_id=target_id, node_positions=positions, max_path_expansions=config.max_path_expansions_per_search, additional_edge_cost=retry_penalties)
                except RouteNoPathError as exc:
                    expansions_total = _add_expansions(expansions_total, exc, config)
                    warnings.append(f"{mode.value} route unavailable after diversity retry")
                    continue
                except (RouteExpansionLimitError, RoutePathfindingInputError, RoutePathfindingInvariantError) as exc:
                    raise RealTerrainRouteAnalysisError("route pathfinding failed.") from exc
                expansions_total = _add_expansions(expansions_total, path, config)
                directed = set(zip(path.node_ids, path.node_ids[1:]))
                if any(path.node_ids == prior.path.node_ids for prior in candidates):
                    warnings.append(f"{mode.value} route duplicates an earlier route after diversity retry")
                    continue
                shared_ratios = _shared_edge_ratios(directed, candidates)
                if shared_ratios and max(shared_ratios) > config.maximum_shared_edge_ratio:
                    warnings.append(f"{mode.value} route exceeds diversity limit")
                    continue
        candidates.append(_PathCandidate(mode, path, shared_ratios))
        previous_edges.update(directed)
    if not candidates:
        raise RealTerrainRouteAnalysisError("no route candidates were produced.")
    if len(candidates) == 1:
        warnings.append("only 1 route candidate is available")
    elif len(candidates) == 2:
        warnings.append("only 2 route candidates are available")
    return tuple(candidates), tuple(dict.fromkeys(warnings))


def _add_expansions(
    total: int,
    outcome: DijkstraPath | RoutePathfindingError,
    config: RealTerrainRouteConfig,
) -> int:
    updated = total + outcome.expansions
    if updated > config.max_total_path_expansions:
        raise RealTerrainRouteAnalysisError("total path expansion guard exceeded.")
    return updated


def _to_output_candidate(
    candidate: _PathCandidate,
    by_id: dict[str, _Node],
    mgrs_cache: dict[LocalPoint, str],
    converter: ProjectedToMgrsConverter,
) -> RealTerrainRouteCandidate:
    mode, path = candidate.mode, candidate.path
    node_ids = path.node_ids
    points = tuple(
        RealTerrainRoutePathPoint(
            index,
            _mgrs_for_point(by_id[node_id].graph.point, converter, mgrs_cache),
            by_id[node_id].flight_msl_m or 0.0,
        )
        for index, node_id in enumerate(node_ids)
    )
    scores = tuple(
        node.score.shielding_stability_score
        for node_id in node_ids
        for node in (by_id[node_id],)
        if node.score is not None
    )
    return RealTerrainRouteCandidate(
        route_id=f"route-{mode.value}",
        mode=mode,
        path=points,
        total_cost=path.total_cost,
        total_distance_3d_m=path.total_distance_3d_m,
        mean_shielding_stability_score=sum(scores) / len(scores),
        minimum_shielding_stability_score=min(scores),
        ordered_node_ids=node_ids,
        ordered_projected_points=tuple(by_id[node_id].graph.point for node_id in node_ids),
        orange_count=sum(by_id[node_id].color_class is ColorClass.ORANGE for node_id in node_ids),
        red_count=sum(by_id[node_id].color_class is ColorClass.RED for node_id in node_ids),
        high_risk_count=sum(
            by_id[node_id].color_class in {ColorClass.ORANGE, ColorClass.RED}
            for node_id in node_ids
        ),
        shared_edge_ratios=candidate.shared_edge_ratios,
    )


def _node_output(node: _Node, config: RealTerrainRouteConfig) -> RealTerrainRouteNode:
    score = node.score
    return RealTerrainRouteNode(
        node_id=node.graph.node_id,
        row=node.graph.row,
        column=node.graph.column,
        projected_point=node.graph.point,
        node_mgrs=None,
        terrain_msl_m=node.terrain_msl_m,
        surface_msl_m=node.surface_msl_m,
        flight_agl_m=config.allowed_flight_agl_m,
        flight_msl_m=node.flight_msl_m,
        distance_3d_from_launch_m=node.distance_3d_m,
        within_operation_radius=node.within_operation_radius,
        state=node.state,
        traversable=node.traversable,
        reason=node.reason,
        shielding_stability_score=None if score is None else score.shielding_stability_score,
        overall_score=None if score is None else score.overall_score,
        color_class=node.color_class,
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="source-zone provider not requested for route nodes",
        fresnel_diagnostics=node.fresnel_diagnostics,
    )


def _edge_output(edge: _BaseRouteEdge) -> RealTerrainRouteEdge:
    return RealTerrainRouteEdge(
        from_node_id=edge.from_node_id,
        to_node_id=edge.to_node_id,
        distance_3d_m=edge.distance_3d_m,
        shielding_risk_cost=edge.shielding_risk_cost,
        distance_cost=edge.distance_cost,
        high_risk_penalty=edge.high_risk_penalty,
    )


def _waypoint_handoff(
    candidate: _PathCandidate,
    by_id: dict[str, _Node],
    mgrs_cache: dict[LocalPoint, str],
    converter: ProjectedToMgrsConverter,
) -> tuple[WaypointHandoffPoint, ...]:
    path = candidate.path
    points: list[WaypointHandoffPoint] = []
    cumulative = 0.0
    previous: _Node | None = None
    for index, node_id in enumerate(path.node_ids):
        node = by_id[node_id]
        if previous is not None:
            cumulative += distance_3d_m(
                LocalPoint(
                    previous.graph.point.x_m,
                    previous.graph.point.y_m,
                    previous.flight_msl_m or 0.0,
                ),
                LocalPoint(node.graph.point.x_m, node.graph.point.y_m, node.flight_msl_m or 0.0),
            )
        if node.score is None or node.terrain_msl_m is None or node.surface_msl_m is None:
            raise RealTerrainRouteAnalysisError("traversable route node is incomplete.")
        points.append(
            WaypointHandoffPoint(
                point_id=f"route-{candidate.mode.value}-handoff-{index:03d}",
                projected_point=node.graph.point,
                point_mgrs=_mgrs_for_point(node.graph.point, converter, mgrs_cache),
                cumulative_distance_3d_m=cumulative,
                terrain_msl_m=node.terrain_msl_m,
                surface_msl_m=node.surface_msl_m,
                flight_agl_m=node.flight_msl_m - node.terrain_msl_m if node.flight_msl_m is not None else 0.0,
                flight_msl_m=node.flight_msl_m or 0.0,
                color_class=node.color_class,
                shielding_stability_score=node.score.shielding_stability_score,
                overall_score=node.score.overall_score,
                source_zone=None,
                source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
                source_sensitive=None,
                source_zone_reason="source-zone provider not requested for route nodes",
            )
        )
        previous = node
    return tuple(points)


def _shared_edge_ratios(
    directed_edges: set[tuple[str, str]],
    prior_candidates: list[_PathCandidate],
) -> tuple[float, ...]:
    if not directed_edges:
        return tuple(0.0 for _ in prior_candidates)
    ratios: list[float] = []
    for candidate in prior_candidates:
        prior_edges = set(zip(candidate.path.node_ids, candidate.path.node_ids[1:]))
        if not prior_edges:
            ratios.append(0.0)
            continue
        ratios.append(len(directed_edges & prior_edges) / min(len(directed_edges), len(prior_edges)))
    return tuple(ratios)


def _normalize_mgrs(value: object) -> str:
    if not isinstance(value, str):
        raise CoordinateConversionError("MGRS conversion did not return text.")
    normalized = value.strip().upper()
    if not normalized:
        raise CoordinateConversionError("MGRS conversion returned empty text.")
    return normalized


def _mgrs_for_point(
    point: LocalPoint,
    converter: ProjectedToMgrsConverter,
    cache: dict[LocalPoint, str],
) -> str:
    """Convert each unique projected route point at most once."""

    if point not in cache:
        cache[point] = _normalize_mgrs(converter(point, precision=5))
    return cache[point]
