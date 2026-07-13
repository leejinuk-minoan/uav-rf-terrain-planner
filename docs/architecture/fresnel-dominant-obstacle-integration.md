# Fresnel Dominant Obstacle Integration

## Purpose
Task 032CD integrates a dominant-obstacle diagnostic into DSM Fresnel analysis without changing operational scoring or outputs.

## Current Project Context
Task 032AB added pure knife-edge helpers. Task 032CD applies them to eligible samples from `analyze_dsm_fresnel(...)`.

## Data Model
`average_fresnel_score` explicitly names the arithmetic mean. Optional `worst_obstacle_score` and nested `DominantFresnelObstacle` record the restrictive sample, geometry, clearance, score, nu, and loss.

## Eligible Sample Rule
Eligible samples have positive `d1_m`, `d2_m`, and Fresnel radius plus finite clearance ratio and score. Endpoints and zero-radius samples are excluded. Non-finite diagnostic values raise `FresnelAnalysisError`.

## Dominant Obstacle Selection
The eligible sample with the smallest clearance ratio is selected. With no eligible sample, both diagnostic fields are `None`.

## Tie-Break Policy
Equal clearance ratios are resolved by lower `sample_index`.

## Average and Worst Score Compatibility
`dsm_fresnel_score` retains its average meaning and equals `average_fresnel_score`. The worst score does not replace it.

## Knife-edge Loss Integration
The selected clearance ratio is converted to nu and a single knife-edge additional diffraction-loss proxy. This is not a full link budget.

## Scoring Boundary
Scoring, colors, overall score, and ranking remain unchanged and continue using the average Fresnel score.

## Output Boundary
Preview, report, CLI, map, and JSON outputs do not expose these fields. A future consumer may define a flat projection; 0.1 dB or integer dB display precision is recommended.

## Error Handling
Non-finite eligible values raise `FresnelAnalysisError`; no eligible sample is a valid optional result.

## Limitations
This is a single-obstacle terrain/surface proxy, not measured RF validation or evidence of communication success.

## Public Repository Sensitivity Check
No private path, terrain raster, generated artifact, credential, or operational command is recorded.

## Follow-Up Tasks
Any report projection or scoring use requires a separate reviewed task.
