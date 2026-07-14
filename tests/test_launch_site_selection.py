from __future__ import annotations

import pytest

from uav_rf_terrain.launch_site_selection import LaunchSiteSelectionError, SelectedLaunchSiteRecord
from uav_rf_terrain.coordinates import LocalPoint
from uav_rf_terrain.schemas import ColorClass
from uav_rf_terrain.real_terrain_candidate_analysis import SourceZoneAvailability


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
