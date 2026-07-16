# Task 035G Handoff - Real-Terrain Waypoint Reporting

## Current Task

Task 035G adds deterministic MGRS-facing approximately 500 m reporting waypoints over
complete Task 035EF route results.

## Contract Boundary

- Accept complete route candidates and handoffs only; revalidate their immutable
  route, snap, MGRS, distance, and `NOT_REQUESTED` source-zone policy.
- Use cumulative 3D handoff distance as sampling authority.
- Reuse exact handoff values; linearly interpolate elevations for segment targets and
  retain conservative color and score values.
- Keep fixed route AGL, launch-ground height difference, deterministic IDs, MGRS cache,
  and public-coordinate restrictions.

## Explicit Non-Goals

- No terrain session, DEM/DSM sampling, LOS/Fresnel, scoring, color classification,
  graph, Dijkstra, route selection, map/UI, route execution, autopilot, or device use.
- No change to legacy `waypoints.py`, `routing.py`, Task 035B/035D/035EF behavior,
  dependency, or workflow contracts.
- No GIS data, generated report, private path, or actual operational coordinate.

## Verification Plan

Focused reporting/output tests plus full pytest, compileall, Ruff, mypy, diff check,
and exact-head Draft PR CI are required before GPT Master re-review.

## Paper Record

The report is an offline terrain/surface-obstacle proxy. It does not establish obstacle
absence, RF availability, flight feasibility, reconnaissance success, or approval.
