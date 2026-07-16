"""Candidate-ID selection over an immutable real-terrain map package."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .coordinates import LocalPoint
from .fresnel_diagnostics import CandidateFresnelDiagnostics
from .real_terrain_candidate_analysis import (
    CandidateAnalysisRecord,
    CandidateAnalysisState,
    RealTerrainLaunchAreaResult,
    SourceZoneAvailability,
)
from .real_terrain_launch_area_map import (
    RealTerrainCandidatePolygon,
    RealTerrainLaunchAreaMapError,
    RealTerrainLaunchAreaMapPackage,
    validate_real_terrain_launch_area_map_package,
)
from .schemas import ColorClass
from .source_zones import TerrainSourceZone


class LaunchSiteSelectionError(ValueError):
    """Raised when a candidate cannot be selected from the supplied package."""


@dataclass(frozen=True)
class SelectedLaunchSiteRecord:
    """Immutable selected-site result; projected point remains internal to later routing."""

    candidate_id: str
    launch_site_mgrs: str
    external_coordinate_format: str
    user_coordinate_field: str
    projected_point: LocalPoint
    color_class: ColorClass
    overall_score: float
    shielding_stability_score: float
    distance_3d_m: float
    candidate_reason: str
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None

    def __post_init__(self) -> None:
        _required_text("candidate_id", self.candidate_id)
        _required_text("launch_site_mgrs", self.launch_site_mgrs)
        if self.launch_site_mgrs != self.launch_site_mgrs.upper():
            raise LaunchSiteSelectionError("launch_site_mgrs must be uppercase.")
        if self.external_coordinate_format != "MGRS":
            raise LaunchSiteSelectionError("external_coordinate_format must be MGRS.")
        if self.user_coordinate_field != "launch_site_mgrs":
            raise LaunchSiteSelectionError("user_coordinate_field must be launch_site_mgrs.")
        if not isinstance(self.projected_point, LocalPoint):
            raise LaunchSiteSelectionError("projected_point must be LocalPoint.")
        if not isinstance(self.color_class, ColorClass) or self.color_class is ColorClass.EXCLUDED:
            raise LaunchSiteSelectionError("selected color_class must be a non-excluded ColorClass.")
        for name, value in (
            ("overall_score", self.overall_score),
            ("shielding_stability_score", self.shielding_stability_score),
            ("distance_3d_m", self.distance_3d_m),
        ):
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
                raise LaunchSiteSelectionError(f"{name} must be finite numeric.")
        _required_text("candidate_reason", self.candidate_reason)
        _required_text("source_zone_reason", self.source_zone_reason)
        if self.source_zone is not None and not isinstance(self.source_zone, TerrainSourceZone):
            raise LaunchSiteSelectionError("source_zone must be approved enum or None.")
        if not isinstance(self.source_zone_state, SourceZoneAvailability):
            raise LaunchSiteSelectionError("source_zone_state must use approved enum.")
        if self.source_sensitive is not None and not isinstance(self.source_sensitive, bool):
            raise LaunchSiteSelectionError("source_sensitive must be bool or None.")
        if self.fresnel_diagnostics is not None and not isinstance(
            self.fresnel_diagnostics, CandidateFresnelDiagnostics
        ):
            raise LaunchSiteSelectionError("fresnel_diagnostics must be approved diagnostics or None.")

    def to_user_facing_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "launch_site_mgrs": self.launch_site_mgrs,
            "external_coordinate_format": self.external_coordinate_format,
            "user_coordinate_field": self.user_coordinate_field,
            "color_class": self.color_class.value,
            "overall_score": self.overall_score,
            "shielding_stability_score": self.shielding_stability_score,
            "distance_3d_m": self.distance_3d_m,
            "candidate_reason": self.candidate_reason,
            "source_zone": None if self.source_zone is None else self.source_zone.value,
            "source_zone_state": self.source_zone_state.value,
            "source_sensitive": self.source_sensitive,
            "source_zone_reason": self.source_zone_reason,
            "fresnel_diagnostics": (
                None if self.fresnel_diagnostics is None else self.fresnel_diagnostics.to_flat_dict()
            ),
        }


def select_launch_site(
    result: RealTerrainLaunchAreaResult,
    package: RealTerrainLaunchAreaMapPackage,
    candidate_id: str,
) -> SelectedLaunchSiteRecord:
    """Select one included selectable candidate without mutating or recomputing analysis."""

    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise LaunchSiteSelectionError("candidate_id must be non-empty.")
    if candidate_id != candidate_id.strip():
        raise LaunchSiteSelectionError("candidate_id must be stripped.")
    if not isinstance(result, RealTerrainLaunchAreaResult):
        raise LaunchSiteSelectionError("result must be RealTerrainLaunchAreaResult.")
    if not isinstance(package, RealTerrainLaunchAreaMapPackage):
        raise LaunchSiteSelectionError("package must be RealTerrainLaunchAreaMapPackage.")
    try:
        validate_real_terrain_launch_area_map_package(package)
    except RealTerrainLaunchAreaMapError as exc:
        raise LaunchSiteSelectionError("package invariant validation failed.") from exc
    if package.selected_candidate_id not in {None, candidate_id}:
        raise LaunchSiteSelectionError("package has a conflicting selected candidate.")
    _validate_unique_ids(result.candidate_records, package.candidate_polygons)
    record = next((item for item in result.candidate_records if item.candidate_id == candidate_id), None)
    if record is None:
        raise LaunchSiteSelectionError("candidate_id was not found.")
    polygon = next((item for item in package.candidate_polygons if item.candidate_id == candidate_id), None)
    if polygon is None:
        raise LaunchSiteSelectionError("candidate_id is hidden by map configuration.")
    if (
        record.state is not CandidateAnalysisState.VALID_SCORED
        or record.candidate_score is None
        or record.color_class is ColorClass.EXCLUDED
        or not record.within_operation_radius
        or record.distance_3d_m is None
        or not polygon.selectable
    ):
        raise LaunchSiteSelectionError("candidate_id is not selectable.")
    _validate_record_polygon_parity(record, polygon)
    if (
        not polygon.popup.candidate_cell_mgrs.strip()
        or polygon.popup.candidate_cell_mgrs != polygon.popup.candidate_cell_mgrs.strip()
    ):
        raise LaunchSiteSelectionError("candidate MGRS is invalid.")
    return SelectedLaunchSiteRecord(
        candidate_id=record.candidate_id,
        launch_site_mgrs=polygon.popup.candidate_cell_mgrs,
        external_coordinate_format="MGRS",
        user_coordinate_field="launch_site_mgrs",
        projected_point=record.candidate_point,
        color_class=record.color_class,
        overall_score=record.candidate_score.overall_score,
        shielding_stability_score=record.candidate_score.shielding_stability_score,
        distance_3d_m=record.distance_3d_m,
        candidate_reason=record.reason,
        source_zone=record.source_zone,
        source_zone_state=record.source_zone_state,
        source_sensitive=record.source_sensitive,
        source_zone_reason=record.source_zone_reason,
        fresnel_diagnostics=record.fresnel_diagnostics,
    )


def _validate_unique_ids(
    records: tuple[CandidateAnalysisRecord, ...],
    polygons: tuple[RealTerrainCandidatePolygon, ...],
) -> None:
    if len({record.candidate_id for record in records}) != len(records):
        raise LaunchSiteSelectionError("result contains duplicate candidate IDs.")
    if len({polygon.candidate_id for polygon in polygons}) != len(polygons):
        raise LaunchSiteSelectionError("package contains duplicate candidate IDs.")


def _validate_record_polygon_parity(
    record: CandidateAnalysisRecord,
    polygon: RealTerrainCandidatePolygon,
) -> None:
    popup = polygon.popup
    score = record.candidate_score
    if (
        polygon.candidate_id != record.candidate_id
        or polygon.state is not record.state
        or polygon.color_class is not record.color_class
        or popup.state is not record.state
        or popup.color_class is not record.color_class
        or popup.within_operation_radius != record.within_operation_radius
        or popup.candidate_reason != record.reason
        or popup.source_zone != record.source_zone
        or popup.source_zone_state is not record.source_zone_state
        or popup.source_sensitive != record.source_sensitive
        or popup.source_zone_reason != record.source_zone_reason
        or popup.fresnel_diagnostics != record.fresnel_diagnostics
        or popup.overall_score != (None if score is None else score.overall_score)
        or popup.shielding_stability_score
        != (None if score is None else score.shielding_stability_score)
        or popup.distance_3d_m != record.distance_3d_m
    ):
        raise LaunchSiteSelectionError("result record and package candidate do not match.")


def _required_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LaunchSiteSelectionError(f"{name} must be a non-empty stripped string.")
