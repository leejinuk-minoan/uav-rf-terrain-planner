# EXP-20260720-058 - Real-Terrain Minimum-Altitude Pure Core

## Purpose

Verify immutable prepared-evidence contracts and deterministic pure calculation of a
route-level minimum required constant MSL proxy. The engine is intentionally isolated
from terrain-session and GIS orchestration.

## Method

Prepared route samples retain private projected/profile evidence internally while
public results retain MGRS-facing identifiers and calculated proxy fields. Eligible
radial samples use the approved Fresnel inversion; every route sample receives a
separate current fixed-AGL clearance margin. Constant-MSL and deficit-limiting samples
remain independent.

## Boundaries

No terrain adapter session, raster sampling, real GIS smoke, route recomputation,
route selection, UI, device control, or operational altitude claim is included.

## Status

Task 036B implementation and exact-head verification are in progress. Final test and
CI evidence belongs in the Draft PR completion comment under the non-recursive ledger
policy.
