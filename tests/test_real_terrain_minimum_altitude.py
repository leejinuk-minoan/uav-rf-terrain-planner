from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import permutations
from math import inf, nextafter, sqrt

import pytest

from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.fresnel import wavelength_m
from uav_rf_terrain.launch_site_selection import SelectedLaunchSiteRecord
from uav_rf_terrain.profile import TerrainProfile, TerrainProfileSample
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
from uav_rf_terrain.real_terrain_minimum_altitude import (
    PreparedRealTerrainRoute,
    PreparedRealTerrainRouteSample,
    RealTerrainMinimumAltitudeError,
    compute_real_terrain_minimum_altitude,
    validate_complete_real_terrain_minimum_altitude_result,
)
from uav_rf_terrain.real_terrain_minimum_altitude_outputs import (
    RealTerrainMinimumAltitudeConfig,
    RealTerrainMinimumAltitudeOutputError,
    validate_real_terrain_minimum_altitude_result,
)
from uav_rf_terrain.real_terrain_route_outputs import (
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
)
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.terrain_data import (
    RASTER_TYPE_DEM,
    RASTER_TYPE_DSM,
    TerrainDatasetMetadata,
    TerrainRasterMetadata,
)


LAUNCH_MGRS = "52SCB0000000000"
TARGET_MGRS = "52SCB0001000000"
LAUNCH_POINT = LocalPoint(0.0, 0.0)
TARGET_POINT = LocalPoint(10.0, 0.0)


def _metadata() -> TerrainDatasetMetadata:
    common = dict(
        source_dataset_name="test",
        source_provider="test",
        license_or_terms="test",
        crs="EPSG:5179",
        resolution_m=10.0,
        width=2,
        height=1,
        bounds=(0.0, 0.0, 10.0, 0.0),
        nodata_value=None,
        vertical_datum="MSL",
        processing_summary="test",
        is_synthetic=True,
        is_redistributable_processed_data=True,
    )
    return TerrainDatasetMetadata(
        "altitude-test",
        TerrainRasterMetadata("dem", RASTER_TYPE_DEM, **common),
        TerrainRasterMetadata("dsm", RASTER_TYPE_DSM, **common),
        "2026-07-20",
        "pytest",
        "aligned",
        "synthetic prepared-evidence fixture",
    )


def _selected_launch() -> SelectedLaunchSiteRecord:
    return SelectedLaunchSiteRecord(
        candidate_id="candidate-001",
        launch_site_mgrs=LAUNCH_MGRS,
        external_coordinate_format="MGRS",
        user_coordinate_field="launch_site_mgrs",
        projected_point=LAUNCH_POINT,
        color_class=ColorClass.GREEN,
        overall_score=90.0,
        shielding_stability_score=90.0,
        distance_3d_m=0.0,
        candidate_reason="synthetic selectable launch",
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="source-zone provider not requested",
        fresnel_diagnostics=None,
    )


def _route_result(
    modes: tuple[RouteMode, ...] = (RouteMode.SHIELDING_MINIMUM,),
) -> RealTerrainRouteResult:
    metadata = _metadata()
    nodes = (
        RealTerrainRouteNode(
            "node-launch", 0, 0, LAUNCH_POINT, LAUNCH_MGRS, 100.0, 100.0,
            20.0, 120.0, 0.0, True, RouteNodeState.VALID_SCORED, True,
            "valid scored", 90.0, 90.0, ColorClass.GREEN, None,
            SourceZoneAvailability.NOT_REQUESTED, None,
            "source-zone provider not requested", None,
        ),
        RealTerrainRouteNode(
            "node-target", 0, 1, TARGET_POINT, TARGET_MGRS, 120.0, 120.0,
            20.0, 140.0, 10.0, True, RouteNodeState.VALID_SCORED, True,
            "valid scored", 90.0, 90.0, ColorClass.GREEN, None,
            SourceZoneAvailability.NOT_REQUESTED, None,
            "source-zone provider not requested", None,
        ),
    )
    path = (
        RealTerrainRoutePathPoint(0, LAUNCH_MGRS, 120.0),
        RealTerrainRoutePathPoint(1, TARGET_MGRS, 140.0),
    )
    candidates = tuple(
        RealTerrainRouteCandidate(
            route_id=f"route-{mode.value}", mode=mode, path=path,
            total_cost=10.0, total_distance_3d_m=10.0,
            mean_shielding_stability_score=90.0,
            minimum_shielding_stability_score=90.0,
            ordered_node_ids=(nodes[0].node_id, nodes[1].node_id),
            ordered_projected_points=(LAUNCH_POINT, TARGET_POINT),
            shared_edge_ratios=tuple(0.0 for _ in range(index)),
        )
        for index, mode in enumerate(modes)
    )
    handoffs = tuple(
        (
            WaypointHandoffPoint(
                f"route-{mode.value}-handoff-000", LAUNCH_POINT, LAUNCH_MGRS,
                0.0, 100.0, 100.0, 20.0, 120.0, ColorClass.GREEN, 90.0,
                90.0, None, SourceZoneAvailability.NOT_REQUESTED, None,
                "source-zone provider not requested",
            ),
            WaypointHandoffPoint(
                f"route-{mode.value}-handoff-001", TARGET_POINT, TARGET_MGRS,
                10.0, 120.0, 120.0, 20.0, 140.0, ColorClass.GREEN, 90.0,
                90.0, None, SourceZoneAvailability.NOT_REQUESTED, None,
                "source-zone provider not requested",
            ),
        )
        for mode in modes
    )
    return RealTerrainRouteResult(
        scenario_name="altitude-test", mission_id="altitude-test",
        selected_candidate_id="candidate-001", launch_site_mgrs=LAUNCH_MGRS,
        target_mgrs=TARGET_MGRS, route_candidates=candidates, warnings=(),
        config=RealTerrainRouteConfig(10.0, 10.0, 20.0, 300_000_000.0, 1.0),
        terrain_metadata=metadata, graph_nodes=nodes,
        graph_edges=(RealTerrainRouteEdge("node-launch", "node-target", 10.0, 1.0, 1.0, 0.0),),
        summary=RealTerrainRouteSummary(2, 1, 2, len(candidates)),
        waypoint_handoffs=handoffs, launch_ground_msl_m=100.0,
        snapped_launch_node_id="node-launch", snapped_target_node_id="node-target",
        snapped_launch_node_mgrs=LAUNCH_MGRS,
        snapped_target_node_mgrs=TARGET_MGRS,
        launch_snap_distance_m=0.0, target_snap_distance_m=0.0,
    )


