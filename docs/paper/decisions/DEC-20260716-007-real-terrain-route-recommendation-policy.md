# DEC-20260716-007 - Real-Terrain Route Recommendation Policy

## Decision

Task 035EF implements selected-launch-site route recommendation only after the Task
035B real-terrain result and Task 035D immutable selection boundaries are validated.
The implementation uses one EPSG:5179 terrain-analysis session, a bounded 8-neighbor
grid, fixed-AGL flight MSL, 3D airborne operating-radius constraints, and deterministic
Dijkstra to produce up to three distinct route candidates.

## Rationale

The existing synthetic route scaffold cannot be treated as an authoritative
real-terrain workflow because it does not bind a user-selected real candidate, raster
metadata, effective DSM surface, or Task 035B exclusion semantics. Recomputing a
launch-site selection or changing score/color semantics would also break reviewed
contracts. The new boundary therefore consumes the authoritative selected record and
source result, reuses existing LOS/Fresnel/scoring/classification helpers, and leaves
existing modules unchanged.

## Cost and Diversity Policy

Route modes use fixed shielding/distance weights: 0.90/0.10, 0.70/0.30, and
0.85/0.15. Existing color classes map to risk penalties of 0 for green/yellow, 50 for
orange, and 100 for red. Directed-edge overlap is penalized for subsequent routes;
identical routes are omitted and one stronger-overlap retry is permitted when sharing
exceeds the configured threshold.

## Interpretation Limit

The output is a deterministic terrain and DSM proxy for research, education, and
simulation. It is not evidence of actual obstacle absence, communications availability,
route safety, flight feasibility, reconnaissance success, or airspace approval.

## Compatibility

This decision does not change Task 035B candidate analysis, Task 035D map/selection,
LOS/Fresnel formulas, scoring/color thresholds, source-zone scoring semantics,
preview/report/CLI behavior, legacy route/waypoint scaffolds, dependencies, or CI.

The source launch-area result preserves mission authority needed by the route boundary:
scenario, target, operation radius, AGL, frequency, and resolved profile spacing. The
route boundary validates that authority and selected MGRS parity before opening terrain.
Route nodes and handoffs intentionally retain `NOT_REQUESTED` source-zone metadata in
this MVP rather than inheriting it from the selected launch site.

## Public Repository Sensitivity Check

This record contains no GIS data, generated route, actual coordinate, private local
path, credential, external-device command, autopilot instruction, or flight-control
output.
