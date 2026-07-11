# MGRS External Input/Output Boundary Policy

## Purpose

This document defines the external coordinate boundary for UAV RF Terrain Planner.

The project may use several coordinate systems internally, but user-facing coordinate input and output must use MGRS by default.

## User-facing coordinate rule

External input: MGRS only.

External output: MGRS only.

MGRS is the standard coordinate format for user-entered target locations, user-facing launch-site locations, candidate-cell tables, route summaries, waypoint tables, map popup content, and report-ready coordinate fields.

## Internal coordinate rule

Internal computation data may include:

- WGS84.
- EPSG:5179.
- local x_m/y_m.
- raster row/col.

These values are internal computation data. They may be used for projection, distance calculation, raster sampling, terrain profile extraction, source-zone assignment, and future map construction.

## Input coordinate requirements

User-entered coordinates must be represented as MGRS fields. Preferred input field names include:

- `target_mgrs`.
- `launch_site_mgrs`.

Internal conversion may produce WGS84, EPSG:5179, local metric coordinates, or raster row/col values after MGRS input is accepted.

## Output coordinate requirements

User-facing output coordinate fields should prefer:

- `target_mgrs`.
- `launch_site_mgrs`.
- `waypoint_mgrs`.
- `candidate_cell_mgrs`.
- `selected_route_waypoint_mgrs`.

Map popup, report, candidate table, route table, and waypoint table default coordinate display must be MGRS.

## Debug/internal coordinate handling

The following field names are internal/debug coordinate fields:

- `x_m`.
- `y_m`.
- `row`.
- `col`.
- `epsg5179_x_m`.
- `epsg5179_y_m`.

These fields must not be the default user-facing coordinate fields. They may be retained in developer/debug outputs only when explicitly labeled internal/debug.

## Candidate map output implications

Candidate map output records may keep internal metric or raster-derived fields for computation and future renderer input.

User-facing candidate map popups and candidate tables should display `candidate_cell_mgrs` as the default coordinate field. Internal `x_m`, `y_m`, row/col, or EPSG:5179 values should be hidden or clearly labeled as internal/debug.

## Route and waypoint output implications

Route summaries and waypoint outputs should display MGRS coordinates by default.

Preferred route and waypoint fields include `launch_site_mgrs`, `waypoint_mgrs`, and `selected_route_waypoint_mgrs`. Internal route geometry, local metric coordinates, and raster index values may remain available for developer/debug inspection only.

## Local smoke / developer CLI implications

Local smoke scripts and developer CLIs may accept internal projected coordinates when the task explicitly states that the interface is developer/debug only.

If local smoke results are copied into user-facing reports, checkpoint summaries, or paper-ready tables, coordinate fields must be converted to MGRS or omitted. Aggregate-only smoke output that contains no coordinates does not conflict with this policy.

## Non-goals

This policy does not implement MGRS to EPSG:5179 conversion.

This policy does not implement UI behavior, map rendering, candidate scoring integration, LOS/Fresnel recalculation, or end-to-end coordinate display conversion.

This policy does not load real raster files or commit local GIS data.

## Safety and interpretation limits

This policy is an external I/O boundary guardrail. It is not field validation and does not certify terrain accuracy, communication behavior, route suitability, approval outcomes, or vehicle operation behavior.

Internal coordinate values are implementation details and should not be interpreted as default user-facing coordinates.

## Follow-up implementation tasks

1. Add explicit MGRS fields to user-facing candidate, route, waypoint, and map output schemas.
2. Add MGRS-to-internal projection adapter validation in a local task.
3. Update developer CLIs to label projected coordinates as internal/debug when shown.
4. Update map popup and report formatting so MGRS is the default coordinate display.
5. Add end-to-end tests for MGRS input acceptance and MGRS output display once conversion implementation is available.
