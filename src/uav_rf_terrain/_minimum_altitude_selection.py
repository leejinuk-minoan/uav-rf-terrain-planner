"""Private exact-extreme and tolerance-representative selection primitives."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from math import isfinite
from typing import Any, TypeVar


T = TypeVar("T")


class MinimumAltitudeSelectionError(ValueError):
    """Raised when a private minimum-altitude selection contract is invalid."""


def select_tolerance_representative(
    candidates: Iterable[T],
    *,
    value: Callable[[T], float],
    tie_key: Callable[[T], Any],
    tolerance: float,
    maximize: bool,
) -> tuple[float, T]:
    """Return an exact finite extreme and canonical item within its absolute tie band."""

    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not isfinite(tolerance)
        or tolerance < 0.0
    ):
        raise MinimumAltitudeSelectionError("tolerance must be a non-negative finite float.")
    items = tuple(candidates)
    if not items:
        raise MinimumAltitudeSelectionError("selection candidates must not be empty.")
    values: list[tuple[T, float]] = []
    for item in items:
        numeric = value(item)
        if isinstance(numeric, bool) or not isinstance(numeric, (int, float)) or not isfinite(numeric):
            raise MinimumAltitudeSelectionError("selection values must be finite floats.")
        values.append((item, float(numeric)))
    extreme = max(numeric for _, numeric in values) if maximize else min(numeric for _, numeric in values)
    tied = tuple(item for item, numeric in values if abs(numeric - extreme) <= tolerance)
    return extreme, min(tied, key=tie_key)