def _profile(
    end: LocalPoint = TARGET_POINT,
    *,
    endpoint_dem_msl: float = 120.0,
    endpoint_dsm_msl: float | None = None,
    spacing_m: float = 10.0,
    middle_dsm_msl: float | None = None,
) -> TerrainProfile:
    distance = end.x_m
    end_dsm = endpoint_dem_msl if endpoint_dsm_msl is None else endpoint_dsm_msl
    samples = [
        TerrainProfileSample(0, 0, 0, LAUNCH_POINT, 0.0, distance, 100.0, 100.0, 0.0)
    ]
    if middle_dsm_msl is not None:
        middle = LocalPoint(distance / 2.0, 0.0)
        samples.append(
            TerrainProfileSample(1, 1, 0, middle, distance / 2.0, distance / 2.0, 100.0, middle_dsm_msl, middle_dsm_msl - 100.0)
        )
        end_index = 2
    else:
        end_index = 1
    samples.append(
        TerrainProfileSample(end_index, 2, 0, end, distance, 0.0, endpoint_dem_msl, end_dsm, end_dsm - endpoint_dem_msl)
    )
    return TerrainProfile("prepared", LAUNCH_POINT, end, spacing_m, tuple(samples))


def _prepared_route(
    route_result: RealTerrainRouteResult,
    mode: RouteMode = RouteMode.SHIELDING_MINIMUM,
    *,
    target_profile: TerrainProfile | None = None,
) -> PreparedRealTerrainRoute:
    profile = target_profile or _profile()
    route_id = f"route-{mode.value}"
    return PreparedRealTerrainRoute(
        route_id=route_id,
        mode=mode,
        source_order=tuple(RouteMode).index(mode),
        source_total_distance_3d_m=10.0,
        route_polyline_total_distance_2d_m=10.0,
        terrain_metadata=route_result.terrain_metadata,
        samples=(
            PreparedRealTerrainRouteSample(
                f"{route_id}-sample-000", route_id, mode, 0, LAUNCH_MGRS,
                LAUNCH_POINT, 0.0, 100.0, 100.0, False, 0.0, None,
            ),
            PreparedRealTerrainRouteSample(
                f"{route_id}-sample-001", route_id, mode, 1, TARGET_MGRS,
                TARGET_POINT, 10.0, 120.0, 120.0, True, 10.0, profile,
            ),
        ),
    )


def _compute(
    route_result: RealTerrainRouteResult | None = None,
    prepared_routes: tuple[PreparedRealTerrainRoute, ...] | None = None,
    config: RealTerrainMinimumAltitudeConfig | None = None,
):
    source = _route_result() if route_result is None else route_result
    routes = (_prepared_route(source),) if prepared_routes is None else prepared_routes
    return compute_real_terrain_minimum_altitude(
        route_result=source,
        selected_launch_site=_selected_launch(),
        prepared_routes=routes,
        config=RealTerrainMinimumAltitudeConfig(expected_frequency_hz=300_000_000.0) if config is None else config,
    )


def test_pure_engine_uses_real_source_contract_and_hand_calculated_endpoint_requirement() -> None:
    result = _compute()
    route = result.route_results[0]
    assert route.minimum_required_constant_route_msl_m == pytest.approx(120.0)
    assert route.route_samples[1].current_clearance_margin_m == pytest.approx(20.0)


@dataclass(frozen=True)
class _FakeSource:
    config: object
    launch_ground_msl_m: float
    selected_candidate_id: str
    launch_site_mgrs: str
    target_mgrs: str
    terrain_metadata: object


def test_engine_rejects_duck_typed_route_source_before_fresnel_work() -> None:
    real = _route_result()
    fake = _FakeSource(
        real.config, real.launch_ground_msl_m, real.selected_candidate_id,
        real.launch_site_mgrs, real.target_mgrs, real.terrain_metadata,
    )
    with pytest.raises(RealTerrainMinimumAltitudeError, match="RealTerrainRouteResult"):
        compute_real_terrain_minimum_altitude(
            route_result=fake,
            selected_launch_site=_selected_launch(),
            prepared_routes=(_prepared_route(real),),
            config=RealTerrainMinimumAltitudeConfig(),
        )


def test_engine_rejects_unrelated_radial_profile_before_fresnel_work() -> None:
    route_result = _route_result()
    unrelated = _profile(LocalPoint(20.0, 0.0), endpoint_dem_msl=120.0, spacing_m=10.0)
    prepared = _prepared_route(route_result, target_profile=unrelated)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="profile"):
        _compute(route_result, (prepared,))


def test_engine_rejects_stored_route_distance_not_recomputed_from_points() -> None:
    route_result = _route_result()
    prepared = _prepared_route(route_result)
    malformed = replace(prepared, route_polyline_total_distance_2d_m=9.0)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="2D"):
        _compute(route_result, (malformed,))


def test_engine_rejects_mutated_selected_launch_before_calculation() -> None:
    selected = _selected_launch()
    object.__setattr__(selected, "projected_point", "not-a-point")
    route_result = _route_result()
    with pytest.raises(RealTerrainMinimumAltitudeError, match="selected"):
        compute_real_terrain_minimum_altitude(
            route_result=route_result,
            selected_launch_site=selected,
            prepared_routes=(_prepared_route(route_result),),
            config=RealTerrainMinimumAltitudeConfig(),
        )


