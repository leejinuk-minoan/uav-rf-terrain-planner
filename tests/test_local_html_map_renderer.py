from __future__ import annotations

import pytest

from uav_rf_terrain.local_html_map_renderer import LocalHtmlMapRenderConfig, LocalHtmlMapRendererError


def test_renderer_config_requires_positive_dimensions_and_safe_padding() -> None:
    assert LocalHtmlMapRenderConfig() == LocalHtmlMapRenderConfig(width_px=1000, height_px=800, padding_px=40)

    with pytest.raises(LocalHtmlMapRendererError):
        LocalHtmlMapRenderConfig(width_px=True)
    with pytest.raises(LocalHtmlMapRendererError):
        LocalHtmlMapRenderConfig(width_px=80, height_px=80, padding_px=40)
