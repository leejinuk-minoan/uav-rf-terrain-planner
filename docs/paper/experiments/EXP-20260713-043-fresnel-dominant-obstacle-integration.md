# EXP-20260713-043 - Fresnel Dominant Obstacle Integration

## Experiment Purpose
Verify deterministic dominant-obstacle diagnostics without changing average Fresnel scoring.

## Input Data
Pure Python synthetic LOS samples covering endpoints, clear samples, intrusion, LOS contact, and LOS exceedance.

## Method
Filter eligible interior samples, select minimum clearance ratio with sample-index tie-break, and calculate knife-edge nu and loss.

## Expected Result
Average compatibility remains exact, endpoints are excluded, and no eligible sample returns optional `None` values.

## Actual Result
Focused tests produced the expected model, selection, compatibility, and knife-edge values.

## Metrics
Assertions cover average versus worst score, sample index, clearance, nu, loss, and optional-result behavior.

## CI / Local Test Result
Local and GitHub Actions results are recorded in the Task 032CD completion report.

## Interpretation
The diagnostic exposes a localized restrictive sample while retaining the historical path-average score.

## Limitations
The loss is a single knife-edge proxy, not a full link budget, RF measurement, or communication outcome.

## Figure/Table Candidacy
Average-versus-worst comparison is a future table candidate. No generated figure is committed.

## Public Repository Sensitivity Check
Only synthetic evidence and repository-relative references are recorded.

## Follow-Up Tasks
Define report projection or scoring integration separately.
