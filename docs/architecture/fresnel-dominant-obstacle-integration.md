# Fresnel Dominant Obstacle Integration

## Purpose

Task 032CD integrates a dominant-obstacle diagnostic into DSM Fresnel analysis without changing operational scoring or outputs.

## Current Project Context

Task 032AB added pure knife-edge helpers. Task 032CD applies them to eligible samples from `analyze_dsm_fresnel(...)`.

Task 033A records the user's selected follow-up direction: expose the diagnostics as optional preview/report support information while keeping scoring, color, ranking, route, and waypoint behavior unchanged.

The approved output boundary is documented in:

```text
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
```

Task 033A does not implement that runtime projection. Task 033B is the separate implementation candidate.

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

Current scoring remains:

```text
shielding_stability_score = dsm_los_score × 0.40 + dsm_fresnel_score × 0.60
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20
```

The strict LOS cap remains in effect when `dsm_los_score == 0`.

Dominant-obstacle fields do not alter scoring, colors, overall score, ranking, route cost, or waypoint cost. No separate DSM surface-complexity score is part of the current default score.

## Output Boundary

Current preview, report, CLI, map, and JSON outputs do not expose these fields.

The Task 033A boundary approves a future optional flat projection for JSON/plain-text/report consumers, preserves legacy saved previews, distinguishes unavailable diagnostics from an enriched no-eligible-obstacle result, and keeps appendix-table columns unchanged for Task 033B.

`dominant_obstacle_sample_index` remains internal. Human-readable diffraction loss uses 0.1 dB precision; JSON retains the original float value.

## Task 033A and Task 033B Boundary

### Task 033A

- documentation and code/document contract audit only;
- no source, test, runtime schema, formatter, or CLI changes;
- output field names, compatibility states, precision, and invariants defined;
- current documentation reconciled with the implemented score model.

### Task 033B

- optional diagnostic bridge across candidate/map/display/preview/report layers;
- legacy preview compatibility;
- all-or-none diagnostic key-set validation;
- `## Fresnel Diagnostics` report section;
- no appendix-table column change;
- no scoring, color, ranking, route, or waypoint change.

## Error Handling

Non-finite eligible values raise `FresnelAnalysisError`; no eligible sample is a valid optional result.

Output consumers must distinguish:

```text
diagnostic fields absent → diagnostics unavailable in this preview record
diagnostic fields present with null obstacle details → no eligible interior dominant obstacle sample
```

A partial diagnostic field set is not an approved state.

## Limitations

This is a single-obstacle terrain/surface proxy, not measured RF validation, a full link budget, RSSI/SINR/packet-loss prediction, or evidence of communication or flight success.

## Public Repository Sensitivity Check

No private path, terrain raster, generated artifact, credential, operational command, or device-control output is recorded.

## Follow-Up Tasks

1. Task 033B may implement the reviewed optional preview/report projection.
2. Appendix-table extension requires a separate reviewed task.
3. Any scoring use requires separate validation and explicit approval.
