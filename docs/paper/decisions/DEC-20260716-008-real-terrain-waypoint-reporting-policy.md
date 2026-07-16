# DEC-20260716-008 - Real-Terrain Waypoint Reporting Policy

## Decision

Task 035G adds a separate waypoint-reporting boundary that consumes only a complete
Task 035EF `RealTerrainRouteResult`. Approximately 500 m targets use cumulative 3D
handoff distance. Exact targets reuse source-node values; interior targets linearly
interpolate elevations and conservatively retain the worse color and lower scores.

## Rationale

The complete route result already owns graph, route, MGRS, handoff, launch-ground, and
snap authority. Opening terrain, recomputing LOS/Fresnel, changing scoring, or copying
selected-site source-zone metadata would duplicate or alter reviewed Task 035EF
semantics. The reporting layer therefore preserves fixed route AGL, converts each
unique waypoint point to MGRS once, and keeps route source-zone metadata explicitly
`NOT_REQUESTED`. Its immutable result retains only the private route-ID/mode/total,
launch-ground, and snapped-MGRS authority required for cross-object validation; its
public dictionary omits those private authority fields.

Interior interpolation is strict (`0 < fraction < 1`). Short, endpoint-only, and
zero-distance route conditions emit deterministic report/summary/result warnings.
For a zero-distance route, the explicit zero-distance warning is used instead of an
endpoint-only warning.

## Limits and Compatibility

This is an offline terrain/surface-obstacle reporting proxy, not evidence of obstacle
absence, communications availability, flight feasibility, reconnaissance success, or
approval. It does not select a route, create map/UI or device output, alter
`waypoints.py`, `routing.py`, terrain analysis, scoring/color, preview/report/CLI,
dependencies, or CI.

## Public Repository Sensitivity Check

No real GIS data, generated report, private path, actual operational coordinate,
credential, or external-device instruction is stored by this decision.