def test_tolerance_aware_radial_tie_prefers_lower_radial_index() -> None:
    # wavelength = 1 m, q = 0.6; at 5 m / 5 m radius=sqrt(2.5).
    # The middle and endpoint inversion values are both exactly 121 m.
    middle_dsm = 120.5 - 0.6 * sqrt(wavelength_m(300_000_000.0) * 2.5)
    route_result = _route_result()
    profile = _profile(endpoint_dsm_msl=121.0, middle_dsm_msl=middle_dsm)
    prepared = _prepared_route(route_result, target_profile=profile)
    endpoint = replace(prepared.samples[-1], local_dsm_msl_m=121.0)
    prepared = replace(prepared, samples=(prepared.samples[0], endpoint))
    result = _compute(route_result, (prepared,))
    limiter = result.route_results[0].route_samples[1].limiting_radial_requirement
    assert limiter is not None
    assert limiter.radial_sample_index == 1


def test_nonzero_evidence_requires_profile() -> None:
    route_result = _route_result()
    prepared = _prepared_route(route_result)
    target = replace(prepared.samples[-1], radial_profile=None)
    with pytest.raises(RealTerrainMinimumAltitudeError):
        _compute(route_result, (replace(prepared, samples=(prepared.samples[0], target)),))


def test_engine_rejects_default_profile_spacing_mismatch() -> None:
    route_result = _route_result()
    profile = _profile(spacing_m=5.0)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="spacing"):
        _compute(route_result, (_prepared_route(route_result, target_profile=profile),))


def test_result_recursive_validator_rejects_nested_formula_mutation() -> None:
    result = _compute()
    route = result.route_results[0]
    sample = route.route_samples[1]
    corrupted_sample = replace(sample, required_endpoint_msl_m=121.0)
    corrupted_route = replace(route, route_samples=(route.route_samples[0], corrupted_sample))
    with pytest.raises(RealTerrainMinimumAltitudeOutputError, match="formula"):
        replace(result, route_results=(corrupted_route,))


def test_result_public_output_retains_status_and_omits_private_geometry() -> None:
    public = _compute().to_public_dict()
    route = public["routes"][0]
    assert route["source_total_distance_3d_m"] == pytest.approx(10.0)
    assert route["route_polyline_total_distance_2d_m"] == pytest.approx(10.0)
    assert route["constant_msl_limiting_sample_mgrs"] == LAUNCH_MGRS
    assert route["current_agl_deficit_limiting_sample_mgrs"] == LAUNCH_MGRS
    assert "x_m" not in str(public)
    assert "TerrainProfile" not in str(public)


@pytest.mark.parametrize("modes", ((RouteMode.SHIELDING_MINIMUM,), tuple(RouteMode)[:2], tuple(RouteMode)))
def test_engine_preserves_one_two_and_three_route_source_order(
    modes: tuple[RouteMode, ...],
) -> None:
    route_result = _route_result(modes)
    prepared = tuple(_prepared_route(route_result, mode) for mode in modes)
    result = _compute(route_result, prepared)
    assert [route.mode for route in result.route_results] == list(modes)
    assert result.summary.route_count == len(modes)
    assert result.summary.route_sample_count == 2 * len(modes)


def test_engine_reruns_nested_route_candidate_validator_after_direct_mutation() -> None:
    route_result = _route_result()
    object.__setattr__(route_result.route_candidates[0], "total_cost", -1.0)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="source or prepared"):
        _compute(route_result)


def test_resource_guard_fails_before_fresnel_calculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    calls: list[float] = []
    monkeypatch.setattr(altitude, "wavelength_m", lambda frequency: calls.append(frequency) or 1.0)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="profile sample count"):
        _compute(config=RealTerrainMinimumAltitudeConfig(max_profile_samples_per_link=1))
    assert not calls


def test_fresnel_error_is_mapped_to_engine_typed_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude
    from uav_rf_terrain.fresnel import FresnelAnalysisError

    monkeypatch.setattr(
        altitude,
        "wavelength_m",
        lambda frequency: (_ for _ in ()).throw(FresnelAnalysisError("fixture failure")),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError, match="minimum-altitude calculation"):
        _compute()


