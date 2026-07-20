from __future__ import annotations

import pytest

from uav_rf_terrain.real_terrain_minimum_altitude_outputs import (
    RealTerrainMinimumAltitudeConfig,
    RealTerrainMinimumAltitudeOutputError,
)


def test_config_rejects_bool_and_invalid_proxy_ratio() -> None:
    with pytest.raises(RealTerrainMinimumAltitudeOutputError):
        RealTerrainMinimumAltitudeConfig(expected_frequency_hz=True)
    with pytest.raises(RealTerrainMinimumAltitudeOutputError):
        RealTerrainMinimumAltitudeConfig(required_fresnel_clearance_ratio=1.01)


def test_config_accepts_reviewed_defaults() -> None:
    config = RealTerrainMinimumAltitudeConfig()
    assert config.required_fresnel_clearance_ratio == 0.6
    assert config.max_routes == 3
