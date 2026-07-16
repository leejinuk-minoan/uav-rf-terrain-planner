from __future__ import annotations

import pytest

from test_real_terrain_launch_area_map import _result

from uav_rf_terrain.launch_site_selection import LaunchSiteSelectionError, SelectedLaunchSiteRecord
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability
from uav_rf_terrain.launch_site_selection import select_launch_site
from uav_rf_terrain.coordinate_conversion import Wgs84MapPoint
from uav_rf_terrain.real_terrain_launch_area_map import (
    RealTerrainLaunchAreaMapConfig,
    build_real_terrain_launch_area_map_package,
)


def test_selected_launch_site_record_is_immutable_and_hides_internal_coordinates() -> None:
    record = SelectedLaunchSiteRecord(
        candidate_id="candidate-001",
        launch_site_mgrs="52SCB1234512345",
        external_coordinate_format="MGRS",
        user_coordinate_field="launch_site_mgrs",
        projected_point=LocalPoint(950000.0, 1950000.0),
        color_class=ColorClass.RED,
        overall_score=10.0,
        shielding_stability_score=5.0,
        distance_3d_m=100.0,
        candidate_reason="valid red candidate",
        source_zone=None,
        source_zone_state=SourceZoneAvailability.NOT_REQUESTED,
        source_sensitive=None,
        source_zone_reason="not requested",
        fresnel_diagnostics=None,
    )

    assert record.to_user_facing_dict()["launch_site_mgrs"] == "52SCB1234512345"
    assert record.to_user_facing_dict()["external_coordinate_format"] == "MGRS"
    assert "projected_point" not in record.to_user_facing_dict()
    with pytest.raises((AttributeError, LaunchSiteSelectionError)):
        record.candidate_id = "other"  # type: ignore[misc]


def test_selection_rejects_whitespace_candidate_id_before_lookup() -> None:
    with pytest.raises(LaunchSiteSelectionError, match="stripped"):
        select_launch_site(None, None, " candidate-001 ")  # type: ignore[arg-type]


def test_selection_rejects_a_package_mutated_after_construction() -> None:
    def wgs(point: LocalPoint) -> Wgs84MapPoint:
        return Wgs84MapPoint(point.x_m / 1000.0, point.y_m / 1000.0)

    result = _result()
    package = build_real_terrain_launch_area_map_package(
        result,
        RealTerrainLaunchAreaMapConfig(10.0),
        projected_to_wgs84=wgs,
        projected_to_mgrs=lambda point, *, precision: "52SCB1234512345",
    )
    object.__setattr__(package.summary, "selected_candidate_count", 1)

    with pytest.raises(LaunchSiteSelectionError, match="invariant"):
        select_launch_site(result, package, "candidate-001")