def test_result_rejects_coordinated_source_authority_mutation() -> None:
    from uav_rf_terrain.real_terrain_minimum_altitude_outputs import (
        RealTerrainMinimumAltitudeSourceRoute,
    )

    result = _compute()
    object.__setattr__(
        result._authority,
        "source_routes",
        (
            RealTerrainMinimumAltitudeSourceRoute(
                "route-shielding_minimum", RouteMode.SHIELDING_MINIMUM, 0, 11.0
            ),
        ),
    )
    with pytest.raises(RealTerrainMinimumAltitudeOutputError, match="source authority"):
        result.__post_init__()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_id", "candidate-other"),
        ("launch_site_mgrs", TARGET_MGRS),
    ),
)
def test_complete_result_validator_rejects_selected_authority_mutation(
    field: str, value: str
) -> None:
    result = _compute()
    authority_field = "selected_candidate_id" if field == "candidate_id" else field
    object.__setattr__(result._authority, authority_field, value)
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_result_validator_rejects_prepared_profile_geometry_mutation() -> None:
    result = _compute()
    prepared = result._authority.prepared_routes[0]
    malformed_sample = replace(
        prepared.samples[-1], projected_point=LocalPoint(11.0, 0.0)
    )
    object.__setattr__(
        result._authority,
        "prepared_routes",
        (replace(prepared, samples=(prepared.samples[0], malformed_sample)),),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_result_validator_rejects_list_substitution() -> None:
    result = _compute()
    object.__setattr__(result, "route_results", [result.route_results[0]])
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_validator_rejects_nonfinite_selected_geometry() -> None:
    result = _compute()
    object.__setattr__(result._authority, "selected_projected_point", LocalPoint(float("nan"), 0.0))
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_validator_rejects_noninterpolated_profile_sample_geometry() -> None:
    route_result = _route_result()
    result = _compute(
        route_result,
        (_prepared_route(route_result, target_profile=_profile(middle_dsm_msl=120.0)),),
    )
    prepared = result._authority.prepared_routes[0]
    profile = prepared.samples[-1].radial_profile
    assert profile is not None
    malformed_middle = replace(profile.samples[1], point=LocalPoint(7.0, 0.0))
    malformed_profile = replace(profile, samples=(profile.samples[0], malformed_middle, profile.samples[-1]))
    malformed_sample = replace(prepared.samples[-1], radial_profile=malformed_profile)
    object.__setattr__(result._authority, "prepared_routes", (replace(prepared, samples=(prepared.samples[0], malformed_sample)),))
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda result: object.__setattr__(result._authority, "frequency_hz", 310_000_000.0), "output route/source"),
        (lambda result: object.__setattr__(result._authority, "resolved_profile_spacing_m", 11.0), "spacing"),
        (lambda result: object.__setattr__(result._authority, "launch_ground_msl_m", 101.0), "output route/source"),
        (lambda result: object.__setattr__(result._authority, "terrain_metadata", "not-metadata"), "terrain metadata"),
        (lambda result: object.__setattr__(result._authority.prepared_routes[0].samples[-1], "local_dem_msl_m", 121.0), "output route sample"),
        (lambda result: object.__setattr__(result._authority.prepared_routes[0].samples[-1].radial_profile.samples[-1], "dsm_msl_m", 121.0), "endpoint parity"),
        (lambda result: object.__setattr__(result.route_results[0], "constant_msl_limiting_sample_id", "wrong"), "constant-MSL"),
        (lambda result: object.__setattr__(result.summary, "route_count", 2), "summary count"),
    ),
)
def test_complete_validator_rejects_authority_and_output_mutations(
    mutation, message: str
) -> None:
    result = _compute()
    mutation(result)
    assert message
    with pytest.raises((RealTerrainMinimumAltitudeError, RealTerrainMinimumAltitudeOutputError)):
        validate_complete_real_terrain_minimum_altitude_result(result)


@pytest.mark.parametrize(
    ("target", "field"),
    (
        ("prepared", "samples"),
        ("profile", "samples"),
        ("route", "route_samples"),
        ("sample", "radial_requirement_samples"),
        ("result", "warnings"),
        ("summary", "warnings"),
    ),
)
def test_complete_validator_rejects_list_substitution_for_immutable_collections(
    target: str, field: str
) -> None:
    result = _compute()
    route = result.route_results[0]
    sample = route.route_samples[-1]
    targets = {
        "prepared": result._authority.prepared_routes[0],
        "profile": result._authority.prepared_routes[0].samples[-1].radial_profile,
        "route": route,
        "sample": sample,
        "result": result,
        "summary": result.summary,
    }
    target_object = targets[target]
    assert target_object is not None
    object.__setattr__(target_object, field, list(getattr(target_object, field)))
    with pytest.raises((RealTerrainMinimumAltitudeError, RealTerrainMinimumAltitudeOutputError)):
        validate_complete_real_terrain_minimum_altitude_result(result)


