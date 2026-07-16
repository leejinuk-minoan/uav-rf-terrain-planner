# Real-Terrain Route Recommendation Boundary

## Purpose

Task 035EF converts one immutable `SelectedLaunchSiteRecord` and its authoritative
`RealTerrainLaunchAreaResult` into up to three deterministic, terrain-derived route
candidates. It is an offline research, education, and simulation analysis boundary.
It is not a flight-control, route-execution, communications-guarantee, or approval
system.

## Authoritative Inputs and Guards

The public entry point accepts a selected launch-site record, its source launch-area
result, `RealTerrainRouteConfig`, `TerrainDataAdapter`, and a
`ProjectedToMgrsConverter`. Before opening a terrain session, it validates that the
selected ID exists, projected point and public MGRS fields match the source record,
the source candidate is `valid_scored`, scored, non-excluded, and within radius, and
the scenario label is public-safe. Target and mission fields must also be valid.

After metadata resolution, DEM/DSM alignment, common bounds, and EPSG:5179 are
required. Invalid input, invalid metadata, terrain errors, conversion errors, and
performance-guard failures are fatal typed route-analysis errors. No partial route is
returned after a fatal error.

## Terrain, Altitude, and Radius Model

One terrain session supplies DEM, effective DSM, and profiles for the complete route
analysis. The selected launch point retains its sampled DEM ground elevation. Flight
MSL is `DEM MSL + allowed flight AGL` at launch, target, and valid graph nodes; free
climb and descent are represented by 3D airborne edges.

The route grid is constrained by the start-target AABB plus margin, the selected
launch-centered operating-radius square, and the common raster extent. A node is
within operating radius only when its 3D airborne distance from the launch aircraft
is less than or equal to the selected operation radius. Segment interiors are accepted
under the same sphere because linear interpolation between two in-sphere endpoints is
convex.

## Grid and Node Contract

The grid uses a fixed EPSG:5179 origin formed by flooring the clipped lower bounds to
`graph_spacing_m`. It then emits only the inclusive integer row/column range whose
aligned points remain inside the clipped bounds (within a small floating tolerance),
in row-major South-to-North then West-to-East order, with stable IDs:

```text
route-node-r{row:05d}-c{column:05d}
```

It uses exactly eight neighbors in `N, NE, E, SE, S, SW, W, NW` order. Start and
target snap to the nearest grid node with row/column tie-breaking and a maximum snap
distance of `graph_spacing_m * sqrt(2) / 2`. Identical snapped nodes produce a
zero-length direct route.

Node analysis reuses DSM LOS, Fresnel, existing scoring, and existing color
classification. Valid nodes are traversable only when they are `valid_scored`, have a
score, have a non-excluded color, are within radius, and have terrain and distance
fields. Other nodes use an explicit non-traversable state:

```text
outside_operation_radius
outside_raster_extent
terrain_nodata
invalid_surface
profile_unavailable
analysis_invalid
```

Source-zone and Fresnel-diagnostic values remain interpretation metadata and do not
alter node score, color, or route cost.

## Edge Cost and Deterministic Search

An edge exists only between traversable neighbor nodes. Its geometric distance is the
3D airborne endpoint distance. The normalized cost combines destination shielding risk
`100 - shielding_stability_score`, normalized 3D edge distance, and an existing color
penalty of green/yellow `0`, orange `50`, and red `100`.

The three fixed route modes are:

| Mode | Shielding weight | Distance weight | High-risk multiplier |
|---|---:|---:|---:|
| `shielding_minimum` | 0.90 | 0.10 | 1 |
| `distance_shielding_balanced` | 0.70 | 0.30 | 1 |
| `detour_stability` | 0.85 | 0.15 | 2 |

Search uses standard-library Dijkstra with deterministic heap ordering by cumulative
cost, cumulative 3D distance, row, column, insertion count, and node ID. Equal costs
within `1e-12` prefer lower cumulative distance and then lower predecessor row/column.
Graph topology, ordered neighbor indexes, 3D edge geometry, and base edge components
are built once; each mode reweights those components only. Graph size, edge count,
profile estimates, profile sample total, and path expansions are bounded before or
during processing. No-path is a per-mode warning, while input/invariant and resource
guard failures are fatal.

Routes are searched in the listed order. Later searches receive a directed-edge
overlap penalty. Duplicate sequences are omitted. If shared directed-edge ratio exceeds
`maximum_shared_edge_ratio`, one stronger-overlap retry is allowed; an unavailable
alternative is omitted with a warning. Three routes are preferred, one or two routes
are non-fatal partial output, and zero routes are fatal.

## Output and Handoff Boundary

The source result retains the scenario, target, operation radius, AGL, frequency, and
profile-spacing authority. These and selected projected-point/MGRS parity are checked
before a terrain session starts. Each unique route point is converted to MGRS once and
the cached value is reused for candidate paths and waypoint handoffs.

The immutable result exposes actual launch/target MGRS separately from snapped graph
endpoint IDs/MGRS and snap distances. Candidate paths are explicitly
`snapped_graph_path` records, so their distance does not imply actual-endpoint
connector distance. It exposes route mode, distance, aggregate score fields, warnings,
and selected-site identity. Route-node and handoff source-zone state is intentionally
`NOT_REQUESTED` in this MVP; no route source-zone summary is retained.
It does not expose projected coordinates, raster indexes, WGS84 geometry, or raw
terrain cells in its default user dictionary. MGRS conversion is required only for
output path points, not all graph nodes.

The result is an input boundary for a future waypoint task. It does not interpolate
500 m waypoints, create a route map/UI, alter selected launch-site state, invoke the
legacy `routing.py` or `waypoints.py` scaffold, or create actual operational guidance.

## Compatibility and Limits

Task 035EF preserves Task 035B candidate analysis, Task 035D selection/map contracts,
LOS/Fresnel calculations, score weights, color thresholds, preview/report/CLI behavior,
and dependency/workflow files. Route outputs are heuristic terrain and surface-obstacle
proxies. They do not establish obstacle absence, RF availability, flight feasibility,
reconnaissance success, or airspace approval.
