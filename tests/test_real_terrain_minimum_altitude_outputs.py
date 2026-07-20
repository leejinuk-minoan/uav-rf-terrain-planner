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


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("expected_frequency_hz", 0.0),
        ("expected_frequency_hz", float("nan")),
        ("required_fresnel_clearance_ratio", float("inf")),
        ("required_fresnel_clearance_ratio", True),
        ("profile_spacing_m", 0.0),
        ("profile_spacing_m", float("nan")),
        ("epsilon_m", -1e-9),
        ("distance_tolerance_m", float("inf")),
        ("max_routes", True),
        ("max_route_samples", 0),
        ("max_profile_samples_per_link", 0),
        ("max_total_profile_samples", 0),
    ),
)
def test_config_rejects_every_invalid_numeric_or_guard_field(field: str, value: object) -> None:
    with pytest.raises(RealTerrainMinimumAltitudeOutputError):
        RealTerrainMinimumAltitudeConfig(**{field: value})


@pytest.mark.parametrize("ratio", (0.0, 0.6, 1.0))
def test_config_accepts_reviewed_clearance_ratio_boundaries(ratio: float) -> None:
    assert RealTerrainMinimumAltitudeConfig(required_fresnel_clearance_ratio=ratio).required_fresnel_clearance_ratio == ratio