@pytest.mark.parametrize("coordinate", (float("nan"), float("inf"), True))
@pytest.mark.parametrize("field", ("x_m", "y_m", "z_m"))
def test_complete_validator_rejects_nonfinite_or_bool_local_point_components(
    field: str, coordinate: object
) -> None:
    result = _compute()
    point = result._authority.selected_projected_point
    values = {"x_m": point.x_m, "y_m": point.y_m, "z_m": point.z_m}
    values[field] = coordinate
    object.__setattr__(
        result._authority,
        "selected_projected_point",
        LocalPoint(**values),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


@pytest.mark.parametrize("authority", ("source", "prepared", "profile_start", "profile_end", "profile_sample"))
def test_complete_validator_rejects_authority_geometry_mutations(authority: str) -> None:
    result = _compute()
    prepared = result._authority.prepared_routes[0]
    profile = prepared.samples[-1].radial_profile
    assert profile is not None
    if authority == "source":
        object.__setattr__(result._authority, "selected_projected_point", LocalPoint(1.0, 0.0))
    elif authority == "prepared":
        object.__setattr__(prepared.samples[-1], "projected_point", LocalPoint(11.0, 0.0))
    elif authority == "profile_start":
        object.__setattr__(profile, "start", LocalPoint(1.0, 0.0))
    elif authority == "profile_end":
        object.__setattr__(profile, "end", LocalPoint(11.0, 0.0))
    else:
        object.__setattr__(profile.samples[-1], "point", LocalPoint(9.0, 0.0))
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_validator_rejects_coordinated_public_and_private_mutation() -> None:
    result = _compute()
    object.__setattr__(result._authority, "selected_candidate_id", "candidate-other")
    object.__setattr__(result, "selected_candidate_id", "candidate-other")
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_public_output_does_not_expose_private_authority() -> None:
    public = _compute().to_public_dict()
    rendered = repr(public)
    for forbidden in ("_authority", "LocalPoint", "TerrainDatasetMetadata"):
        assert forbidden not in rendered


def test_complete_validator_uses_independent_snapshot_after_caller_alias_attack() -> None:
    route_result = _route_result()
    selected = _selected_launch()
    prepared = _prepared_route(route_result)
    result = compute_real_terrain_minimum_altitude(
        route_result=route_result,
        selected_launch_site=selected,
        prepared_routes=(prepared,),
        config=RealTerrainMinimumAltitudeConfig(expected_frequency_hz=300_000_000.0),
    )
    object.__setattr__(selected, "projected_point", LocalPoint(1.0, 0.0))
    object.__setattr__(prepared.samples[-1], "projected_point", LocalPoint(11.0, 0.0))
    object.__setattr__(
        route_result.route_candidates[0],
        "ordered_projected_points",
        (LocalPoint(1.0, 0.0), TARGET_POINT),
    )
    validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_validator_requires_exact_frequency_not_distance_tolerance() -> None:
    result = _compute(config=RealTerrainMinimumAltitudeConfig(expected_frequency_hz=300_000_000.0, distance_tolerance_m=1e-6))
    object.__setattr__(result.route_results[0], "frequency_hz", nextafter(300_000_000.0, inf))
    with pytest.raises(RealTerrainMinimumAltitudeError, match="emitted output"):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_engine_rejects_shuffled_or_duplicate_profile_order() -> None:
    route_result = _route_result()
    profile = _profile(middle_dsm_msl=120.0)
    shuffled = replace(profile, samples=(profile.samples[0], profile.samples[-1], profile.samples[1]))
    with pytest.raises(RealTerrainMinimumAltitudeError, match="order"):
        _compute(route_result, (_prepared_route(route_result, target_profile=shuffled),))
    duplicate = replace(
        profile,
        samples=(profile.samples[0], replace(profile.samples[1], distance_from_start_m=0.0, distance_to_end_m=10.0), profile.samples[-1]),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError, match="order"):
        _compute(route_result, (_prepared_route(route_result, target_profile=duplicate),))


def test_complete_validator_recomputes_radial_requirements_from_snapshot() -> None:
    result = _compute()
    route = result.route_results[0]
    sample = route.route_samples[-1]
    radial = sample.limiting_radial_requirement
    assert radial is not None
    changed = replace(
        radial,
        dsm_msl_m=121.0,
        required_los_msl_m=121.0 + radial.required_clearance_m,
        required_endpoint_msl_m=121.0 + radial.required_clearance_m,
    )
    changed_sample = replace(
        sample,
        radial_requirement_samples=(changed,),
        limiting_radial_requirement=changed,
        required_endpoint_msl_m=changed.required_endpoint_msl_m,
        current_route_flight_msl_m=121.0,
        current_clearance_margin_m=121.0 - changed.required_endpoint_msl_m,
    )
    changed_route = replace(
        route,
        route_samples=(route.route_samples[0], changed_sample),
        minimum_required_constant_route_msl_m=changed.required_endpoint_msl_m,
        constant_msl_limiting_sample_id=changed_sample.route_sample_id,
        minimum_current_clearance_margin_m=changed_sample.current_clearance_margin_m,
        current_agl_deficit_limiting_sample_id=changed_sample.route_sample_id,
        allowed_flight_agl_m=21.0,
        warnings=(f"{route.route_id}: constant-MSL limiting sample is the snapped target endpoint.", f"{route.route_id}: current-AGL deficit-limiting sample is the snapped target endpoint."),
    )
    object.__setattr__(result, "route_results", (changed_route,))
    object.__setattr__(result, "warnings", changed_route.warnings)
    object.__setattr__(result, "summary", replace(result.summary, warnings=changed_route.warnings))
    with pytest.raises((RealTerrainMinimumAltitudeError, RealTerrainMinimumAltitudeOutputError)):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_calculation_uses_reviewed_clearance_ratio_boundaries() -> None:
    route_result = _route_result()
    prepared = (_prepared_route(route_result, target_profile=_profile(middle_dsm_msl=121.0)),)
    values = {
        ratio: _compute(route_result, prepared, RealTerrainMinimumAltitudeConfig(expected_frequency_hz=300_000_000.0, required_fresnel_clearance_ratio=ratio)).route_results[0].minimum_required_constant_route_msl_m
        for ratio in (0.0, 0.6, 1.0)
    }
    assert values[0.0] == pytest.approx(122.0)
    radius = sqrt(wavelength_m(300_000_000.0) * 2.5)
    assert values[0.6] == pytest.approx(122.0 + 1.2 * radius)
    assert values[1.0] == pytest.approx(122.0 + 2.0 * radius)


@pytest.mark.parametrize(("distance", "expected_count"), ((0.005, 1), (0.01, 1), (0.02, 2)))
def test_epsilon_eligibility_and_endpoint_fresnel_zero(distance: float, expected_count: int) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    route_result = _route_result()
    end = TARGET_POINT
    profile = TerrainProfile(
        "prepared",
        LAUNCH_POINT,
        end,
        10.0,
        (
            TerrainProfileSample(0, 0, 0, LAUNCH_POINT, 0.0, 10.0, 100.0, 100.0, 0.0),
            TerrainProfileSample(1, 1, 0, LocalPoint(distance, 0.0), distance, 10.0 - distance, 100.0, 100.0, 0.0),
            TerrainProfileSample(2, 2, 0, end, 10.0, 0.0, 120.0, 120.0, 0.0),
        ),
    )
    item = replace(_prepared_route(route_result).samples[-1], radial_profile=profile)
    requirements = altitude._requirements(item, 120.0, 300_000_000.0, RealTerrainMinimumAltitudeConfig(epsilon_m=1e-3))
    assert len(requirements) == expected_count
    assert requirements[-1].path_ratio == pytest.approx(1.0)
    assert requirements[-1].fresnel_radius_m == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("delta", "expected_index"),
    ((5e-10, 0), (1e-9, 0), (2e-9, 1)),
)
def test_radial_limiter_tolerance_and_reversed_order(delta: float, expected_index: int) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    radial = _compute().route_results[0].route_samples[-1].radial_requirement_samples[0]
    lower = replace(radial, radial_sample_index=0, required_endpoint_msl_m=0.0)
    higher = replace(radial, radial_sample_index=1, required_endpoint_msl_m=delta)
    assert altitude._select_radial_limiter((higher, lower), 1e-9).radial_sample_index == expected_index


