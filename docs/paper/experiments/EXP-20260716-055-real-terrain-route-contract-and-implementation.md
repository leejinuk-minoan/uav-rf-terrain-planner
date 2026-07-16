# EXP-20260716-055 - Real-Terrain Route Contract and Implementation

## Purpose

Record the Task 035EF contract and local implementation verification for a bounded,
deterministic route recommendation layer following real-terrain launch-site selection.

## Method

The route layer consumes an immutable selected launch-site record and its authoritative
Task 035B result. It validates parity, opens one terrain session, creates a clipped
EPSG:5179 8-neighbor grid, evaluates valid nodes with existing DSM LOS/Fresnel and
score/color helpers, then performs deterministic Dijkstra for three fixed route modes.
Later modes penalize prior directed edges to seek bounded diversity.

## Evidence Boundary

Focused synthetic adapter tests verify configuration, selection guards, graph order,
snapping, explicit node invariants, deterministic Dijkstra, public MGRS output, and
performance failures. The initial Task 035EF focused suite passed 11 tests and the
full local suite passed 875 tests. Local tests verify source behavior only. No field
RF test, real GIS route run, browser/UI test, generated route artifact, or actual
coordinate is recorded in the repository.

## Interpretation Limit

The calculated paths are research and simulation terrain-risk proxies. They do not
measure link performance or demonstrate operational route suitability, flight
feasibility, or regulatory approval.
