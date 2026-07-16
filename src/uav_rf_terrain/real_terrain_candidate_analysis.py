"""Real-terrain candidate analysis with session-backed terrain sampling."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from enum import StrEnum
from math import ceil, isfinite
from typing import Protocol, cast

from .classification import ClassificationError, classification_reason, classify_candidate_score
from .coordinates import LocalPoint, distance_2d_m, distance_3d_m
from .fresnel import FresnelAnalysisError, analyze_dsm_fresnel
from .fresnel_diagnostics import CandidateFresnelDiagnostics, candidate_fresnel_diagnostics_from_analysis
from .grid import CandidateCell, CandidateGridConfig, generate_candidate_grid
from .los import LineOfSightAnalysis, LineOfSightError, analyze_dsm_los
from .map_outputs import MapStyle, style_for_color_class
from .profile import TerrainProfile, TerrainProfileError, TerrainProfileSample, local_point_to_metadata_grid_index
from .schemas import ColorClass
from .scoring import CandidateScore, ScoringError, compute_candidate_score
from .source_zones import TerrainSourceZone, is_source_sensitive_zone
from .terrain_data import (
    TerrainDataAdapter,
    TerrainDataError,
    TerrainDatasetMetadata,
    TerrainNoDataError,
    TerrainPointOutsideError,
    TerrainPointSample,
    validate_public_safe_label,
)


class RealTerrainLaunchAreaAnalysisError(ValueError):
    """Raised when the configuration, target, or terrain session is invalid."""


class CandidateAnalysisState(StrEnum):
    VALID_SCORED = "valid_scored"
    OUTSIDE_OPERATING_RADIUS = "outside_operating_radius"
    OUTSIDE_RASTER_EXTENT = "outside_raster_extent"
    TERRAIN_NODATA = "terrain_nodata"
    LAUNCH_SURFACE_OBSTRUCTED = "launch_surface_obstructed"
    COINCIDENT_WITH_TARGET = "coincident_with_target"
    PROFILE_UNAVAILABLE = "profile_unavailable"
    ANALYSIS_INVALID = "analysis_invalid"


class SourceZoneAvailability(StrEnum):
    AVAILABLE = "available"
    NOT_REQUESTED = "not_requested"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class SourceZoneBatchProvider(Protocol):
    def __call__(self, points: Sequence[LocalPoint]) -> Sequence[TerrainSourceZone]: ...


class TerrainAnalysisSession(Protocol):
    metadata: TerrainDatasetMetadata

    def sample_point(self, point: LocalPoint) -> TerrainPointSample: ...

    def extract_profile(
        self,
        start: LocalPoint,
        end: LocalPoint,
        *,
        sample_spacing_m: float,
        scenario_name: str,
    ) -> TerrainProfile: ...


@dataclass(frozen=True)
class RealTerrainLaunchAreaConfig:
    scenario_name: str
    target_point: LocalPoint
    operating_radius_m: float
    candidate_spacing_m: float
    allowed_agl_m: float
    frequency_hz: float
    profile_sample_spacing_m: float | None = None
    launch_antenna_height_agl_m: float = 0.0
    include_center: bool = False
    include_out_of_radius: bool = True
    max_candidate_count: int = 2_500
    max_profile_samples_per_candidate: int = 512
    max_total_profile_samples: int = 250_000

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_name, str) or not self.scenario_name.strip():
            raise RealTerrainLaunchAreaAnalysisError("scenario_name must be non-empty.")
        try:
            validate_public_safe_label(self.scenario_name)
        except TerrainDataError as exc:
            raise RealTerrainLaunchAreaAnalysisError(
                "scenario_name must not include private local paths."
            ) from exc
        if not isinstance(self.target_point, LocalPoint):
            raise RealTerrainLaunchAreaAnalysisError("target_point must be LocalPoint.")
        _finite("target_point.x_m", self.target_point.x_m)
        _finite("target_point.y_m", self.target_point.y_m)
        if self.target_point.z_m != 0.0:
            raise RealTerrainLaunchAreaAnalysisError("target_point.z_m must be 0.0.")
        _positive("operating_radius_m", self.operating_radius_m)
        _positive("candidate_spacing_m", self.candidate_spacing_m)
        if self.candidate_spacing_m > self.operating_radius_m:
            raise RealTerrainLaunchAreaAnalysisError(
                "candidate_spacing_m must not exceed operating_radius_m."
            )
        _positive("allowed_agl_m", self.allowed_agl_m)
        _positive("frequency_hz", self.frequency_hz)
        if self.profile_sample_spacing_m is not None:
            _positive("profile_sample_spacing_m", self.profile_sample_spacing_m)
        if (
            isinstance(self.launch_antenna_height_agl_m, bool)
            or not isfinite(self.launch_antenna_height_agl_m)
            or self.launch_antenna_height_agl_m < 0
        ):
            raise RealTerrainLaunchAreaAnalysisError(
                "launch_antenna_height_agl_m must be finite and non-negative."
            )
        if not isinstance(self.include_center, bool) or not isinstance(
            self.include_out_of_radius, bool
        ):
            raise RealTerrainLaunchAreaAnalysisError(
                "include_center and include_out_of_radius must be bool."
            )
        for name, value in (
            ("max_candidate_count", self.max_candidate_count),
            ("max_profile_samples_per_candidate", self.max_profile_samples_per_candidate),
            ("max_total_profile_samples", self.max_total_profile_samples),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise RealTerrainLaunchAreaAnalysisError(f"{name} must be a positive integer.")


@dataclass(frozen=True)
class CandidateAnalysisRecord:
    candidate_id: str
    candidate_point: LocalPoint
    sampled_cell_center: LocalPoint | None
    state: CandidateAnalysisState
    reason: str
    distance_2d_m: float
    distance_3d_m: float | None
    within_operation_radius: bool
    launch_ground_msl: float | None
    launch_surface_msl: float | None
    launch_antenna_msl: float | None
    profile_sample_count: int | None
    candidate_score: CandidateScore | None
    color_class: ColorClass
    fresnel_diagnostics: CandidateFresnelDiagnostics | None
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str


@dataclass(frozen=True)
class CandidateAnalysisMapFeature:
    feature_id: str
    candidate_id: str
    x_m: float
    y_m: float
    geometry_crs: str
    candidate_cell_mgrs: str | None
    coordinate_display_state: str
    state: CandidateAnalysisState
    color_class: ColorClass
    style: MapStyle
    overall_score: float | None
    shielding_stability_score: float | None
    distance_3d_m: float | None
    within_operation_radius: bool
    reason: str
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None


@dataclass(frozen=True)
class RealTerrainLaunchAreaSummary:
    total_candidate_count: int
    valid_scored_count: int
    excluded_count: int
    state_counts: tuple[tuple[str, int], ...]
    color_counts: tuple[tuple[str, int], ...]
    source_zone_state_counts: tuple[tuple[str, int], ...]
    source_sensitive_count: int


@dataclass(frozen=True)
class RealTerrainLaunchAreaResult:
    scenario_name: str
    dataset_metadata: TerrainDatasetMetadata
    target_point: LocalPoint
    target_ground_msl: float
    target_surface_msl: float
    target_flight_msl: float
    candidate_records: tuple[CandidateAnalysisRecord, ...]
    candidate_features: tuple[CandidateAnalysisMapFeature, ...]
    summary: RealTerrainLaunchAreaSummary
    warnings: tuple[str, ...]
    operation_radius_m: float | None = None
    allowed_agl_m: float | None = None
    frequency_hz: float | None = None
    profile_sample_spacing_m: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("operation_radius_m", self.operation_radius_m),
            ("allowed_agl_m", self.allowed_agl_m),
            ("frequency_hz", self.frequency_hz),
            ("profile_sample_spacing_m", self.profile_sample_spacing_m),
        ):
            if value is not None and (
                isinstance(value, bool) or not isfinite(value) or value <= 0.0
            ):
                raise RealTerrainLaunchAreaAnalysisError(f"{name} must be positive when present.")


def analyze_real_terrain_launch_area(
    adapter: TerrainDataAdapter,
    config: RealTerrainLaunchAreaConfig,
    *,
    source_zone_provider: SourceZoneBatchProvider | None = None,
) -> RealTerrainLaunchAreaResult:
    """Return deterministic candidate records and projected renderer-input features."""

    if not isinstance(config, RealTerrainLaunchAreaConfig):
        raise RealTerrainLaunchAreaAnalysisError("config must be RealTerrainLaunchAreaConfig.")
    _validate_candidate_count_guard(config)
    try:
        with _resolve_session(adapter) as session:
            metadata = session.metadata
            if metadata.dem.crs != "EPSG:5179":
                raise RealTerrainLaunchAreaAnalysisError("dataset CRS must be EPSG:5179.")
            resolved_profile_spacing_m = (
                config.profile_sample_spacing_m
                if config.profile_sample_spacing_m is not None
                else metadata.dem.resolution_m
            )
            _validate_profile_sample_guards(config, resolved_profile_spacing_m)
            try:
                target = session.sample_point(config.target_point)
            except TerrainDataError as exc:
                raise RealTerrainLaunchAreaAnalysisError(
                    f"target terrain sample failed: {exc}"
                ) from exc
            target_flight_msl = target.dem_msl + config.allowed_agl_m
            if target.dsm_msl > target_flight_msl:
                raise RealTerrainLaunchAreaAnalysisError("target surface is above target flight MSL.")
            cells = generate_candidate_grid(
                config.target_point,
                CandidateGridConfig(
                    radius_m=config.operating_radius_m,
                    spacing_m=config.candidate_spacing_m,
                    include_center=config.include_center,
                    include_excluded=config.include_out_of_radius,
                ),
            )
            records = tuple(
                _analyze_candidate(
                    session,
                    cell,
                    config,
                    target_flight_msl,
                    resolved_profile_spacing_m,
                )
                for cell in cells
            )
    except TerrainDataError as exc:
        raise RealTerrainLaunchAreaAnalysisError("terrain analysis session failed") from exc
    records, source_warning = _attach_source_zones(records, source_zone_provider)
    warnings: list[str] = []
    if source_warning is not None:
        warnings.append(source_warning)
    if not any(record.state is CandidateAnalysisState.VALID_SCORED for record in records):
        warnings.append("no valid scored candidates were produced")
    features = tuple(_feature_from_record(index, record) for index, record in enumerate(records))
    return RealTerrainLaunchAreaResult(
        scenario_name=config.scenario_name,
        dataset_metadata=metadata,
        target_point=config.target_point,
        target_ground_msl=target.dem_msl,
        target_surface_msl=target.dsm_msl,
        target_flight_msl=target_flight_msl,
        candidate_records=records,
        candidate_features=features,
        summary=_summary(records),
        warnings=tuple(warnings),
        operation_radius_m=config.operating_radius_m,
        allowed_agl_m=config.allowed_agl_m,
        frequency_hz=config.frequency_hz,
        profile_sample_spacing_m=resolved_profile_spacing_m,
    )


def _analyze_candidate(
    session: TerrainAnalysisSession,
    cell: CandidateCell,
    config: RealTerrainLaunchAreaConfig,
    target_flight_msl: float,
    resolved_profile_spacing_m: float,
) -> CandidateAnalysisRecord:
    """Build an excluded record with the radius result known at the call site."""

    point = cell.point
    distance_2d = distance_2d_m(config.target_point, point)
    if distance_2d > config.operating_radius_m:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
            "outside operating radius",
            distance_2d,
            within_operation_radius=False,
        )
    try:
        sample = session.sample_point(point)
    except TerrainPointOutsideError as exc:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.OUTSIDE_RASTER_EXTENT,
            str(exc),
            distance_2d,
            within_operation_radius=True,
        )
    except TerrainNoDataError as exc:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.TERRAIN_NODATA,
            str(exc),
            distance_2d,
            within_operation_radius=True,
        )
    launch_antenna_msl = sample.dem_msl + config.launch_antenna_height_agl_m
    distance_3d = distance_3d_m(
        LocalPoint(point.x_m, point.y_m, launch_antenna_msl),
        LocalPoint(config.target_point.x_m, config.target_point.y_m, target_flight_msl),
    )
    if distance_3d > config.operating_radius_m:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
            "outside operating radius",
            distance_2d,
            sample,
            distance_3d,
            launch_antenna_msl,
            within_operation_radius=False,
        )
    if point.x_m == config.target_point.x_m and point.y_m == config.target_point.y_m:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.COINCIDENT_WITH_TARGET,
            "candidate coincides with target",
            distance_2d,
            sample,
            distance_3d,
            launch_antenna_msl,
            within_operation_radius=True,
        )
    if sample.dsm_msl > launch_antenna_msl:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.LAUNCH_SURFACE_OBSTRUCTED,
            "launch surface is above launch antenna",
            distance_2d,
            sample,
            distance_3d,
            launch_antenna_msl,
            within_operation_radius=True,
        )
    try:
        profile = session.extract_profile(
            point,
            config.target_point,
            sample_spacing_m=resolved_profile_spacing_m,
            scenario_name=config.scenario_name,
        )
    except (TerrainDataError, TerrainProfileError) as exc:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.PROFILE_UNAVAILABLE,
            str(exc),
            distance_2d,
            sample,
            distance_3d,
            launch_antenna_msl,
            within_operation_radius=True,
        )
    try:
        base_los = analyze_dsm_los(
            profile,
            launch_antenna_msl=launch_antenna_msl,
            drone_flight_msl=target_flight_msl,
        )
        los = _occupied_endpoint_los(base_los)
        fresnel = analyze_dsm_fresnel(los, frequency_hz=config.frequency_hz)
        score = compute_candidate_score(
            distance_3d_m=distance_3d,
            operating_radius_m=config.operating_radius_m,
            dsm_los_score=los.dsm_los_score,
            dsm_fresnel_score=fresnel.dsm_fresnel_score,
        )
        color = classify_candidate_score(score, within_operation_radius=True)
    except (LineOfSightError, FresnelAnalysisError, ScoringError, ClassificationError) as exc:
        return _excluded_record(
            cell.cell_id,
            point,
            CandidateAnalysisState.ANALYSIS_INVALID,
            str(exc),
            distance_2d,
            sample,
            distance_3d,
            launch_antenna_msl,
            within_operation_radius=True,
        )
    return CandidateAnalysisRecord(
        candidate_id=cell.cell_id,
        candidate_point=point,
        sampled_cell_center=sample.cell_center_point,
        state=CandidateAnalysisState.VALID_SCORED,
        reason=classification_reason(
            candidate_score=score,
            within_operation_radius=True,
            color_class=color,
        ),
        distance_2d_m=distance_2d,
        distance_3d_m=distance_3d,
        within_operation_radius=True,
        launch_ground_msl=sample.dem_msl,
        launch_surface_msl=sample.dsm_msl,
        launch_antenna_msl=launch_antenna_msl,
        profile_sample_count=profile.sample_count,
        candidate_score=score,
        color_class=color,
        fresnel_diagnostics=candidate_fresnel_diagnostics_from_analysis(fresnel),
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="source-zone provider not requested",
    )


def _excluded_record(
    candidate_id: str,
    point: LocalPoint,
    state: CandidateAnalysisState,
    reason: str,
    distance_2d: float,
    sample: TerrainPointSample | None = None,
    distance_3d: float | None = None,
    launch_antenna_msl: float | None = None,
    within_operation_radius: bool = False,
) -> CandidateAnalysisRecord:
    applicable = sample is not None and state not in {
        CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
        CandidateAnalysisState.OUTSIDE_RASTER_EXTENT,
        CandidateAnalysisState.TERRAIN_NODATA,
    }
    return CandidateAnalysisRecord(
        candidate_id=candidate_id,
        candidate_point=point,
        sampled_cell_center=None if sample is None else sample.cell_center_point,
        state=state,
        reason=reason,
        distance_2d_m=distance_2d,
        distance_3d_m=distance_3d,
        within_operation_radius=within_operation_radius,
        launch_ground_msl=None if sample is None else sample.dem_msl,
        launch_surface_msl=None if sample is None else sample.dsm_msl,
        launch_antenna_msl=launch_antenna_msl,
        profile_sample_count=None,
        candidate_score=None,
        color_class=ColorClass.EXCLUDED,
        fresnel_diagnostics=None,
        source_zone=None,
        source_zone_state=(
            SourceZoneAvailability.NOT_REQUESTED
            if applicable
            else SourceZoneAvailability.NOT_APPLICABLE
        ),
        source_sensitive=None,
        source_zone_reason=(
            "source-zone provider not requested" if applicable else "source-zone not applicable"
        ),
    )


def _occupied_endpoint_los(base: LineOfSightAnalysis) -> LineOfSightAnalysis:
    samples = tuple(
        replace(sample, is_blocked=False)
        if index in {0, len(base.samples) - 1}
        else sample
        for index, sample in enumerate(base.samples)
    )
    return LineOfSightAnalysis(
        scenario_name=base.scenario_name,
        launch_antenna_msl=base.launch_antenna_msl,
        drone_flight_msl=base.drone_flight_msl,
        samples=samples,
        dsm_los_score=0.0 if any(sample.is_blocked for sample in samples) else 100.0,
    )


def _attach_source_zones(
    records: tuple[CandidateAnalysisRecord, ...],
    provider: SourceZoneBatchProvider | None,
) -> tuple[tuple[CandidateAnalysisRecord, ...], str | None]:
    ineligible = {
        CandidateAnalysisState.OUTSIDE_OPERATING_RADIUS,
        CandidateAnalysisState.OUTSIDE_RASTER_EXTENT,
        CandidateAnalysisState.TERRAIN_NODATA,
    }
    eligible_indices = [
        index
        for index, record in enumerate(records)
        if record.sampled_cell_center is not None and record.state not in ineligible
    ]
    if provider is None:
        return records, None
    if not eligible_indices:
        return records, None
    points = tuple(records[index].candidate_point for index in eligible_indices)
    try:
        zones = tuple(provider(points))
        if len(zones) != len(points) or any(
            not isinstance(zone, TerrainSourceZone) for zone in zones
        ):
            raise ValueError("invalid source-zone provider result")
    except Exception:
        eligible = set(eligible_indices)
        return (
            tuple(
                replace(
                    record,
                    source_zone_state=SourceZoneAvailability.UNAVAILABLE,
                    source_zone_reason="source-zone provider unavailable",
                )
                if index in eligible
                else record
                for index, record in enumerate(records)
            ),
            "source-zone provider unavailable",
        )
    zones_by_index = dict(zip(eligible_indices, zones, strict=True))
    return (
        tuple(
            replace(
                record,
                source_zone=zones_by_index[index],
                source_zone_state=SourceZoneAvailability.AVAILABLE,
                source_sensitive=is_source_sensitive_zone(zones_by_index[index]),
                source_zone_reason=f"{zones_by_index[index].value} source zone",
            )
            if index in zones_by_index
            else record
            for index, record in enumerate(records)
        ),
        None,
    )


def _feature_from_record(index: int, record: CandidateAnalysisRecord) -> CandidateAnalysisMapFeature:
    score = record.candidate_score
    return CandidateAnalysisMapFeature(
        feature_id=f"candidate-feature-{index:05d}",
        candidate_id=record.candidate_id,
        x_m=record.candidate_point.x_m,
        y_m=record.candidate_point.y_m,
        geometry_crs="EPSG:5179",
        candidate_cell_mgrs=None,
        coordinate_display_state="projected_only",
        state=record.state,
        color_class=record.color_class,
        style=style_for_color_class(record.color_class),
        overall_score=None if score is None else score.overall_score,
        shielding_stability_score=None if score is None else score.shielding_stability_score,
        distance_3d_m=record.distance_3d_m,
        within_operation_radius=record.within_operation_radius,
        reason=record.reason,
        source_zone=record.source_zone,
        source_zone_state=record.source_zone_state,
        source_sensitive=record.source_sensitive,
        source_zone_reason=record.source_zone_reason,
        fresnel_diagnostics=record.fresnel_diagnostics,
    )


def _summary(records: tuple[CandidateAnalysisRecord, ...]) -> RealTerrainLaunchAreaSummary:
    states = Counter(record.state for record in records)
    colors = Counter(record.color_class for record in records)
    source_states = Counter(record.source_zone_state for record in records)
    valid_count = states[CandidateAnalysisState.VALID_SCORED]
    return RealTerrainLaunchAreaSummary(
        total_candidate_count=len(records),
        valid_scored_count=valid_count,
        excluded_count=len(records) - valid_count,
        state_counts=tuple((state.value, states[state]) for state in CandidateAnalysisState),
        color_counts=tuple((color.value, colors[color]) for color in ColorClass),
        source_zone_state_counts=tuple(
            (state.value, source_states[state]) for state in SourceZoneAvailability
        ),
        source_sensitive_count=sum(record.source_sensitive is True for record in records),
    )


class _CompatibilityTerrainAnalysisSession(
    AbstractContextManager["_CompatibilityTerrainAnalysisSession"]
):
    def __init__(self, adapter: TerrainDataAdapter) -> None:
        self._adapter = adapter
        self.metadata = adapter.validate_metadata()

    def __exit__(self, *args: object) -> None:
        return None

    def sample_point(self, point: LocalPoint) -> TerrainPointSample:
        try:
            x_index, y_index = local_point_to_metadata_grid_index(self.metadata, point)
            dem = self._adapter.get_dem_msl(x_index, y_index)
            raw_dsm = self._adapter.get_dsm_msl(x_index, y_index)
        except TerrainPointOutsideError:
            raise
        except TerrainNoDataError:
            raise
        except TerrainProfileError as exc:
            raise TerrainPointOutsideError("sample point is outside the terrain extent.") from exc
        except TerrainDataError as exc:
            raise TerrainNoDataError("terrain point data is unavailable.") from exc
        if not isfinite(dem) or not isfinite(raw_dsm):
            raise TerrainNoDataError("terrain point data must be finite.")
        effective_dsm = max(raw_dsm, dem)
        x_min, y_min, _, _ = self.metadata.dem.bounds
        return TerrainPointSample(
            requested_point=point,
            cell_center_point=LocalPoint(
                x_min + x_index * self.metadata.dem.resolution_m,
                y_min + y_index * self.metadata.dem.resolution_m,
            ),
            x_index=x_index,
            y_index=y_index,
            dem_msl=dem,
            dsm_msl=effective_dsm,
            surface_delta_m=effective_dsm - dem,
        )

    def extract_profile(
        self,
        start: LocalPoint,
        end: LocalPoint,
        *,
        sample_spacing_m: float,
        scenario_name: str,
    ) -> TerrainProfile:
        if sample_spacing_m <= 0:
            raise TerrainProfileError("sample_spacing_m must be positive.")
        distance = distance_2d_m(start, end)
        if distance <= 0:
            raise TerrainProfileError("start and end must be different local points.")
        steps = max(1, int(ceil(distance / sample_spacing_m)))
        samples: list[TerrainProfileSample] = []
        for index in range(steps + 1):
            fraction = index / steps
            point = LocalPoint(
                start.x_m + (end.x_m - start.x_m) * fraction,
                start.y_m + (end.y_m - start.y_m) * fraction,
            )
            sample = self.sample_point(point)
            samples.append(
                TerrainProfileSample(
                    sample_index=index,
                    ix=sample.x_index,
                    iy=sample.y_index,
                    point=point,
                    distance_from_start_m=distance * fraction,
                    distance_to_end_m=distance * (1.0 - fraction),
                    dem_msl=sample.dem_msl,
                    dsm_msl=sample.dsm_msl,
                    surface_delta_m=sample.surface_delta_m,
                )
            )
        return TerrainProfile(scenario_name, start, end, sample_spacing_m, tuple(samples))


def _resolve_session(adapter: TerrainDataAdapter) -> AbstractContextManager[TerrainAnalysisSession]:
    factory = getattr(adapter, "open_analysis_session", None)
    if callable(factory):
        return cast(AbstractContextManager[TerrainAnalysisSession], factory())
    return _CompatibilityTerrainAnalysisSession(adapter)


def _validate_candidate_count_guard(config: RealTerrainLaunchAreaConfig) -> None:
    steps = ceil(config.operating_radius_m / config.candidate_spacing_m)
    candidate_count = (2 * steps + 1) ** 2 - (0 if config.include_center else 1)
    if candidate_count > config.max_candidate_count:
        raise RealTerrainLaunchAreaAnalysisError("candidate count guard exceeded.")


def _validate_profile_sample_guards(
    config: RealTerrainLaunchAreaConfig,
    resolved_profile_spacing_m: float,
) -> None:
    _positive("resolved_profile_spacing_m", resolved_profile_spacing_m)
    profile_count = max(
        1,
        int(ceil((2.0 * config.operating_radius_m) / resolved_profile_spacing_m)),
    ) + 1
    if profile_count > config.max_profile_samples_per_candidate:
        raise RealTerrainLaunchAreaAnalysisError("profile sample guard exceeded.")
    steps = ceil(config.operating_radius_m / config.candidate_spacing_m)
    candidate_count = (2 * steps + 1) ** 2 - (0 if config.include_center else 1)
    if candidate_count * profile_count > config.max_total_profile_samples:
        raise RealTerrainLaunchAreaAnalysisError("total profile sample guard exceeded.")


def _finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value):
        raise RealTerrainLaunchAreaAnalysisError(f"{name} must be finite.")


def _positive(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value <= 0:
        raise RealTerrainLaunchAreaAnalysisError(f"{name} must be finite and positive.")