@pytest.mark.parametrize(
    ("delta", "expected_index"),
    ((5e-10, 0), (1e-9, 0), (2e-9, 1)),
)
def test_route_limiters_tolerance_and_reversed_order(delta: float, expected_index: int) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    route = _compute().route_results[0]
    first = replace(route.route_samples[0], route_sample_index=0, cumulative_route_distance_2d_m=0.0, required_endpoint_msl_m=0.0, current_clearance_margin_m=0.0)
    second = replace(route.route_samples[1], route_sample_index=1, cumulative_route_distance_2d_m=10.0, required_endpoint_msl_m=delta, current_clearance_margin_m=-delta)
    assert altitude._select_constant_msl_limiter((second, first), 1e-9).route_sample_index == expected_index
    assert altitude._select_current_margin_limiter((second, first), 1e-9).route_sample_index == expected_index


def test_constant_and_current_margin_limiters_can_differ() -> None:
    result = _compute()
    route = result.route_results[0]
    first = replace(route.route_samples[0], required_endpoint_msl_m=130.0, current_clearance_margin_m=10.0)
    second = replace(route.route_samples[1], required_endpoint_msl_m=120.0, current_clearance_margin_m=-10.0)
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    assert altitude._select_constant_msl_limiter((first, second), 1e-9).route_sample_index == 0
    assert altitude._select_current_margin_limiter((first, second), 1e-9).route_sample_index == 1


@pytest.mark.parametrize("mutator", ("dem", "dsm", "point", "profile"))
def test_coincident_occupancy_contract_rejects_each_invalid_variant(mutator: str) -> None:
    route_result = _route_result()
    prepared = _prepared_route(route_result)
    first = prepared.samples[0]
    if mutator == "dem":
        first = replace(first, local_dem_msl_m=101.0, local_dsm_msl_m=101.0)
    elif mutator == "dsm":
        first = replace(first, local_dsm_msl_m=121.0)
    elif mutator == "point":
        first = replace(first, projected_point=LocalPoint(1.0, 0.0))
    else:
        first = replace(first, radial_profile=_profile())
    with pytest.raises(RealTerrainMinimumAltitudeError):
        _compute(route_result, (replace(prepared, samples=(first, prepared.samples[-1])),))


@pytest.mark.parametrize(
    ("config", "message"),
    (
        (RealTerrainMinimumAltitudeConfig(max_routes=1), "route count"),
        (RealTerrainMinimumAltitudeConfig(max_route_samples=1), "route sample count"),
        (RealTerrainMinimumAltitudeConfig(max_profile_samples_per_link=1), "profile sample count"),
        (RealTerrainMinimumAltitudeConfig(max_total_profile_samples=1), "total profile sample count"),
    ),
)
def test_all_resource_guards_run_before_fresnel(
    monkeypatch: pytest.MonkeyPatch, config: RealTerrainMinimumAltitudeConfig, message: str
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    calls: list[float] = []
    monkeypatch.setattr(altitude, "wavelength_m", lambda frequency: calls.append(frequency) or 1.0)
    route_result = _route_result(tuple(RouteMode)[:2]) if config.max_routes == 1 else _route_result()
    prepared = tuple(_prepared_route(route_result, mode) for mode in tuple(RouteMode)[:2]) if config.max_routes == 1 else (_prepared_route(route_result),)
    with pytest.raises(RealTerrainMinimumAltitudeError, match=message):
        _compute(route_result, prepared, config)
    assert not calls


@pytest.mark.parametrize("target", ("candidate", "prepared", "output"))
def test_wrong_nested_types_map_to_typed_minimum_altitude_error(target: str) -> None:
    if target == "candidate":
        route_result = _route_result()
        object.__setattr__(route_result, "route_candidates", (object(),))
        with pytest.raises(RealTerrainMinimumAltitudeError):
            _compute(route_result)
        return
    if target == "prepared":
        route_result = _route_result()
        with pytest.raises(RealTerrainMinimumAltitudeError):
            _compute(route_result, (object(),))
        return
    result = _compute()
    object.__setattr__(result, "route_results", (object(),))
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_canonical_fingerprint_rejects_config_mutation() -> None:
    result = _compute()
    object.__setattr__(result._authority.config, "max_total_profile_samples", 1)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="fingerprint"):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_emitted_output_fingerprint_rejects_subtolerance_direct_and_coordinated_mutation() -> None:
    result = _compute(config=RealTerrainMinimumAltitudeConfig(distance_tolerance_m=1e-6))
    route = result.route_results[0]
    object.__setattr__(route, "minimum_required_constant_route_msl_m", route.minimum_required_constant_route_msl_m + 1e-9)
    with pytest.raises(RealTerrainMinimumAltitudeError, match="emitted output"):
        validate_complete_real_terrain_minimum_altitude_result(result)

    result = _compute(config=RealTerrainMinimumAltitudeConfig(distance_tolerance_m=1e-6))
    route = result.route_results[0]
    sample = route.route_samples[-1]
    radial = sample.limiting_radial_requirement
    assert radial is not None
    changed_radial = replace(radial, required_endpoint_msl_m=radial.required_endpoint_msl_m + 1e-9)
    changed_sample = replace(sample, radial_requirement_samples=(changed_radial,), limiting_radial_requirement=changed_radial, required_endpoint_msl_m=changed_radial.required_endpoint_msl_m)
    changed_route = replace(route, route_samples=(route.route_samples[0], changed_sample), minimum_required_constant_route_msl_m=changed_radial.required_endpoint_msl_m)
    object.__setattr__(result, "route_results", (changed_route,))
    with pytest.raises(RealTerrainMinimumAltitudeError, match="emitted output"):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_output_target_flag_and_coordinated_warning_mutation_is_rejected() -> None:
    result = _compute()
    route = result.route_results[0]
    first, last = route.route_samples
    changed_first = replace(first, is_snapped_target_endpoint=True)
    changed_last = replace(last, is_snapped_target_endpoint=False)
    warnings = (f"{route.route_id}: current fixed-AGL route is below the configured clearance proxy at one or more route samples.",)
    changed_route = replace(route, route_samples=(changed_first, changed_last), warnings=warnings)
    object.__setattr__(result, "route_results", (changed_route,))
    object.__setattr__(result, "warnings", warnings)
    object.__setattr__(result, "summary", replace(result.summary, warnings=warnings))
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_prepared_metadata_requires_exact_reviewed_type() -> None:
    route_result = _route_result()
    prepared = _prepared_route(route_result)
    object.__setattr__(prepared, "terrain_metadata", object())
    with pytest.raises(RealTerrainMinimumAltitudeError, match="metadata"):
        _compute(route_result, (prepared,))


