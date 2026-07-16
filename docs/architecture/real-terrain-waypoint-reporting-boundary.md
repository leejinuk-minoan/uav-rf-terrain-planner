# Real-Terrain Waypoint Reporting Boundary

## Purpose

Task 035G turns each available complete `RealTerrainRouteResult` candidate into an
ordered, approximately 500 m, MGRS-facing waypoint report. It is an offline research,
education, and simulation reporting boundary. It does not choose a route, recompute a
route, access terrain data, or create vehicle-execution output.

## Input Authority

`build_real_terrain_waypoint_reports()` accepts only a complete
`RealTerrainRouteResult` and a `RealTerrainWaypointConfig`. Before it produces any
report, it revalidates the complete result contract, candidate/handoff order and
parity, snapped graph-path semantics, cumulative-distance monotonicity, final
cumulative-distance parity with the candidate 3D total, and the route-source-zone MVP
policy.

The handoff `cumulative_distance_3d_m` values and candidate
`total_distance_3d_m` are the sole sampling-distance authority. This task does not
resample DEM/DSM, open a terrain session, run LOS/Fresnel, score, classify colors,
build a graph, or run route search.

## Sampling Contract

The default spacing is 500 m. Target distances are start zero when included, positive
integer spacing multiples strictly below the route total within tolerance, and the
route total when included. Equal or tolerance-equivalent targets are emitted once.

For a zero-length one-node route, including both start and end produces exactly one
waypoint. A route shorter than spacing follows the same start/end inclusion policy.
All waypoint cumulative distances are ascending and the first segment distance is zero.
The number of generated waypoints is bounded per route and across the result before
MGRS conversion begins.

## Values and Interpolation

An exact target distance reuses its `WaypointHandoffPoint` values. If duplicate exact
source distances occur, the lowest source sequence index wins. A target strictly inside
a segment linearly interpolates projected point, terrain MSL, surface MSL, and flight
MSL from the bracketing handoffs. The configured route AGL remains fixed and the
derived values must keep `terrain <= surface <= flight` and `flight = terrain + AGL`.

Interpolated risk is conservative: the color takes the worse endpoint in
green, yellow, orange, red severity order, and both shielding-stability and overall
scores take the lower endpoint score. Exact values use `source_node` semantics;
interpolated values use `segment_conservative_proxy` and
`endpoint_linear_interpolation` semantics. Excluded source endpoints, a non-positive
interpolation denominator, or a broken source invariant are fatal errors.

## MGRS and Source-Zone Policy

Each unique waypoint projected point is converted at precision 5 once through the
supplied converter. The result is stripped, non-empty uppercase MGRS text. Exact
source waypoints must match their handoff MGRS. Conversion failure, malformed text, or
parity failure is fatal and returns no partial result.

The route waypoint source-zone policy remains explicit MVP metadata:
`source_zone=None`, `source_zone_state=NOT_REQUESTED`,
`source_sensitive=None`, and a deterministic not-requested reason. It does not copy
the selected launch-site source zone or infer a source zone from interpolation.

## Output and Public Boundary

The immutable output contains report records in source candidate order without
automatically selecting one route. It retains only report-ready MGRS, distance,
altitude, color, score, value-semantics, source-reference, source-zone-policy, and
warning fields. Its public dictionary must not expose projected EPSG:5179 points,
WGS84 geometry, raster indexes, raw terrain metadata, or internal graph records.

The report is a terrain/surface-obstacle proxy. It is not evidence of obstacle absence,
communications availability, flight feasibility, reconnaissance success, or airspace
approval.

## Compatibility and Non-goals

Task 035G adds separate real-terrain waypoint modules. It leaves legacy
`waypoints.py`, `routing.py`, Task 035B/035D/035EF analysis, LOS/Fresnel, scoring,
color, preview/report/CLI, workflow, and dependency contracts unchanged. It adds no
real GIS data, generated report artifact, private path, operational coordinate, map/UI,
route-selection, autopilot, or device-control behavior.
