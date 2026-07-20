# Task 036A Handoff - Real-Terrain Minimum-Altitude Contract

## Current Task

Task 036A is a contract and audit task for future real-terrain minimum-required MSL
and AGL proxy analysis. It creates no runtime implementation.

## Current Branch

`agent/task-036a-real-terrain-minimum-altitude-contract`

## Draft PR

Draft PR #109: `docs: define real-terrain minimum-altitude boundary`.

## Selected Contract

- Consume a complete `RealTerrainRouteResult` as mission/route authority plus a
  `TerrainDataAdapter` and one terrain session.
- Build dedicated bounded DSM/DEM radial profiles from the snapped launch to each
  resampled route point; route handoffs and 500 m waypoint reports are not sufficient
  clearance-profile authority.
- Return one comparison-only minimum required constant-route MSL for every available
  route candidate in source order. Do not choose a final route or produce a flight
  command.
- Derive launch antenna MSL from launch ground plus the source fixed AGL. Use source
  route frequency and a configurable `[0, 1]` clearance ratio whose default is 0.6.
- Retain private route/frequency/launch/terrain/profile authority for validation and
  expose MGRS-facing values only by default.

## Legacy Compatibility

`src/uav_rf_terrain/minimum_altitude.py` remains the Task 015 synthetic single-profile
API. No source, test, workflow, dependency, or GIS change is part of Task 036A.

## Verification

The required local test commands are regression verification only because source and
tests remain unchanged. `compileall`, Ruff, mypy, and diff checks passed; the legacy
minimum-altitude focused suite passed 19 tests and the full suite passed 913 with 1
skip. Exact final-head CI is recorded in the Draft PR completion comment and
completion report under the non-recursive ledger policy.

## Paper Record

This feature is an offline DSM/LOS/Fresnel clearance proxy. It is not obstacle
clearance certification, flight-safety approval, communication-success evidence,
regulatory approval, airspace authorization, or autopilot output.

## Next Implementation Task

Implement a separate runtime module only after review of the architecture, DEC-009,
and EXP-057. Required future coverage includes terrain profile provenance, resource
bounds, input authority, MSL inversion, AGL conversions, warning order, MGRS output,
and public-coordinate omission.
