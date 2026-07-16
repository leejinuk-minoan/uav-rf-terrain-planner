# EXP-20260716-056 - Real-Terrain Waypoint Reporting

## Purpose

Record focused synthetic-contract verification for Task 035G real-terrain waypoint
reporting over complete route handoffs.

## Method

Focused tests construct immutable synthetic route results and verify 3D-distance
sampling, exact source-node reuse, conservative interpolated color/score values,
short and zero-length routes, MGRS cache behavior, source-zone `NOT_REQUESTED` policy,
output guards, and public output restrictions.

## Evidence Boundary

The tests use synthetic in-memory route contracts only. They do not load GIS files,
create a generated report, use actual coordinates, run browser/UI behavior, validate
field RF conditions, or establish flight feasibility.

## Interpretation Limit

Waypoint values are deterministic reporting proxies derived from prior route output.
They do not prove real-world obstacle absence, communication success, route safety, or
airspace approval.
