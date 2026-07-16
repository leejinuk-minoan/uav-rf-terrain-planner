# Task 035EF Handoff - Real-Terrain Route Recommendation

## Current Task

Task 035EF implements deterministic, selected-launch-site route recommendation over
the existing real-terrain analysis boundary.

## Current Branch

`agent/task-035ef-real-terrain-route-recommendation`

## Contract Boundary

- Consume `SelectedLaunchSiteRecord`, its `RealTerrainLaunchAreaResult`, an existing
  `TerrainDataAdapter`, route configuration, and an MGRS converter.
- Validate selection/source parity before terrain access; resolve one terrain session
  for DEM/DSM sampling and profiles.
- Use EPSG:5179 graph construction, fixed AGL-to-MSL altitude rules, 3D operating-radius
  checks, existing LOS/Fresnel/scoring/classification, and deterministic Dijkstra.
- Return up to three diverse MGRS-facing route candidates in fixed mode order.
- Retain immutable graph node/edge analysis records and unsampled waypoint handoff
  points without changing the existing waypoint report behavior.

## Explicit Non-Goals

- No map/UI rendering, browser behavior, route execution, autopilot, or external-device
  control.
- No changes to existing candidate analysis, selection, score/color, preview/report/CLI,
  `routing.py`, or `waypoints.py` behavior.
- No generated output, GIS data, private path, or operational coordinate is committed.

## Verification Plan

Focused tests cover route-analysis guards, grid and edge construction, deterministic
pathfinding/diversity, and public output conversion. The final local gate runs focused
tests, full pytest, compileall, Ruff, mypy, and diff validation. The final Draft PR
must also pass its exact-head standard GitHub Actions run.

## Local Verification Result

The focused Task 035EF suite passed 11 tests and the full local suite passed 875 tests.
`compileall`, Ruff, mypy, and `git diff --check` are required again on the final commit
head. No real GIS route smoke, generated route artifact, or browser/UI test is run by
this task.

## Paper Record

The Task records route recommendation as a terrain-derived proxy and documents
performance guards, source-zone interpretation limits, and the separation from field
RF, flight-feasibility, and approval claims.
