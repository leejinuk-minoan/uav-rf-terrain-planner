from __future__ import annotations

from itertools import permutations
from math import nextafter

import pytest

from uav_rf_terrain._minimum_altitude_selection import (
    MinimumAltitudeSelectionError,
    select_tolerance_representative,
)


@pytest.mark.parametrize("maximize", (True, False))
def test_selects_exact_extreme_and_canonical_tolerance_representative_for_all_orders(
    maximize: bool,
) -> None:
    tolerance = 1.0
    values = (0.0, 0.75 * tolerance, 1.5 * tolerance)
    expected_extreme = max(values) if maximize else min(values)
    for ordered in permutations(values):
        extreme, selected = select_tolerance_representative(
            ordered,
            value=lambda item: item,
            tie_key=lambda item: item,
            tolerance=tolerance,
            maximize=maximize,
        )
        assert extreme == expected_extreme
        assert selected == (0.75 * tolerance if maximize else 0.0)


@pytest.mark.parametrize("offset", (nextafter(1.0, 0.0), 1.0, nextafter(1.0, 2.0)))
def test_tolerance_boundary_controls_canonical_tie_set(offset: float) -> None:
    extreme, selected = select_tolerance_representative(
        (0.0, offset),
        value=lambda item: item,
        tie_key=lambda item: item,
        tolerance=1.0,
        maximize=True,
    )
    assert extreme == offset
    assert selected == 0.0 if offset <= 1.0 else offset


@pytest.mark.parametrize("items,tolerance", (((), 1.0), ((1.0,), -1.0), ((1.0,), float("inf"))))
def test_rejects_empty_or_invalid_selection_contract(
    items: tuple[float, ...], tolerance: float
) -> None:
    with pytest.raises(MinimumAltitudeSelectionError):
        select_tolerance_representative(
            items,
            value=lambda item: item,
            tie_key=lambda item: item,
            tolerance=tolerance,
            maximize=True,
        )
