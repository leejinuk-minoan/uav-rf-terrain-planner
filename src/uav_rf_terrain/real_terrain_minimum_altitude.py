"""Pure Task 036B minimum-altitude engine over prepared immutable evidence.

This module never opens a terrain session or reads GIS data.  Task 036C prepares
the route and radial-profile evidence after the approved terrain-session checks.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite

from ._minimum_altitude_selection import (
    MinimumAltitudeSelectionError,
    select_tolerance_representative,
)
from .coordinates import LocalPoint, distance_2d_m
from .fresnel import FresnelAnalysisError, first_fresnel_radius_m, wavelength_m
from .launch_site_selection import LaunchSiteSelectionError, SelectedLaunchSiteRecord
from .profile import TerrainProfile, TerrainProfileError, TerrainProfileSample
from .real_terrain_minimum_altitude_outputs import (
    RealTerrainMinimumAltitudeConfig,
    RealTerrainMinimumAltitudeAuthoritySnapshot,
    RealTerrainMinimumAltitudeOutputError,
    RealTerrainMinimumAltitudePreparedRouteSnapshot,
    RealTerrainMinimumAltitudePreparedSampleSnapshot,
    RealTerrainMinimumAltitudeProfileSampleSnapshot,
    RealTerrainMinimumAltitudeProfileSnapshot,
    RealTerrainMinimumAltitudeResult,
    RealTerrainMinimumAltitudeSourceRoute,
    RealTerrainMinimumAltitudeSummary,
    RealTerrainRadialRequirementSample,
    RealTerrainRouteAltitudeSample,
    RealTerrainRouteMinimumAltitudeResult,
)
from .real_terrain_route_outputs import (
    RealTerrainRouteCandidate,
    RealTerrainRouteConfig,
    RealTerrainRouteEdge,
    RealTerrainRouteNode,
    RealTerrainRouteOutputError,
    RealTerrainRoutePathPoint,
    RealTerrainRouteResult,
    RealTerrainRouteSummary,
    RouteMode,
    RouteNodeState,
    WaypointHandoffPoint,
)
from .terrain_data import (
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
    validate_terrain_dataset_metadata,
)


class RealTerrainMinimumAltitudeError(ValueError):
    """Raised when prepared evidence or the pure engine contract is invalid."""


@dataclass(frozen=True)
class PreparedRealTerrainRouteSample:
    """One route-resampling endpoint with its already prepared radial profile."""

    route_sample_id: str
    route_id: str
    mode: RouteMode
    route_sample_index: int
    route_sample_mgrs: str
    projected_point: LocalPoint
    cumulative_route_distance_2d_m: float
    local_dem_msl_m: float
    local_dsm_msl_m: float
    is_snapped_target_endpoint: bool
    radial_distance_2d_m: float
    radial_profile: TerrainProfile | None

    def __post_init__(self) -> None:
        if not isinstance(self.projected_point, LocalPoint) or not isinstance(self.mode, RouteMode):
            raise RealTerrainMinimumAltitudeError("prepared sample point and mode are invalid.")
        if not isinstance(self.route_sample_id, str) or not self.route_sample_id:
            raise RealTerrainMinimumAltitudeError("prepared sample ID is required.")
        if not isinstance(self.route_id, str) or not self.route_id:
            raise RealTerrainMinimumAltitudeError("prepared sample route ID is required.")
        if not isinstance(self.route_sample_mgrs, str) or not self.route_sample_mgrs or self.route_sample_mgrs != self.route_sample_mgrs.upper():
            raise RealTerrainMinimumAltitudeError("prepared sample MGRS must be uppercase.")
        if isinstance(self.route_sample_index, bool) or not isinstance(self.route_sample_index, int) or self.route_sample_index < 0:
            raise RealTerrainMinimumAltitudeError("prepared sample index is invalid.")
        _validate_finite_values(
            "prepared numeric evidence",
            self.cumulative_route_distance_2d_m,
            self.local_dem_msl_m,
            self.local_dsm_msl_m,
            self.radial_distance_2d_m,
        )
        if self.cumulative_route_distance_2d_m < 0.0 or self.radial_distance_2d_m < 0.0 or self.local_dsm_msl_m < self.local_dem_msl_m:
            raise RealTerrainMinimumAltitudeError("prepared terrain/distance evidence is invalid.")
        if not isinstance(self.is_snapped_target_endpoint, bool):
            raise RealTerrainMinimumAltitudeError("target endpoint flag must be bool.")
        if self.radial_profile is not None and not isinstance(self.radial_profile, TerrainProfile):
            raise RealTerrainMinimumAltitudeError("prepared radial profile must be TerrainProfile or None.")


@dataclass(frozen=True)
class PreparedRealTerrainRoute:
    """Prepared evidence for one reviewed source route candidate."""

    route_id: str
    mode: RouteMode
    source_order: int
    source_total_distance_3d_m: float
    route_polyline_total_distance_2d_m: float
    terrain_metadata: TerrainDatasetMetadata
    samples: tuple[PreparedRealTerrainRouteSample, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.mode, RouteMode) or not isinstance(self.route_id, str) or self.route_id != f"route-{self.mode.value}":
            raise RealTerrainMinimumAltitudeError("prepared route identity is invalid.")
        if type(self.samples) is not tuple:
            raise RealTerrainMinimumAltitudeError("prepared route samples must be a tuple.")
        if isinstance(self.source_order, bool) or not isinstance(self.source_order, int) or self.source_order < 0 or not self.samples:
            raise RealTerrainMinimumAltitudeError("prepared route order/samples are invalid.")
        _validate_finite_values("prepared route distances", self.source_total_distance_3d_m, self.route_polyline_total_distance_2d_m)
        if self.source_total_distance_3d_m < 0.0 or self.route_polyline_total_distance_2d_m < 0.0:
            raise RealTerrainMinimumAltitudeError("prepared route distances are invalid.")
        _validate_exact_terrain_metadata(self.terrain_metadata, "prepared")
        if any(not isinstance(sample, PreparedRealTerrainRouteSample) for sample in self.samples):
            raise RealTerrainMinimumAltitudeError("prepared route samples must use the approved type.")
        if tuple(sample.route_sample_index for sample in self.samples) != tuple(range(len(self.samples))):
            raise RealTerrainMinimumAltitudeError("prepared sample indexes must be contiguous.")
        if any(sample.route_id != self.route_id or sample.mode is not self.mode for sample in self.samples):
            raise RealTerrainMinimumAltitudeError("prepared sample route parity failed.")


def compute_real_terrain_minimum_altitude(
    *,
    route_result: RealTerrainRouteResult,
    selected_launch_site: SelectedLaunchSiteRecord,
    prepared_routes: tuple[PreparedRealTerrainRoute, ...],
    config: RealTerrainMinimumAltitudeConfig,
) -> RealTerrainMinimumAltitudeResult:
    """Compute deterministic proxy MSL results without terrain/session access."""

    try:
        _validate_source_authority(route_result, selected_launch_site, config)
        _enforce_resource_guards(prepared_routes, config)
        _validate_prepared_authority(route_result, selected_launch_site, prepared_routes, config)
    except RealTerrainMinimumAltitudeError:
        raise
    except _KNOWN_CONTRACT_ERRORS as exc:
        raise RealTerrainMinimumAltitudeError("source or prepared-evidence validation failed.") from exc

    source_config = route_result.config
    launch_ground = float(route_result.launch_ground_msl_m)
    allowed_agl = float(source_config.allowed_flight_agl_m)
    frequency = float(source_config.frequency_hz)
    launch_antenna = launch_ground + allowed_agl
    _validate_finite_values("launch authority", launch_ground, allowed_agl, launch_antenna)
    if allowed_agl <= 0.0:
        raise RealTerrainMinimumAltitudeError("route allowed AGL must be positive.")
    if config.expected_frequency_hz is not None and config.expected_frequency_hz != frequency:
        raise RealTerrainMinimumAltitudeError("expected frequency does not match route authority.")
    if config.profile_spacing_m is not None and config.profile_spacing_m > source_config.profile_spacing_m:
        raise RealTerrainMinimumAltitudeError("explicit profile spacing cannot exceed route profile spacing.")
    resolved_spacing = float(config.profile_spacing_m or source_config.profile_spacing_m)
    try:
        route_results = tuple(
            _compute_route(
                route,
                launch_point=selected_launch_site.projected_point,
                launch_ground=launch_ground,
                launch_antenna=launch_antenna,
                allowed_agl=allowed_agl,
                frequency=frequency,
                profile_spacing_m=resolved_spacing,
                config=config,
            )
            for route in prepared_routes
        )
        warnings = tuple(warning for route in route_results for warning in route.warnings)
        authority = _snapshot_authority(
            route_result,
            selected_launch_site,
            prepared_routes,
            resolved_spacing,
            config,
        )
        result = RealTerrainMinimumAltitudeResult(
            route_result.selected_candidate_id,
            route_result.launch_site_mgrs,
            route_result.target_mgrs,
            route_results,
            warnings,
            RealTerrainMinimumAltitudeSummary(
                len(route_results),
                sum(len(route.route_samples) for route in route_results),
                sum(
                    len(sample.radial_requirement_samples)
                    for route in route_results
                    for sample in route.route_samples
                ),
                warnings,
            ),
            authority,
            _authority_fingerprint(authority),
            "pending",
        )
        object.__setattr__(result, "_output_fingerprint", _emitted_output_fingerprint(result))
        validate_complete_real_terrain_minimum_altitude_result(result)
        return result
    except RealTerrainMinimumAltitudeError:
        raise
    except _KNOWN_CONTRACT_ERRORS as exc:
        raise RealTerrainMinimumAltitudeError("minimum-altitude calculation failed.") from exc


def _copy_point(point: LocalPoint) -> LocalPoint:
    return LocalPoint(point.x_m, point.y_m, point.z_m)


def _snapshot_profile(profile: TerrainProfile) -> RealTerrainMinimumAltitudeProfileSnapshot:
    return RealTerrainMinimumAltitudeProfileSnapshot(
        profile.scenario_name,
        _copy_point(profile.start),
        _copy_point(profile.end),
        profile.sample_spacing_m,
        tuple(
            RealTerrainMinimumAltitudeProfileSampleSnapshot(
                item.sample_index,
                _copy_point(item.point),
                item.distance_from_start_m,
                item.distance_to_end_m,
                item.dem_msl,
                item.dsm_msl,
                item.surface_delta_m,
            )
            for item in profile.samples
        ),
    )


def _snapshot_authority(
    route_result: RealTerrainRouteResult,
    selected_launch_site: SelectedLaunchSiteRecord,
    prepared_routes: tuple[PreparedRealTerrainRoute, ...],
    resolved_spacing: float,
    config: RealTerrainMinimumAltitudeConfig,
) -> RealTerrainMinimumAltitudeAuthoritySnapshot:
    """Copy only the authority required for later recursive revalidation."""

    return RealTerrainMinimumAltitudeAuthoritySnapshot(
        route_result.selected_candidate_id,
        route_result.launch_site_mgrs,
        route_result.target_mgrs,
        _copy_point(selected_launch_site.projected_point),
        deepcopy(config),
        route_result.config.frequency_hz,
        route_result.config.allowed_flight_agl_m,
        route_result.config.profile_spacing_m,
        resolved_spacing,
        route_result.launch_ground_msl_m,
        deepcopy(route_result.terrain_metadata),
        tuple(
            RealTerrainMinimumAltitudeSourceRoute(
                candidate.route_id,
                candidate.mode,
                index,
                candidate.total_distance_3d_m,
            )
            for index, candidate in enumerate(route_result.route_candidates)
        ),
        tuple(
            RealTerrainMinimumAltitudePreparedRouteSnapshot(
                route.route_id,
                route.mode,
                route.source_order,
                route.source_total_distance_3d_m,
                route.route_polyline_total_distance_2d_m,
                tuple(
                    RealTerrainMinimumAltitudePreparedSampleSnapshot(
                        sample.route_sample_id,
                        sample.route_id,
                        sample.mode,
                        sample.route_sample_index,
                        sample.route_sample_mgrs,
                        _copy_point(sample.projected_point),
                        sample.cumulative_route_distance_2d_m,
                        sample.local_dem_msl_m,
                        sample.local_dsm_msl_m,
                        sample.is_snapped_target_endpoint,
                        sample.radial_distance_2d_m,
                        None if sample.radial_profile is None else _snapshot_profile(sample.radial_profile),
                    )
                    for sample in route.samples
                ),
            )
            for route in prepared_routes
        ),
    )


def _authority_fingerprint(authority: RealTerrainMinimumAltitudeAuthoritySnapshot) -> str:
    """Canonical local invariant seal, not a hostile in-process security boundary."""
    return sha256(repr(authority).encode("utf-8")).hexdigest()


def _emitted_output_fingerprint(result: RealTerrainMinimumAltitudeResult) -> str:
    """Exact private seal for all emitted result fields before tolerant replay."""
    return sha256(
        repr(
            (
                result.selected_candidate_id,
                result.launch_site_mgrs,
                result.target_mgrs,
                result.route_results,
                result.warnings,
                result.summary,
            )
        ).encode("utf-8")
    ).hexdigest()


_KNOWN_CONTRACT_ERRORS = (
    RealTerrainRouteOutputError,
    LaunchSiteSelectionError,
    TerrainProfileError,
    FresnelAnalysisError,
    RealTerrainMinimumAltitudeOutputError,
    TerrainDataError,
    MinimumAltitudeSelectionError,
)


def _validate_exact_terrain_metadata(metadata: object, context: str) -> TerrainDatasetMetadata:
    """Rerun exact reviewed terrain metadata validators before replay or sealing."""

    if type(metadata) is not TerrainDatasetMetadata:
        raise RealTerrainMinimumAltitudeError(f"{context} terrain metadata type is invalid.")
    if type(metadata.dem) is not TerrainRasterMetadata or type(metadata.dsm) is not TerrainRasterMetadata:
        raise RealTerrainMinimumAltitudeError(f"{context} terrain metadata raster type is invalid.")
    _preflight_terrain_metadata_fields(metadata, context)
    try:
        metadata.dem.__post_init__()
        metadata.dsm.__post_init__()
        metadata.__post_init__()
        validate_terrain_dataset_metadata(metadata)
    except TerrainDataError as exc:
        raise RealTerrainMinimumAltitudeError(f"{context} terrain metadata is invalid.") from exc
    return metadata


def _preflight_terrain_metadata_fields(metadata: TerrainDatasetMetadata, context: str) -> None:
    """Reject malformed metadata primitives before reviewed validators dereference them."""

    if any(
        type(value) is not str
        for value in (
            metadata.dataset_name,
            metadata.processing_date,
            metadata.processing_tool,
            metadata.alignment_status,
            metadata.notes,
        )
    ):
        raise RealTerrainMinimumAltitudeError(f"{context} terrain metadata text is invalid.")
    for raster in (metadata.dem, metadata.dsm):
        if any(
            type(value) is not str
            for value in (
                raster.name,
                raster.raster_type,
                raster.source_dataset_name,
                raster.source_provider,
                raster.license_or_terms,
                raster.crs,
                raster.vertical_datum,
                raster.processing_summary,
            )
        ):
            raise RealTerrainMinimumAltitudeError(f"{context} terrain raster text is invalid.")
        if (
            isinstance(raster.resolution_m, bool)
            or not isinstance(raster.resolution_m, (int, float))
            or not isfinite(raster.resolution_m)
            or isinstance(raster.width, bool)
            or not isinstance(raster.width, int)
            or isinstance(raster.height, bool)
            or not isinstance(raster.height, int)
            or type(raster.bounds) is not tuple
            or len(raster.bounds) != 4
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                for value in raster.bounds
            )
            or (
                raster.nodata_value is not None
                and (
                    isinstance(raster.nodata_value, bool)
                    or not isinstance(raster.nodata_value, (int, float))
                    or not isfinite(raster.nodata_value)
                )
            )
            or type(raster.is_synthetic) is not bool
            or type(raster.is_redistributable_processed_data) is not bool
        ):
            raise RealTerrainMinimumAltitudeError(f"{context} terrain raster fields are invalid.")


def _preflight_source_collections(route_result: RealTerrainRouteResult) -> None:
    """Reject oversized or malformed source collections before deep replay."""

    if type(route_result.config) is not RealTerrainRouteConfig:
        raise RealTerrainMinimumAltitudeError("source route config type is invalid.")
    route_result.config.__post_init__()
    for name in (
        "route_candidates",
        "warnings",
        "graph_nodes",
        "graph_edges",
        "waypoint_handoffs",
    ):
        if type(getattr(route_result, name)) is not tuple:
            raise RealTerrainMinimumAltitudeError(f"source {name} must be an exact tuple.")
    if any(type(warning) is not str for warning in route_result.warnings):
        raise RealTerrainMinimumAltitudeError("source warnings must be text.")
    if len(route_result.route_candidates) > len(RouteMode):
        raise RealTerrainMinimumAltitudeError("source route candidate count violates fixed route-mode guard.")
    if len(route_result.graph_nodes) > route_result.config.max_graph_nodes:
        raise RealTerrainMinimumAltitudeError("source graph node count violates resource guard.")
    if len(route_result.graph_edges) > route_result.config.max_graph_edges:
        raise RealTerrainMinimumAltitudeError("source graph edge count violates resource guard.")
    if len(route_result.waypoint_handoffs) > len(RouteMode):
        raise RealTerrainMinimumAltitudeError("source waypoint handoff count violates fixed route-mode guard.")
    if type(route_result.summary) is not RealTerrainRouteSummary:
        raise RealTerrainMinimumAltitudeError("source route summary type is invalid.")
    if (
        route_result.summary.graph_node_count != len(route_result.graph_nodes)
        or route_result.summary.graph_edge_count != len(route_result.graph_edges)
        or route_result.summary.route_count != len(route_result.route_candidates)
    ):
        raise RealTerrainMinimumAltitudeError("source graph summary count parity is invalid.")
    if len(route_result.waypoint_handoffs) != len(route_result.route_candidates):
        raise RealTerrainMinimumAltitudeError("source waypoint handoff count does not match routes.")
    for candidate, handoff in zip(route_result.route_candidates, route_result.waypoint_handoffs):
        if type(candidate) is not RealTerrainRouteCandidate or type(handoff) is not tuple:
            raise RealTerrainMinimumAltitudeError("source route-local collection type is invalid.")
        if (
            type(candidate.path) is not tuple
            or type(candidate.ordered_node_ids) is not tuple
            or type(candidate.ordered_projected_points) is not tuple
        ):
            raise RealTerrainMinimumAltitudeError("source route-local collections must be exact tuples.")
        route_local_length = len(candidate.path)
        if (
            route_local_length != len(candidate.ordered_node_ids)
            or route_local_length != len(candidate.ordered_projected_points)
            or route_local_length != len(handoff)
        ):
            raise RealTerrainMinimumAltitudeError("source route-local collection lengths are inconsistent.")
        if (
            route_local_length > len(route_result.graph_nodes)
            or route_local_length > route_result.config.max_graph_nodes
        ):
            raise RealTerrainMinimumAltitudeError("source route-local length violates graph guard.")


def _preflight_source_nested_types(route_result: RealTerrainRouteResult) -> None:
    """Check exact nested records before source ``__post_init__`` dereferences them."""

    for candidate in route_result.route_candidates:
        if type(candidate) is not RealTerrainRouteCandidate or type(candidate.mode) is not RouteMode:
            raise RealTerrainMinimumAltitudeError("source route candidate type or mode is invalid.")
        if type(candidate.path) is not tuple or type(candidate.ordered_projected_points) is not tuple:
            raise RealTerrainMinimumAltitudeError("source route candidate collections must be exact tuples.")
        if any(type(path_point) is not RealTerrainRoutePathPoint for path_point in candidate.path):
            raise RealTerrainMinimumAltitudeError("source route path point type is invalid.")
        if any(type(point) is not LocalPoint for point in candidate.ordered_projected_points):
            raise RealTerrainMinimumAltitudeError("source route projected point type is invalid.")
        if (
            type(candidate.route_id) is not str
            or type(candidate.reason) is not str
            or any(type(warning) is not str for warning in candidate.warnings)
            or any(type(node_id) is not str for node_id in candidate.ordered_node_ids)
        ):
            raise RealTerrainMinimumAltitudeError("source route candidate text is invalid.")
        for path_point in candidate.path:
            if type(path_point.mgrs) is not str:
                raise RealTerrainMinimumAltitudeError("source route path point text is invalid.")
    for node in route_result.graph_nodes:
        if type(node) is not RealTerrainRouteNode:
            raise RealTerrainMinimumAltitudeError("source graph node type is invalid.")
        if type(node.state) is not RouteNodeState or type(node.projected_point) is not LocalPoint:
            raise RealTerrainMinimumAltitudeError("source graph node state or point type is invalid.")
        if type(node.reason) is not str or type(node.source_zone_reason) is not str:
            raise RealTerrainMinimumAltitudeError("source graph node text is invalid.")
    for edge in route_result.graph_edges:
        if type(edge) is not RealTerrainRouteEdge:
            raise RealTerrainMinimumAltitudeError("source graph edge type is invalid.")
    for handoff in route_result.waypoint_handoffs:
        if type(handoff) is not tuple or any(type(item) is not WaypointHandoffPoint for item in handoff):
            raise RealTerrainMinimumAltitudeError("source waypoint handoff type is invalid.")
        for item in handoff:
            if (
                type(item.point_id) is not str
                or type(item.point_mgrs) is not str
                or type(item.source_zone_reason) is not str
            ):
                raise RealTerrainMinimumAltitudeError("source waypoint handoff text is invalid.")


def _validate_source_authority(
    route_result: RealTerrainRouteResult,
    selected_launch_site: SelectedLaunchSiteRecord,
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    if type(route_result) is not RealTerrainRouteResult:
        raise RealTerrainMinimumAltitudeError("route_result must be RealTerrainRouteResult.")
    if type(selected_launch_site) is not SelectedLaunchSiteRecord:
        raise RealTerrainMinimumAltitudeError("selected_launch_site must be SelectedLaunchSiteRecord.")
    if type(config) is not RealTerrainMinimumAltitudeConfig:
        raise RealTerrainMinimumAltitudeError("config must be RealTerrainMinimumAltitudeConfig.")
    _preflight_source_collections(route_result)
    _preflight_source_nested_types(route_result)
    if not isinstance(selected_launch_site.projected_point, LocalPoint):
        raise RealTerrainMinimumAltitudeError("selected launch projected point is invalid.")
    _validate_local_point(selected_launch_site.projected_point, "selected launch")
    _validate_exact_terrain_metadata(route_result.terrain_metadata, "source")
    # Frozen dataclasses can be corrupted through object.__setattr__; rerun validators.
    route_result.__post_init__()
    route_result.config.__post_init__()
    route_result.summary.__post_init__()
    for candidate in route_result.route_candidates:
        if type(candidate) is not RealTerrainRouteCandidate:
            raise RealTerrainMinimumAltitudeError("source route candidate type is invalid.")
        candidate.__post_init__()
        if not all(
            type(getattr(candidate, name)) is tuple
            for name in ("path", "warnings", "ordered_node_ids", "ordered_projected_points", "shared_edge_ratios")
        ):
            raise RealTerrainMinimumAltitudeError("source route candidate collections must be tuples.")
        for projected_point in candidate.ordered_projected_points:
            _validate_local_point(projected_point, "source route")
        for path_point in candidate.path:
            if type(path_point) is not RealTerrainRoutePathPoint:
                raise RealTerrainMinimumAltitudeError("source route path point type is invalid.")
            path_point.__post_init__()
    for node in route_result.graph_nodes:
        if type(node) is not RealTerrainRouteNode:
            raise RealTerrainMinimumAltitudeError("source graph node type is invalid.")
        node.__post_init__()
        _validate_local_point(node.projected_point, "source graph node")
    for edge in route_result.graph_edges:
        if type(edge) is not RealTerrainRouteEdge:
            raise RealTerrainMinimumAltitudeError("source graph edge type is invalid.")
        edge.__post_init__()
    for handoff in route_result.waypoint_handoffs:
        if type(handoff) is not tuple:
            raise RealTerrainMinimumAltitudeError("source waypoint handoff must be a tuple.")
        for handoff_point in handoff:
            if type(handoff_point) is not WaypointHandoffPoint:
                raise RealTerrainMinimumAltitudeError("source waypoint handoff item type is invalid.")
            handoff_point.__post_init__()
            _validate_local_point(handoff_point.projected_point, "source waypoint handoff")
    selected_launch_site.__post_init__()
    config.__post_init__()
    if selected_launch_site.candidate_id != route_result.selected_candidate_id:
        raise RealTerrainMinimumAltitudeError("selected launch candidate authority does not match route result.")
    if selected_launch_site.launch_site_mgrs != route_result.launch_site_mgrs:
        raise RealTerrainMinimumAltitudeError("selected launch MGRS authority does not match route result.")


def validate_complete_real_terrain_minimum_altitude_result(
    result: RealTerrainMinimumAltitudeResult,
) -> None:
    """Revalidate private source/prepared evidence and recursive public output parity."""
    if type(result) is not RealTerrainMinimumAltitudeResult:
        raise RealTerrainMinimumAltitudeError("result must be RealTerrainMinimumAltitudeResult.")
    try:
        authority = result._authority
        if type(authority) is not RealTerrainMinimumAltitudeAuthoritySnapshot:
            raise RealTerrainMinimumAltitudeError("authority snapshot type is invalid.")
        _validate_exact_terrain_metadata(authority.terrain_metadata, "snapshot")
        if _authority_fingerprint(authority) != result._authority_fingerprint:
            raise RealTerrainMinimumAltitudeError("authority snapshot does not match canonical fingerprint.")
        if _emitted_output_fingerprint(result) != result._output_fingerprint:
            raise RealTerrainMinimumAltitudeError("emitted output does not match canonical fingerprint.")
        _validate_snapshot_authority(authority, authority.config)
        result.__post_init__()
        if result.selected_candidate_id != authority.selected_candidate_id:
            raise RealTerrainMinimumAltitudeError("result selected candidate does not match source authority.")
        if result.launch_site_mgrs != authority.launch_site_mgrs:
            raise RealTerrainMinimumAltitudeError("result selected launch MGRS does not match selected launch authority.")
        if result.target_mgrs != authority.target_mgrs:
            raise RealTerrainMinimumAltitudeError("result target MGRS does not match source authority.")
        _validate_complete_output_authority_parity(result)
    except RealTerrainMinimumAltitudeError:
        raise
    except _KNOWN_CONTRACT_ERRORS as exc:
        raise RealTerrainMinimumAltitudeError("complete result authority validation failed.") from exc


def _validate_snapshot_authority(
    authority: RealTerrainMinimumAltitudeAuthoritySnapshot,
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    if type(authority) is not RealTerrainMinimumAltitudeAuthoritySnapshot:
        raise RealTerrainMinimumAltitudeError("authority snapshot type is invalid.")
    if type(config) is not RealTerrainMinimumAltitudeConfig:
        raise RealTerrainMinimumAltitudeError("config must be RealTerrainMinimumAltitudeConfig.")
    if type(authority.source_routes) is not tuple or type(authority.prepared_routes) is not tuple:
        raise RealTerrainMinimumAltitudeError("authority snapshot collections must be tuples.")
    if len(authority.source_routes) != len(authority.prepared_routes) or not authority.source_routes:
        raise RealTerrainMinimumAltitudeError("authority snapshot route count is invalid.")
    _validate_local_point(authority.selected_projected_point, "snapshot selected launch")
    _validate_finite_values(
        "snapshot mission authority",
        authority.frequency_hz,
        authority.allowed_flight_agl_m,
        authority.source_profile_spacing_m,
        authority.resolved_profile_spacing_m,
        authority.launch_ground_msl_m,
    )
    if authority.frequency_hz <= 0.0 or authority.allowed_flight_agl_m <= 0.0 or authority.source_profile_spacing_m <= 0.0 or authority.resolved_profile_spacing_m <= 0.0:
        raise RealTerrainMinimumAltitudeError("snapshot mission authority is invalid.")
    _validate_exact_terrain_metadata(authority.terrain_metadata, "snapshot")
    if config.expected_frequency_hz is not None and config.expected_frequency_hz != authority.frequency_hz:
        raise RealTerrainMinimumAltitudeError("expected frequency does not match snapshot authority.")
    if config.profile_spacing_m is not None and config.profile_spacing_m > authority.source_profile_spacing_m:
        raise RealTerrainMinimumAltitudeError("configured profile spacing exceeds snapshot authority.")
    for order, (source, route) in enumerate(zip(authority.source_routes, authority.prepared_routes)):
        if type(source) is not RealTerrainMinimumAltitudeSourceRoute:
            raise RealTerrainMinimumAltitudeError("snapshot source route type is invalid.")
        if type(route) is not RealTerrainMinimumAltitudePreparedRouteSnapshot:
            raise RealTerrainMinimumAltitudeError("snapshot prepared route type is invalid.")
        source.__post_init__()
        if (
            source.source_order != order
            or route.source_order != order
            or route.route_id != source.route_id
            or route.mode is not source.mode
            or not _near(route.source_total_distance_3d_m, source.source_total_distance_3d_m, config.distance_tolerance_m)
        ):
            raise RealTerrainMinimumAltitudeError("snapshot source route parity failed.")
        _validate_snapshot_prepared_route(authority, route, config)


def _validate_snapshot_prepared_route(
    authority: RealTerrainMinimumAltitudeAuthoritySnapshot,
    route: RealTerrainMinimumAltitudePreparedRouteSnapshot,
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    if type(route.samples) is not tuple or not route.samples:
        raise RealTerrainMinimumAltitudeError("snapshot prepared samples must be a non-empty tuple.")
    tolerance = config.distance_tolerance_m
    cumulative = 0.0
    for index, sample in enumerate(route.samples):
        if type(sample) is not RealTerrainMinimumAltitudePreparedSampleSnapshot:
            raise RealTerrainMinimumAltitudeError("snapshot prepared sample type is invalid.")
        _validate_local_point(sample.projected_point, "snapshot prepared sample")
        _validate_finite_values(
            "snapshot prepared sample",
            sample.cumulative_route_distance_2d_m,
            sample.local_dem_msl_m,
            sample.local_dsm_msl_m,
            sample.radial_distance_2d_m,
        )
        if (
            sample.route_id != route.route_id
            or sample.mode is not route.mode
            or sample.route_sample_index != index
            or sample.route_sample_id != f"{route.route_id}-sample-{index:03d}"
        ):
            raise RealTerrainMinimumAltitudeError("snapshot prepared sample identity is invalid.")
        if index:
            cumulative += distance_2d_m(route.samples[index - 1].projected_point, sample.projected_point)
        if not _near(sample.cumulative_route_distance_2d_m, cumulative, tolerance):
            raise RealTerrainMinimumAltitudeError("snapshot cumulative route geometry is invalid.")
        if not _near(sample.radial_distance_2d_m, distance_2d_m(authority.selected_projected_point, sample.projected_point), tolerance):
            raise RealTerrainMinimumAltitudeError("snapshot radial geometry is invalid.")
        _validate_snapshot_profile(authority, sample, config)
    if not _near(route.route_polyline_total_distance_2d_m, cumulative, tolerance):
        raise RealTerrainMinimumAltitudeError("snapshot route total geometry is invalid.")
    if sum(sample.is_snapped_target_endpoint for sample in route.samples) != 1 or not route.samples[-1].is_snapped_target_endpoint:
        raise RealTerrainMinimumAltitudeError("snapshot target endpoint is invalid.")


def _validate_snapshot_profile(
    authority: RealTerrainMinimumAltitudeAuthoritySnapshot,
    item: RealTerrainMinimumAltitudePreparedSampleSnapshot,
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    tolerance = config.distance_tolerance_m
    launch_antenna = authority.launch_ground_msl_m + authority.allowed_flight_agl_m
    recomputed_radial_distance = distance_2d_m(
        authority.selected_projected_point, item.projected_point
    )
    if not _near(item.radial_distance_2d_m, recomputed_radial_distance, tolerance):
        raise RealTerrainMinimumAltitudeError("snapshot radial geometry is invalid.")
    if recomputed_radial_distance <= tolerance:
        if (
            item.radial_profile is not None
            or not _near(item.local_dem_msl_m, authority.launch_ground_msl_m, tolerance)
            or item.local_dsm_msl_m > launch_antenna + tolerance
        ):
            raise RealTerrainMinimumAltitudeError("snapshot coincident occupancy is invalid.")
        return
    profile = item.radial_profile
    if type(profile) is not RealTerrainMinimumAltitudeProfileSnapshot:
        raise RealTerrainMinimumAltitudeError("snapshot nonzero radial profile is invalid.")
    if type(profile.samples) is not tuple or not profile.samples:
        raise RealTerrainMinimumAltitudeError("snapshot profile samples must be a non-empty tuple.")
    _validate_local_point(profile.start, "snapshot profile start")
    _validate_local_point(profile.end, "snapshot profile end")
    _validate_finite_values("snapshot profile spacing", profile.sample_spacing_m)
    if (
        not _near(profile.sample_spacing_m, authority.resolved_profile_spacing_m, tolerance)
        or not _points_within_tolerance(profile.start, authority.selected_projected_point, tolerance)
        or not _points_within_tolerance(profile.end, item.projected_point, tolerance)
    ):
        raise RealTerrainMinimumAltitudeError("snapshot profile endpoint/spacing parity failed.")
    total = distance_2d_m(profile.start, profile.end)
    if not _near(total, item.radial_distance_2d_m, tolerance):
        raise RealTerrainMinimumAltitudeError("snapshot profile total is invalid.")
    previous_from = -1.0
    previous_to = float("inf")
    for index, sample in enumerate(profile.samples):
        if type(sample) is not RealTerrainMinimumAltitudeProfileSampleSnapshot:
            raise RealTerrainMinimumAltitudeError("snapshot profile sample type is invalid.")
        _validate_local_point(sample.point, "snapshot profile sample")
        _validate_finite_values("snapshot profile sample", sample.distance_from_start_m, sample.distance_to_end_m, sample.dem_msl_m, sample.dsm_msl_m, sample.surface_delta_m)
        if (
            sample.sample_index != index
            or sample.distance_from_start_m <= previous_from
            or sample.distance_to_end_m >= previous_to
            or sample.dsm_msl_m < sample.dem_msl_m
            or not _near(sample.dsm_msl_m - sample.dem_msl_m, sample.surface_delta_m, tolerance)
            or not _near(sample.distance_from_start_m + sample.distance_to_end_m, total, tolerance)
        ):
            raise RealTerrainMinimumAltitudeError("snapshot profile sample order/parity is invalid.")
        ratio = sample.distance_from_start_m / total
        expected = LocalPoint(
            profile.start.x_m + (profile.end.x_m - profile.start.x_m) * ratio,
            profile.start.y_m + (profile.end.y_m - profile.start.y_m) * ratio,
            profile.start.z_m + (profile.end.z_m - profile.start.z_m) * ratio,
        )
        if not _points_within_tolerance(sample.point, expected, tolerance):
            raise RealTerrainMinimumAltitudeError("snapshot profile interpolation parity failed.")
        previous_from, previous_to = sample.distance_from_start_m, sample.distance_to_end_m
    first, last = profile.samples[0], profile.samples[-1]
    if (
        not _near(first.distance_from_start_m, 0.0, tolerance)
        or not _near(first.dem_msl_m, authority.launch_ground_msl_m, tolerance)
        or first.dsm_msl_m > launch_antenna + tolerance
        or not _near(last.distance_to_end_m, 0.0, tolerance)
        or not _near(last.dem_msl_m, item.local_dem_msl_m, tolerance)
        or not _near(last.dsm_msl_m, item.local_dsm_msl_m, tolerance)
    ):
        raise RealTerrainMinimumAltitudeError("snapshot profile endpoint terrain parity failed.")


def _validate_complete_output_authority_parity(
    result: RealTerrainMinimumAltitudeResult,
) -> None:
    """Bind every public computation field to retained source/prepared authority."""

    authority = result._authority
    tolerance = authority.config.distance_tolerance_m
    resolved_spacing = authority.resolved_profile_spacing_m
    if (
        authority.config.expected_frequency_hz is not None
        and not _near(
            authority.config.expected_frequency_hz,
            authority.frequency_hz,
            0.0,
        )
    ):
        raise RealTerrainMinimumAltitudeError("expected frequency does not match retained source authority.")
    if (
        authority.config.profile_spacing_m is not None
        and authority.config.profile_spacing_m > authority.source_profile_spacing_m
    ):
        raise RealTerrainMinimumAltitudeError("configured profile spacing exceeds retained source authority.")
    for output, prepared, source_record in zip(
        result.route_results,
        authority.prepared_routes,
        authority.source_routes,
    ):
        if not isinstance(prepared, RealTerrainMinimumAltitudePreparedRouteSnapshot):
            raise RealTerrainMinimumAltitudeError("prepared route authority type is invalid.")
        if (
            output.route_id != source_record.route_id
            or output.mode is not source_record.mode
            or output.source_order != prepared.source_order
            or source_record.source_order != output.source_order
            or not _near(output.source_total_distance_3d_m, source_record.source_total_distance_3d_m, tolerance)
            or not _near(output.route_polyline_total_distance_2d_m, prepared.route_polyline_total_distance_2d_m, tolerance)
            or output.frequency_hz != authority.frequency_hz
            or output.allowed_flight_agl_m != authority.allowed_flight_agl_m
            or not _near(output.actual_launch_ground_msl_m, authority.launch_ground_msl_m, tolerance)
            or not _near(output.profile_spacing_m, resolved_spacing, tolerance)
        ):
            raise RealTerrainMinimumAltitudeError("output route/source authority parity failed.")
        if len(output.route_samples) != len(prepared.samples):
            raise RealTerrainMinimumAltitudeError("output route sample count does not match prepared authority.")
        if (
            sum(sample.is_snapped_target_endpoint for sample in output.route_samples) != 1
            or not output.route_samples[-1].is_snapped_target_endpoint
        ):
            raise RealTerrainMinimumAltitudeError("output route target endpoint policy is invalid.")
        for output_sample, prepared_sample in zip(output.route_samples, prepared.samples):
            if (
                output_sample.route_sample_id != prepared_sample.route_sample_id
                or output_sample.route_sample_mgrs != prepared_sample.route_sample_mgrs
                or output_sample.route_sample_index != prepared_sample.route_sample_index
                or not _near(output_sample.cumulative_route_distance_2d_m, prepared_sample.cumulative_route_distance_2d_m, tolerance)
                or not _near(output_sample.local_dem_msl_m, prepared_sample.local_dem_msl_m, tolerance)
                or not _near(output_sample.local_dsm_msl_m, prepared_sample.local_dsm_msl_m, tolerance)
                or output_sample.is_snapped_target_endpoint != prepared_sample.is_snapped_target_endpoint
            ):
                raise RealTerrainMinimumAltitudeError("output route sample/prepared authority parity failed.")
            _validate_emitted_radial_requirements(output, output_sample, prepared_sample, authority, authority.config)


def _expected_snapshot_requirements(
    item: RealTerrainMinimumAltitudePreparedSampleSnapshot,
    authority: RealTerrainMinimumAltitudeAuthoritySnapshot,
    config: RealTerrainMinimumAltitudeConfig,
) -> tuple[RealTerrainRadialRequirementSample, ...]:
    profile = item.radial_profile
    if profile is None:
        return ()
    wavelength = wavelength_m(authority.frequency_hz)
    antenna = authority.launch_ground_msl_m + authority.allowed_flight_agl_m
    expected: list[RealTerrainRadialRequirementSample] = []
    for profile_sample in profile.samples:
        total = profile_sample.distance_from_start_m + profile_sample.distance_to_end_m
        ratio = profile_sample.distance_from_start_m / total
        if ratio <= config.epsilon_m:
            continue
        radius = first_fresnel_radius_m(
            wavelength_m=wavelength,
            d1_m=profile_sample.distance_from_start_m,
            d2_m=profile_sample.distance_to_end_m,
        )
        clearance = config.required_fresnel_clearance_ratio * radius
        los = profile_sample.dsm_msl_m + clearance
        endpoint = antenna + (los - antenna) / ratio
        expected.append(
            RealTerrainRadialRequirementSample(
                f"{item.route_sample_id}-radial-{profile_sample.sample_index:03d}",
                item.route_sample_id,
                profile_sample.sample_index,
                profile_sample.distance_from_start_m,
                profile_sample.distance_to_end_m,
                ratio,
                profile_sample.dem_msl_m,
                profile_sample.dsm_msl_m,
                radius,
                clearance,
                los,
                endpoint,
            )
        )
    return tuple(expected)


def _validate_emitted_radial_requirements(
    route: RealTerrainRouteMinimumAltitudeResult,
    output: RealTerrainRouteAltitudeSample,
    prepared: RealTerrainMinimumAltitudePreparedSampleSnapshot,
    authority: RealTerrainMinimumAltitudeAuthoritySnapshot,
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    if prepared.radial_profile is None:
        if output.radial_requirement_samples or output.limiting_radial_requirement is not None:
            raise RealTerrainMinimumAltitudeError("coincident output has unexpected radial requirements.")
        return
    expected = _expected_snapshot_requirements(prepared, authority, config)
    actual = output.radial_requirement_samples
    if len(actual) != len(expected):
        raise RealTerrainMinimumAltitudeError("emitted radial requirement count does not match snapshot.")
    names = (
        "radial_requirement_id",
        "route_sample_id",
        "radial_sample_index",
        "distance_from_launch_m",
        "distance_to_endpoint_m",
        "path_ratio",
        "dem_msl_m",
        "dsm_msl_m",
        "fresnel_radius_m",
        "required_clearance_m",
        "required_los_msl_m",
        "required_endpoint_msl_m",
    )
    for actual_item, expected_item in zip(actual, expected):
        for name in names:
            actual_value = getattr(actual_item, name)
            expected_value = getattr(expected_item, name)
            if isinstance(expected_value, float):
                if not _near(actual_value, expected_value, config.distance_tolerance_m):
                    raise RealTerrainMinimumAltitudeError("emitted radial requirement does not match snapshot calculation.")
            elif actual_value != expected_value:
                raise RealTerrainMinimumAltitudeError("emitted radial requirement identity does not match snapshot.")
    expected_required, expected_limiter = _select_radial_extreme(
        expected, config.distance_tolerance_m
    )
    if output.limiting_radial_requirement != expected_limiter:
        raise RealTerrainMinimumAltitudeError("emitted radial limiter does not match snapshot calculation.")
    if output.required_endpoint_msl_m != expected_required:
        raise RealTerrainMinimumAltitudeError("emitted endpoint requirement does not match snapshot calculation.")


def _validate_prepared_authority(
    route_result: RealTerrainRouteResult,
    selected_launch_site: SelectedLaunchSiteRecord,
    prepared_routes: tuple[PreparedRealTerrainRoute, ...],
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    if type(prepared_routes) is not tuple or not prepared_routes:
        raise RealTerrainMinimumAltitudeError("prepared_routes must be a non-empty tuple.")
    if len(prepared_routes) > config.max_routes:
        raise RealTerrainMinimumAltitudeError("prepared route count violates resource guard.")
    if len(route_result.route_candidates) != len(prepared_routes):
        raise RealTerrainMinimumAltitudeError("prepared route count does not match source routes.")
    sample_ids: set[str] = set()
    for expected_order, (route, source) in enumerate(zip(prepared_routes, route_result.route_candidates)):
        if type(route) is not PreparedRealTerrainRoute:
            raise RealTerrainMinimumAltitudeError("prepared route must use PreparedRealTerrainRoute.")
        route.__post_init__()
        if route.source_order != expected_order or route.source_order != expected_order:
            raise RealTerrainMinimumAltitudeError("prepared route source order mismatch.")
        _validate_exact_terrain_metadata(route.terrain_metadata, "prepared")
        if route.terrain_metadata != route_result.terrain_metadata:
            raise RealTerrainMinimumAltitudeError("prepared terrain metadata does not match route authority.")
        if route.route_id != source.route_id or route.mode is not source.mode:
            raise RealTerrainMinimumAltitudeError("prepared route identity does not match source route authority.")
        if not _near(route.source_total_distance_3d_m, source.total_distance_3d_m, config.distance_tolerance_m):
            raise RealTerrainMinimumAltitudeError("prepared source 3D total does not match source route authority.")
        _validate_route_geometry(
            route,
            route_result,
            selected_launch_site,
            config,
            route_result.config.profile_spacing_m,
        )
        current_ids = tuple(sample.route_sample_id for sample in route.samples)
        if len(set(current_ids)) != len(current_ids) or sample_ids.intersection(current_ids):
            raise RealTerrainMinimumAltitudeError("prepared sample IDs must be globally unique.")
        sample_ids.update(current_ids)


def _validate_route_geometry(
    route: PreparedRealTerrainRoute,
    route_result: RealTerrainRouteResult,
    selected_launch_site: SelectedLaunchSiteRecord,
    config: RealTerrainMinimumAltitudeConfig,
    source_profile_spacing_m: float,
) -> None:
    tolerance = config.distance_tolerance_m
    expected_cumulative = 0.0
    for index, sample in enumerate(route.samples):
        sample.__post_init__()
        _validate_local_point(sample.projected_point, "prepared route sample")
        if sample.route_sample_id != f"{route.route_id}-sample-{index:03d}":
            raise RealTerrainMinimumAltitudeError("prepared route sample IDs are not deterministic.")
        if index:
            expected_cumulative += distance_2d_m(route.samples[index - 1].projected_point, sample.projected_point)
        if not _near(sample.cumulative_route_distance_2d_m, expected_cumulative, tolerance):
            raise RealTerrainMinimumAltitudeError("prepared cumulative route 2D distance does not match projected geometry.")
        expected_radial = distance_2d_m(selected_launch_site.projected_point, sample.projected_point)
        if not _near(sample.radial_distance_2d_m, expected_radial, tolerance):
            raise RealTerrainMinimumAltitudeError("prepared radial distance does not match selected launch geometry.")
    if not _near(route.route_polyline_total_distance_2d_m, expected_cumulative, tolerance):
        raise RealTerrainMinimumAltitudeError("prepared route 2D total does not match projected geometry.")
    targets = tuple(sample for sample in route.samples if sample.is_snapped_target_endpoint)
    if len(targets) != 1 or targets[0] is not route.samples[-1]:
        raise RealTerrainMinimumAltitudeError("prepared route must have exactly one final target endpoint.")
    if route.samples[0].route_sample_mgrs != route_result.snapped_launch_node_mgrs:
        raise RealTerrainMinimumAltitudeError("prepared first sample MGRS does not match snapped launch authority.")
    if route.samples[-1].route_sample_mgrs != route_result.snapped_target_node_mgrs:
        raise RealTerrainMinimumAltitudeError("prepared final sample MGRS does not match snapped target authority.")
    for sample in route.samples:
        _validate_sample_profile(
            sample,
            selected_launch_site,
            route_result,
            config,
            source_profile_spacing_m,
        )


def _validate_sample_profile(
    item: PreparedRealTerrainRouteSample,
    selected_launch_site: SelectedLaunchSiteRecord,
    route_result: RealTerrainRouteResult,
    config: RealTerrainMinimumAltitudeConfig,
    source_profile_spacing_m: float,
) -> None:
    tolerance = config.distance_tolerance_m
    launch_ground = route_result.launch_ground_msl_m
    launch_antenna = launch_ground + route_result.config.allowed_flight_agl_m
    recomputed_radial_distance = distance_2d_m(
        selected_launch_site.projected_point, item.projected_point
    )
    if not _near(item.radial_distance_2d_m, recomputed_radial_distance, tolerance):
        raise RealTerrainMinimumAltitudeError("prepared radial distance does not match selected launch geometry.")
    if recomputed_radial_distance <= tolerance:
        if item.radial_profile is not None:
            raise RealTerrainMinimumAltitudeError("coincident prepared sample must not contain a radial profile.")
        if not _near(item.local_dem_msl_m, launch_ground, tolerance):
            raise RealTerrainMinimumAltitudeError("coincident prepared sample DEM does not match launch ground.")
        if item.local_dsm_msl_m > launch_antenna + tolerance:
            raise RealTerrainMinimumAltitudeError("coincident prepared sample DSM exceeds launch antenna MSL.")
        return
    if item.radial_profile is None:
        raise RealTerrainMinimumAltitudeError("noncoincident prepared sample requires a radial profile.")
    _validate_terrain_profile(
        item.radial_profile,
        item,
        selected_launch_site,
        launch_ground,
        launch_antenna,
        config,
        source_profile_spacing_m,
    )


def _validate_terrain_profile(
    profile: TerrainProfile,
    item: PreparedRealTerrainRouteSample,
    selected_launch_site: SelectedLaunchSiteRecord,
    launch_ground: float,
    launch_antenna: float,
    config: RealTerrainMinimumAltitudeConfig,
    source_profile_spacing_m: float,
) -> None:
    tolerance = config.distance_tolerance_m
    if type(profile) is not TerrainProfile or type(profile.start) is not LocalPoint or type(profile.end) is not LocalPoint:
        raise RealTerrainMinimumAltitudeError("prepared radial profile type is invalid.")
    _validate_local_point(profile.start, "prepared radial profile start")
    _validate_local_point(profile.end, "prepared radial profile end")
    if not isinstance(profile.sample_spacing_m, (int, float)) or isinstance(profile.sample_spacing_m, bool) or not isfinite(profile.sample_spacing_m) or profile.sample_spacing_m <= 0.0:
        raise RealTerrainMinimumAltitudeError("prepared radial profile spacing is invalid.")
    resolved_spacing = config.profile_spacing_m or source_profile_spacing_m
    if not _near(profile.sample_spacing_m, resolved_spacing, tolerance):
        raise RealTerrainMinimumAltitudeError("prepared radial profile spacing does not match resolved spacing.")
    if profile.start != selected_launch_site.projected_point or profile.end != item.projected_point:
        raise RealTerrainMinimumAltitudeError("prepared radial profile start/end does not match authority.")
    total = distance_2d_m(profile.start, profile.end)
    if not _near(total, item.radial_distance_2d_m, tolerance):
        raise RealTerrainMinimumAltitudeError("prepared radial profile total does not match radial distance.")
    if type(profile.samples) is not tuple or not profile.samples:
        raise RealTerrainMinimumAltitudeError("prepared radial profile samples must be a non-empty tuple.")
    previous_from = -1.0
    previous_to = float("inf")
    for sample in profile.samples:
        if type(sample) is not TerrainProfileSample:
            raise RealTerrainMinimumAltitudeError("prepared radial profile sample type is invalid.")
        if (
            sample.distance_from_start_m <= previous_from
            or sample.distance_to_end_m >= previous_to
        ):
            raise RealTerrainMinimumAltitudeError("prepared radial profile sample order is invalid.")
        previous_from, previous_to = sample.distance_from_start_m, sample.distance_to_end_m
    if tuple(sample.sample_index for sample in profile.samples) != tuple(range(len(profile.samples))):
        raise RealTerrainMinimumAltitudeError("prepared radial profile sample indexes are not contiguous.")
    first = profile.samples[0]
    last = profile.samples[-1]
    if first.point != profile.start or not _near(first.distance_from_start_m, 0.0, tolerance) or not _near(first.dem_msl, launch_ground, tolerance) or first.dsm_msl > launch_antenna + tolerance:
        raise RealTerrainMinimumAltitudeError("prepared radial profile launch endpoint parity failed.")
    if last.point != profile.end or not _near(last.distance_to_end_m, 0.0, tolerance) or not _near(last.dem_msl, item.local_dem_msl_m, tolerance) or not _near(last.dsm_msl, item.local_dsm_msl_m, tolerance):
        raise RealTerrainMinimumAltitudeError("prepared radial profile route endpoint parity failed.")
    has_eligible = False
    for sample in profile.samples:
        if type(sample) is not TerrainProfileSample or type(sample.point) is not LocalPoint:
            raise RealTerrainMinimumAltitudeError("prepared radial profile sample type is invalid.")
        _validate_local_point(sample.point, "prepared radial profile sample")
        _validate_finite_values("prepared radial profile sample", sample.distance_from_start_m, sample.distance_to_end_m, sample.dem_msl, sample.dsm_msl, sample.surface_delta_m)
        if sample.distance_from_start_m < 0.0 or sample.distance_to_end_m < 0.0 or sample.dsm_msl < sample.dem_msl:
            raise RealTerrainMinimumAltitudeError("prepared radial profile terrain values are invalid.")
        if not _near(sample.distance_from_start_m + sample.distance_to_end_m, total, tolerance):
            raise RealTerrainMinimumAltitudeError("prepared radial profile sample distance parity failed.")
        ratio = sample.distance_from_start_m / total
        if not 0.0 <= ratio <= 1.0:
            raise RealTerrainMinimumAltitudeError("prepared radial profile path ratio is invalid.")
        expected_point = LocalPoint(
            profile.start.x_m + (profile.end.x_m - profile.start.x_m) * ratio,
            profile.start.y_m + (profile.end.y_m - profile.start.y_m) * ratio,
            profile.start.z_m + (profile.end.z_m - profile.start.z_m) * ratio,
        )
        if not _points_within_tolerance(sample.point, expected_point, tolerance):
            raise RealTerrainMinimumAltitudeError("prepared radial profile interpolation parity failed.")
        has_eligible = has_eligible or ratio > config.epsilon_m
    if not has_eligible:
        raise RealTerrainMinimumAltitudeError("prepared radial profile has no eligible path ratio sample.")


def _enforce_resource_guards(
    prepared_routes: tuple[PreparedRealTerrainRoute, ...],
    config: RealTerrainMinimumAltitudeConfig,
) -> None:
    if type(prepared_routes) is not tuple or not prepared_routes:
        raise RealTerrainMinimumAltitudeError("prepared_routes must be a non-empty tuple.")
    if len(prepared_routes) > config.max_routes:
        raise RealTerrainMinimumAltitudeError("prepared route count violates resource guard.")
    total_profile_samples = 0
    for route in prepared_routes:
        if type(route) is not PreparedRealTerrainRoute or type(route.samples) is not tuple:
            raise RealTerrainMinimumAltitudeError("prepared route outer type is invalid.")
        if len(route.samples) > config.max_route_samples:
            raise RealTerrainMinimumAltitudeError("route sample count violates resource guard.")
        for sample in route.samples:
            if type(sample) is not PreparedRealTerrainRouteSample:
                raise RealTerrainMinimumAltitudeError("prepared sample outer type is invalid.")
            if sample.radial_profile is not None:
                if type(sample.radial_profile) is not TerrainProfile or type(sample.radial_profile.samples) is not tuple:
                    raise RealTerrainMinimumAltitudeError("prepared profile outer type is invalid.")
                count = len(sample.radial_profile.samples)
                if count > config.max_profile_samples_per_link:
                    raise RealTerrainMinimumAltitudeError("profile sample count violates resource guard.")
                total_profile_samples += count
    if total_profile_samples > config.max_total_profile_samples:
        raise RealTerrainMinimumAltitudeError("total profile sample count violates resource guard.")


def _compute_route(
    route: PreparedRealTerrainRoute,
    *,
    launch_point: LocalPoint,
    launch_ground: float,
    launch_antenna: float,
    allowed_agl: float,
    frequency: float,
    profile_spacing_m: float,
    config: RealTerrainMinimumAltitudeConfig,
) -> RealTerrainRouteMinimumAltitudeResult:
    samples = tuple(
        _compute_sample(item, launch_point, launch_ground, launch_antenna, allowed_agl, frequency, config)
        for item in route.samples
    )
    msl, max_sample = _select_constant_msl_extreme(samples, config.distance_tolerance_m)
    minimum_margin, deficit_sample = _select_current_margin_extreme(
        samples, config.distance_tolerance_m
    )
    highest_dem = max(item.local_dem_msl_m for item in samples)
    target = samples[-1].local_dem_msl_m
    agl_high = _nonnegative(msl - highest_dem, config.distance_tolerance_m)
    agl_target = _nonnegative(msl - target, config.distance_tolerance_m)
    warnings: list[str] = []
    if minimum_margin < -config.distance_tolerance_m:
        warnings.append(f"{route.route_id}: current fixed-AGL route is below the configured clearance proxy at one or more route samples.")
    if max_sample.is_snapped_target_endpoint:
        warnings.append(f"{route.route_id}: constant-MSL limiting sample is the snapped target endpoint.")
    if deficit_sample.is_snapped_target_endpoint:
        warnings.append(f"{route.route_id}: current-AGL deficit-limiting sample is the snapped target endpoint.")
    return RealTerrainRouteMinimumAltitudeResult(
        route.route_id, route.mode, route.source_order, route.source_total_distance_3d_m,
        route.route_polyline_total_distance_2d_m, frequency,
        config.required_fresnel_clearance_ratio, profile_spacing_m, launch_ground,
        launch_antenna, allowed_agl, msl, highest_dem, target, agl_high, agl_target,
        max_sample.route_sample_id, minimum_margin,
        minimum_margin >= -config.distance_tolerance_m,
        deficit_sample.route_sample_id, samples, tuple(warnings),
    )


def _compute_sample(
    item: PreparedRealTerrainRouteSample,
    launch_point: LocalPoint,
    launch_ground: float,
    launch_antenna: float,
    allowed_agl: float,
    frequency: float,
    config: RealTerrainMinimumAltitudeConfig,
) -> RealTerrainRouteAltitudeSample:
    recomputed_radial_distance = distance_2d_m(launch_point, item.projected_point)
    if not _near(
        item.radial_distance_2d_m,
        recomputed_radial_distance,
        config.distance_tolerance_m,
    ):
        raise RealTerrainMinimumAltitudeError("prepared radial distance does not match launch geometry.")
    if recomputed_radial_distance <= config.distance_tolerance_m:
        if item.radial_profile is not None or abs(item.local_dem_msl_m - launch_ground) > config.distance_tolerance_m or item.local_dsm_msl_m > launch_antenna + config.distance_tolerance_m:
            raise RealTerrainMinimumAltitudeError("coincident launch evidence is invalid.")
        required = launch_antenna
        requirements: tuple[RealTerrainRadialRequirementSample, ...] = ()
        limiting = None
        semantics = "coincident_launch_occupancy"
    else:
        if item.radial_profile is None:
            raise RealTerrainMinimumAltitudeError("nonzero radial evidence requires a profile.")
        requirements = _requirements(item, launch_antenna, frequency, config)
        if not requirements:
            raise RealTerrainMinimumAltitudeError("radial profile has no eligible path ratio sample.")
        required, limiting = _select_radial_extreme(requirements, config.distance_tolerance_m)
        semantics = "radial_profile_proxy"
    current = item.local_dem_msl_m + allowed_agl
    return RealTerrainRouteAltitudeSample(
        item.route_sample_id, item.route_id, item.mode, item.route_sample_index,
        item.route_sample_mgrs, item.cumulative_route_distance_2d_m,
        item.local_dem_msl_m, item.local_dsm_msl_m, current, required,
        current - required, requirements, limiting, semantics,
        item.is_snapped_target_endpoint,
    )


def _requirements(
    item: PreparedRealTerrainRouteSample,
    antenna: float,
    frequency: float,
    config: RealTerrainMinimumAltitudeConfig,
) -> tuple[RealTerrainRadialRequirementSample, ...]:
    if item.radial_profile is None:
        raise RealTerrainMinimumAltitudeError("nonzero radial evidence requires a profile.")
    result: list[RealTerrainRadialRequirementSample] = []
    wavelength = wavelength_m(frequency)
    for sample in item.radial_profile.samples:
        total = sample.distance_from_start_m + sample.distance_to_end_m
        if total <= 0.0:
            raise RealTerrainMinimumAltitudeError("radial profile total distance must be positive.")
        ratio = sample.distance_from_start_m / total
        if ratio <= config.epsilon_m:
            continue
        radius = first_fresnel_radius_m(wavelength_m=wavelength, d1_m=sample.distance_from_start_m, d2_m=sample.distance_to_end_m)
        clearance = config.required_fresnel_clearance_ratio * radius
        los = sample.dsm_msl + clearance
        endpoint = antenna + (los - antenna) / ratio
        if not isfinite(endpoint):
            raise RealTerrainMinimumAltitudeError("radial requirement is non-finite.")
        result.append(
            RealTerrainRadialRequirementSample(
                f"{item.route_sample_id}-radial-{sample.sample_index:03d}",
                item.route_sample_id, sample.sample_index, sample.distance_from_start_m,
                sample.distance_to_end_m, ratio, sample.dem_msl, sample.dsm_msl,
                radius, clearance, los, endpoint,
            )
        )
    return tuple(result)


def _select_radial_limiter(
    requirements: tuple[RealTerrainRadialRequirementSample, ...], tolerance: float
) -> RealTerrainRadialRequirementSample:
    return _select_radial_extreme(requirements, tolerance)[1]


def _select_radial_extreme(
    requirements: tuple[RealTerrainRadialRequirementSample, ...], tolerance: float
) -> tuple[float, RealTerrainRadialRequirementSample]:
    try:
        return select_tolerance_representative(
            requirements,
            value=lambda item: item.required_endpoint_msl_m,
            tie_key=lambda item: item.radial_sample_index,
            tolerance=tolerance,
            maximize=True,
        )
    except MinimumAltitudeSelectionError as exc:
        raise RealTerrainMinimumAltitudeError("radial limiter selection is invalid.") from exc


def _select_constant_msl_limiter(
    samples: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float
) -> RealTerrainRouteAltitudeSample:
    return _select_constant_msl_extreme(samples, tolerance)[1]


def _select_constant_msl_extreme(
    samples: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float
) -> tuple[float, RealTerrainRouteAltitudeSample]:
    try:
        return select_tolerance_representative(
            samples,
            value=lambda item: item.required_endpoint_msl_m,
            tie_key=lambda item: (
                item.cumulative_route_distance_2d_m,
                item.route_sample_index,
                _radial_index(item),
            ),
            tolerance=tolerance,
            maximize=True,
        )
    except MinimumAltitudeSelectionError as exc:
        raise RealTerrainMinimumAltitudeError("constant-MSL limiter selection is invalid.") from exc


def _select_current_margin_limiter(
    samples: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float
) -> RealTerrainRouteAltitudeSample:
    return _select_current_margin_extreme(samples, tolerance)[1]


def _select_current_margin_extreme(
    samples: tuple[RealTerrainRouteAltitudeSample, ...], tolerance: float
) -> tuple[float, RealTerrainRouteAltitudeSample]:
    try:
        return select_tolerance_representative(
            samples,
            value=lambda item: item.current_clearance_margin_m,
            tie_key=lambda item: (item.cumulative_route_distance_2d_m, item.route_sample_index),
            tolerance=tolerance,
            maximize=False,
        )
    except MinimumAltitudeSelectionError as exc:
        raise RealTerrainMinimumAltitudeError("current-margin limiter selection is invalid.") from exc


def _radial_index(sample: RealTerrainRouteAltitudeSample) -> int:
    return -1 if sample.limiting_radial_requirement is None else sample.limiting_radial_requirement.radial_sample_index


def _validate_finite_values(name: str, *values: object) -> None:
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) for value in values):
        raise RealTerrainMinimumAltitudeError(f"{name} must be finite numeric.")


def _validate_local_point(point: LocalPoint, name: str) -> None:
    if type(point) is not LocalPoint:
        raise RealTerrainMinimumAltitudeError(f"{name} point must be LocalPoint.")
    _validate_finite_values(f"{name} point", point.x_m, point.y_m, point.z_m)


def _points_within_tolerance(left: LocalPoint, right: LocalPoint, tolerance: float) -> bool:
    _validate_local_point(left, "left")
    _validate_local_point(right, "right")
    _validate_finite_values("point tolerance", tolerance)
    return _near(left.x_m, right.x_m, tolerance) and _near(left.y_m, right.y_m, tolerance) and _near(left.z_m, right.z_m, tolerance)


def _near(left: float, right: float, tolerance: float) -> bool:
    _validate_finite_values("near comparison", left, right, tolerance)
    return float(tolerance) >= 0.0 and abs(float(left) - float(right)) <= float(tolerance)


def _nonnegative(value: float, tolerance: float) -> float:
    if value < -tolerance:
        raise RealTerrainMinimumAltitudeError("AGL invariant is negative beyond tolerance.")
    return 0.0 if abs(value) <= tolerance else value
