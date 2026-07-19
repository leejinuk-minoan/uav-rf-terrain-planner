# EXP-20260716-055 - Real-Terrain Route Contract and Implementation

## Date

2026-07-16

## Related Task / Issue / PR

Task 035EF, Issue #104, PR #105. PR #105 final head was
`4308aba994c2fdf8b1520566dad801e5349ebb2d`; it merged to `main` through
`7c49c8f74e0d827cb6f5aa155ea51b924ce51f36` on 2026-07-16. Issue #104 is
closed/completed.

## Purpose

Record the Task 035EF contract and local implementation verification for a bounded,
deterministic route recommendation layer following real-terrain launch-site selection.

## Input Data

Synthetic in-memory terrain adapter, immutable selected launch-site record, and
authoritative Task 035B launch-area result. No local GIS route input, field RF
measurement, actual flight data, generated route artifact, or actual operational
coordinate is recorded.

## Scenario / Configuration

The route layer uses a bounded EPSG:5179 8-neighbor graph, fixed AGL flight MSL, 3D
operation-radius checks, three fixed route modes, and route-node/handoff source-zone
state `NOT_REQUESTED`. Resource and path-expansion guards are enabled by the route
configuration.

## Method

The route layer consumes an immutable selected launch-site record and its authoritative
Task 035B result. It validates parity, opens one terrain session, creates a clipped
EPSG:5179 8-neighbor grid, evaluates valid nodes with existing DSM LOS/Fresnel and
score/color helpers, then performs deterministic Dijkstra for three fixed route modes.
Later modes penalize prior directed edges to seek bounded diversity.

## Expected Result

Return one to three deterministic MGRS-facing snapped-graph route candidates only
when the complete selection, mission, terrain, graph, snap, handoff, and output
contracts hold. Input, invariant, terrain, conversion, and resource failures are
fatal; a per-mode no-path is a warning.

## Actual Result

The final implementation returned complete immutable route results in focused
synthetic tests, including a valid one-node zero-edge route when snapped endpoints
coincide. It preserved legacy route/waypoint scaffolds and did not commit GIS or
generated output.

## Metrics

- Focused: graph 7, pathfinding 4, analysis 5, outputs 12; total 28.
- Full local pytest: 892 passed.
- Exact-head GitHub Actions: CI #881, run ID 29469082285, success.

## CI / Local Test Result

Local `compileall`, focused tests, full pytest, Ruff, mypy, and `git diff --check`
passed at final head. GitHub Actions CI #881 independently passed install, syntax,
pytest, Ruff, and mypy for the same final head. These are separate source-level
verification records.

## Evidence Boundary

Focused synthetic adapter tests verify configuration, selection and mission-authority
guards, clipped graph order, snapping, explicit node invariants, deterministic Dijkstra,
typed failures, cached public MGRS output, and performance failures. The amended focused
suite passed 28 tests and the full local suite passed 892 tests. Complete-result tests
also reject partial authority removal and endpoint parity mutations while accepting a
consistent one-node, zero-distance snapped route. Local tests verify source
behavior only. No field
RF test, real GIS route run, browser/UI test, generated route artifact, or actual
coordinate is recorded in the repository.

## Interpretation Limit

The calculated paths are research and simulation terrain-risk proxies. They do not
measure link performance or demonstrate operational route suitability, flight
feasibility, or regulatory approval.

## Paper Figure / Table Candidate

Potential methods table: route mode weights, bounded graph controls, and output
contract. Potential verification table: focused/full test counts and CI state. Neither
is field-performance evidence.

## Public Repository Sensitivity Check

No GIS raster, private path, actual operational coordinate, credential, generated
route artifact, browser capture, or device-control content is included.

## Follow-up Tasks

Task 035G consumes the complete handoff for deterministic waypoint reporting. Real GIS
route smoke, browser/UI verification, field RF validation, and approval/flight claims
remain out of scope.