def test_no_eligible_radial_profile_is_fatal() -> None:
    route_result = _route_result()
    profile = TerrainProfile(
        "prepared", LAUNCH_POINT, TARGET_POINT, 10.0,
        (
            TerrainProfileSample(0, 0, 0, LAUNCH_POINT, 0.0, 10.0, 100.0, 100.0, 0.0),
            TerrainProfileSample(1, 1, 0, LocalPoint(5.0, 0.0), 5.0, 5.0, 110.0, 110.0, 0.0),
            TerrainProfileSample(2, 2, 0, TARGET_POINT, 10.0, 0.0, 120.0, 120.0, 0.0),
        ),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError):
        _compute(route_result, (_prepared_route(route_result, target_profile=profile),), RealTerrainMinimumAltitudeConfig(epsilon_m=1.0))


def test_oversized_profile_guard_precedes_profile_sample_traversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    route_result = _route_result()
    prepared = _prepared_route(route_result)
    monkeypatch.setattr(
        altitude,
        "_validate_terrain_profile",
        lambda *_: (_ for _ in ()).throw(AssertionError("profile samples must not be traversed before guard")),
    )
    monkeypatch.setattr(altitude, "wavelength_m", lambda _: (_ for _ in ()).throw(AssertionError("Fresnel called")))
    with pytest.raises(RealTerrainMinimumAltitudeError, match="profile sample count"):
        _compute(route_result, (prepared,), RealTerrainMinimumAltitudeConfig(max_profile_samples_per_link=1))


@pytest.mark.parametrize("mutation", ("resolution", "provider", "nested_type"))
def test_complete_validator_revalidates_exact_nested_raster_metadata_before_seals(
    mutation: str,
) -> None:
    result = _compute()
    metadata = result._authority.terrain_metadata
    if mutation == "resolution":
        object.__setattr__(metadata.dem, "resolution_m", 0.0)
    elif mutation == "provider":
        object.__setattr__(metadata.dsm, "source_provider", "")
    else:
        object.__setattr__(metadata, "dem", object())
    with pytest.raises(RealTerrainMinimumAltitudeError, match="terrain metadata"):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_source_collection_guard_precedes_deep_source_traversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    route_result = _route_result()
    object.__setattr__(route_result.config, "max_graph_nodes", 1)
    monkeypatch.setattr(
        altitude,
        "_validate_local_point",
        lambda *_: (_ for _ in ()).throw(AssertionError("deep source validation ran")),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError, match="source graph node count"):
        _compute(route_result)


@pytest.mark.parametrize("ordered_indices", tuple(permutations((0, 1, 2))))
def test_each_limiter_separates_exact_extreme_from_canonical_representative(
    ordered_indices: tuple[int, int, int],
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    tolerance = 1.0
    values = (0.0, 0.75, 1.5)
    radial_base = _compute().route_results[0].route_samples[-1].radial_requirement_samples[0]
    radial_items = tuple(
        replace(radial_base, radial_sample_index=index, required_endpoint_msl_m=values[index])
        for index in ordered_indices
    )
    radial_extreme, radial_limiter = altitude._select_radial_extreme(radial_items, tolerance)
    assert radial_extreme == 1.5
    assert radial_limiter.radial_sample_index == 1

    sample_base = _compute().route_results[0].route_samples[-1]
    route_items = tuple(
        replace(
            sample_base,
            route_sample_index=index,
            cumulative_route_distance_2d_m=float(index),
            required_endpoint_msl_m=values[index],
            current_clearance_margin_m=-values[index],
        )
        for index in ordered_indices
    )
    constant_extreme, constant_limiter = altitude._select_constant_msl_extreme(route_items, tolerance)
    margin_extreme, margin_limiter = altitude._select_current_margin_extreme(route_items, tolerance)
    assert constant_extreme == 1.5
    assert constant_limiter.route_sample_index == 1
    assert margin_extreme == -1.5
    assert margin_limiter.route_sample_index == 1


def test_subtolerance_xy_coincidence_ignores_z_and_requires_no_profile() -> None:
    route_result = _route_result()
    prepared = _prepared_route(route_result)
    first = replace(
        prepared.samples[0],
        projected_point=LocalPoint(0.0005, 0.0, 999.0),
        radial_distance_2d_m=0.0005,
        radial_profile=None,
    )
    result = _compute(
        route_result,
        (replace(prepared, samples=(first, prepared.samples[-1])),),
        RealTerrainMinimumAltitudeConfig(
            expected_frequency_hz=300_000_000.0,
            distance_tolerance_m=0.001,
        ),
    )
    assert result.route_results[0].route_samples[0].sample_semantics == "coincident_launch_occupancy"


@pytest.mark.parametrize("field", ("path", "ordered_node_ids", "ordered_projected_points", "handoff"))
def test_source_route_local_collection_guards_run_before_fresnel(
    monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    route_result = _route_result()
    candidate = route_result.route_candidates[0]
    if field == "handoff":
        object.__setattr__(route_result, "waypoint_handoffs", (route_result.waypoint_handoffs[0][:-1],))
    else:
        object.__setattr__(candidate, field, getattr(candidate, field)[:-1])
    monkeypatch.setattr(
        altitude,
        "wavelength_m",
        lambda _: (_ for _ in ()).throw(AssertionError("Fresnel work must not run")),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError, match="route-local collection lengths"):
        _compute(route_result)


def test_equal_length_source_route_local_collections_cannot_exceed_graph_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    route_result = _route_result()
    candidate = route_result.route_candidates[0]
    handoff = route_result.waypoint_handoffs[0]
    object.__setattr__(candidate, "path", candidate.path + (candidate.path[-1],))
    object.__setattr__(candidate, "ordered_node_ids", candidate.ordered_node_ids + ("node-extra",))
    object.__setattr__(candidate, "ordered_projected_points", candidate.ordered_projected_points + (TARGET_POINT,))
    object.__setattr__(route_result, "waypoint_handoffs", (handoff + (handoff[-1],),))
    monkeypatch.setattr(
        altitude,
        "wavelength_m",
        lambda _: (_ for _ in ()).throw(AssertionError("Fresnel work must not run")),
    )
    with pytest.raises(RealTerrainMinimumAltitudeError, match="route-local length violates graph guard"):
        _compute(route_result)


def test_public_output_includes_limiter_semantics_and_distance_tolerance() -> None:
    result = _compute(config=RealTerrainMinimumAltitudeConfig(distance_tolerance_m=0.25))
    public = result.to_public_dict()
    assert public["distance_tolerance_m"] == 0.25
    assert public["limiter_semantics"] == "canonical_extreme_tolerance_representative"


def test_route_result_uses_exact_minimum_for_status_and_canonical_representative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uav_rf_terrain.real_terrain_minimum_altitude as altitude

    prepared = _prepared_route(_route_result())
    first, target = _compute().route_results[0].route_samples
    synthetic_samples = iter(
        (
            replace(
                first,
                required_endpoint_msl_m=140.75,
                current_route_flight_msl_m=140.0,
                current_clearance_margin_m=-0.75,
            ),
            replace(
                target,
                required_endpoint_msl_m=141.5,
                current_route_flight_msl_m=140.0,
                current_clearance_margin_m=-1.5,
            ),
        )
    )
    monkeypatch.setattr(altitude, "_compute_sample", lambda *_: next(synthetic_samples))
    route = altitude._compute_route(
        prepared,
        launch_point=LAUNCH_POINT,
        launch_ground=100.0,
        launch_antenna=120.0,
        allowed_agl=20.0,
        frequency=300_000_000.0,
        profile_spacing_m=10.0,
        config=RealTerrainMinimumAltitudeConfig(distance_tolerance_m=1.0),
    )
    assert route.minimum_required_constant_route_msl_m == 141.5
    assert route.constant_msl_limiting_sample_id == first.route_sample_id
    assert route.minimum_current_clearance_margin_m == -1.5
    assert route.current_agl_deficit_limiting_sample_id == first.route_sample_id
    assert not route.current_fixed_agl_meets_proxy
    assert route.warnings == (
        "route-shielding_minimum: current fixed-AGL route is below the configured clearance proxy at one or more route samples.",
    )


@pytest.mark.parametrize("mutation", ("authority", "config", "route_sample", "radial"))
def test_complete_and_output_validators_preflight_exact_nested_types(
    mutation: str,
) -> None:
    result = _compute()
    if mutation == "authority":
        object.__setattr__(result, "_authority", object())
        with pytest.raises(RealTerrainMinimumAltitudeError):
            validate_complete_real_terrain_minimum_altitude_result(result)
        return
    if mutation == "config":
        object.__setattr__(result._authority, "config", object())
    elif mutation == "route_sample":
        route = result.route_results[0]
        object.__setattr__(route, "route_samples", (object(),))
    else:
        sample = result.route_results[0].route_samples[-1]
        object.__setattr__(sample, "radial_requirement_samples", (object(),))
    with pytest.raises(RealTerrainMinimumAltitudeOutputError):
        validate_real_terrain_minimum_altitude_result(result)


@pytest.mark.parametrize("mutation", ("metadata_name", "metadata_bounds", "warnings", "handoff_reason"))
def test_source_and_metadata_malformed_nested_values_map_to_engine_error(mutation: str) -> None:
    route_result = _route_result()
    if mutation == "metadata_name":
        object.__setattr__(route_result.terrain_metadata.dem, "name", object())
    elif mutation == "metadata_bounds":
        object.__setattr__(route_result.terrain_metadata.dem, "bounds", object())
    elif mutation == "warnings":
        object.__setattr__(route_result, "warnings", ([],))
    else:
        object.__setattr__(route_result.waypoint_handoffs[0][0], "source_zone_reason", object())
    with pytest.raises(RealTerrainMinimumAltitudeError):
        _compute(route_result)


@pytest.mark.parametrize("field", ("name", "bounds"))
def test_complete_and_output_validators_normalize_mutated_metadata_primitives(field: str) -> None:
    result = _compute()
    object.__setattr__(
        result._authority.terrain_metadata.dem,
        field,
        object(),
    )
    with pytest.raises(RealTerrainMinimumAltitudeOutputError):
        validate_real_terrain_minimum_altitude_result(result)
    with pytest.raises(RealTerrainMinimumAltitudeError):
        validate_complete_real_terrain_minimum_altitude_result(result)


def test_complete_and_output_validation_accept_exact_extreme_with_distinct_canonical_limiter() -> None:
    route_result = _route_result()
    profile = _profile(endpoint_dsm_msl=120.5)
    prepared = _prepared_route(route_result, target_profile=profile)
    target = replace(prepared.samples[-1], local_dsm_msl_m=120.5)
    result = _compute(
        route_result,
        (replace(prepared, samples=(prepared.samples[0], target)),),
        RealTerrainMinimumAltitudeConfig(
            expected_frequency_hz=300_000_000.0,
            distance_tolerance_m=1.0,
        ),
    )
    route = result.route_results[0]
    assert route.minimum_required_constant_route_msl_m == 120.5
    assert route.constant_msl_limiting_sample_id == route.route_samples[0].route_sample_id
    validate_real_terrain_minimum_altitude_result(result)
    validate_complete_real_terrain_minimum_altitude_result(result)
